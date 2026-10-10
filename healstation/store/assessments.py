"""Assessment records: the fast-path result at once, the full result when its job ends."""

from __future__ import annotations

import json

from sqlalchemy import select

from healstation.store.cases import CaseStore, new_id
from healstation.store.models import Assessment


class AssessmentStore:
    def __init__(self, cases: CaseStore):
        self.cases = cases

    def create(self, case_id: str, fast_path: dict, inputs_digest: str | None) -> str:
        assessment_id = new_id()
        sealer = self.cases.sealer(case_id)
        with self.cases.db.session() as session:
            session.add(
                Assessment(
                    id=assessment_id,
                    case_id=case_id,
                    inputs_digest=inputs_digest,
                    fast_path_enc=sealer.seal_json("assessments.fast_path", assessment_id, fast_path),
                    urgency=fast_path.get("urgency"),
                )
            )
        return assessment_id

    def attach_job(self, assessment_id: str, job_id: str) -> None:
        with self.cases.db.session() as session:
            row = session.get(Assessment, assessment_id)
            if row is not None:
                row.job_id = job_id

    def complete(self, case_id: str, assessment_id: str, result: dict) -> None:
        sealer = self.cases.sealer(case_id)
        with self.cases.db.session() as session:
            row = session.get(Assessment, assessment_id)
            if row is None:
                return
            row.result_enc = sealer.seal_json("assessments.result", assessment_id, result)
            row.urgency = result.get("urgency")
            row.versions_json = json.dumps(result.get("versions") or {}, sort_keys=True)
            row.sources_json = json.dumps(result.get("sources") or [], sort_keys=True)

    def list(self, case_id: str) -> list[dict]:
        sealer = self.cases.sealer(case_id)
        with self.cases.db.session() as session:
            rows = session.scalars(
                select(Assessment).where(Assessment.case_id == case_id).order_by(Assessment.created_at)
            ).all()
        return [
            {
                "assessment_id": row.id,
                "job_id": row.job_id,
                "created_at": row.created_at.isoformat(),
                "urgency": row.urgency,
                "fast_path": sealer.open_json("assessments.fast_path", row.id, row.fast_path_enc),
                "result": sealer.open_json("assessments.result", row.id, row.result_enc),
            }
            for row in rows
        ]
