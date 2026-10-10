from pathlib import Path
import re

from fastapi.testclient import TestClient

import api


def test_local_gemma_routing_prefers_local(monkeypatch):
    client = TestClient(api.app)

    def _write_dummy_audio(text, output_path, language):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"dummy-audio")

    local_payload = {
        "urgency": "medium",
        "reasons": ["Symptoms are stable without red flags"],
        "actions": ["Monitor symptoms and rest"],
        "specialist": "general",
        "confidence": 0.92,
        "doctor_response": "Local triage result.",
    }
    emergency_payload = {
        "urgency": "low",
        "reasons": ["Emergency fallback"],
        "actions": ["Fallback action"],
        "specialist": "general",
        "confidence": 0.4,
        "doctor_response": "Emergency fallback result.",
    }

    def _should_not_run(*args, **kwargs):
        raise AssertionError("Cloud fallback should not run for valid local triage")

    monkeypatch.setattr(api, "text_to_speech_for_api", _write_dummy_audio)
    monkeypatch.setattr(api, "_run_local_gemma_triage", lambda *args, **kwargs: local_payload)
    monkeypatch.setattr(api, "_build_emergency_fallback_triage", lambda *args, **kwargs: emergency_payload)

    response = client.post(
        "/api/get-doctor-response",
        json={
            "patient_text": "Mild headache and sore throat for two days.",
            "language": "en",
            "image_data": [],
            "pdf_data": [],
            "image_count": 0,
            "pdf_count": 0,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["triage_source"] == "local_gemma"
    assert payload["doctor_response"] == "Local triage result."
    assert payload["urgency"] == "medium"
    assert payload["specialist"] == "general"


def test_local_gemma_payload_normalization():
    raw_payload = (
        '{"urgency":"critical","reasons":"single reason","actions":"single action",'
        '"specialist":"general","confidence":"not_a_number","doctor_response":"ok"}'
    )

    payload = api._extract_json_payload(raw_payload)

    assert payload["urgency"] == "high"
    assert payload["reasons"] == ["single reason"]
    assert payload["actions"] == ["single action"]
    assert payload["confidence"] == 0.5


def test_local_gemma_urgency_mapping_for_urgent_and_stable():
    urgent_payload = api._extract_json_payload(
        '{"urgency":"urgent","reasons":["r"],"actions":["a"],'
        '"specialist":"general","confidence":0.7,"doctor_response":"ok"}'
    )
    stable_payload = api._extract_json_payload(
        '{"urgency":"stable","reasons":["r"],"actions":["a"],'
        '"specialist":"general","confidence":0.7,"doctor_response":"ok"}'
    )

    assert urgent_payload["urgency"] == "medium"
    assert stable_payload["urgency"] == "low"


def test_local_gemma_language_fallback_adds_devanagari(monkeypatch):
    client = TestClient(api.app)

    def _write_dummy_audio(text, output_path, language):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"dummy-audio")

    local_payload = {
        "urgency": "medium",
        "reasons": ["Symptoms look stable"],
        "actions": ["Monitor symptoms"],
        "specialist": "general",
        "confidence": 0.9,
        "doctor_response": "This is still in English.",
    }
    emergency_payload = {
        "urgency": "low",
        "reasons": ["Emergency fallback"],
        "actions": ["Fallback action"],
        "specialist": "general",
        "confidence": 0.4,
        "doctor_response": "Emergency fallback result.",
    }

    def _should_not_run(*args, **kwargs):
        raise AssertionError("Cloud fallback should not run for valid local triage")

    monkeypatch.setattr(api, "text_to_speech_for_api", _write_dummy_audio)
    monkeypatch.setattr(api, "_run_local_gemma_triage", lambda *args, **kwargs: local_payload)
    monkeypatch.setattr(api, "_build_emergency_fallback_triage", lambda *args, **kwargs: emergency_payload)

    response = client.post(
        "/api/get-doctor-response",
        json={
            "patient_text": "Light fever and fatigue.",
            "language": "hi",
            "image_data": [],
            "pdf_data": [],
            "image_count": 0,
            "pdf_count": 0,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["triage_source"] == "local_gemma"
    assert re.search(r"[\u0900-\u097F]", payload["doctor_response"])
