import { Calculator, Dna, Save } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { CasePayload, GenomicInterpretation, GenomicTest, RiskModelResult, api } from "../api";
import { Field } from "../components/Field";

type Props = {
  caseId: number | null;
  caseValue: CasePayload;
};

const emptyTest: GenomicTest = {
  test_type: "Oncotype DX / 21-gene",
  test_name: "",
  test_date: "",
  institution: "",
  raw_score: "",
  risk_level: "",
  recurrence_score: null,
  report_conclusion: "",
  chemo_benefit: "不确定",
  endocrine_benefit: "不详",
  extended_endocrine_benefit: "不详",
  notes: ""
};

export function GenomicRiskPage({ caseId, caseValue }: Props) {
  const [tab, setTab] = useState<"genomic" | "models">("genomic");
  const [test, setTest] = useState<GenomicTest>(emptyTest);
  const [tests, setTests] = useState<GenomicTest[]>([]);
  const [interpretation, setInterpretation] = useState<GenomicInterpretation | null>(null);
  const [models, setModels] = useState<RiskModelResult[]>([]);
  const [cts5, setCts5] = useState({ age: caseValue.patient.age || 50, tumor_size_mm: (caseValue.case.tumor_size_cm || 0) * 10, histologic_grade: 2, positive_nodes: 0 });
  const [npi, setNpi] = useState({ tumor_size_cm: caseValue.case.tumor_size_cm || 0, node_stage: 1, histologic_grade: 2 });
  const [rcb, setRcb] = useState({ tumor_bed_max_mm: 0, tumor_bed_second_mm: 0, cellularity_percent: 0, dcis_percent: 0, positive_nodes: 0, largest_nodal_met_mm: 0 });
  const [predict, setPredict] = useState({ risk_group: "", score: "", interpretation: "" });

  async function load() {
    if (!caseId) return;
    setTests(await api.listGenomicTests(caseId));
    setModels(await api.listRiskModelResults(caseId));
  }

  useEffect(() => {
    load();
  }, [caseId]);

  async function saveTest() {
    if (!caseId) return;
    const saved = await api.createGenomicTest(caseId, test);
    setInterpretation(await api.interpretGenomicTest(saved));
    await load();
  }

  async function calculate(kind: "cts5" | "npi" | "rcb" | "predict") {
    if (!caseId) return;
    if (kind === "cts5") await api.calculateCts5(caseId, cts5);
    if (kind === "npi") await api.calculateNpi(caseId, npi);
    if (kind === "rcb") await api.calculateRcb(caseId, rcb);
    if (kind === "predict") await api.savePredictManual(caseId, { input_json: { ...caseValue.case, ...caseValue.pathology }, score: predict.score ? Number(predict.score) : null, risk_group: predict.risk_group, interpretation: predict.interpretation });
    await load();
  }

  const setNumber = <T extends Record<string, number>>(value: T, setter: (v: T) => void, key: keyof T) => (event: React.ChangeEvent<HTMLInputElement>) => setter({ ...value, [key]: Number(event.target.value) });

  return (
    <main className="content">
      <div className="page-header">
        <div>
          <h1>基因检测/风险模型</h1>
          <p>商业检测只解释已出具结果；公开模型透明计算</p>
        </div>
      </div>
      <div className="tabs">
        <button className={tab === "genomic" ? "active" : ""} onClick={() => setTab("genomic")}><Dna size={18} /> 基因检测</button>
        <button className={tab === "models" ? "active" : ""} onClick={() => setTab("models")}><Calculator size={18} /> 公开风险模型</button>
      </div>

      {tab === "genomic" && (
        <>
          <section>
            <h2>检测结果录入</h2>
            <div className="warning">不计算 Oncotype DX、MammaPrint、EndoPredict、Prosigna、BCI 等商业检测内部算法，仅解释检测机构报告结果。</div>
            <div className="grid">
              <Field label="检测类型"><select value={test.test_type} onChange={(e) => setTest({ ...test, test_type: e.target.value })}><option>Oncotype DX / 21-gene</option><option>MammaPrint / 70-gene</option><option>72基因 / 国产多基因</option><option>EndoPredict</option><option>Prosigna / PAM50</option><option>Breast Cancer Index, BCI</option></select></Field>
              <Field label="检测名称"><input value={test.test_name || ""} onChange={(e) => setTest({ ...test, test_name: e.target.value })} /></Field>
              <Field label="检测日期"><input type="date" value={test.test_date || ""} onChange={(e) => setTest({ ...test, test_date: e.target.value })} /></Field>
              <Field label="检测机构"><input value={test.institution || ""} onChange={(e) => setTest({ ...test, institution: e.target.value })} /></Field>
              <Field label="Recurrence Score / ROR / EPclin"><input type="number" value={test.recurrence_score ?? ""} onChange={(e) => setTest({ ...test, recurrence_score: e.target.value ? Number(e.target.value) : null })} /></Field>
              <Field label="风险等级"><select value={test.risk_level || ""} onChange={(e) => setTest({ ...test, risk_level: e.target.value })}><option value="">不详</option><option>低危</option><option>中危</option><option>高危</option><option>Low Risk</option><option>High Risk</option><option>Ultra-low Risk</option></select></Field>
              <Field label="临床风险/淋巴结/远期风险"><input value={test.raw_score || ""} onChange={(e) => setTest({ ...test, raw_score: e.target.value })} /></Field>
              <Field label="化疗获益"><select value={test.chemo_benefit || "不确定"} onChange={(e) => setTest({ ...test, chemo_benefit: e.target.value })}><option>是</option><option>否</option><option>不确定</option></select></Field>
              <Field label="延长内分泌获益"><select value={test.extended_endocrine_benefit || "不详"} onChange={(e) => setTest({ ...test, extended_endocrine_benefit: e.target.value })}><option>是</option><option>否</option><option>不详</option></select></Field>
            </div>
            <div className="grid one">
              <Field label="原报告结论文本"><textarea value={test.report_conclusion || ""} onChange={(e) => setTest({ ...test, report_conclusion: e.target.value })} /></Field>
              <Field label="医生备注"><textarea value={test.notes || ""} onChange={(e) => setTest({ ...test, notes: e.target.value })} /></Field>
            </div>
            <div className="actions"><button className="primary" onClick={saveTest} disabled={!caseId}><Save size={18} /> 保存并解释</button></div>
          </section>
          {interpretation && <section><h2>解释结果</h2><p className="summary">{interpretation.interpretation}</p><div className="warning">{interpretation.limitations}</div></section>}
          <section><h2>已保存检测</h2>{tests.map((item) => <div className="mini-row" key={item.id}><strong>{item.test_type}</strong><span>{item.risk_level || item.recurrence_score || "不详"}</span><span>{item.institution || "-"}</span></div>)} {!tests.length && <div className="empty">暂无记录</div>}</section>
        </>
      )}

      {tab === "models" && (
        <>
          <section>
            <h2>CTS5</h2>
            <div className="grid"><Field label="年龄"><input type="number" value={cts5.age} onChange={setNumber(cts5, setCts5, "age")} /></Field><Field label="肿瘤大小 mm"><input type="number" value={cts5.tumor_size_mm} onChange={setNumber(cts5, setCts5, "tumor_size_mm")} /></Field><Field label="分级"><input type="number" value={cts5.histologic_grade} onChange={setNumber(cts5, setCts5, "histologic_grade")} /></Field><Field label="阳性淋巴结数"><input type="number" value={cts5.positive_nodes} onChange={setNumber(cts5, setCts5, "positive_nodes")} /></Field></div>
            <button onClick={() => calculate("cts5")}><Calculator size={18} /> 计算 CTS5</button>
          </section>
          <section>
            <h2>NPI</h2>
            <div className="grid"><Field label="肿瘤大小 cm"><input type="number" value={npi.tumor_size_cm} onChange={setNumber(npi, setNpi, "tumor_size_cm")} /></Field><Field label="淋巴结分期值"><input type="number" value={npi.node_stage} onChange={setNumber(npi, setNpi, "node_stage")} /></Field><Field label="组织学分级"><input type="number" value={npi.histologic_grade} onChange={setNumber(npi, setNpi, "histologic_grade")} /></Field></div>
            <button onClick={() => calculate("npi")}><Calculator size={18} /> 计算 NPI</button>
          </section>
          <section>
            <h2>RCB</h2>
            <div className="grid">{Object.keys(rcb).map((key) => <Field key={key} label={key}><input type="number" value={rcb[key as keyof typeof rcb]} onChange={setNumber(rcb, setRcb, key as keyof typeof rcb)} /></Field>)}</div>
            <button onClick={() => calculate("rcb")}><Calculator size={18} /> 计算 RCB</button>
          </section>
          <section>
            <h2>PREDICT 手动结果</h2>
            <div className="grid"><Field label="官网结果数值"><input value={predict.score} onChange={(e) => setPredict({ ...predict, score: e.target.value })} /></Field><Field label="风险/获益分层"><input value={predict.risk_group} onChange={(e) => setPredict({ ...predict, risk_group: e.target.value })} /></Field></div>
            <Field label="解释"><textarea value={predict.interpretation} onChange={(e) => setPredict({ ...predict, interpretation: e.target.value })} /></Field>
            <button onClick={() => calculate("predict")}><Save size={18} /> 保存 PREDICT 结果</button>
          </section>
          <section><h2>已保存模型结果</h2>{models.map((item) => <div className="mini-row" key={`${item.model_name}-${item.id}`}><strong>{item.model_name}</strong><span>{item.score ?? "-"}</span><span>{item.risk_group}</span><p>{item.interpretation}</p></div>)} {!models.length && <div className="empty">暂无记录</div>}</section>
        </>
      )}
    </main>
  );
}
