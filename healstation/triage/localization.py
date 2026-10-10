"""User-facing triage text in English, Hindi and Marathi."""

from typing import Any


def normalize_language(language: str | None) -> str:
    raw = str(language or "en").strip().lower()
    if "-" in raw:
        raw = raw.split("-", 1)[0]
    return raw if raw in {"en", "hi", "mr"} else "en"


UNASSESSED_MESSAGES = {
    "en": (
        "Automated triage could not be completed for these symptoms. Please arrange an "
        "in-person assessment today, and call 108 immediately if symptoms are severe or getting worse."
    ),
    "hi": (
        "इन लक्षणों के लिए स्वचालित ट्राइएज पूरा नहीं हो सका। कृपया आज ही किसी स्वास्थ्य कार्यकर्ता या डॉक्टर से "
        "जांच कराएं, और लक्षण गंभीर हों या बढ़ रहे हों तो तुरंत 108 पर कॉल करें।"
    ),
    "mr": (
        "या लक्षणांसाठी स्वयंचलित ट्रायएज पूर्ण होऊ शकले नाही. कृपया आजच आरोग्य कर्मचारी किंवा डॉक्टरांकडून "
        "तपासणी करून घ्या, आणि लक्षणे गंभीर असल्यास किंवा वाढत असल्यास त्वरित 108 वर कॉल करा."
    ),
}


ASSESSMENT_FAILED_MESSAGES = {
    "en": "The assessment could not be completed due to a technical problem. Please try again. If symptoms are severe, call 108 now.",
    "hi": "तकनीकी समस्या के कारण आकलन पूरा नहीं हो सका। कृपया फिर से प्रयास करें। लक्षण गंभीर हों तो तुरंत 108 पर कॉल करें।",
    "mr": "तांत्रिक अडचणीमुळे मूल्यांकन पूर्ण होऊ शकले नाही. कृपया पुन्हा प्रयत्न करा. लक्षणे गंभीर असल्यास त्वरित 108 वर कॉल करा.",
}


STT_FAILED_MESSAGES = {
    "en": "Could not transcribe the recording. Please try again or type the symptoms instead.",
    "hi": "रिकॉर्डिंग को टेक्स्ट में नहीं बदला जा सका। कृपया फिर से प्रयास करें या लक्षण टाइप करें।",
    "mr": "रेकॉर्डिंगचे मजकुरात रूपांतर करता आले नाही. कृपया पुन्हा प्रयत्न करा किंवा लक्षणे टाइप करा.",
}


def localized_message(messages: dict[str, str], language: str | None) -> str:
    return messages.get(normalize_language(language), messages["en"])


def contains_devanagari(text: str) -> bool:
    return any("\u0900" <= char <= "\u097f" for char in text)


def enforce_doctor_response_language(doctor_response: str, language: str) -> str:
    lang = normalize_language(language)
    if not doctor_response or lang == "en":
        return doctor_response
    if contains_devanagari(doctor_response):
        return doctor_response

    prefix = "हिंदी में उत्तर: " if lang == "hi" else "मराठीमध्ये उत्तर: "
    return f"{prefix}{doctor_response}"


def localize_urgency_label(language: str, urgency: str) -> str:
    mapping = {
        "en": {"high": "high", "medium": "medium", "low": "low"},
        "hi": {"high": "उच्च", "medium": "मध्यम", "low": "निम्न"},
        "mr": {"high": "उच्च", "medium": "मध्यम", "low": "कमी"},
    }
    return mapping.get(language, mapping["en"]).get(urgency, urgency)


