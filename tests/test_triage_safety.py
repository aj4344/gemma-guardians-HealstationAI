"""Regression tests for clinical-safety behaviour of the consultation pipeline."""
import ast
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import api
from emergency_triage.offline_triage_engine import select_offline_first_triage

API_SOURCE = Path(api.__file__)


def _stub_tts(monkeypatch):
    monkeypatch.setattr(api, "text_to_speech_for_api", lambda *args, **kwargs: None)


def test_api_has_no_duplicate_top_level_functions():
    # A second definition silently replaces the first; this is how the
    # hardened red-flag guardrail was once lost.
    tree = ast.parse(API_SOURCE.read_text(encoding="utf-8"))
    names = [node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    duplicates = {name for name in names if names.count(name) > 1}
    assert duplicates == set()


@pytest.mark.parametrize(
    "text, category",
    [
        ("I have pain in my heart since morning", "cardiac"),
        ("my chest hurts when I walk", "cardiac"),
        ("दिल में दर्द हो रहा है", "cardiac"),
        ("छातीत दडपण आहे", "cardiac"),
        ("I can't breathe properly", "breathing_distress"),
        ("सांस लेने में तकलीफ है", "breathing_distress"),
        ("श्वास घेता येत नाही", "breathing_distress"),
        ("her face is drooping and speech is slurred", "stroke"),
        ("he collapsed and is unresponsive", "unconscious"),
        ("my son is having a seizure", "seizure"),
        ("throat is closing after a bee sting", "anaphylaxis"),
        ("I want to kill myself", "self_harm"),
    ],
)
def test_red_flags_detected(text, category):
    red_flag = api._evaluate_red_flag_guardrail(text)
    assert red_flag["apply_guardrail"] is True
    assert category in red_flag["matched_categories"]


@pytest.mark.parametrize(
    "text",
    [
        "Worried about potential side effects of my new tablets.",  # "tia" inside a word
        "Heartburn after eating spicy food.",
        "Blood pressure check done, chest clear, mild cough.",
        "No chest pain, mild cough for two days.",
        "Denies shortness of breath; runny nose since yesterday.",
        "Mild headache for two days.",
    ],
)
def test_red_flags_not_triggered_by_benign_text(text):
    red_flag = api._evaluate_red_flag_guardrail(text)
    assert red_flag["apply_guardrail"] is False, red_flag["matched_keywords"]


def test_self_harm_block_includes_mental_health_helpline():
    red_flag = api._evaluate_red_flag_guardrail("I took steps to end my life")
    block = api._build_emergency_action_block(red_flag, "en")
    assert "mental_health" in block["emergency_numbers"]
    assert any(block["emergency_numbers"]["mental_health"] in action for action in block["immediate_actions"])


def test_vitals_parser_accepts_ui_placeholder_format():
    vitals = api._parse_vital_signs_from_text(
        "Fever.\n\n[Vital Signs]: BP: 140/90, Heart Rate: 85 bpm, Temp: 101°F, Oxygen: 96%"
    )
    assert vitals == {
        "heart_rate": 85,
        "bp_systolic": 140,
        "bp_diastolic": 90,
        "spo2": 96,
        "temperature": 38.3,
    }


def test_vitals_parser_long_form_and_celsius():
    vitals = api._parse_vital_signs_from_text(
        "Blood Pressure: 120/80, Oxygen Saturation: 97, Temperature: 37.2 C"
    )
    assert vitals["bp_systolic"] == 120
    assert vitals["spo2"] == 97
    assert vitals["temperature"] == 37.2


def test_rules_fallback_survives_extreme_vitals():
    # SpO2 45% and HR 25 are outside the VitalSigns model range; they used to
    # raise, drop the fallback and default the patient to "low".
    result = api._build_emergency_fallback_triage("feeling weak and dizzy", "en", heart_rate=25, spo2=45)
    assert result is not None
    assert result["urgency"] in {"critical", "emergency"}


def test_unknown_model_urgency_is_not_trusted():
    local = {
        "urgency": "unclear",
        "reasons": ["r"],
        "actions": ["a"],
        "specialist": "general",
        "confidence": 0.95,
    }
    fallback = {"urgency": "urgent", "reasons": ["rules"], "actions": ["go"], "specialist": "general", "confidence": 0.7}
    triage, source = select_offline_first_triage(local, fallback, confidence_threshold=0.6)
    assert source == "emergency_fallback"


def test_model_payload_with_unknown_urgency_is_flagged():
    payload = api._extract_json_payload(
        '{"urgency":"HIGH | MEDIUM | LOW","reasons":["r"],"actions":["a"],'
        '"specialist":"general","confidence":0.9,"doctor_response":"ok"}'
    )
    assert payload["urgency"] is None


def test_no_triage_source_never_reports_low():
    triage, source = select_offline_first_triage(None, None, confidence_threshold=0.6)
    assert source == "unassessed"
    assert triage["urgency"] != "low"


def test_critical_vitals_floor_overrides_low_model_urgency(monkeypatch):
    _stub_tts(monkeypatch)
    monkeypatch.setattr(api, "_run_local_gemma_triage", lambda *args, **kwargs: {
        "urgency": "low",
        "reasons": ["Mild headache"],
        "actions": ["Rest"],
        "specialist": "general",
        "confidence": 0.95,
        "doctor_response": "URGENCY: LOW",
    })

    response = TestClient(api.app).post(
        "/api/get-doctor-response",
        json={"patient_text": "Mild headache.\n\n[Vital Signs]: Oxygen: 82%", "language": "en"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["urgency"] == "high"
    assert payload["emergency_action_block"]["type"] == "critical_vitals"
    assert any("Oxygen saturation" in reason for reason in payload["reasons"])
    assert payload["doctor_response"].startswith("Emergency safety alert")


def test_unexpected_error_returns_503_without_internals(monkeypatch):
    def _boom(*args, **kwargs):
        raise RuntimeError("secret internal detail /srv/models")

    monkeypatch.setattr(api, "_evaluate_toxin_fast_lane", _boom)

    response = TestClient(api.app).post(
        "/api/get-doctor-response",
        json={"patient_text": "Mild headache.", "language": "hi"},
    )

    assert response.status_code == 503
    body = response.text
    assert "secret" not in body
    assert "108" in response.json()["detail"]
