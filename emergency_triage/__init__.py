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

from .models import (
    VitalSigns,
    EmergencyTriageRequest,
    HeartScore,
    BeFastScore,
    TraumaScore,
    EmergencyScores,
    TriageLevel,
    EmergencyHospital,
    TriageResponse,
    HospitalSearchRequest,
    EmergencyAction
)

from .constants import (
    TRIAGE_LEVELS,
    CRITICAL_KEYWORDS,
    EMERGENCY_KEYWORDS,
    URGENT_KEYWORDS,
    HEART_SCORE_CONFIG,
    BEFAST_KEYWORDS,
    TRAUMA_KEYWORDS,
    EMERGENCY_NUMBERS,
    TOXIN_FAST_LANE_KEYWORDS
)

from .triage_service import TriageService
from .emergency_classifier import EmergencyClassifier
from .hospital_routing_service import HospitalRoutingService

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
    'HospitalRoutingService'
]
