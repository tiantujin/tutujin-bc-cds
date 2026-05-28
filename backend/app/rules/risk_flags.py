from __future__ import annotations

from app.rules.common import RuleResult, has_distant_metastasis, result


def evaluate(data: dict) -> RuleResult:
    flags = []
    missing = []
    if has_distant_metastasis(data.get("distant_metastasis")):
        flags.append("远处转移或疑似远处转移")
    if data.get("focality") in {"多中心", "multicentric"}:
        flags.append("多中心病灶")
    if data.get("lymphovascular_invasion") in {"有", "阳性", "positive"}:
        flags.append("脉管癌栓阳性")
    if data.get("age") is None:
        missing.append("age")
    if data.get("histologic_grade") in (None, ""):
        missing.append("histologic_grade")
    if flags:
        return result("存在需 MDT 讨论或重点复核的风险因素", "风险因素可能影响治疗顺序、手术方式和系统治疗强度。", missing, flags)
    return result("暂未触发强 MDT 风险提示", "当前结构化信息未见远处转移、多中心病灶或脉管癌栓阳性等 MVP 强提醒。", missing)
