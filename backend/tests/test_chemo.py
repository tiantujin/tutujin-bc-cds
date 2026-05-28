from app import chemo
from app.chemo_importer import parse_docx


def test_docx_import_parser_reads_uploaded_table():
    rows, missing = parse_docx()
    assert len(rows) >= 40
    assert rows[0]["drug_class"] == "蒽环类"
    assert rows[0]["generic_name"] == "表柔比星"
    assert "80-100mg/m2" in rows[0]["dose"]
    assert "mechanism" in missing


def test_regimen_recommendation_for_her2_positive():
    names = chemo.recommend_regimen_names({"her2": "3+", "tumor_size_cm": 2.5, "clinical_node_status": "阴性"}, [])
    assert "TCHP" in names
