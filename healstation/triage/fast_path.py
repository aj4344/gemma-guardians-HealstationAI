"""Emergency fast path (RES-01, INV-1).

Deterministic safety rules only — no model, no queue — so the answer is back
in milliseconds whatever else the device is doing. The full assessment runs
afterwards as a job and can only raise this result (INV-2).
"""

from __future__ import annotations

from typing import Any

from healstation.triage import guardrails, toxin, vitals
from healstation.triage.localization import normalize_language

_NO_RULE_MESSAGE = {
    "en": "The safety rules found no emergency warning signs. The full assessment is still running — "
    "do not treat this as low urgency.",
    "hi": "सुरक्षा नियमों में कोई आपातकालीन चेतावनी संकेत नहीं मिला। पूरा आकलन अभी चल रहा है — इसे कम तात्कालिकता न समझें।",
    "mr": "सुरक्षा नियमांना कोणतेही आपत्कालीन धोक्याचे लक्षण आढळले नाही. पूर्ण मूल्यांकन अजून चालू आहे — याला कमी तातडीचे समजू नका.",
}

URGENCY_RANK = {None: -1, "low": 0, "medium": 1, "high": 2}


def max_urgency(*levels: str | None) -> str | None:
    """INV-2: the final urgency is the highest any source reported."""
    return max(levels, key=lambda level: URGENCY_RANK.get(level, -1)) if levels else None


def evaluate(symptoms: str, language: str, vital_signs: dict[str, Any] | None = None) -> dict[str, Any]:
    language = normalize_language(language)
    vital_signs = {k: v for k, v in (vital_signs or {}).items() if v is not None}
    rules_fired: list[str] = []
    reasons: list[str] = []
    block = None

    toxin_flag = toxin.evaluate_toxin_fast_lane(symptoms)
    if toxin_flag["apply_fast_lane"]:
        rules_fired.append("toxin_fast_lane")
        reasons += toxin.build_toxin_fast_lane_triage(toxin_flag, language)["reasons"]
        block = toxin.build_toxin_emergency_action_block(toxin_flag, language)

    red_flag = guardrails.evaluate_red_flag_guardrail(symptoms)
    if red_flag["apply_guardrail"]:
        rules_fired.append("red_flag_guardrail")
        reasons += guardrails.build_guardrail_triage(red_flag, language)["reasons"]
        block = block or guardrails.build_emergency_action_block(red_flag, language)

    vital_findings = vitals.critical_vital_findings(**vital_signs, language=language)
    if vital_findings:
        rules_fired.append("critical_vitals")
        reasons += vital_findings
        if block is None:
            flag = {"apply_guardrail": True, "matched_categories": ["critical_vitals"], "confidence": 0.95}
            block = guardrails.build_emergency_action_block(flag, language)
            block["type"] = "critical_vitals"

    result: dict[str, Any] = {
        "urgency": "high" if rules_fired else None,
        "rules_fired": rules_fired,
        "reasons": reasons,
        "emergency_action_block": block,
    }
    if not rules_fired:
        # INV-3: no rule fired is not an assessment, and is never shown as "low".
        result["status"] = "no_emergency_rule_triggered"
        result["message_localized"] = _NO_RULE_MESSAGE[language]
    return result
