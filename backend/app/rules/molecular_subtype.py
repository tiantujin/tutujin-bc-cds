from __future__ import annotations

from app.rules.common import RuleResult, is_positive_percent, normalized, result


def evaluate(data: dict) -> RuleResult:
    er = is_positive_percent(data.get("er_percent"))
    pr = is_positive_percent(data.get("pr_percent"))
    her2_text = normalized(data.get("her2"))
    fish_text = normalized(data.get("her2_fish"))
    ki67 = data.get("ki67_percent")
    missing = [field for field in ["er_percent", "pr_percent", "her2"] if data.get(field) in (None, "")]
    if "2+" in her2_text and not fish_text:
        missing.append("her2_fish")
    if missing:
        return result("分子分型暂不能确定", "ER、PR、HER2 是分子分型的核心字段，信息不完整时不输出强分型。", missing)

    her2_positive = "3+" in her2_text or "阳" in her2_text or "positive" in her2_text or ("2+" in her2_text and ("阳" in fish_text or "扩增" in fish_text or "positive" in fish_text))
    her2_negative = "0" in her2_text or "1+" in her2_text or "阴" in her2_text or "negative" in her2_text or ("2+" in her2_text and ("阴" in fish_text or "未扩增" in fish_text or "negative" in fish_text))
    hormone_positive = bool(er or pr)

    if her2_positive:
        subtype = "HER2阳性型"
    elif not hormone_positive and her2_negative:
        subtype = "三阴性乳腺癌（TNBC）"
    elif hormone_positive and her2_negative:
        subtype = "HR+/HER2-"
        if ki67 is not None:
            subtype += "，Ki-67较高" if ki67 >= 20 else "，Ki-67较低"
    else:
        subtype = "分子分型需结合 HER2 FISH/ISH 或补充报告确认"

    return result(subtype, "依据 ER/PR 是否阳性、HER2 状态及 Ki-67 风险信息进行 MVP 分型。")
