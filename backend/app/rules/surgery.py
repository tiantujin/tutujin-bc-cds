from __future__ import annotations

from app.rules.common import RuleResult, has_distant_metastasis, result


def evaluate(data: dict) -> RuleResult:
    if has_distant_metastasis(data.get("distant_metastasis")):
        return result(
            "暂不建议直接进入早期根治性手术路径",
            "远处转移存在时，应优先 MDT 明确全身治疗目标和局部治疗时机。",
            caution_flags=["需 MDT 讨论局部治疗价值"],
        )
    missing = [field for field in ["tumor_size_cm", "focality", "tumor_location"] if data.get(field) in (None, "")]
    if missing:
        return result("手术方式方向待补充评估", "保乳/全乳切除方向需结合肿瘤大小、位置、乳房体积、单灶或多灶/多中心信息。", missing)
    focality = data.get("focality")
    size = data.get("tumor_size_cm") or 0
    if focality in {"多中心", "multicentric"}:
        return result("倾向评估全乳切除方向", "多中心病灶通常不利于常规保乳，应结合影像范围和患者意愿评估。")
    if size <= 3 and focality in {"单灶", "unifocal"}:
        return result("可评估保乳手术可行性", "单灶且肿瘤较小，可结合肿瘤/乳房比例、切缘可达性和放疗条件评估保乳。")
    return result("手术方式需个体化评估", "病灶范围或大小提示需要结合影像范围、乳房条件及新辅助降期可能性判断。")
