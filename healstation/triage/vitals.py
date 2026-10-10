"""Vital-sign parsing, prompt formatting and the critical-vitals safety rule."""

import re

from emergency_triage.constants import VITAL_SIGNS_CRITICAL


def parse_vital_signs_from_text(text: str) -> dict[str, float | None]:
    """Extract structured vital signs from patient text if frontend appended them as a string."""
    vitals: dict[str, float | None] = {
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


def format_vitals_for_prompt(
    heart_rate: int | None = None,
    bp_systolic: int | None = None,
    bp_diastolic: int | None = None,
    spo2: int | None = None,
    temperature: float | None = None,
) -> str:
    """Format structured vital signs into a clinical string for Gemma's prompt."""
    parts = []
    if heart_rate is not None:
        flag = (
            " (CRITICAL HIGH)"
            if heart_rate > 150
            else " (CRITICAL LOW)"
            if heart_rate < 40
            else " (HIGH)"
            if heart_rate > 100
            else " (LOW)"
            if heart_rate < 60
            else ""
        )
        parts.append(f"Heart Rate: {heart_rate} BPM{flag}")
    if bp_systolic is not None and bp_diastolic is not None:
        flag = (
            " (HYPERTENSIVE CRISIS)"
            if bp_systolic >= 180
            else " (HIGH)"
            if bp_systolic >= 140
            else " (LOW)"
            if bp_systolic < 90
            else ""
        )
        parts.append(f"Blood Pressure: {bp_systolic}/{bp_diastolic} mmHg{flag}")
    if spo2 is not None:
        flag = " (CRITICAL LOW)" if spo2 < 88 else " (LOW)" if spo2 < 92 else ""
        parts.append(f"SpO2: {spo2}%{flag}")
    if temperature is not None:
        flag = (
            " (HIGH FEVER)"
            if temperature >= 39.5
            else " (FEVER)"
            if temperature >= 38
            else " (LOW)"
            if temperature < 36
            else ""
        )
        parts.append(f"Temperature: {temperature}°C{flag}")
    return ", ".join(parts) if parts else ""


def clamp_vital(value: float | None, low: float, high: float, as_int: bool = True):
    if value is None:
        return None
    clamped = min(max(value, low), high)
    return int(round(clamped)) if as_int else float(clamped)


def critical_vital_findings(
    heart_rate: float | None = None,
    bp_systolic: float | None = None,
    bp_diastolic: float | None = None,
    spo2: float | None = None,
    temperature: float | None = None,
) -> list[str]:
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
