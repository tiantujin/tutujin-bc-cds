from __future__ import annotations

import sqlite3
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("CDS_DATA_DIR", BASE_DIR / "data"))
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "breast_cancer_cds.db"


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_or_code TEXT NOT NULL,
                age INTEGER,
                menopausal_status TEXT,
                family_history TEXT,
                comorbidities TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS breast_cancer_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                laterality TEXT,
                tumor_location TEXT,
                tumor_size_cm REAL,
                focality TEXT,
                clinical_node_status TEXT,
                distant_metastasis TEXT,
                status TEXT DEFAULT 'draft',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(patient_id) REFERENCES patients(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS pathology_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL UNIQUE,
                pathology_type TEXT,
                er_percent REAL,
                pr_percent REAL,
                her2 TEXT,
                ki67_percent REAL,
                histologic_grade TEXT,
                lymphovascular_invasion TEXT,
                raw_text TEXT,
                FOREIGN KEY(case_id) REFERENCES breast_cancer_cases(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS imaging_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL UNIQUE,
                ultrasound_text TEXT,
                mammography_text TEXT,
                mri_text TEXT,
                FOREIGN KEY(case_id) REFERENCES breast_cancer_cases(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                output_json TEXT NOT NULL,
                case_summary TEXT NOT NULL,
                mdt_summary TEXT NOT NULL,
                disclaimer TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(case_id) REFERENCES breast_cancer_cases(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS guideline_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                source_file TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS genomic_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                test_type TEXT NOT NULL,
                test_name TEXT,
                test_date TEXT,
                institution TEXT,
                raw_score TEXT,
                risk_level TEXT,
                recurrence_score REAL,
                report_conclusion TEXT,
                chemo_benefit TEXT,
                endocrine_benefit TEXT,
                extended_endocrine_benefit TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(case_id) REFERENCES breast_cancer_cases(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS risk_model_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                model_name TEXT NOT NULL,
                input_json TEXT NOT NULL,
                score REAL,
                risk_group TEXT,
                interpretation TEXT,
                limitations TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(case_id) REFERENCES breast_cancer_cases(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS chemotherapy_regimens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                regimen_name TEXT NOT NULL,
                indication TEXT,
                subtype TEXT,
                setting TEXT,
                drugs TEXT,
                cycle TEXT,
                dose_summary TEXT,
                premedication TEXT,
                dilution TEXT,
                adverse_events TEXT,
                mechanism TEXT,
                caution TEXT,
                source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chemo_drugs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_class TEXT,
                subclass TEXT,
                generic_name TEXT,
                brand_name TEXT,
                dose TEXT,
                dilution TEXT,
                premedication TEXT,
                adverse_events TEXT,
                mechanism TEXT,
                notes TEXT
            );
            """
        )
        _ensure_column(conn, "breast_cancer_cases", "lesion_details", "TEXT")
        _ensure_column(conn, "breast_cancer_cases", "clinical_t_stage", "TEXT")
        _ensure_column(conn, "breast_cancer_cases", "clinical_n_stage", "TEXT")
        _ensure_column(conn, "breast_cancer_cases", "clinical_m_stage", "TEXT")
        _ensure_column(conn, "breast_cancer_cases", "pdl1_cps", "REAL")
        _ensure_column(conn, "breast_cancer_cases", "brca_status", "TEXT")
        _ensure_column(conn, "pathology_reports", "her2_fish", "TEXT")
        conn.commit()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str):
    existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
