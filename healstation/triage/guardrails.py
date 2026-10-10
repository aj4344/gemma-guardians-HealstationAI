"""Red-flag guardrail: rules-based detection of life-threatening presentations.

Runs before and independently of any model (INV-1); its HIGH result can only
be raised further, never lowered (INV-2).
"""

import re
from typing import Any

from emergency_triage import EMERGENCY_NUMBERS
from emergency_triage.offline_triage_engine import normalize_triage
from healstation.triage.localization import (
    localize_guardrail_categories,
    localize_guardrail_reasons,
    localize_urgency_label,
    normalize_language,
)

# Version of the keyword and pattern tables below (QA-06).
RULES_VERSION = "red-flags-v1"


# ── Red-flag guardrail ────────────────────────────────────────────────────────
# Hard, rules-based detection of life-threatening presentations. Runs before the
# model so an unavailable or wrong model can never downgrade these cases.
# Latin-script phrases match on word boundaries; Devanagari phrases match as
# substrings (Hindi/Marathi inflect by suffix, e.g. छाती → छातीत).
RED_FLAG_KEYWORDS: dict[str, list[str]] = {
    "cardiac": [
        "heart attack",
        "chest pain",
        "chest tightness",
        "chest pressure",
        "chest heaviness",
        "crushing chest",
        "pain radiating to arm",
        "radiating to left arm",
        "radiating to jaw",
        "left arm pain",
        "arm pain with chest",
        "jaw pain with chest",
        "sweating with chest pain",
        # Hindi
        "दिल का दौरा",
        "हार्ट अटैक",
        "सीने में दर्द",
        "सीने में दबाव",
        "सीने में जकड़न",
        "सीने में भारीपन",
        "छाती में दर्द",
        "दिल में दर्द",
        "बाएं हाथ में दर्द",
        # Marathi
        "हृदयविकाराचा झटका",
        "हार्ट अटॅक",
        "छातीत दुखणे",
        "छातीत दुखत",
        "छातीत दडपण",
        "छातीवर दडपण",
        "छातीत घट्टपणा",
        "छातीत जडपणा",
        "छातीत वेदना",
        "हृदयात वेदना",
        "डाव्या हातात वेदना",
    ],
    "stroke": [
        "stroke",
        "tia",
        "brain attack",
        "face droop",
        "face drooping",
        "facial droop",
        "facial drooping",
        "slurred speech",
        "speech is slurred",
        "sudden confusion",
        "trouble speaking",
        "can't speak",
        "cannot speak",
        "weakness on one side",
        "weakness one side",
        "one side weak",
        "one sided weakness",
        "one-sided weakness",
        "numbness on one side",
        "sudden numbness",
        "can't lift my arm",
        "can't lift my left arm",
        "can't lift my right arm",
        "paralysis",
        "paralyzed",
        "sudden vision loss",
        "worst headache of my life",
        # Hindi
        "लकवा",
        "चेहरा टेढ़ा",
        "चेहरा लटक",
        "बोली अस्पष्ट",
        "लड़खड़ाती बोली",
        "बोल नहीं पा रहा",
        "बोल नहीं पा रही",
        "एक तरफ कमजोरी",
        "हाथ ऊपर नहीं उठ",
        # Marathi
        "अर्धांगवायू",
        "चेहरा वाकडा",
        "चेहरा लटक",
        "अस्पष्ट बोलणे",
        "बोलता येत नाही",
        "एक बाजू कमजोर",
        "हात वर उचलता येत नाही",
    ],
    "breathing_distress": [
        "can't breathe",
        "cannot breathe",
        "can not breathe",
        "unable to breathe",
        "difficulty breathing",
        "trouble breathing",
        "struggling to breathe",
        "hard to breathe",
        "shortness of breath",
        "short of breath",
        "breathless",
        "breathlessness",
        "gasping",
        "choking",
        "suffocating",
        "blue lips",
        "turning blue",
        "respiratory distress",
        "not breathing",
        "stopped breathing",
        # Hindi
        "सांस नहीं ले पा",
        "सांस लेने में तकलीफ",
        "सांस लेने में दिक्कत",
        "सांस फूल",
        "सांस की कमी",
        "दम घुट",
        "सांस रुक",
        "सांस बंद",
        # Marathi
        "श्वास घेता येत नाही",
        "श्वास घेण्यास त्रास",
        "श्वास घेण्यास अडचण",
        "श्वास कोंड",
        "दम लागत",
        "श्वास बंद",
    ],
    "severe_bleeding": [
        "severe bleeding",
        "heavy bleeding",
        "bleeding heavily",
        "bleeding profusely",
        "won't stop bleeding",
        "wont stop bleeding",
        "bleeding won't stop",
        "bleeding wont stop",
        "massive blood loss",
        "hemorrhage",
        "haemorrhage",
        "vomiting blood",
        "coughing blood",
        "coughing up blood",
        "soaked in blood",
        # Hindi
        "खून नहीं रुक रहा",
        "खून बंद नहीं",
        "बहुत खून",
        "अत्यधिक रक्तस्राव",
        "खून की उल्टी",
        "रक्तस्राव",
        # Marathi
        "खून थांबत नाही",
        "रक्त थांबत नाही",
        "खूप रक्त",
        "तीव्र रक्तस्राव",
        "रक्ताची उलटी",
    ],
    "trauma": [
        "car accident",
        "road accident",
        "bike accident",
        "motorcycle accident",
        "hit by a car",
        "hit by a vehicle",
        "major fall",
        "fall from height",
        "fell from height",
        "head injury",
        "gunshot",
        "stab wound",
        "stabbed",
        "electrocuted",
        "electric shock",
        # Hindi
        "गंभीर चोट",
        "सड़क दुर्घटना",
        "कार एक्सीडेंट",
        "बाइक एक्सीडेंट",
        "गाड़ी दुर्घटना",
        "सिर में चोट",
        "ऊंचाई से गिर",
        "ऊँचाई से गिर",
        "करंट लग",
        # Marathi
        "गंभीर दुखापत",
        "रस्ता अपघात",
        "कार अपघात",
        "गाडी अपघात",
        "मोटरसायकल अपघात",
        "डोक्याला मार",
        "उंचीवरून पड",
        "शॉक लाग",
    ],
    "unconscious": [
        "unconscious",
        "unresponsive",
        "not responding",
        "won't wake up",
        "wont wake up",
        "collapsed",
        # Hindi
        "बेहोश",
        "होश नहीं",
        # Marathi
        "बेशुद्ध",
        "शुद्ध हरपली",
    ],
    "seizure": [
        "seizure",
        "seizures",
        "convulsion",
        "convulsions",
        "convulsing",
        # Hindi
        "मिर्गी",
        "झटके आ",
        # Marathi
        "फेफरे",
        "झटके येत",
        "फिट आली",
    ],
    "anaphylaxis": [
        "anaphylaxis",
        "anaphylactic",
        "throat closing",
        "throat is closing",
        "throat swelling",
        "tongue swelling",
        "severe allergic reaction",
        # Hindi
        "गला बंद हो",
        # Marathi
        "घसा बंद होत",
    ],
    "self_harm": [
        "suicide attempt",
        "attempted suicide",
        "suicidal",
        "kill myself",
        "end my life",
        "want to die",
        "self harm",
        "self-harm",
        "cut myself",
        # Hindi
        "आत्महत्या",
        "खुद को मार",
        "जान दे दूं",
        # Marathi
        "स्वतःला मार",
        "जीव द्यायचा",
    ],
}


