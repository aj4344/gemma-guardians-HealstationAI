"""Rules-based classifier used when the model is unavailable or not confident."""

import logging
from typing import Any

from emergency_triage import EmergencyClassifier, EmergencyTriageRequest, VitalSigns
from healstation.triage.vitals import clamp_vital

logger = logging.getLogger("healstation")

emergency_classifier = EmergencyClassifier()


def build_emergency_fallback_triage(
    patient_text: str,
    language: str,
    age: int | None = None,
    gender: str | None = None,
    heart_rate: int | None = None,
    bp_systolic: int | None = None,
    bp_diastolic: int | None = None,
    spo2: int | None = None,
    temperature: float | None = None,
) -> dict[str, Any] | None:
    """Reuse existing emergency classifier as strict fallback path."""
    try:
        # Build VitalSigns object only if any value was provided. Values are
        # clamped into the model's accepted range: the most extreme readings
        # (e.g. SpO2 45%) would otherwise fail validation and drop the whole
        # fallback. Clamped values stay beyond every critical threshold.
        vital_signs = None
        if any(v is not None for v in [heart_rate, bp_systolic, bp_diastolic, spo2, temperature]):
            vital_signs = VitalSigns(
                heart_rate=clamp_vital(heart_rate, 30, 250),
                blood_pressure_systolic=clamp_vital(bp_systolic, 50, 250),
                blood_pressure_diastolic=clamp_vital(bp_diastolic, 30, 150),
                oxygen_saturation=clamp_vital(spo2, 50, 100),
                temperature_celsius=clamp_vital(temperature, 34, 43, as_int=False),
            )
        emergency_request = EmergencyTriageRequest(
            symptoms=patient_text,
            language=language,
            age=age,
            gender=gender,
            vital_signs=vital_signs,
        )
        triage_result = emergency_classifier.classify(emergency_request)

        triage_level_name = triage_result.triage_level_name
        urgency_raw = triage_level_name.value if hasattr(triage_level_name, "value") else str(triage_level_name)

        reasons = list(triage_result.detected_conditions or [])
        reasons.append(
            f"Overall risk score: {triage_result.scores.overall_score}/10 ({triage_result.scores.overall_risk_level})"
        )

        actions = []
        if triage_result.primary_action:
            actions.append(triage_result.primary_action.action_text)
        if triage_result.secondary_actions:
            actions.extend([a.action_text for a in triage_result.secondary_actions if a.action_text])

        return {
            "urgency": urgency_raw,
            "reasons": reasons,
            "actions": actions,
            "specialist": triage_result.specialist_recommendation or "general",
            "confidence": triage_result.confidence,
            "doctor_response": triage_result.preliminary_assessment,
        }
    except Exception as emergency_error:
        logger.warning("Emergency triage fallback failed: %s", type(emergency_error).__name__)
        return None


def compose_doctor_response_from_triage(triage_data: dict[str, Any]) -> str:
    urgency = triage_data.get('urgency', 'low').upper()
    reasons = triage_data.get("reasons", [])
    actions = triage_data.get("actions", [])

    response = f"Based on your symptoms, I have assessed this as a {urgency} urgency situation. "

    if reasons:
        response += f"Key findings include: {'; '.join(reasons[:3])}. "

    if actions:
        response += f"I recommend the following immediate actions: {'; '.join(actions[:3])}. "

    response += "Please monitor your symptoms closely. If you experience worsening pain, difficulty breathing, or any other red flags, seek emergency medical attention immediately."

    return response
