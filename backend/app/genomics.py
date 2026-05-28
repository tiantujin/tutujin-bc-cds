from __future__ import annotations

from typing import Any

from app import schemas


COMMERCIAL_LIMITATION = "本系统不复现商业基因检测内部算法，仅解释医生录入的检测机构报告结果。"


def _text(value: Any, default: str = "不详") -> str:
    if value is None or value == "":
        return default
    return str(value)


def _oncotype(test: dict[str, Any]) -> schemas.GenomicInterpretation:
    rs = test.get("recurrence_score")
    if rs is None:
        risk = "无法判断"
        chemo = "未录入 RS，不能判断化疗获益提示"
    elif rs < 18:
        risk = "低风险"
        chemo = "通常不提示明确化疗获益，但需结合年龄、绝经状态和淋巴结状态"
    elif rs <= 25:
        risk = "中间风险"
        chemo = "化疗获益需结合年龄、绝经状态、淋巴结状态综合判断"
    else:
        risk = "高风险"
        chemo = "提示化疗获益可能较大，需结合临床病理因素确认"
    interpretation = (
        f"Oncotype DX/21基因 Recurrence Score：{_text(rs)}。风险分层：{risk}。"
        f"{chemo}。淋巴结状态：{_text(test.get('raw_score'))}；检测机构：{_text(test.get('institution'))}。"
    )
    return schemas.GenomicInterpretation(
        test_id=test.get("id"),
        test_type=test.get("test_type", "Oncotype DX"),
        risk_group=risk,
        chemo_benefit_hint=chemo,
        interpretation=interpretation,
        limitations=COMMERCIAL_LIMITATION,
        trigger="医生录入 Recurrence Score 结果",
    )


def _mammaprint(test: dict[str, Any]) -> schemas.GenomicInterpretation:
    risk = _text(test.get("risk_level"), "未知")
    clinical_risk = _text(test.get("raw_score"), "未知")
    consistent = "无法判断"
    if risk.lower() in {"low risk", "ultra-low risk", "低危", "超低危"} and clinical_risk.lower() in {"low", "低", "low risk"}:
        consistent = "与临床低风险一致"
    elif risk.lower() in {"high risk", "高危"} and clinical_risk.lower() in {"high", "高", "high risk"}:
        consistent = "与临床高风险一致"
    elif risk != "未知" and clinical_risk != "未知":
        consistent = "与临床风险不完全一致，建议 MDT 讨论"
    chemo = "辅助化疗倾向需结合临床风险"
    if risk.lower() in {"high risk", "高危"}:
        chemo = "基因结果提示可考虑辅助化疗倾向"
    elif risk.lower() in {"low risk", "ultra-low risk", "低危", "超低危"}:
        chemo = "基因结果支持谨慎评估减少化疗"
    return schemas.GenomicInterpretation(
        test_id=test.get("id"),
        test_type=test.get("test_type", "MammaPrint"),
        risk_group=risk,
        chemo_benefit_hint=chemo,
        interpretation=f"MammaPrint/70基因结果：{risk}；临床风险：{clinical_risk}；{consistent}。{chemo}。",
        limitations=COMMERCIAL_LIMITATION,
        trigger="医生录入 MammaPrint 风险结果",
    )


def _domestic_panel(test: dict[str, Any]) -> schemas.GenomicInterpretation:
    risk = _text(test.get("risk_level"), "无法判断")
    chemo = _text(test.get("chemo_benefit"), "不确定")
    if risk in {"低危", "低风险"}:
        hint = "原报告倾向支持减少化疗或谨慎评估化疗必要性"
    elif risk in {"高危", "高风险"} or chemo == "是":
        hint = "原报告提示可考虑化疗或化疗获益"
    elif risk in {"中危", "中风险"}:
        hint = "原报告提示中间风险，建议结合临床病理因素或 MDT"
    else:
        hint = "原报告不足以形成明确化疗倾向"
    return schemas.GenomicInterpretation(
        test_id=test.get("id"),
        test_type=test.get("test_type", "其他多基因检测"),
        risk_group=risk,
        chemo_benefit_hint=hint,
        interpretation=f"{_text(test.get('test_name'), '多基因检测')}：{risk}；化疗获益提示：{chemo}。原报告结论：{_text(test.get('report_conclusion'))}。{hint}。",
        limitations=COMMERCIAL_LIMITATION,
        trigger="医生录入国产/其他多基因检测报告结论",
    )


def _generic(test: dict[str, Any]) -> schemas.GenomicInterpretation:
    test_type = _text(test.get("test_type"), "基因检测")
    risk = _text(test.get("risk_level"), "无法判断")
    chemo = _text(test.get("chemo_benefit"), "不确定")
    extended = _text(test.get("extended_endocrine_benefit"), "不详")
    extra = ""
    if "BCI" in test_type.upper() or "BREAST CANCER INDEX" in test_type.upper():
        extra = f"延长内分泌治疗获益提示：{extended}。"
    return schemas.GenomicInterpretation(
        test_id=test.get("id"),
        test_type=test_type,
        risk_group=risk,
        chemo_benefit_hint=chemo,
        interpretation=f"{test_type} 结果：{risk}；评分/风险：{_text(test.get('raw_score'))}；10年/远期风险：{_text(test.get('report_conclusion'))}。{extra}",
        limitations=COMMERCIAL_LIMITATION,
        trigger="医生录入检测机构报告结果",
    )


def interpret_genomic_test(test: dict[str, Any]) -> schemas.GenomicInterpretation:
    test_type = (test.get("test_type") or "").lower()
    if "oncotype" in test_type or "21" in test_type:
        return _oncotype(test)
    if "mammaprint" in test_type or "70" in test_type:
        return _mammaprint(test)
    if "72" in test_type or "国产" in test_type or "其他" in test_type:
        return _domestic_panel(test)
    return _generic(test)


def interpret_many(tests: list[dict[str, Any]]) -> list[schemas.GenomicInterpretation]:
    return [interpret_genomic_test(test) for test in tests]
