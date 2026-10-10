"""Prompts for the local Gemma triage call."""

from healstation.triage.localization import normalize_language
from healstation.triage.vitals import format_vitals_for_prompt

# Bumped whenever the system prompt or the user-message template changes, and
# recorded with every assessment (QA-06).
PROMPT_VERSION = "triage-v1"


GEMMA_SYSTEM_PROMPT = (
    "You are an experienced medical triage doctor providing offline clinical assessment. "
    "Analyze patient symptoms thoroughly and return a single valid JSON object. "
    "Do NOT wrap the JSON in markdown code fences. Output raw JSON only.\n\n"
    "CRITICAL SAFETY RULES:\n"
    "- chest pain / heart pain / radiating arm pain → urgency MUST be high\n"
    "- cannot breathe / severe breathlessness → urgency MUST be high\n"
    "- severe bleeding / unconscious / stroke signs → urgency MUST be high\n"
    "- any vital sign marked CRITICAL → urgency MUST be high\n\n"
    "JSON schema (all keys required):\n"
    "{\n"
    '  "urgency": "high" | "medium" | "low",\n'
    '  "reasons": ["string", ...],\n'
    '  "actions": ["string", ...],\n'
    '  "specialist": "cardiologist"|"dermatologist"|"neurologist"|"orthopedic"|"pulmonologist"|"urologist"|"nephrologist"|"psychiatrist"|"ophthalmologist"|"pediatrician"|"gynecologist"|"general",\n'
    '  "confidence": 0.0-1.0,\n'
    '  "doctor_response": "string"\n'
    "}\n\n"
    "The doctor_response field MUST follow this exact structure (write it in the patient's language):\n"
    "URGENCY: [HIGH/MEDIUM/LOW] [emoji: ⚠️ for high, ⚡ for medium, ✅ for low]\n"
    "CONFIDENCE: [XX]%\n\n"
    "CLINICAL REASONING:\n"
    "[2-3 sentences: what the symptoms suggest, relevant risk factors, likely diagnosis]\n\n"
    "IMMEDIATE ACTION:\n"
    "1. [most urgent action]\n"
    "2. [next action]\n"
    "3. [next action]\n"
    "(add up to 5 actions total as needed)\n\n"
    "SPECIALIST: [Specialist Name] — [Department]\n\n"
    "RED FLAGS — go to emergency immediately if:\n"
    "[2-3 specific warning signs that should trigger immediate emergency visit]\n\n"
    "For HIGH urgency: add a TIME SENSITIVITY section explaining why minutes matter.\n"
    "Keep doctor_response under 280 words. Use plain line breaks, no markdown bold/italic."
)


def build_local_gemma_prompt(
    patient_text: str,
    language: str,
    heart_rate: int | None = None,
    bp_systolic: int | None = None,
    bp_diastolic: int | None = None,
    spo2: int | None = None,
    temperature: float | None = None,
) -> str:
    language = normalize_language(language)
    vitals_str = format_vitals_for_prompt(heart_rate, bp_systolic, bp_diastolic, spo2, temperature)
    vitals_section = f"\nPatient Vitals: {vitals_str}" if vitals_str else ""

    lang_instruction = {
        "hi": "Write doctor_response entirely in Hindi (Devanagari script). Keep section headers like URGENCY, CONFIDENCE, CLINICAL REASONING, IMMEDIATE ACTION, SPECIALIST, RED FLAGS in English, but all body text in Hindi.",
        "mr": "Write doctor_response entirely in Marathi (Devanagari script). Keep section headers like URGENCY, CONFIDENCE, CLINICAL REASONING, IMMEDIATE ACTION, SPECIALIST, RED FLAGS in English, but all body text in Marathi.",
    }.get(language, "Write doctor_response in English.")

    return (
        f"Patient language: {language}. {lang_instruction}\n"
        f"Patient symptoms: {patient_text}.{vitals_section}\n\n"
        "Respond with a single JSON object following the schema in your instructions."
    )


# Ported from the retired brain_of_the_doctor.py. Not part of PROMPT_VERSION
# "triage-v1"; used from the v2 prompt onwards.
SPECIALIST_GUIDE = {
    "dermatologist": "skin conditions (acne, rashes, moles, dermatitis)",
    "cardiologist": "heart and blood-vessel problems",
    "orthopedic": "bone, joint and muscle problems",
    "ophthalmologist": "eye and vision problems",
    "neurologist": "brain and nerve problems",
    "psychiatrist": "mental health concerns",
    "pediatrician": "children's health",
    "gynecologist": "women's health and pregnancy",
    "pulmonologist": "lung and breathing problems",
    "urologist": "kidney stones, urinary and bladder problems",
    "nephrologist": "kidney disease, kidney failure, dialysis",
    "general": "general symptoms or unclear conditions",
}

# Words the speech-to-text model commonly mishears in Marathi and Hindi
# (misheard form → intended word).
TRANSCRIPTION_HINTS = {
    "mr": {"माला": "मला", "चांदात": "छातीत / अंगात", "काई जाले": "काय झाले", "बगुन": "आज / बघून"},
    "hi": {"मुझ": "मुझे", "छाति": "छाती", "सास": "सांस", "दील": "दिल"},
}
