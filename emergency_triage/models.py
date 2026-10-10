"""
Emergency Triage Models
======================
Pydantic models for emergency triage requests, responses, and scoring.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TriageLevel(str, Enum):
    """ESI-like 5-level triage classification"""

    CRITICAL = "critical"  # Level 1 - Immediate life threat
    EMERGENCY = "emergency"  # Level 2 - High risk, needs immediate attention
    URGENT = "urgent"  # Level 3 - Needs prompt care (1-2 hours)
    STANDARD = "standard"  # Level 4 - Can wait (24 hours)
    SELF_CARE = "self_care"  # Level 5 - Home care appropriate


class VitalSigns(BaseModel):
    """Patient vital signs for enhanced scoring"""

    blood_pressure_systolic: int | None = Field(None, ge=50, le=250, description="Systolic BP in mmHg")
    blood_pressure_diastolic: int | None = Field(None, ge=30, le=150, description="Diastolic BP in mmHg")
    heart_rate: int | None = Field(None, ge=30, le=250, description="Heart rate in BPM")
    temperature_celsius: float | None = Field(None, ge=34, le=43, description="Body temperature in °C")
    oxygen_saturation: int | None = Field(None, ge=50, le=100, description="SpO2 percentage")
    respiratory_rate: int | None = Field(None, ge=5, le=60, description="Breaths per minute")


class EmergencyTriageRequest(BaseModel):
    """Request model for emergency triage assessment"""

    symptoms: str = Field(..., min_length=3, description="Patient's symptoms description")
    age: int | None = Field(None, ge=0, le=120, description="Patient age in years")
    gender: str | None = Field(None, description="Patient gender: male/female/other")
    vital_signs: VitalSigns | None = None
    medical_history: list[str] | None = Field(default=[], description="List of pre-existing conditions")
    symptom_duration: str | None = Field(None, description="How long symptoms have been present")
    language: str = Field(default="en", description="Response language: en/hi/mr")

    # Location for hospital routing
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)

    # Optional AI analysis for enhanced classification
    ai_analysis: str | None = Field(None, description="AI doctor's analysis if already performed")


class HeartScore(BaseModel):
    """Modified HEART Score for pre-hospital cardiac assessment"""

    score: int = Field(..., ge=0, le=10, description="Total HEART score (0-10)")
    max_score: int = Field(default=10)
    risk_level: str = Field(..., description="LOW/MODERATE/HIGH")

    # Component scores
    history_score: int = Field(..., ge=0, le=2, description="Symptom history score")
    age_score: int = Field(..., ge=0, le=2, description="Age-based risk score")
    risk_factors_score: int = Field(..., ge=0, le=2, description="Risk factors score")
    severity_score: int = Field(..., ge=0, le=2, description="Symptom severity score")

    # Additional info
    symptoms_detected: list[str] = Field(default=[])
    recommendation: str
    confidence: float = Field(default=0.8, ge=0, le=1)


class BeFastScore(BaseModel):
    """BE-FAST Score for stroke assessment"""

    score: int = Field(..., ge=0, le=6, description="Total BE-FAST score (0-6)")
    max_score: int = Field(default=6)
    risk_level: str = Field(..., description="LOW/MODERATE/HIGH/CRITICAL")
    is_stroke_likely: bool = Field(default=False)

    # Component detection
    balance_issues: bool = Field(default=False)
    eye_symptoms: bool = Field(default=False)
    face_drooping: bool = Field(default=False)
    arm_weakness: bool = Field(default=False)
    speech_difficulty: bool = Field(default=False)
    time_critical: bool = Field(default=False)

    symptoms_detected: list[str] = Field(default=[])
    recommendation: str
    golden_hour_warning: str | None = None
    confidence: float = Field(default=0.8, ge=0, le=1)


class TraumaScore(BaseModel):
    """Trauma severity assessment"""

    score: int = Field(..., ge=0, le=10, description="Trauma severity (0-10)")
    max_score: int = Field(default=10)
    risk_level: str = Field(..., description="LOW/MODERATE/HIGH/CRITICAL")

    # Assessment components
    mechanism_severe: bool = Field(default=False, description="High-energy mechanism")
    bleeding_severe: bool = Field(default=False)
    consciousness_altered: bool = Field(default=False)
    multiple_injuries: bool = Field(default=False)

    symptoms_detected: list[str] = Field(default=[])
    recommendation: str
    confidence: float = Field(default=0.7, ge=0, le=1)


class EmergencyScores(BaseModel):
    """Combined emergency scores"""

    overall_score: int = Field(..., ge=0, le=10, description="Overall risk score")
    overall_risk_level: str = Field(..., description="Combined risk assessment")

    # Individual condition scores
    heart_score: HeartScore | None = None
    befast_score: BeFastScore | None = None
    trauma_score: TraumaScore | None = None

    # Vital signs assessment
    vitals_concern_level: str | None = None

    # Detection flags
    is_cardiac_concern: bool = Field(default=False)
    is_stroke_concern: bool = Field(default=False)
    is_trauma_concern: bool = Field(default=False)
    is_respiratory_concern: bool = Field(default=False)


class EmergencyHospital(BaseModel):
    """Hospital with emergency capabilities"""

    id: str
    name: str
    address: str
    latitude: float
    longitude: float

    # Contact
    phone: str | None = None
    emergency_phone: str | None = None

    # Distance
    distance_km: float
    distance_text: str
    estimated_travel_time: str | None = None

    # Capabilities
    has_emergency_room: bool = Field(default=True)
    has_icu: bool = Field(default=False)
    has_cardiac_care: bool = Field(default=False)
    has_stroke_unit: bool = Field(default=False)
    has_trauma_center: bool = Field(default=False)
    is_24x7: bool = Field(default=True)

    # Metadata
    operator: str | None = None
    operator_type: str | None = None  # "government", "private"
    source: str = Field(default="OpenStreetMap")
    verified: bool = Field(default=False)

    # Matching score for routing
    match_score: int = Field(default=0, description="How well hospital matches needs")
    match_reason: str | None = None


class EmergencyAction(BaseModel):
    """Recommended action for the user"""

    action_type: str  # "call_108", "go_to_er", "seek_care", "self_care", "schedule"
    action_text: str
    action_text_hindi: str | None = None
    action_text_marathi: str | None = None
    urgency: str
    icon: str
    call_number: str | None = None
    hospital: EmergencyHospital | None = None


class HospitalSearchRequest(BaseModel):
    """Request for hospital search"""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_km: int = Field(default=10, ge=1, le=50)
    required_capabilities: list[str] = Field(default=["emergency_room"])
    triage_level: int | None = Field(None, ge=1, le=5)
    emergency_type: str | None = None
    language: str = Field(default="en")


class TriageResponse(BaseModel):
    """Complete triage assessment response"""

    # Core classification
    triage_level: int = Field(..., ge=1, le=5, description="1=Critical, 5=Self-care")
    triage_level_name: TriageLevel
    triage_color: str

    # Scoring
    scores: EmergencyScores

    # Emergency type detection
    emergency_type: str | None = None  # "cardiac", "stroke", "trauma", "respiratory", "other"
    detected_conditions: list[str] = Field(default=[])

    # Critical recommendations
    call_108: bool = Field(default=False)
    time_sensitivity: str  # "immediate", "within_1_hour", "within_24_hours", "scheduled"

    # Actions
    primary_action: EmergencyAction
    secondary_actions: list[EmergencyAction] = Field(default=[])

    # Hospital routing
    hospitals: list[EmergencyHospital] = Field(default=[])
    nearest_capable_hospital: EmergencyHospital | None = None

    # Medical recommendation
    specialist_recommendation: str | None = None
    preliminary_assessment: str

    # Disclaimers (ALWAYS PRESENT)
    disclaimer: str = Field(
        default="This AI assessment is for guidance only and does NOT replace professional medical judgment. In any emergency, CALL 108 IMMEDIATELY."
    )

    # Metadata
    assessed_at: datetime = Field(default_factory=datetime.now)
    confidence: float = Field(default=0.7, ge=0, le=1)
