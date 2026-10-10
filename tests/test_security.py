"""Regression tests for security and privacy behaviour."""
import logging

from fastapi.testclient import TestClient

import api

client = TestClient(api.app)
SECRET_SYMPTOM = "zebra-striped rash on my left elbow"


def test_cors_only_allows_configured_origins():
    evil = client.options(
        "/api/get-doctor-response",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in evil.headers

    ui_origin = api.CORS_ALLOW_ORIGINS[0]
    ok = client.options(
        "/api/get-doctor-response",
        headers={
            "Origin": ui_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert ok.headers["access-control-allow-origin"] == ui_origin
    assert "access-control-allow-credentials" not in ok.headers


def test_patient_text_and_model_output_are_not_logged(monkeypatch, caplog):
    class _FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            # Models often echo the symptoms back in their reasoning.
            return {"message": {"content": f'{{"urgency": "low", "reasons": ["{SECRET_SYMPTOM}"]}}'}}

    monkeypatch.setattr(api.requests, "post", lambda *a, **k: _FakeResponse())
    monkeypatch.setattr(api, "LOCAL_TTS_ENABLED", False)

    with caplog.at_level(logging.DEBUG):
        response = client.post("/api/get-doctor-response", json={"patient_text": SECRET_SYMPTOM, "language": "en"})

    assert response.status_code == 200
    assert SECRET_SYMPTOM not in caplog.text


def test_emergency_triage_does_not_log_symptoms(caplog):
    with caplog.at_level(logging.DEBUG):
        response = client.post("/api/emergency-triage", json={"symptoms": SECRET_SYMPTOM})
    assert response.status_code == 200
    assert SECRET_SYMPTOM not in caplog.text


def test_quick_triage_accepts_symptoms_in_body():
    response = client.post("/api/emergency-triage/quick", json={"symptoms": "crushing chest pain"})
    assert response.status_code == 200
    assert response.json()["call_108"] is True


def test_directory_results_do_not_claim_unverified_data():
    response = client.post(
        "/api/search-doctors",
        json={"latitude": 18.5204, "longitude": 73.8567, "specialty": "nephrologist"},
    )
    doctors = response.json()["doctors"]
    assert doctors
    for doctor in doctors:
        assert doctor["verified"] is False
        assert doctor["rating"] is None
        assert doctor["review_count"] is None
        assert doctor["next_available"] == "Contact for appointment"
        assert "Contact" in doctor["consultation_fee"]
        assert isinstance(doctor["distance"], float)


def test_search_errors_do_not_leak_exception_text(monkeypatch):
    async def _boom(**kwargs):
        raise RuntimeError("database password=hunter2")

    monkeypatch.setattr(api, "advanced_search_doctors", _boom)
    response = client.post(
        "/api/search-doctors",
        json={"latitude": 18.5, "longitude": 73.8, "specialty": "cardiologist"},
    )
    assert response.status_code == 200
    assert "hunter2" not in response.text
