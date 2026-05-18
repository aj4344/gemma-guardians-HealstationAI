from pathlib import Path

from fastapi.testclient import TestClient

import api


def test_consensus_aligned_signals_no_conflict():
    result = api._build_consensus_explanation(
        patient_text="mild headache",
        typed_text="mild headache",
        transcription_text="mild headache",
        image_data=[],
        pdf_data=[],
        final_urgency="low",
    )

    assert result["conflict"] is False
    assert "signals aligned" in result["resolution_reason"].lower()


def test_consensus_conflicting_signals():
    result = api._build_consensus_explanation(
        patient_text="mild headache",
        typed_text="mild headache",
        transcription_text="severe chest pain and shortness of breath",
        image_data=[],
        pdf_data=[],
        final_urgency="high",
    )

    assert result["conflict"] is True
    assert "conflicting signals" in result["resolution_reason"].lower()


def test_consensus_missing_modality_fallback():
    result = api._build_consensus_explanation(
        patient_text="mild headache",
        typed_text=None,
        transcription_text=None,
        image_data=[],
        pdf_data=[],
        final_urgency="low",
    )

    assert result["conflict"] is False
    assert "limited inputs" in result["resolution_reason"].lower()


def test_api_response_includes_consensus_block(monkeypatch):
    client = TestClient(api.app)

    def _write_dummy_audio(text, output_path, language):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"dummy-audio")

    local_payload = {
        "urgency": "low",
        "reasons": ["Mild symptoms reported"],
        "actions": ["Rest and monitor"],
        "specialist": "general",
        "confidence": 0.9,
        "doctor_response": "Local triage result.",
    }
    emergency_payload = {
        "urgency": "medium",
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
    monkeypatch.setattr(api, "get_doctor_response", _should_not_run)

    response = client.post(
        "/api/get-doctor-response",
        json={
            "patient_text": "Mild headache for two days.",
            "typed_text": "Mild headache for two days.",
            "transcription_text": "Mild headache for two days.",
            "language": "en",
            "image_data": [],
            "pdf_data": [],
            "image_count": 0,
            "pdf_count": 0,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert "consensus_explanation" in payload
    assert payload["consensus_explanation"]["conflict"] is False
    assert "signals" in payload["consensus_explanation"]
