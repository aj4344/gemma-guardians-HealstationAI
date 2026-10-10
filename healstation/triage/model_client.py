"""Local Gemma 4 triage call through Ollama /api/chat, and output normalisation."""

import json
import logging
from typing import Any

import requests

from config import (
    ENABLE_LOCAL_TRIAGE,
    LOCAL_GEMMA_MODEL,
    LOCAL_GEMMA_NUM_CTX,
    LOCAL_GEMMA_NUM_PREDICT,
    LOCAL_GEMMA_TIMEOUT_SECONDS,
    LOCAL_GEMMA_URL,
)
from healstation.triage.prompts import GEMMA_SYSTEM_PROMPT, build_local_gemma_prompt

logger = logging.getLogger("healstation")


# Accept a legacy /api/generate URL from older .env files; triage uses /api/chat.
LOCAL_GEMMA_CHAT_URL = LOCAL_GEMMA_URL.replace("/api/generate", "/api/chat")


def extract_json_payload(text: str) -> dict[str, Any] | None:
    """Extract first JSON object from model text output."""
    if not text:
        return None

    text = text.strip()
    try:
        parsed = json.loads(text)
        return _normalize_local_gemma_payload(parsed) if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    candidate = text[start : end + 1]
    try:
        parsed = json.loads(candidate)
        return _normalize_local_gemma_payload(parsed) if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _normalize_local_gemma_urgency(value: Any) -> str | None:
    """Map the model's urgency label to low/medium/high.

    Unrecognised labels return None so the payload fails validation and the
    rules-based classifier is used, instead of silently defaulting to "low".
    """
    text = str(value or "").strip().lower()
    if text in {"low", "medium", "high"}:
        return text

    mapping = {
        "critical": "high",
        "emergency": "high",
        "immediate": "high",
        "severe": "high",
        "urgent": "medium",
        "moderate": "medium",
        "stable": "low",
        "minor": "low",
        "routine": "low",
    }
    return mapping.get(text)


def _normalize_local_gemma_list(value: Any) -> list[str]:
    if value is None:
        return []

    items = value if isinstance(value, list) else [value]
    normalized: list[str] = []
    for item in items:
        text = str(item).strip()
        if text:
            normalized.append(text)
    return normalized


def _normalize_local_gemma_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.5

    if confidence < 0:
        return 0.0
    if confidence > 1:
        return 1.0
    return confidence


def _normalize_local_gemma_payload(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None

    normalized = dict(payload)
    normalized["urgency"] = _normalize_local_gemma_urgency(payload.get("urgency"))
    normalized["reasons"] = _normalize_local_gemma_list(payload.get("reasons"))
    normalized["actions"] = _normalize_local_gemma_list(payload.get("actions"))
    normalized["confidence"] = _normalize_local_gemma_confidence(payload.get("confidence"))
    return normalized


def run_local_gemma_triage(
    patient_text: str,
    language: str,
    heart_rate: int | None = None,
    bp_systolic: int | None = None,
    bp_diastolic: int | None = None,
    spo2: int | None = None,
    temperature: float | None = None,
    timeout: float | None = None,
) -> dict[str, Any] | None:
    """Try local Gemma via Ollama /api/chat (instruction-tuned endpoint).

    ``timeout`` caps the HTTP call (a job passes its remaining deadline).
    """
    if not ENABLE_LOCAL_TRIAGE:
        return None
    try:
        user_message = build_local_gemma_prompt(
            patient_text,
            language,
            heart_rate=heart_rate,
            bp_systolic=bp_systolic,
            bp_diastolic=bp_diastolic,
            spo2=spo2,
            temperature=temperature,
        )
        # Use /api/chat — required for instruction-tuned models like gemma4:e2b
        chat_url = LOCAL_GEMMA_CHAT_URL
        payload = {
            "model": LOCAL_GEMMA_MODEL,
            "messages": [
                {"role": "system", "content": GEMMA_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {
                "temperature": 0.15,
                "num_ctx": LOCAL_GEMMA_NUM_CTX,
                "num_predict": LOCAL_GEMMA_NUM_PREDICT,
            },
        }
        logger.info("Calling Ollama model=%s num_ctx=%d", LOCAL_GEMMA_MODEL, LOCAL_GEMMA_NUM_CTX)
        response = requests.post(chat_url, json=payload, timeout=timeout or LOCAL_GEMMA_TIMEOUT_SECONDS)
        response.raise_for_status()

        raw = response.json()
        # /api/chat response is at raw["message"]["content"]
        if isinstance(raw, dict) and "message" in raw:
            model_text = raw["message"].get("content", "")
        else:
            model_text = raw.get("response", "") if isinstance(raw, dict) else ""

        logger.debug("Model output received (%d chars)", len(model_text))
        parsed = extract_json_payload(model_text)
        if parsed:
            logger.info(
                "Model triage parsed: urgency=%s specialist=%s", parsed.get("urgency"), parsed.get("specialist")
            )
        else:
            logger.warning("Could not parse JSON from model output")
        return parsed
    except Exception as local_error:
        logger.warning("Local Gemma triage unavailable/failed: %s", local_error)
        return None