# Phrases that alone justify maximum confidence.
EXPLICIT_CRITICAL_KEYWORDS = {
    "heart attack",
    "crushing chest",
    "stroke",
    "face droop",
    "face drooping",
    "slurred speech",
    "can't breathe",
    "cannot breathe",
    "not breathing",
    "stopped breathing",
    "severe bleeding",
    "won't stop bleeding",
    "unconscious",
    "unresponsive",
    "anaphylaxis",
    "suicide attempt",
    "दिल का दौरा",
    "हृदयविकाराचा झटका",
    "बेहोश",
    "बेशुद्ध",
    "लकवा",
    "अर्धांगवायू",
}


# Separator between words that does not cross a clause boundary.
_SEP = r"[^\w.,;:!?\n।]+"


_RED_FLAG_PATTERNS: dict[str, list["re.Pattern[str]"]] = {
    "cardiac": [
        # "pain in my heart", "pressure on the chest"
        re.compile(
            rf"\b(?:pain|ache|pressure|tightness|heaviness|discomfort)\b(?:{_SEP}\w+){{0,3}}?{_SEP}(?:heart|chest)\b"
        ),
        # "my chest hurts", "heart is aching"
        re.compile(
            rf"\b(?:heart|chest)\b(?:{_SEP}\w+){{0,2}}?{_SEP}(?:pain|pains|ache|aches|aching|pressure|tightness|heaviness|discomfort|hurts?|hurting)\b"
        ),
        re.compile(r"(?:दिल|सीने|छाती|हृदय)\S*\s+(?:\S+\s+){0,2}?(?:दर्द|दबाव|जकड़न|भारीपन|वेदना|दुख|दडपण)"),
        re.compile(r"(?:दर्द|वेदना)\s+(?:\S+\s+){0,2}?(?:दिल|सीने|छाती|हृदय)"),
    ],
    "breathing_distress": [
        re.compile(
            rf"\b(?:can'?t|cannot|unable to|hard to|difficult to|struggling to|trouble)\b(?:{_SEP}\w+){{0,2}}?{_SEP}(?:breathe|breathing)\b"
        ),
        re.compile(r"सांस\S*\s+(?:\S+\s+){0,3}?(?:तकलीफ|दिक्कत|फूल|नहीं ले|रुक)"),
        re.compile(r"श्वास\S*\s+(?:\S+\s+){0,3}?(?:त्रास|अडचण|येत नाही|कोंड|बंद)"),
    ],
}


