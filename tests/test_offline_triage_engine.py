from emergency_triage.offline_triage_engine import select_offline_first_triage


def test_local_success_case_uses_local_output():
    local_payload = {
        "urgency": "high",
        "reasons": ["Severe chest pain with sweating"],
        "actions": ["Call 108 immediately"],
        "specialist": "cardiologist",
        "confidence": 0.92,
    }
    emergency_payload = {
        "urgency": "medium",
        "reasons": ["Fallback reason"],
        "actions": ["Fallback action"],
        "specialist": "general",
        "confidence": 0.7,
    }

    triage, source = select_offline_first_triage(
        local_payload=local_payload,
        emergency_payload=emergency_payload,
        confidence_threshold=0.6,
    )

    assert source == "local_gemma"
    assert triage["urgency"] == "high"
    assert triage["specialist"] == "cardiologist"


def test_malformed_local_output_falls_back_to_emergency():
    local_payload = {
        "urgency": "high",
        # Missing canonical fields expected from local model output
        "confidence": "not_a_number",
    }
    emergency_payload = {
        "urgency": "medium",
        "reasons": ["Emergency classifier detected moderate risk"],
        "actions": ["Visit emergency room"],
        "specialist": "general",
        "confidence": 0.73,
    }

    triage, source = select_offline_first_triage(
        local_payload=local_payload,
        emergency_payload=emergency_payload,
        confidence_threshold=0.6,
    )

    assert source == "emergency_fallback"
    assert triage["urgency"] == "medium"
    assert triage["reasons"] == ["Emergency classifier detected moderate risk"]


def test_low_confidence_local_output_falls_back_to_emergency():
    local_payload = {
        "urgency": "high",
        "reasons": ["Possible emergency"],
        "actions": ["Call ambulance"],
        "specialist": "cardiologist",
        "confidence": 0.21,
    }
    emergency_payload = {
        "urgency": "low",
        "reasons": ["No critical signs from emergency scoring"],
        "actions": ["Schedule clinic visit"],
        "specialist": "general",
        "confidence": 0.8,
    }

    triage, source = select_offline_first_triage(
        local_payload=local_payload,
        emergency_payload=emergency_payload,
        confidence_threshold=0.6,
    )

    assert source == "emergency_fallback"
    assert triage["urgency"] == "low"
    assert triage["actions"] == ["Schedule clinic visit"]
