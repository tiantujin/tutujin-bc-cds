from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.chemo_importer import DOCX_PATH, import_chemo_drugs  # noqa: E402
from app.database import connect, init_db  # noqa: E402


def main():
    init_db()
    with connect() as conn:
        report = import_chemo_drugs(conn, DOCX_PATH)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
