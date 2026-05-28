import { ClipboardCheck, Wand2 } from "lucide-react";
import { useState } from "react";
import { api } from "../api";

type Props = {
  caseId: number | null;
  onApplied: () => void;
};

const labels: Record<string, string> = {
  er_percent: "ER %",
  pr_percent: "PR %",
  her2: "HER2",
  ki67_percent: "Ki-67 %",
  tumor_size_cm: "肿瘤大小 cm",
  clinical_node_status: "临床淋巴结状态",
  pathology_type: "病理类型",
  histologic_grade: "组织学分级",
  lymphovascular_invasion: "脉管癌栓"
};

export function ExtractionPage({ caseId, onApplied }: Props) {
  const [text, setText] = useState("");
  const [extracted, setExtracted] = useState<Record<string, string | number>>({});
  const [unknown, setUnknown] = useState<string[]>([]);

  async function runExtract() {
    const result = await api.extract(text);
    setExtracted(result.extracted);
    setUnknown(result.unknown_fields);
  }

  async function apply() {
    if (!caseId) return;
    await api.applyExtraction(caseId, extracted);
    onApplied();
  }

  return (
    <main className="content">
      <div className="page-header">
        <div>
          <h1>报告文本粘贴</h1>
          <p>基础版使用正则抽取，医生确认后写入病例</p>
        </div>
        <div className="actions">
          <button onClick={runExtract}><Wand2 size={18} /> 自动抽取</button>
          <button className="primary" disabled={!caseId || !Object.keys(extracted).length} onClick={apply}>
            <ClipboardCheck size={18} /> 确认写入
          </button>
        </div>
      </div>
      <section>
        <textarea className="paste-box" value={text} onChange={(event) => setText(event.target.value)} placeholder="粘贴中文病历、检查或病理报告文本..." />
      </section>
      <section>
        <h2>自动抽取结果</h2>
        {unknown.length > 0 && <div className="warning">未识别字段：{unknown.map((key) => labels[key] || key).join("、")}</div>}
        <div className="extract-grid">
          {Object.entries(labels).map(([key, label]) => (
            <label className="field" key={key}>
              <span>{label}</span>
              <input
                value={extracted[key] ?? ""}
                onChange={(event) => setExtracted({ ...extracted, [key]: event.target.value })}
                placeholder="unknown"
              />
            </label>
          ))}
        </div>
      </section>
    </main>
  );
}
