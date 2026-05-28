export const API_BASE = "http://127.0.0.1:8000/api";

export type Patient = {
  name_or_code: string;
  age?: number | null;
  menopausal_status?: string | null;
  family_history?: string | null;
  comorbidities?: string | null;
};

export type CaseCore = {
  laterality?: string | null;
  tumor_location?: string | null;
  tumor_size_cm?: number | null;
  focality?: string | null;
  clinical_node_status?: string | null;
  distant_metastasis?: string | null;
  status?: string;
};

export type Pathology = {
  pathology_type?: string | null;
  er_percent?: number | null;
  pr_percent?: number | null;
  her2?: string | null;
  ki67_percent?: number | null;
  histologic_grade?: string | null;
  lymphovascular_invasion?: string | null;
  raw_text?: string | null;
};

export type Imaging = {
  ultrasound_text?: string | null;
  mammography_text?: string | null;
  mri_text?: string | null;
};

export type CasePayload = {
  patient: Patient;
  case: CaseCore;
  pathology: Pathology;
  imaging: Imaging;
};

export type CaseRead = CasePayload & {
  id: number;
  patient_id: number;
};

export type CaseListItem = {
  id: number;
  patient_name_or_code: string;
  age?: number | null;
  laterality?: string | null;
  tumor_size_cm?: number | null;
  clinical_node_status?: string | null;
  distant_metastasis?: string | null;
  updated_at: string;
};

export type RuleResult = {
  recommendation: string;
  rationale: string;
  evidence_level: string;
  guideline_version: string;
  missing_fields: string[];
  caution_flags: string[];
};

export type Recommendation = {
  case_id: number;
  disclaimer: string;
  case_summary: string;
  mdt_summary: string;
  sections: Record<string, RuleResult>;
  missing_fields: string[];
  caution_flags: string[];
  genomic_interpretations: GenomicInterpretation[];
  risk_model_results: RiskModelResult[];
  chemo_regimens: ChemoRegimen[];
};

export type GenomicTest = {
  id?: number;
  case_id?: number;
  test_type: string;
  test_name?: string | null;
  test_date?: string | null;
  institution?: string | null;
  raw_score?: string | null;
  risk_level?: string | null;
  recurrence_score?: number | null;
  report_conclusion?: string | null;
  chemo_benefit?: string | null;
  endocrine_benefit?: string | null;
  extended_endocrine_benefit?: string | null;
  notes?: string | null;
};

export type GenomicInterpretation = {
  test_id?: number | null;
  test_type: string;
  risk_group: string;
  chemo_benefit_hint: string;
  interpretation: string;
  limitations: string;
  trigger: string;
  source: string;
};

export type RiskModelResult = {
  id?: number;
  case_id?: number;
  model_name: string;
  input_json: Record<string, unknown>;
  score?: number | null;
  risk_group: string;
  interpretation: string;
  limitations: string;
  created_at?: string;
};

export type ChemoDrug = {
  id: number;
  drug_class?: string | null;
  subclass?: string | null;
  generic_name?: string | null;
  brand_name?: string | null;
  dose?: string | null;
  dilution?: string | null;
  premedication?: string | null;
  adverse_events?: string | null;
  mechanism?: string | null;
  notes?: string | null;
};

export type ChemoRegimen = {
  id: number;
  regimen_name: string;
  indication?: string | null;
  subtype?: string | null;
  setting?: string | null;
  drugs?: string | null;
  cycle?: string | null;
  dose_summary?: string | null;
  premedication?: string | null;
  dilution?: string | null;
  adverse_events?: string | null;
  mechanism?: string | null;
  caution?: string | null;
  source?: string | null;
  drug_details: ChemoDrug[];
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json();
}

export const api = {
  listCases: () => request<CaseListItem[]>("/cases"),
  getCase: (id: number) => request<CaseRead>(`/cases/${id}`),
  createCase: (payload: CasePayload) => request<CaseRead>("/cases", { method: "POST", body: JSON.stringify(payload) }),
  updateCase: (id: number, payload: CasePayload) => request<CaseRead>(`/cases/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteCase: (id: number) => request<{ ok: boolean }>(`/cases/${id}`, { method: "DELETE" }),
  extract: (text: string) => request<{ extracted: Record<string, string | number>; unknown_fields: string[] }>("/extract", { method: "POST", body: JSON.stringify({ text }) }),
  applyExtraction: (id: number, extracted: Record<string, string | number>) => request<CaseRead>(`/cases/${id}/apply-extraction`, { method: "POST", body: JSON.stringify({ extracted }) }),
  recommend: (id: number) => request<Recommendation>(`/cases/${id}/recommendations`, { method: "POST" }),
  latestRecommendation: (id: number) => request<Recommendation>(`/cases/${id}/recommendations/latest`),
  exportCase: (id: number) => request<{ case_summary: string; mdt_summary: string; disclaimer: string }>(`/cases/${id}/export`),
  exportMdt: (id: number) => request<{ case_summary: string; mdt_summary: string; disclaimer: string }>(`/cases/${id}/export/mdt`),
  listGenomicTests: (id: number) => request<GenomicTest[]>(`/cases/${id}/genomic-tests`),
  createGenomicTest: (id: number, payload: GenomicTest) => request<GenomicTest>(`/cases/${id}/genomic-tests`, { method: "POST", body: JSON.stringify(payload) }),
  interpretGenomicTest: (payload: GenomicTest) => request<GenomicInterpretation>("/genomic-tests/interpret", { method: "POST", body: JSON.stringify(payload) }),
  listRiskModelResults: (id: number) => request<RiskModelResult[]>(`/cases/${id}/risk-model-results`),
  calculateCts5: (id: number, payload: Record<string, number>) => request<RiskModelResult>(`/cases/${id}/risk-models/cts5`, { method: "POST", body: JSON.stringify(payload) }),
  calculateNpi: (id: number, payload: Record<string, number>) => request<RiskModelResult>(`/cases/${id}/risk-models/npi`, { method: "POST", body: JSON.stringify(payload) }),
  calculateRcb: (id: number, payload: Record<string, number>) => request<RiskModelResult>(`/cases/${id}/risk-models/rcb`, { method: "POST", body: JSON.stringify(payload) }),
  savePredictManual: (id: number, payload: { input_json: Record<string, unknown>; score?: number | null; risk_group?: string | null; interpretation: string; limitations?: string | null }) =>
    request<RiskModelResult>(`/cases/${id}/risk-models/predict-manual`, { method: "POST", body: JSON.stringify(payload) }),
  listChemoRegimens: () => request<ChemoRegimen[]>("/chemo/regimens"),
  importChemoDrugs: () => request<{ imported_rows: number; total_rows: number; source: string; missing_field_counts: Record<string, number> }>("/admin/import-chemo-drugs", { method: "POST" }),
  seedDemo: () => request<CaseRead>("/demo/seed", { method: "POST" })
};