UNCERTAINTY_MARKERS = (
    "maybe",
    "might",
    "not sure",
    "unclear",
    "possibly",
    "i think",
    "could be",
    "unsure",
    "शायद",
    "पता नहीं",
    "कदाचित",
    "माहित नाही",
)


# A negation word followed by at most two words directly before the finding,
# within the same clause: "no chest pain", "denies any chest pain".
_NEGATION_RE = re.compile(
    r"\b(?:no|not|without|denies|denied|deny|negative for|no signs? of|free of)\s+(?:\w+\s+){0,2}$"
)


def _keyword_regex(keyword: str) -> "re.Pattern[str]":
    escaped = re.escape(keyword)
    if keyword.isascii():
        return re.compile(rf"(?<![a-z]){escaped}(?![a-z])")
    return re.compile(escaped)


_RED_FLAG_KEYWORD_REGEXES: dict[str, list[tuple[str, "re.Pattern[str]"]]] = {
    category: [(kw, _keyword_regex(kw)) for kw in keywords] for category, keywords in RED_FLAG_KEYWORDS.items()
}


def _normalize_symptom_text(text: str | None) -> str:
    return str(text or "").lower().replace("’", "'").replace("‘", "'")


def _is_negated(text: str, start: int) -> bool:
    window = text[max(0, start - 40) : start]
    clause = re.split(r"[.,;:!?\n।]", window)[-1]
    return bool(_NEGATION_RE.search(clause))


def _first_unnegated_match(pattern: "re.Pattern[str]", text: str) -> str | None:
    for match in pattern.finditer(text):
        if not _is_negated(text, match.start()):
            return match.group(0)
    return None


