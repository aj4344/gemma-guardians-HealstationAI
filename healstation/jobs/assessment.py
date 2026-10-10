"""The full-assessment job (resource: llm)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from config import LOCAL_GEMMA_MODEL
from healstation import __version__
from healstation.jobs.queue import JobContext, JobSpec, payload_strings
from healstation.speech import response_audio
from healstation.triage import guardrails, pipeline, toxin
from healstation.triage.fast_path import max_urgency
from healstation.triage.prompts import PROMPT_VERSION

if TYPE_CHECKING:
    from healstation.runtime import Runtime


def versions() -> dict[str, Any]:
    """What produced an assessment (QA-06)."""
    return {
        "app": __version__,
        "prompt": PROMPT_VERSION,
        "rules": {"red_flags": guardrails.RULES_VERSION, "toxin": toxin.RULES_VERSION},
        "model": {"tag": LOCAL_GEMMA_MODEL},
    }


def build_result(outcome: pipeline.TriageOutcome, fast_path: dict, *, model_status: str) -> dict[str, Any]:
    triage = outcome.triage_data
    urgency = max_urgency(fast_path.get("urgency"), triage["urgency"])
    reasons = list(triage["reasons"])
    if urgency != triage["urgency"]:
        # A safety rule set a higher urgency than the assessment: the rule wins (INV-2).
        reasons = list(fast_path.get("reasons") or []) + reasons
    return {
        "urgency": urgency,
        "reasons": reasons,
        "actions": triage["actions"],
        "specialist": triage["specialist"],
        "confidence": triage["confidence"],
        "triage_source": outcome.triage_source,
        "doctor_response": outcome.doctor_text,
        "emergency_action_block": outcome.emergency_action_block or fast_path.get("emergency_action_block"),
        "fast_path_urgency": fast_path.get("urgency"),
        "model_status": model_status,
        "versions": versions(),
    }


def _model_status(outcome: pipeline.TriageOutcome) -> str:
    if not outcome.model_attempted:
        return "not_needed"
    return (
        "used" if outcome.triage_source == "local_gemma" else ("declined" if outcome.model_responded else "unavailable")
    )


def assessment_spec(runtime: Runtime) -> JobSpec:
    def run(ctx: JobContext) -> dict:
        p = ctx.payload
        common = {
            "age": p.get("age"),
            "gender": p.get("sex"),
            **{name: p["vitals"].get(name) for name in pipeline.VITAL_NAMES},
            "respiratory_rate": p["vitals"].get("respiratory_rate"),
        }
        ctx.progress("rules", 0.1)
        rules_only = pipeline.assess_symptoms(p["symptoms"], p["language"], **common, use_model=False)
        ctx.save_partial(build_result(rules_only, p["fast_path"], model_status="pending"))
        ctx.check()

        ctx.progress("assessing", 0.3)
        outcome = pipeline.assess_symptoms(
            p["symptoms"], p["language"], **common, use_model=True, model_timeout=max(1.0, ctx.remaining())
        )
        ctx.check()
        result = build_result(outcome, p["fast_path"], model_status=_model_status(outcome))

        if response_audio.LOCAL_TTS_ENABLED:
            ctx.progress("speaking", 0.9)
            result["audio_url"] = response_audio.generate_response_audio(result["doctor_response"], p["language"])
        ctx.check()
        runtime.assessments.complete(ctx.case_id, p["assessment_id"], result)
        return result

    def on_failure(job, payload, code) -> None:
        # Keep whatever partial result exists (RES-04): normally the rules-based assessment.
        partial = runtime.queue.result(job)
        if partial:
            runtime.assessments.complete(job.case_id, payload["assessment_id"], {**partial, "ended": code})

    return JobSpec(
        resource="llm",
        handler=run,
        timeout_s=lambda payload: runtime.settings.timeout_llm_s,
        max_attempts=2,
        sensitive=payload_strings("symptoms"),
        on_failure=on_failure,
    )
