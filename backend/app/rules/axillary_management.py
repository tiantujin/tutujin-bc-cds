from __future__ import annotations

from app.rules.common import RuleResult, is_node_positive, result


def evaluate(data: dict) -> RuleResult:
    node_positive = is_node_positive(data.get("clinical_node_status"))
    if node_positive is None:
        return result("腋窝处理建议待补充", "需明确临床淋巴结状态，必要时结合腋窝超声和穿刺病理。", ["clinical_node_status"])
    if node_positive:
        return result("建议评估腋窝阳性证据并制定腋窝处理策略", "临床淋巴结阳性时，应结合穿刺病理、新辅助计划和术后病理决定 SLNB/ALND 等路径。")
    return result("可考虑前哨淋巴结活检路径", "临床腋窝阴性时，早期病例通常可评估 SLNB 作为腋窝分期方式。")
