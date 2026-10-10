"""RES-01..05: emergency fast path, job queue, back-pressure, deadlines, recovery."""

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

import api
from healstation.jobs import queue as queue_module
from healstation.jobs.queue import FAILED, JobQueue, JobSpec, QueueFull
from healstation.speech import response_audio
from healstation.store.models import Job
from healstation.triage import fast_path, model_client
from tests.helpers import new_case


@pytest.fixture(autouse=True)
def _no_tts(monkeypatch):
    monkeypatch.setattr(response_audio, "LOCAL_TTS_ENABLED", False)


@pytest.fixture
def busy_model(monkeypatch):
    """A model that blocks until released, like Gemma on a slow CPU."""
    release = threading.Event()
    calls = []

    def _blocking(*args, **kwargs):
        calls.append(kwargs.get("timeout"))
        release.wait(30)
        return None

    monkeypatch.setattr(model_client, "run_local_gemma_triage", _blocking)
    yield calls
    release.set()


def _assess(client, case_id, text, **extra):
    return client.post(f"/api/v2/cases/{case_id}/assess", json={"symptoms_confirmed": text, **extra})


def test_fast_path_flags_emergencies_without_the_model(client, runtime, monkeypatch):
    monkeypatch.setattr(model_client, "run_local_gemma_triage", lambda *a, **k: pytest.fail("model called"))
    case_id = new_case(client)
    response = _assess(client, case_id, "Crushing chest pain and sweating for 20 minutes", language="hi")
    assert response.status_code == 200
    body = response.json()
    assert body["fast_path"]["urgency"] == "high"
    assert body["fast_path"]["rules_fired"] == ["red_flag_guardrail"]
    assert body["fast_path"]["emergency_action_block"]["call_ambulance"] is True
    assert any("ऀ" <= ch <= "ॿ" for ch in body["fast_path"]["reasons"][0])

    job = runtime.queue.wait(body["job_id"])
    assert job.status == "SUCCEEDED"
    result = client.get(f"/api/v2/jobs/{body['job_id']}").json()["result"]
    assert result["urgency"] == "high" and result["triage_source"] == "red_flag_guardrail"
    assert result["versions"]["rules"]["red_flags"] == "red-flags-v1"


def test_no_rule_fired_is_never_reported_as_low(client):
    case_id = new_case(client)
    fast = _assess(client, case_id, "Mild headache for two days").json()["fast_path"]
    assert fast["urgency"] is None
    assert fast["status"] == "no_emergency_rule_triggered"
    assert "low" not in fast["message_localized"].lower().replace("low urgency", "")


def test_critical_vitals_raise_urgency_even_if_the_model_says_low(client, runtime, monkeypatch):
    monkeypatch.setattr(
        model_client,
        "run_local_gemma_triage",
        lambda *a, **k: {
            "urgency": "low",
            "reasons": ["Mild"],
            "actions": ["Rest"],
            "specialist": "general",
            "confidence": 0.99,
            "doctor_response": "LOW",
        },
    )
    case_id = new_case(client)
    body = _assess(client, case_id, "Feeling tired", vitals={"spo2": 81, "respiratory_rate": 34}).json()
    assert body["fast_path"]["urgency"] == "high"
    assert body["fast_path"]["rules_fired"] == ["critical_vitals"]
    assert len(body["fast_path"]["reasons"]) == 2
    job = runtime.queue.wait(body["job_id"])
    result = runtime.queue.result(job)
    assert result["urgency"] == "high"
    assert result["fast_path_urgency"] == "high"


@pytest.mark.parametrize("levels", [(None, "low"), ("high", "low"), ("medium", None), ("high", "medium", "low")])
def test_max_urgency_never_lowers(levels):
    best = fast_path.max_urgency(*levels)
    for level in levels:
        assert fast_path.URGENCY_RANK[best] >= fast_path.URGENCY_RANK[level]


def test_fast_path_stays_fast_while_the_model_is_busy(client, runtime, busy_model):
    case_id = new_case(client)
    for _ in range(runtime.settings.max_queue_depth):
        assert _assess(client, case_id, "Cough and mild fever").status_code == 200
    assert runtime.queue.depth() == runtime.settings.max_queue_depth

    timings = []
    for _ in range(40):
        start = time.perf_counter()
        response = _assess(client, case_id, "Sudden weakness on one side and slurred speech")
        timings.append(time.perf_counter() - start)
        assert response.status_code == 429
        assert response.json()["fast_path"]["urgency"] == "high"
    timings.sort()
    assert timings[int(len(timings) * 0.95)] < 0.3, f"p95 {timings[int(len(timings) * 0.95)]:.3f}s"


