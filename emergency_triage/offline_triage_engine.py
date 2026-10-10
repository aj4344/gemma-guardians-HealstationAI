"""
Offline-first triage normalization and routing helpers.

This module provides a canonical triage schema:
urgency, reasons, actions, specialist, confidence
"""

from typing import Any, Dict, List, Optional, Tuple


ALLOWED_URGENCY = {"low", "medium", "high"}
DEFAULT_SPECIALIST = "general"
DEFAULT_CONFIDENCE = 0.5

_URGENCY_MAPPING = {
    "critical": "high",
    "emergency": "high",
    "urgent": "high",
    "high": "high",
    "within_10_minutes": "high",
    "immediate": "high",
    "moderate": "medium",
    "medium": "medium",
    "standard": "medium",
    "within_24_hours": "medium",
    "low": "low",
    "minimal": "low",
    "self_care": "low",
    "scheduled": "low",
}

# Used when no triage source produced a usable result: never report "low"
# for a patient nobody has actually assessed.
UNASSESSED_TRIAGE = {
    "urgency": "medium",
    "reasons": ["Automated triage could not be completed for these symptoms."],
    "actions": [
        "Arrange an in-person assessment by a health worker or doctor today.",
        "Call 108 immediately if symptoms are severe or getting worse.",
    ],
    "specialist": DEFAULT_SPECIALIST,
    "confidence": 0.0,
}


def is_known_urgency(value: Any) -> bool:
    return str(value or "").strip().lower() in _URGENCY_MAPPING


def normalize_urgency(value: Any) -> str:
    """Map arbitrary urgency labels to low/medium/high."""
    text = str(value or "").strip().lower()
    return _URGENCY_MAPPING.get(text, "low")


def ensure_list(value: Any) -> List[str]:
    """Always return a list of non-empty strings."""
    if value is None:
        return []

    if isinstance(value, list):
        items = value
    else:
        items = [value]

    normalized_items: List[str] = []
    for item in items:
        text = str(item).strip()
        if text:
            normalized_items.append(text)
    return normalized_items


def normalize_specialist(value: Any, default: str = DEFAULT_SPECIALIST) -> str:
    text = str(value or "").strip().lower()
    return text if text else default


def normalize_confidence(value: Any, default: float = DEFAULT_CONFIDENCE) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return float(default)

    if confidence < 0:
        return 0.0
    if confidence > 1:
        return 1.0
    return confidence


def normalize_triage(payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return canonical triage payload with safe defaults."""
    payload = payload or {}

    urgency = normalize_urgency(payload.get("urgency"))
    reasons = ensure_list(payload.get("reasons"))
    actions = ensure_list(payload.get("actions"))
    specialist = normalize_specialist(payload.get("specialist"))
    confidence = normalize_confidence(payload.get("confidence"))

    if not reasons:
        reasons = ["Clinical details were limited; conservative triage applied."]

    if not actions:
        actions = ["Seek in-person medical assessment if symptoms persist or worsen."]

    return {
        "urgency": urgency,
        "reasons": reasons,
        "actions": actions,
        "specialist": specialist,
        "confidence": confidence,
    }


def normalize_and_validate_local_triage(payload: Optional[Dict[str, Any]]) -> Tuple[Dict[str, Any], bool]:
    """
    Normalize local model output and determine if it is structurally valid.

    Valid local output requires all canonical fields to be explicitly present
    and parseable from the local payload.
    """
    normalized = normalize_triage(payload)

    if not isinstance(payload, dict):
        return normalized, False

    raw_urgency = payload.get("urgency")
    raw_reasons = payload.get("reasons")
    raw_actions = payload.get("actions")
    raw_specialist = payload.get("specialist")
    raw_confidence = payload.get("confidence")

    reasons_ok = len(ensure_list(raw_reasons)) > 0
    actions_ok = len(ensure_list(raw_actions)) > 0
    specialist_ok = bool(str(raw_specialist or "").strip())

    confidence_ok = True
    try:
        float(raw_confidence)
    except (TypeError, ValueError):
        confidence_ok = False

    urgency_ok = is_known_urgency(raw_urgency)

    is_valid = urgency_ok and reasons_ok and actions_ok and specialist_ok and confidence_ok
    return normalized, is_valid


def select_offline_first_triage(
    local_payload: Optional[Dict[str, Any]],
    emergency_payload: Optional[Dict[str, Any]],
    confidence_threshold: float,
) -> Tuple[Dict[str, Any], str]:
    """
    Local-first selection:
    1) local model when valid and confidence >= threshold
    2) emergency fallback otherwise
    3) a conservative "unassessed" result when neither produced output
    """
    normalized_local, local_valid = normalize_and_validate_local_triage(local_payload)
    if local_valid and normalized_local["confidence"] >= confidence_threshold:
        return normalized_local, "local_gemma"

    if not emergency_payload:
        return normalize_triage(UNASSESSED_TRIAGE), "unassessed"

    return normalize_triage(emergency_payload), "emergency_fallback"