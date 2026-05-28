from __future__ import annotations

from app.rules.common import RuleResult, has_distant_metastasis, is_node_positive, result


def _t_stage(size_cm: float | None) -> str | None:
    if size_cm is None:
        return None
    if size_cm <= 2:
        return "cT1"
    if size_cm <= 5:
        return "cT2"
    return "cT3"


def _n_stage(node_status: str | None) -> str | None:
    positive = is_node_positive(node_status)
    if positive is None:
        return None
    return "cN+" if positive else "cN0"


def _m_stage(metastasis: str | None) -> str | None:
    present = has_distant_metastasis(metastasis)
    if present is None:
        return None
    return "cM1" if present else "cM0"


def evaluate(data: dict) -> RuleResult:
    missing = []
    t = data.get("clinical_t_stage") or _t_stage(data.get("tumor_size_cm"))
    n = data.get("clinical_n_stage") or _n_stage(data.get("clinical_node_status"))
    m = data.get("clinical_m_stage") or _m_stage(data.get("distant_metastasis"))
    if not t:
        missing.append("tumor_size_cm")
    if not n:
        missing.append("clinical_node_status")
    if not m:
        missing.append("distant_metastasis")
    if missing:
        return result("临床 TNM 分期暂不完整", "需要肿瘤大小、临床淋巴结状态和远处转移信息共同判断。", missing)
    caution = ["M1 为IV期/晚期路径，系统治疗和MDT优先"] if m == "cM1" else []
    stage_hint = "IV期" if m == "cM1" else "需结合完整TNM和病理分期"
    return result(f"{t}{n}{m}（{stage_hint}）", "优先使用医生录入TNM；未填写时按肿瘤大小、临床淋巴结状态和远处转移状态进行MVP估算。", caution_flags=caution)