def test_back_pressure_with_25_concurrent_assessments(runtime, busy_model):
    client = TestClient(api.app)
    case_id = new_case(client)
    with ThreadPoolExecutor(max_workers=25) as pool:
        responses = list(pool.map(lambda i: _assess(client, case_id, f"Cough for {i + 2} days"), range(25)))
    statuses = sorted(r.status_code for r in responses)
    assert statuses.count(200) == 20 and statuses.count(429) == 5
    for refused in (r for r in responses if r.status_code == 429):
        body = refused.json()
        assert body["error"]["code"] == "QUEUE_FULL" and body["error"]["retryable"] is True
        assert int(refused.headers["retry-after"]) == body["error"]["retry_after_s"] >= 5
        assert "fast_path" in body and body["job_id"] is None


def test_llm_timeout_ends_the_job_with_the_rules_based_result(client, runtime, busy_model):
    runtime.settings.timeout_llm_s = 1
    case_id = new_case(client)
    body = _assess(client, case_id, "Fever and body ache for three days").json()
    started = time.monotonic()
    job = runtime.queue.wait(body["job_id"], timeout=5)
    assert time.monotonic() - started < 3
    assert job.status == "TIMED_OUT" and job.error_code == "JOB_TIMED_OUT"
    view = client.get(f"/api/v2/jobs/{job.id}", headers={"Accept-Language": "hi"}).json()
    assert view["error"]["code"] == "JOB_TIMED_OUT" and "108" in view["error"]["message_localized"]
    assert view["result"]["partial"] is True
    assert view["result"]["triage_source"] in {"emergency_fallback", "unassessed"}
    assert view["result"]["urgency"] in {"low", "medium", "high"}
    assessment = client.get(f"/api/v2/cases/{case_id}/assessments").json()["assessments"][0]
    assert assessment["result"]["ended"] == "JOB_TIMED_OUT"
    assert busy_model and busy_model[0] <= 1.0


def test_interrupted_jobs_are_retried_once_then_failed(runtime):
    case = runtime.cases.create()
    sealer = runtime.cases.sealer(case.id)
    ran = []

    def _handler(ctx):
        ran.append(ctx.payload["n"])
        return {"ok": True}

    def _job(job_id, attempts):
        return Job(
            id=job_id,
            type="probe",
            resource="llm",
            case_id=case.id,
            status="RUNNING",
            attempts=attempts,
            max_attempts=2,
            timeout_s=10,
            payload_enc=sealer.seal_json("jobs.payload", job_id, {"n": attempts}),
        )

    with runtime.db.session() as session:
        session.add(_job("a" * 32, 1))  # killed during its first attempt
        session.add(_job("b" * 32, 2))  # killed during its retry
    restarted = JobQueue(runtime.cases, {"llm": 1}, max_depth=5)
    restarted.register("probe", JobSpec(resource="llm", handler=_handler, timeout_s=lambda p: 10))
    restarted.start()
    try:
        assert restarted.wait("a" * 32).status == "SUCCEEDED"
        failed = restarted.wait("b" * 32)
        assert failed.status == FAILED and failed.error_code == "JOB_INTERRUPTED"
        assert ran == [1]
    finally:
        restarted.stop()


def test_queue_full_is_raised_before_anything_is_stored(runtime):
    queue = JobQueue(runtime.cases, {"llm": 1}, max_depth=0)
    queue.register("probe", JobSpec(resource="llm", handler=lambda ctx: None, timeout_s=lambda p: 1))
    with pytest.raises(QueueFull) as full:
        queue.submit("probe", runtime.cases.create().id, {})
    assert 5 <= full.value.retry_after_s <= 300


def test_low_free_disk_refuses_uploads(client, runtime):
    from tests.helpers import png_bytes, upload

    runtime.settings.min_free_disk_bytes = 10**18
    response = upload(client, new_case(client), png_bytes())
    assert response.status_code == 507 and response.json()["error"]["code"] == "STORAGE_FULL"


def test_job_payloads_are_encrypted(client, runtime, busy_model):
    secret = "zebra-striped rash on my left elbow"
    case_id = new_case(client)
    _assess(client, case_id, secret)
    runtime.db.dispose()
    assert secret.encode() not in runtime.db.path.read_bytes()
    assert queue_module.TERMINAL >= {"SUCCEEDED", "FAILED"}