def evaluate_red_flag_guardrail(patient_text: str) -> dict[str, Any]:
    """Evaluate high-risk red flags before any model-based triage."""
    text = _normalize_symptom_text(patient_text)

    category_matches: dict[str, list[str]] = {}
    for category, keyword_regexes in _RED_FLAG_KEYWORD_REGEXES.items():
        found = [kw for kw, regex in keyword_regexes if _first_unnegated_match(regex, text)]
        for pattern in _RED_FLAG_PATTERNS.get(category, []):
            hit = _first_unnegated_match(pattern, text)
            if hit and hit not in found:
                found.append(hit)
        if found:
            category_matches[category] = found

    matched_categories = list(category_matches.keys())
    total_matches = sum(len(v) for v in category_matches.values())
    has_uncertainty = any(marker in text for marker in UNCERTAINTY_MARKERS)
    explicit_critical_hit = any(kw in EXPLICIT_CRITICAL_KEYWORDS for kws in category_matches.values() for kw in kws)

    confidence = 0.0
    if explicit_critical_hit:
        confidence = 0.95
    elif len(matched_categories) >= 2 or total_matches >= 3:
        confidence = 0.88
    elif total_matches >= 1:
        confidence = 0.8

    guardrail_hit = total_matches >= 1
    ambiguous = guardrail_hit and has_uncertainty
    if ambiguous:
        confidence = max(confidence, 0.7)

    reasons = []
    for category in matched_categories:
        sample = ", ".join(category_matches[category][:3])
        reasons.append(f"Red-flag {category.replace('_', ' ')} indicators detected: {sample}.")
    if ambiguous:
        reasons.append(
            "Symptoms are ambiguous but suggest possible emergency risk; conservative safety guidance applied."
        )

    return {
        "apply_guardrail": guardrail_hit,
        "guardrail_hit": guardrail_hit,
        "ambiguous": ambiguous,
        "confidence": confidence,
        "matched_categories": matched_categories,
        "matched_keywords": category_matches,
        "reasons": reasons,
    }


def build_guardrail_triage(red_flag: dict[str, Any], language: str | None = None) -> dict[str, Any]:
    lang = normalize_language(language)
    reasons = localize_guardrail_reasons(red_flag, lang)
    actions_map = {
        "en": [
            f"Call {EMERGENCY_NUMBERS.get('ambulance', '108')} immediately if severe symptoms are present.",
            "Proceed to the nearest emergency department now.",
            "Keep the patient under observation and avoid delays in transport.",
        ],
        "hi": [
            f"अगर गंभीर लक्षण हों तो तुरंत {EMERGENCY_NUMBERS.get('ambulance', '108')} पर कॉल करें।",
            "सबसे नजदीकी इमरजेंसी विभाग अभी जाएं।",
            "मरीज को निगरानी में रखें और परिवहन में देरी न करें।",
        ],
        "mr": [
            f"लक्षण गंभीर असतील तर त्वरित {EMERGENCY_NUMBERS.get('ambulance', '108')} वर कॉल करा.",
            "ताबडतोब जवळच्या इमर्जन्सी विभागात जा.",
            "रुग्णावर नजर ठेवा आणि वाहतुकीला उशीर करू नका.",
        ],
    }
    actions = actions_map.get(lang, actions_map["en"])
    return normalize_triage(
        {
            "urgency": "high",
            "reasons": reasons,
            "actions": actions,
            "specialist": "emergency medicine",
            "confidence": red_flag.get("confidence", 0.85),
        }
    )


