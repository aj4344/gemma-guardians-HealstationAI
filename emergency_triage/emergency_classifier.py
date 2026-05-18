"""
Emergency Classifier
====================
Master classification logic that combines all scoring methods
to determine overall triage level and recommendations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from .models import (
    EmergencyTriageRequest, TriageResponse, EmergencyScores,
    EmergencyAction, TriageLevel, VitalSigns
)
from .constants import (
    TRIAGE_LEVELS, EMERGENCY_SPECIALIST_MAPPING, EMERGENCY_NUMBERS
)
from .triage_service import TriageService


class EmergencyClassifier:
    """
    Master emergency classification service.
    Combines keyword detection, scoring algorithms, and optional AI analysis
    to determine triage level and generate recommendations.
    """
    
    def __init__(self):
        self.triage_service = TriageService()
    
    def classify(
        self,
        request: EmergencyTriageRequest
    ) -> TriageResponse:
        """
        Perform complete emergency classification.
        
        This uses a dual-layer approach:
        1. Keyword-based detection (fast, reliable failsafe)
        2. Scoring algorithms (nuanced assessment)
        
        The more severe result is used (conservative approach).
        
        Args:
            request: EmergencyTriageRequest with symptoms and optional data
            
        Returns:
            Complete TriageResponse with level, scores, and recommendations
        """
        symptoms = request.symptoms
        
        # Layer 1: Quick keyword check (failsafe)
        keyword_level, matched_keywords = self.triage_service.quick_keyword_check(symptoms)
        
        # Layer 2: Detailed scoring
        scores = self.triage_service.calculate_all_scores(
            symptoms=symptoms,
            age=request.age,
            vital_signs=request.vital_signs,
            medical_history=request.medical_history
        )
        
        # Determine triage level from scores
        score_level = self._score_to_level(scores)
        
        # Use the more severe (lower number) of keyword vs score assessment
        # This is conservative - better to over-triage than under-triage
        final_level = min(keyword_level, score_level)
        
        # Determine emergency type
        emergency_type = self._determine_emergency_type(scores, symptoms)
        
        # Detect conditions
        detected_conditions = self._detect_conditions(scores, matched_keywords)
        
        # Get triage level config
        level_config = TRIAGE_LEVELS[final_level]
        
        # Determine if 108 should be called
        call_108 = final_level <= 2 or level_config["call_108"]
        
        # Determine time sensitivity
        time_sensitivity = self._determine_time_sensitivity(final_level)
        
        # Generate actions
        primary_action = self._generate_primary_action(
            final_level, emergency_type, call_108, request.language
        )
        secondary_actions = self._generate_secondary_actions(
            final_level, emergency_type, request.language
        )
        
        # Generate specialist recommendation
        specialist = self._get_specialist_recommendation(emergency_type)
        
        # Generate preliminary assessment text
        assessment = self._generate_assessment(
            scores, detected_conditions, final_level, request.language
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(scores, request)
        
        return TriageResponse(
            triage_level=final_level,
            triage_level_name=TriageLevel(level_config["name"]),
            triage_color=level_config["color"],
            scores=scores,
            emergency_type=emergency_type,
            detected_conditions=detected_conditions,
            call_108=call_108,
            time_sensitivity=time_sensitivity,
            primary_action=primary_action,
            secondary_actions=secondary_actions,
            hospitals=[],  # Will be filled by hospital routing service
            nearest_capable_hospital=None,
            specialist_recommendation=specialist,
            preliminary_assessment=assessment,
            assessed_at=datetime.now(),
            confidence=confidence
        )
    
    def _score_to_level(self, scores: EmergencyScores) -> int:
        """Convert overall score to triage level"""
        overall = scores.overall_score
        
        # Check for specific critical conditions first
        if scores.befast_score and scores.befast_score.is_stroke_likely:
            return 1  # Stroke is always critical
        
        if scores.heart_score and scores.heart_score.risk_level == "HIGH":
            return 1  # High cardiac risk is critical
        
        if scores.trauma_score and scores.trauma_score.risk_level == "CRITICAL":
            return 1
        
        if scores.vitals_concern_level == "critical":
            return 1
        
        # Score-based classification
        if overall >= 8:
            return 1  # Critical
        elif overall >= 6:
            return 2  # Emergency
        elif overall >= 4:
            return 3  # Urgent
        elif overall >= 2:
            return 4  # Standard
        else:
            return 5  # Self-care
    
    def _determine_emergency_type(
        self,
        scores: EmergencyScores,
        symptoms: str
    ) -> Optional[str]:
        """Determine the primary emergency type"""
        symptoms_lower = symptoms.lower()
        
        # Check stroke first (time-critical)
        if scores.is_stroke_concern:
            return "stroke"
        
        # Check cardiac
        if scores.is_cardiac_concern:
            return "cardiac"
        
        # Check trauma
        if scores.is_trauma_concern:
            return "trauma"
        
        # Check respiratory
        if scores.is_respiratory_concern:
            return "respiratory"
        
        # Check for other emergencies based on keywords
        if any(kw in symptoms_lower for kw in ["pregnant", "pregnancy", "labor", "baby coming"]):
            return "obstetric"
        
        if any(kw in symptoms_lower for kw in ["child", "infant", "baby", "pediatric"]):
            return "pediatric"
        
        if any(kw in symptoms_lower for kw in ["suicidal", "self harm", "suicide", "kill myself"]):
            return "psychiatric"
        
        # General emergency
        if scores.overall_score >= 5:
            return "general"
        
        return None
    
    def _detect_conditions(
        self,
        scores: EmergencyScores,
        matched_keywords: List[str]
    ) -> List[str]:
        """Compile list of detected conditions"""
        conditions = []
        
        if scores.is_cardiac_concern:
            conditions.append("Potential cardiac event")
        
        if scores.is_stroke_concern:
            conditions.append("Possible stroke (BE-FAST positive)")
        
        if scores.is_trauma_concern:
            conditions.append("Significant trauma")
        
        if scores.is_respiratory_concern:
            conditions.append("Respiratory distress")
        
        if scores.vitals_concern_level == "critical":
            conditions.append("Critical vital signs")
        elif scores.vitals_concern_level == "concerning":
            conditions.append("Abnormal vital signs")
        
        # Add specific symptoms detected
        if scores.heart_score and scores.heart_score.symptoms_detected:
            for s in scores.heart_score.symptoms_detected[:3]:
                conditions.append(f"Cardiac indicator: {s}")
        
        if scores.befast_score and scores.befast_score.symptoms_detected:
            for s in scores.befast_score.symptoms_detected[:3]:
                conditions.append(f"Stroke indicator: {s}")
        
        return conditions[:10]  # Limit to top 10
    
    def _determine_time_sensitivity(self, level: int) -> str:
        """Determine time sensitivity based on triage level"""
        if level == 1:
            return "immediate"
        elif level == 2:
            return "within_10_minutes"
        elif level == 3:
            return "within_1_hour"
        elif level == 4:
            return "within_24_hours"
        else:
            return "scheduled"
    
    def _generate_primary_action(
        self,
        level: int,
        emergency_type: Optional[str],
        call_108: bool,
        language: str
    ) -> EmergencyAction:
        """Generate primary action recommendation dynamically from level configuration."""
        level_config = TRIAGE_LEVELS[level]
        action_key = "action"
        action_key_hindi = "action_hindi"
        action_key_marathi = "action_marathi"

        if call_108:
            return EmergencyAction(
                action_type="call_108",
                action_text=level_config.get(action_key, "Call emergency services immediately"),
                action_text_hindi=level_config.get(action_key_hindi, "तुरंत आपातकालीन सेवाओं को कॉल करें"),
                action_text_marathi=level_config.get(action_key_marathi, "लगेच आपत्कालीन सेवांना कॉल करा"),
                urgency="immediate",
                icon=level_config.get("icon", ""),
                call_number=EMERGENCY_NUMBERS["ambulance"]
            )
        return EmergencyAction(
            action_type=level_config.get("name", "standard"),
            action_text=level_config.get(action_key, "Follow appropriate care pathway"),
            action_text_hindi=level_config.get(action_key_hindi, "उचित देखभाल मार्ग का पालन करें"),
            action_text_marathi=level_config.get(action_key_marathi, "योग्य काळजी मार्गाचे पालन करा"),
            urgency=level_config.get("name", "standard"),
            icon=level_config.get("icon", "")
        )
    
    def _generate_secondary_actions(
        self,
        level: int,
        emergency_type: Optional[str],
        language: str
    ) -> List[EmergencyAction]:
        """Generate secondary action recommendations based on computed triage level and type."""
        actions = []
        if level <= 2:
            actions.append(EmergencyAction(
                action_type="find_er",
                action_text="Locate nearest emergency facility",
                action_text_hindi="निकटतम आपातकालीन सुविधा खोजें",
                action_text_marathi="जवळची आपत्कालीन सुविधा शोधा",
                urgency="immediate",
                icon=""
            ))
        if level <= 3:
            actions.append(EmergencyAction(
                action_type="call_112",
                action_text="Emergency Helpline: 112",
                action_text_hindi="आपातकालीन हेल्पलाइन: 112",
                action_text_marathi="आपत्कालीन हेल्पलाइन: 112",
                urgency="backup",
                icon="",
                call_number="112"
            ))
        if emergency_type == "psychiatric":
            actions.append(EmergencyAction(
                action_type="mental_health",
                action_text="Access mental health crisis support",
                action_text_hindi="मानसिक स्वास्थ्य संकट सहायता प्राप्त करें",
                action_text_marathi="मानसिक आरोग्य संकट समर्थन मिळवा",
                urgency="supportive",
                icon="",
                call_number=EMERGENCY_NUMBERS["mental_health"]
            ))
        return actions
    
    def _get_specialist_recommendation(self, emergency_type: Optional[str]) -> Optional[str]:
        """Get specialist recommendation based on emergency type"""
        if not emergency_type:
            return "General Physician"
        
        specialists = EMERGENCY_SPECIALIST_MAPPING.get(emergency_type, ["General Physician"])
        return specialists[0] if specialists else "Emergency Medicine"
    
    def _generate_assessment(
        self,
        scores: EmergencyScores,
        conditions: List[str],
        level: int,
        language: str
    ) -> str:
        """Generate preliminary assessment text from computed scores and conditions."""
        level_config = TRIAGE_LEVELS[level]
        lines = [f"Triage assessment: {level_config['display_name']} — {level_config['description']}."]
        if conditions:
            lines.append("Identified indicators: " + "; ".join(conditions[:5]) + ".")
        lines.append(f"Composite risk score: {scores.overall_score}/10 ({scores.overall_risk_level}).")
        if scores.heart_score and scores.is_cardiac_concern:
            lines.append(f"Cardiac component: {scores.heart_score.risk_level} (HEART-derived score {scores.heart_score.score}/{scores.heart_score.max_score}).")
        if scores.befast_score and scores.is_stroke_concern:
            lines.append(f"Neurological component: {scores.befast_score.risk_level} (BE-FAST-derived score {scores.befast_score.score}/{scores.befast_score.max_score}).")
        if scores.trauma_score and scores.is_trauma_concern:
            lines.append(f"Trauma component: {scores.trauma_score.risk_level} (severity score {scores.trauma_score.score}/{scores.trauma_score.max_score}).")
        lines.append(f"Recommended action: {level_config['action']}.")
        return " ".join(lines)
    
    def _calculate_confidence(
        self,
        scores: EmergencyScores,
        request: EmergencyTriageRequest
    ) -> float:
        """Calculate confidence from available data completeness and score clarity."""
        confidence = 0.55
        data_points = 0
        if request.age is not None:
            data_points += 1
        if request.vital_signs is not None:
            data_points += 2
        if request.medical_history:
            data_points += 1
        if request.symptom_duration:
            data_points += 1
        confidence += data_points * 0.05
        # High or low composite scores increase clarity
        if scores.overall_score >= 8 or scores.overall_score <= 2:
            confidence += 0.08
        return min(confidence, 0.95)
    
    def quick_classify(self, symptoms: str) -> Dict[str, Any]:
        """
        Quick classification for real-time feedback.
        Uses only keyword matching for speed.
        
        Returns:
            Dict with level, call_108, and basic message
        """
        level, keywords = self.triage_service.quick_keyword_check(symptoms)
        level_config = TRIAGE_LEVELS[level]
        
        return {
            "triage_level": level,
            "triage_level_name": level_config["name"],
            "triage_color": level_config["color"],
            "call_108": level_config["call_108"],
            "action": level_config["action"],
            "matched_keywords": keywords[:5],
            "icon": level_config["icon"]
        }
