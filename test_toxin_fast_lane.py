from pathlib import Path

from fastapi.testclient import TestClient

import api


def test_trigger_hit_case_returns_toxin_fast_lane_block_data():
    toxin_flag = api._evaluate_toxin_fast_lane(
        "I drank bleach by mistake and now I feel sick."
    )

    assert toxin_flag["apply_fast_lane"] is True
    assert "ingestion" in toxin_flag["matched_categories"]

    triage = api._build_toxin_fast_lane_triage(toxin_flag)
    assert triage["urgency"] == "high"
    assert triage["specialist"] == "emergency medicine"

    block = api._build_toxin_emergency_action_block(toxin_flag)
    assert block["type"] == "toxin_fast_lane"
    assert block["triggered"] is True
    assert block["call_ambulance"] is True
    assert any("Do not induce vomiting" in action for action in block["immediate_actions"])


def test_bleach_ingestion_phrase_triggers_toxin_fast_lane():
    toxin_flag = api._evaluate_toxin_fast_lane(
        "Bleach ingestion about 10 minutes ago."
    )

    assert toxin_flag["apply_fast_lane"] is True
    assert "ingestion" in toxin_flag["matched_categories"]


def test_non_trigger_case_does_not_force_toxin_fast_lane():
    toxin_flag = api._evaluate_toxin_fast_lane(
        "Mild runny nose and sore throat for two days without exposure to chemicals."
    )

    assert toxin_flag["apply_fast_lane"] is False
    assert toxin_flag["matched_categories"] == []


def test_ambiguous_toxin_case_defaults_to_conservative_guidance():
    toxin_flag = api._evaluate_toxin_fast_lane(
        "Maybe I inhaled some gas leak fumes, not sure if it was toxic."
    )

    assert toxin_flag["apply_fast_lane"] is True
    assert toxin_flag["ambiguous"] is True
    assert toxin_flag["confidence"] >= 0.78

    triage = api._build_toxin_fast_lane_triage(toxin_flag)
    assert triage["urgency"] == "high"
    assert "Call" in triage["actions"][0]


def test_hindi_toxin_phrase_triggers_fast_lane_and_localization():
    toxin_flag = api._evaluate_toxin_fast_lane(
        "मैंने गलती से ब्लीच पी लिया है और गला जल रहा है।"
    )

    assert toxin_flag["apply_fast_lane"] is True
    assert "ingestion" in toxin_flag["matched_categories"]

    triage = api._build_toxin_fast_lane_triage(toxin_flag, language="hi")
    assert triage["urgency"] == "high"
    assert any("उल्टी" in action for action in triage["actions"])

    block = api._build_toxin_emergency_action_block(toxin_flag, language="hi")
    assert any("उल्टी" in action for action in block["immediate_actions"])

    response_text = api._compose_toxin_response_text(toxin_flag, triage, language="hi")
    assert "आपातकालीन" in response_text


def test_marathi_toxin_phrase_triggers_fast_lane_and_localization():
    toxin_flag = api._evaluate_toxin_fast_lane(
        "मी चुकून ब्लीच पिले आणि घसा जळत आहे."
    )

    assert toxin_flag["apply_fast_lane"] is True
    assert "ingestion" in toxin_flag["matched_categories"]

    triage = api._build_toxin_fast_lane_triage(toxin_flag, language="mr")
    assert triage["urgency"] == "high"
    assert any("उलटी" in action for action in triage["actions"])

    block = api._build_toxin_emergency_action_block(toxin_flag, language="mr")
    assert any("उलटी" in action for action in block["immediate_actions"])

    response_text = api._compose_toxin_response_text(toxin_flag, triage, language="mr")
    assert "आपत्कालीन" in response_text


def test_consultation_route_trigger_behavior_returns_toxin_fast_lane(monkeypatch):
    client = TestClient(api.app)

    def _write_dummy_audio(text, output_path, language):
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_bytes(b"dummy-audio")

    def _should_not_run(*args, **kwargs):
        raise AssertionError("Non-toxin paths should not run for toxin fast-lane case")

    monkeypatch.setattr(api, "text_to_speech_for_api", _write_dummy_audio)
    monkeypatch.setattr(api, "_evaluate_red_flag_guardrail", _should_not_run)
    monkeypatch.setattr(api, "_run_local_gemma_triage", _should_not_run)
    monkeypatch.setattr(api, "_build_emergency_fallback_triage", _should_not_run)

    response = client.post(
        "/api/get-doctor-response",
        json={
            "patient_text": "I accidentally drank bleach and now my throat burns.",
            "language": "en",
            "image_data": [],
            "pdf_data": [],
            "image_count": 0,
            "pdf_count": 0,
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert "specialist_recommendation" in payload
    assert "urgency_level" in payload
    assert payload["triage_source"] == "toxin_fast_lane"
    assert payload["urgency"] == "high"
    assert payload["emergency_action_block"] is not None
    assert payload["emergency_action_block"]["triggered"] is True
    assert payload["emergency_action_block"]["call_ambulance"] is True