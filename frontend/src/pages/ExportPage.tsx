import { Copy } from "lucide-react";
import { Disclaimer } from "../components/Disclaimer";

type Props = {
  exportData: { case_summary: string; mdt_summary: string; disclaimer: string } | null;
};

export function ExportPage({ exportData }: Props) {
  async function copy(text: string) {
    await navigator.clipboard.writeText(text);
  }

  return (
    <main className="content">
      <div className="page-header">
        <div>
          <h1>导出</h1>
          <p>复制病例摘要和 MDT 讨论摘要</p>
        </div>
      </div>
      <Disclaimer />
      {!exportData && <div className="empty panel">暂无可导出的推荐结果。</div>}
      {exportData && (
        <div className="export-grid">
          <section>
            <div className="section-title">
              <h2>病例摘要</h2>
              <button onClick={() => copy(`${exportData.case_summary}\n${exportData.disclaimer}`)}><Copy size={18} /> 复制</button>
            </div>
            <textarea readOnly value={`${exportData.case_summary}\n${exportData.disclaimer}`} />
          </section>
          <section>
            <div className="section-title">
              <h2>MDT 讨论摘要</h2>
              <button onClick={() => copy(`${exportData.mdt_summary}\n${exportData.disclaimer}`)}><Copy size={18} /> 复制</button>
            </div>
            <textarea readOnly value={`${exportData.mdt_summary}\n${exportData.disclaimer}`} />
          </section>
        </div>
      )}
    </main>
  );
}
