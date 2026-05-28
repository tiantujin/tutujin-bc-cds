from app import genomics


def test_oncotype_interpretation_does_not_calculate_algorithm():
    result = genomics.interpret_genomic_test({"test_type": "Oncotype DX / 21-gene", "recurrence_score": 28, "institution": "外送机构"})
    assert result.risk_group == "高风险"
    assert "不复现商业基因检测内部算法" in result.limitations
    assert "化疗获益可能较大" in result.chemo_benefit_hint


def test_domestic_panel_uses_report_conclusion():
    result = genomics.interpret_genomic_test({"test_type": "72基因", "risk_level": "低危", "report_conclusion": "低复发风险"})
    assert result.risk_group == "低危"
    assert "原报告结论" in result.interpretation
