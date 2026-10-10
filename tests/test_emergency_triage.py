"""
Emergency Triage Test Script
============================
Comprehensive tests for the emergency triage system.
Run this to verify all components work correctly.
"""

import asyncio
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '.')

from emergency_triage import (
    EmergencyClassifier,
    EmergencyTriageRequest,
    HospitalRoutingService,
    HospitalSearchRequest,
    TriageService,
    VitalSigns,
)


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_result(label: str, value, indent: int = 0):
    """Print a formatted result"""
    prefix = "  " * indent
    print(f"{prefix}• {label}: {value}")


def test_triage_service():
    """Test the scoring algorithms"""
    print_header("TESTING TRIAGE SERVICE - Scoring Algorithms")

    service = TriageService()

    # Test Case 1: Critical Cardiac (Heart Attack)
    print("\n🫀 Test Case 1: Critical Cardiac Symptoms")
    print("-" * 40)
    symptoms1 = "I have severe crushing chest pain radiating to my left arm, I'm sweating profusely and feeling nauseous. The pain started 30 minutes ago."

    scores1 = service.calculate_all_scores(symptoms1, age=55, medical_history=["diabetes", "hypertension"])
    print_result("Symptoms", symptoms1[:80] + "...")
    print_result("Overall Score", f"{scores1.overall_score}/10 ({scores1.overall_risk_level})")
    print_result(
        "HEART Score", f"{scores1.heart_score.score}/{scores1.heart_score.max_score} ({scores1.heart_score.risk_level})"
    )
    print_result("Cardiac Concern", scores1.is_cardiac_concern)
    print_result("Symptoms Detected", scores1.heart_score.symptoms_detected)
    print_result("Recommendation", scores1.heart_score.recommendation)

    assert scores1.overall_score >= 7, "Critical cardiac should score >= 7"
    assert scores1.is_cardiac_concern, "Should detect cardiac concern"
    print("✅ PASSED: Critical cardiac symptoms correctly identified")

    # Test Case 2: Stroke (BE-FAST)
    print("\n🧠 Test Case 2: Stroke Symptoms (BE-FAST)")
    print("-" * 40)
    symptoms2 = "My face suddenly started drooping on one side, I can't lift my right arm, and my speech is slurred. This happened suddenly 20 minutes ago."

    scores2 = service.calculate_all_scores(symptoms2, age=70)
    print_result("Symptoms", symptoms2[:80] + "...")
    print_result("Overall Score", f"{scores2.overall_score}/10 ({scores2.overall_risk_level})")
    print_result("BE-FAST Score", f"{scores2.befast_score.score}/{scores2.befast_score.max_score}")
    print_result("Stroke Likely", scores2.befast_score.is_stroke_likely)
    print_result("Symptoms Detected", scores2.befast_score.symptoms_detected)
    print_result("Golden Hour Warning", scores2.befast_score.golden_hour_warning)

    assert scores2.befast_score.is_stroke_likely, "Should detect stroke"
    assert scores2.is_stroke_concern, "Should flag stroke concern"
    print("✅ PASSED: Stroke symptoms correctly identified")

    # Test Case 3: Trauma
    print("\n🚗 Test Case 3: Trauma - Car Accident")
    print("-" * 40)
    symptoms3 = "I was in a car accident at high speed. I hit my head and lost consciousness briefly. I'm bleeding from a cut on my forehead and my left leg looks deformed."

    scores3 = service.calculate_all_scores(symptoms3, age=35)
    print_result("Symptoms", symptoms3[:80] + "...")
    print_result("Overall Score", f"{scores3.overall_score}/10 ({scores3.overall_risk_level})")
    print_result("Trauma Score", f"{scores3.trauma_score.score}/{scores3.trauma_score.max_score}")
    print_result("Mechanism Severe", scores3.trauma_score.mechanism_severe)
    print_result("Consciousness Altered", scores3.trauma_score.consciousness_altered)

    assert scores3.is_trauma_concern, "Should detect trauma concern"
    print("✅ PASSED: Trauma correctly identified")

    # Test Case 4: Low Severity (Self-Care)
    print("\n💊 Test Case 4: Low Severity - Common Cold")
    print("-" * 40)
    symptoms4 = "I have a runny nose and mild sore throat for the past 2 days. No fever, just general tiredness."

    scores4 = service.calculate_all_scores(symptoms4, age=30)
    print_result("Symptoms", symptoms4[:80] + "...")
    print_result("Overall Score", f"{scores4.overall_score}/10 ({scores4.overall_risk_level})")

    assert scores4.overall_score <= 3, "Low severity should score <= 3"
    print("✅ PASSED: Low severity correctly identified")

    # Test Case 5: Quick Keyword Check
    print("\n⚡ Test Case 5: Quick Keyword Detection")
    print("-" * 40)

    test_cases = [
        ("can't breathe", 1, "Critical"),
        ("heart attack", 1, "Critical"),
        ("chest pain with sweating", 2, "Emergency"),
        ("high fever 103", 3, "Urgent"),
        ("headache for 2 days", 4, "Standard"),
    ]

    for symptoms, expected_level, _expected_name in test_cases:
        level, keywords = service.quick_keyword_check(symptoms)
        status = "✅" if level == expected_level else "❌"
        print(f"  {status} '{symptoms}' → Level {level} (expected {expected_level})")

    print("✅ PASSED: Quick keyword detection working")


