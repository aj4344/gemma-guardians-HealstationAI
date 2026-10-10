"""Version 1 HTTP API (deprecated; kept until the frontend has moved to /api/v2)."""

import logging
import os
import tempfile
from typing import Any

import requests
from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from config import ENABLE_LOCAL_STT, FAIRNESS_PARITY_THRESHOLD, LOCAL_GEMMA_MODEL, MAX_AUDIO_UPLOAD_MB
from emergency_triage import (
    EMERGENCY_NUMBERS,
    TRIAGE_LEVELS,
    EmergencyTriageRequest,
    HospitalRoutingService,
    HospitalSearchRequest,
    TriageResponse,
)
from emergency_triage.fairness_engine import FairnessTracker
from healstation.directory.doctors import search_doctors_by_city as advanced_search_city
from healstation.directory.doctors import search_doctors_enhanced as advanced_search_doctors
from healstation.speech import response_audio
from healstation.speech.stt import (
    LOCAL_STT_COMPUTE_TYPE,
    LOCAL_STT_DEVICE,
    LOCAL_STT_MODEL_SIZE,
    _get_local_stt_model,
    transcribe_audio,
)
from healstation.speech.tts import get_available_voices
from healstation.triage import fallback, pipeline
from healstation.triage.consensus import build_consensus_explanation
from healstation.triage.localization import (
    ASSESSMENT_FAILED_MESSAGES,
    STT_FAILED_MESSAGES,
    localized_message,
    normalize_language,
)
from healstation.triage.model_client import LOCAL_GEMMA_CHAT_URL

logger = logging.getLogger("healstation")
router = APIRouter()


# Models for request/response
MAX_TEXT_CHARS = 20_000


MAX_ATTACHMENTS = 8


class ConsultationRequest(BaseModel):
    patient_text: str = Field(..., min_length=1, max_length=MAX_TEXT_CHARS)
    typed_text: str | None = Field(None, max_length=MAX_TEXT_CHARS)
    transcription_text: str | None = Field(None, max_length=MAX_TEXT_CHARS)
    language: str = Field("en", max_length=16)
    age: int | None = Field(None, ge=0, le=130)
    gender: str | None = Field(None, max_length=32)
    triage_correct: bool | None = None
    image_data: list[str] | None = Field(None, max_length=MAX_ATTACHMENTS)
    pdf_data: list[dict] | None = Field(None, max_length=MAX_ATTACHMENTS)
    image_count: int | None = 0
    pdf_count: int | None = 0
    # Structured vital signs (optional — UI can send individual fields).
    # Bounds only reject impossible values; critical readings stay accepted.
    heart_rate: int | None = Field(None, ge=0, le=400)
    bp_systolic: int | None = Field(None, ge=0, le=400)
    bp_diastolic: int | None = Field(None, ge=0, le=300)
    spo2: int | None = Field(None, ge=0, le=100)
    temperature: float | None = Field(None, ge=20, le=46)


class ConsultationResponse(BaseModel):
    doctor_response: str
    audio_url: str | None = None
    specialist_recommendation: str | None = None
    urgency_level: str | None = None
    # Canonical triage schema (Step 1)
    urgency: str = "low"
    reasons: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    specialist: str = "general"
    confidence: float = 0.5
    triage: dict[str, Any] = Field(default_factory=dict)
    triage_source: str | None = None
    emergency_action_block: dict[str, Any] | None = None
    consensus_explanation: dict[str, Any] | None = None
    fairness_metrics: dict[str, Any] | None = None


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
    doctors: list[dict[str, Any]]
    total_found: int
    search_params: dict[str, Any]


class CitySearchRequest(BaseModel):
    city: str
    specialty: str
    sort_by: str = "distance"
    limit: int = 20
    language: str = "en"
    user_latitude: float | None = None  # Optional user location for distance calculation
    user_longitude: float | None = None


class CitySearchResponse(BaseModel):
    doctors: list[dict[str, Any]]
    total_found: int
    city_coordinates: dict[str, float] | None
    search_params: dict[str, Any]


fairness_tracker = FairnessTracker(parity_threshold=FAIRNESS_PARITY_THRESHOLD)


