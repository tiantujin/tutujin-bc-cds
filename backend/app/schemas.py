from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


DISCLAIMER = "本系统仅供医生个人参考，不替代临床判断，不作为自动诊疗依据。"
EXTENDED_DISCLAIMER = (
    "本系统仅供医生个人学习、病例整理和临床决策辅助使用，不替代医生判断，不作为自动诊疗、处方或医嘱依据。"
    "化疗方案和剂量需结合患者体表面积、肝肾功能、心功能、血常规、合并症、既往治疗史及本院规范最终确认。"
)


class PatientBase(BaseModel):
    name_or_code: str = Field(..., min_length=1)
    age: Optional[int] = None
    menopausal_status: Optional[str] = None
    family_history: Optional[str] = None
    comorbidities: Optional[str] = None


class PathologyBase(BaseModel):
    pathology_type: Optional[str] = None
    er_percent: Optional[float] = None
    pr_percent: Optional[float] = None
    her2: Optional[str] = None
    her2_fish: Optional[str] = None
    ki67_percent: Optional[float] = None
    histologic_grade: Optional[str] = None
    lymphovascular_invasion: Optional[str] = None
    raw_text: Optional[str] = None


class ImagingBase(BaseModel):
    ultrasound_text: Optional[str] = None
    mammography_text: Optional[str] = None
    mri_text: Optional[str] = None


class CaseBase(BaseModel):
    laterality: Optional[str] = None
    tumor_location: Optional[str] = None
    tumor_size_cm: Optional[float] = None
    focality: Optional[str] = None
    lesion_details: Optional[str] = None
    clinical_node_status: Optional[str] = None
    distant_metastasis: Optional[str] = None
    clinical_t_stage: Optional[str] = None
    clinical_n_stage: Optional[str] = None
    clinical_m_stage: Optional[str] = None
    pdl1_cps: Optional[float] = None
    brca_status: Optional[str] = None
    status: str = "draft"


class CaseCreate(BaseModel):
    patient: PatientBase
    case: CaseBase = Field(default_factory=CaseBase)
    pathology: PathologyBase = Field(default_factory=PathologyBase)
    imaging: ImagingBase = Field(default_factory=ImagingBase)


class CaseUpdate(CaseCreate):
    pass


class CaseRead(BaseModel):
    id: int
    patient_id: int
    patient: PatientBase
    case: CaseBase
    pathology: Optional[PathologyBase] = None
    imaging: Optional[ImagingBase] = None


class CaseListItem(BaseModel):
    id: int
    patient_name_or_code: str
    age: Optional[int] = None
    laterality: Optional[str] = None
    tumor_size_cm: Optional[float] = None
    clinical_node_status: Optional[str] = None
    distant_metastasis: Optional[str] = None
    updated_at: str


class ExtractionRequest(BaseModel):
    text: str


class ExtractionResponse(BaseModel):
    extracted: Dict[str, Any]
    unknown_fields: List[str]


class RuleResult(BaseModel):
    recommendation: str
    rationale: str
    evidence_level: str = "MVP规则/指南要点"
    guideline_version: str = "CBCS 2026 精要版 + breast.pdf 本地参考"
    missing_fields: List[str] = Field(default_factory=list)
    caution_flags: List[str] = Field(default_factory=list)


class RecommendationResponse(BaseModel):
    case_id: int
    disclaimer: str = EXTENDED_DISCLAIMER
    case_summary: str
    mdt_summary: str
    sections: Dict[str, RuleResult]
    missing_fields: List[str]
    caution_flags: List[str]
    genomic_interpretations: List[Dict[str, Any]] = Field(default_factory=list)
    risk_model_results: List[Dict[str, Any]] = Field(default_factory=list)
    chemo_regimens: List[Dict[str, Any]] = Field(default_factory=list)


class ApplyExtractionRequest(BaseModel):
    extracted: Dict[str, Any]


class ExportResponse(BaseModel):
    case_summary: str
    mdt_summary: str
    disclaimer: str = EXTENDED_DISCLAIMER


class GenomicTestBase(BaseModel):
    test_type: str
    test_name: Optional[str] = None
    test_date: Optional[str] = None
    institution: Optional[str] = None
    raw_score: Optional[str] = None
    risk_level: Optional[str] = None
    recurrence_score: Optional[float] = None
    report_conclusion: Optional[str] = None
    chemo_benefit: Optional[str] = None
    endocrine_benefit: Optional[str] = None
    extended_endocrine_benefit: Optional[str] = None
    notes: Optional[str] = None


class GenomicTestCreate(GenomicTestBase):
    pass


class GenomicTestRead(GenomicTestBase):
    id: int
    case_id: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class GenomicInterpretation(BaseModel):
    test_id: Optional[int] = None
    test_type: str
    risk_group: str
    chemo_benefit_hint: str
    interpretation: str
    limitations: str
    trigger: str
    source: str = "检测机构报告结果 + MVP解释规则"


class CTS5Request(BaseModel):
    age: float
    tumor_size_mm: float
    histologic_grade: int
    positive_nodes: int


class NPIRequest(BaseModel):
    tumor_size_cm: float
    node_stage: int
    histologic_grade: int


class RCBRequest(BaseModel):
    tumor_bed_max_mm: float
    tumor_bed_second_mm: float
    cellularity_percent: float
    dcis_percent: float
    positive_nodes: int
    largest_nodal_met_mm: float


class PredictManualRequest(BaseModel):
    input_json: Dict[str, Any]
    score: Optional[float] = None
    risk_group: Optional[str] = None
    interpretation: str
    limitations: Optional[str] = None


class RiskModelResultRead(BaseModel):
    id: Optional[int] = None
    case_id: Optional[int] = None
    model_name: str
    input_json: Dict[str, Any]
    score: Optional[float] = None
    risk_group: str
    interpretation: str
    limitations: str
    created_at: Optional[str] = None


class ChemoDrugRead(BaseModel):
    id: int
    drug_class: Optional[str] = None
    subclass: Optional[str] = None
    generic_name: Optional[str] = None
    brand_name: Optional[str] = None
    dose: Optional[str] = None
    dilution: Optional[str] = None
    premedication: Optional[str] = None
    adverse_events: Optional[str] = None
    mechanism: Optional[str] = None
    notes: Optional[str] = None


class ChemoRegimenRead(BaseModel):
    id: int
    regimen_name: str
    indication: Optional[str] = None
    subtype: Optional[str] = None
    setting: Optional[str] = None
    drugs: Optional[str] = None
    cycle: Optional[str] = None
    dose_summary: Optional[str] = None
    premedication: Optional[str] = None
    dilution: Optional[str] = None
    adverse_events: Optional[str] = None
    mechanism: Optional[str] = None
    caution: Optional[str] = None
    source: Optional[str] = None
    drug_details: List[ChemoDrugRead] = Field(default_factory=list)


class ImportChemoResponse(BaseModel):
    source: str
    imported_rows: int
    total_rows: int
    missing_field_counts: Dict[str, int]
