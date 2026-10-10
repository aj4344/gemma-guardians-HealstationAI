"""
Hospital Routing Service
========================
Find emergency-equipped hospitals from the built-in static database.
No network required — works fully offline.
"""

import math

from .models import EmergencyHospital, HospitalSearchRequest


class HospitalRoutingService:
    """
    Offline hospital routing service for emergency triage.
    Uses built-in static emergency hospital database.
    """

    # Static emergency hospitals (major cities)
    STATIC_EMERGENCY_HOSPITALS = {
        "mumbai": [
            {
                "id": "static_1",
                "name": "King Edward Memorial Hospital (KEM)",
                "address": "Acharya Donde Marg, Parel, Mumbai",
                "latitude": 19.0028,
                "longitude": 72.8426,
                "phone": "022-24136051",
                "has_emergency_room": True,
                "has_icu": True,
                "has_trauma_center": True,
                "is_24x7": True,
                "operator_type": "government",
            },
            {
                "id": "static_2",
                "name": "Lilavati Hospital",
                "address": "A-791, Bandra Reclamation, Bandra West, Mumbai",
                "latitude": 19.0509,
                "longitude": 72.8294,
                "phone": "022-26568000",
                "has_emergency_room": True,
                "has_icu": True,
                "has_cardiac_care": True,
                "is_24x7": True,
                "operator_type": "private",
            },
        ],
        "delhi": [
            {
                "id": "static_3",
                "name": "AIIMS New Delhi",
                "address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi",
                "latitude": 28.5672,
                "longitude": 77.2100,
                "phone": "011-26588500",
                "has_emergency_room": True,
                "has_icu": True,
                "has_trauma_center": True,
                "has_cardiac_care": True,
                "has_stroke_unit": True,
                "is_24x7": True,
                "operator_type": "government",
            },
            {
                "id": "static_4",
                "name": "Safdarjung Hospital",
                "address": "Ansari Nagar West, New Delhi",
                "latitude": 28.5679,
                "longitude": 77.2090,
                "phone": "011-26707437",
                "has_emergency_room": True,
                "has_icu": True,
                "has_trauma_center": True,
                "is_24x7": True,
                "operator_type": "government",
            },
        ],
        "bangalore": [
            {
                "id": "static_5",
                "name": "Victoria Hospital",
                "address": "Fort, Bengaluru",
                "latitude": 12.9569,
                "longitude": 77.5771,
                "phone": "080-26701150",
                "has_emergency_room": True,
                "has_icu": True,
                "is_24x7": True,
                "operator_type": "government",
            }
        ],
        "chennai": [
            {
                "id": "static_6",
                "name": "Rajiv Gandhi Government General Hospital",
                "address": "Park Town, Chennai",
                "latitude": 13.0878,
                "longitude": 80.2785,
                "phone": "044-25305000",
                "has_emergency_room": True,
                "has_icu": True,
                "has_trauma_center": True,
                "is_24x7": True,
                "operator_type": "government",
            }
        ],
        "kolkata": [
            {
                "id": "static_7",
                "name": "SSKM Hospital",
                "address": "244, AJC Bose Road, Kolkata",
                "latitude": 22.5355,
                "longitude": 88.3442,
                "phone": "033-22041101",
                "has_emergency_room": True,
                "has_icu": True,
                "is_24x7": True,
                "operator_type": "government",
            }
        ],
        "hyderabad": [
            {
                "id": "static_8",
                "name": "Osmania General Hospital",
                "address": "Afzal Gunj, Hyderabad",
                "latitude": 17.3616,
                "longitude": 78.4747,
                "phone": "040-24600146",
                "has_emergency_room": True,
                "has_icu": True,
                "is_24x7": True,
                "operator_type": "government",
            }
        ],
        "pune": [
            {
                "id": "static_9",
                "name": "Sassoon General Hospital",
                "address": "Bund Garden Road, Pune",
                "latitude": 18.5286,
                "longitude": 73.8715,
                "phone": "020-26128000",
                "has_emergency_room": True,
                "has_icu": True,
                "is_24x7": True,
                "operator_type": "government",
            }
        ],
    }

    def __init__(self):
        pass

    async def find_emergency_hospitals(self, request: HospitalSearchRequest) -> list[EmergencyHospital]:
        """
        Find emergency hospitals near the given location.

        Args:
            request: HospitalSearchRequest with location and requirements

        Returns:
            List of EmergencyHospital sorted by match score and distance
        """
        # Use built-in static database (fully offline)
        hospitals = self._get_static_hospitals(request.latitude, request.longitude, request.radius_km)

        # Calculate match scores and sort
        hospitals = self._score_and_sort(hospitals, request.required_capabilities, request.latitude, request.longitude)

        return hospitals[:20]  # Return top 20

    def _get_static_hospitals(self, latitude: float, longitude: float, radius_km: int) -> list[EmergencyHospital]:
        """Get hospitals from static database (failsafe)"""
        hospitals = []

        # Determine nearest city
        cities = {
            "mumbai": (19.0760, 72.8777),
            "delhi": (28.6139, 77.2090),
            "bangalore": (12.9716, 77.5946),
            "chennai": (13.0827, 80.2707),
            "kolkata": (22.5726, 88.3639),
            "hyderabad": (17.3850, 78.4867),
            "pune": (18.5204, 73.8567),
        }

        # Find closest city
        nearest_city = None
        min_distance = float('inf')

        for city, (lat, lon) in cities.items():
            dist = self._haversine(latitude, longitude, lat, lon)
            if dist < min_distance:
                min_distance = dist
                nearest_city = city

        # If within 100km of a city, use its hospitals
        if nearest_city and min_distance < 100:
            static_list = self.STATIC_EMERGENCY_HOSPITALS.get(nearest_city, [])

            for h in static_list:
                distance = self._haversine(latitude, longitude, h["latitude"], h["longitude"])

                if distance <= radius_km:
                    hospital = EmergencyHospital(
                        id=h["id"],
                        name=h["name"],
                        address=h["address"],
                        latitude=h["latitude"],
                        longitude=h["longitude"],
                        phone=h.get("phone"),
                        distance_km=round(distance, 2),
                        distance_text=f"{round(distance, 1)} km",
                        estimated_travel_time=f"{int(distance * 2)} mins",
                        has_emergency_room=h.get("has_emergency_room", True),
                        has_icu=h.get("has_icu", False),
                        has_cardiac_care=h.get("has_cardiac_care", False),
                        has_stroke_unit=h.get("has_stroke_unit", False),
                        has_trauma_center=h.get("has_trauma_center", False),
                        is_24x7=h.get("is_24x7", True),
                        operator_type=h.get("operator_type", ""),
                        source="StaticDatabase",
                        verified=True,
                    )
                    hospitals.append(hospital)

        return hospitals

    def _score_and_sort(
        self, hospitals: list[EmergencyHospital], required_capabilities: list[str], user_lat: float, user_lon: float
    ) -> list[EmergencyHospital]:
        """Score hospitals by capability match and distance, then sort"""
        for hospital in hospitals:
            score = 0
            match_reasons = []

            # Score by capabilities
            if "emergency_room" in required_capabilities and hospital.has_emergency_room:
                score += 30
                match_reasons.append("Has ER")

            if "icu" in required_capabilities and hospital.has_icu:
                score += 20
                match_reasons.append("Has ICU")

            if "cardiac_care" in required_capabilities and hospital.has_cardiac_care:
                score += 25
                match_reasons.append("Cardiac care")

            if "stroke_unit" in required_capabilities and hospital.has_stroke_unit:
                score += 25
                match_reasons.append("Stroke unit")

            if "trauma_center" in required_capabilities and hospital.has_trauma_center:
                score += 25
                match_reasons.append("Trauma center")

            if "24x7" in required_capabilities and hospital.is_24x7:
                score += 15
                match_reasons.append("24/7")

            # Government hospitals (often free emergency care)
            if hospital.operator_type == "government":
                score += 10
                match_reasons.append("Govt hospital")

            # Distance factor (closer = higher score)
            if hospital.distance_km <= 2:
                score += 30
            elif hospital.distance_km <= 5:
                score += 20
            elif hospital.distance_km <= 10:
                score += 10

            # Verified hospitals get bonus
            if hospital.verified:
                score += 10

            hospital.match_score = score
            hospital.match_reason = ", ".join(match_reasons) if match_reasons else "Nearest hospital"

        # Sort by match score (desc), then distance (asc)
        hospitals.sort(key=lambda h: (-h.match_score, h.distance_km))

        return hospitals

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in km"""
        R = 6371  # Earth's radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def get_nearest_hospital(self, hospitals: list[EmergencyHospital]) -> EmergencyHospital | None:
        """Get the nearest hospital with emergency capability"""
        for h in hospitals:
            if h.has_emergency_room:
                return h
        return hospitals[0] if hospitals else None

    def get_best_match(
        self, hospitals: list[EmergencyHospital], emergency_type: str | None
    ) -> EmergencyHospital | None:
        """Get best matching hospital for the emergency type"""
        if not hospitals:
            return None

        for h in hospitals:
            if emergency_type == "cardiac" and h.has_cardiac_care:
                return h
            if emergency_type == "stroke" and h.has_stroke_unit:
                return h
            if emergency_type == "trauma" and h.has_trauma_center:
                return h

        # Default to first (already sorted by match score)
        return hospitals[0]
