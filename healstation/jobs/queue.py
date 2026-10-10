"""Persistent job queue with one bounded worker pool per heavy resource (ADR-002).

- Back-pressure (RES-03): at most ``max_queue_depth`` unfinished jobs; above that
  ``submit`` raises QueueFull with a retry estimate. The emergency fast path
  never enqueues, so it is never refused.
- Deadlines (RES-04): a watchdog marks overdue jobs TIMED_OUT and signals the
  handler to stop. Partial results saved by the handler are kept and labelled.
- Restart recovery (RES-02): jobs left RUNNING are retried once, then FAILED.
"""

from __future__ import annotations

import logging
import math
import threading
import time
from collections import deque
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select

from healstation.security.context import sensitive_scope
from healstation.store.cases import CaseStore, new_id
from healstation.store.keys import CaseKeyMissing, FieldSealer
from healstation.store.models import Job, utcnow

logger = logging.getLogger("healstation.jobs")

QUEUED = "QUEUED"
RUNNING = "RUNNING"
SUCCEEDED = "SUCCEEDED"
FAILED = "FAILED"
TIMED_OUT = "TIMED_OUT"
CANCELLED = "CANCELLED"
TERMINAL = {SUCCEEDED, FAILED, TIMED_OUT, CANCELLED}


class QueueFull(Exception):
    def __init__(self, retry_after_s: int):
        super().__init__("queue full")
        self.retry_after_s = retry_after_s


