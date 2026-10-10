"""Explainability summary of which inputs contributed to a triage decision."""

from typing import Any


def build_consensus_explanation(
    patient_text: str | None,
    typed_text: str | None,
    transcription_text: str | None,
    image_data: list[str] | None,
    pdf_data: list[dict] | None,
    final_urgency: str,
) -> dict[str, Any]:
    """
    Build a simple multi-input consensus summary for explainability.
    """

    def _norm(text: str | None) -> str:
        return str(text or "").strip().lower()

    def _high_risk(text: str) -> bool:
        markers = [
            "chest pain",
            "shortness of breath",
            "cannot breathe",
            "can't breathe",
            "stroke",
            "severe bleeding",
            "poison",
            "overdose",
        ]
        return any(marker in text for marker in markers)

    patient_norm = _norm(patient_text)
    typed_norm = _norm(typed_text)
    trans_norm = _norm(transcription_text)

    has_typed = bool(typed_norm)
    has_trans = bool(trans_norm)
    has_images = bool(image_data)
    has_pdfs = bool(pdf_data)

    typed_risk = _high_risk(typed_norm) if has_typed else False
    trans_risk = _high_risk(trans_norm) if has_trans else False

    conflict = bool(has_typed and has_trans and typed_risk != trans_risk)
    if not has_typed and not has_trans:
        resolution_reason = "Limited inputs across modalities; consensus used available signals."
    elif conflict:
        resolution_reason = "Conflicting signals detected across modalities; conservative triage selected."
    else:
        resolution_reason = "Clinical signals aligned across modalities."

    return {
        "conflict": conflict,
        "final_urgency": final_urgency,
        "resolution_reason": resolution_reason,
        "signals": {
            "patient_text_present": bool(patient_norm),
            "typed_text_present": has_typed,
            "transcription_present": has_trans,
            "image_count": len(image_data or []),
            "pdf_count": len(pdf_data or []),
            "typed_high_risk": typed_risk,
            "transcription_high_risk": trans_risk,
            "images_present": has_images,
            "pdfs_present": has_pdfs,
        },
    }
