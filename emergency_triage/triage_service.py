"""
Triage Service
==============
Medical risk scoring algorithms for emergency triage.
Implements HEART Score, BE-FAST Score, and Trauma Assessment.
"""

import re

from .constants import (
    BEFAST_KEYWORDS,
    CRITICAL_KEYWORDS,
    EMERGENCY_KEYWORDS,
    HEART_SCORE_CONFIG,
    TRAUMA_KEYWORDS,
    URGENT_KEYWORDS,
    VITAL_SIGNS_CONCERNING,
    VITAL_SIGNS_CRITICAL,
)
from .models import BeFastScore, EmergencyScores, HeartScore, TraumaScore, VitalSigns


class TriageService:
    """
    Production-grade triage scoring service.
    Implements validated medical scoring systems adapted for pre-hospital assessment.

    IMPORTANT: This is for guidance only and does not replace medical judgment.
    """

    def __init__(self):
        # Pre-compile regex patterns for efficiency
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for keyword matching"""
        # Create case-insensitive patterns
        self.critical_pattern = re.compile('|'.join(re.escape(kw) for kw in CRITICAL_KEYWORDS), re.IGNORECASE)
        self.emergency_pattern = re.compile('|'.join(re.escape(kw) for kw in EMERGENCY_KEYWORDS), re.IGNORECASE)
        self.urgent_pattern = re.compile('|'.join(re.escape(kw) for kw in URGENT_KEYWORDS), re.IGNORECASE)

    def calculate_all_scores(
        self,
        symptoms: str,
        age: int | None = None,
        vital_signs: VitalSigns | None = None,
        medical_history: list[str] | None = None,
    ) -> EmergencyScores:
        """
        Calculate all emergency scores for given symptoms.

        Args:
            symptoms: Patient's symptom description
            age: Patient age in years
            vital_signs: Optional vital signs
            medical_history: Optional list of pre-existing conditions

        Returns:
            EmergencyScores with all individual and combined scores
        """
        symptoms_lower = symptoms.lower()

        # Calculate individual scores
        heart_score = self.calculate_heart_score(symptoms_lower, age, medical_history)
        befast_score = self.calculate_befast_score(symptoms_lower)
        trauma_score = self.calculate_trauma_score(symptoms_lower)

        # Assess vital signs if provided
        vitals_concern = None
        if vital_signs:
            vitals_concern = self._assess_vital_signs(vital_signs)

        # Normalize to 0-10 scale
        normalized_scores = [
            (heart_score.score / heart_score.max_score) * 10,
            (befast_score.score / befast_score.max_score) * 10,
            (trauma_score.score / trauma_score.max_score) * 10,
        ]
        overall_score = int(max(normalized_scores))

        # Boost score if vitals are concerning
        if vitals_concern == "critical":
            overall_score = max(overall_score, 9)
        elif vitals_concern == "concerning":
            overall_score = max(overall_score, 6)

        # Determine overall risk level
        if overall_score >= 8:
            overall_risk = "CRITICAL"
        elif overall_score >= 6:
            overall_risk = "HIGH"
        elif overall_score >= 4:
            overall_risk = "MODERATE"
        elif overall_score >= 2:
            overall_risk = "LOW"
        else:
            overall_risk = "MINIMAL"

        return EmergencyScores(
            overall_score=overall_score,
            overall_risk_level=overall_risk,
            heart_score=heart_score,
            befast_score=befast_score,
            trauma_score=trauma_score,
            vitals_concern_level=vitals_concern,
            is_cardiac_concern=heart_score.score >= 4,
            is_stroke_concern=befast_score.is_stroke_likely,
            is_trauma_concern=trauma_score.score >= 5,
            is_respiratory_concern=self._check_respiratory_concern(symptoms_lower),
        )

    def calculate_heart_score(
        self, symptoms: str, age: int | None = None, medical_history: list[str] | None = None
    ) -> HeartScore:
        """
        Calculate modified HEART Score for pre-hospital cardiac assessment.

        Original HEART Score components:
        - H: History (symptom characteristics)
        - E: ECG (not available pre-hospital, use symptom description)
        - A: Age
        - R: Risk factors
        - T: Troponin (not available, use symptom severity proxy)

        Returns:
            HeartScore with 0-10 total (adapted from 0-10 clinical scale)
        """
        symptoms_lower = symptoms.lower()
        symptoms_detected = []
        score = 0

        # HISTORY SCORE (0-2)
        history_score = 0
        config = HEART_SCORE_CONFIG

        high_suspicion = config["highly_suspicious_history"]
        mod_suspicion = config["moderately_suspicious_history"]

        if any(kw in symptoms_lower for kw in high_suspicion):
            history_score = 2
            symptoms_detected.extend([kw for kw in high_suspicion if kw in symptoms_lower])
        elif any(kw in symptoms_lower for kw in mod_suspicion):
            history_score = 1
            symptoms_detected.extend([kw for kw in mod_suspicion if kw in symptoms_lower])

        score += history_score

        # AGE SCORE (0-2)
        age_score = 0
        if age:
            if age >= config["age_thresholds"]["high_risk"]:
                age_score = 2
            elif age >= config["age_thresholds"]["moderate_risk"]:
                age_score = 1
        else:
            # If age unknown, assume moderate risk (conservative)
            age_score = 1

        score += age_score

        # RISK FACTORS SCORE (0-2)
        risk_score = 0
        risk_factors = config["risk_factors"]

        # Check symptoms text for mentioned risk factors
        mentioned_risks = [rf for rf in risk_factors if rf in symptoms_lower]

        # Also check medical history if provided
        if medical_history:
            for condition in medical_history:
                if any(rf in condition.lower() for rf in risk_factors):
                    mentioned_risks.append(condition)

        if len(mentioned_risks) >= 3:
            risk_score = 2
        elif len(mentioned_risks) >= 1:
            risk_score = 1

        symptoms_detected.extend(mentioned_risks)
        score += risk_score

        # SEVERITY SCORE (0-2) - Proxy for troponin
        severity_score = 0
        severity_indicators = config["severity_indicators"]

        if any(kw in symptoms_lower for kw in severity_indicators):
            severity_score = 2
            symptoms_detected.extend([kw for kw in severity_indicators if kw in symptoms_lower])
        elif "moderate" in symptoms_lower or "increasing" in symptoms_lower:
            severity_score = 1

        score += severity_score

        # Additional points for classic heart attack presentation
        classic_presentation = [
            "sweating",
            "nausea",
            "nauseous",
            "arm pain",
            "left arm",
            "jaw pain",
            "shortness of breath",
        ]
        classic_count = sum(1 for c in classic_presentation if c in symptoms_lower)
        if classic_count >= 2:
            score += 2  # Boost for classic presentation
            symptoms_detected.append("classic_heart_attack_presentation")

        # Cap at max score
        score = min(score, 10)

        # Compose recommendation dynamically from detected indicators
        detected_str = ", ".join(symptoms_detected[:4]) if symptoms_detected else "no specific cardiac indicators"
        if score >= 7:
            risk_level = "HIGH"
            recommendation = f"High cardiac risk detected ({detected_str}). Immediate emergency evaluation recommended."
        elif score >= 4:
            risk_level = "MODERATE"
            recommendation = f"Cardiac concern identified ({detected_str}). Prompt medical evaluation advised."
        else:
            risk_level = "LOW"
            recommendation = f"Limited cardiac indicators ({detected_str}). Monitor symptoms and seek care if they persist or worsen."

        # Calculate confidence based on data completeness
        confidence = 0.6
        if age:
            confidence += 0.1
        if medical_history:
            confidence += 0.1
        if len(symptoms_detected) >= 3:
            confidence += 0.1

        return HeartScore(
            score=score,
            max_score=10,
            risk_level=risk_level,
            history_score=history_score,
            age_score=age_score,
            risk_factors_score=risk_score,
            severity_score=severity_score,
            symptoms_detected=list(set(symptoms_detected)),
            recommendation=recommendation,
            confidence=min(confidence, 0.95),
        )

    def calculate_befast_score(self, symptoms: str) -> BeFastScore:
        """
        Calculate BE-FAST Score for stroke assessment.

        BE-FAST:
        - B: Balance (sudden loss of balance/coordination)
        - E: Eyes (sudden vision changes)
        - F: Face (facial drooping)
        - A: Arms (arm weakness)
        - S: Speech (slurred speech)
        - T: Time (symptom onset - time is critical)

        Returns:
            BeFastScore with stroke likelihood assessment
        """
        symptoms_lower = symptoms.lower()
        symptoms_detected = []

        # Check each BE-FAST component
        balance_issues = any(kw in symptoms_lower for kw in BEFAST_KEYWORDS["balance"])
        if balance_issues:
            symptoms_detected.append("balance_issues")

        eye_symptoms = any(kw in symptoms_lower for kw in BEFAST_KEYWORDS["eyes"])
        if eye_symptoms:
            symptoms_detected.append("eye_symptoms")

        face_drooping = any(kw in symptoms_lower for kw in BEFAST_KEYWORDS["face"])
        if face_drooping:
            symptoms_detected.append("face_drooping")

        arm_weakness = any(kw in symptoms_lower for kw in BEFAST_KEYWORDS["arm"])
        if arm_weakness:
            symptoms_detected.append("arm_weakness")

        speech_difficulty = any(kw in symptoms_lower for kw in BEFAST_KEYWORDS["speech"])
        if speech_difficulty:
            symptoms_detected.append("speech_difficulty")

        time_critical = any(kw in symptoms_lower for kw in BEFAST_KEYWORDS["time_indicators"])
        if time_critical:
            symptoms_detected.append("sudden_onset")

        # Calculate score (0-6)
        score = sum([balance_issues, eye_symptoms, face_drooping, arm_weakness, speech_difficulty, time_critical])

        # Stroke is likely if classic FAS symptoms present
        # (Face, Arm, Speech - the core of FAST)
        classic_stroke_symptoms = sum([face_drooping, arm_weakness, speech_difficulty])
        is_stroke_likely = classic_stroke_symptoms >= 2 or (
            classic_stroke_symptoms >= 1 and (balance_issues or eye_symptoms)
        )

        # Also check for specific stroke indicators
        stroke_words = ["stroke", "tia", "brain attack"]
        if any(w in symptoms_lower for w in stroke_words):
            is_stroke_likely = True
            score = max(score, 4)

        # Compose recommendation dynamically from detected neurological indicators
        neuro_indicators = ", ".join(symptoms_detected[:4]) if symptoms_detected else "no acute neurological signs"
        if is_stroke_likely:
            risk_level = "CRITICAL"
            recommendation = (
                f"Critical stroke indicators present ({neuro_indicators}). Immediate emergency response required."
            )
            golden_hour = (
                f"Neurological deficit detected: {neuro_indicators}. Time-critical intervention window applies."
            )
        elif score >= 3:
            risk_level = "HIGH"
            recommendation = (
                f"Significant neurological indicators ({neuro_indicators}). Urgent specialist evaluation required."
            )
            golden_hour = f"Detected: {neuro_indicators}. Early intervention improves outcomes."
        elif score >= 2:
            risk_level = "MODERATE"
            recommendation = f"Neurological symptoms identified ({neuro_indicators}). Medical evaluation recommended."
            golden_hour = None
        else:
            risk_level = "LOW"
            recommendation = (
                f"Minimal neurological indicators ({neuro_indicators}). Monitor and seek care if progression occurs."
            )
            golden_hour = None

        return BeFastScore(
            score=score,
            max_score=6,
            risk_level=risk_level,
            is_stroke_likely=is_stroke_likely,
            balance_issues=balance_issues,
            eye_symptoms=eye_symptoms,
            face_drooping=face_drooping,
            arm_weakness=arm_weakness,
            speech_difficulty=speech_difficulty,
            time_critical=time_critical,
            symptoms_detected=symptoms_detected,
            recommendation=recommendation,
            golden_hour_warning=golden_hour,
            confidence=0.85 if is_stroke_likely else 0.7,
        )

    def calculate_trauma_score(self, symptoms: str) -> TraumaScore:
        """
        Calculate trauma severity score.

        Assesses:
        - Mechanism of injury
        - Bleeding severity
        - Consciousness level
        - Multiple injuries

        Returns:
            TraumaScore with severity assessment
        """
        symptoms_lower = symptoms.lower()
        symptoms_detected = []
        score = 0

        # Check mechanism (0-3)
        mechanism_severe = any(kw in symptoms_lower for kw in TRAUMA_KEYWORDS["mechanism_severe"])
        if mechanism_severe:
            score += 3
            symptoms_detected.append("high_energy_mechanism")

        # Check bleeding (0-3)
        bleeding_keywords = TRAUMA_KEYWORDS["bleeding"]
        if any(kw in symptoms_lower for kw in ["severe bleeding", "won't stop bleeding", "massive"]):
            score += 3
            symptoms_detected.append("severe_bleeding")
        elif any(kw in symptoms_lower for kw in bleeding_keywords):
            score += 1
            symptoms_detected.append("bleeding")

        # Check consciousness (0-2)
        consciousness_altered = any(kw in symptoms_lower for kw in TRAUMA_KEYWORDS["consciousness"])
        if consciousness_altered:
            score += 2
            symptoms_detected.append("altered_consciousness")

        # Check injuries (0-2)
        injury_keywords = TRAUMA_KEYWORDS["injuries"]
        injury_count = sum(1 for kw in injury_keywords if kw in symptoms_lower)
        if injury_count >= 2:
            score += 2
            symptoms_detected.append("multiple_injuries")
        elif injury_count >= 1:
            score += 1
            symptoms_detected.append("injury_present")

        # Cap at 10
        score = min(score, 10)

        # Compose recommendation dynamically from trauma indicators
        trauma_indicators = ", ".join(symptoms_detected[:4]) if symptoms_detected else "no significant trauma markers"
        if score >= 7:
            risk_level = "CRITICAL"
            recommendation = f"Severe trauma indicators ({trauma_indicators}). Immediate emergency response and immobilisation protocols apply."
        elif score >= 4:
            risk_level = "HIGH"
            recommendation = (
                f"Significant trauma detected ({trauma_indicators}). Emergency evaluation and imaging recommended."
            )
        elif score >= 2:
            risk_level = "MODERATE"
            recommendation = (
                f"Trauma indicators present ({trauma_indicators}). Medical evaluation for occult injury recommended."
            )
        else:
            risk_level = "LOW"
            recommendation = (
                f"Minor trauma indicators ({trauma_indicators}). Home care with monitoring; seek care if worsening."
            )

        return TraumaScore(
            score=score,
            max_score=10,
            risk_level=risk_level,
            mechanism_severe=mechanism_severe,
            bleeding_severe=score >= 3 and "severe_bleeding" in symptoms_detected,
            consciousness_altered=consciousness_altered,
            multiple_injuries="multiple_injuries" in symptoms_detected,
            symptoms_detected=symptoms_detected,
            recommendation=recommendation,
            confidence=0.75,
        )

    def _assess_vital_signs(self, vitals: VitalSigns) -> str:
        """
        Assess vital signs for abnormalities.

        Returns: "critical", "concerning", or "normal"
        """
        critical = VITAL_SIGNS_CRITICAL
        concerning = VITAL_SIGNS_CONCERNING

        # Check for critical values
        if vitals.heart_rate:
            if vitals.heart_rate < critical["heart_rate_low"] or vitals.heart_rate > critical["heart_rate_high"]:
                return "critical"

        if vitals.blood_pressure_systolic:
            if (
                vitals.blood_pressure_systolic < critical["systolic_bp_low"]
                or vitals.blood_pressure_systolic > critical["systolic_bp_high"]
            ):
                return "critical"

        if vitals.oxygen_saturation:
            if vitals.oxygen_saturation < critical["oxygen_saturation_low"]:
                return "critical"

        if vitals.temperature_celsius:
            if (
                vitals.temperature_celsius > critical["temperature_high"]
                or vitals.temperature_celsius < critical["temperature_low"]
            ):
                return "critical"

        if vitals.respiratory_rate:
            if (
                vitals.respiratory_rate < critical["respiratory_rate_low"]
                or vitals.respiratory_rate > critical["respiratory_rate_high"]
            ):
                return "critical"

        # Check for concerning values
        if vitals.heart_rate:
            if vitals.heart_rate < concerning["heart_rate_low"] or vitals.heart_rate > concerning["heart_rate_high"]:
                return "concerning"

        if vitals.oxygen_saturation:
            if vitals.oxygen_saturation < concerning["oxygen_saturation_low"]:
                return "concerning"

        if vitals.temperature_celsius:
            if vitals.temperature_celsius > concerning["temperature_high"]:
                return "concerning"

        return "normal"

    def _check_respiratory_concern(self, symptoms: str) -> bool:
        """Check for respiratory emergency indicators"""
        respiratory_keywords = [
            "can't breathe",
            "difficulty breathing",
            "shortness of breath",
            "gasping",
            "wheezing",
            "choking",
            "blue lips",
            "suffocating",
            "asthma attack",
            "copd exacerbation",
            "oxygen low",
            "breathlessness",
            "सांस फूलना",
            "सांस फूल रही",
            "दम घुट रहा",
            "श्वास कोंडणे",
            "दम लागतोय",
        ]
        return any(kw in symptoms for kw in respiratory_keywords)

    def quick_keyword_check(self, symptoms: str) -> tuple[int, list[str]]:
        """
        Quick keyword-based triage check.
        This is a failsafe that works even if AI analysis fails.

        Returns:
            Tuple of (triage_level, matched_keywords)
        """
        # Check for critical keywords
        critical_matches = self.critical_pattern.findall(symptoms)
        if critical_matches:
            return (1, critical_matches)

        # Check for emergency keywords
        emergency_matches = self.emergency_pattern.findall(symptoms)
        if emergency_matches:
            return (2, emergency_matches)

        # Check for urgent keywords
        urgent_matches = self.urgent_pattern.findall(symptoms)
        if urgent_matches:
            return (3, urgent_matches)

        # Default to standard
        return (4, [])
