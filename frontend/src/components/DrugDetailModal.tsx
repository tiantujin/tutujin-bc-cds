import { X } from "lucide-react";
import { ChemoDrug } from "../api";

type Props = {
  drug: ChemoDrug | null;
  onClose: () => void;
};

export function DrugDetailModal({ drug, onClose }: Props) {
  if (!drug) return null;
  const rows = [
    ["药物种类", drug.drug_class],
    ["亚分类", drug.subclass],
    ["商品名", drug.brand_name],
    ["参考剂量", drug.dose],
    ["配药", drug.dilution],
    ["预处理", drug.premedication],
    ["不良反应", drug.adverse_events],
    ["作用机制", drug.mechanism],
    ["备注", drug.notes]
  ];
  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="section-title">
          <h2>{drug.generic_name || drug.subclass || "药物详情"}</h2>
          <button className="icon" onClick={onClose} title="关闭"><X size={18} /></button>
        </div>
        <div className="detail-list">
          {rows.map(([label, value]) => (
            <div key={label}>
              <strong>{label}</strong>
              <span>{value || "unknown"}</span>
            </div>
          ))}
        </div>
        <div className="warning">药物剂量仅为参考剂量，不自动生成最终医嘱。</div>
      </div>
    </div>
  );
}
