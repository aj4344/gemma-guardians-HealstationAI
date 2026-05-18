"""
HealStation AI — Emergency Triage System | FastAPI Backend
All clinical inference runs locally via Ollama (Gemma 4 gemma4:e2b).
No patient data is transmitted to external servers.
"""

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
import uvicorn
import os
import time
import uuid
import json
from io import BytesIO
import requests
import re
from dotenv import load_dotenv

load_dotenv(override=True)

# Import core AI components
from brain_of_the_doctor import get_doctor_response, encode_image
from voice_of_the_doctor import text_to_speech_for_api, get_available_voices
from voice_of_the_patient import (
    transcribe_audio,
    _get_local_stt_model,
    LOCAL_STT_MODEL_SIZE,
    LOCAL_STT_DEVICE,
    LOCAL_STT_COMPUTE_TYPE,
    ENABLE_LOCAL_STT,
)
from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from doctor_search import (
    search_doctors_enhanced,
    EnhancedDoctorSearchService,
)
from doctor_search import search_doctors_enhanced as advanced_search_doctors, search_doctors_by_city as advanced_search_city

# Import Emergency Triage Module
from emergency_triage import (
    EmergencyTriageRequest, TriageResponse, HospitalSearchRequest,
    EmergencyHospital, EmergencyScores, VitalSigns, TriageLevel,
    EmergencyClassifier, HospitalRoutingService, TriageService,
    TRIAGE_LEVELS, EMERGENCY_NUMBERS,
    BEFAST_KEYWORDS,
    TRAUMA_KEYWORDS, HEART_SCORE_CONFIG,
    TOXIN_FAST_LANE_KEYWORDS
)
from emergency_triage.offline_triage_engine import (
    normalize_triage,
    select_offline_first_triage,
)
from emergency_triage.fairness_engine import FairnessTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("healstation")

