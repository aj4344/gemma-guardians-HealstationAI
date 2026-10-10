"""
HealStation AI — Emergency Triage System | FastAPI Backend
All clinical inference runs locally via Ollama (Gemma 4 gemma4:e2b).
No patient data is transmitted to external servers.
"""

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Tuple
import logging
import uvicorn
import os
import time
import uuid
import json
import requests
import re
import tempfile
from contextlib import asynccontextmanager

# config loads .env before anything below reads the environment
from config import (
    API_HOST,
    API_PORT,
    AUDIO_OUTPUT_DIR,
    AUDIO_RETENTION_SECONDS,
    CORS_ALLOW_ORIGINS,
    ENABLE_LOCAL_TRIAGE,
    FAIRNESS_PARITY_THRESHOLD,
    FRONTEND_DIST_DIR,
    LOCAL_GEMMA_MODEL,
    LOCAL_GEMMA_NUM_CTX,
    LOCAL_GEMMA_NUM_PREDICT,
    LOCAL_GEMMA_TIMEOUT_SECONDS,
    LOCAL_GEMMA_URL,
    LOCAL_TRIAGE_CONFIDENCE_THRESHOLD,
    LOCAL_TTS_ENABLED,
    MAX_AUDIO_UPLOAD_MB,
    MAX_REQUEST_MB,
)

# Import core AI components
from voice_of_the_doctor import text_to_speech_for_api, get_available_voices
from voice_of_the_patient import (
    transcribe_audio,
    _get_local_stt_model,
    LOCAL_STT_MODEL_SIZE,
    LOCAL_STT_DEVICE,
    LOCAL_STT_COMPUTE_TYPE,
    ENABLE_LOCAL_STT,
)
from doctor_search import search_doctors_enhanced as advanced_search_doctors, search_doctors_by_city as advanced_search_city

# Import Emergency Triage Module
from emergency_triage import (
    EmergencyTriageRequest, TriageResponse, HospitalSearchRequest,
    VitalSigns, EmergencyClassifier, HospitalRoutingService,
    TRIAGE_LEVELS, EMERGENCY_NUMBERS,
    TOXIN_FAST_LANE_KEYWORDS
)
from emergency_triage.constants import VITAL_SIGNS_CRITICAL
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

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Recordings from a previous run may hold patient data; purge stale ones.
    cleanup_old_audio_files()
    yield


