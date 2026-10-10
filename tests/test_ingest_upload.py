"""ING-01..07: streaming uploads into the encrypted quarantine."""

import json
import resource
import sys
import tracemalloc

import pytest
from sqlalchemy import select

import api
from healstation.ingest.filetypes import TypeRejected, check_tail, detect
from healstation.store.models import Attachment
from tests.helpers import BOUNDARY, jpeg_bytes, minimal_pdf, multipart_parts, new_case, png_bytes, run_asgi, upload

MB = 1024 * 1024


def _all_files(runtime):
    return [p for p in runtime.blobs.cases_dir.rglob("*") if p.is_file()]


def _attachment_rows(runtime):
    with runtime.db.session() as session:
        return list(session.scalars(select(Attachment)).all())


def test_upload_is_quarantined_encrypted_and_reported_without_filename(client, runtime):
    case_id = new_case(client)
    data = png_bytes()
    response = upload(client, case_id, data, filename="Ramesh-Kumar-xray.png")
    assert response.status_code == 202
    body = response.json()
    assert body["stage"] == "QUARANTINED" and body["kind"] == "image" and body["detected_type"] == "png"
    assert "Ramesh" not in response.text

    status = client.get(f"/api/v2/cases/{case_id}/attachments/{body['attachment_id']}")
    assert status.status_code == 200 and "Ramesh" not in status.text
    listing = client.get(f"/api/v2/cases/{case_id}/attachments").json()["attachments"]
    assert [a["attachment_id"] for a in listing] == [body["attachment_id"]]

    files = _all_files(runtime)
    assert len(files) == 1 and data not in files[0].read_bytes()


@pytest.mark.parametrize("filename", ["../../etc/x.png", "CON.png", "a\x00b.png", "..\\..\\boot.ini.png", "स्कैन.png"])
def test_hostile_filenames_are_stored_safely(client, runtime, filename):
    case_id = new_case(client)
    response = upload(client, case_id, png_bytes(), filename=filename)
    assert response.status_code == 202
    files = _all_files(runtime)
    assert len(files) == 1
    assert files[0].parent == runtime.blobs.case_dir(case_id)
    assert files[0].name.endswith(".hse") and len(files[0].stem) == 32
    row = _attachment_rows(runtime)[0]
    stored = runtime.cases.sealer(case_id).open_text("attachments.original_name", row.id, row.original_name_enc)
    assert "/" not in stored and "\\" not in stored and "\x00" not in stored


@pytest.mark.parametrize(
    "data, filename, content_type, code",
    [
        (b"MZ\x90\x00" + b"\x00" * 200, "report.pdf", "application/pdf", "UNSUPPORTED_TYPE"),  # renamed .exe
        (jpeg_bytes(), "report.pdf", "application/pdf", "TYPE_MISMATCH"),
        (jpeg_bytes(), "photo.jpg", "application/pdf", "TYPE_MISMATCH"),
        (jpeg_bytes(), "photo.pdf", "image/jpeg", "TYPE_MISMATCH"),
        (jpeg_bytes()[:20] + b"%PDF-1.4" + jpeg_bytes()[20:], "photo.jpg", "image/jpeg", "POLYGLOT_FILE"),
        (
            b"\x1a\x45\xdf\xa3" + b"\x00" * 100,
            "voice.webm",
            "audio/webm",
            "UNSUPPORTED_TYPE",
        ),  # audio is not an attachment
    ],
)
def test_type_detection_rejects_and_leaves_no_residue(client, runtime, data, filename, content_type, code):
    case_id = new_case(client)
    response = upload(client, case_id, data, filename=filename, content_type=content_type)
    assert response.status_code == 415
    assert response.json()["error"]["code"] == code
    assert _all_files(runtime) == [] and _attachment_rows(runtime) == []


def test_generic_mime_and_missing_extension_are_accepted(client):
    case_id = new_case(client)
    response = upload(client, case_id, jpeg_bytes(), filename="IMG_0001", content_type="application/octet-stream")
    assert response.status_code == 202 and response.json()["detected_type"] == "jpeg"


def test_oversize_upload_is_refused_before_the_body_is_read(runtime):
    runtime.settings.max_image_bytes = 64 * 1024
    from fastapi.testclient import TestClient

    case_id = new_case(TestClient(api.app))
    head, tail = multipart_parts("big.png", "image/png")
    chunk = b"\x00" * (16 * 1024)
    chunks = [head + png_bytes()[:32] + chunk[32:], *([chunk] * 200), tail]  # ~3.2 MB in total
    status, body, consumed = run_asgi(
        api.app,
        "POST",
        f"/api/v2/cases/{case_id}/attachments",
        chunks,
        {"content-type": f"multipart/form-data; boundary={BOUNDARY}"},
    )
    assert status == 413 and json.loads(body)["error"]["code"] == "FILE_TOO_LARGE"
    assert consumed < 10, f"read {consumed} of {len(chunks)} chunks"
    assert _all_files(runtime) == [] and _attachment_rows(runtime) == []


def test_declared_length_over_the_limit_is_refused_immediately(runtime):
    runtime.settings.max_image_bytes = 64 * 1024
    from fastapi.testclient import TestClient

    case_id = new_case(TestClient(api.app))
    head, tail = multipart_parts("big.png", "image/png")
    status, body, consumed = run_asgi(
        api.app,
        "POST",
        f"/api/v2/cases/{case_id}/attachments",
        [head + png_bytes() + b"\x00" * 2048, b"\x00" * 1024, tail],
        {"content-type": f"multipart/form-data; boundary={BOUNDARY}", "content-length": str(5 * MB)},
    )
    assert status == 413 and json.loads(body)["error"]["code"] == "FILE_TOO_LARGE"
    assert consumed <= 1


