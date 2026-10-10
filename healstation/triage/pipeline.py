"""Text triage decision: safety rules first, then the model, then the rules-based fallback.

Order (INV-1): toxin fast lane → red-flag guardrail → model + rules-based
classifier → critical-vitals floor. Helpers are called through their modules
so tests can replace them.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from config import LOCAL_TRIAGE_CONFIDENCE_THRESHOLD
from emergency_triage.offline_triage_engine import select_offline_first_triage
from healstation.triage import fallback, guardrails, model_client, toxin, vitals
from healstation.triage.localization import (
    UNASSESSED_MESSAGES,
    enforce_doctor_response_language,
    localized_message,
)

logger = logging.getLogger("healstation")


@dataclass
class TriageOutcome:
    triage_data: dict[str, Any]
    triage_source: str
    specialist_recommendation: str
    urgency_level: str
    doctor_text: str
    emergency_action_block: dict[str, Any] | None = None
    # Vital signs after merging structured fields with values parsed from text.
    vitals: dict[str, float | None] = field(default_factory=dict)


VITAL_NAMES = ("heart_rate", "bp_systolic", "bp_diastolic", "spo2", "temperature")


def assess_symptoms(
    patient_text: str,
    language: str,
    age: int | None = None,
    gender: str | None = None,
    heart_rate: int | None = None,
    bp_systolic: int | None = None,
    bp_diastolic: int | None = None,
    spo2: int | None = None,
    temperature: float | None = None,
) -> TriageOutcome:
    structured = {
        "heart_rate": heart_rate,
        "bp_systolic": bp_systolic,
        "bp_diastolic": bp_diastolic,
        "spo2": spo2,
        "temperature": temperature,
    }
    emergency_action_block = None

    # Step 4 fast-lane: evaluate toxin/poison exposure before any other triage flow.
    toxin_flag = toxin.evaluate_toxin_fast_lane(patient_text)

    if toxin_flag["apply_fast_lane"]:
        triage_data = toxin.build_toxin_fast_lane_triage(toxin_flag, language)
        triage_source = "toxin_fast_lane"
        specialist_recommendation = triage_data.get("specialist", "emergency medicine")
        urgency_level = triage_data.get("urgency", "high")
        emergency_action_block = toxin.build_toxin_emergency_action_block(toxin_flag, language)
        doctor_text = toxin.compose_toxin_response_text(toxin_flag, triage_data, language)
        resolved_vitals = structured
    else:
        # Step 2 guardrail: evaluate hard red-flags before non-emergency triage flow.
        red_flag = guardrails.evaluate_red_flag_guardrail(patient_text)

        if red_flag["apply_guardrail"]:
            triage_data = guardrails.build_guardrail_triage(red_flag, language)
            triage_source = "red_flag_guardrail"
            specialist_recommendation = triage_data.get("specialist", "emergency medicine")
            urgency_level = triage_data.get("urgency", "high")
            emergency_action_block = guardrails.build_emergency_action_block(red_flag, language)
            doctor_text = guardrails.compose_guardrail_response_text(red_flag, triage_data, language)
            resolved_vitals = structured
        else:
            logger.info("Running offline-first triage with Gemma 4")

            # Step 1: Parse vitals from text; structured fields win.
            parsed_vitals = vitals.parse_vital_signs_from_text(patient_text)
            resolved_vitals = {
                name: structured[name] if structured[name] is not None else parsed_vitals.get(name)
                for name in VITAL_NAMES
            }

            # Step 2: Local Gemma triage
            local_triage_raw = model_client.run_local_gemma_triage(patient_text, language, **resolved_vitals)

            # Step 3: Emergency triage as fallback
            emergency_triage_raw = fallback.build_emergency_fallback_triage(
                patient_text, language, age=age, gender=gender, **resolved_vitals
            )

            triage_data, triage_source = select_offline_first_triage(
                local_payload=local_triage_raw,
                emergency_payload=emergency_triage_raw,
                confidence_threshold=LOCAL_TRIAGE_CONFIDENCE_THRESHOLD,
            )

            if triage_source == "local_gemma":
                logger.info("Gemma 4 selected for offline-first triage.")

            # SAFETY FLOOR: critical vital signs always mean HIGH urgency,
            # whatever the model or the keyword classifier concluded.
            vital_findings = vitals.critical_vital_findings(**resolved_vitals)
            vitals_flag = None
            if vital_findings:
                vitals_flag = {
                    "apply_guardrail": True,
                    "matched_categories": ["critical_vitals"],
                    "confidence": 0.95,
                }
                emergency_action_block = guardrails.build_emergency_action_block(vitals_flag, language)
                emergency_action_block["type"] = "critical_vitals"
                if triage_data["urgency"] != "high":
                    logger.warning("Safety floor: critical vital signs, upgrading to HIGH urgency.")
                    triage_data["urgency"] = "high"
                    triage_data["reasons"] = vital_findings + triage_data["reasons"]
                    triage_data["actions"] = (
                        guardrails.build_guardrail_triage(vitals_flag, language)["actions"] + triage_data["actions"]
                    )

            # Keep old keys for backward compatibility
            specialist_recommendation = triage_data.get("specialist", "general")
            urgency_level = triage_data.get("urgency", "low")

            # Build doctor response text from selected source when available
            doctor_text = ""
            if triage_source == "local_gemma" and isinstance(local_triage_raw, dict):
                doctor_text = str(local_triage_raw.get("doctor_response", "")).strip()
            elif triage_source == "unassessed":
                doctor_text = localized_message(UNASSESSED_MESSAGES, language)
            elif emergency_triage_raw:
                doctor_text = str(emergency_triage_raw.get("doctor_response", "")).strip()

            # Final local fallback: compose from triage data if no text yet
            if not doctor_text:
                logger.info("Composing response from local triage data.")
                doctor_text = fallback.compose_doctor_response_from_triage(triage_data)

            if vitals_flag:
                alert = guardrails.compose_guardrail_response_text(vitals_flag, triage_data, language)
                doctor_text = f"{alert}\n\n{doctor_text}"

    # Final safety fallback to ensure backwards-compatible doctor text
    if not doctor_text:
        doctor_text = fallback.compose_doctor_response_from_triage(triage_data)

    doctor_text = enforce_doctor_response_language(doctor_text, language)

    return TriageOutcome(
        triage_data=triage_data,
        triage_source=triage_source,
        specialist_recommendation=specialist_recommendation,
        urgency_level=urgency_level,
        doctor_text=doctor_text,
        emergency_action_block=emergency_action_block,
        vitals=resolved_vitals,
    )
