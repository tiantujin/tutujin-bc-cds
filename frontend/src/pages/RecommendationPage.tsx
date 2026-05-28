import { RefreshCw } from "lucide-react";
import { useState } from "react";
import { ChemoDrug, Recommendation } from "../api";
import { ChemoRegimenCard } from "../components/ChemoRegimenCard";
import { Disclaimer } from "../components/Disclaimer";
import { DrugDetailModal } from "../components/DrugDetailModal";
import { MissingInfo } from "../components/MissingInfo";

const sectionLabels: Record<string, string> = {
  molecular_subtype: "分子分型",
  staging: "临床 TNM 分期",
  neoadjuvant: "新辅助治疗",
  surgery: "手术方式方向",
  axillary_management: "腋窝处理建议",
  adjuvant_treatment: "系统治疗方向",
  risk_flags: "MDT 与风险提醒"
};

type Props = {
  recommendation: Recommendation | null;
  onGenerate: () => void;
  onExport: () => void;
};

export function RecommendationPage({ recommendation, onGenerate, onExport }: Props) {
  const [drug, setDrug] = useState<ChemoDrug | null>(null);
  return (
    <main className="content">
      <div className="page-header">
        <div>
          <h1>推荐结果</h1>
          <p>规则引擎输出，每条建议显示原因与指南版本</p>
        </div>
        <div className="actions">
          <button onClick={onGenerate}><RefreshCw size={18} /> 重新生成</button>
          <button className="primary" onClick={onExport}>导出摘要</button>
        </div>
      </div>
      <Disclaimer />
      {!recommendation && <div className="empty panel">请先保存病例，再生成推荐。</div>}
      {recommendation && (
        <>
          <section>
            <h2>病例摘要</h2>
            <p className="summary">{recommendation.case_summary}</p>
            <MissingInfo items={recommendation.missing_fields} />
            {recommendation.caution_flags.length > 0 && <div className="warning">MDT 提醒：{recommendation.caution_flags.join("、")}</div>}
          </section>
          <section>
            <h2>基因检测解释</h2>
            {recommendation.genomic_interpretations.length ? recommendation.genomic_interpretations.map((item) => (
              <article className="result-item" key={`${item.test_type}-${item.test_id}`}>
                <h3>{item.test_type}</h3>
                <strong>{item.risk_group}｜{item.chemo_benefit_hint}</strong>
                <p>{item.interpretation}</p>
                <footer><span>{item.trigger}</span><span>{item.source}</span><span>{item.limitations}</span></footer>
              </article>
            )) : <div className="warning">HR+/HER2- 等辅助治疗决策场景，可考虑录入基因检测结果辅助判断。</div>}
          </section>
          <section>
            <h2>公开风险模型结果</h2>
            {recommendation.risk_model_results.length ? recommendation.risk_model_results.map((item) => (
              <article className="result-item" key={`${item.model_name}-${item.id}`}>
                <h3>{item.model_name}</h3>
                <strong>{item.score ?? "-"}｜{item.risk_group}</strong>
                <p>{item.interpretation}</p>
                <footer><span>{item.limitations}</span></footer>
              </article>
            )) : <div className="empty">暂无 CTS5、NPI、RCB 或 PREDICT 手动结果。</div>}
          </section>
          <section>
            <h2>化疗/系统治疗方案方向</h2>
            <div className="warning">方案必须由医生修改和确认，剂量仅作为参考，不自动生成处方或医嘱。</div>
            {recommendation.chemo_regimens.length ? recommendation.chemo_regimens.map((item) => (
              <ChemoRegimenCard key={item.id} regimen={item} onDrug={setDrug} />
            )) : <div className="empty">暂无自动关联方案。</div>}
          </section>
          <section className="result-list">
            {Object.entries(recommendation.sections).map(([key, item]) => (
              <article className="result-item" key={key}>
                <div>
                  <h3>{sectionLabels[key] || key}</h3>
                  <strong>{item.recommendation}</strong>
                  <p>{item.rationale}</p>
                </div>
                <footer>
                  <span>{item.evidence_level}</span>
                  <span>{item.guideline_version}</span>
                </footer>
              </article>
            ))}
          </section>
          <DrugDetailModal drug={drug} onClose={() => setDrug(null)} />
        </>
      )}
    </main>
  );
}
