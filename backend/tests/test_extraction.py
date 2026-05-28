from app.extraction import extract_report


def test_extract_cn_report():
    text = "病理诊断：浸润性导管癌。ER 80%，PR: 30%，HER2 3+，Ki-67 45%。肿块大小 2.5cm。淋巴结见转移。"
    result = extract_report(text)
    assert result["er_percent"] == 80
    assert result["pr_percent"] == 30
    assert result["her2"] == "3+"
    assert result["ki67_percent"] == 45
    assert result["tumor_size_cm"] == 2.5
    assert result["clinical_node_status"] == "阳性"
    assert result["pathology_type"] == "浸润性导管癌"


def test_extract_common_ihc_parentheses_and_fish():
    text = "免疫组化：ER（阳性，90%），PR（阳性 70%），HER-2（2+），Ki67约35%。FISH检测：HER2基因未扩增。腋窝淋巴结未见转移。"
    result = extract_report(text)
    assert result["er_percent"] == 90
    assert result["pr_percent"] == 70
    assert result["her2"] == "2+"
    assert result["her2_fish"] == "阴性"
    assert result["ki67_percent"] == 35
    assert result["clinical_node_status"] == "阴性"
