import { CheckCircle2 } from "lucide-react";
import { ChemoDrug, ChemoRegimen } from "../api";

type Props = {
  regimen: ChemoRegimen;
  onDrug: (drug: ChemoDrug) => void;
};

export function ChemoRegimenCard({ regimen, onDrug }: Props) {
  return (
    <article className="result-item regimen-card">
      <div className="section-title">
        <h3>{regimen.regimen_name}</h3>
        <button title="医生确认剂量"><CheckCircle2 size={18} /> 医生确认剂量</button>
      </div>
      <strong>{regimen.indication}</strong>
      <p>药物组成：{regimen.drugs}</p>
      <p>周期：{regimen.cycle}</p>
      <p>剂量摘要：{regimen.dose_summary}</p>
      <p>配药：{regimen.dilution}</p>
      <p>预处理：{regimen.premedication}</p>
      <p>常见不良反应：{regimen.adverse_events}</p>
      <p>重点注意事项：{regimen.caution}</p>
      {regimen.drug_details.length > 0 && (
        <div className="drug-chips">
          {regimen.drug_details.map((drug) => (
            <button key={drug.id} onClick={() => onDrug(drug)}>{drug.generic_name || drug.subclass}</button>
          ))}
        </div>
      )}
    </article>
  );
}