@router.get("/api")
def api_health_check():
    """API health check endpoint for frontend to verify connection"""
    return {"status": "healthy", "message": "HealStation AI: Doctor Assistant API is running"}


@router.get("/api/stt-health")
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


@router.get("/api/ollama-status")
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


@router.get("/api/ollama-health")
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


@router.post("/api/transcribe-audio", response_model=TranscriptionResponse)
def transcribe_audio_endpoint(audio: UploadFile = File(...), language: str = Form("en")):
    """
    Transcribe patient's voice recording to text (offline, faster-whisper).
    Sync handler: FastAPI runs it in a worker thread so CPU-bound decoding
    does not block other requests.
    """
    if not ENABLE_LOCAL_STT:
        raise HTTPException(status_code=503, detail="Speech-to-text is disabled on this server.")

    language = normalize_language(language)
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
            raise HTTPException(status_code=503, detail=localized_message(STT_FAILED_MESSAGES, language))
        return {"text": transcription, "language": language}
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)


@router.post("/api/get-doctor-response", response_model=ConsultationResponse)
def get_consultation(request: ConsultationRequest, background_tasks: BackgroundTasks):
    """
    Get doctor's AI response based on patient input.
    Sync handler: the Ollama call and TTS block, so FastAPI runs this in a
    worker thread instead of stalling the event loop for every other request.
    """
    try:
        logger.info(
            "Consultation request | lang=%s text_len=%d images=%d",
            request.language,
            len(request.patient_text) if request.patient_text else 0,
            len(request.image_data) if request.image_data else 0,
        )

        outcome = pipeline.assess_symptoms(
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
        triage_data = outcome.triage_data
        doctor_text = outcome.doctor_text

        logger.info(
            "Response ready | urgency=%s specialist=%s source=%s len=%d",
            outcome.urgency_level,
            outcome.specialist_recommendation,
            outcome.triage_source,
            len(doctor_text),
        )

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

        consensus_explanation = build_consensus_explanation(
            patient_text=request.patient_text,
            typed_text=request.typed_text,
            transcription_text=request.transcription_text,
            image_data=request.image_data,
            pdf_data=request.pdf_data,
            final_urgency=triage_data.get("urgency", "low"),
        )

        audio_url = response_audio.generate_response_audio(doctor_text, request.language)

        # Clean up old audio files in the background
        background_tasks.add_task(response_audio.cleanup_old_audio_files)

        # Return the response with the audio URL and specialist recommendation
        response_data = {
            "doctor_response": doctor_text,
            "audio_url": audio_url,
            "specialist_recommendation": outcome.specialist_recommendation,
            "urgency_level": outcome.urgency_level,
            "urgency": triage_data["urgency"],
            "reasons": triage_data["reasons"],
            "actions": triage_data["actions"],
            "specialist": triage_data["specialist"],
            "confidence": triage_data["confidence"],
            "triage": triage_data,
            "triage_source": outcome.triage_source,
            "emergency_action_block": outcome.emergency_action_block,
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
            detail=localized_message(ASSESSMENT_FAILED_MESSAGES, request.language),
        ) from None


@router.get("/api/audio/{filename}")
def get_audio(filename: str):
    """Serve a generated response recording."""
    audio_path = response_audio.audio_path_for(filename)
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


@router.get("/api/voices")
async def get_voices():
    """
    Get available TTS voices
    """
    return get_available_voices()


def format_directory_entry(entry: dict[str, Any], specialty: str) -> dict[str, Any]:
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
        "verification_note": entry.get("verification_note", "Please verify current information with the facility."),
        "safety_warning": "⚠️ Always call ahead to confirm doctor availability, fees, and appointment requirements",
        "last_updated": entry.get("last_updated", "Not verified"),
    }


@router.post("/api/search-doctors", response_model=DoctorSearchResponse)
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
        return DoctorSearchResponse(
            doctors=[], total_found=0, search_params={**search_params, "error": "search_failed"}
        )

    doctors = [format_directory_entry(entry, request.specialty) for entry in entries]
    return DoctorSearchResponse(doctors=doctors, total_found=len(doctors), search_params=search_params)


