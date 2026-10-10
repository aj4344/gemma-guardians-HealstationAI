"""Encrypted blob files (format HSE1, ADR-001).

Layout: a fixed 79-byte header, then the plaintext in 64 KiB chunks, each
sealed with AES-256-GCM under a random per-blob key:

    magic "HSE1" | version u8 | reserved u8 | chunk size u32 | wrapped-key length u16
    | file key wrapped by the case key (60 bytes) | nonce prefix (7 bytes)

Chunk *i* uses nonce ``prefix ‖ i (u32) ‖ last-chunk flag (u8)`` and the whole
header as associated data, so reordered, truncated or re-headed files fail to
decrypt. Fixed chunk sizes make the reader seekable: zipfile, pydicom, Pillow
and PyAV read straight from an encrypted blob without plaintext on disk.
"""

from __future__ import annotations

import io
import os
import shutil
import struct
from collections.abc import Iterator
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from healstation.store.crypto import KEY_BYTES, TAG_BYTES, CryptoError, new_key, unwrap_key, wrap_key

MAGIC = b"HSE1"
VERSION = 1
CHUNK_SIZE = 64 * 1024
WRAPPED_KEY_BYTES = 12 + KEY_BYTES + TAG_BYTES
NONCE_PREFIX_BYTES = 7
_HEADER_STRUCT = struct.Struct(f">4sBBIH{WRAPPED_KEY_BYTES}s{NONCE_PREFIX_BYTES}s")
HEADER_BYTES = _HEADER_STRUCT.size
BLOB_SUFFIX = ".hse"
PARTIAL_SUFFIX = ".part"


def _nonce(prefix: bytes, index: int, last: bool) -> bytes:
    return prefix + index.to_bytes(4, "big") + (b"\x01" if last else b"\x00")


def _context(blob_id: str) -> str:
    return f"blob:{blob_id}"