class JobError(Exception):
    """A handler's expected failure, reported with a reason code."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class JobCancelled(Exception):
    pass


@dataclass
class JobSpec:
    resource: str
    handler: Callable[[JobContext], dict | None]
    timeout_s: Callable[[dict], float]
    max_attempts: int = 2
    # Patient strings in the payload, for the logging filter.
    sensitive: Callable[[dict], Iterable[str | None]] = lambda payload: ()
    # Called once when the job ends without succeeding (e.g. to reject an upload).
    on_failure: Callable[[Job, dict, str], None] | None = None


@dataclass
class JobContext:
    queue: JobQueue
    job_id: str
    case_id: str | None
    payload: dict
    deadline: float  # time.monotonic() value
    cancel_event: threading.Event = field(default_factory=threading.Event)

    @property
    def cancelled(self) -> bool:
        return self.cancel_event.is_set()

    def remaining(self) -> float:
        return max(0.0, self.deadline - time.monotonic())

    def check(self) -> None:
        if self.cancelled or self.remaining() <= 0:
            raise JobCancelled()

    def progress(self, stage: str, fraction: float | None = None) -> None:
        self.queue._update(self.job_id, stage=stage, progress=fraction)

    def save_partial(self, result: dict) -> None:
        """Store a usable result now, so a timeout still has something to show."""
        self.queue._store_result(self.job_id, self.case_id, {**result, "partial": True})


class JobQueue:
    def __init__(self, cases: CaseStore, pools: dict[str, int], max_depth: int, clock: Callable[[], datetime] = utcnow):
        self.cases = cases
        self.db = cases.db
        self.pools = dict(pools)
        self.max_depth = max_depth
        self.clock = clock
        self.specs: dict[str, JobSpec] = {}
        self._executors: dict[str, ThreadPoolExecutor] = {}
        self._running: dict[str, tuple[JobContext, JobSpec]] = {}
        self._lock = threading.Lock()
        self._depth = 0
        self._durations: dict[str, deque[float]] = {}
        self._stop = threading.Event()
        self._watchdog: threading.Thread | None = None
        self._started = False

    # ── lifecycle ────────────────────────────────────────────────────────────
    def register(self, job_type: str, spec: JobSpec) -> None:
        if spec.resource not in self.pools:
            raise ValueError(f"no pool for resource {spec.resource}")
        self.specs[job_type] = spec

    def start(self) -> None:
        if self._started:
            return
        self._stop.clear()
        for resource, size in self.pools.items():
            self._executors[resource] = ThreadPoolExecutor(
                max_workers=max(1, size), thread_name_prefix=f"hs-{resource}"
            )
        queued = self._recover()
        with self._lock:
            self._depth = self._count_unfinished()
        for job_id, resource in queued:
            self._dispatch(job_id, resource)
        self._watchdog = threading.Thread(target=self._watch, name="hs-job-watchdog", daemon=True)
        self._watchdog.start()
        self._started = True

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            running = list(self._running.values())
        for ctx, _spec in running:
            ctx.cancel_event.set()
        for executor in self._executors.values():
            executor.shutdown(wait=False, cancel_futures=True)
        self._executors.clear()
        self._started = False

    def _recover(self) -> list[tuple[str, str]]:
        """Interrupted jobs are retried once; a second interruption fails them (RES-02)."""
        with self.db.session() as session:
            for job in session.scalars(select(Job).where(Job.status == RUNNING)):
                if job.attempts < job.max_attempts:
                    job.status = QUEUED
                    job.stage = "retrying"
                else:
                    job.status = FAILED
                    job.error_code = "JOB_INTERRUPTED"
                    job.finished_at = self.clock()
                    self._notify_failure(job, "JOB_INTERRUPTED")
            queued = session.scalars(select(Job).where(Job.status == QUEUED).order_by(Job.created_at)).all()
            return [(job.id, job.resource) for job in queued]

    def _count_unfinished(self) -> int:
        with self.db.session() as session:
            return session.scalar(select(func.count()).select_from(Job).where(Job.status.in_((QUEUED, RUNNING))))

    # ── submitting ───────────────────────────────────────────────────────────
    def depth(self) -> int:
        with self._lock:
            return self._depth

    def retry_after(self, resource: str) -> int:
        recent = self._durations.get(resource)
        average = sum(recent) / len(recent) if recent else 10.0
        backlog = max(1, self.depth() - self.max_depth + 1)
        estimate = average * backlog / max(1, self.pools.get(resource, 1))
        return int(min(300, max(5, math.ceil(estimate))))

    def submit(self, job_type: str, case_id: str | None, payload: dict, ref_id: str | None = None) -> str:
        spec = self.specs[job_type]
        with self._lock:
            full = self._depth >= self.max_depth
            if not full:
                self._depth += 1
        if full:
            raise QueueFull(self.retry_after(spec.resource))
        job_id = new_id()
        try:
            sealer = self._sealer(case_id)
            with self.db.session() as session:
                session.add(
                    Job(
                        id=job_id,
                        type=job_type,
                        resource=spec.resource,
                        case_id=case_id,
                        ref_id=ref_id,
                        status=QUEUED,
                        stage="queued",
                        max_attempts=spec.max_attempts,
                        timeout_s=float(spec.timeout_s(payload)),
                        payload_enc=sealer.seal_json("jobs.payload", job_id, payload),
                    )
                )
        except Exception:
            with self._lock:
                self._depth -= 1
            raise
        self._dispatch(job_id, spec.resource)
        return job_id

    def _dispatch(self, job_id: str, resource: str) -> None:
        executor = self._executors.get(resource)
        if executor is not None:
            executor.submit(self._run, job_id)

    def _sealer(self, case_id: str | None) -> FieldSealer:
        if case_id is None:
            raise ValueError("jobs belong to a case")
        return self.cases.sealer(case_id)

    # ── running ──────────────────────────────────────────────────────────────
    def _run(self, job_id: str) -> None:
        with self.db.session() as session:
            job = session.get(Job, job_id)
            if job is None or job.status != QUEUED:
                return
            spec = self.specs.get(job.type)
            if spec is None:
                return
            job.status = RUNNING
            job.attempts += 1
            job.started_at = self.clock()
            job.deadline_at = job.started_at + timedelta(seconds=job.timeout_s)
            job.stage = "starting"
            case_id, timeout_s = job.case_id, job.timeout_s
        started = time.monotonic()
        try:
            payload = self._sealer(case_id).open_json("jobs.payload", job_id, job.payload_enc)
        except CaseKeyMissing:
            self._finish(job_id, CANCELLED, error_code="NOT_FOUND")
            return
        ctx = JobContext(self, job_id, case_id, payload, deadline=started + timeout_s)
        with self._lock:
            self._running[job_id] = (ctx, spec)
        try:
            with sensitive_scope(spec.sensitive(payload)):
                result = spec.handler(ctx)
            self._finish(job_id, SUCCEEDED, result=result)
        except JobCancelled:
            pass  # the watchdog or a cancel already recorded the outcome
        except JobError as error:
            self._finish(job_id, FAILED, error_code=error.code)
        except CaseKeyMissing:
            self._finish(job_id, CANCELLED, error_code="NOT_FOUND")
        except Exception as error:
            logger.error("Job failed", extra={"hs": {"job_type": job.type, "error_type": type(error).__name__}})
            self._finish(job_id, FAILED, error_code="JOB_FAILED")
        finally:
            with self._lock:
                self._running.pop(job_id, None)
            self._durations.setdefault(spec.resource, deque(maxlen=20)).append(time.monotonic() - started)

    def _finish(self, job_id: str, status: str, *, result: dict | None = None, error_code: str | None = None) -> bool:
        """Record a terminal state once; later outcomes (a late result after a timeout) are ignored."""
        with self.db.session() as session:
            job = session.get(Job, job_id)
            if job is None or job.status in TERMINAL:
                return False
            if result is not None:
                job.result_enc = self._sealer(job.case_id).seal_json("jobs.result", job_id, result)
            job_type = job.type
            job.status = status
            job.error_code = error_code
            job.finished_at = self.clock()
            if status == SUCCEEDED:
                job.progress = 1.0
                job.stage = "done"
            failed_job = job if status != SUCCEEDED else None
        with self._lock:
            self._depth = max(0, self._depth - 1)
        if failed_job is not None and error_code != "NOT_FOUND":
            self._notify_failure(failed_job, error_code or "JOB_FAILED")
        logger.info("Job finished", extra={"hs": {"job_type": job_type, "status": status, "reason_code": error_code}})
        return True

    def _notify_failure(self, job: Job, code: str) -> None:
        spec = self.specs.get(job.type)
        if spec is None or spec.on_failure is None:
            return
        try:
            payload = self._sealer(job.case_id).open_json("jobs.payload", job.id, job.payload_enc)
            spec.on_failure(job, payload, code)
        except Exception as error:
            logger.error("Job failure hook failed", extra={"hs": {"error_type": type(error).__name__}})

    def _watch(self) -> None:
        while not self._stop.wait(0.2):
            now = time.monotonic()
            with self._lock:
                overdue = [(job_id, ctx) for job_id, (ctx, _spec) in self._running.items() if now > ctx.deadline]
            for job_id, ctx in overdue:
                ctx.cancel_event.set()
                self._finish(job_id, TIMED_OUT, error_code="JOB_TIMED_OUT")

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            running = self._running.get(job_id)
        if running:
            running[0].cancel_event.set()
        return self._finish(job_id, CANCELLED, error_code="CANCELLED")

    # ── state for handlers and the API ───────────────────────────────────────
    def _update(self, job_id: str, *, stage: str | None = None, progress: float | None = None) -> None:
        with self.db.session() as session:
            job = session.get(Job, job_id)
            if job is None or job.status in TERMINAL:
                return
            if stage is not None:
                job.stage = stage
            if progress is not None:
                job.progress = max(0.0, min(1.0, progress))

    def _store_result(self, job_id: str, case_id: str | None, result: dict) -> None:
        sealed = self._sealer(case_id).seal_json("jobs.result", job_id, result)
        with self.db.session() as session:
            job = session.get(Job, job_id)
            if job is not None and job.status == RUNNING:
                job.result_enc = sealed

    def get(self, job_id: str) -> Job | None:
        with self.db.session() as session:
            return session.get(Job, job_id)

    def result(self, job: Job) -> dict | None:
        if job.result_enc is None:
            return None
        return self._sealer(job.case_id).open_json("jobs.result", job.id, job.result_enc)

    def wait(self, job_id: str, timeout: float = 10.0) -> Job:
        """Block until the job is finished (tests and scripts)."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            job = self.get(job_id)
            if job is not None and job.status in TERMINAL:
                return job
            time.sleep(0.02)
        raise TimeoutError(job_id)

    def prune(self, older_than: datetime) -> int:
        """Delete finished jobs (their encrypted payloads and results) after a day (PRIV-02)."""
        with self.db.session() as session:
            rows = session.scalars(select(Job).where(Job.status.in_(TERMINAL), Job.finished_at < older_than)).all()
            for row in rows:
                session.delete(row)
            return len(rows)


def payload_strings(*keys: str) -> Callable[[dict], list[Any]]:
    return lambda payload: [payload.get(key) for key in keys]
