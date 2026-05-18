from pathlib import Path

from fastapi.testclient import TestClient
import pytest

import api
from emergency_triage.fairness_engine import FairnessTracker


def _record_case(tracker, age, gender, language, is_correct, confidence):
    tracker.record_case(
        age=age,
        gender=gender,
        language=language,
        is_correct=is_correct,
        confidence=confidence,
    )


def _stub_consultation_dependencies(monkeypatch):
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


def test_age_group_accuracy_buckets_match_required_ranges():
    tracker = FairnessTracker(parity_threshold=0.05)
    _record_case(tracker, 10, "male", "en", True, 0.9)
    _record_case(tracker, 40, "female", "es", False, 0.8)
    _record_case(tracker, 70, "other", "fr", True, 0.7)

    metrics = tracker.get_metrics()
    assert metrics["group_accuracy"]["age"]["0-18"] == 1.0
    assert metrics["group_accuracy"]["age"]["19-65"] == 0.0
    assert metrics["group_accuracy"]["age"]["65+"] == 1.0


def test_gender_group_normalization_maps_to_male_female_other():
    tracker = FairnessTracker(parity_threshold=0.05)
    _record_case(tracker, 20, "M", "en", True, 0.7)
    _record_case(tracker, 21, "F", "en", False, 0.7)
    _record_case(tracker, 22, "non-binary", "en", True, 0.7)

    metrics = tracker.get_metrics()
    assert metrics["group_accuracy"]["gender"]["male"] == 1.0
    assert metrics["group_accuracy"]["gender"]["female"] == 0.0
    assert metrics["group_accuracy"]["gender"]["other"] == 1.0


def test_language_group_normalization_tracks_english_spanish_french_mandarin():
    tracker = FairnessTracker(parity_threshold=0.05)
    _record_case(tracker, 20, "male", "english", True, 0.9)
    _record_case(tracker, 20, "male", "es", True, 0.9)
    _record_case(tracker, 20, "male", "fr", True, 0.9)
    _record_case(tracker, 20, "male", "mandarin", True, 0.9)

    metrics = tracker.get_metrics()
    assert metrics["group_accuracy"]["language"]["English"] == 1.0
    assert metrics["group_accuracy"]["language"]["Spanish"] == 1.0
    assert metrics["group_accuracy"]["language"]["French"] == 1.0
    assert metrics["group_accuracy"]["language"]["Mandarin"] == 1.0


def test_confidence_parity_reports_average_confidence_per_group():
    tracker = FairnessTracker(parity_threshold=0.05)
    _record_case(tracker, 10, "male", "en", True, 0.90)
    _record_case(tracker, 14, "male", "en", True, 0.80)
    _record_case(tracker, 40, "female", "es", True, 0.50)
    _record_case(tracker, 70, "other", "fr", True, 0.70)

    metrics = tracker.get_metrics()
    assert metrics["confidence_parity"]["age"]["0-18"] == pytest.approx(0.85)
    assert metrics["confidence_parity"]["age"]["19-65"] == 0.50
    assert metrics["confidence_parity"]["age"]["65+"] == 0.70


def test_parity_detection_flags_review_when_gap_exceeds_5_percent():
    tracker = FairnessTracker(parity_threshold=0.05)
    _record_case(tracker, 10, "male", "en", True, 0.9)
    _record_case(tracker, 16, "male", "en", True, 0.9)
    _record_case(tracker, 30, "female", "es", False, 0.9)
    _record_case(tracker, 40, "female", "es", False, 0.9)
    _record_case(tracker, 70, "other", "fr", True, 0.9)
    _record_case(tracker, 72, "other", "zh", True, 0.9)

    metrics = tracker.get_metrics()
    assert metrics["parity_score"] > 0.05
    assert metrics["fairness_status"] == "Review"


def test_fairness_status_is_fair_when_all_groups_within_5_percent():
    tracker = FairnessTracker(parity_threshold=0.05)
    _record_case(tracker, 12, "male", "en", True, 0.80)
    _record_case(tracker, 14, "male", "en", True, 0.81)
    _record_case(tracker, 30, "female", "es", True, 0.79)
    _record_case(tracker, 45, "female", "es", True, 0.80)
    _record_case(tracker, 70, "other", "fr", True, 0.80)
    _record_case(tracker, 72, "other", "zh", True, 0.79)

    metrics = tracker.get_metrics()
    assert metrics["parity_score"] <= 0.05
    assert metrics["fairness_status"] == "Fair"


def test_tracker_reset_clears_all_counters():
    tracker = FairnessTracker(parity_threshold=0.05)
    _record_case(tracker, 10, "male", "en", True, 0.9)
    tracker.reset()

    metrics = tracker.get_metrics()
    assert metrics["samples_seen"] == 0
    assert metrics["group_accuracy"]["age"]["0-18"] is None
    assert metrics["confidence_parity"]["language"]["English"] is None


def test_api_response_includes_fairness_metrics(monkeypatch):
    client = TestClient(api.app)
    api.fairness_tracker.reset()
    _stub_consultation_dependencies(monkeypatch)

    response = client.post(
        "/api/get-doctor-response",
        json={
            "patient_text": "Mild headache for two days.",
            "language": "en",
            "age": 30,
            "gender": "female",
            "triage_correct": True,
            "image_data": [],
            "pdf_data": [],
            "image_count": 0,
            "pdf_count": 0,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert all(key in payload for key in ["urgency", "reasons", "actions", "specialist", "confidence"])
    assert "fairness_metrics" in payload
    assert "parity_score" in payload["fairness_metrics"]
    assert "group_accuracy" in payload["fairness_metrics"]
    assert "confidence_parity" in payload["fairness_metrics"]
    assert "fairness_status" in payload["fairness_metrics"]


def test_backward_compatibility_when_demographics_missing(monkeypatch):
    client = TestClient(api.app)
    api.fairness_tracker.reset()
    _stub_consultation_dependencies(monkeypatch)

    response = client.post(
        "/api/get-doctor-response",
        json={
            "patient_text": "Mild headache for two days.",
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
    assert all(key in payload for key in ["urgency", "reasons", "actions", "specialist", "confidence"])
    assert "fairness_metrics" in payload