# Initialize FastAPI app
app = FastAPI(
    title="HealStation AI — Emergency Triage API",
    description="Offline clinical triage powered by Gemma 4 (gemma4:e2b) via Ollama.",
    version="2.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    """Reject oversized bodies before they are read into memory."""
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_REQUEST_MB * 1024 * 1024:
        return JSONResponse(status_code=413, content={"detail": f"Request body exceeds {MAX_REQUEST_MB} MB."})
    return await call_next(request)

# CORS: only the configured UI origins may call the API from a browser.
# A wildcard would let any website the health worker visits read patient
# triage results from this local server. No cookies are used, so no
# credentials are allowed either.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Models for request/response
MAX_TEXT_CHARS = 20_000
MAX_ATTACHMENTS = 8


class ConsultationRequest(BaseModel):
    patient_text: str = Field(..., min_length=1, max_length=MAX_TEXT_CHARS)
    typed_text: Optional[str] = Field(None, max_length=MAX_TEXT_CHARS)
    transcription_text: Optional[str] = Field(None, max_length=MAX_TEXT_CHARS)
    language: str = Field("en", max_length=16)
    age: Optional[int] = Field(None, ge=0, le=130)
    gender: Optional[str] = Field(None, max_length=32)
    triage_correct: Optional[bool] = None
    image_data: Optional[List[str]] = Field(None, max_length=MAX_ATTACHMENTS)
    pdf_data: Optional[List[dict]] = Field(None, max_length=MAX_ATTACHMENTS)
    image_count: Optional[int] = 0
    pdf_count: Optional[int] = 0
    # Structured vital signs (optional — UI can send individual fields).
    # Bounds only reject impossible values; critical readings stay accepted.
    heart_rate: Optional[int] = Field(None, ge=0, le=400)
    bp_systolic: Optional[int] = Field(None, ge=0, le=400)
    bp_diastolic: Optional[int] = Field(None, ge=0, le=300)
    spo2: Optional[int] = Field(None, ge=0, le=100)
    temperature: Optional[float] = Field(None, ge=20, le=46)

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


# Accept a legacy /api/generate URL from older .env files; triage uses /api/chat.
LOCAL_GEMMA_CHAT_URL = LOCAL_GEMMA_URL.replace("/api/generate", "/api/chat")
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


def _normalize_local_gemma_urgency(value: Any) -> Optional[str]:
    """Map the model's urgency label to low/medium/high.

    Unrecognised labels return None so the payload fails validation and the
    rules-based classifier is used, instead of silently defaulting to "low".
    """
    text = str(value or "").strip().lower()
    if text in {"low", "medium", "high"}:
        return text

    mapping = {
        "critical": "high",
        "emergency": "high",
        "immediate": "high",
        "severe": "high",
        "urgent": "medium",
        "moderate": "medium",
        "stable": "low",
        "minor": "low",
        "routine": "low",
    }
    return mapping.get(text)


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

    # Accepts the UI placeholder format ("BP: 140/90, Heart Rate: 85 bpm,
    # Temp: 101°F, Oxygen: 96%") as well as long forms ("Blood Pressure: ...").
    hr_match = re.search(r"\b(?:heart\s*rate|hr|pulse)\s*[:=]?\s*(\d{2,3})\b", text, re.IGNORECASE)
    if hr_match:
        vitals["heart_rate"] = int(hr_match.group(1))

    bp_match = re.search(r"\b(?:blood\s*pressure|bp)\s*[:=]?\s*(\d{2,3})\s*/\s*(\d{2,3})\b", text, re.IGNORECASE)
    if bp_match:
        vitals["bp_systolic"] = int(bp_match.group(1))
        vitals["bp_diastolic"] = int(bp_match.group(2))

    spo2_match = re.search(
        r"\b(?:oxygen(?:\s*saturation)?|sp\s*o2|o2\s*sat(?:uration)?|saturation)\s*[:=]?\s*(\d{2,3})\b",
        text,
        re.IGNORECASE,
    )
    if spo2_match:
        vitals["spo2"] = int(spo2_match.group(1))

    temp_match = re.search(
        r"\b(?:temperature|temp)\s*[:=]?\s*(\d{2,3}(?:\.\d+)?)\s*°?\s*([cf])?\b",
        text,
        re.IGNORECASE,
    )
    if temp_match:
        temperature = float(temp_match.group(1))
        unit = (temp_match.group(2) or "").lower()
        # No body temperature in Celsius exceeds 45, so larger values are Fahrenheit.
        if unit == "f" or (not unit and temperature > 45):
            temperature = (temperature - 32) * 5 / 9
        vitals["temperature"] = round(temperature, 1)

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
        chat_url = LOCAL_GEMMA_CHAT_URL
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
        logger.info("Calling Ollama model=%s num_ctx=%d", LOCAL_GEMMA_MODEL, LOCAL_GEMMA_NUM_CTX)
        response = requests.post(chat_url, json=payload, timeout=LOCAL_GEMMA_TIMEOUT_SECONDS)
        response.raise_for_status()

        raw = response.json()
        # /api/chat response is at raw["message"]["content"]
        if isinstance(raw, dict) and "message" in raw:
            model_text = raw["message"].get("content", "")
        else:
            model_text = raw.get("response", "") if isinstance(raw, dict) else ""

        logger.debug("Model output received (%d chars)", len(model_text))
        parsed = _extract_json_payload(model_text)
        if parsed:
            logger.info("Model triage parsed: urgency=%s specialist=%s", parsed.get("urgency"), parsed.get("specialist"))
        else:
            logger.warning("Could not parse JSON from model output")
        return parsed
    except Exception as local_error:
        logger.warning("Local Gemma triage unavailable/failed: %s", local_error)
        return None


def _clamp_vital(value: Optional[float], low: float, high: float, as_int: bool = True):
    if value is None:
        return None
    clamped = min(max(value, low), high)
    return int(round(clamped)) if as_int else float(clamped)


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
        # Build VitalSigns object only if any value was provided. Values are
        # clamped into the model's accepted range: the most extreme readings
        # (e.g. SpO2 45%) would otherwise fail validation and drop the whole
        # fallback. Clamped values stay beyond every critical threshold.
        vital_signs = None
        if any(v is not None for v in [heart_rate, bp_systolic, bp_diastolic, spo2, temperature]):
            vital_signs = VitalSigns(
                heart_rate=_clamp_vital(heart_rate, 30, 250),
                blood_pressure_systolic=_clamp_vital(bp_systolic, 50, 250),
                blood_pressure_diastolic=_clamp_vital(bp_diastolic, 30, 150),
                oxygen_saturation=_clamp_vital(spo2, 50, 100),
                temperature_celsius=_clamp_vital(temperature, 34, 43, as_int=False),
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


_UNASSESSED_MESSAGES = {
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

_ASSESSMENT_FAILED_MESSAGES = {
    "en": "The assessment could not be completed due to a technical problem. Please try again. If symptoms are severe, call 108 now.",
    "hi": "तकनीकी समस्या के कारण आकलन पूरा नहीं हो सका। कृपया फिर से प्रयास करें। लक्षण गंभीर हों तो तुरंत 108 पर कॉल करें।",
    "mr": "तांत्रिक अडचणीमुळे मूल्यांकन पूर्ण होऊ शकले नाही. कृपया पुन्हा प्रयत्न करा. लक्षणे गंभीर असल्यास त्वरित 108 वर कॉल करा.",
}


def _localized_message(messages: Dict[str, str], language: Optional[str]) -> str:
    return messages.get(_normalize_language(language), messages["en"])


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


_GUARDRAIL_CATEGORY_LABELS = {
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


def _localize_guardrail_categories(categories: List[str], language: str) -> str:
    mapping = _GUARDRAIL_CATEGORY_LABELS.get(language, _GUARDRAIL_CATEGORY_LABELS["en"])
    localized = [mapping.get(category, category.replace("_", " ")) for category in categories]
    return ", ".join(localized) if localized else ""


_TOXIN_CATEGORY_LABELS = {
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


def _localize_toxin_categories(categories: List[str], language: str) -> str:
    mapping = _TOXIN_CATEGORY_LABELS.get(language, _TOXIN_CATEGORY_LABELS["en"])
    localized = [mapping.get(cat, cat.replace("_", " ")) for cat in categories]
    return ", ".join(localized) if localized else ""


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


# ── Red-flag guardrail ────────────────────────────────────────────────────────
# Hard, rules-based detection of life-threatening presentations. Runs before the
# model so an unavailable or wrong model can never downgrade these cases.
# Latin-script phrases match on word boundaries; Devanagari phrases match as
# substrings (Hindi/Marathi inflect by suffix, e.g. छाती → छातीत).
_RED_FLAG_KEYWORDS: Dict[str, List[str]] = {
    "cardiac": [
        "heart attack", "chest pain", "chest tightness", "chest pressure", "chest heaviness",
        "crushing chest", "pain radiating to arm", "radiating to left arm", "radiating to jaw",
        "left arm pain", "arm pain with chest", "jaw pain with chest", "sweating with chest pain",
        # Hindi
        "दिल का दौरा", "हार्ट अटैक", "सीने में दर्द", "सीने में दबाव", "सीने में जकड़न",
        "सीने में भारीपन", "छाती में दर्द", "दिल में दर्द", "बाएं हाथ में दर्द",
        # Marathi
        "हृदयविकाराचा झटका", "हार्ट अटॅक", "छातीत दुखणे", "छातीत दुखत", "छातीत दडपण",
        "छातीवर दडपण", "छातीत घट्टपणा", "छातीत जडपणा", "छातीत वेदना", "हृदयात वेदना",
        "डाव्या हातात वेदना",
    ],
    "stroke": [
        "stroke", "tia", "brain attack", "face droop", "face drooping", "facial droop",
        "facial drooping", "slurred speech", "speech is slurred", "sudden confusion",
        "trouble speaking", "can't speak", "cannot speak", "weakness on one side",
        "weakness one side", "one side weak", "one sided weakness", "one-sided weakness",
        "numbness on one side", "sudden numbness", "can't lift my arm", "can't lift my left arm",
        "can't lift my right arm", "paralysis", "paralyzed", "sudden vision loss",
        "worst headache of my life",
        # Hindi
        "लकवा", "चेहरा टेढ़ा", "चेहरा लटक", "बोली अस्पष्ट", "लड़खड़ाती बोली",
        "बोल नहीं पा रहा", "बोल नहीं पा रही", "एक तरफ कमजोरी", "हाथ ऊपर नहीं उठ",
        # Marathi
        "अर्धांगवायू", "चेहरा वाकडा", "चेहरा लटक", "अस्पष्ट बोलणे", "बोलता येत नाही",
        "एक बाजू कमजोर", "हात वर उचलता येत नाही",
    ],
    "breathing_distress": [
        "can't breathe", "cannot breathe", "can not breathe", "unable to breathe",
        "difficulty breathing", "trouble breathing", "struggling to breathe", "hard to breathe",
        "shortness of breath", "short of breath", "breathless", "breathlessness", "gasping",
        "choking", "suffocating", "blue lips", "turning blue", "respiratory distress",
        "not breathing", "stopped breathing",
        # Hindi
        "सांस नहीं ले पा", "सांस लेने में तकलीफ", "सांस लेने में दिक्कत", "सांस फूल",
        "सांस की कमी", "दम घुट", "सांस रुक", "सांस बंद",
        # Marathi
        "श्वास घेता येत नाही", "श्वास घेण्यास त्रास", "श्वास घेण्यास अडचण", "श्वास कोंड",
        "दम लागत", "श्वास बंद",
    ],
    "severe_bleeding": [
        "severe bleeding", "heavy bleeding", "bleeding heavily", "bleeding profusely",
        "won't stop bleeding", "wont stop bleeding", "bleeding won't stop", "bleeding wont stop",
        "massive blood loss", "hemorrhage", "haemorrhage", "vomiting blood", "coughing blood",
        "coughing up blood", "soaked in blood",
        # Hindi
        "खून नहीं रुक रहा", "खून बंद नहीं", "बहुत खून", "अत्यधिक रक्तस्राव", "खून की उल्टी",
        "रक्तस्राव",
        # Marathi
        "खून थांबत नाही", "रक्त थांबत नाही", "खूप रक्त", "तीव्र रक्तस्राव", "रक्ताची उलटी",
    ],
    "trauma": [
        "car accident", "road accident", "bike accident", "motorcycle accident",
        "hit by a car", "hit by a vehicle", "major fall", "fall from height", "fell from height",
        "head injury", "gunshot", "stab wound", "stabbed", "electrocuted", "electric shock",
        # Hindi
        "गंभीर चोट", "सड़क दुर्घटना", "कार एक्सीडेंट", "बाइक एक्सीडेंट", "गाड़ी दुर्घटना",
        "सिर में चोट", "ऊंचाई से गिर", "ऊँचाई से गिर", "करंट लग",
        # Marathi
        "गंभीर दुखापत", "रस्ता अपघात", "कार अपघात", "गाडी अपघात", "मोटरसायकल अपघात",
        "डोक्याला मार", "उंचीवरून पड", "शॉक लाग",
    ],
    "unconscious": [
        "unconscious", "unresponsive", "not responding", "won't wake up", "wont wake up",
        "collapsed",
        # Hindi
        "बेहोश", "होश नहीं",
        # Marathi
        "बेशुद्ध", "शुद्ध हरपली",
    ],
    "seizure": [
        "seizure", "seizures", "convulsion", "convulsions", "convulsing",
        # Hindi
        "मिर्गी", "झटके आ",
        # Marathi
        "फेफरे", "झटके येत", "फिट आली",
    ],
    "anaphylaxis": [
        "anaphylaxis", "anaphylactic", "throat closing", "throat is closing", "throat swelling",
        "tongue swelling", "severe allergic reaction",
        # Hindi
        "गला बंद हो",
        # Marathi
        "घसा बंद होत",
    ],
    "self_harm": [
        "suicide attempt", "attempted suicide", "suicidal", "kill myself", "end my life",
        "want to die", "self harm", "self-harm", "cut myself",
        # Hindi
        "आत्महत्या", "खुद को मार", "जान दे दूं",
        # Marathi
        "स्वतःला मार", "जीव द्यायचा",
    ],
}

# Phrases that alone justify maximum confidence.
_EXPLICIT_CRITICAL_KEYWORDS = {
    "heart attack", "crushing chest", "stroke", "face droop", "face drooping", "slurred speech",
    "can't breathe", "cannot breathe", "not breathing", "stopped breathing", "severe bleeding",
    "won't stop bleeding", "unconscious", "unresponsive", "anaphylaxis", "suicide attempt",
    "दिल का दौरा", "हृदयविकाराचा झटका", "बेहोश", "बेशुद्ध", "लकवा", "अर्धांगवायू",
}

# Separator between words that does not cross a clause boundary.
_SEP = r"[^\w.,;:!?\n।]+"
_RED_FLAG_PATTERNS: Dict[str, List["re.Pattern[str]"]] = {
    "cardiac": [
        # "pain in my heart", "pressure on the chest"
        re.compile(rf"\b(?:pain|ache|pressure|tightness|heaviness|discomfort)\b(?:{_SEP}\w+){{0,3}}?{_SEP}(?:heart|chest)\b"),
        # "my chest hurts", "heart is aching"
        re.compile(rf"\b(?:heart|chest)\b(?:{_SEP}\w+){{0,2}}?{_SEP}(?:pain|pains|ache|aches|aching|pressure|tightness|heaviness|discomfort|hurts?|hurting)\b"),
        re.compile(r"(?:दिल|सीने|छाती|हृदय)\S*\s+(?:\S+\s+){0,2}?(?:दर्द|दबाव|जकड़न|भारीपन|वेदना|दुख|दडपण)"),
        re.compile(r"(?:दर्द|वेदना)\s+(?:\S+\s+){0,2}?(?:दिल|सीने|छाती|हृदय)"),
    ],
    "breathing_distress": [
        re.compile(rf"\b(?:can'?t|cannot|unable to|hard to|difficult to|struggling to|trouble)\b(?:{_SEP}\w+){{0,2}}?{_SEP}(?:breathe|breathing)\b"),
        re.compile(r"सांस\S*\s+(?:\S+\s+){0,3}?(?:तकलीफ|दिक्कत|फूल|नहीं ले|रुक)"),
        re.compile(r"श्वास\S*\s+(?:\S+\s+){0,3}?(?:त्रास|अडचण|येत नाही|कोंड|बंद)"),
    ],
}

_UNCERTAINTY_MARKERS = (
    "maybe", "might", "not sure", "unclear", "possibly", "i think", "could be", "unsure",
    "शायद", "पता नहीं", "कदाचित", "माहित नाही",
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


_RED_FLAG_KEYWORD_REGEXES: Dict[str, List[Tuple[str, "re.Pattern[str]"]]] = {
    category: [(kw, _keyword_regex(kw)) for kw in keywords]
    for category, keywords in _RED_FLAG_KEYWORDS.items()
}


def _normalize_symptom_text(text: Optional[str]) -> str:
    return str(text or "").lower().replace("’", "'").replace("‘", "'")


def _is_negated(text: str, start: int) -> bool:
    window = text[max(0, start - 40):start]
    clause = re.split(r"[.,;:!?\n।]", window)[-1]
    return bool(_NEGATION_RE.search(clause))


def _first_unnegated_match(pattern: "re.Pattern[str]", text: str) -> Optional[str]:
    for match in pattern.finditer(text):
        if not _is_negated(text, match.start()):
            return match.group(0)
    return None


def _evaluate_red_flag_guardrail(patient_text: str) -> Dict[str, Any]:
    """Evaluate high-risk red flags before any model-based triage."""
    text = _normalize_symptom_text(patient_text)

    category_matches: Dict[str, List[str]] = {}
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
    has_uncertainty = any(marker in text for marker in _UNCERTAINTY_MARKERS)
    explicit_critical_hit = any(
        kw in _EXPLICIT_CRITICAL_KEYWORDS for kws in category_matches.values() for kw in kws
    )

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
        reasons.append("Symptoms are ambiguous but suggest possible emergency risk; conservative safety guidance applied.")

    return {
        "apply_guardrail": guardrail_hit,
        "guardrail_hit": guardrail_hit,
        "ambiguous": ambiguous,
        "confidence": confidence,
        "matched_categories": matched_categories,
        "matched_keywords": category_matches,
        "reasons": reasons,
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


def _build_emergency_action_block(red_flag: Dict[str, Any], language: Optional[str] = None) -> Dict[str, Any]:
    lang = _normalize_language(language)
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
        immediate_actions.insert(0, {
            "hi": "लक्षण स्पष्ट नहीं हैं; सुरक्षा के लिए आपातकालीन सलाह दी जा रही है।",
            "mr": "लक्षण स्पष्ट नाहीत; सुरक्षिततेसाठी आपत्कालीन मार्गदर्शन दिले आहे.",
        }.get(lang, "Symptoms are uncertain; using conservative emergency-first guidance for safety."))

    emergency_numbers = {
        "ambulance": ambulance,
        "emergency": EMERGENCY_NUMBERS.get("emergency", "112"),
    }
    if "self_harm" in categories and mental_health:
        emergency_numbers["mental_health"] = mental_health
        immediate_actions.append({
            "hi": f"व्यक्ति को अकेला न छोड़ें। मानसिक स्वास्थ्य हेल्पलाइन: {mental_health}।",
            "mr": f"व्यक्तीला एकटे सोडू नका. मानसिक आरोग्य हेल्पलाइन: {mental_health}.",
        }.get(lang, f"Do not leave the person alone. Mental health helpline: {mental_health}."))

    return {
        "type": "emergency_guardrail",
        "triggered": bool(red_flag.get("apply_guardrail")),
        "confidence": float(red_flag.get("confidence", 0.9)),
        "matched_categories": categories,
        "matched_keywords": red_flag.get("matched_keywords", {}),
        "reasoning": _localize_guardrail_reasons(red_flag, lang),
        "time_sensitivity": "immediate",
        "call_ambulance": True,
        "emergency_numbers": emergency_numbers,
        "immediate_actions": immediate_actions,
    }


def _critical_vital_findings(
    heart_rate: Optional[float] = None,
    bp_systolic: Optional[float] = None,
    bp_diastolic: Optional[float] = None,
    spo2: Optional[float] = None,
    temperature: Optional[float] = None,
) -> List[str]:
    """Vital signs in the critical range (emergency_triage.constants thresholds)."""
    limits = VITAL_SIGNS_CRITICAL
    findings = []
    if heart_rate is not None and not limits["heart_rate_low"] <= heart_rate <= limits["heart_rate_high"]:
        findings.append(f"Heart rate {heart_rate:g} BPM is in the critical range.")
    if bp_systolic is not None and not limits["systolic_bp_low"] <= bp_systolic <= limits["systolic_bp_high"]:
        findings.append(f"Systolic blood pressure {bp_systolic:g} mmHg is in the critical range.")
    if bp_diastolic is not None and bp_diastolic > limits["diastolic_bp_high"]:
        findings.append(f"Diastolic blood pressure {bp_diastolic:g} mmHg is in the critical range.")
    if spo2 is not None and spo2 < limits["oxygen_saturation_low"]:
        findings.append(f"Oxygen saturation {spo2:g}% is critically low.")
    if temperature is not None and not limits["temperature_low"] <= temperature <= limits["temperature_high"]:
        findings.append(f"Temperature {temperature:g}°C is in the critical range.")
    return findings


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

_AUDIO_FILENAME_RE = re.compile(r"^doctor_response_[0-9a-f]{32}\.(?:wav|mp3)$")


def _audio_path_for(filename: str) -> str:
    """Resolve a generated-audio filename, rejecting anything we did not create."""
    if not _AUDIO_FILENAME_RE.fullmatch(filename or ""):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return os.path.join(AUDIO_OUTPUT_DIR, filename)


def _generate_response_audio(text: str, language: str) -> Optional[str]:
    """Speak the response with offline TTS; returns its URL or None."""
    if not LOCAL_TTS_ENABLED:
        return None
    os.makedirs(AUDIO_OUTPUT_DIR, exist_ok=True)
    # Random names: these files contain health information and are served
    # without authentication, so they must not be guessable.
    output_path = os.path.join(AUDIO_OUTPUT_DIR, f"doctor_response_{uuid.uuid4().hex}.wav")
    try:
        generated_path = text_to_speech_for_api(text=text, output_path=output_path, language=language)
    except Exception:
        logger.exception("TTS generation failed")
        return None
    if not generated_path or not os.path.exists(generated_path) or os.path.getsize(generated_path) == 0:
        logger.warning("TTS: audio file missing or empty")
        return None
    return f"/api/audio/{os.path.basename(generated_path)}"


# API Routes

_FRONTEND_BUILT = (FRONTEND_DIST_DIR / "index.html").is_file()

if not _FRONTEND_BUILT:
    @app.get("/")
    def read_root():
        return {"status": "healthy", "message": "HealStation AI: Doctor Assistant API is running"}

@app.get("/api")
def api_health_check():
    """API health check endpoint for frontend to verify connection"""
    return {"status": "healthy", "message": "HealStation AI: Doctor Assistant API is running"}

@app.get("/api/stt-health")
def stt_health_check():
    if not ENABLE_LOCAL_STT:
        return {
            "ready": False,
            "mode": "offline",
            "provider": "faster-whisper",
            "model": LOCAL_STT_MODEL_SIZE,
            "error": "Speech-to-text is disabled (ENABLE_LOCAL_STT=false).",
            "languages": ["en", "hi", "mr"],
        }
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
    try:
        ping = {
            "model": LOCAL_GEMMA_MODEL,
            "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
            "stream": False,
            "options": {"num_predict": 5},
        }
        resp = requests.post(LOCAL_GEMMA_CHAT_URL, json=ping, timeout=15)
        resp.raise_for_status()
        return {"ollama": "connected", "model": LOCAL_GEMMA_MODEL, "offline_ready": True}
    except Exception as err:
        return {
            "ollama": "not running",
            "model": LOCAL_GEMMA_MODEL,
            "offline_ready": False,
            "message": "Start Ollama: ollama serve",
            "error": str(err),
        }


@app.get("/api/ollama-health")
def ollama_health_check():
    """Check whether Ollama is running and gemma4:e2b is reachable."""
    chat_url = LOCAL_GEMMA_CHAT_URL
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


_STT_FAILED_MESSAGES = {
    "en": "Could not transcribe the recording. Please try again or type the symptoms instead.",
    "hi": "रिकॉर्डिंग को टेक्स्ट में नहीं बदला जा सका। कृपया फिर से प्रयास करें या लक्षण टाइप करें।",
    "mr": "रेकॉर्डिंगचे मजकुरात रूपांतर करता आले नाही. कृपया पुन्हा प्रयत्न करा किंवा लक्षणे टाइप करा.",
}


@app.post("/api/transcribe-audio", response_model=TranscriptionResponse)
def transcribe_audio_endpoint(audio: UploadFile = File(...), language: str = Form("en")):
    """
    Transcribe patient's voice recording to text (offline, faster-whisper).
    Sync handler: FastAPI runs it in a worker thread so CPU-bound decoding
    does not block other requests.
    """
    if not ENABLE_LOCAL_STT:
        raise HTTPException(status_code=503, detail="Speech-to-text is disabled on this server.")

    language = _normalize_language(language)
    max_bytes = MAX_AUDIO_UPLOAD_MB * 1024 * 1024
    temp_audio_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".audio") as temp_file:
            temp_audio_path = temp_file.name
            written = 0
            while chunk := audio.file.read(1024 * 1024):
                written += len(chunk)
                if written > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Audio recording exceeds {MAX_AUDIO_UPLOAD_MB} MB.",
                    )
                temp_file.write(chunk)
        if written == 0:
            raise HTTPException(status_code=400, detail="Empty audio upload.")

        transcription = transcribe_audio(temp_audio_path, language_code=language)
        if str(transcription).startswith("ERROR:"):
            # Details (decoder errors, file headers) go to the server log only.
            logger.error("Transcription failed: %s", transcription)
            raise HTTPException(status_code=503, detail=_localized_message(_STT_FAILED_MESSAGES, language))
        return {"text": transcription, "language": language}
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

@app.post("/api/get-doctor-response", response_model=ConsultationResponse)
def get_consultation(request: ConsultationRequest, background_tasks: BackgroundTasks):
    """
    Get doctor's AI response based on patient input.
    Sync handler: the Ollama call and TTS block, so FastAPI runs this in a
    worker thread instead of stalling the event loop for every other request.
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

                # SAFETY FLOOR: critical vital signs always mean HIGH urgency,
                # whatever the model or the keyword classifier concluded.
                vital_findings = _critical_vital_findings(
                    heart_rate=request.heart_rate,
                    bp_systolic=request.bp_systolic,
                    bp_diastolic=request.bp_diastolic,
                    spo2=request.spo2,
                    temperature=request.temperature,
                )
                vitals_flag = None
                if vital_findings:
                    vitals_flag = {
                        "apply_guardrail": True,
                        "matched_categories": ["critical_vitals"],
                        "confidence": 0.95,
                    }
                    emergency_action_block = _build_emergency_action_block(vitals_flag, request.language)
                    emergency_action_block["type"] = "critical_vitals"
                    if triage_data["urgency"] != "high":
                        logger.warning("Safety floor: critical vital signs, upgrading to HIGH urgency.")
                        triage_data["urgency"] = "high"
                        triage_data["reasons"] = vital_findings + triage_data["reasons"]
                        triage_data["actions"] = (
                            _build_guardrail_triage(vitals_flag, request.language)["actions"]
                            + triage_data["actions"]
                        )

                # Keep old keys for backward compatibility
                specialist_recommendation = triage_data.get("specialist", "general")
                urgency_level = triage_data.get("urgency", "low")

                # Build doctor response text from selected source when available
                doctor_text = ""
                if triage_source == "local_gemma" and isinstance(local_triage_raw, dict):
                    doctor_text = str(local_triage_raw.get("doctor_response", "")).strip()
                elif triage_source == "unassessed":
                    doctor_text = _localized_message(_UNASSESSED_MESSAGES, request.language)
                elif emergency_triage_raw:
                    doctor_text = str(emergency_triage_raw.get("doctor_response", "")).strip()

                # Final local fallback: compose from triage data if no text yet
                if not doctor_text:
                    logger.info("Composing response from local triage data.")
                    doctor_text = _compose_doctor_response_from_triage(triage_data)

                if vitals_flag:
                    alert = _compose_guardrail_response_text(vitals_flag, triage_data, request.language)
                    doctor_text = f"{alert}\n\n{doctor_text}"

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
        except Exception:
            logger.exception("Fairness tracking skipped")

        consensus_explanation = _build_consensus_explanation(
            patient_text=request.patient_text,
            typed_text=request.typed_text,
            transcription_text=request.transcription_text,
            image_data=request.image_data,
            pdf_data=request.pdf_data,
            final_urgency=triage_data.get("urgency", "low"),
        )
        
        audio_url = _generate_response_audio(doctor_text, request.language)

        # Clean up old audio files in the background
        background_tasks.add_task(cleanup_old_audio_files)

        # Return the response with the audio URL and specialist recommendation
        response_data = {
            "doctor_response": doctor_text,
            "audio_url": audio_url,
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

    except Exception:
        logger.exception("Unhandled error in consultation endpoint")
        # A failed assessment must look like a failure, never like a "low"
        # urgency result, and must not leak internals to the client.
        raise HTTPException(
            status_code=503,
            detail=_localized_message(_ASSESSMENT_FAILED_MESSAGES, request.language),
        )

@app.get("/api/audio/{filename}")
def get_audio(filename: str):
    """Serve a generated response recording."""
    audio_path = _audio_path_for(filename)
    if not os.path.isfile(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    media_type = "audio/wav" if filename.endswith(".wav") else "audio/mpeg"
    return FileResponse(
        audio_path,
        media_type=media_type,
        headers={
            # Contains health information: never cache in shared caches.
            "Cache-Control": "no-store",
            "Content-Disposition": "inline",
        },
    )

@app.get("/api/voices")
async def get_voices():
    """
    Get available TTS voices
    """
    return get_available_voices()

def _format_directory_entry(entry: Dict[str, Any], specialty: str) -> Dict[str, Any]:
    """Shape a static-directory entry for the UI.

    Only facility-level data from the directory is passed through; fields the
    directory cannot back up (ratings, fees, credentials, slots) are left for
    the user to confirm with the facility.
    """
    distance_km = entry.get("user_distance_km", entry.get("distance_km"))
    phone = entry.get("phone") or "Contact facility directly"
    return {
        "name": entry.get("name", "Medical Facility"),
        "specialty": entry.get("specialty", specialty),
        "hospital": entry.get("hospital", entry.get("clinic_name", "Medical Center")),
        "clinic_name": entry.get("hospital", entry.get("clinic_name", "Medical Center")),
        "address": entry.get("address", "Address not available"),
        "location": entry.get("address", "Location not available"),
        "latitude": entry.get("latitude"),
        "longitude": entry.get("longitude"),
        "distance": round(distance_km, 1) if distance_km is not None else None,
        "distance_km": round(distance_km, 1) if distance_km is not None else None,
        "distance_text": entry.get("user_distance", entry.get("distance", "Distance unavailable")),
        "phone": phone,
        "contact": phone,
        "hours": entry.get("hours", "Contact facility for current hours"),
        "available_today": entry.get("available_today", False),
        "availability_status": entry.get("availability_status", "Contact for availability"),
        "next_available": "Contact for appointment",
        "rating": None,
        "review_count": None,
        "consultation_fee": "Contact for current fees",
        "qualification": "Contact facility for qualifications",
        "experience": "Contact facility for experience",
        "registration_number": "Contact facility for registration details",
        "source": entry.get("source", "static_directory"),
        "data_type": entry.get("data_type", "directory_listing"),
        "verified": bool(entry.get("verified", False)),
        "verification_note": entry.get(
            "verification_note", "Please verify current information with the facility."
        ),
        "safety_warning": "⚠️ Always call ahead to confirm doctor availability, fees, and appointment requirements",
        "last_updated": entry.get("last_updated", "Not verified"),
    }


@app.post("/api/search-doctors", response_model=DoctorSearchResponse)
async def search_doctors_endpoint(request: DoctorSearchRequest):
    """Find listed specialists near a location (offline static directory)."""
    search_params = {
        "latitude": request.latitude,
        "longitude": request.longitude,
        "specialty": request.specialty,
        "radius": request.radius,
        "sort_by": request.sort_by,
        "limit": request.limit,
        "language": request.language,
        "data_source": "static_directory",
        "verified": False,
    }
    try:
        entries = await advanced_search_doctors(
            specialty=request.specialty,
            latitude=request.latitude,
            longitude=request.longitude,
            radius=request.radius,
            sort_by=request.sort_by,
            limit=request.limit,
        )
    except Exception:
        logger.exception("Doctor search failed")
        return DoctorSearchResponse(doctors=[], total_found=0, search_params={**search_params, "error": "search_failed"})

    doctors = [_format_directory_entry(entry, request.specialty) for entry in entries]
    return DoctorSearchResponse(doctors=doctors, total_found=len(doctors), search_params=search_params)


@app.post("/api/search-doctors-by-city", response_model=CitySearchResponse)
async def search_doctors_by_city_endpoint(request: CitySearchRequest):
    """Find listed specialists in a named Indian city (offline static directory)."""
    search_params = {
        "city": request.city,
        "specialty": request.specialty,
        "sort_by": request.sort_by,
        "limit": request.limit,
        "language": request.language,
        "data_source": "static_directory",
        "verified": False,
    }
    try:
        entries = await advanced_search_city(
            city=request.city,
            specialty=request.specialty,
            sort_by=request.sort_by,
            limit=request.limit,
            user_latitude=request.user_latitude,
            user_longitude=request.user_longitude,
        )
    except Exception:
        logger.exception("City doctor search failed")
        return CitySearchResponse(
            doctors=[], total_found=0, city_coordinates=None,
            search_params={**search_params, "error": "search_failed"},
        )

    city_coordinates = next((e["city_coordinates"] for e in entries if e.get("city_coordinates")), None)
    doctors = [
        {**_format_directory_entry(entry, request.specialty), "city": request.city, "city_search": True}
        for entry in entries
    ]
    return CitySearchResponse(
        doctors=doctors,
        total_found=len(doctors),
        city_coordinates=city_coordinates,
        search_params=search_params,
    )


@app.get("/api/audio-status/{filename}")
def check_audio_status(filename: str):
    """Report whether a generated recording is available.

    Audio is generated before the consultation response is returned, so a
    file that exists is complete.
    """
    audio_path = _audio_path_for(filename)
    if not os.path.isfile(audio_path):
        return {"ready": False, "status": "generating", "file_size": 0}
    file_size = os.path.getsize(audio_path)
    if file_size == 0:
        return {"ready": False, "status": "generating", "file_size": 0}
    return {"ready": True, "status": "ready", "file_size": file_size}


# Utility Functions
def cleanup_old_audio_files():
    """Delete generated recordings older than AUDIO_RETENTION_SECONDS."""
    if not os.path.isdir(AUDIO_OUTPUT_DIR):
        return
    cutoff = time.time() - AUDIO_RETENTION_SECONDS
    for filename in os.listdir(AUDIO_OUTPUT_DIR):
        file_path = os.path.join(AUDIO_OUTPUT_DIR, filename)
        try:
            if os.path.isfile(file_path) and os.path.getmtime(file_path) < cutoff:
                os.remove(file_path)
        except OSError:
            # Another request may have removed it concurrently.
            pass


# =============================================================================
# 🚨 EMERGENCY TRIAGE ENDPOINTS
# =============================================================================

# Initialize emergency services
emergency_classifier = EmergencyClassifier()
hospital_router = HospitalRoutingService()


class QuickTriageRequest(BaseModel):
    """Quick triage check for real-time symptom analysis"""
    symptoms: str = Field(..., max_length=MAX_TEXT_CHARS, description="Symptom description")


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
        
        # Step 1: Classify emergency level and calculate scores
        triage_result = emergency_classifier.classify(request)
        
        logger.info(
            "Emergency triage: level=%s type=%s call_108=%s",
            triage_result.triage_level, triage_result.emergency_type, triage_result.call_108,
        )
        
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
                
                
            except Exception:
                logger.exception("Hospital routing failed")
                # Continue without hospital data
        
        return triage_result
        
    except Exception:
        logger.exception("Emergency triage failed")
        
        # Return a safe fallback - always recommend calling 108 on error
        raise HTTPException(
            status_code=500,
            detail="Emergency triage system error. Please CALL 108 for emergencies."
        )


def _quick_triage(symptoms: str) -> Dict[str, Any]:
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
        return QuickTriageResponse(**emergency_classifier.quick_classify(symptoms)).model_dump()
    except Exception:
        logger.exception("Quick triage failed")
        return {
            "triage_level": 4,
            "triage_level_name": "standard",
            "triage_color": "#22C55E",
            "call_108": False,
            "action": "Quick check unavailable. If symptoms are severe, call 108.",
            "icon": "ℹ️",
            "matched_keywords": []
        }


@app.post("/api/emergency-triage/quick", response_model=QuickTriageResponse)
async def quick_emergency_triage(request: QuickTriageRequest):
    """
    🚨 QUICK TRIAGE CHECK — fast keyword-based triage for real-time feedback
    as the user types. Returns a basic triage level without full scoring.
    """
    return _quick_triage(request.symptoms)


@app.get("/api/emergency-triage/quick", response_model=QuickTriageResponse, deprecated=True)
async def quick_emergency_triage_get(symptoms: str):
    """Deprecated: puts symptoms in the URL (and so in access logs). Use POST."""
    return _quick_triage(symptoms)


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
        
    except Exception:
        logger.exception("Hospital search failed")
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


# Serve the built React app (frontend/dist) from the API when it exists, so a
# deployment is a single offline process. Mounted last: API routes win.
if _FRONTEND_BUILT:
    app.mount("/", StaticFiles(directory=FRONTEND_DIST_DIR, html=True), name="frontend")


# Run the server if executed directly
if __name__ == "__main__":
    uvicorn.run("api:app", host=API_HOST, port=API_PORT, reload=False)