@router.post("/api/search-doctors-by-city", response_model=CitySearchResponse)
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
            doctors=[],
            total_found=0,
            city_coordinates=None,
            search_params={**search_params, "error": "search_failed"},
        )

    city_coordinates = next((e["city_coordinates"] for e in entries if e.get("city_coordinates")), None)
    doctors = [
        {**format_directory_entry(entry, request.specialty), "city": request.city, "city_search": True}
        for entry in entries
    ]
    return CitySearchResponse(
        doctors=doctors,
        total_found=len(doctors),
        city_coordinates=city_coordinates,
        search_params=search_params,
    )


@router.get("/api/audio-status/{filename}")
def check_audio_status(filename: str):
    """Report whether a generated recording is available.

    Audio is generated before the consultation response is returned, so a
    file that exists is complete.
    """
    audio_path = response_audio.audio_path_for(filename)
    if not os.path.isfile(audio_path):
        return {"ready": False, "status": "generating", "file_size": 0}
    file_size = os.path.getsize(audio_path)
    if file_size == 0:
        return {"ready": False, "status": "generating", "file_size": 0}
    return {"ready": True, "status": "ready", "file_size": file_size}


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
    matched_keywords: list[str] = []


@router.post("/api/emergency-triage", response_model=TriageResponse)
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
        triage_result = fallback.emergency_classifier.classify(request)

        logger.info(
            "Emergency triage: level=%s type=%s call_108=%s",
            triage_result.triage_level,
            triage_result.emergency_type,
            triage_result.call_108,
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
                    emergency_type=triage_result.emergency_type,
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
            status_code=500, detail="Emergency triage system error. Please CALL 108 for emergencies."
        ) from None


def quick_triage(symptoms: str) -> dict[str, Any]:
    try:
        if not symptoms or len(symptoms) < 3:
            return {
                "triage_level": 5,
                "triage_level_name": "self_care",
                "triage_color": "#3B82F6",
                "call_108": False,
                "action": "Continue describing your symptoms",
                "icon": "ℹ️",
                "matched_keywords": [],
            }
        return QuickTriageResponse(**fallback.emergency_classifier.quick_classify(symptoms)).model_dump()
    except Exception:
        logger.exception("Quick triage failed")
        return {
            "triage_level": 4,
            "triage_level_name": "standard",
            "triage_color": "#22C55E",
            "call_108": False,
            "action": "Quick check unavailable. If symptoms are severe, call 108.",
            "icon": "ℹ️",
            "matched_keywords": [],
        }


@router.post("/api/emergency-triage/quick", response_model=QuickTriageResponse)
async def quick_emergency_triage(request: QuickTriageRequest):
    """
    🚨 QUICK TRIAGE CHECK — fast keyword-based triage for real-time feedback
    as the user types. Returns a basic triage level without full scoring.
    """
    return quick_triage(request.symptoms)


@router.get("/api/emergency-triage/quick", response_model=QuickTriageResponse, deprecated=True)
async def quick_emergency_triage_get(symptoms: str):
    """Deprecated: puts symptoms in the URL (and so in access logs). Use POST."""
    return quick_triage(symptoms)


@router.post("/api/emergency-hospitals")
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
                "required_capabilities": request.required_capabilities,
            },
            "nearest_with_er": hospitals[0].model_dump() if hospitals else None,
        }

    except Exception:
        logger.exception("Hospital search failed")
        raise HTTPException(status_code=500, detail="Hospital search failed. For emergencies, CALL 108.") from None


@router.get("/api/emergency-info")
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
                "icon": config["icon"],
            }
            for level, config in TRIAGE_LEVELS.items()
        },
        "disclaimer": "⚠️ This AI assessment is for guidance only and does NOT replace professional medical judgment. In any emergency, CALL 108 IMMEDIATELY.",
    }


@router.get("/api/health-check")
async def health_check():
    """System health check including emergency services"""
    return {
        "status": "healthy",
        "services": {"api": "running", "emergency_triage": "available", "hospital_routing": "available"},
        "emergency_number": "108",
        "version": "2.0.0",
    }