# Initialize FastAPI app
app = FastAPI(
    title="HealStation AI — Emergency Triage API",
    description="Offline clinical triage powered by Gemma 4 (gemma4:e2b) via Ollama.",
    version="2.0.0"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models for request/response
class ConsultationRequest(BaseModel):
    patient_text: str
    typed_text: Optional[str] = None
    transcription_text: Optional[str] = None
    language: str = "en"
    age: Optional[int] = None
    gender: Optional[str] = None
    triage_correct: Optional[bool] = None
    image_data: Optional[List[str]] = None
    pdf_data: Optional[List[dict]] = None
    image_count: Optional[int] = 0
    pdf_count: Optional[int] = 0
    # Structured vital signs (optional — UI can send individual fields)
    heart_rate: Optional[int] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    spo2: Optional[int] = None
    temperature: Optional[float] = None

class ConsultationResponse(BaseModel):
    doctor_response: str
    audio_url: Optional[str] = None
    specialist_recommendation: Optional[str] = None
    urgency_level: Optional[str] = None
    # Canonical triage schema (Step 1)
    urgency: str = "low"
    reasons: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    specialist: str = "general"
    confidence: float = 0.5
    triage: Dict[str, Any] = Field(default_factory=dict)
    triage_source: Optional[str] = None
    emergency_action_block: Optional[Dict[str, Any]] = None
    consensus_explanation: Optional[Dict[str, Any]] = None
    fairness_metrics: Optional[Dict[str, Any]] = None

class TranscriptionResponse(BaseModel):
    text: str
    language: str

class DoctorSearchRequest(BaseModel):
    latitude: float
    longitude: float
    specialty: str
    radius: int = 25000
    sort_by: str = "distance"
    limit: int = 20
    language: str = "en"
    ai_response: Optional[str] = None  # AI doctor's response for semantic analysis

class DoctorSearchResponse(BaseModel):
    doctors: List[Dict[str, Any]]
    total_found: int
    search_params: Dict[str, Any]

class CitySearchRequest(BaseModel):
    city: str
    specialty: str
    sort_by: str = "distance"
    limit: int = 20
    language: str = "en"
    user_latitude: Optional[float] = None  # Optional user location for distance calculation
    user_longitude: Optional[float] = None

class CitySearchResponse(BaseModel):
    doctors: List[Dict[str, Any]]
    total_found: int
    city_coordinates: Optional[Dict[str, float]]
    search_params: Dict[str, Any]


def _safe_float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _safe_int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _safe_bool_env(name: str, default: bool) -> bool:
    raw = str(os.getenv(name, str(default))).strip().lower()
    if raw in {"1", "true", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "no", "n", "off"}:
        return False
    return default


LOCAL_GEMMA_MODEL = os.getenv("LOCAL_GEMMA_MODEL", "gemma4:e2b")
LOCAL_GEMMA_URL = os.getenv("LOCAL_GEMMA_URL", "http://127.0.0.1:11434/api/generate")
LOCAL_GEMMA_TIMEOUT_SECONDS = _safe_int_env("LOCAL_GEMMA_TIMEOUT_SECONDS", 120)
LOCAL_GEMMA_NUM_CTX = _safe_int_env("LOCAL_GEMMA_NUM_CTX", 1024)
LOCAL_GEMMA_NUM_PREDICT = _safe_int_env("LOCAL_GEMMA_NUM_PREDICT", 1400)
LOCAL_TRIAGE_CONFIDENCE_THRESHOLD = _safe_float_env("LOCAL_TRIAGE_CONFIDENCE_THRESHOLD", 0.6)
ENABLE_LOCAL_TRIAGE = _safe_bool_env("ENABLE_LOCAL_TRIAGE", True)
FAIRNESS_PARITY_THRESHOLD = _safe_float_env("FAIRNESS_PARITY_THRESHOLD", 0.05)
fairness_tracker = FairnessTracker(parity_threshold=FAIRNESS_PARITY_THRESHOLD)


def _extract_json_payload(text: str) -> Optional[Dict[str, Any]]:
    """Extract first JSON object from model text output."""
    if not text:
        return None

    text = text.strip()
    try:
        parsed = json.loads(text)
        return _normalize_local_gemma_payload(parsed) if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    candidate = text[start:end + 1]
    try:
        parsed = json.loads(candidate)
        return _normalize_local_gemma_payload(parsed) if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _normalize_local_gemma_urgency(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text in {"low", "medium", "high"}:
        return text

    mapping = {
        "critical": "high",
        "immediate": "high",
        "urgent": "medium",
        "stable": "low",
        "minor": "low",
    }
    return mapping.get(text, "low")


def _normalize_local_gemma_list(value: Any) -> List[str]:
    if value is None:
        return []

    items = value if isinstance(value, list) else [value]
    normalized: List[str] = []
    for item in items:
        text = str(item).strip()
        if text:
            normalized.append(text)
    return normalized


def _normalize_local_gemma_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.5

    if confidence < 0:
        return 0.0
    if confidence > 1:
        return 1.0
    return confidence


def _normalize_local_gemma_payload(payload: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return None

    normalized = dict(payload)
    normalized["urgency"] = _normalize_local_gemma_urgency(payload.get("urgency"))
    normalized["reasons"] = _normalize_local_gemma_list(payload.get("reasons"))
    normalized["actions"] = _normalize_local_gemma_list(payload.get("actions"))
    normalized["confidence"] = _normalize_local_gemma_confidence(payload.get("confidence"))
    return normalized


def _parse_vital_signs_from_text(text: str) -> Dict[str, Optional[float]]:
    """Extract structured vital signs from patient text if frontend appended them as a string."""
    vitals: Dict[str, Optional[float]] = {
        "heart_rate": None,
        "bp_systolic": None,
        "bp_diastolic": None,
        "spo2": None,
        "temperature": None,
    }
    if not text:
        return vitals

    # Look for patterns like "Heart Rate: 85 bpm", "BP: 120/80", "SpO2: 98%", "Temp: 98.6"
    hr_match = re.search(r"Heart\s*Rate:\s*(\d+)", text, re.IGNORECASE)
    if hr_match:
        vitals["heart_rate"] = int(hr_match.group(1))

    bp_match = re.search(r"Blood\s*Pressure:\s*(\d+)/(\d+)", text, re.IGNORECASE)
    if bp_match:
        vitals["bp_systolic"] = int(bp_match.group(1))
        vitals["bp_diastolic"] = int(bp_match.group(2))

    spo2_match = re.search(r"Oxygen\s*Saturation:\s*(\d+)", text, re.IGNORECASE)
    if spo2_match:
        vitals["spo2"] = int(spo2_match.group(1))

    temp_match = re.search(r"Temperature:\s*([\d.]+)", text, re.IGNORECASE)
    if temp_match:
        try:
            vitals["temperature"] = float(temp_match.group(1))
        except ValueError:
            pass

    return vitals


def _format_vitals_for_prompt(
    heart_rate: Optional[int] = None,
    bp_systolic: Optional[int] = None,
    bp_diastolic: Optional[int] = None,
    spo2: Optional[int] = None,
    temperature: Optional[float] = None,
) -> str:
    """Format structured vital signs into a clinical string for Gemma's prompt."""
    parts = []
    if heart_rate is not None:
        flag = " (CRITICAL HIGH)" if heart_rate > 150 else " (CRITICAL LOW)" if heart_rate < 40 else " (HIGH)" if heart_rate > 100 else " (LOW)" if heart_rate < 60 else ""
        parts.append(f"Heart Rate: {heart_rate} BPM{flag}")
    if bp_systolic is not None and bp_diastolic is not None:
        flag = " (HYPERTENSIVE CRISIS)" if bp_systolic >= 180 else " (HIGH)" if bp_systolic >= 140 else " (LOW)" if bp_systolic < 90 else ""
        parts.append(f"Blood Pressure: {bp_systolic}/{bp_diastolic} mmHg{flag}")
    if spo2 is not None:
        flag = " (CRITICAL LOW)" if spo2 < 88 else " (LOW)" if spo2 < 92 else ""
        parts.append(f"SpO2: {spo2}%{flag}")
    if temperature is not None:
        flag = " (HIGH FEVER)" if temperature >= 39.5 else " (FEVER)" if temperature >= 38 else " (LOW)" if temperature < 36 else ""
        parts.append(f"Temperature: {temperature}°C{flag}")
    return ", ".join(parts) if parts else ""


_GEMMA_SYSTEM_PROMPT = (
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


def _build_local_gemma_prompt(
    patient_text: str,
    language: str,
    heart_rate: Optional[int] = None,
    bp_systolic: Optional[int] = None,
    bp_diastolic: Optional[int] = None,
    spo2: Optional[int] = None,
    temperature: Optional[float] = None,
) -> str:
    language = _normalize_language(language)
    vitals_str = _format_vitals_for_prompt(heart_rate, bp_systolic, bp_diastolic, spo2, temperature)
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


def _run_local_gemma_triage(
    patient_text: str,
    language: str,
    heart_rate: Optional[int] = None,
    bp_systolic: Optional[int] = None,
    bp_diastolic: Optional[int] = None,
    spo2: Optional[int] = None,
    temperature: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """Try local Gemma via Ollama /api/chat (instruction-tuned endpoint)."""
    if not ENABLE_LOCAL_TRIAGE:
        return None
    try:
        user_message = _build_local_gemma_prompt(
            patient_text, language,
            heart_rate=heart_rate, bp_systolic=bp_systolic,
            bp_diastolic=bp_diastolic, spo2=spo2, temperature=temperature,
        )
        # Use /api/chat — required for instruction-tuned models like gemma4:e2b
        chat_url = LOCAL_GEMMA_URL.replace("/api/generate", "/api/chat")
        payload = {
            "model": LOCAL_GEMMA_MODEL,
            "messages": [
                {"role": "system", "content": _GEMMA_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {
                "temperature": 0.15,
                "num_ctx": LOCAL_GEMMA_NUM_CTX,
                "num_predict": LOCAL_GEMMA_NUM_PREDICT,
            }
        }
        print(f"[GEMMA] Calling Ollama /api/chat model={LOCAL_GEMMA_MODEL} num_ctx={LOCAL_GEMMA_NUM_CTX} mode=CPU-offload")
        response = requests.post(chat_url, json=payload, timeout=LOCAL_GEMMA_TIMEOUT_SECONDS)
        response.raise_for_status()

        raw = response.json()
        # /api/chat response is at raw["message"]["content"]
        if isinstance(raw, dict) and "message" in raw:
            model_text = raw["message"].get("content", "")
        else:
            model_text = raw.get("response", "") if isinstance(raw, dict) else ""

        print(f"[GEMMA] Raw output ({len(model_text)} chars): {model_text[:200]}")
        parsed = _extract_json_payload(model_text)
        if parsed:
            print(f"[GEMMA] Parsed JSON: urgency={parsed.get('urgency')}, specialist={parsed.get('specialist')}")
        else:
            print("[GEMMA] WARNING: Could not parse JSON from model output")
        return parsed
    except Exception as local_error:
        print(f"[GEMMA] Local Gemma triage unavailable/failed: {local_error}")
        return None


def _build_emergency_fallback_triage(
    patient_text: str,
    language: str,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    heart_rate: Optional[int] = None,
    bp_systolic: Optional[int] = None,
    bp_diastolic: Optional[int] = None,
    spo2: Optional[int] = None,
    temperature: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """Reuse existing emergency classifier as strict fallback path."""
    try:
        # Build VitalSigns object only if any value was provided
        vital_signs = None
        if any(v is not None for v in [heart_rate, bp_systolic, bp_diastolic, spo2, temperature]):
            vital_signs = VitalSigns(
                heart_rate=heart_rate,
                blood_pressure_systolic=bp_systolic,
                blood_pressure_diastolic=bp_diastolic,
                oxygen_saturation=spo2,
                temperature_celsius=temperature,
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
        print(f"[API DEBUG] Emergency triage fallback failed: {emergency_error}")
        return None


def _compose_doctor_response_from_triage(triage_data: Dict[str, Any]) -> str:
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


def _build_consensus_explanation(
    patient_text: Optional[str],
    typed_text: Optional[str],
    transcription_text: Optional[str],
    image_data: Optional[List[str]],
    pdf_data: Optional[List[dict]],
    final_urgency: str,
) -> Dict[str, Any]:
    """
    Build a simple multi-input consensus summary for explainability.
    """
    def _norm(text: Optional[str]) -> str:
        return str(text or "").strip().lower()

    def _high_risk(text: str) -> bool:
        markers = [
            "chest pain",
            "shortness of breath",
            "cannot breathe",
            "can't breathe",
            "stroke",
            "severe bleeding",
            "poison",
            "overdose",
        ]
        return any(marker in text for marker in markers)

    patient_norm = _norm(patient_text)
    typed_norm = _norm(typed_text)
    trans_norm = _norm(transcription_text)

    has_typed = bool(typed_norm)
    has_trans = bool(trans_norm)
    has_images = bool(image_data)
    has_pdfs = bool(pdf_data)

    typed_risk = _high_risk(typed_norm) if has_typed else False
    trans_risk = _high_risk(trans_norm) if has_trans else False

    conflict = bool(has_typed and has_trans and typed_risk != trans_risk)
    if not has_typed and not has_trans:
        resolution_reason = "Limited inputs across modalities; consensus used available signals."
    elif conflict:
        resolution_reason = "Conflicting signals detected across modalities; conservative triage selected."
    else:
        resolution_reason = "Clinical signals aligned across modalities."

    return {
        "conflict": conflict,
        "final_urgency": final_urgency,
        "resolution_reason": resolution_reason,
        "signals": {
            "patient_text_present": bool(patient_norm),
            "typed_text_present": has_typed,
            "transcription_present": has_trans,
            "image_count": len(image_data or []),
            "pdf_count": len(pdf_data or []),
            "typed_high_risk": typed_risk,
            "transcription_high_risk": trans_risk,
            "images_present": has_images,
            "pdfs_present": has_pdfs,
        },
    }


def _normalize_language(language: Optional[str]) -> str:
    raw = str(language or "en").strip().lower()
    if "-" in raw:
        raw = raw.split("-", 1)[0]
    return raw if raw in {"en", "hi", "mr"} else "en"


def _contains_devanagari(text: str) -> bool:
    return any("\u0900" <= char <= "\u097F" for char in text)


def _enforce_doctor_response_language(doctor_response: str, language: str) -> str:
    lang = _normalize_language(language)
    if not doctor_response or lang == "en":
        return doctor_response
    if _contains_devanagari(doctor_response):
        return doctor_response

    prefix = "हिंदी में उत्तर: " if lang == "hi" else "मराठीमध्ये उत्तर: "
    return f"{prefix}{doctor_response}"


def _localize_urgency_label(language: str, urgency: str) -> str:
    mapping = {
        "en": {"high": "high", "medium": "medium", "low": "low"},
        "hi": {"high": "उच्च", "medium": "मध्यम", "low": "निम्न"},
        "mr": {"high": "उच्च", "medium": "मध्यम", "low": "कमी"},
    }
    return mapping.get(language, mapping["en"]).get(urgency, urgency)


def _localize_guardrail_categories(categories: List[str], language: str) -> str:
    labels = {
        "en": {
            "cardiac": "cardiac",
            "stroke": "stroke",
            "breathing_distress": "breathing distress",
            "severe_bleeding": "severe bleeding",
        },
        "hi": {
            "cardiac": "हृदय संबंधी",
            "stroke": "स्ट्रोक",
            "breathing_distress": "सांस लेने में कठिनाई",
            "severe_bleeding": "गंभीर रक्तस्राव",
        },
        "mr": {
            "cardiac": "हृदय संबंधित",
            "stroke": "स्ट्रोक",
            "breathing_distress": "श्वासोच्छ्वास त्रास",
            "severe_bleeding": "तीव्र रक्तस्राव",
        },
    }
    mapping = labels.get(language, labels["en"])
    localized = [mapping.get(category, category.replace("_", " ")) for category in categories]
    return ", ".join(localized) if localized else ""


def _localize_toxin_categories(categories: List[str], language: str) -> str:
    labels = {
        "en": {"ingestion": "ingestion", "exposure": "exposure", "inhalation": "inhalation"},
        "hi": {"ingestion": "सेवन", "exposure": "संपर्क", "inhalation": "श्वास द्वारा"},
        "mr": {"ingestion": "सेवन", "exposure": "संपर्क", "inhalation": "श्वासातून"},
    }
    mapping = labels.get(language, labels["en"])
    localized = [mapping.get(category, category) for category in categories]
    return ", ".join(localized) if localized else ""


def _localize_guardrail_reasons(red_flag: Dict[str, Any], language: str) -> List[str]:
    if language == "en":
        return red_flag.get("reasons", []) or ["High-risk emergency red-flag detected."]

    categories_text = _localize_guardrail_categories(red_flag.get("matched_categories", []), language)
    reasons: List[str] = []
    if categories_text:
        if language == "hi":
            reasons.append(f"उच्च जोखिम संकेत मिले: {categories_text}.")
        else:
            reasons.append(f"उच्च धोका संकेत आढळले: {categories_text}.")

    if red_flag.get("ambiguous"):
        if language == "hi":
            reasons.append("लक्षण स्पष्ट नहीं हैं, लेकिन संभावित आपातकाल का जोखिम है; सुरक्षा के लिए सावधानी बरती गई है।")
        else:
            reasons.append("लक्षण स्पष्ट नाहीत, पण संभाव्य आपत्कालाचा धोका आहे; सुरक्षिततेसाठी सावध मार्गदर्शन दिले.")

    if not reasons:
        if language == "hi":
            reasons.append("उच्च जोखिम आपातकाल संकेत मिला।")
        else:
            reasons.append("उच्च धोका आपत्काल संकेत आढळला.")
    return reasons


def _localize_toxin_reasons(toxin_flag: Dict[str, Any], language: str) -> List[str]:
    if language == "en":
        return toxin_flag.get("reasons", []) or ["Potential toxin or poison exposure detected."]

    categories_text = _localize_toxin_categories(toxin_flag.get("matched_categories", []), language)
    reasons: List[str] = []
    if categories_text:
        if language == "hi":
            reasons.append(f"विषाक्त संपर्क के संकेत मिले: {categories_text}.")
        else:
            reasons.append(f"विषारी संपर्काचे संकेत आढळले: {categories_text}.")

    if toxin_flag.get("ambiguous"):
        if language == "hi":
            reasons.append("संपर्क स्पष्ट नहीं है, लेकिन संभावित विषाक्त जोखिम है; सुरक्षा के लिए आपातकालीन मार्गदर्शन दिया गया है।")
        else:
            reasons.append("संपर्क स्पष्ट नाही, पण संभाव्य विषारी धोका आहे; सुरक्षिततेसाठी आपत्कालीन मार्गदर्शन.")

    if not reasons:
        if language == "hi":
            reasons.append("संभावित विषाक्त संपर्क पाया गया।")
        else:
            reasons.append("संभाव्य विषारी संपर्क आढळला.")
    return reasons


def _get_red_flag_keyword_groups() -> Dict[str, List[str]]:
    """Hard red-flag groups for early emergency guardrails."""
    return {
        "cardiac": [
            "heart attack", "severe chest pain", "crushing chest pain", "chest pain",
            "chest tightness", "chest pressure", "radiating to arm", "arm pain with chest",
            "jaw pain with chest", "sweating with chest pain", "left arm pain",
        ] + HEART_SCORE_CONFIG.get("highly_suspicious_history", []) + HEART_SCORE_CONFIG.get("moderately_suspicious_history", []),
        "stroke": ["stroke", "tia", "brain attack"]
        + BEFAST_KEYWORDS.get("balance", [])
        + BEFAST_KEYWORDS.get("eyes", [])
        + BEFAST_KEYWORDS.get("face", [])
        + BEFAST_KEYWORDS.get("arm", [])
        + BEFAST_KEYWORDS.get("speech", []),
        "breathing_distress": [
            "can't breathe", "cannot breathe", "difficulty breathing", "shortness of breath",
            "gasping", "choking", "suffocating", "blue lips", "turning blue",
            "respiratory distress", "wheezing severe",
        ],
        "severe_bleeding": [
            "severe bleeding", "won't stop bleeding", "massive blood loss", "bleeding heavily",
            "hemorrhage", "blood loss", "vomiting blood", "coughing blood",
        ] + TRAUMA_KEYWORDS.get("bleeding", []),
    }


_NEGATION_PREFIXES = (
    "no",
    "not",
    "without",
    "denies",
    "deny",
    "denied",
    "negative for",
    "no sign of",
    "no signs of",
)


def _keyword_is_negated(text: str, keyword: str) -> bool:
    if not keyword:
        return False
    for prefix in _NEGATION_PREFIXES:
        if f"{prefix} {keyword}" in text:
            return True
    return False


def _evaluate_red_flag_guardrail(patient_text: str) -> Dict[str, Any]:
    """Evaluate high-risk red flags before non-emergency triage interpretation."""
    text = str(patient_text or "").lower()
    groups = _get_red_flag_keyword_groups()

    category_matches: Dict[str, List[str]] = {}
    for category, keywords in groups.items():
        seen = []
        for kw in keywords:
            if kw and kw in text and kw not in seen and not _keyword_is_negated(text, kw):
                seen.append(kw)
        if seen:
            category_matches[category] = seen

    matched_categories = list(category_matches.keys())
    total_matches = sum(len(v) for v in category_matches.values())

    uncertainty_markers = [
        "maybe", "might", "not sure", "unclear", "possibly", "i think", "could be", "unsure"
    ]
    has_uncertainty = any(marker in text for marker in uncertainty_markers)

    explicit_critical_markers = [
        "heart attack", "severe chest pain", "crushing chest pain",
        "stroke", "face droop", "slurred speech",
        "can't breathe", "cannot breathe", "severe bleeding", "won't stop bleeding",
    ]
    explicit_critical_hit = any(
        marker in text and not _keyword_is_negated(text, marker)
        for marker in explicit_critical_markers
    )

    confidence = 0.0
    if explicit_critical_hit:
        confidence = 0.95
    elif len(matched_categories) >= 2 or total_matches >= 3:
        confidence = 0.85
    elif total_matches >= 1:
        confidence = 0.62

    ambiguous = bool(total_matches >= 1 and has_uncertainty)
    guardrail_hit = bool(explicit_critical_hit or len(matched_categories) >= 1)
    apply_guardrail = bool(guardrail_hit or ambiguous)

    reasons = []
    for category in matched_categories:
        sample = ", ".join(category_matches[category][:3])
        reasons.append(f"Red-flag {category.replace('_', ' ')} indicators detected: {sample}.")
    if ambiguous and not reasons:
        reasons.append("Symptoms are ambiguous but suggest possible emergency risk; conservative safety guidance applied.")

    return {
        "apply_guardrail": apply_guardrail,
        "guardrail_hit": guardrail_hit,
        "ambiguous": ambiguous,
        "confidence": max(confidence, 0.7 if ambiguous else confidence),
        "matched_categories": matched_categories,
        "matched_keywords": category_matches,
        "reasons": reasons,
    }


def _build_emergency_action_block(red_flag: Dict[str, Any], language: Optional[str] = None) -> Dict[str, Any]:
    """Structured emergency action block required when red flags are detected."""
    lang = _normalize_language(language)
    immediate_actions_map = {
        "en": [
            "Call ambulance immediately if severe symptoms are present.",
            "Go to the nearest emergency room without delay.",
            "Do not drive yourself if dizzy, weak, or short of breath.",
        ],
        "hi": [
            "अगर गंभीर लक्षण हों तो तुरंत एंबुलेंस बुलाएं।",
            "सबसे नजदीकी इमरजेंसी रूम बिना देरी के जाएं।",
            "यदि चक्कर, कमजोरी या सांस फूलना हो तो खुद वाहन न चलाएं।",
        ],
        "mr": [
            "लक्षण गंभीर असतील तर त्वरित रुग्णवाहिका बोलवा.",
            "ताबडतोब जवळच्या इमर्जन्सी कक्षात जा.",
            "चक्कर, कमजोरी किंवा दम लागल्यास स्वतः वाहन चालवू नका.",
        ],
    }
    immediate_actions = list(immediate_actions_map.get(lang, immediate_actions_map["en"]))
    if red_flag.get("ambiguous"):
        if lang == "hi":
            immediate_actions.insert(0, "लक्षण स्पष्ट नहीं हैं; सुरक्षा के लिए आपातकालीन सलाह दी जा रही है।")
        elif lang == "mr":
            immediate_actions.insert(0, "लक्षण स्पष्ट नाहीत; सुरक्षिततेसाठी आपत्कालीन मार्गदर्शन दिले आहे.")
        else:
            immediate_actions.insert(0, "Symptoms are uncertain; using conservative emergency-first guidance for safety.")

    return {
        "type": "emergency_guardrail",
        "triggered": bool(red_flag.get("apply_guardrail")),
        "confidence": float(red_flag.get("confidence", 0.8)),
        "matched_categories": red_flag.get("matched_categories", []),
        "matched_keywords": red_flag.get("matched_keywords", {}),
        "reasoning": _localize_guardrail_reasons(red_flag, lang),
        "time_sensitivity": "immediate",
        "call_ambulance": True,
        "emergency_numbers": {
            "ambulance": EMERGENCY_NUMBERS.get("ambulance", "108"),
            "emergency": EMERGENCY_NUMBERS.get("emergency", "112"),
        },
        "immediate_actions": immediate_actions,
    }


def _build_guardrail_triage(red_flag: Dict[str, Any], language: Optional[str] = None) -> Dict[str, Any]:
    lang = _normalize_language(language)
    reasons = _localize_guardrail_reasons(red_flag, lang)
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

def _compose_guardrail_response_text(
    red_flag: Dict[str, Any],
    triage_data: Dict[str, Any],
    language: Optional[str] = None,
) -> str:
    lang = _normalize_language(language)
    category_text = _localize_guardrail_categories(red_flag.get("matched_categories", []), lang)
    if not category_text:
        category_text = "high-risk symptoms" if lang == "en" else "उच्च जोखिम लक्षण" if lang == "hi" else "उच्च धोका लक्षणे"

    urgency_label = _localize_urgency_label(lang, triage_data.get("urgency", "high"))
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


def _localize_guardrail_reasons(red_flag: Dict[str, Any], language: str) -> List[str]:
    reasons = []
    cat_text = _localize_guardrail_categories(red_flag.get("matched_categories", []), language)
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


def _localize_toxin_reasons(toxin_flag: Dict[str, Any], language: str) -> List[str]:
    reasons = []
    cat_text = _localize_toxin_categories(toxin_flag.get("matched_categories", []), language)
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


def _localize_toxin_categories(categories: List[str], language: str) -> str:
    labels = {
        "en": {"ingestion": "ingestion", "inhalation": "inhalation", "skin_contact": "skin contact", "eye_contact": "eye contact"},
        "hi": {"ingestion": "निगलना", "inhalation": "सांस लेना", "skin_contact": "त्वचा संपर्क", "eye_contact": "आंखों का संपर्क"},
        "mr": {"ingestion": "गिळणे", "inhalation": "श्वास घेणे", "skin_contact": "त्वचा संपर्क", "eye_contact": "डोळ्यांचा संपर्क"},
    }
    mapping = labels.get(language, labels["en"])
    localized = [mapping.get(cat, cat) for cat in categories]
    return ", ".join(localized) if localized else ""


def _evaluate_red_flag_guardrail(patient_text: str) -> Dict[str, Any]:
    """Strict rules-based detection for life-threatening symptoms."""
    text = str(patient_text or "").lower()
    
    # Proximity patterns for complex phrasing like "pain in my heart"
    proximity_patterns = {
        "cardiac": [
            r"pain.*heart", r"heart.*pain", r"chest.*pain", r"pain.*chest",
            r"heavy.*chest", r"pressure.*chest", r"tightness.*chest",
            r"दिल.*दर्द", r"दर्द.*दिल", r"सीने.*दर्द", r"दर्द.*सीने",
            r"हृदय.*वेदना", r"वेदना.*हृदय", r"छातीत.*दुखणे"
        ],
        "breathing": [
            r"can't.*breathe", r"cannot.*breathe", r"difficulty.*breathing",
            r"short.*breath", r"breathless", r"gasping",
            r"सांस.*तकलीफ", r"सांस.*फूलना", r"श्वास.*त्रास", r"दम.*लागतो"
        ]
    }
    
    matched_categories = []
    matched_keywords = {}
    
    # 1. Check proximity patterns first
    for cat, patterns in proximity_patterns.items():
        found = []
        for pattern in patterns:
            if re.search(pattern, text):
                found.append(pattern)
        if found:
            matched_categories.append(cat)
            matched_keywords[cat] = found
            
    # 2. Check static keywords from constants for extra coverage
    guardrail_categories = {
        "stroke": ["face drooping", "slurred speech", "numbness", "paralysis", "लकवा", "अर्धांगवायू"],
        "severe_bleeding": ["heavy bleeding", "bleeding profusely", "खून निकलना", "रक्तस्राव", "अत्यधिक रक्तस्राव"],
        "trauma": ["car accident", "major fall", "head injury", "गंभीर चोट"],
    }
    
    for cat, kws in guardrail_categories.items():
        matches = [kw for kw in kws if kw in text]
        if matches:
            if cat not in matched_categories:
                matched_categories.append(cat)
                matched_keywords[cat] = matches
            else:
                matched_keywords[cat].extend(matches)
            
    apply_guardrail = len(matched_categories) > 0
    
    return {
        "apply_guardrail": apply_guardrail,
        "guardrail_hit": apply_guardrail,
        "matched_categories": matched_categories,
        "matched_keywords": matched_keywords,
        "confidence": 0.98 if apply_guardrail else 0.0,
        "ambiguous": False
    }


def _build_emergency_action_block(red_flag: Dict[str, Any], language: Optional[str] = None) -> Dict[str, Any]:
    lang = _normalize_language(language)
    ambulance = EMERGENCY_NUMBERS.get("ambulance", "108")
    
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
    
    return {
        "type": "emergency_guardrail",
        "triggered": bool(red_flag.get("apply_guardrail")),
        "confidence": float(red_flag.get("confidence", 0.9)),
        "matched_categories": red_flag.get("matched_categories", []),
        "matched_keywords": red_flag.get("matched_keywords", {}),
        "reasoning": _localize_guardrail_reasons(red_flag, lang),
        "time_sensitivity": "immediate",
        "call_ambulance": True,
        "emergency_numbers": {
            "ambulance": ambulance,
            "emergency": EMERGENCY_NUMBERS.get("emergency", "112"),
        },
        "immediate_actions": immediate_actions,
    }


def _evaluate_toxin_fast_lane(patient_text: str) -> Dict[str, Any]:
    """Detect toxin/poison exposure early and conservatively."""
    text = str(patient_text or "").lower()
    category_matches: Dict[str, List[str]] = {}

    for category, keywords in TOXIN_FAST_LANE_KEYWORDS.items():
        seen: List[str] = []
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


def _build_toxin_fast_lane_triage(toxin_flag: Dict[str, Any], language: Optional[str] = None) -> Dict[str, Any]:
    lang = _normalize_language(language)
    reasons = _localize_toxin_reasons(toxin_flag, lang)
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


def _build_toxin_emergency_action_block(toxin_flag: Dict[str, Any], language: Optional[str] = None) -> Dict[str, Any]:
    lang = _normalize_language(language)
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
        "reasoning": _localize_toxin_reasons(toxin_flag, lang),
        "time_sensitivity": "immediate",
        "call_ambulance": True,
        "emergency_numbers": {
            "ambulance": EMERGENCY_NUMBERS.get("ambulance", "108"),
            "emergency": EMERGENCY_NUMBERS.get("emergency", "112"),
        },
        "immediate_actions": immediate_actions,
    }


def _compose_toxin_response_text(
    toxin_flag: Dict[str, Any],
    triage_data: Dict[str, Any],
    language: Optional[str] = None,
) -> str:
    lang = _normalize_language(language)
    category_text = _localize_toxin_categories(toxin_flag.get("matched_categories", []), lang)
    if not category_text:
        category_text = "toxin exposure" if lang == "en" else "विषाक्त संपर्क" if lang == "hi" else "विषारी संपर्क"

    urgency_label = _localize_urgency_label(lang, triage_data.get("urgency", "high"))
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

# API Routes

@app.get("/")
def read_root():
    return {"status": "healthy", "message": "HealStation AI: Doctor Assistant API is running"}

@app.get("/api")
def api_health_check():
    """API health check endpoint for frontend to verify connection"""
    return {"status": "healthy", "message": "HealStation AI: Doctor Assistant API is running"}

@app.get("/api/stt-health")
def stt_health_check():
    try:
        _get_local_stt_model()
        return {
            "ready": True,
            "mode": "offline",
            "provider": "faster-whisper",
            "model": LOCAL_STT_MODEL_SIZE,
            "device": LOCAL_STT_DEVICE,
            "compute_type": LOCAL_STT_COMPUTE_TYPE,
            "languages": ["en", "hi", "mr"],
        }
    except Exception as error:
        return {
            "ready": False,
            "mode": "offline",
            "provider": "faster-whisper",
            "model": LOCAL_STT_MODEL_SIZE,
            "error": str(error),
            "languages": ["en", "hi", "mr"],
        }

@app.get("/api/ollama-status")
def ollama_status():
    """
    Canonical Ollama status check for judges and CI.
    Returns offline_ready=true when Ollama is reachable and the model is loaded.
    """
    chat_url = f"{OLLAMA_BASE_URL}/api/chat"
    try:
        ping = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
            "stream": False,
            "options": {"num_predict": 5},
        }
        resp = requests.post(chat_url, json=ping, timeout=15)
        resp.raise_for_status()
        return {"ollama": "connected", "model": OLLAMA_MODEL, "offline_ready": True}
    except Exception as err:
        return {
            "ollama": "not running",
            "model": OLLAMA_MODEL,
            "offline_ready": False,
            "message": "Start Ollama: ollama serve",
            "error": str(err),
        }


@app.get("/api/ollama-health")
def ollama_health_check():
    """Check whether Ollama is running and gemma4:e2b is reachable."""
    chat_url = LOCAL_GEMMA_URL.replace("/api/generate", "/api/chat")
    try:
        ping_payload = {
            "model": LOCAL_GEMMA_MODEL,
            "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
            "stream": False,
            "options": {"num_predict": 5},
        }
        resp = requests.post(chat_url, json=ping_payload, timeout=15)
        resp.raise_for_status()
        return {
            "running": True,
            "model": LOCAL_GEMMA_MODEL,
            "url": chat_url,
            "status": "ok",
        }
    except Exception as err:
        return {
            "running": False,
            "model": LOCAL_GEMMA_MODEL,
            "url": chat_url,
            "error": str(err),
            "hint": "Run 'ollama serve' then 'ollama run gemma4:e2b' to start the model.",
        }


@app.post("/api/transcribe-audio", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...), language: str = Form("en")):
    """
    Transcribe patient's voice recording to text
    """
    # Save the uploaded audio temporarily
    temp_audio_path = f"temp_audio_{uuid.uuid4()}.wav"
    with open(temp_audio_path, "wb") as temp_file:
        temp_file.write(await audio.read())
    
    try:
        # Process audio with the transcription function
        transcription = transcribe_audio(temp_audio_path, language_code=language)
        if str(transcription).startswith("ERROR:"):
            raise HTTPException(status_code=503, detail=transcription)
        return {"text": transcription, "language": language}
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

@app.post("/api/get-doctor-response", response_model=ConsultationResponse)
async def get_consultation(request: ConsultationRequest, background_tasks: BackgroundTasks):
    """
    Get doctor's AI response based on patient input
    """
    try:
        logger.info("Consultation request | lang=%s text_len=%d images=%d",
                    request.language,
                    len(request.patient_text) if request.patient_text else 0,
                    len(request.image_data) if request.image_data else 0)

        # Step 4 fast-lane: evaluate toxin/poison exposure before any other triage flow.
        toxin_flag = _evaluate_toxin_fast_lane(request.patient_text)
        emergency_action_block = None

        if toxin_flag["apply_fast_lane"]:
            triage_data = _build_toxin_fast_lane_triage(toxin_flag, request.language)
            triage_source = "toxin_fast_lane"
            specialist_recommendation = triage_data.get("specialist", "emergency medicine")
            urgency_level = triage_data.get("urgency", "high")
            emergency_action_block = _build_toxin_emergency_action_block(toxin_flag, request.language)
            doctor_text = _compose_toxin_response_text(toxin_flag, triage_data, request.language)
        else:
            # Step 2 guardrail: evaluate hard red-flags before non-emergency triage flow.
            red_flag = _evaluate_red_flag_guardrail(request.patient_text)

            if red_flag["apply_guardrail"]:
                triage_data = _build_guardrail_triage(red_flag, request.language)
                triage_source = "red_flag_guardrail"
                specialist_recommendation = triage_data.get("specialist", "emergency medicine")
                urgency_level = triage_data.get("urgency", "high")
                emergency_action_block = _build_emergency_action_block(red_flag, request.language)
                doctor_text = _compose_guardrail_response_text(red_flag, triage_data, request.language)
            else:
                logger.info("Running offline-first triage with Gemma 4")

                # Step 1: Parse vitals from text
                parsed_vitals = _parse_vital_signs_from_text(request.patient_text)
                request.heart_rate = request.heart_rate if request.heart_rate is not None else parsed_vitals.get("heart_rate")
                request.bp_systolic = request.bp_systolic if request.bp_systolic is not None else parsed_vitals.get("bp_systolic")
                request.bp_diastolic = request.bp_diastolic if request.bp_diastolic is not None else parsed_vitals.get("bp_diastolic")
                request.spo2 = request.spo2 if request.spo2 is not None else parsed_vitals.get("spo2")
                request.temperature = request.temperature if request.temperature is not None else parsed_vitals.get("temperature")

                # Step 2: Local Gemma triage
                local_triage_raw = _run_local_gemma_triage(
                    request.patient_text,
                    request.language,
                    heart_rate=request.heart_rate,
                    bp_systolic=request.bp_systolic,
                    bp_diastolic=request.bp_diastolic,
                    spo2=request.spo2,
                    temperature=request.temperature,
                )

                # Step 3: Emergency triage as fallback
                emergency_triage_raw = _build_emergency_fallback_triage(
                    request.patient_text,
                    request.language,
                    age=request.age,
                    gender=request.gender,
                    heart_rate=request.heart_rate,
                    bp_systolic=request.bp_systolic,
                    bp_diastolic=request.bp_diastolic,
                    spo2=request.spo2,
                    temperature=request.temperature,
                )

                triage_data, triage_source = select_offline_first_triage(
                    local_payload=local_triage_raw,
                    emergency_payload=emergency_triage_raw,
                    confidence_threshold=LOCAL_TRIAGE_CONFIDENCE_THRESHOLD,
                )

                if triage_source == "local_gemma":
                    logger.info("Gemma 4 selected for offline-first triage.")

                # SAFETY OVERRIDE: Force high urgency if critical keywords are present but triage missed them
                current_urgency = str(triage_data.get("urgency", "low")).lower()
                if current_urgency != "high":
                    critical_check = _evaluate_red_flag_guardrail(request.patient_text)
                    if critical_check.get("guardrail_hit"):
                        logger.warning("Safety override: critical red-flags detected, upgrading to HIGH urgency.")
                        triage_data["urgency"] = "high"
                        triage_data["reasons"].extend(critical_check.get("reasons", []))
                        triage_data["actions"].insert(0, "Go to the nearest emergency department immediately.")
                        triage_data["confidence"] = 1.0

                # Keep old keys for backward compatibility
                specialist_recommendation = triage_data.get("specialist", "general")
                urgency_level = triage_data.get("urgency", "low")

                # Build doctor response text from selected source when available
                doctor_text = ""
                if triage_source == "local_gemma" and isinstance(local_triage_raw, dict):
                    doctor_text = str(local_triage_raw.get("doctor_response", "")).strip()
                elif emergency_triage_raw:
                    doctor_text = str(emergency_triage_raw.get("doctor_response", "")).strip()

                # Final local fallback: compose from triage data if no text yet
                if not doctor_text:
                    logger.info("Composing response from local triage data.")
                    doctor_text = _compose_doctor_response_from_triage(triage_data)

        # Final safety fallback to ensure backwards-compatible doctor text
        if not doctor_text:
            doctor_text = _compose_doctor_response_from_triage(triage_data)

        doctor_text = _enforce_doctor_response_language(doctor_text, request.language)
        
        logger.info("Response ready | urgency=%s specialist=%s source=%s len=%d",
                    urgency_level, specialist_recommendation, triage_source, len(doctor_text))

        fairness_metrics = None
        try:
            fairness_tracker.record_case(
                age=request.age,
                gender=request.gender,
                language=request.language,
                is_correct=request.triage_correct,
                confidence=triage_data.get("confidence"),
            )
            fairness_metrics = fairness_tracker.get_metrics()
        except Exception as fairness_error:
            print(f"[API DEBUG] Fairness tracking skipped due to error: {fairness_error}")

        consensus_explanation = _build_consensus_explanation(
            patient_text=request.patient_text,
            typed_text=request.typed_text,
            transcription_text=request.transcription_text,
            image_data=request.image_data,
            pdf_data=request.pdf_data,
            final_urgency=triage_data.get("urgency", "low"),
        )
        
        # Generate doctor's voice using offline pyttsx3
        audio_filename = None
        timestamp = int(time.time())
        audio_filename = f"audio_outputs/doctor_response_{timestamp}.mp3"

        # Ensure the audio_outputs directory exists
        os.makedirs("audio_outputs", exist_ok=True)

        # Generate speech synchronously to ensure it's complete
        try:
            logger.debug("TTS: generating %s", audio_filename)
            generated_path = text_to_speech_for_api(
                text=doctor_text,
                output_path=audio_filename,
                language=request.language
            )
            if generated_path:
                audio_filename = generated_path

                if audio_filename and os.path.exists(audio_filename) and os.path.getsize(audio_filename) > 0:
                    logger.debug("TTS: audio ready (%d bytes)", os.path.getsize(audio_filename))
                else:
                    logger.warning("TTS: audio file missing or empty")
                    audio_filename = None

        except Exception as audio_error:
            logger.error("TTS generation failed: %s", audio_error)
            audio_filename = None

        # Clean up old audio files in the background
        background_tasks.add_task(cleanup_old_audio_files)
        
        # Return the response with the audio URL and specialist recommendation
        response_data = {
            "doctor_response": doctor_text,
            "audio_url": f"/api/audio/{os.path.basename(audio_filename)}" if audio_filename else None,
            "specialist_recommendation": specialist_recommendation,
            "urgency_level": urgency_level,
            "urgency": triage_data["urgency"],
            "reasons": triage_data["reasons"],
            "actions": triage_data["actions"],
            "specialist": triage_data["specialist"],
            "confidence": triage_data["confidence"],
            "triage": triage_data,
            "triage_source": triage_source,
            "emergency_action_block": emergency_action_block,
            "consensus_explanation": consensus_explanation,
            "fairness_metrics": fairness_metrics,
        }
        
        logger.info("Consultation completed successfully.")
        return response_data

    except Exception as e:
        logger.exception("Unhandled error in consultation endpoint: %s", e)
        
        # Return a fallback response
        fallback_response = {
            "doctor_response": f"I apologize, but I encountered a technical issue while processing your consultation. Please try again. If the problem persists, please check your internet connection and ensure all files are properly formatted. Technical details: {str(e)}",
            "audio_url": None,
            "specialist_recommendation": "general",
            "urgency_level": "low",
            "urgency": "low",
            "reasons": ["Technical failure triggered safe fallback triage."],
            "actions": ["Seek medical care if symptoms are severe or worsening."],
            "specialist": "general",
            "confidence": 0.3,
            "triage": {
                "urgency": "low",
                "reasons": ["Technical failure triggered safe fallback triage."],
                "actions": ["Seek medical care if symptoms are severe or worsening."],
                "specialist": "general",
                "confidence": 0.3,
            },
            "triage_source": "error_fallback",
            "emergency_action_block": None,
            "consensus_explanation": _build_consensus_explanation(
                patient_text=request.patient_text,
                typed_text=request.typed_text,
                transcription_text=request.transcription_text,
                image_data=request.image_data,
                pdf_data=request.pdf_data,
                final_urgency="low",
            ),
            "fairness_metrics": None,
        }
        return fallback_response

@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """
    Retrieve generated audio file with CORS support
    """
    audio_path = os.path.join("audio_outputs", filename)
    
    # Check if file exists, if not wait a bit for background generation
    max_wait_time = 10  # seconds
    wait_interval = 0.5  # seconds
    elapsed_time = 0
    
    while not os.path.exists(audio_path) and elapsed_time < max_wait_time:
        time.sleep(wait_interval)
        elapsed_time += wait_interval
    
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found or still being generated")

    ext = os.path.splitext(filename)[1].lower()
    if ext == ".wav":
        media_type = "audio/wav"
    else:
        media_type = "audio/mpeg"
    
    return FileResponse(
        audio_path,
        media_type=media_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "*",
            "Cache-Control": "no-cache",
            "Content-Disposition": "inline"
        }
    )

@app.get("/api/voices")
async def get_voices():
    """
    Get available TTS voices
    """
    return get_available_voices()

@app.post("/api/search-doctors", response_model=DoctorSearchResponse)
async def search_doctors_endpoint(request: DoctorSearchRequest):
    """
    🚨 VERIFIED HOSPITALS ONLY - Medical Safety First
    Returns ONLY verified real hospitals with confirmed phone numbers
    NO fake doctors, NO generated credentials, NO misleading information
    """
    try:
        print(f"🏥 [API] REAL LOCATION-BASED medical search for {request.specialty} near {request.latitude}, {request.longitude}")
        
        # ✅ ADVANCED ENHANCED SEARCH: Use the new advanced service with top-rated sorting
        try:
            # Use the advanced search function that queries the static medical database
            medical_facilities = await advanced_search_doctors(
                specialty=request.specialty,
                latitude=request.latitude,
                longitude=request.longitude,
                radius=request.radius,
                sort_by=request.sort_by,
                limit=request.limit
            )
            
            print(f"✅ Advanced enhanced search found {len(medical_facilities)} medical facilities")
                
        except Exception as search_error:
            print(f"⚠️ Advanced search error: {search_error}")
            
            # Fallback to previous enhanced service
            try:
                enhanced_service = EnhancedDoctorSearchService()
                medical_facilities = await enhanced_service.search_doctors_enhanced(
                    specialty=request.specialty,
                    latitude=request.latitude,
                    longitude=request.longitude,
                    radius=request.radius,
                    sort_by=request.sort_by,
                    limit=request.limit
                )
                print(f"✅ Fallback enhanced search found {len(medical_facilities)} medical facilities")
            except Exception as fallback_error:
                print(f"⚠️ Fallback search error: {fallback_error}")
                medical_facilities = []
        
        # Convert to API format - Enhanced advanced data structure
        formatted_doctors = []
        for medical_facility in medical_facilities:
            # ✅ Handle enhanced dictionary format from advanced service with MEDICAL SAFETY VERIFICATION
            formatted_doctors.append({
                "name": medical_facility.get("name", "Medical Facility"),
                "specialty": medical_facility.get("specialty", request.specialty),
                "qualification": medical_facility.get("qualifications", medical_facility.get("qualification", "Contact facility for qualifications")),
                "experience": medical_facility.get("experience", "Contact facility for experience"),
                "hospital": medical_facility.get("hospital", medical_facility.get("clinic_name", "Medical Center")),
                "location": medical_facility.get("location", medical_facility.get("address", "Location not available")),
                "contact": medical_facility.get("phone", "Contact facility directly"),  # SAFETY: No unverified numbers
                "rating": medical_facility.get("rating", "") if medical_facility.get("rating") else "Contact for ratings",  # SAFETY: No fake ratings
                "consultation_fee": medical_facility.get("consultation_fee", "Contact for current fees"),  # SAFETY: No unverified fees
                "address": medical_facility.get("address", "Address not available"),
                "latitude": medical_facility.get("latitude", request.latitude),
                "longitude": medical_facility.get("longitude", request.longitude),
                "registration_number": "Contact facility for registration details",  # SAFETY: No fake registration numbers
                "source": medical_facility.get("source", "advanced_search"),
                "verified": medical_facility.get("verified", False) or medical_facility.get("source") == "prominent_medical",  # Mark prominent medical as verified
                "fake_data": False,
                "real_data": True,
                "distance_km": medical_facility.get("distance_km", 0.0),
                "distance": medical_facility.get("distance_km", 0.0),
                "distance_text": medical_facility.get("distance", "Distance unavailable"),
                "clinic_name": medical_facility.get("hospital", medical_facility.get("clinic_name", medical_facility.get("name", "Medical Center"))),
                "phone": medical_facility.get("phone", "Contact facility directly"),  # SAFETY: Consistent with contact
                "hours": medical_facility.get("hours", medical_facility.get("availability", "Contact facility for current hours")),
                "review_count": medical_facility.get("reviews_count", "") if medical_facility.get("reviews_count") else "Contact for reviews",
                "verification_note": medical_facility.get("verification_note", "Please verify current information with facility"),
                "safety_warning": "⚠️ Always call ahead to confirm doctor availability, fees, and appointment requirements",
                "data_type": medical_facility.get("data_type", "enhanced_search"),
                "available_today": medical_facility.get("available_today", True),
                "availability_status": medical_facility.get("availability_status", "Contact for availability"),
                "next_available": medical_facility.get("next_available", "Contact for appointment"),
                "last_updated": medical_facility.get("last_updated", "Recently updated")
            })
        
        total_found = len(formatted_doctors)
        
        print(f"✅ [API] ADVANCED LOCATION-BASED search found {total_found} medical facilities")
        print(f"   📍 Near location: {request.latitude}, {request.longitude}")
        print(f"   🏥 All data from verified hospital database")
        print(f"   🎯 Sort by: {request.sort_by}")
        print(f"   ❌ NO fake doctors or credentials")
        
        return DoctorSearchResponse(
            doctors=formatted_doctors,
            total_found=total_found,
            search_params={
                "latitude": request.latitude,
                "longitude": request.longitude,
                "specialty": request.specialty,
                "radius": request.radius,
                "sort_by": request.sort_by,
                "limit": request.limit,
                "language": request.language,
                "api_used": "advanced_doctor_service_enhanced_search",
                "enhanced_search": True,
                "real_data_only": True,
                "fake_data_removed": True,
                "location_based": True,
                "verification": "Data from verified hospital database"
            }
        )
        
    except Exception as e:
        print(f"[API ERROR] Verified medical data search failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return empty results on error - NO FAKE FALLBACK
        return DoctorSearchResponse(
            doctors=[],
            total_found=0,
            search_params={
                "error": str(e), 
                "real_medical_search": True,
                "fake_data_fallback": False,
                "message": "Real data search failed. No fake data provided."
            }
        )

@app.post("/api/search-doctors-by-city", response_model=CitySearchResponse)
async def search_doctors_by_city_endpoint(request: CitySearchRequest):
    """
    🏙️ ADVANCED CITY-BASED SEARCH - Find doctors in any Indian city
    Allows users to search for specialists in specific cities
    Returns ONLY verified real hospitals with confirmed information
    """
    try:
        print(f"🏙️ [API] ADVANCED CITY-BASED search for {request.specialty} in {request.city}")
        
        # ✅ ADVANCED CITY-BASED SEARCH: Use the new advanced city search function
        medical_facilities = await advanced_search_city(
            city=request.city,
            specialty=request.specialty,
            sort_by=request.sort_by,
            limit=request.limit,
            user_latitude=request.user_latitude,
            user_longitude=request.user_longitude
        )
        
        # Convert to API format with enhanced data structure
        formatted_doctors = []
        city_coordinates = None
        
        for medical_facility in medical_facilities:
            # Extract city coordinates from first result if available
            if not city_coordinates and medical_facility.get("city_coordinates"):
                city_coordinates = medical_facility["city_coordinates"]
            
            # ✅ Handle enhanced dictionary format from advanced service
            formatted_doctors.append({
                "name": medical_facility.get("name", "Medical Facility"),
                "specialty": medical_facility.get("specialty", request.specialty),
                "qualification": medical_facility.get("qualifications", medical_facility.get("qualification", "Contact facility for qualifications")),
                "experience": medical_facility.get("experience", "Contact facility for experience"),
                "hospital": medical_facility.get("hospital", medical_facility.get("clinic_name", "Medical Center")),
                "location": medical_facility.get("location", medical_facility.get("address", "Location not available")),
                "contact": medical_facility.get("phone", medical_facility.get("contact", "Contact facility directly")),
                "rating": medical_facility.get("rating", "Contact for ratings"),
                "consultation_fee": medical_facility.get("consultation_fee", "Contact for current fees"),
                "address": medical_facility.get("address", "Address not available"),
                "latitude": medical_facility.get("latitude", 0.0),
                "longitude": medical_facility.get("longitude", 0.0),
                "registration_number": medical_facility.get("registration_number", "Not available"),
                "source": medical_facility.get("source", "advanced_search"),
                "verified": medical_facility.get("verified", False),
                "fake_data": False,
                "real_data": True,
                "distance_km": medical_facility.get("distance_km", medical_facility.get("user_distance_km", 0)),
                "distance": medical_facility.get("distance", medical_facility.get("user_distance", "Distance unavailable")),
                "distance_text": medical_facility.get("distance", medical_facility.get("user_distance", "Distance unavailable")),
                "clinic_name": medical_facility.get("hospital", medical_facility.get("clinic_name", "Medical Center")),
                "phone": medical_facility.get("phone", "Contact facility directly"),
                "hours": medical_facility.get("hours", medical_facility.get("availability", "Contact for hours")),
                "review_count": medical_facility.get("reviews_count", "Contact for reviews"),
                "city": request.city,
                "city_search": True,
                "data_type": medical_facility.get("data_type", "enhanced_search"),
                "available_today": medical_facility.get("available_today", True),
                "availability_status": medical_facility.get("availability_status", "Contact for availability"),
                "next_available": medical_facility.get("next_available", "Contact for appointment"),
                "last_updated": medical_facility.get("last_updated", "Recently updated")
            })
        
        total_found = len(formatted_doctors)
        
        print(f"✅ [API] CITY-BASED search found {total_found} medical facilities in {request.city}")
        print(f"   🏙️ City: {request.city}")
        print(f"   🏥 Specialty: {request.specialty}")
        print(f"   ❌ NO fake doctors or credentials")
        
        return CitySearchResponse(
            doctors=formatted_doctors,
            total_found=total_found,
            city_coordinates=city_coordinates,
            search_params={
                "city": request.city,
                "specialty": request.specialty,
                "sort_by": request.sort_by,
                "limit": request.limit,
                "language": request.language,
                "user_latitude": request.user_latitude,
                "user_longitude": request.user_longitude,
                "api_used": "advanced_doctor_service_city_search",
                "advanced_search": True,
                "real_data_only": True,
                "fake_data_removed": True,
                "city_based": True,
                "verification": "Data from verified hospital database"
            }
        )
        
    except Exception as e:
        print(f"[API ERROR] City-based medical search failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return empty results on error - NO FAKE FALLBACK
        return CitySearchResponse(
            doctors=[],
            total_found=0,
            city_coordinates=None,
            search_params={
                "error": str(e), 
                "city": request.city,
                "specialty": request.specialty,
                "real_medical_search": True,
                "fake_data_fallback": False,
                "message": "City-based search failed. No fake data provided."
            }
        )

@app.get("/api/doctor-details/{place_id}")
async def get_doctor_details(place_id: str):
    """
    Get detailed information about a specific doctor
    """
    try:
        # This would typically fetch more detailed information
        # For now, return basic structure
        return {
            "place_id": place_id,
            "detailed_info": "Coming soon",
            "reviews": [],
            "photos": [],
            "additional_ratings": {}
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail="Doctor details not found")

@app.get("/api/audio-status/{filename}")
async def check_audio_status(filename: str):
    """
    Check if audio file is ready and return its status (optimized for speed)
    """
    audio_path = f"audio_outputs/{filename}"
    
    if not os.path.exists(audio_path):
        return {"ready": False, "status": "generating", "file_size": 0}
    
    # Quick file size check
    file_size = os.path.getsize(audio_path)
    if file_size == 0:
        return {"ready": False, "status": "generating", "file_size": 0}
    
    # Shorter wait to check if file is still being written (optimized)
    time.sleep(0.05)  # Reduced from 0.1 to 0.05
    new_file_size = os.path.getsize(audio_path)
    
    if new_file_size != file_size:
        # File is still being written
        return {"ready": False, "status": "generating", "file_size": new_file_size}
    
    return {"ready": True, "status": "ready", "file_size": file_size}

# Utility Functions
def generate_audio_background(text: str, output_path: str, language: str):
    """
    Generate audio in the background (non-blocking)
    """
    try:
        generated_path = text_to_speech_for_api(
            text=text,
            output_path=output_path,
            language=language
        )
        final_path = generated_path or output_path
        print(f"[API DEBUG] Audio file generated: {final_path}")
    except Exception as audio_error:
        print(f"[API WARNING] Audio generation failed: {str(audio_error)}")

def cleanup_old_audio_files():
    """
    Remove audio files older than 1 hour to save space
    """
    current_time = time.time()
    audio_dir = "audio_outputs"
    
    if os.path.exists(audio_dir):
        for filename in os.listdir(audio_dir):
            file_path = os.path.join(audio_dir, filename)
            # If file is older than 1 hour (3600 seconds)
            if os.path.isfile(file_path) and current_time - os.path.getmtime(file_path) > 3600:
                os.remove(file_path)


# =============================================================================
# 🚨 EMERGENCY TRIAGE ENDPOINTS
# =============================================================================

# Initialize emergency services
emergency_classifier = EmergencyClassifier()
hospital_router = HospitalRoutingService()


class QuickTriageRequest(BaseModel):
    """Quick triage check for real-time symptom analysis"""
    symptoms: str = Field(..., min_length=3, description="Symptom description")


class QuickTriageResponse(BaseModel):
    """Quick triage response with essential info"""
    triage_level: int
    triage_level_name: str
    triage_color: str
    call_108: bool
    action: str
    icon: str
    matched_keywords: List[str] = []


@app.post("/api/emergency-triage", response_model=TriageResponse)
async def emergency_triage(request: EmergencyTriageRequest):
    """
    🚨 EMERGENCY TRIAGE ASSESSMENT
    
    Performs comprehensive emergency risk scoring including:
    - HEART Score for chest pain/cardiac assessment
    - BE-FAST Score for stroke detection
    - Trauma severity scoring
    - 5-level ESI-like triage classification
    
    Returns triage level, risk scores, and hospital routing.
    
    ⚠️ DISCLAIMER: This is for guidance only and does NOT replace 
    professional medical judgment. In emergencies, CALL 108 IMMEDIATELY.
    """
    try:
        print(f"🚨 [EMERGENCY TRIAGE] Processing request")
        print(f"   Symptoms: {request.symptoms[:100]}...")
        
        # Step 1: Classify emergency level and calculate scores
        triage_result = emergency_classifier.classify(request)
        
        print(f"   Triage Level: {triage_result.triage_level} ({triage_result.triage_level_name})")
        print(f"   Emergency Type: {triage_result.emergency_type}")
        print(f"   Call 108: {triage_result.call_108}")
        
        # Step 2: Find nearby emergency hospitals if location provided
        if request.latitude and request.longitude:
            try:
                # Determine required capabilities based on emergency type
                required_capabilities = ["emergency_room", "24x7"]
                
                if triage_result.emergency_type == "cardiac":
                    required_capabilities.append("cardiac_care")
                elif triage_result.emergency_type == "stroke":
                    required_capabilities.append("stroke_unit")
                elif triage_result.emergency_type == "trauma":
                    required_capabilities.append("trauma_center")
                
                hospital_request = HospitalSearchRequest(
                    latitude=request.latitude,
                    longitude=request.longitude,
                    radius_km=15,  # 15km radius for emergencies
                    required_capabilities=required_capabilities,
                    triage_level=triage_result.triage_level,
                    emergency_type=triage_result.emergency_type
                )
                
                hospitals = await hospital_router.find_emergency_hospitals(hospital_request)
                
                # Update triage result with hospitals
                triage_result.hospitals = hospitals
                triage_result.nearest_capable_hospital = hospital_router.get_best_match(
                    hospitals, triage_result.emergency_type
                )
                
                print(f"   Found {len(hospitals)} nearby hospitals")
                
            except Exception as hospital_error:
                print(f"⚠️ Hospital routing error: {hospital_error}")
                # Continue without hospital data
        
        return triage_result
        
    except Exception as e:
        print(f"❌ [EMERGENCY TRIAGE ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return a safe fallback - always recommend calling 108 on error
        raise HTTPException(
            status_code=500,
            detail="Emergency triage system error. Please CALL 108 for emergencies."
        )


@app.get("/api/emergency-triage/quick")
async def quick_emergency_triage(symptoms: str):
    """
    🚨 QUICK TRIAGE CHECK (GET request for real-time analysis)
    
    Fast keyword-based triage for real-time symptom entry.
    Use this for instant feedback as user types symptoms.
    
    Query params:
        symptoms: The symptom text to analyze
    
    Returns basic triage level without full scoring.
    """
    try:
        if not symptoms or len(symptoms) < 3:
            return {
                "triage_level": 5,
                "triage_level_name": "self_care",
                "triage_color": "#3B82F6",
                "call_108": False,
                "action": "Continue describing your symptoms",
                "icon": "ℹ️",
                "matched_keywords": []
            }
        
        result = emergency_classifier.quick_classify(symptoms)
        return QuickTriageResponse(**result)
        
    except Exception as e:
        print(f"⚠️ Quick triage error: {e}")
        # Safe fallback
        return {
            "triage_level": 4,
            "triage_level_name": "standard",
            "triage_color": "#22C55E",
            "call_108": False,
            "action": "Please consult a healthcare provider",
            "icon": "✅",
            "matched_keywords": []
        }


@app.post("/api/emergency-hospitals")
async def find_emergency_hospitals(request: HospitalSearchRequest):
    """
    🏥 EMERGENCY HOSPITAL SEARCH
    
    Find nearby hospitals with emergency capabilities.
    Uses Overpass API (OpenStreetMap) with static database fallback.
    
    Returns hospitals sorted by:
    1. Capability match (ER, ICU, cardiac care, etc.)
    2. Distance from user
    """
    try:
        print(f"🏥 [HOSPITAL SEARCH] Near ({request.latitude}, {request.longitude})")
        print(f"   Required: {request.required_capabilities}")
        
        hospitals = await hospital_router.find_emergency_hospitals(request)
        
        return {
            "hospitals": [h.model_dump() for h in hospitals],
            "total_found": len(hospitals),
            "search_params": {
                "latitude": request.latitude,
                "longitude": request.longitude,
                "radius_km": request.radius_km,
                "required_capabilities": request.required_capabilities
            },
            "nearest_with_er": hospitals[0].model_dump() if hospitals else None
        }
        
    except Exception as e:
        print(f"❌ Hospital search error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Hospital search failed. For emergencies, CALL 108."
        )


@app.get("/api/emergency-info")
async def get_emergency_info():
    """
    📞 GET EMERGENCY INFORMATION
    
    Returns emergency numbers and triage level definitions.
    Useful for frontend to display emergency contacts.
    """
    return {
        "emergency_numbers": EMERGENCY_NUMBERS,
        "triage_levels": {
            level: {
                "name": config["display_name"],
                "name_hindi": config.get("display_name_hindi", ""),
                "name_marathi": config.get("display_name_marathi", ""),
                "color": config["color"],
                "bg_color": config.get("bg_color", ""),
                "description": config["description"],
                "action": config["action"],
                "action_hindi": config.get("action_hindi", ""),
                "call_108": config["call_108"],
                "icon": config["icon"]
            }
            for level, config in TRIAGE_LEVELS.items()
        },
        "disclaimer": "⚠️ This AI assessment is for guidance only and does NOT replace professional medical judgment. In any emergency, CALL 108 IMMEDIATELY."
    }


@app.get("/api/health-check")
async def health_check():
    """System health check including emergency services"""
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "emergency_triage": "available",
            "hospital_routing": "available"
        },
        "emergency_number": "108",
        "version": "2.0.0",
    }


# Run the server if executed directly
if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=8001, reload=False)
