import { ArrowLeft, ClipboardList, Dna, FileText, Home, Stethoscope, Wand2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { CaseListPage } from "./pages/CaseListPage";
import { CaseEditPage } from "./pages/CaseEditPage";
import { ExtractionPage } from "./pages/ExtractionPage";
import { RecommendationPage } from "./pages/RecommendationPage";
import { ExportPage } from "./pages/ExportPage";
import { GenomicRiskPage } from "./pages/GenomicRiskPage";
import { CaseListItem, CasePayload, Recommendation, api } from "./api";

const emptyPayload: CasePayload = {
  patient: { name_or_code: "", age: null, menopausal_status: "", family_history: "", comorbidities: "" },
  case: { laterality: "", tumor_location: "", tumor_size_cm: null, focality: "", clinical_node_status: "", distant_metastasis: "", status: "draft" },
  pathology: { pathology_type: "", er_percent: null, pr_percent: null, her2: "", ki67_percent: null, histologic_grade: "", lymphovascular_invasion: "", raw_text: "" },
  imaging: { ultrasound_text: "", mammography_text: "", mri_text: "" }
};

type Page = "list" | "edit" | "extract" | "genomic" | "recommendation" | "export";

export default function App() {
  const [page, setPage] = useState<Page>("list");
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [caseId, setCaseId] = useState<number | null>(null);
  const [payload, setPayload] = useState<CasePayload>(emptyPayload);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [exportData, setExportData] = useState<{ case_summary: string; mdt_summary: string; disclaimer: string } | null>(null);
  const currentTitle = useMemo(() => cases.find((item) => item.id === caseId)?.patient_name_or_code || payload.patient.name_or_code, [cases, caseId, payload.patient.name_or_code]);

  async function refresh() {
    setCases(await api.listCases());
  }

  useEffect(() => {
    refresh();
  }, []);

  async function openCase(id: number, target: string = "edit") {
    const data = await api.getCase(id);
    setCaseId(id);
    setPayload({ patient: data.patient, case: data.case, pathology: data.pathology || emptyPayload.pathology, imaging: data.imaging || emptyPayload.imaging });
    setRecommendation(null);
    setPage(target as Page);
    if (target === "recommendation") {
      setRecommendation(await api.latestRecommendation(id));
    }
  }

  function newCase() {
    setCaseId(null);
    setPayload(emptyPayload);
    setRecommendation(null);
    setPage("edit");
  }

  async function saveCase() {
    if (!payload.patient.name_or_code.trim()) {
      alert("请填写姓名/编号");
      return null;
    }
    const saved = caseId ? await api.updateCase(caseId, payload) : await api.createCase(payload);
    setCaseId(saved.id);
    await refresh();
    setPage("edit");
    return saved.id;
  }

  async function generateRecommendation() {
    const id = caseId || (await saveCase());
    if (!id) return;
    setRecommendation(await api.recommend(id));
  }

  async function openExport() {
    if (!caseId) return;
    setExportData(await api.exportMdt(caseId));
    setPage("export");
  }

  const nav = [
    { id: "list", label: "病例", icon: Home },
    { id: "edit", label: "录入", icon: Stethoscope },
    { id: "extract", label: "抽取", icon: Wand2 },
    { id: "genomic", label: "基因/模型", icon: Dna },
    { id: "recommendation", label: "推荐", icon: ClipboardList },
    { id: "export", label: "导出", icon: FileText }
  ] as const;

  return (
    <div className="app">
      <aside>
        <div className="brand">
          <span>BC</span>
          <div>
            <strong>乳腺癌 CDS</strong>
            <small>MVP 本地版</small>
          </div>
        </div>
        <nav>
          {nav.map((item) => {
            const Icon = item.icon;
            return (
              <button key={item.id} className={page === item.id ? "active" : ""} onClick={() => setPage(item.id as Page)} disabled={item.id !== "list" && !caseId && item.id !== "edit"}>
                <Icon size={18} /> {item.label}
              </button>
            );
          })}
        </nav>
        {page !== "list" && (
          <button className="back" onClick={() => setPage("list")}>
            <ArrowLeft size={18} /> 返回列表
          </button>
        )}
        <div className="case-chip">{currentTitle || "未选择病例"}</div>
      </aside>
      {page === "list" && <CaseListPage cases={cases} onRefresh={refresh} onNew={newCase} onOpen={openCase} />}
      {page === "edit" && <CaseEditPage value={payload} onChange={setPayload} onSave={saveCase} onExtract={() => setPage("extract")} />}
      {page === "extract" && <ExtractionPage caseId={caseId} onApplied={async () => caseId && openCase(caseId, "edit")} />}
      {page === "genomic" && <GenomicRiskPage caseId={caseId} caseValue={payload} />}
      {page === "recommendation" && <RecommendationPage recommendation={recommendation} onGenerate={generateRecommendation} onExport={openExport} />}
      {page === "export" && <ExportPage exportData={exportData} />}
    </div>
  );
}
