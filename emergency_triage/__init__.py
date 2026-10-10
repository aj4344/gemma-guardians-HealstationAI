"""
Emergency Triage Module
======================
Production-grade emergency risk scoring and hospital routing for HealStation AI.

This module provides:
- HEART Score for chest pain/cardiac assessment
- BE-FAST Score for stroke assessment
- Trauma severity scoring
- 5-level ESI-like triage classification
- Emergency hospital routing via Overpass API
"""

from .constants import (
    BEFAST_KEYWORDS,
    CRITICAL_KEYWORDS,
    EMERGENCY_KEYWORDS,
    EMERGENCY_NUMBERS,
    HEART_SCORE_CONFIG,
    TOXIN_FAST_LANE_KEYWORDS,
    TRAUMA_KEYWORDS,
    TRIAGE_LEVELS,
    URGENT_KEYWORDS,
)
from .emergency_classifier import EmergencyClassifier
from .hospital_routing_service import HospitalRoutingService
from .models import (
    BeFastScore,
    EmergencyAction,
    EmergencyHospital,
    EmergencyScores,
    EmergencyTriageRequest,
    HeartScore,
    HospitalSearchRequest,
    TraumaScore,
    TriageLevel,
    TriageResponse,
    VitalSigns,
)
from .triage_service import TriageService

__all__ = [
    # Models
    'VitalSigns',
    'EmergencyTriageRequest',
    'HeartScore',
    'BeFastScore',
    'TraumaScore',
    'EmergencyScores',
    'TriageLevel',
    'EmergencyHospital',
    'TriageResponse',
    'HospitalSearchRequest',
    'EmergencyAction',
    'HEART_SCORE_CONFIG',
    'BEFAST_KEYWORDS',
    'TRAUMA_KEYWORDS',
    # Constants
    'TRIAGE_LEVELS',
    'CRITICAL_KEYWORDS',
    'EMERGENCY_KEYWORDS',
    'URGENT_KEYWORDS',
    'EMERGENCY_NUMBERS',
    'TOXIN_FAST_LANE_KEYWORDS',
    # Services
    'TriageService',
    'EmergencyClassifier',
    'HospitalRoutingService',
]
