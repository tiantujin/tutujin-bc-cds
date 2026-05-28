from app.rules import neoadjuvant


def test_her2_positive_neoadjuvant():
    result = neoadjuvant.evaluate(
        {
            "tumor_size_cm": 2.1,
            "clinical_node_status": "阴性",
            "distant_metastasis": "无",
            "er_percent": 10,
            "pr_percent": 0,
            "her2": "3+",
        }
    )
    assert "新辅助" in result.recommendation
    assert "抗 HER2" in result.recommendation


def test_missing_fields_blocks_strong_recommendation():
    result = neoadjuvant.evaluate({"tumor_size_cm": None, "clinical_node_status": "阴性"})
    assert result.missing_fields
    assert "暂不" in result.recommendation
