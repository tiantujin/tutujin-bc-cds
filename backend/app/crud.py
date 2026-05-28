from __future__ import annotations

import sqlite3
import json
from typing import Any

from app import schemas


def _dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def _case_payload(conn: sqlite3.Connection, case_id: int) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT c.*, p.name_or_code, p.age, p.menopausal_status, p.family_history, p.comorbidities
        FROM breast_cancer_cases c
        JOIN patients p ON p.id = c.patient_id
        WHERE c.id = ?
        """,
        (case_id,),
    ).fetchone()
    if not row:
        return None
    path = _dict(conn.execute("SELECT * FROM pathology_reports WHERE case_id = ?", (case_id,)).fetchone()) or {}
    img = _dict(conn.execute("SELECT * FROM imaging_reports WHERE case_id = ?", (case_id,)).fetchone()) or {}
    data = dict(row)
    return {
        "id": data["id"],
        "patient_id": data["patient_id"],
        "patient": {
            "name_or_code": data["name_or_code"],
            "age": data["age"],
            "menopausal_status": data["menopausal_status"],
            "family_history": data["family_history"],
            "comorbidities": data["comorbidities"],
        },
        "case": {
            "laterality": data["laterality"],
            "tumor_location": data["tumor_location"],
            "tumor_size_cm": data["tumor_size_cm"],
            "focality": data["focality"],
            "lesion_details": data.get("lesion_details"),
            "clinical_node_status": data["clinical_node_status"],
            "distant_metastasis": data["distant_metastasis"],
            "clinical_t_stage": data.get("clinical_t_stage"),
            "clinical_n_stage": data.get("clinical_n_stage"),
            "clinical_m_stage": data.get("clinical_m_stage"),
            "pdl1_cps": data.get("pdl1_cps"),
            "brca_status": data.get("brca_status"),
            "status": data["status"],
        },
        "pathology": {key: path.get(key) for key in schemas.PathologyBase.model_fields},
        "imaging": {key: img.get(key) for key in schemas.ImagingBase.model_fields},
    }


def list_cases(conn: sqlite3.Connection) -> list[schemas.CaseListItem]:
    rows = conn.execute(
        """
        SELECT c.id, p.name_or_code, p.age, c.laterality, c.tumor_size_cm,
               c.clinical_node_status, c.distant_metastasis, c.updated_at
        FROM breast_cancer_cases c
        JOIN patients p ON p.id = c.patient_id
        ORDER BY c.updated_at DESC
        """
    ).fetchall()
    return [
        schemas.CaseListItem(
            id=row["id"],
            patient_name_or_code=row["name_or_code"],
            age=row["age"],
            laterality=row["laterality"],
            tumor_size_cm=row["tumor_size_cm"],
            clinical_node_status=row["clinical_node_status"],
            distant_metastasis=row["distant_metastasis"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


def get_case(conn: sqlite3.Connection, case_id: int) -> dict[str, Any] | None:
    return _case_payload(conn, case_id)


def create_case(conn: sqlite3.Connection, payload: schemas.CaseCreate) -> dict[str, Any]:
    patient = payload.patient.model_dump()
    case = payload.case.model_dump()
    pathology = payload.pathology.model_dump()
    imaging = payload.imaging.model_dump()
    cur = conn.execute(
        """
        INSERT INTO patients (name_or_code, age, menopausal_status, family_history, comorbidities)
        VALUES (:name_or_code, :age, :menopausal_status, :family_history, :comorbidities)
        """,
        patient,
    )
    patient_id = cur.lastrowid
    cur = conn.execute(
        """
        INSERT INTO breast_cancer_cases
        (patient_id, laterality, tumor_location, tumor_size_cm, focality, lesion_details, clinical_node_status, distant_metastasis,
         clinical_t_stage, clinical_n_stage, clinical_m_stage, pdl1_cps, brca_status, status)
        VALUES (:patient_id, :laterality, :tumor_location, :tumor_size_cm, :focality, :lesion_details, :clinical_node_status, :distant_metastasis,
         :clinical_t_stage, :clinical_n_stage, :clinical_m_stage, :pdl1_cps, :brca_status, :status)
        """,
        {"patient_id": patient_id, **case},
    )
    case_id = cur.lastrowid
    conn.execute(
        """
        INSERT INTO pathology_reports
        (case_id, pathology_type, er_percent, pr_percent, her2, her2_fish, ki67_percent, histologic_grade, lymphovascular_invasion, raw_text)
        VALUES (:case_id, :pathology_type, :er_percent, :pr_percent, :her2, :her2_fish, :ki67_percent, :histologic_grade, :lymphovascular_invasion, :raw_text)
        """,
        {"case_id": case_id, **pathology},
    )
    conn.execute(
        """
        INSERT INTO imaging_reports (case_id, ultrasound_text, mammography_text, mri_text)
        VALUES (:case_id, :ultrasound_text, :mammography_text, :mri_text)
        """,
        {"case_id": case_id, **imaging},
    )
    conn.commit()
    return get_case(conn, case_id)


def update_case(conn: sqlite3.Connection, case_id: int, payload: schemas.CaseUpdate) -> dict[str, Any] | None:
    existing = get_case(conn, case_id)
    if not existing:
        return None
    patient = payload.patient.model_dump()
    case = payload.case.model_dump()
    pathology = payload.pathology.model_dump()
    imaging = payload.imaging.model_dump()
    conn.execute(
        """
        UPDATE patients
        SET name_or_code = :name_or_code, age = :age, menopausal_status = :menopausal_status,
            family_history = :family_history, comorbidities = :comorbidities, updated_at = CURRENT_TIMESTAMP
        WHERE id = :patient_id
        """,
        {"patient_id": existing["patient_id"], **patient},
    )
    conn.execute(
        """
        UPDATE breast_cancer_cases
        SET laterality = :laterality, tumor_location = :tumor_location, tumor_size_cm = :tumor_size_cm,
            focality = :focality, lesion_details = :lesion_details, clinical_node_status = :clinical_node_status,
            distant_metastasis = :distant_metastasis, clinical_t_stage = :clinical_t_stage, clinical_n_stage = :clinical_n_stage,
            clinical_m_stage = :clinical_m_stage, pdl1_cps = :pdl1_cps, brca_status = :brca_status,
            status = :status, updated_at = CURRENT_TIMESTAMP
        WHERE id = :case_id
        """,
        {"case_id": case_id, **case},
    )
    conn.execute(
        """
        UPDATE pathology_reports
        SET pathology_type = :pathology_type, er_percent = :er_percent, pr_percent = :pr_percent,
            her2 = :her2, her2_fish = :her2_fish, ki67_percent = :ki67_percent, histologic_grade = :histologic_grade,
            lymphovascular_invasion = :lymphovascular_invasion, raw_text = :raw_text
        WHERE case_id = :case_id
        """,
        {"case_id": case_id, **pathology},
    )
    conn.execute(
        """
        UPDATE imaging_reports
        SET ultrasound_text = :ultrasound_text, mammography_text = :mammography_text, mri_text = :mri_text
        WHERE case_id = :case_id
        """,
        {"case_id": case_id, **imaging},
    )
    conn.commit()
    return get_case(conn, case_id)


def delete_case(conn: sqlite3.Connection, case_id: int) -> bool:
    existing = get_case(conn, case_id)
    if not existing:
        return False
    conn.execute("DELETE FROM patients WHERE id = ?", (existing["patient_id"],))
    conn.commit()
    return True


def apply_extraction(conn: sqlite3.Connection, case_id: int, extracted: dict[str, Any]) -> dict[str, Any] | None:
    if not get_case(conn, case_id):
        return None
    case_updates = {key: extracted[key] for key in ["tumor_size_cm", "clinical_node_status"] if extracted.get(key) != "unknown"}
    pathology_updates = {
        key: extracted[key]
        for key in [
            "pathology_type",
            "er_percent",
            "pr_percent",
            "her2",
            "her2_fish",
            "ki67_percent",
            "histologic_grade",
            "lymphovascular_invasion",
        ]
        if extracted.get(key) != "unknown"
    }
    if case_updates:
        assignments = ", ".join(f"{key} = :{key}" for key in case_updates)
        conn.execute(f"UPDATE breast_cancer_cases SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = :case_id", {"case_id": case_id, **case_updates})
    if pathology_updates:
        assignments = ", ".join(f"{key} = :{key}" for key in pathology_updates)
        conn.execute(f"UPDATE pathology_reports SET {assignments} WHERE case_id = :case_id", {"case_id": case_id, **pathology_updates})
    conn.commit()
    return get_case(conn, case_id)


def insert_recommendation(conn: sqlite3.Connection, case_id: int, output_json: str, case_summary: str, mdt_summary: str, disclaimer: str):
    conn.execute(
        """
        INSERT INTO recommendations (case_id, output_json, case_summary, mdt_summary, disclaimer)
        VALUES (?, ?, ?, ?, ?)
        """,
        (case_id, output_json, case_summary, mdt_summary, disclaimer),
    )
    conn.commit()


def latest_recommendation_json(conn: sqlite3.Connection, case_id: int) -> str | None:
    row = conn.execute(
        "SELECT output_json FROM recommendations WHERE case_id = ? ORDER BY created_at DESC, id DESC LIMIT 1",
        (case_id,),
    ).fetchone()
    return row["output_json"] if row else None


def list_genomic_tests(conn: sqlite3.Connection, case_id: int) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute("SELECT * FROM genomic_tests WHERE case_id = ? ORDER BY created_at DESC, id DESC", (case_id,)).fetchall()]


def create_genomic_test(conn: sqlite3.Connection, case_id: int, payload: schemas.GenomicTestCreate) -> dict[str, Any] | None:
    if not get_case(conn, case_id):
        return None
    data = payload.model_dump()
    cur = conn.execute(
        """
        INSERT INTO genomic_tests
        (case_id, test_type, test_name, test_date, institution, raw_score, risk_level, recurrence_score,
         report_conclusion, chemo_benefit, endocrine_benefit, extended_endocrine_benefit, notes)
        VALUES (:case_id, :test_type, :test_name, :test_date, :institution, :raw_score, :risk_level, :recurrence_score,
         :report_conclusion, :chemo_benefit, :endocrine_benefit, :extended_endocrine_benefit, :notes)
        """,
        {"case_id": case_id, **data},
    )
    conn.commit()
    return get_genomic_test(conn, cur.lastrowid)


def get_genomic_test(conn: sqlite3.Connection, test_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM genomic_tests WHERE id = ?", (test_id,)).fetchone()
    return dict(row) if row else None


def update_genomic_test(conn: sqlite3.Connection, test_id: int, payload: schemas.GenomicTestCreate) -> dict[str, Any] | None:
    if not get_genomic_test(conn, test_id):
        return None
    data = payload.model_dump()
    conn.execute(
        """
        UPDATE genomic_tests
        SET test_type = :test_type, test_name = :test_name, test_date = :test_date, institution = :institution,
            raw_score = :raw_score, risk_level = :risk_level, recurrence_score = :recurrence_score,
            report_conclusion = :report_conclusion, chemo_benefit = :chemo_benefit,
            endocrine_benefit = :endocrine_benefit, extended_endocrine_benefit = :extended_endocrine_benefit,
            notes = :notes, updated_at = CURRENT_TIMESTAMP
        WHERE id = :test_id
        """,
        {"test_id": test_id, **data},
    )
    conn.commit()
    return get_genomic_test(conn, test_id)


def delete_genomic_test(conn: sqlite3.Connection, test_id: int) -> bool:
    if not get_genomic_test(conn, test_id):
        return False
    conn.execute("DELETE FROM genomic_tests WHERE id = ?", (test_id,))
    conn.commit()
    return True


def list_risk_model_results(conn: sqlite3.Connection, case_id: int) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM risk_model_results WHERE case_id = ? ORDER BY created_at DESC, id DESC", (case_id,)).fetchall()
    results = []
    for row in rows:
        data = dict(row)
        data["input_json"] = json.loads(data["input_json"]) if data.get("input_json") else {}
        results.append(data)
    return results


def insert_risk_model_result(conn: sqlite3.Connection, case_id: int, result: schemas.RiskModelResultRead) -> dict[str, Any] | None:
    if not get_case(conn, case_id):
        return None
    cur = conn.execute(
        """
        INSERT INTO risk_model_results (case_id, model_name, input_json, score, risk_group, interpretation, limitations)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case_id,
            result.model_name,
            json.dumps(result.input_json, ensure_ascii=False),
            result.score,
            result.risk_group,
            result.interpretation,
            result.limitations,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM risk_model_results WHERE id = ?", (cur.lastrowid,)).fetchone()
    data = dict(row)
    data["input_json"] = json.loads(data["input_json"])
    return data


