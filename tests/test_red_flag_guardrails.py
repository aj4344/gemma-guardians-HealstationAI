from pathlib import Path

from fastapi.testclient import TestClient

import api


def test_trigger_hit_case_returns_emergency_action_block_data():
    red_flag = api._evaluate_red_flag_guardrail("Severe chest pain with sweating and pain radiating to left arm.")

    assert red_flag["apply_guardrail"] is True
    assert "cardiac" in red_flag["matched_categories"]

    block = api._build_emergency_action_block(red_flag)
    assert block["triggered"] is True
    assert block["call_ambulance"] is True
    assert block["time_sensitivity"] == "immediate"


def test_non_trigger_case_does_not_force_emergency_block():
    red_flag = api._evaluate_red_flag_guardrail(
        "Mild runny nose and sore throat for two days without breathing issues."
    )

    assert red_flag["apply_guardrail"] is False
    assert red_flag["matched_categories"] == []


def test_negated_red_flag_phrase_does_not_trigger_guardrail():
    red_flag = api._evaluate_red_flag_guardrail("No chest pain, mild cough for two days.")

    assert red_flag["apply_guardrail"] is False
    assert red_flag["matched_categories"] == []


def test_ambiguous_case_defaults_to_conservative_guidance():
    red_flag = api._evaluate_red_flag_guardrail("Maybe chest tightness, not sure if serious, could be chest pain.")

    assert red_flag["apply_guardrail"] is True
    assert red_flag["ambiguous"] is True
    assert red_flag["confidence"] >= 0.7

    triage = api._build_guardrail_triage(red_flag)
    assert triage["urgency"] == "high"
    assert "Call" in triage["actions"][0]


def test_hindi_red_flag_triggers_guardrail_and_localization():
    red_flag = api._evaluate_red_flag_guardrail("मुझे सीने में दबाव है और बाएं हाथ में दर्द है।")

    assert red_flag["apply_guardrail"] is True
    assert "cardiac" in red_flag["matched_categories"]

    triage = api._build_guardrail_triage(red_flag, language="hi")
    assert triage["urgency"] == "high"
    assert any("108" in action for action in triage["actions"])

    block = api._build_emergency_action_block(red_flag, language="hi")
    assert any("एंबुलेंस" in action or "108" in action for action in block["immediate_actions"])

    response_text = api._compose_guardrail_response_text(red_flag, triage, language="hi")
    assert "आपातकालीन" in response_text


def test_marathi_red_flag_triggers_guardrail_and_localization():
    red_flag = api._evaluate_red_flag_guardrail("छातीत दडपण आहे आणि डाव्या हातात वेदना आहे.")

    assert red_flag["apply_guardrail"] is True
    assert "cardiac" in red_flag["matched_categories"]

    triage = api._build_guardrail_triage(red_flag, language="mr")
    assert triage["urgency"] == "high"
    assert any("108" in action for action in triage["actions"])

    block = api._build_emergency_action_block(red_flag, language="mr")
    assert any("रुग्णवाहिका" in action or "108" in action for action in block["immediate_actions"])

    response_text = api._compose_guardrail_response_text(red_flag, triage, language="mr")
    assert "आपत्कालीन" in response_text


def test_consultation_route_trigger_behavior_returns_emergency_block(monkeypatch):
    client = TestClient(api.app)

    def _write_dummy_audio(text, output_path, language):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"dummy-audio")

    def _should_not_run(*args, **kwargs):
        raise AssertionError("Non-guardrail triage path should not run for trigger-hit case")

    monkeypatch.setattr(api, "text_to_speech_for_api", _write_dummy_audio)
    monkeypatch.setattr(api, "_run_local_gemma_triage", _should_not_run)
    monkeypatch.setattr(api, "_build_emergency_fallback_triage", _should_not_run)

    response = client.post(
        "/api/get-doctor-response",
        json={
            "patient_text": "I have severe chest pain and sweating with left arm pain.",
            "language": "en",
            "image_data": [],
            "pdf_data": [],
            "image_count": 0,
            "pdf_count": 0,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    # Backward-compatible keys remain.
    assert "specialist_recommendation" in payload
    assert "urgency_level" in payload

    # New guardrail behavior.
    assert payload["triage_source"] == "red_flag_guardrail"
    assert payload["urgency"] == "high"
    assert payload["emergency_action_block"] is not None
    assert payload["emergency_action_block"]["triggered"] is True
    assert payload["emergency_action_block"]["call_ambulance"] is True


def test_local_gemma_preferred_when_valid(monkeypatch):
    client = TestClient(api.app)

    local_payload = {
        "urgency": "low",
        "reasons": ["Low-risk symptoms reported."],
        "actions": ["Monitor symptoms and rest."],
        "specialist": "general",
        "confidence": 0.92,
        "doctor_response": "Local Gemma summary response.",
    }

    monkeypatch.setattr(api, "_run_local_gemma_triage", lambda *args, **kwargs: local_payload)
    monkeypatch.setattr(
        api,
        "_build_emergency_fallback_triage",
        lambda *args, **kwargs: {
            "urgency": "high",
            "reasons": ["Fallback triggered."],
            "actions": ["Seek emergency care."],
            "specialist": "emergency medicine",
            "confidence": 0.2,
            "doctor_response": "Emergency fallback response.",
        },
    )
    monkeypatch.setattr(api, "text_to_speech_for_api", lambda *args, **kwargs: None)

    response = client.post(
        "/api/get-doctor-response",
        json={
            "patient_text": "Mild cough and sore throat for two days.",
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
    assert payload["doctor_response"] == "Local Gemma summary response."


def test_tts_disabled_skips_audio_generation(monkeypatch):
    client = TestClient(api.app)

    monkeypatch.setattr(api, "LOCAL_TTS_ENABLED", False)

    local_payload = {
        "urgency": "medium",
        "reasons": ["Symptoms appear moderate."],
        "actions": ["Schedule a routine visit."],
        "specialist": "general",
        "confidence": 0.91,
        "doctor_response": "",
    }

    monkeypatch.setattr(api, "_run_local_gemma_triage", lambda *args, **kwargs: local_payload)
    monkeypatch.setattr(api, "_build_emergency_fallback_triage", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        api,
        "text_to_speech_for_api",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("TTS should not run when LOCAL_TTS_ENABLED is false")
        ),
    )

    response = client.post(
        "/api/get-doctor-response",
        json={
            "patient_text": "Moderate headache and mild nausea.",
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
    assert payload["audio_url"] is None
    assert "MEDIUM urgency" in payload["doctor_response"]
