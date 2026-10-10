"""File type detection by content (ING-04, PRD Appendix B).

The client's MIME type and file extension are never trusted: they are only
compared against what the bytes say. A file that matches no signature is
UNSUPPORTED_TYPE, one whose declared type disagrees is TYPE_MISMATCH, and one
that matches signatures of more than one kind is POLYGLOT_FILE.
"""

from __future__ import annotations

from dataclasses import dataclass

PDF_SIGNATURE_WINDOW = 1024
# Enough for every signature: %PDF- may start anywhere in the first 1024 bytes.
SNIFF_BYTES = PDF_SIGNATURE_WINDOW
TAIL_BYTES = 64 * 1024  # ZIP end-of-central-directory may sit anywhere in the last 64 KiB


@dataclass(frozen=True)
class FileType:
    kind: str  # audio | image | pdf | dicom
    mime: str
    label: str  # short name for status summaries
    archive: bool = False


WEBM = FileType("audio", "audio/webm", "webm")
OGG = FileType("audio", "audio/ogg", "ogg")
WAV = FileType("audio", "audio/wav", "wav")
MP3 = FileType("audio", "audio/mpeg", "mp3")
M4A = FileType("audio", "audio/mp4", "m4a")
JPEG = FileType("image", "image/jpeg", "jpeg")
PNG = FileType("image", "image/png", "png")
WEBP = FileType("image", "image/webp", "webp")
HEIC = FileType("image", "image/heic", "heic")
PDF = FileType("pdf", "application/pdf", "pdf")
DICOM = FileType("dicom", "application/dicom", "dicom")
DICOM_ZIP = FileType("dicom", "application/zip", "zip", archive=True)

_HEIF_BRANDS = {b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"hevm", b"hevs", b"mif1", b"msf1", b"avif"}
_AUDIO_MP4_BRANDS = {b"M4A ", b"M4B ", b"mp41", b"mp42", b"isom", b"iso2", b"dash", b"3gp4", b"3gp5", b"3g2a"}


def _ftyp(header: bytes) -> FileType | None:
    if len(header) < 12 or header[4:8] != b"ftyp":
        return None
    brand = header[8:12]
    if brand in _HEIF_BRANDS:
        return None if brand == b"avif" else HEIC
    if brand in _AUDIO_MP4_BRANDS:
        return M4A
    return None


def signatures(header: bytes) -> list[FileType]:
    """Every type whose signature the first bytes match (normally zero or one)."""
    found: list[FileType] = []
    if header.startswith(b"\x1a\x45\xdf\xa3"):
        found.append(WEBM)
    if header.startswith(b"OggS"):
        found.append(OGG)
    if header.startswith(b"RIFF") and header[8:12] == b"WAVE":
        found.append(WAV)
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        found.append(WEBP)
    if header.startswith(b"ID3") or (len(header) > 1 and header[0] == 0xFF and (header[1] & 0xE0) == 0xE0):
        found.append(MP3)
    ftyp = _ftyp(header)
    if ftyp:
        found.append(ftyp)
    if header.startswith(b"\xff\xd8\xff"):
        found.append(JPEG)
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        found.append(PNG)
    if b"%PDF-" in header[:PDF_SIGNATURE_WINDOW]:
        found.append(PDF)
    if header[128:132] == b"DICM":
        found.append(DICOM)
    if header.startswith(b"PK\x03\x04"):
        found.append(DICOM_ZIP)
    # MP3 frame-sync bytes are weak: drop them when a stronger signature matched.
    if len(found) > 1 and MP3 in found and not header.startswith(b"ID3"):
        found.remove(MP3)
    return found


_MIME_KINDS = {
    "audio": "audio",
    "image": "image",
    "application/pdf": "pdf",
    "application/x-pdf": "pdf",
    "application/dicom": "dicom",
    "application/zip": "dicom",
    "application/x-zip-compressed": "dicom",
    # Browsers label MediaRecorder output as video/* in some versions.
    "video/webm": "audio",
    "video/mp4": "audio",
    "video/ogg": "audio",
}
_GENERIC_MIMES = {"", "application/octet-stream", "binary/octet-stream", "application/unknown"}
_EXTENSION_KINDS = {
    "webm": "audio", "ogg": "audio", "oga": "audio", "opus": "audio", "wav": "audio", "mp3": "audio",
    "m4a": "audio", "aac": "audio", "mp4": "audio",
    "jpg": "image", "jpeg": "image", "png": "image", "webp": "image", "heic": "image", "heif": "image",
    "pdf": "pdf",
    "dcm": "dicom", "dicom": "dicom", "zip": "dicom",
}  # fmt: skip


def declared_kind(mime: str | None, filename: str | None) -> tuple[str | None, str | None]:
    """(kind from MIME, kind from extension); None where nothing specific is declared."""
    base = (mime or "").split(";", 1)[0].strip().lower()
    mime_kind = None
    if base not in _GENERIC_MIMES:
        mime_kind = _MIME_KINDS.get(base) or _MIME_KINDS.get(base.split("/", 1)[0]) or "other"
    extension = None
    name = (filename or "").strip().lower()
    if "." in name:
        extension = _EXTENSION_KINDS.get(name.rsplit(".", 1)[-1], "other")
    return mime_kind, extension


class TypeRejected(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def detect(header: bytes, mime: str | None, filename: str | None, allowed_kinds: set[str]) -> FileType:
    """Detected type of an upload from its first bytes, or TypeRejected(code)."""
    matches = signatures(header)
    kinds = {match.kind for match in matches}
    if len(kinds) > 1 or len(matches) > 1 and not all(m.kind == "audio" for m in matches):
        raise TypeRejected("POLYGLOT_FILE")
    if not matches:
        raise TypeRejected("UNSUPPORTED_TYPE")
    detected = matches[0]
    if detected.kind not in allowed_kinds:
        raise TypeRejected("UNSUPPORTED_TYPE")
    mime_kind, extension_kind = declared_kind(mime, filename)
    for declared in (mime_kind, extension_kind):
        if declared is not None and declared != detected.kind:
            raise TypeRejected("TYPE_MISMATCH")
    return detected


def check_tail(detected: FileType, tail: bytes) -> None:
    """Deep check once the whole file is in: hidden archives and broken PDFs (VALIDATING)."""
    if not detected.archive and b"PK\x05\x06" in tail:
        # A ZIP directory appended to another file: a classic polyglot.
        raise TypeRejected("POLYGLOT_FILE")
    if detected.kind == "pdf" and b"%%EOF" not in tail[-PDF_SIGNATURE_WINDOW:]:
        raise TypeRejected("CORRUPT_FILE")
