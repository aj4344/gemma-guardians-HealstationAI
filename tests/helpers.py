"""Shared test helpers: synthetic files and a streaming ASGI client."""

from __future__ import annotations

import io
import uuid
import zipfile

import anyio
from PIL import Image

BOUNDARY = "----healstation-test-boundary"


def png_bytes(size=(64, 48), color=(200, 30, 30)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def jpeg_bytes(size=(64, 48), color=(30, 160, 60), exif: bytes | None = None) -> bytes:
    buffer = io.BytesIO()
    kwargs = {"exif": exif} if exif else {}
    Image.new("RGB", size, color).save(buffer, format="JPEG", quality=90, **kwargs)
    return buffer.getvalue()


def minimal_pdf(text: str = "Haemoglobin 9.5 g/dL") -> bytes:
    """A small valid one-page PDF with a text layer."""
    content = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(b"%d 0 obj\n" % number + body + b"\nendobj\n")
    xref = out.tell()
    out.write(b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1))
    for offset in offsets:
        out.write(b"%010d 00000 n \n" % offset)
    out.write(b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref))
    return out.getvalue()


def zip_bytes(entries: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return buffer.getvalue()


def multipart_parts(
    filename: str, content_type: str, fields: dict[str, str] | None = None, field_name: str = "file"
) -> tuple[bytes, bytes]:
    """(prefix, suffix) framing one file part, so the file body can be streamed in between."""
    head = b""
    for name, value in (fields or {}).items():
        head += (f"--{BOUNDARY}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n").encode()
    head += (
        f"--{BOUNDARY}\r\nContent-Disposition: form-data; name=\"{field_name}\"; filename=\"{filename}\"\r\n"
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode()
    return head, f"\r\n--{BOUNDARY}--\r\n".encode()


def multipart_body(filename: str, content_type: str, data: bytes, fields: dict[str, str] | None = None) -> bytes:
    head, tail = multipart_parts(filename, content_type, fields)
    return head + data + tail


def upload(client, case_id: str, data: bytes, filename="photo.png", content_type="image/png", fields=None, **kw):
    return client.post(
        f"/api/v2/cases/{case_id}/attachments",
        content=multipart_body(filename, content_type, data, fields),
        headers={"Content-Type": f"multipart/form-data; boundary={BOUNDARY}", **kw.pop("headers", {})},
        **kw,
    )


def run_asgi(app, method: str, path: str, chunks, headers: dict[str, str]):
    """Drive the ASGI app with a body delivered chunk by chunk; returns (status, body, chunks read)."""
    consumed = 0
    iterator = iter(chunks)
    messages: list[dict] = []

    async def receive():
        nonlocal consumed
        try:
            chunk = next(iterator)
        except StopIteration:
            return {"type": "http.request", "body": b"", "more_body": False}
        consumed += 1
        return {"type": "http.request", "body": chunk, "more_body": True}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
    }
    anyio.run(app, scope, receive, send)
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return status, body, consumed


def new_case(client) -> str:
    return client.post("/api/v2/cases").json()["case_id"]


def random_id() -> str:
    return uuid.uuid4().hex
