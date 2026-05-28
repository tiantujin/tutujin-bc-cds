import { Save, Wand2 } from "lucide-react";
import type React from "react";
import { CasePayload } from "../api";
import { Field } from "../components/Field";

type Props = {
  value: CasePayload;
  onChange: (value: CasePayload) => void;
  onSave: () => void;
  onExtract: () => void;
};

function updateSection<T extends keyof CasePayload>(payload: CasePayload, section: T, key: string, value: string) {
  const normalized = value === "" ? null : value;
  const numericFields = ["age", "tumor_size_cm", "er_percent", "pr_percent", "ki67_percent"];
  return {
    ...payload,
    [section]: {
      ...payload[section],
      [key]: numericFields.includes(key) && normalized !== null ? Number(normalized) : normalized
    }
  };
}

export function CaseEditPage({ value, onChange, onSave, onExtract }: Props) {
  const set = (section: keyof CasePayload, key: string) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    onChange(updateSection(value, section, key, event.target.value));
  };

  return (
    <main className="content">
      <div className="page-header">
        <div>
          <h1>新建/编辑病例</h1>
          <p>分区录入，必填项用于生成基础推荐</p>
        </div>
        <div className="actions">
          <button onClick={onExtract}>
            <Wand2 size={18} /> 文本抽取
          </button>
          <button className="primary" onClick={onSave}>
            <Save size={18} /> 保存
          </button>
        </div>
      </div>

      <section>
        <h2>患者基本信息</h2>
        <div className="grid">
          <Field label="姓名/编号" required><input value={value.patient.name_or_code} onChange={set("patient", "name_or_code")} /></Field>
          <Field label="年龄"><input type="number" value={value.patient.age ?? ""} onChange={set("patient", "age")} /></Field>
          <Field label="绝经状态"><select value={value.patient.menopausal_status ?? ""} onChange={set("patient", "menopausal_status")}><option value="">未填写</option><option>未绝经</option><option>已绝经</option><option>围绝经期</option></select></Field>
          <Field label="家族史"><input value={value.patient.family_history ?? ""} onChange={set("patient", "family_history")} /></Field>
          <Field label="合并症"><input value={value.patient.comorbidities ?? ""} onChange={set("patient", "comorbidities")} /></Field>
        </div>
      </section>

      <section>
        <h2>肿瘤信息</h2>
        <div className="grid">
          <Field label="左/右乳"><select value={value.case.laterality ?? ""} onChange={set("case", "laterality")}><option value="">未填写</option><option>左</option><option>右</option><option>双侧</option></select></Field>
          <Field label="肿瘤位置"><input value={value.case.tumor_location ?? ""} onChange={set("case", "tumor_location")} /></Field>
          <Field label="肿瘤大小 cm" required><input type="number" step="0.1" value={value.case.tumor_size_cm ?? ""} onChange={set("case", "tumor_size_cm")} /></Field>
          <Field label="病灶"><select value={value.case.focality ?? ""} onChange={set("case", "focality")}><option value="">未填写</option><option>单灶</option><option>多灶</option><option>多中心</option></select></Field>
          <Field label="临床淋巴结状态" required><select value={value.case.clinical_node_status ?? ""} onChange={set("case", "clinical_node_status")}><option value="">未填写</option><option>阴性</option><option>阳性</option><option>可疑</option><option>cN0</option><option>cN1</option></select></Field>
          <Field label="远处转移" required><select value={value.case.distant_metastasis ?? ""} onChange={set("case", "distant_metastasis")}><option value="">未填写</option><option>无</option><option>有</option><option>待排</option></select></Field>
        </div>
      </section>

      <section>
        <h2>影像报告文字</h2>
        <div className="grid one">
          <Field label="超声"><textarea value={value.imaging.ultrasound_text ?? ""} onChange={set("imaging", "ultrasound_text")} /></Field>
          <Field label="钼靶"><textarea value={value.imaging.mammography_text ?? ""} onChange={set("imaging", "mammography_text")} /></Field>
          <Field label="MRI"><textarea value={value.imaging.mri_text ?? ""} onChange={set("imaging", "mri_text")} /></Field>
        </div>
      </section>

      <section>
        <h2>病理和免疫组化</h2>
        <div className="grid">
          <Field label="病理类型"><input value={value.pathology.pathology_type ?? ""} onChange={set("pathology", "pathology_type")} /></Field>
          <Field label="ER %"><input type="number" value={value.pathology.er_percent ?? ""} onChange={set("pathology", "er_percent")} /></Field>
          <Field label="PR %"><input type="number" value={value.pathology.pr_percent ?? ""} onChange={set("pathology", "pr_percent")} /></Field>
          <Field label="HER2"><select value={value.pathology.her2 ?? ""} onChange={set("pathology", "her2")}><option value="">未填写</option><option>0</option><option>1+</option><option>2+</option><option>3+</option><option>阴性</option><option>阳性</option></select></Field>
          <Field label="Ki-67 %"><input type="number" value={value.pathology.ki67_percent ?? ""} onChange={set("pathology", "ki67_percent")} /></Field>
          <Field label="组织学分级"><select value={value.pathology.histologic_grade ?? ""} onChange={set("pathology", "histologic_grade")}><option value="">未填写</option><option>I级</option><option>II级</option><option>III级</option></select></Field>
          <Field label="脉管癌栓"><select value={value.pathology.lymphovascular_invasion ?? ""} onChange={set("pathology", "lymphovascular_invasion")}><option value="">未填写</option><option>无</option><option>有</option></select></Field>
        </div>
      </section>
    </main>
  );
}
