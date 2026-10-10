"""Toxin / poisoning fast lane: evaluated before every other triage step."""

from typing import Any

from emergency_triage import EMERGENCY_NUMBERS, TOXIN_FAST_LANE_KEYWORDS
from emergency_triage.offline_triage_engine import normalize_triage
from healstation.triage.localization import (
    localize_toxin_categories,
    localize_toxin_reasons,
    localize_urgency_label,
    normalize_language,
)

RULES_VERSION = "toxin-v1"


def evaluate_toxin_fast_lane(patient_text: str) -> dict[str, Any]:
    """Detect toxin/poison exposure early and conservatively."""
    text = str(patient_text or "").lower()
    category_matches: dict[str, list[str]] = {}

    for category, keywords in TOXIN_FAST_LANE_KEYWORDS.items():
        seen: list[str] = []
        for keyword in keywords:
            if keyword and keyword in text and keyword not in seen:
                seen.append(keyword)
        if seen:
            category_matches[category] = seen

    matched_categories = list(category_matches.keys())
    total_matches = sum(len(values) for values in category_matches.values())
    uncertainty_markers = ["maybe", "might", "not sure", "unclear", "possibly", "i think", "could be", "unsure"]
    has_uncertainty = any(marker in text for marker in uncertainty_markers)

    apply_fast_lane = bool(total_matches >= 1)
    ambiguous = bool(apply_fast_lane and has_uncertainty)
    confidence = 0.95 if total_matches >= 2 else 0.82 if total_matches == 1 else 0.0
    if ambiguous:
        confidence = max(confidence, 0.78)

    reasons = []
    for category in matched_categories:
        sample = ", ".join(category_matches[category][:4])
        reasons.append(f"Toxin exposure indicators detected in {category}: {sample}.")
    if ambiguous:
        reasons.append("Exposure is uncertain but potentially toxic; conservative poison emergency guidance applied.")

    return {
        "apply_fast_lane": apply_fast_lane,
        "ambiguous": ambiguous,
        "confidence": confidence,
        "matched_categories": matched_categories,
        "matched_keywords": category_matches,
        "reasons": reasons,
    }


def build_toxin_fast_lane_triage(toxin_flag: dict[str, Any], language: str | None = None) -> dict[str, Any]:
    lang = normalize_language(language)
    reasons = localize_toxin_reasons(toxin_flag, lang)
    actions_map = {
        "en": [
            f"Call {EMERGENCY_NUMBERS.get('ambulance', '108')} immediately and seek urgent poison/emergency care.",
            "Move away from the exposure source and to fresh air if inhalation is involved.",
            "Do not induce vomiting unless a poison specialist or emergency clinician instructs you to do so.",
            "Bring the product container, label, or suspected food/medicine details to the hospital.",
        ],
        "hi": [
            f"तुरंत {EMERGENCY_NUMBERS.get('ambulance', '108')} पर कॉल करें और आपातकालीन विष उपचार लें।",
            "यदि गैस/धुएं का एक्सपोजर हो तो तुरंत ताजा हवा में जाएं।",
            "डॉक्टर/पॉइज़न विशेषज्ञ की सलाह के बिना उल्टी न कराएं।",
            "उत्पाद का कंटेनर, लेबल या संदिग्ध पदार्थ/दवा की जानकारी साथ ले जाएं।",
        ],
        "mr": [
            f"त्वरित {EMERGENCY_NUMBERS.get('ambulance', '108')} वर कॉल करा आणि आपत्कालीन विष उपचार घ्या.",
            "गॅस/धूर एक्सपोजर असल्यास त्वरित ताजी हवा घ्या.",
            "डॉक्टर/पॉइझन तज्ज्ञांच्या सल्ल्याशिवाय उलटी करू नका.",
            "उत्पादनाचे कंटेनर, लेबल किंवा संशयित पदार्थ/औषधाची माहिती सोबत घ्या.",
        ],
    }
    return normalize_triage(
        {
            "urgency": "high",
            "reasons": reasons,
            "actions": actions_map.get(lang, actions_map["en"]),
            "specialist": "emergency medicine",
            "confidence": toxin_flag.get("confidence", 0.9),
        }
    )


