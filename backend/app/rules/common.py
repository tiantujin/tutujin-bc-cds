from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RuleResult:
    recommendation: str
    rationale: str
    evidence_level: str = "MVP规则/指南要点"
    guideline_version: str = "CBCS 2026 精要版 + breast.pdf 本地参考"
    missing_fields: list[str] = field(default_factory=list)
    caution_flags: list[str] = field(default_factory=list)


GUIDELINE_VERSION = "CBCS 2026 精要版 + breast.pdf 本地参考"


def result(
    recommendation: str,
    rationale: str,
    missing_fields: list[str] | None = None,
    caution_flags: list[str] | None = None,
    evidence_level: str = "MVP规则/指南要点",
) -> RuleResult:
    return RuleResult(
        recommendation=recommendation,
        rationale=rationale,
        evidence_level=evidence_level,
        guideline_version=GUIDELINE_VERSION,
        missing_fields=missing_fields or [],
        caution_flags=caution_flags or [],
    )


def normalized(value: str | None) -> str:
    return (value or "").strip().lower()


def is_positive_percent(value: float | None) -> bool | None:
    if value is None:
        return None
    return value >= 1


def is_node_positive(node_status: str | None) -> bool | None:
    text = normalized(node_status)
    if not text:
        return None
    if "阳" in text or "+" in text or text in {"n1", "n2", "n3", "cn1", "cn2", "cn3"}:
        return True
    if "阴" in text or "-" in text or text in {"n0", "cn0"}:
        return False
    return None


def has_distant_metastasis(value: str | None) -> bool | None:
    text = normalized(value)
    if not text:
        return None
    if any(token in text for token in ["有", "m1", "yes", "阳", "存在"]):
        return True
    if any(token in text for token in ["无", "m0", "no", "阴", "未见"]):
        return False
    return None