class BlobWriter(io.RawIOBase):
    """Write-only stream that encrypts as it goes; the file appears only on close()."""

    def __init__(self, path: Path, case_key: bytes, blob_id: str, chunk_size: int = CHUNK_SIZE):
        super().__init__()
        self.path = path
        self._partial = path.with_name(path.name + PARTIAL_SUFFIX)
        self._file_key = new_key()
        self._aead = AESGCM(self._file_key)
        self._prefix = os.urandom(NONCE_PREFIX_BYTES)
        self._chunk_size = chunk_size
        wrapped = wrap_key(case_key, self._file_key, _context(blob_id))
        self._header = _HEADER_STRUCT.pack(MAGIC, VERSION, 0, chunk_size, len(wrapped), wrapped, self._prefix)
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(self._partial, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        self._out = os.fdopen(fd, "wb")
        self._out.write(self._header)
        self._buffer = bytearray()
        self._index = 0
        self.bytes_written = 0
        self._finished = False

    def writable(self) -> bool:
        return True

    def write(self, data) -> int:
        if self._finished:
            raise ValueError("write to a closed blob")
        view = memoryview(data)
        self._buffer += view
        self.bytes_written += len(view)
        # Keep at least one byte back: the final chunk must carry the last flag.
        while len(self._buffer) > self._chunk_size:
            chunk = bytes(self._buffer[: self._chunk_size])
            del self._buffer[: self._chunk_size]
            self._emit(chunk, last=False)
        return len(view)

    def _emit(self, chunk: bytes, last: bool) -> None:
        self._out.write(self._aead.encrypt(_nonce(self._prefix, self._index, last), chunk, self._header))
        self._index += 1

    def close(self) -> None:
        if self._finished:
            return
        self._emit(bytes(self._buffer), last=True)
        self._buffer.clear()
        self._out.flush()
        os.fsync(self._out.fileno())
        self._out.close()
        os.replace(self._partial, self.path)
        self._finished = True
        super().close()

    def abort(self) -> None:
        """Discard everything written so far; leaves no file behind."""
        if self._finished:
            return
        self._finished = True
        self._buffer.clear()
        try:
            self._out.close()
        finally:
            self._partial.unlink(missing_ok=True)
        super().close()


class BlobReader(io.RawIOBase):
    """Seekable, read-only plaintext view of an encrypted blob."""

    def __init__(self, path: Path, case_key: bytes, blob_id: str):
        super().__init__()
        self._file = open(path, "rb")  # noqa: SIM115 — closed in close()
        try:
            self._header = self._file.read(HEADER_BYTES)
            if len(self._header) != HEADER_BYTES:
                raise CryptoError("blob header truncated")
            magic, version, _, chunk_size, key_len, wrapped, prefix = _HEADER_STRUCT.unpack(self._header)
            if magic != MAGIC or version != VERSION or key_len != WRAPPED_KEY_BYTES or chunk_size <= 0:
                raise CryptoError("not an HSE1 blob")
            self._aead = AESGCM(unwrap_key(case_key, wrapped, _context(blob_id)))
            self._prefix = prefix
            self._chunk_size = chunk_size
            data_bytes = os.fstat(self._file.fileno()).st_size - HEADER_BYTES
            stride = chunk_size + TAG_BYTES
            self._chunks = max(1, -(-data_bytes // stride))
            last_len = data_bytes - (self._chunks - 1) * stride
            if data_bytes < TAG_BYTES or last_len < TAG_BYTES:
                raise CryptoError("blob truncated")
            self.size = (self._chunks - 1) * chunk_size + last_len - TAG_BYTES
        except Exception:
            self._file.close()
            raise
        self._pos = 0
        self._cached_index = -1
        self._cached = b""

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self._pos

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self._pos, io.SEEK_END: self.size}[whence]
        target = base + offset
        if target < 0:
            raise ValueError("negative seek position")
        self._pos = target
        return target

    def _chunk(self, index: int) -> bytes:
        if index != self._cached_index:
            stride = self._chunk_size + TAG_BYTES
            self._file.seek(HEADER_BYTES + index * stride)
            sealed = self._file.read(stride)
            last = index == self._chunks - 1
            try:
                self._cached = self._aead.decrypt(_nonce(self._prefix, index, last), sealed, self._header)
            except InvalidTag as error:
                raise CryptoError("blob chunk failed authentication") from error
            self._cached_index = index
        return self._cached

    def readinto(self, buffer) -> int:
        if self._pos >= self.size:
            return 0
        index, offset = divmod(self._pos, self._chunk_size)
        data = self._chunk(index)[offset : offset + len(buffer)]
        buffer[: len(data)] = data
        self._pos += len(data)
        return len(data)

    def readall(self) -> bytes:
        parts = []
        while chunk := self.read(self._chunk_size):
            parts.append(chunk)
        return b"".join(parts)

    def close(self) -> None:
        self._cached = b""
        self._file.close()
        super().close()


class BlobStore:
    """Per-case directories of encrypted blobs: DATA_DIR/cases/<case id>/<blob id>.hse."""

    def __init__(self, root: Path):
        self.root = root
        self.cases_dir = root / "cases"
        self.cases_dir.mkdir(parents=True, exist_ok=True, mode=0o700)

    def case_dir(self, case_id: str) -> Path:
        _check_id(case_id)
        return self.cases_dir / case_id

    def path(self, case_id: str, blob_id: str) -> Path:
        _check_id(blob_id)
        return self.case_dir(case_id) / f"{blob_id}{BLOB_SUFFIX}"

    def writer(self, case_id: str, blob_id: str, case_key: bytes) -> BlobWriter:
        return BlobWriter(self.path(case_id, blob_id), case_key, blob_id)

    def reader(self, case_id: str, blob_id: str, case_key: bytes) -> BlobReader:
        return BlobReader(self.path(case_id, blob_id), case_key, blob_id)

    def write_bytes(self, case_id: str, blob_id: str, case_key: bytes, data: bytes) -> int:
        writer = self.writer(case_id, blob_id, case_key)
        try:
            writer.write(data)
        except Exception:
            writer.abort()
            raise
        writer.close()
        return len(data)

    def read_bytes(self, case_id: str, blob_id: str, case_key: bytes) -> bytes:
        with self.reader(case_id, blob_id, case_key) as reader:
            return reader.readall()

    def exists(self, case_id: str, blob_id: str) -> bool:
        return self.path(case_id, blob_id).is_file()

    def delete(self, case_id: str, blob_id: str) -> None:
        path = self.path(case_id, blob_id)
        path.unlink(missing_ok=True)
        path.with_name(path.name + PARTIAL_SUFFIX).unlink(missing_ok=True)

    def delete_case(self, case_id: str) -> None:
        shutil.rmtree(self.case_dir(case_id), ignore_errors=True)

    def usage_bytes(self) -> int:
        total = 0
        for _case_id, _blob_id, path in self.iter_files():
            try:
                total += path.stat().st_size
            except FileNotFoundError:
                continue
        return total

    def iter_files(self) -> Iterator[tuple[str, str, Path]]:
        """Every blob or partial file on disk as (case id, blob id, path)."""
        if not self.cases_dir.is_dir():
            return
        for case_dir in self.cases_dir.iterdir():
            if not case_dir.is_dir():
                continue
            for path in case_dir.iterdir():
                name = path.name
                blob_id = name.split(".", 1)[0]
                yield case_dir.name, blob_id, path

    def iter_case_ids(self) -> Iterator[str]:
        if self.cases_dir.is_dir():
            for case_dir in self.cases_dir.iterdir():
                if case_dir.is_dir():
                    yield case_dir.name


_ID_CHARS = frozenset("0123456789abcdef")


def _check_id(value: str) -> None:
    # Ids are server-generated uuid4 hex strings; nothing else is ever used in a path.
    if not (isinstance(value, str) and len(value) == 32 and _ID_CHARS.issuperset(value)):
        raise ValueError("invalid storage id")