def insert_chemo_drugs(conn: sqlite3.Connection, rows: list[dict[str, Any]], replace: bool = True) -> int:
    if replace:
        conn.execute("DELETE FROM chemo_drugs")
    conn.executemany(
        """
        INSERT INTO chemo_drugs
        (drug_class, subclass, generic_name, brand_name, dose, dilution, premedication, adverse_events, mechanism, notes)
        VALUES (:drug_class, :subclass, :generic_name, :brand_name, :dose, :dilution, :premedication, :adverse_events, :mechanism, :notes)
        """,
        rows,
    )
    conn.commit()
    return len(rows)


def seed_guidelines(conn: sqlite3.Connection):
    if conn.execute("SELECT id FROM guideline_versions LIMIT 1").fetchone():
        return
    conn.executemany(
        "INSERT INTO guideline_versions (name, version, source_file, notes) VALUES (?, ?, ?, ?)",
        [
            (
                "CBCS乳腺癌指南精要版",
                "2026",
                "【Finallized】2026 CBCS指南精要版小红书 1215.pdf",
                "本地上传文件，MVP规则以医生可审阅的结构化要点表达。",
            ),
            ("Breast cancer reference", "local", "breast.pdf", "本地上传文件，后续可逐条补充证据等级和原文定位。"),
        ],
    )
    conn.commit()
