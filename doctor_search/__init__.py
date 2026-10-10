"""
HealStation AI — Doctor Search Package
Part of the HealStation AI Emergency Triage System.
Provides location-based hospital and specialist search (offline-first, static database only).
"""

from advanced_doctor_service import (
    search_doctors_by_city,
    search_doctors_enhanced,
)

__all__ = [
    "search_doctors_enhanced",
    "search_doctors_by_city",
]
