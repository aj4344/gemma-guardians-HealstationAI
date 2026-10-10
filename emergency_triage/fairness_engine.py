"""
Fairness metrics tracker for demographic parity checks.
"""

from dataclasses import dataclass
from threading import Lock
from typing import Any

from .constants import (
    FAIRNESS_AGE_GROUPS,
    FAIRNESS_GENDER_GROUPS,
    FAIRNESS_LANGUAGE_GROUPS,
)


@dataclass
class GroupStats:
    total: int = 0
    correct: int = 0
    accuracy_count: int = 0
    confidence_sum: float = 0.0
    confidence_count: int = 0

    def record(self, is_correct: bool | None, confidence: float | None) -> None:
        self.total += 1

        if is_correct is not None:
            self.accuracy_count += 1
            if is_correct:
                self.correct += 1

        if confidence is None:
            return
        try:
            confidence_value = float(confidence)
        except (TypeError, ValueError):
            return
        self.confidence_sum += confidence_value
        self.confidence_count += 1

    def accuracy(self) -> float | None:
        if self.accuracy_count == 0:
            return None
        return self.correct / self.accuracy_count

    def avg_confidence(self) -> float | None:
        if self.confidence_count == 0:
            return None
        return self.confidence_sum / self.confidence_count


class FairnessTracker:
    """Tracks group parity for age, gender, and language."""

    def __init__(
        self,
        age_groups: list | None = None,
        gender_groups: list | None = None,
        language_groups: dict[str, str] | None = None,
        parity_threshold: float = 0.05,
    ) -> None:
        self._lock = Lock()
        self.parity_threshold = float(parity_threshold)

        self._age_groups = age_groups or FAIRNESS_AGE_GROUPS
        self._gender_groups = gender_groups or list(FAIRNESS_GENDER_GROUPS)
        self._language_groups = language_groups or dict(FAIRNESS_LANGUAGE_GROUPS)

        self._age_stats = {group["label"]: GroupStats() for group in self._age_groups}
        self._gender_stats = {group: GroupStats() for group in self._gender_groups}
        self._language_stats = {label: GroupStats() for label in self._language_groups.values()}
        self._language_aliases = {
            "en": "en",
            "english": "en",
            "en-in": "en",
            "hi": "hi",
            "hindi": "hi",
            "hi-in": "hi",
            "mr": "mr",
            "marathi": "mr",
            "mr-in": "mr",
            "es": "es",
            "spanish": "es",
            "fr": "fr",
            "french": "fr",
            "zh": "zh",
            "zh-cn": "zh",
            "zh-hans": "zh",
            "mandarin": "zh",
        }
        self.total_samples = 0

    def record_case(
        self,
        age: Any | None,
        gender: Any | None,
        language: Any | None,
        is_correct: bool | None,
        confidence: float | None,
    ) -> None:
        age_group = self._bucket_age(age)
        gender_group = self._normalize_gender(gender)
        language_group = self._normalize_language(language)

        with self._lock:
            self.total_samples += 1
            if age_group:
                self._age_stats[age_group].record(is_correct, confidence)
            if gender_group:
                self._gender_stats[gender_group].record(is_correct, confidence)
            if language_group:
                self._language_stats[language_group].record(is_correct, confidence)

    def get_metrics(self) -> dict[str, Any]:
        with self._lock:
            age_metrics = self._build_dimension_metrics(self._age_stats)
            gender_metrics = self._build_dimension_metrics(self._gender_stats)
            language_metrics = self._build_dimension_metrics(self._language_stats)

            group_accuracy = {
                "age": age_metrics["accuracy_by_group"],
                "gender": gender_metrics["accuracy_by_group"],
                "language": language_metrics["accuracy_by_group"],
            }
            confidence_parity = {
                "age": age_metrics["confidence_by_group"],
                "gender": gender_metrics["confidence_by_group"],
                "language": language_metrics["confidence_by_group"],
            }

            gaps = [
                age_metrics["accuracy_gap"],
                age_metrics["confidence_gap"],
                gender_metrics["accuracy_gap"],
                gender_metrics["confidence_gap"],
                language_metrics["accuracy_gap"],
                language_metrics["confidence_gap"],
            ]
            valid_gaps = [gap for gap in gaps if gap is not None]
            parity_score = max(valid_gaps) if valid_gaps else 0.0

            data_sufficiency = {
                "age": age_metrics["sufficient"],
                "gender": gender_metrics["sufficient"],
                "language": language_metrics["sufficient"],
            }

            return {
                "group_accuracy": group_accuracy,
                "confidence_parity": confidence_parity,
                "parity_score": float(parity_score),
                "parity_threshold": self.parity_threshold,
                "data_sufficiency": data_sufficiency,
                "fairness_status": self._build_fairness_status(parity_score, data_sufficiency),
                "samples_seen": self.total_samples,
            }

    def reset(self) -> None:
        with self._lock:
            for stats in self._age_stats.values():
                stats.total = 0
                stats.correct = 0
                stats.accuracy_count = 0
                stats.confidence_sum = 0.0
                stats.confidence_count = 0
            for stats in self._gender_stats.values():
                stats.total = 0
                stats.correct = 0
                stats.accuracy_count = 0
                stats.confidence_sum = 0.0
                stats.confidence_count = 0
            for stats in self._language_stats.values():
                stats.total = 0
                stats.correct = 0
                stats.accuracy_count = 0
                stats.confidence_sum = 0.0
                stats.confidence_count = 0
            self.total_samples = 0

    def _bucket_age(self, age: Any | None) -> str | None:
        if age is None:
            return None
        try:
            age_value = int(age)
        except (TypeError, ValueError):
            return None
        for group in self._age_groups:
            minimum = group.get("min")
            maximum = group.get("max")
            if minimum is not None and age_value < minimum:
                continue
            if maximum is not None and age_value > maximum:
                continue
            return group.get("label")
        return None

    def _normalize_gender(self, gender: Any | None) -> str | None:
        if not gender:
            return None
        text = str(gender).strip().lower()
        if text in {"male", "m"}:
            return "male"
        if text in {"female", "f"}:
            return "female"
        if text in {"other", "nonbinary", "non-binary", "nb", "prefer not to say"}:
            return "other"
        return None

    def _normalize_language(self, language: Any | None) -> str | None:
        if not language:
            return None
        text = str(language).strip().lower()
        code = self._language_aliases.get(text)
        if not code:
            return None
        return self._language_groups.get(code)

    @staticmethod
    def _parity_gap(values: dict[str, float | None]) -> tuple[float | None, bool]:
        valid_values = [value for value in values.values() if value is not None]
        if len(valid_values) < 2:
            return None, False
        return max(valid_values) - min(valid_values), True

    def _build_dimension_metrics(self, stats_map: dict[str, GroupStats]) -> dict[str, Any]:
        accuracy_by_group = {group: stats.accuracy() for group, stats in stats_map.items()}
        confidence_by_group = {group: stats.avg_confidence() for group, stats in stats_map.items()}
        accuracy_gap, accuracy_sufficient = self._parity_gap(accuracy_by_group)
        confidence_gap, confidence_sufficient = self._parity_gap(confidence_by_group)

        return {
            "accuracy_by_group": accuracy_by_group,
            "confidence_by_group": confidence_by_group,
            "accuracy_gap": accuracy_gap,
            "confidence_gap": confidence_gap,
            "sufficient": accuracy_sufficient and confidence_sufficient,
        }

    def _build_fairness_status(
        self,
        parity_score: float,
        data_sufficiency: dict[str, bool],
    ) -> str:
        if not all(data_sufficiency.values()):
            return "Review"
        if parity_score > self.parity_threshold:
            return "Review"
        return "Fair"