def build_toxin_emergency_action_block(toxin_flag: dict[str, Any], language: str | None = None) -> dict[str, Any]:
    lang = normalize_language(language)
    ambulance = EMERGENCY_NUMBERS.get("ambulance", "108")
    immediate_actions_map = {
        "en": [
            f"Call {ambulance} immediately.",
            "Move to fresh air if gas, fumes, or smoke exposure is possible.",
            "Do not induce vomiting unless instructed by a clinician or poison specialist.",
            "Bring the container, label, or suspected substance details to the emergency team.",
        ],
        "hi": [
            f"तुरंत {ambulance} पर कॉल करें।",
            "यदि गैस/धुआं/फ्यूम्स का संपर्क हो तो ताजी हवा में जाएं।",
            "डॉक्टर या पॉइज़न विशेषज्ञ के कहे बिना उल्टी न कराएं।",
            "कंटेनर/लेबल या संदिग्ध पदार्थ का विवरण साथ ले जाएं।",
        ],
        "mr": [
            f"तुरंत {ambulance} वर कॉल करा.",
            "गॅस/धूर/वाफेचा संपर्क असेल तर ताजी हवा मिळेल तिथे जा.",
            "डॉक्टर किंवा विषतज्ज्ञ सांगितल्याशिवाय उलटी करू नका.",
            "कंटेनर/लेबल किंवा संशयित पदार्थाची माहिती सोबत घ्या.",
        ],
    }
    immediate_actions = list(immediate_actions_map.get(lang, immediate_actions_map["en"]))
    if toxin_flag.get("ambiguous"):
        if lang == "hi":
            immediate_actions.insert(0, "संपर्क स्पष्ट नहीं है, फिर भी इसे आपातकाल मानें।")
        elif lang == "mr":
            immediate_actions.insert(0, "संपर्क स्पष्ट नाही, तरीही हे आपत्काल समजा.")
        else:
            immediate_actions.insert(0, "Exposure is uncertain but potentially toxic; treat this as an emergency now.")

    return {
        "type": "toxin_fast_lane",
        "triggered": bool(toxin_flag.get("apply_fast_lane")),
        "confidence": float(toxin_flag.get("confidence", 0.8)),
        "matched_categories": toxin_flag.get("matched_categories", []),
        "matched_keywords": toxin_flag.get("matched_keywords", {}),
        "reasoning": localize_toxin_reasons(toxin_flag, lang),
        "time_sensitivity": "immediate",
        "call_ambulance": True,
        "emergency_numbers": {
            "ambulance": EMERGENCY_NUMBERS.get("ambulance", "108"),
            "emergency": EMERGENCY_NUMBERS.get("emergency", "112"),
        },
        "immediate_actions": immediate_actions,
    }


def compose_toxin_response_text(
    toxin_flag: dict[str, Any],
    triage_data: dict[str, Any],
    language: str | None = None,
) -> str:
    lang = normalize_language(language)
    category_text = localize_toxin_categories(toxin_flag.get("matched_categories", []), lang)
    if not category_text:
        category_text = "toxin exposure" if lang == "en" else "विषाक्त संपर्क" if lang == "hi" else "विषारी संपर्क"

    urgency_label = localize_urgency_label(lang, triage_data.get("urgency", "high"))
    ambulance = EMERGENCY_NUMBERS.get("ambulance", "108")
    if lang == "hi":
        return (
            f"आपातकालीन विषाक्त चेतावनी: संभव {category_text}. "
            f"तात्कालिकता {urgency_label} है. "
            f"अभी {ambulance} पर कॉल करें और तुरंत इमरजेंसी देखभाल लें."
        )
    if lang == "mr":
        return (
            f"आपत्कालीन विषारी चेतावणी: शक्य {category_text}. "
            f"तातडी {urgency_label} आहे. "
            f"आत्ताच {ambulance} वर कॉल करा आणि तात्काळ इमर्जन्सी उपचार घ्या."
        )
    return (
        f"Emergency toxin alert: possible {category_text}. "
        f"Urgency is {triage_data.get('urgency', 'high')}. "
        f"Call {ambulance} now and seek emergency care immediately."
    )
