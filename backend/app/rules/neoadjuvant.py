from __future__ import annotations

from app.rules.common import RuleResult, has_distant_metastasis, is_node_positive, is_positive_percent, normalized, result


def evaluate(data: dict) -> RuleResult:
    missing = [field for field in ["tumor_size_cm", "clinical_node_status", "distant_metastasis", "er_percent", "pr_percent", "her2"] if data.get(field) in (None, "")]
    if missing:
        return result("暂不作新辅助强推荐", "关键分期或免疫组化信息不完整，应先补齐后再判断治疗路径。", missing)

    if has_distant_metastasis(data.get("distant_metastasis")):
        return result(
            "不属于早期先手术/新辅助常规路径，建议 MDT 讨论",
            "存在远处转移时，治疗目标和系统治疗策略需重新评估。",
            caution_flags=["远处转移/疑似 IV 期"],
        )

    size = data.get("tumor_size_cm") or 0
    node_positive = bool(is_node_positive(data.get("clinical_node_status")))
    her2 = normalized(data.get("her2"))
    er = is_positive_percent(data.get("er_percent"))
    pr = is_positive_percent(data.get("pr_percent"))
    hormone_positive = bool(er or pr)
    her2_positive = "3+" in her2 or "阳" in her2 or "positive" in her2
    her2_negative = "0" in her2 or "1+" in her2 or "阴" in her2 or "negative" in her2

    if her2_positive and (size >= 2 or node_positive):
        return result("考虑新辅助化疗联合抗 HER2 治疗", "HER2 阳性且肿瘤 >=2 cm 或临床淋巴结阳性，符合 MVP 新辅助提示条件。")
    if (not hormone_positive) and her2_negative and (size >= 2 or node_positive):
        return result("考虑新辅助系统治疗", "TNBC 且肿瘤 >=2 cm 或临床淋巴结阳性，符合 MVP 新辅助提示条件。")
    if hormone_positive and her2_negative and size < 2 and not node_positive:
        return result("可优先考虑手术", "HR+/HER2-、肿瘤 <2 cm 且临床淋巴结阴性，倾向早期低危路径，术后再结合病理风险决定辅助治疗。")
    return result("可在先手术与新辅助之间个体化评估", "当前信息未触发明确的新辅助强提示，应结合保乳需求、腋窝状态、分级、Ki-67 和患者意愿综合判断。")