def test_same_file_twice_returns_the_existing_attachment(client, runtime):
    case_id = new_case(client)
    first = upload(client, case_id, png_bytes())
    second = upload(client, case_id, png_bytes(), filename="again.png")
    assert first.status_code == 202 and second.status_code == 200
    assert second.json()["duplicate"] is True
    assert second.json()["attachment_id"] == first.json()["attachment_id"]
    assert len(_all_files(runtime)) == 1


def test_duplicate_digest_is_keyed_per_installation(runtime):
    from healstation.store.crypto import new_key
    from healstation.store.keys import KeyService

    data = png_bytes()
    assert runtime.keys.content_digest(data) != KeyService(new_key()).content_digest(data)


def test_delete_attachment_removes_its_files(client, runtime):
    case_id = new_case(client)
    attachment_id = upload(client, case_id, png_bytes()).json()["attachment_id"]
    assert client.delete(f"/api/v2/cases/{case_id}/attachments/{attachment_id}").status_code == 204
    assert client.get(f"/api/v2/cases/{case_id}/attachments/{attachment_id}").status_code == 404
    assert _all_files(runtime) == []


def test_attachment_count_limit(client, runtime):
    runtime.settings.max_attachments_per_case = 2
    case_id = new_case(client)
    for color in ((1, 1, 1), (2, 2, 2)):
        assert upload(client, case_id, png_bytes(color=color)).status_code == 202
    third = upload(client, case_id, png_bytes(color=(3, 3, 3)))
    assert third.status_code == 409 and third.json()["error"]["code"] == "TOO_MANY_ATTACHMENTS"


def test_storage_quota_is_enforced(client, runtime):
    runtime.settings.storage_quota_bytes = 1
    case_id = new_case(client)
    response = upload(client, case_id, png_bytes())
    assert response.status_code == 507 and response.json()["error"]["code"] == "STORAGE_FULL"
    assert _all_files(runtime) == []


def test_malformed_multipart_requests(client):
    case_id = new_case(client)
    url = f"/api/v2/cases/{case_id}/attachments"
    multipart = {"Content-Type": f"multipart/form-data; boundary={BOUNDARY}"}
    empty = upload(client, case_id, b"")
    assert empty.status_code == 400 and empty.json()["error"]["code"] == "EMPTY_FILE"
    no_file = client.post(url, content=f"--{BOUNDARY}--\r\n".encode(), headers=multipart)
    assert no_file.json()["error"]["code"] == "NO_FILE"
    head1, _ = multipart_parts("a.png", "image/png")
    head2, tail = multipart_parts("b.png", "image/png")
    two = client.post(url, content=head1 + png_bytes() + b"\r\n" + head2 + png_bytes() + tail, headers=multipart)
    assert two.json()["error"]["code"] == "MULTIPLE_FILES"
    not_multipart = client.post(url, content=png_bytes(), headers={"Content-Type": "image/png"})
    assert not_multipart.json()["error"]["code"] == "BAD_REQUEST"


def test_upload_to_unknown_case_is_not_found(client):
    response = upload(client, "0" * 32, png_bytes())
    assert response.status_code == 404


@pytest.mark.skipif(sys.platform == "win32", reason="ru_maxrss is Unix-only")
def test_300mb_upload_streams_with_bounded_memory(runtime):
    """ING-01: a 300 MB series upload keeps memory growth far below 50 MB."""
    from fastapi.testclient import TestClient

    case_id = new_case(TestClient(api.app))
    head, tail = multipart_parts("series.zip", "application/zip")
    block = bytes(range(256)) * 4096  # 1 MiB, reused: the test itself allocates nothing per chunk

    def chunks():
        yield head + b"PK\x03\x04" + block[4:]
        for _ in range(299):
            yield block
        yield tail

    rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    tracemalloc.start()
    status, body, _consumed = run_asgi(
        api.app,
        "POST",
        f"/api/v2/cases/{case_id}/attachments",
        chunks(),
        {"content-type": f"multipart/form-data; boundary={BOUNDARY}"},
    )
    _current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    rss_growth_mb = (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss - rss_before) / 1024
    assert status == 202, body
    assert peak < 16 * MB, f"Python allocations peaked at {peak / MB:.1f} MB"
    assert rss_growth_mb < 50, f"RSS grew {rss_growth_mb:.1f} MB"
    assert runtime.blobs.usage_bytes() > 300 * MB


def test_detect_and_tail_checks():
    assert detect(minimal_pdf(), "application/pdf", "lab.pdf", {"pdf"}).kind == "pdf"
    with pytest.raises(TypeRejected) as hidden_zip:
        check_tail(detect(jpeg_bytes(), "image/jpeg", "x.jpg", {"image"}), jpeg_bytes() + b"PK\x05\x06" + b"\x00" * 18)
    assert hidden_zip.value.code == "POLYGLOT_FILE"
    with pytest.raises(TypeRejected) as truncated:
        check_tail(detect(minimal_pdf(), None, None, {"pdf"}), minimal_pdf()[:-10])
    assert truncated.value.code == "CORRUPT_FILE"