def compose_guardrail_response_text(
    red_flag: dict[str, Any],
    triage_data: dict[str, Any],
    language: str | None = None,
) -> str:
    lang = normalize_language(language)
    category_text = localize_guardrail_categories(red_flag.get("matched_categories", []), lang)
    if not category_text:
        category_text = "high-risk symptoms" if lang == "en" else "उच्च जोखिम लक्षण" if lang == "hi" else "उच्च धोका लक्षणे"

    urgency_label = localize_urgency_label(lang, triage_data.get("urgency", "high"))
    ambulance = EMERGENCY_NUMBERS.get("ambulance", "108")
    if lang == "hi":
        return (
            f"आपातकालीन सुरक्षा चेतावनी: संभव {category_text}. "
            f"तात्कालिकता {urgency_label} है. "
            f"अभी {ambulance} पर कॉल करें या तुरंत नजदीकी इमरजेंसी रूम जाएं."
        )
    if lang == "mr":
        return (
            f"आपत्कालीन चेतावणी: शक्य {category_text}. "
            f"तातडी {urgency_label} आहे. "
            f"आत्ताच {ambulance} वर कॉल करा किंवा तात्काळ जवळच्या इमर्जन्सी कक्षात जा."
        )
    return (
        f"Emergency safety alert: possible {category_text}. "
        f"Urgency is {triage_data.get('urgency', 'high')}. "
        f"Call {ambulance} now or go to the nearest emergency room immediately."
    )


def build_emergency_action_block(red_flag: dict[str, Any], language: str | None = None) -> dict[str, Any]:
    lang = normalize_language(language)
    ambulance = EMERGENCY_NUMBERS.get("ambulance", "108")
    mental_health = EMERGENCY_NUMBERS.get("mental_health")
    categories = red_flag.get("matched_categories", [])

    immediate_actions_map = {
        "en": [
            f"Call {ambulance} immediately.",
            "Stay calm and wait for the emergency team.",
            "Do not drive yourself to the hospital.",
        ],
        "hi": [
            f"तुरंत {ambulance} पर कॉल करें।",
            "शांत रहें और आपातकालीन टीम का इंतज़ार करें।",
            "खुद अस्पताल वाहन न चलाएं।",
        ],
        "mr": [
            f"त्वरित {ambulance} वर कॉल करा.",
            "शांत राहा आणि आपत्कालीन पथकाची प्रतीक्षा करा.",
            "स्वतः वाहन चालवून हॉस्पिटलला जाऊ नका.",
        ],
    }
    immediate_actions = list(immediate_actions_map.get(lang, immediate_actions_map["en"]))

    if red_flag.get("ambiguous"):
        immediate_actions.insert(
            0,
            {
                "hi": "लक्षण स्पष्ट नहीं हैं; सुरक्षा के लिए आपातकालीन सलाह दी जा रही है।",
                "mr": "लक्षण स्पष्ट नाहीत; सुरक्षिततेसाठी आपत्कालीन मार्गदर्शन दिले आहे.",
            }.get(lang, "Symptoms are uncertain; using conservative emergency-first guidance for safety."),
        )

    emergency_numbers = {
        "ambulance": ambulance,
        "emergency": EMERGENCY_NUMBERS.get("emergency", "112"),
    }
    if "self_harm" in categories and mental_health:
        emergency_numbers["mental_health"] = mental_health
        immediate_actions.append(
            {
                "hi": f"व्यक्ति को अकेला न छोड़ें। मानसिक स्वास्थ्य हेल्पलाइन: {mental_health}।",
                "mr": f"व्यक्तीला एकटे सोडू नका. मानसिक आरोग्य हेल्पलाइन: {mental_health}.",
            }.get(lang, f"Do not leave the person alone. Mental health helpline: {mental_health}.")
        )

    return {
        "type": "emergency_guardrail",
        "triggered": bool(red_flag.get("apply_guardrail")),
        "confidence": float(red_flag.get("confidence", 0.9)),
        "matched_categories": categories,
        "matched_keywords": red_flag.get("matched_keywords", {}),
        "reasoning": localize_guardrail_reasons(red_flag, lang),
        "time_sensitivity": "immediate",
        "call_ambulance": True,
        "emergency_numbers": emergency_numbers,
        "immediate_actions": immediate_actions,
    }
