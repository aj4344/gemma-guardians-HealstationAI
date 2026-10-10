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


_CRITICAL_VITAL_TEXT = {
    "en": {
        "heart_rate": "Heart rate {value} BPM is in the critical range.",
        "bp_systolic": "Systolic blood pressure {value} mmHg is in the critical range.",
        "bp_diastolic": "Diastolic blood pressure {value} mmHg is in the critical range.",
        "spo2": "Oxygen saturation {value}% is critically low.",
        "temperature": "Temperature {value}°C is in the critical range.",
        "respiratory_rate": "Breathing rate {value} per minute is in the critical range.",
    },
    "hi": {
        "heart_rate": "हृदय गति {value} प्रति मिनट गंभीर सीमा में है।",
        "bp_systolic": "सिस्टोलिक रक्तचाप {value} mmHg गंभीर सीमा में है।",
        "bp_diastolic": "डायस्टोलिक रक्तचाप {value} mmHg गंभीर सीमा में है।",
        "spo2": "ऑक्सीजन स्तर {value}% गंभीर रूप से कम है।",
        "temperature": "तापमान {value}°C गंभीर सीमा में है।",
        "respiratory_rate": "सांस की दर {value} प्रति मिनट गंभीर सीमा में है।",
    },
    "mr": {
        "heart_rate": "हृदयाचे ठोके {value} प्रति मिनिट गंभीर मर्यादेत आहेत.",
        "bp_systolic": "सिस्टोलिक रक्तदाब {value} mmHg गंभीर मर्यादेत आहे.",
        "bp_diastolic": "डायस्टोलिक रक्तदाब {value} mmHg गंभीर मर्यादेत आहे.",
        "spo2": "ऑक्सिजन पातळी {value}% गंभीरपणे कमी आहे.",
        "temperature": "तापमान {value}°C गंभीर मर्यादेत आहे.",
        "respiratory_rate": "श्वसन दर {value} प्रति मिनिट गंभीर मर्यादेत आहे.",
    },
}


def critical_vital_names(
    heart_rate: float | None = None,
    bp_systolic: float | None = None,
    bp_diastolic: float | None = None,
    spo2: float | None = None,
    temperature: float | None = None,
    respiratory_rate: float | None = None,
) -> list[tuple[str, float]]:
    """(vital, value) for every reading in the critical range (emergency_triage.constants thresholds)."""
    limits = VITAL_SIGNS_CRITICAL
    critical = []
    if heart_rate is not None and not limits["heart_rate_low"] <= heart_rate <= limits["heart_rate_high"]:
        critical.append(("heart_rate", heart_rate))
    if bp_systolic is not None and not limits["systolic_bp_low"] <= bp_systolic <= limits["systolic_bp_high"]:
        critical.append(("bp_systolic", bp_systolic))
    if bp_diastolic is not None and bp_diastolic > limits["diastolic_bp_high"]:
        critical.append(("bp_diastolic", bp_diastolic))
    if spo2 is not None and spo2 < limits["oxygen_saturation_low"]:
        critical.append(("spo2", spo2))
    if temperature is not None and not limits["temperature_low"] <= temperature <= limits["temperature_high"]:
        critical.append(("temperature", temperature))
    if respiratory_rate is not None and not (
        limits["respiratory_rate_low"] <= respiratory_rate <= limits["respiratory_rate_high"]
    ):
        critical.append(("respiratory_rate", respiratory_rate))
    return critical


def critical_vital_findings(
    heart_rate: float | None = None,
    bp_systolic: float | None = None,
    bp_diastolic: float | None = None,
    spo2: float | None = None,
    temperature: float | None = None,
    respiratory_rate: float | None = None,
    language: str = "en",
) -> list[str]:
    """Localized findings for every vital sign in the critical range."""
    texts = _CRITICAL_VITAL_TEXT.get(language, _CRITICAL_VITAL_TEXT["en"])
    return [
        texts[name].format(value=f"{value:g}")
        for name, value in critical_vital_names(
            heart_rate, bp_systolic, bp_diastolic, spo2, temperature, respiratory_rate
        )
    ]
