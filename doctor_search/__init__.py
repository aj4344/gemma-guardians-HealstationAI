"""
HealStation AI — Doctor Search Package
Part of the HealStation AI Emergency Triage System.
Provides location-based hospital and specialist search (offline-first, static database only).
"""
import sys
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from advanced_doctor_service import (
    search_doctors_enhanced,
    search_doctors_by_city,
)
from enhanced_doctor_service import EnhancedDoctorSearchService

__all__ = [
    "search_doctors_enhanced",
    "search_doctors_by_city",
    "EnhancedDoctorSearchService",
]
