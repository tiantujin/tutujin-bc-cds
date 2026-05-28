from fastapi.testclient import TestClient

from app.main import app


def test_demo_recommendation_flow():
    with TestClient(app) as client:
        created = client.post("/api/demo/seed")
        assert created.status_code == 200
        case_id = created.json()["id"]
        genomic = client.post(
            f"/api/cases/{case_id}/genomic-tests",
            json={"test_type": "Oncotype DX / 21-gene", "recurrence_score": 28, "institution": "示例机构"},
        )
        assert genomic.status_code == 200
        cts5 = client.post(
            f"/api/cases/{case_id}/risk-models/cts5",
            json={"age": 48, "tumor_size_mm": 26, "histologic_grade": 3, "positive_nodes": 1},
        )
        assert cts5.status_code == 200
        import_report = client.post("/api/admin/import-chemo-drugs")
        assert import_report.status_code == 200
        assert import_report.json()["imported_rows"] >= 40
        recommendation = client.post(f"/api/cases/{case_id}/recommendations")
        assert recommendation.status_code == 200
        body = recommendation.json()
        assert body["case_id"] == case_id
        assert "免责声明" not in body["case_summary"]
        assert "neoadjuvant" in body["sections"]
        assert body["genomic_interpretations"]
        assert body["risk_model_results"]
        assert body["chemo_regimens"]
        export = client.get(f"/api/cases/{case_id}/export")
        assert export.status_code == 200
        assert "不作为自动诊疗、处方或医嘱依据" in export.json()["disclaimer"]
        assert "最终确认" in export.json()["disclaimer"]
