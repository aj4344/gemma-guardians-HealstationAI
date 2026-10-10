"""CASE-01, PRIV-03, API-02, API-03: v2 case endpoints, error envelope and headers."""

SENTINEL = "zebra-striped rash village"


def test_create_read_and_erase_case(client, runtime):
    created = client.post("/api/v2/cases", json={"language": "hi", "age": 34, "sex": "female", "area": SENTINEL})
    assert created.status_code == 201
    body = created.json()
    case_id = body["case_id"]
    assert body["pseudonym"].startswith("HS-") and body["language"] == "hi"

    fetched = client.get(f"/api/v2/cases/{case_id}").json()
    assert fetched["area"] == SENTINEL and fetched["age"] == 34

    assert client.delete(f"/api/v2/cases/{case_id}").status_code == 204
    gone = client.get(f"/api/v2/cases/{case_id}")
    assert gone.status_code == 404
    assert gone.json()["error"]["code"] == "NOT_FOUND"
    assert not runtime.blobs.case_dir(case_id).exists()


def test_case_body_is_optional(client):
    assert client.post("/api/v2/cases").status_code == 201


def test_validation_errors_use_the_envelope_without_values(client):
    response = client.post(
        "/api/v2/cases",
        json={"age": 300, "abha_number": "not-a-number", "area": SENTINEL},
        headers={"Accept-Language": "mr"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["retryable"] is False
    assert any("ऀ" <= ch <= "ॿ" for ch in body["error"]["message_localized"])
    assert set(body["fields"]) == {"age", "abha_number"}
    assert SENTINEL not in response.text and "not-a-number" not in response.text
    assert body["request_id"] == response.headers["x-request-id"]


def test_unknown_and_malformed_case_ids_are_not_found(client):
    for case_id in ("0" * 32, "..%2F..%2Fetc%2Fpasswd", "ABC", "a" * 32 + "%00"):
        response = client.get(f"/api/v2/cases/{case_id}")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"


def test_api_responses_carry_no_store_and_security_headers(client):
    response = client.post("/api/v2/cases")
    headers = response.headers
    assert headers["cache-control"] == "no-store"
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["referrer-policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in headers["content-security-policy"]
    assert "http" not in headers["content-security-policy"].replace("'self'", "")
    assert "camera=(self)" in headers["permissions-policy"]
    assert len(headers["x-request-id"]) == 32


def test_client_request_id_is_echoed_only_when_safe(client):
    assert client.get("/api", headers={"X-Request-ID": "abcd-1234-efgh"}).headers["x-request-id"] == "abcd-1234-efgh"
    injected = client.get("/api", headers={"X-Request-ID": "bad\nvalue with spaces"}).headers["x-request-id"]
    assert injected != "bad\nvalue with spaces" and len(injected) == 32


def test_v1_responses_keep_their_shape(client):
    response = client.post("/api/get-doctor-response", json={"patient_text": ""})
    assert response.status_code == 422
    assert "detail" in response.json()
    assert response.headers["cache-control"] == "no-store"


def test_chunked_body_over_the_limit_is_refused(client, monkeypatch):
    from healstation.api import app as app_module

    monkeypatch.setattr(app_module, "MAX_REQUEST_MB", 1)

    def body():
        for _ in range(3):
            yield b"x" * (600 * 1024)

    response = client.post("/api/v2/cases", content=body(), headers={"Content-Type": "application/json"})
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "REQUEST_TOO_LARGE"
