"""Regression tests for API endpoint behaviour and configuration."""

import inspect
import os
import re
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient

import api
from emergency_triage.fairness_engine import FairnessTracker

REPO_ROOT = Path(api.__file__).resolve().parent
client = TestClient(api.app)


def test_transcribe_endpoint_calls_stt_not_itself(monkeypatch):
    # The endpoint used to be named transcribe_audio, shadowing the STT
    # function it calls, so every transcription request failed.
    calls = []

    def _fake_stt(path, language_code="en"):
        calls.append((os.path.exists(path), language_code))
        return "chest pain since morning"

    monkeypatch.setattr(api, "transcribe_audio", _fake_stt)
    response = client.post(
        "/api/transcribe-audio",
        files={"audio": ("recording.webm", b"\x1a\x45\xdf\xa3fake-webm", "audio/webm")},
        data={"language": "hi-IN"},
    )

    assert response.status_code == 200
    assert response.json() == {"text": "chest pain since morning", "language": "hi"}
    assert calls == [(True, "hi")]


def test_transcribe_failure_hides_internal_details(monkeypatch):
    monkeypatch.setattr(api, "transcribe_audio", lambda *a, **k: "ERROR: decoder crashed | first_bytes=deadbeef")
    response = client.post(
        "/api/transcribe-audio",
        files={"audio": ("recording.webm", b"data", "audio/webm")},
        data={"language": "en"},
    )
    assert response.status_code == 503
    assert "deadbeef" not in response.text


def test_transcribe_rejects_oversized_and_empty_uploads(monkeypatch):
    monkeypatch.setattr(api, "transcribe_audio", lambda *a, **k: "unreachable")
    empty = client.post("/api/transcribe-audio", files={"audio": ("a.webm", b"", "audio/webm")})
    assert empty.status_code == 400

    monkeypatch.setattr(api, "MAX_AUDIO_UPLOAD_MB", 0)
    too_big = client.post("/api/transcribe-audio", files={"audio": ("a.webm", b"x" * 10, "audio/webm")})
    assert too_big.status_code == 413


def test_blocking_handlers_run_in_threadpool():
    # Sync handlers are run in a worker thread by FastAPI; async ones that
    # block (Ollama, TTS, Whisper) would freeze every other request.
    for handler in (api.get_consultation, api.transcribe_audio_endpoint, api.get_audio, api.check_audio_status):
        assert not inspect.iscoroutinefunction(handler), handler.__name__


def test_generated_audio_is_unguessable_and_not_cached(monkeypatch, tmp_path):
    monkeypatch.setattr(api, "AUDIO_OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(api, "LOCAL_TTS_ENABLED", True)

    def _fake_tts(text, output_path, language):
        Path(output_path).write_bytes(b"RIFF....WAVE")
        return output_path

    monkeypatch.setattr(api, "text_to_speech_for_api", _fake_tts)
    monkeypatch.setattr(api, "_run_local_gemma_triage", lambda *a, **k: None)

    response = client.post("/api/get-doctor-response", json={"patient_text": "Mild headache.", "language": "en"})
    assert response.status_code == 200
    audio_url = response.json()["audio_url"]
    assert re.fullmatch(r"/api/audio/doctor_response_[0-9a-f]{32}\.wav", audio_url)

    audio = client.get(audio_url)
    assert audio.status_code == 200
    assert audio.headers["cache-control"] == "no-store"
    assert "access-control-allow-origin" not in audio.headers

    status = client.get(audio_url.replace("/api/audio/", "/api/audio-status/"))
    assert status.json()["ready"] is True


def test_audio_endpoints_reject_unknown_filenames():
    for name in ("api.py", "config.py", "doctor_response_123.mp3", "doctor_response_" + "a" * 32 + ".exe"):
        assert client.get(f"/api/audio/{name}").status_code == 404
        assert client.get(f"/api/audio-status/{name}").status_code == 404


def test_consultation_input_limits():
    assert client.post("/api/get-doctor-response", json={"patient_text": ""}).status_code == 422
    too_long = "a" * (api.MAX_TEXT_CHARS + 1)
    assert client.post("/api/get-doctor-response", json={"patient_text": too_long}).status_code == 422
    many_images = {"patient_text": "rash", "image_data": ["x"] * (api.MAX_ATTACHMENTS + 1)}
    assert client.post("/api/get-doctor-response", json=many_images).status_code == 422


def test_request_size_limit(monkeypatch):
    monkeypatch.setattr(api, "MAX_REQUEST_MB", 0)
    response = client.post("/api/get-doctor-response", json={"patient_text": "headache"})
    assert response.status_code == 413


def test_fairness_tracks_hindi_and_marathi():
    tracker = FairnessTracker()
    tracker.record_case(age=30, gender="female", language="hi", is_correct=True, confidence=0.8)
    tracker.record_case(age=30, gender="male", language="mr-IN", is_correct=False, confidence=0.6)
    accuracy = tracker.get_metrics()["group_accuracy"]["language"]
    assert accuracy["Hindi"] == 1.0
    assert accuracy["Marathi"] == 0.0


def _config_value(expression, **env):
    clean_env = {k: v for k, v in os.environ.items() if not k.startswith(("OLLAMA_", "LOCAL_GEMMA_"))}
    clean_env.update(env)
    result = subprocess.run(
        [sys.executable, "-c", f"import config; print({expression})"],
        cwd=REPO_ROOT,
        env=clean_env,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def test_triage_model_follows_ollama_model():
    # .env.example documents OLLAMA_MODEL=gemma2:2b for low-spec hardware;
    # triage used to ignore it and always call gemma4:e2b.
    assert _config_value("config.LOCAL_GEMMA_MODEL", OLLAMA_MODEL="gemma2:2b") == "gemma2:2b"
    assert (
        _config_value("config.LOCAL_GEMMA_URL", OLLAMA_BASE_URL="http://ollama:11434/")
        == "http://ollama:11434/api/chat"
    )


def test_bad_numeric_env_values_fall_back_to_defaults():
    assert _config_value("config.API_PORT", API_PORT="not-a-port") == "8001"
    assert _config_value("config.STT_CPU_THREADS", LOCAL_STT_CPU_THREADS="lots") == "0"