GUARDRAIL_CATEGORY_LABELS = {
    "en": {
        "cardiac": "cardiac",
        "stroke": "stroke",
        "breathing_distress": "breathing distress",
        "severe_bleeding": "severe bleeding",
        "trauma": "major trauma",
        "unconscious": "unconsciousness",
        "seizure": "seizure",
        "anaphylaxis": "severe allergic reaction",
        "self_harm": "suicide or self-harm risk",
        "critical_vitals": "critical vital signs",
    },
    "hi": {
        "cardiac": "हृदय संबंधी",
        "stroke": "स्ट्रोक",
        "breathing_distress": "सांस लेने में कठिनाई",
        "severe_bleeding": "गंभीर रक्तस्राव",
        "trauma": "गंभीर चोट",
        "unconscious": "बेहोशी",
        "seizure": "दौरा (मिर्गी)",
        "anaphylaxis": "गंभीर एलर्जी प्रतिक्रिया",
        "self_harm": "आत्महत्या या आत्म-क्षति का जोखिम",
        "critical_vitals": "गंभीर वाइटल साइन",
    },
    "mr": {
        "cardiac": "हृदय संबंधित",
        "stroke": "स्ट्रोक",
        "breathing_distress": "श्वासोच्छ्वास त्रास",
        "severe_bleeding": "तीव्र रक्तस्राव",
        "trauma": "गंभीर दुखापत",
        "unconscious": "बेशुद्धी",
        "seizure": "झटके (फिट)",
        "anaphylaxis": "तीव्र ॲलर्जी प्रतिक्रिया",
        "self_harm": "आत्महत्या किंवा स्वतःला इजा होण्याचा धोका",
        "critical_vitals": "गंभीर जीवनावश्यक चिन्हे",
    },
}


def localize_guardrail_categories(categories: list[str], language: str) -> str:
    mapping = GUARDRAIL_CATEGORY_LABELS.get(language, GUARDRAIL_CATEGORY_LABELS["en"])
    localized = [mapping.get(category, category.replace("_", " ")) for category in categories]
    return ", ".join(localized) if localized else ""


TOXIN_CATEGORY_LABELS = {
    "en": {
        "ingestion": "ingestion",
        "exposure": "exposure",
        "inhalation": "inhalation",
        "skin_contact": "skin contact",
        "eye_contact": "eye contact",
    },
    "hi": {
        "ingestion": "निगलना",
        "exposure": "संपर्क",
        "inhalation": "सांस लेना",
        "skin_contact": "त्वचा संपर्क",
        "eye_contact": "आंखों का संपर्क",
    },
    "mr": {
        "ingestion": "गिळणे",
        "exposure": "संपर्क",
        "inhalation": "श्वास घेणे",
        "skin_contact": "त्वचा संपर्क",
        "eye_contact": "डोळ्यांचा संपर्क",
    },
}


def localize_toxin_categories(categories: list[str], language: str) -> str:
    mapping = TOXIN_CATEGORY_LABELS.get(language, TOXIN_CATEGORY_LABELS["en"])
    localized = [mapping.get(cat, cat.replace("_", " ")) for cat in categories]
    return ", ".join(localized) if localized else ""


def localize_guardrail_reasons(red_flag: dict[str, Any], language: str) -> list[str]:
    reasons = []
    cat_text = localize_guardrail_categories(red_flag.get("matched_categories", []), language)
    if cat_text:
        if language == "hi":
            reasons.append(f"गंभीर लक्षण पाए गए: {cat_text}।")
        elif language == "mr":
            reasons.append(f"गंभीर लक्षणे आढळली: {cat_text}।")
        else:
            reasons.append(f"Critical indicators detected: {cat_text}.")

    if red_flag.get("ambiguous"):
        if language == "hi":
            reasons.append("लक्षण स्पष्ट नहीं हैं; सुरक्षा के लिए रूढ़िवादी आपातकालीन मार्गदर्शन लागू किया गया।")
        elif language == "mr":
            reasons.append("लक्षण स्पष्ट नाहीत; सुरक्षिततेसाठी आपत्कालीन मार्गदर्शन दिले आहे।")
        else:
            reasons.append("Symptoms are uncertain; using conservative emergency-first guidance for safety.")
    return reasons


def localize_toxin_reasons(toxin_flag: dict[str, Any], language: str) -> list[str]:
    reasons = []
    cat_text = localize_toxin_categories(toxin_flag.get("matched_categories", []), language)
    if cat_text:
        if language == "hi":
            reasons.append(f"विषाक्त संपर्क के संकेत पाए गए: {cat_text}।")
        elif language == "mr":
            reasons.append(f"विषारी संपर्काचे संकेत आढळले: {cat_text}।")
        else:
            reasons.append(f"Toxin exposure indicators detected: {cat_text}.")

    if toxin_flag.get("ambiguous"):
        if language == "hi":
            reasons.append("संपर्क स्पष्ट नहीं है, फिर भी इसे आपातकाल माना गया।")
        elif language == "mr":
            reasons.append("संपर्क स्पष्ट नाही, तरीही हे आपत्काल समजले गेले।")
        else:
            reasons.append("Exposure is uncertain but potentially toxic; treated as emergency.")
    return reasons