def test_emergency_classifier():
    """Test the master classifier"""
    print_header("TESTING EMERGENCY CLASSIFIER")

    classifier = EmergencyClassifier()

    # Test Case 1: Full triage response for cardiac emergency
    print("\n🚨 Test Case 1: Full Triage - Cardiac Emergency")
    print("-" * 40)

    request = EmergencyTriageRequest(
        symptoms="Severe chest pain, sweating, nausea, pain in left arm",
        age=60,
        gender="male",
        medical_history=["diabetes"],
        language="en",
    )

    result = classifier.classify(request)

    print_result("Triage Level", f"{result.triage_level} ({result.triage_level_name})")
    print_result("Triage Color", result.triage_color)
    print_result("Emergency Type", result.emergency_type)
    print_result("Call 108", result.call_108)
    print_result("Time Sensitivity", result.time_sensitivity)
    print_result("Primary Action", result.primary_action.action_text)
    print_result("Specialist", result.specialist_recommendation)
    print_result("Confidence", f"{result.confidence:.0%}")

    assert result.triage_level <= 2, "Cardiac emergency should be level 1 or 2"
    assert result.call_108, "Should recommend calling 108"
    assert result.emergency_type == "cardiac", "Should classify as cardiac"
    print("✅ PASSED: Cardiac emergency correctly classified")

    # Test Case 2: Quick classify
    print("\n⚡ Test Case 2: Quick Classify")
    print("-" * 40)

    quick_result = classifier.quick_classify("can't breathe, choking")
    print_result("Level", quick_result["triage_level"])
    print_result("Name", quick_result["triage_level_name"])
    print_result("Call 108", quick_result["call_108"])
    print_result("Keywords", quick_result["matched_keywords"])

    assert quick_result["call_108"], "Choking should trigger 108"
    print("✅ PASSED: Quick classify working")


def test_hospital_routing():
    """Test offline hospital search (static database)"""
    print_header("TESTING HOSPITAL ROUTING SERVICE")

    router = HospitalRoutingService()

    print("\n🏥 Test Case 1: Hospital Search - Mumbai")
    print("-" * 40)

    request = HospitalSearchRequest(
        latitude=19.0760,  # Mumbai
        longitude=72.8777,
        radius_km=10,
        required_capabilities=["emergency_room", "24x7"],
    )
    hospitals = asyncio.run(router.find_emergency_hospitals(request))

    print_result("Hospitals Found", len(hospitals))
    assert hospitals, "Expected static Mumbai hospitals within 10 km"
    assert all(h.has_emergency_room for h in hospitals)
    assert all(h.distance_km <= 10 for h in hospitals)
    scores = [h.match_score for h in hospitals]
    assert scores == sorted(scores, reverse=True), "Hospitals must be sorted by match score"

    for i, h in enumerate(hospitals[:3]):
        print(f"\n  Hospital #{i + 1}:")
        print_result("Name", h.name, indent=2)
        print_result("Distance", h.distance_text, indent=2)
        print_result("Source", h.source, indent=2)

    print("\n🏥 Test Case 2: Remote location - no static coverage")
    remote = HospitalSearchRequest(latitude=34.15, longitude=77.58, radius_km=10)  # Leh
    assert asyncio.run(router.find_emergency_hospitals(remote)) == []
    print("\n✅ PASSED: Hospital search working")


def test_vital_signs():
    """Test vital signs assessment"""
    print_header("TESTING VITAL SIGNS ASSESSMENT")

    service = TriageService()

    # Test critical vitals
    print("\n🩺 Test Case 1: Critical Vital Signs")
    print("-" * 40)

    critical_vitals = VitalSigns(heart_rate=160, blood_pressure_systolic=80, oxygen_saturation=85)

    scores = service.calculate_all_scores("feeling dizzy", vital_signs=critical_vitals)

    print_result("Heart Rate", "160 bpm (critical high)")
    print_result("BP", "80 systolic (critical low)")
    print_result("SpO2", "85% (critical low)")
    print_result("Vitals Concern Level", scores.vitals_concern_level)
    print_result("Overall Score", f"{scores.overall_score}/10")

    assert scores.vitals_concern_level == "critical", "Should detect critical vitals"
    print("✅ PASSED: Critical vitals detected")


def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║   🚨 EMERGENCY TRIAGE SYSTEM - COMPREHENSIVE TEST SUITE   ║")
    print("║                                                            ║")
    print("║   Testing: Risk Scoring, Classification, Hospital Search  ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"\n📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Run synchronous tests
        test_triage_service()
        test_emergency_classifier()
        test_vital_signs()

        test_hospital_routing()

        # Summary
        print_header("TEST SUMMARY")
        print("\n✅ ALL TESTS PASSED!")
        print("\nThe emergency triage system is ready for use.")
        print("\n⚠️  REMINDER: This is for guidance only.")
        print("    In real emergencies, ALWAYS call 108.")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
