from __future__ import annotations

import sqlite3
import base64
import hashlib
import os
import secrets
from urllib.parse import parse_qs
from typing import List
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import chemo, chemo_importer, crud, genomics, risk_models, schemas
from app.database import connect, get_db, init_db
from app.extraction import extract_report, unknown_fields
from app.recommendation_service import evaluate_case, latest_recommendation


app = FastAPI(title="乳腺癌临床决策支持系统 MVP")
STATIC_DIR = Path(__file__).resolve().parent / "static"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def optional_share_password(request: Request, call_next):
    password = os.environ.get("CDS_SHARE_PASSWORD")
    if not password or request.url.path in {"/api/health", "/login"}:
        return await call_next(request)
    auth = request.headers.get("authorization", "")
    expected = "Basic " + base64.b64encode(f"doctor:{password}".encode("utf-8")).decode("ascii")
    cookie_ok = secrets.compare_digest(request.cookies.get("cds_auth", ""), _share_token(password))
    basic_ok = secrets.compare_digest(auth, expected)
    if not (cookie_ok or basic_ok):
        return _login_page()
    return await call_next(request)


def _share_token(password: str) -> str:
    return hashlib.sha256(f"bc-cds-local-share:{password}".encode("utf-8")).hexdigest()


def _login_page(error: str = "") -> HTMLResponse:
    error_html = f"<p class='error'>{error}</p>" if error else ""
    return HTMLResponse(
        f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>访问验证｜土土金的中二BC小工具</title>
  <style>
    body {{ margin:0; min-height:100vh; display:grid; place-items:center; background:#f5f7fb; color:#1f2933; font-family:"PingFang SC","Microsoft YaHei",system-ui,sans-serif; }}
    main {{ width:min(420px, calc(100vw - 32px)); background:#fff; border:1px solid #d8e0ea; border-radius:10px; padding:24px; box-shadow:0 18px 50px rgba(15,23,42,.12); }}
    h1 {{ margin:0 0 8px; font-size:22px; }}
    p {{ line-height:1.65; color:#475569; }}
    label {{ display:grid; gap:8px; font-weight:700; margin:16px 0; }}
    input {{ min-height:42px; border:1px solid #cbd5e1; border-radius:7px; padding:8px 10px; font:inherit; }}
    button {{ width:100%; min-height:42px; border:0; border-radius:7px; background:#1f7a6d; color:white; font:inherit; cursor:pointer; }}
    .error {{ color:#9f1239; background:#fff1f2; border:1px solid #fecdd3; border-radius:7px; padding:10px 12px; }}
    .hint {{ font-size:13px; }}
  </style>
</head>
<body>
  <main>
    <h1>访问验证</h1>
    <p>请输入分享者提供的访问密码。通过后即可进入“土土金的中二BC小工具”。</p>
    {error_html}
    <form method="post" action="login">
      <label>访问密码<input name="password" type="password" autocomplete="current-password" autofocus></label>
      <button type="submit">进入系统</button>
    </form>
    <p class="hint">请只分享给可信试用者，避免录入真实患者身份信息。</p>
  </main>
</body>
</html>""",
        status_code=401 if error else 200,
    )


@app.on_event("startup")
def startup():
    init_db()
    with connect() as conn:
        crud.seed_guidelines(conn)
        chemo.seed_regimens(conn)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/login")
async def login(request: Request):
    password = os.environ.get("CDS_SHARE_PASSWORD")
    if not password:
        return RedirectResponse(url="./", status_code=303)
    raw = (await request.body()).decode("utf-8")
    submitted = parse_qs(raw).get("password", [""])[0]
    if not secrets.compare_digest(submitted, password):
        return _login_page("密码不正确，请重新输入。")
    response = RedirectResponse(url="./", status_code=303)
    response.set_cookie("cds_auth", _share_token(password), httponly=True, samesite="lax", max_age=60 * 60 * 12)
    return response


@app.get("/")
def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/cds")
def local_app_entry():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/cases", response_model=List[schemas.CaseListItem])
def list_cases(db: sqlite3.Connection = Depends(get_db)):
    return crud.list_cases(db)


@app.post("/api/cases", response_model=schemas.CaseRead)
def create_case(payload: schemas.CaseCreate, db: sqlite3.Connection = Depends(get_db)):
    return crud.create_case(db, payload)


@app.get("/api/cases/{case_id}", response_model=schemas.CaseRead)
def get_case(case_id: int, db: sqlite3.Connection = Depends(get_db)):
    case = crud.get_case(db, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="病例不存在")
    return case


@app.put("/api/cases/{case_id}", response_model=schemas.CaseRead)
def update_case(case_id: int, payload: schemas.CaseUpdate, db: sqlite3.Connection = Depends(get_db)):
    case = crud.update_case(db, case_id, payload)
    if not case:
        raise HTTPException(status_code=404, detail="病例不存在")
    return case


@app.delete("/api/cases/{case_id}")
def delete_case(case_id: int, db: sqlite3.Connection = Depends(get_db)):
    if not crud.delete_case(db, case_id):
        raise HTTPException(status_code=404, detail="病例不存在")
    return {"ok": True}


@app.post("/api/extract", response_model=schemas.ExtractionResponse)
def extract(payload: schemas.ExtractionRequest):
    extracted = extract_report(payload.text)
    return schemas.ExtractionResponse(extracted=extracted, unknown_fields=unknown_fields(extracted))


@app.post("/api/cases/{case_id}/apply-extraction", response_model=schemas.CaseRead)
def apply_extraction(case_id: int, payload: schemas.ApplyExtractionRequest, db: sqlite3.Connection = Depends(get_db)):
    case = crud.apply_extraction(db, case_id, payload.extracted)
    if not case:
        raise HTTPException(status_code=404, detail="病例不存在")
    return case


@app.post("/api/cases/{case_id}/recommendations", response_model=schemas.RecommendationResponse)
def create_recommendation(case_id: int, db: sqlite3.Connection = Depends(get_db)):
    recommendation = evaluate_case(db, case_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="病例不存在")
    return recommendation


@app.get("/api/cases/{case_id}/recommendations/latest", response_model=schemas.RecommendationResponse)
def get_latest_recommendation(case_id: int, db: sqlite3.Connection = Depends(get_db)):
    recommendation = latest_recommendation(db, case_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="病例不存在")
    return recommendation


@app.get("/api/cases/{case_id}/export", response_model=schemas.ExportResponse)
def export_case(case_id: int, db: sqlite3.Connection = Depends(get_db)):
    recommendation = latest_recommendation(db, case_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="病例不存在")
    return schemas.ExportResponse(case_summary=recommendation.case_summary, mdt_summary=recommendation.mdt_summary)


@app.get("/api/cases/{case_id}/export/mdt", response_model=schemas.ExportResponse)
def export_mdt_case(case_id: int, db: sqlite3.Connection = Depends(get_db)):
    recommendation = evaluate_case(db, case_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="病例不存在")
    return schemas.ExportResponse(case_summary=recommendation.case_summary, mdt_summary=recommendation.mdt_summary)


@app.get("/api/cases/{case_id}/genomic-tests", response_model=List[schemas.GenomicTestRead])
def list_genomic_tests(case_id: int, db: sqlite3.Connection = Depends(get_db)):
    if not crud.get_case(db, case_id):
        raise HTTPException(status_code=404, detail="病例不存在")
    return crud.list_genomic_tests(db, case_id)


@app.post("/api/cases/{case_id}/genomic-tests", response_model=schemas.GenomicTestRead)
def create_genomic_test(case_id: int, payload: schemas.GenomicTestCreate, db: sqlite3.Connection = Depends(get_db)):
    test = crud.create_genomic_test(db, case_id, payload)
    if not test:
        raise HTTPException(status_code=404, detail="病例不存在")
    return test


@app.put("/api/genomic-tests/{test_id}", response_model=schemas.GenomicTestRead)
def update_genomic_test(test_id: int, payload: schemas.GenomicTestCreate, db: sqlite3.Connection = Depends(get_db)):
    test = crud.update_genomic_test(db, test_id, payload)
    if not test:
        raise HTTPException(status_code=404, detail="基因检测记录不存在")
    return test


@app.delete("/api/genomic-tests/{test_id}")
def delete_genomic_test(test_id: int, db: sqlite3.Connection = Depends(get_db)):
    if not crud.delete_genomic_test(db, test_id):
        raise HTTPException(status_code=404, detail="基因检测记录不存在")
    return {"ok": True}


@app.post("/api/genomic-tests/interpret", response_model=schemas.GenomicInterpretation)
def interpret_genomic_test(payload: schemas.GenomicTestCreate):
    return genomics.interpret_genomic_test(payload.model_dump())


@app.get("/api/cases/{case_id}/risk-model-results", response_model=List[schemas.RiskModelResultRead])
def list_risk_model_results(case_id: int, db: sqlite3.Connection = Depends(get_db)):
    if not crud.get_case(db, case_id):
        raise HTTPException(status_code=404, detail="病例不存在")
    return crud.list_risk_model_results(db, case_id)


@app.post("/api/cases/{case_id}/risk-models/cts5", response_model=schemas.RiskModelResultRead)
def create_cts5(case_id: int, payload: schemas.CTS5Request, db: sqlite3.Connection = Depends(get_db)):
    result = crud.insert_risk_model_result(db, case_id, risk_models.calculate_cts5(payload))
    if not result:
        raise HTTPException(status_code=404, detail="病例不存在")
    return result


@app.post("/api/cases/{case_id}/risk-models/npi", response_model=schemas.RiskModelResultRead)
def create_npi(case_id: int, payload: schemas.NPIRequest, db: sqlite3.Connection = Depends(get_db)):
    result = crud.insert_risk_model_result(db, case_id, risk_models.calculate_npi(payload))
    if not result:
        raise HTTPException(status_code=404, detail="病例不存在")
    return result


@app.post("/api/cases/{case_id}/risk-models/rcb", response_model=schemas.RiskModelResultRead)
def create_rcb(case_id: int, payload: schemas.RCBRequest, db: sqlite3.Connection = Depends(get_db)):
    result = crud.insert_risk_model_result(db, case_id, risk_models.calculate_rcb(payload))
    if not result:
        raise HTTPException(status_code=404, detail="病例不存在")
    return result


@app.post("/api/cases/{case_id}/risk-models/predict-manual", response_model=schemas.RiskModelResultRead)
def create_predict_manual(case_id: int, payload: schemas.PredictManualRequest, db: sqlite3.Connection = Depends(get_db)):
    result = crud.insert_risk_model_result(db, case_id, risk_models.predict_manual(payload))
    if not result:
        raise HTTPException(status_code=404, detail="病例不存在")
    return result


@app.get("/api/chemo/drugs", response_model=List[schemas.ChemoDrugRead])
def list_chemo_drugs(db: sqlite3.Connection = Depends(get_db)):
    return chemo.list_drugs(db)


@app.get("/api/chemo/drugs/{drug_id}", response_model=schemas.ChemoDrugRead)
def get_chemo_drug(drug_id: int, db: sqlite3.Connection = Depends(get_db)):
    drug = chemo.get_drug(db, drug_id)
    if not drug:
        raise HTTPException(status_code=404, detail="药物不存在")
    return drug


@app.get("/api/chemo/regimens", response_model=List[schemas.ChemoRegimenRead])
def list_chemo_regimens(db: sqlite3.Connection = Depends(get_db)):
    chemo.seed_regimens(db)
    return chemo.list_regimens(db)


@app.get("/api/chemo/regimens/{regimen_id}", response_model=schemas.ChemoRegimenRead)
def get_chemo_regimen(regimen_id: int, db: sqlite3.Connection = Depends(get_db)):
    regimen = chemo.get_regimen(db, regimen_id)
    if not regimen:
        raise HTTPException(status_code=404, detail="方案不存在")
    return regimen


@app.post("/api/admin/seed-chemo-regimens")
def seed_chemo_regimens(db: sqlite3.Connection = Depends(get_db)):
    return {"inserted": chemo.seed_regimens(db)}


@app.post("/api/admin/import-chemo-drugs", response_model=schemas.ImportChemoResponse)
def import_chemo_drugs(db: sqlite3.Connection = Depends(get_db)):
    return chemo_importer.import_chemo_drugs(db)


app.mount("/app", StaticFiles(directory=STATIC_DIR, html=True), name="local_app")


@app.get("/api/guidelines")
def guidelines(db: sqlite3.Connection = Depends(get_db)):
    return [dict(row) for row in db.execute("SELECT * FROM guideline_versions ORDER BY id").fetchall()]


@app.post("/api/demo/seed", response_model=schemas.CaseRead)
def seed_demo_case(db: sqlite3.Connection = Depends(get_db)):
    payload = schemas.CaseCreate(
        patient=schemas.PatientBase(
            name_or_code="DEMO-001",
            age=48,
            menopausal_status="未绝经",
            family_history="无明确乳腺癌家族史",
            comorbidities="无特殊",
        ),
        case=schemas.CaseBase(
            laterality="左",
            tumor_location="外上象限",
            tumor_size_cm=2.6,
            focality="单灶",
            clinical_node_status="阳性",
            distant_metastasis="无",
        ),
        pathology=schemas.PathologyBase(
            pathology_type="浸润性导管癌",
            er_percent=0,
            pr_percent=0,
            her2="阴性",
            ki67_percent=60,
            histologic_grade="III级",
            lymphovascular_invasion="无",
        ),
        imaging=schemas.ImagingBase(
            ultrasound_text="左乳外上象限低回声结节约2.6cm，腋窝淋巴结可疑。",
            mammography_text="左乳肿块影。",
            mri_text="未提供。",
        ),
    )
    return crud.create_case(db, payload)
