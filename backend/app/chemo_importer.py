from __future__ import annotations

import re
import sqlite3
import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

from app import crud


BASE_DIR = Path(__file__).resolve().parents[1]
DOCX_PATH = Path("/Users/chelseatian/Desktop/化疗药物(2).docx")
SEED_JSON_PATH = BASE_DIR / "data" / "chemo_drugs_seed.json"
UNKNOWN = "unknown"


def _cell_text(cell: ET.Element, ns: dict[str, str]) -> str:
    return "".join(node.text or "" for node in cell.findall(".//w:t", ns)).strip()


def _normalize(value: str | None) -> str:
    value = (value or "").strip()
    return value or UNKNOWN


def _split_dose_variants(row: dict[str, str]) -> list[dict[str, str]]:
    dose = row.get("dose", UNKNOWN)
    if dose == UNKNOWN:
        return [row]
    parts = re.split(r"(?:\n|；|;)(?=.*(?:q3w|qw|d1|d8|D1|D8|每周|三周))", dose)
    variants = [part.strip() for part in parts if part.strip()]
    if len(variants) <= 1:
        return [row]
    rows = []
    for variant in variants:
        copied = dict(row)
        copied["dose"] = variant
        rows.append(copied)
    return rows


def parse_docx(path: Path = DOCX_PATH) -> tuple[list[dict[str, str]], dict[str, int]]:
    if not path.exists():
        return parse_seed_json()
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    table = root.find(".//w:tbl", ns)
    if table is None:
        return [], {}
    rows = table.findall("w:tr", ns)
    parsed: list[dict[str, str]] = []
    last_class = UNKNOWN
    missing_counts = {
        "drug_class": 0,
        "subclass": 0,
        "brand_name": 0,
        "dose": 0,
        "dilution": 0,
        "premedication": 0,
        "adverse_events": 0,
        "mechanism": 0,
    }
    for row in rows[1:]:
        cells = [_cell_text(cell, ns) for cell in row.findall("w:tc", ns)]
        if not any(cells):
            continue
        cells = cells + [""] * (8 - len(cells))
        drug_class = cells[0].strip() or last_class
        last_class = drug_class or last_class
        record = {
            "drug_class": _normalize(drug_class),
            "subclass": _normalize(cells[1]),
            "generic_name": _normalize(cells[1]),
            "brand_name": _normalize(cells[2]),
            "dose": _normalize(cells[3]),
            "dilution": _normalize(cells[4]),
            "premedication": _normalize(cells[5]),
            "adverse_events": _normalize(cells[6]),
            "mechanism": _normalize(cells[7]),
            "notes": "来源：化疗药物(2).docx；剂量为原表参考剂量，未改写。",
        }
        for key in missing_counts:
            if record[key] == UNKNOWN:
                missing_counts[key] += 1
        parsed.extend(_split_dose_variants(record))
    return parsed, missing_counts


def parse_seed_json(path: Path = SEED_JSON_PATH) -> tuple[list[dict[str, str]], dict[str, int]]:
    rows = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    missing_counts = {
        "drug_class": 0,
        "subclass": 0,
        "brand_name": 0,
        "dose": 0,
        "dilution": 0,
        "premedication": 0,
        "adverse_events": 0,
        "mechanism": 0,
    }
    for row in rows:
        for key in missing_counts:
            if row.get(key) in (None, "", UNKNOWN):
                missing_counts[key] += 1
    return rows, missing_counts


def import_chemo_drugs(conn: sqlite3.Connection, path: Path = DOCX_PATH) -> dict[str, Any]:
    rows, missing_counts = parse_docx(path)
    imported = crud.insert_chemo_drugs(conn, rows, replace=True)
    return {
        "source": str(path),
        "imported_rows": imported,
        "total_rows": len(rows),
        "missing_field_counts": missing_counts,
    }
