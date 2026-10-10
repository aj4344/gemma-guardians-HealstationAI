"""Streaming single-file multipart receiver (ING-01, ING-02).

The request body is parsed as it arrives and the file's bytes go straight to
a sink (the encrypted quarantine writer). Nothing is buffered beyond one
network chunk plus the first few KiB used to detect the file type, and
nothing is spooled to disk in plaintext. Limits are enforced by the sink as
bytes arrive, so an oversized upload is refused without reading the rest.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Protocol

import anyio
from python_multipart.multipart import MultipartParser, parse_options_header
from starlette.requests import ClientDisconnect, Request

from healstation.api.errors import ApiError
from healstation.ingest.filetypes import SNIFF_BYTES

MAX_FIELDS = 8
MAX_FIELD_BYTES = 1024
MAX_FILENAME_CHARS = 255


class UploadSink(Protocol):
    def begin(self, header: bytes, filename: str, content_type: str) -> None: ...

    def write(self, data: bytes) -> None: ...

    def finish(self) -> None: ...

    def abort(self) -> None: ...


def clean_filename(raw: bytes | None) -> str:
    """A display-only version of the client filename (stored encrypted, never used in a path)."""
    text = (raw or b"").decode("utf-8", "replace")
    text = re.split(r"[\\/]", text)[-1]
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C")
    return text.strip()[:MAX_FILENAME_CHARS] or "upload"


class _Receiver:
    def __init__(self, sink: UploadSink):
        self.sink = sink
        self.fields: dict[str, str] = {}
        self.files_seen = 0
        self.file_bytes = 0
        self._header_field = bytearray()
        self._header_value = bytearray()
        self._headers: dict[bytes, bytes] = {}
        self._part_name = ""
        self._is_file = False
        self._filename = ""
        self._content_type = ""
        self._sniff = bytearray()
        self._begun = False
        self._field_value = bytearray()

    # python-multipart callbacks ------------------------------------------------
    def on_part_begin(self) -> None:
        self._headers = {}
        self._is_file = False
        self._field_value = bytearray()

    def on_header_field(self, data: bytes, start: int, end: int) -> None:
        self._header_field += data[start:end]

    def on_header_value(self, data: bytes, start: int, end: int) -> None:
        self._header_value += data[start:end]

    def on_header_end(self) -> None:
        self._headers[bytes(self._header_field).strip().lower()] = bytes(self._header_value).strip()
        self._header_field.clear()
        self._header_value.clear()

    def on_headers_finished(self) -> None:
        _disposition, options = parse_options_header(self._headers.get(b"content-disposition", b""))
        self._part_name = options.get(b"name", b"").decode("utf-8", "replace")
        if b"filename" in options:
            self.files_seen += 1
            if self.files_seen > 1:
                raise ApiError("MULTIPLE_FILES")
            self._is_file = True
            self._filename = clean_filename(options.get(b"filename"))
            self._content_type = self._headers.get(b"content-type", b"").decode("latin-1", "replace")
            self._sniff = bytearray()
            self._begun = False
        elif len(self.fields) >= MAX_FIELDS:
            raise ApiError("BAD_REQUEST")

    def on_part_data(self, data: bytes, start: int, end: int) -> None:
        chunk = data[start:end]
        if not self._is_file:
            self._field_value += chunk
            if len(self._field_value) > MAX_FIELD_BYTES:
                raise ApiError("BAD_REQUEST")
            return
        self.file_bytes += len(chunk)
        if self._begun:
            self.sink.write(chunk)
            return
        self._sniff += chunk
        if len(self._sniff) >= SNIFF_BYTES:
            self._start_file()

    def _start_file(self) -> None:
        header = bytes(self._sniff)
        self.sink.begin(header, self._filename, self._content_type)
        self._begun = True
        self._sniff = bytearray()
        if header:
            self.sink.write(header)

    def on_part_end(self) -> None:
        if self._is_file:
            if self.file_bytes == 0:
                raise ApiError("EMPTY_FILE")
            if not self._begun:
                self._start_file()
            self.sink.finish()
        else:
            self.fields[self._part_name] = bytes(self._field_value).decode("utf-8", "replace")


async def receive_single_file(request: Request, sink: UploadSink) -> dict[str, str]:
    """Stream a multipart upload with exactly one file into ``sink``; returns the form fields."""
    content_type, options = parse_options_header(request.headers.get("content-type", ""))
    boundary = options.get(b"boundary")
    if content_type != b"multipart/form-data" or not boundary:
        raise ApiError("BAD_REQUEST")
    receiver = _Receiver(sink)
    callbacks = {
        name: getattr(receiver, name)
        for name in (
            "on_part_begin",
            "on_part_data",
            "on_part_end",
            "on_header_field",
            "on_header_value",
            "on_header_end",
            "on_headers_finished",
        )
    }
    parser = MultipartParser(boundary, callbacks)
    finished = False
    try:
        async for chunk in request.stream():
            if chunk:
                # Parsing calls the sink, which encrypts and writes: keep it off the event loop.
                await anyio.to_thread.run_sync(parser.write, chunk)
        await anyio.to_thread.run_sync(parser.finalize)
        if receiver.files_seen == 0:
            raise ApiError("NO_FILE")
        finished = True
    except ClientDisconnect:
        raise ApiError("BAD_REQUEST") from None
    except ApiError:
        raise
    except Exception:
        # Malformed multipart framing; parser details are not echoed back.
        raise ApiError("BAD_REQUEST") from None
    finally:
        if not finished:
            sink.abort()
    return receiver.fields
