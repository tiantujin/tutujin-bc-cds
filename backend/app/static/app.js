const API = "/api";
const state = {
  view: "edit",
  cases: [],
  caseId: null,
  current: emptyCase(),
  recommendation: null,
  exportData: null,
};

const $ = (id) => document.getElementById(id);
const view = $("view");
const actions = $("actions");

async function api(path, options = {}) {
  const res = await fetch(API + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function setView(name) {
  state.view = name;
  document.querySelectorAll("aside button").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === name));
  render();
}

document.querySelectorAll("aside button").forEach((btn) => btn.addEventListener("click", () => setView(btn.dataset.view)));

function currentTitle() {
  return state.current?.patient?.name_or_code || "未选择病例";
}

function setHeader(title, buttons = "") {
  $("title").textContent = title;
  $("caseBadge").textContent = currentTitle();
  actions.innerHTML = buttons;
}

function notice(text, kind = "ok") {
  const existing = document.querySelector(".toast");
  if (existing) existing.remove();
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = text;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2600);
}

function payloadFromForm() {
  const v = (name) => document.querySelector(`[name="${name}"]`)?.value || "";
  const n = (name) => (v(name) === "" ? null : Number(v(name)));
  return {
    patient: {
      name_or_code: v("name_or_code"),
      age: n("age"),
      menopausal_status: v("menopausal_status"),
      family_history: v("family_history"),
      comorbidities: v("comorbidities"),
    },
    case: {
      laterality: v("laterality"),
      tumor_location: v("tumor_location"),
      tumor_size_cm: n("tumor_size_cm"),
      focality: v("focality"),
      lesion_details: lesionDetailsFromForm(),
      clinical_node_status: v("clinical_node_status"),
      distant_metastasis: v("distant_metastasis"),
      clinical_t_stage: v("clinical_t_stage"),
      clinical_n_stage: v("clinical_n_stage"),
      clinical_m_stage: v("clinical_m_stage"),
      pdl1_cps: n("pdl1_cps"),
      brca_status: v("brca_status"),
      status: "draft",
    },
    pathology: {
      pathology_type: v("pathology_type"),
      er_percent: n("er_percent"),
      pr_percent: n("pr_percent"),
      her2: v("her2"),
      her2_fish: v("her2_fish"),
      ki67_percent: n("ki67_percent"),
      histologic_grade: v("histologic_grade"),
      lymphovascular_invasion: v("lymphovascular_invasion"),
      raw_text: v("raw_text"),
    },
    imaging: {
      ultrasound_text: v("ultrasound_text"),
      mammography_text: v("mammography_text"),
      mri_text: v("mri_text"),
    },
  };
}

function emptyCase() {
  return {
    patient: {},
    case: {},
    pathology: {},
    imaging: {},
  };
}

function parseLesions(value) {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function lesionDetailsFromForm() {
  const lesions = [];
  for (let i = 1; i <= 4; i += 1) {
    const location = document.querySelector(`[name="lesion_location_${i}"]`)?.value || "";
    const size = document.querySelector(`[name="lesion_size_${i}"]`)?.value || "";
    const note = document.querySelector(`[name="lesion_note_${i}"]`)?.value || "";
    if (location || size || note) lesions.push({ index: i, location, size_cm: size ? Number(size) : null, note });
  }
  return lesions.length ? JSON.stringify(lesions) : "";
}

async function loadCases() {
  state.cases = await api("/cases");
}

async function openCase(id, next = "edit") {
  state.caseId = id;
  state.current = await api(`/cases/${id}`);
  state.recommendation = null;
  setView(next);
}

async function seedDemo() {
  const created = await api("/demo/seed", { method: "POST" });
  await api("/admin/import-chemo-drugs", { method: "POST" }).catch(() => null);
  await openCase(created.id, "recommend");
}

async function saveCase() {
  const payload = payloadFromForm();
  if (!payload.patient.name_or_code) {
    payload.patient.name_or_code = `LOCAL-${new Date().toISOString().slice(0, 19).replace(/[-:T]/g, "")}`;
    const field = document.querySelector('[name="name_or_code"]');
    if (field) field.value = payload.patient.name_or_code;
  }
  const saved = state.caseId
    ? await api(`/cases/${state.caseId}`, { method: "PUT", body: JSON.stringify(payload) })
    : await api("/cases", { method: "POST", body: JSON.stringify(payload) });
  state.caseId = saved.id;
  state.current = saved;
  $("caseBadge").textContent = currentTitle();
  notice("已保存病例，可以继续录入或生成推荐");
  return saved.id;
}

function renderCases() {
  setHeader("病例列表", `<button class="primary" onclick="newCase()">新建并录入</button><button onclick="seedDemo()">示例病例</button>`);
  view.innerHTML = `
    <section>
      <table>
        <thead><tr><th>姓名/编号</th><th>年龄</th><th>侧别</th><th>大小</th><th>cN</th><th>M</th><th>操作</th></tr></thead>
        <tbody>${state.cases.map((c) => `
          <tr>
            <td>${c.patient_name_or_code}</td><td>${c.age ?? "-"}</td><td>${c.laterality ?? "-"}</td>
            <td>${c.tumor_size_cm ?? "-"} cm</td><td>${c.clinical_node_status ?? "-"}</td><td>${c.distant_metastasis ?? "-"}</td>
            <td class="row-actions"><button onclick="openCase(${c.id}, 'edit')">编辑</button><button onclick="openCase(${c.id}, 'recommend')">推荐</button></td>
          </tr>`).join("") || `<tr><td colspan="7" class="muted">暂无病例</td></tr>`}
        </tbody>
      </table>
    </section>`;
}

function newCase() {
  state.caseId = null;
  state.current = emptyCase();
  setView("edit");
  setTimeout(() => document.querySelector('[name="name_or_code"]')?.focus(), 50);
}

function renderEdit() {
  if (!state.current) state.current = emptyCase();
  const p = state.current.patient || {}, c = state.current.case || {}, path = state.current.pathology || {}, img = state.current.imaging || {};
  const lesions = parseLesions(c.lesion_details);
  setHeader("病例录入", `<button onclick="newCase()">清空新建</button><button class="primary" onclick="saveCase()">保存病例</button><button onclick="saveThenRecommend()">保存并生成推荐</button>`);
  view.innerHTML = `
    <section class="quick-tip"><h2>快速录入</h2><p>直接在下面表格填写即可。姓名/编号为空时，保存会自动生成本地编号。把原始病理或影像报告粘贴到对应文本框后，系统会自动抽取 ER、PR、HER2、Ki-67、肿瘤大小、淋巴结状态等能识别的信息并回填。</p></section>
    <section><h2>患者基本信息</h2><div class="grid">
      ${input("姓名/编号", "name_or_code", p.name_or_code || "")}${input("年龄", "age", p.age || "", "number")}
      ${select("绝经状态", "menopausal_status", p.menopausal_status, ["", "未绝经", "已绝经", "围绝经期"])}
      ${input("家族史", "family_history", p.family_history || "")}${input("合并症", "comorbidities", p.comorbidities || "")}
    </div></section>
    <section><h2>肿瘤信息</h2><div class="grid">
      ${select("侧别", "laterality", c.laterality, ["", "左", "右", "双侧"])}${input("肿瘤位置", "tumor_location", c.tumor_location || "")}
      ${input("肿瘤大小 cm", "tumor_size_cm", c.tumor_size_cm || "", "number")}
      ${select("病灶", "focality", c.focality, ["", "单灶", "多灶", "多中心"])}
      ${select("临床淋巴结", "clinical_node_status", c.clinical_node_status, ["", "阴性", "阳性", "可疑", "cN0", "cN1", "cN2", "cN3"])}
      ${select("远处转移", "distant_metastasis", c.distant_metastasis, ["", "无", "有", "待排", "M0", "M1"])}
      ${select("cT", "clinical_t_stage", c.clinical_t_stage, ["", "cTis", "cT1", "cT2", "cT3", "cT4"])}
      ${select("cN", "clinical_n_stage", c.clinical_n_stage, ["", "cN0", "cN1", "cN2", "cN3"])}
      ${select("cM", "clinical_m_stage", c.clinical_m_stage, ["", "cM0", "cM1"])}
      ${input("PD-L1 CPS", "pdl1_cps", c.pdl1_cps ?? "", "number")}
      ${select("BRCA状态", "brca_status", c.brca_status, ["", "未知", "gBRCA1/2突变", "BRCA1突变", "BRCA2突变", "无致病突变", "未检测"])}
    </div>${lesionEditor(lesions)}</section>
    <section><h2>病理和免疫组化</h2><div class="grid">
      ${input("病理类型", "pathology_type", path.pathology_type || "")}${input("ER %", "er_percent", path.er_percent ?? "", "number")}
      ${input("PR %", "pr_percent", path.pr_percent ?? "", "number")}${select("HER2", "her2", path.her2, ["", "0", "1+", "2+", "3+", "阴性", "阳性"])}
      ${select("HER2 FISH/ISH", "her2_fish", path.her2_fish, ["", "未检测", "阴性", "阳性", "阴性/未扩增", "阳性/扩增", "不详"])}
      ${input("Ki-67 %", "ki67_percent", path.ki67_percent ?? "", "number")}${select("组织学分级", "histologic_grade", path.histologic_grade, ["", "I级", "II级", "III级"])}
      ${select("脉管癌栓", "lymphovascular_invasion", path.lymphovascular_invasion, ["", "无", "有"])}
    </div><div id="her2FishHint" class="warning" style="display:none">HER2 IHC 2+ 时请补充 FISH/ISH 阴性或阳性，否则分型和抗 HER2 推荐只能作为待确认提示。</div><label>原始病理<textarea name="raw_text" data-auto-extract="1">${path.raw_text || ""}</textarea></label><div id="autoExtractStatus" class="muted"></div></section>
    <section><h2>影像报告</h2><div class="grid one">
      ${textarea("超声", "ultrasound_text", img.ultrasound_text || "", true)}${textarea("钼靶", "mammography_text", img.mammography_text || "", true)}${textarea("MRI", "mri_text", img.mri_text || "", true)}
    </div></section>`;
  attachReportAutoExtract();
  attachHer2FishHint();
}

function lesionEditor(lesions) {
  const rows = [1, 2, 3, 4].map((i) => {
    const item = lesions.find((x) => Number(x.index) === i) || lesions[i - 1] || {};
    return `<div class="lesion-row">
      <b>病灶${i}</b>
      <label>位置<input name="lesion_location_${i}" value="${escapeHtml(item.location || "")}"></label>
      <label>大小 cm<input name="lesion_size_${i}" type="number" value="${item.size_cm ?? ""}"></label>
      <label>备注<input name="lesion_note_${i}" value="${escapeHtml(item.note || "")}"></label>
    </div>`;
  }).join("");
  return `<div class="lesion-panel"><h3>多病灶记录</h3><p class="muted">多灶/多中心时可分别记录病灶位置和大小；TNM 仍需医生结合最大径、范围和影像/病理综合判断。</p>${rows}</div>`;
}

function input(label, name, value, type = "text") {
  return `<label>${label}<input name="${name}" type="${type}" value="${escapeHtml(value)}"></label>`;
}
function textarea(label, name, value, autoExtract = false) {
  return `<label>${label}<textarea name="${name}" ${autoExtract ? 'data-auto-extract="1"' : ""}>${escapeHtml(value)}</textarea></label>`;
}
function select(label, name, value, options) {
  return `<label>${label}<select name="${name}">${options.map((o) => `<option ${o === (value || "") ? "selected" : ""}>${o}</option>`).join("")}</select></label>`;
}

async function runExtract() {
  const text = $("pasteText").value;
  const result = await api("/extract", { method: "POST", body: JSON.stringify({ text }) });
  $("extractResult").innerHTML = `<div class="warning">未识别：${result.unknown_fields.join("、") || "无"}</div>
    <pre>${escapeHtml(JSON.stringify(result.extracted, null, 2))}</pre>
    <button class="primary" onclick='applyExtract(${JSON.stringify(JSON.stringify(result.extracted))})'>确认写入当前病例</button>`;
}
async function applyExtract(json) {
  if (!state.caseId) return alert("请先在病例列表选择病例，或到录入页保存新病例后再写入抽取结果");
  await api(`/cases/${state.caseId}/apply-extraction`, { method: "POST", body: JSON.stringify({ extracted: JSON.parse(json) }) });
  state.current = await api(`/cases/${state.caseId}`);
  notice("抽取结果已写入当前病例");
  setView("edit");
}
function renderExtract() {
  setHeader("报告文本抽取", `<button class="primary" onclick="runExtract()">自动抽取</button>`);
  view.innerHTML = `<section><textarea id="pasteText" class="copybox" placeholder="粘贴病理/影像/检查报告文本"></textarea></section><section id="extractResult"></section>`;
}

async function saveGenomic() {
  if (!state.caseId) return alert("请先保存或选择病例");
  const payload = {
    test_type: $("gType").value,
    test_name: $("gName").value,
    test_date: $("gDate").value,
    institution: $("gInstitution").value,
    raw_score: $("gRaw").value,
    risk_level: $("gRisk").value,
    recurrence_score: $("gRS").value ? Number($("gRS").value) : null,
    report_conclusion: $("gConclusion").value,
    chemo_benefit: $("gChemo").value,
    endocrine_benefit: $("gEndocrine").value,
    extended_endocrine_benefit: $("gExtended").value,
    notes: $("gNotes").value,
  };
  const saved = await api(`/cases/${state.caseId}/genomic-tests`, { method: "POST", body: JSON.stringify(payload) });
  const interp = await api("/genomic-tests/interpret", { method: "POST", body: JSON.stringify(saved) });
  $("genomicResult").innerHTML = `<div class="ok">${interp.interpretation}</div><div class="warning">${interp.limitations}</div>`;
  notice("基因检测结果已保存");
}
async function calcModel(name) {
  if (!state.caseId) return alert("请先保存或选择病例");
  const number = (id) => Number($(id).value || 0);
  let path = "", payload = {};
  if (name === "cts5") { path = "cts5"; payload = { age: number("ctsAge"), tumor_size_mm: number("ctsSize"), histologic_grade: number("ctsGrade"), positive_nodes: number("ctsNodes") }; }
  if (name === "npi") { path = "npi"; payload = { tumor_size_cm: number("npiSize"), node_stage: number("npiNode"), histologic_grade: number("npiGrade") }; }
  if (name === "rcb") { path = "rcb"; payload = { tumor_bed_max_mm: number("rcbA"), tumor_bed_second_mm: number("rcbB"), cellularity_percent: number("rcbCell"), dcis_percent: number("rcbDcis"), positive_nodes: number("rcbNodes"), largest_nodal_met_mm: number("rcbMet") }; }
  const result = await api(`/cases/${state.caseId}/risk-models/${path}`, { method: "POST", body: JSON.stringify(payload) });
  $("modelResult").innerHTML = `<div class="ok">${result.model_name}: ${result.score ?? "-"}｜${result.risk_group}。${result.interpretation}</div>`;
}
function renderGenomic() {
  const c = state.current || emptyCase();
  setHeader("基因检测/风险模型");
  view.innerHTML = `
    <section><h2>基因检测结果</h2><div class="warning">不复现商业检测内部算法，只解释检测机构已出具结果。</div>
      <div class="grid">
        <label>检测类型<select id="gType"><option>Oncotype DX / 21-gene</option><option>MammaPrint / 70-gene</option><option>72基因 / 国产多基因</option><option>EndoPredict</option><option>Prosigna / PAM50</option><option>Breast Cancer Index, BCI</option></select></label>
        <label>检测名称<input id="gName"></label><label>检测日期<input id="gDate" type="date"></label><label>检测机构<input id="gInstitution"></label>
        <label>RS/ROR/EPclin<input id="gRS" type="number"></label><label>风险等级<input id="gRisk" placeholder="低危/中危/高危/Low Risk"></label>
        <label>临床风险/淋巴结/远期风险<input id="gRaw"></label><label>化疗获益<select id="gChemo"><option>不确定</option><option>是</option><option>否</option></select></label>
        <label>内分泌获益<input id="gEndocrine" placeholder="不详"></label><label>延长内分泌获益<input id="gExtended" placeholder="不详"></label>
      </div>
      <label>原报告结论<textarea id="gConclusion"></textarea></label><label>医生备注<textarea id="gNotes"></textarea></label>
      <button class="primary" onclick="saveGenomic()">保存并解释</button><div id="genomicResult"></div>
    </section>
    <section><h2>公开风险模型</h2>
      <div class="grid">
        <label>CTS5 年龄<input id="ctsAge" type="number" value="${c.patient?.age || 50}"></label><label>CTS5 大小 mm<input id="ctsSize" type="number" value="${(c.case?.tumor_size_cm || 0) * 10}"></label><label>CTS5 分级<input id="ctsGrade" type="number" value="2"></label><label>CTS5 阳性结数<input id="ctsNodes" type="number" value="0"></label>
      </div><button onclick="calcModel('cts5')">计算 CTS5</button>
      <hr><div class="grid"><label>NPI 大小 cm<input id="npiSize" type="number" value="${c.case?.tumor_size_cm || 0}"></label><label>NPI 淋巴结分期值<input id="npiNode" type="number" value="1"></label><label>NPI 分级<input id="npiGrade" type="number" value="2"></label></div><button onclick="calcModel('npi')">计算 NPI</button>
      <hr><div class="grid"><label>RCB 最大径<input id="rcbA" type="number" value="0"></label><label>RCB 第二径<input id="rcbB" type="number" value="0"></label><label>细胞密度%<input id="rcbCell" type="number" value="0"></label><label>DCIS%<input id="rcbDcis" type="number" value="0"></label><label>阳性结数<input id="rcbNodes" type="number" value="0"></label><label>最大转移灶mm<input id="rcbMet" type="number" value="0"></label></div><button onclick="calcModel('rcb')">计算 RCB</button>
      <div id="modelResult"></div>
    </section>`;
}

async function generateRecommendation() {
  if (!state.caseId) {
    const savedId = await saveCase();
    if (!savedId) return;
  }
  state.recommendation = await api(`/cases/${state.caseId}/recommendations`, { method: "POST" });
  renderRecommend();
}

async function saveThenRecommend() {
  const savedId = await saveCase();
  if (!savedId) return;
  state.recommendation = await api(`/cases/${state.caseId}/recommendations`, { method: "POST" });
  setView("recommend");
}
function renderRecommend() {
  setHeader("推荐结果", `<button class="primary" onclick="generateRecommendation()">生成/刷新推荐</button>`);
  const r = state.recommendation;
  if (!r) { view.innerHTML = `<section><button class="primary" onclick="generateRecommendation()">生成推荐</button></section>`; return; }
  view.innerHTML = `
    <section><h2>病例摘要</h2><p>${r.case_summary}</p>${r.missing_fields.length ? `<div class="warning">缺失信息：${r.missing_fields.join("、")}</div>` : ""}</section>
    <section><h2>基因检测解释</h2>${cards(r.genomic_interpretations.map((x) => ({ title: x.test_type, strong: `${x.risk_group}｜${x.chemo_benefit_hint}`, text: `${x.interpretation} ${x.limitations}` }))) || `<div class="warning">未录入基因检测结果。</div>`}</section>
    <section><h2>风险模型结果</h2>${cards(r.risk_model_results.map((x) => ({ title: x.model_name, strong: `${x.score ?? "-"}｜${x.risk_group}`, text: x.interpretation }))) || `<p class="muted">暂无模型结果。</p>`}</section>
    <section><h2>化疗/系统治疗方案方向</h2><div class="warning">方案可修改，剂量只作参考，最终需医生确认。</div>${bsaCalculator()}${r.chemo_regimens.map(regimenCard).join("")}</section>
    <section><h2>规则输出</h2>${cards(Object.entries(r.sections).map(([k, x]) => ({ title: k, strong: x.recommendation, text: x.rationale })))}</section>`;
}
function cards(items) {
  return items.map((x) => `<div class="card"><h3>${x.title}</h3><strong>${x.strong}</strong><p>${x.text}</p></div>`).join("");
}
function regimenCard(x) {
  return `<div class="card"><h3>${x.regimen_name}</h3><strong>${x.indication}</strong><p>药物组成：${x.drugs}</p><p>周期：${x.cycle}</p><p>剂量摘要：${x.dose_summary}</p><p>配药：${x.dilution}</p><p>预处理：${x.premedication}</p><p>不良反应：${x.adverse_events}</p><p>注意：${x.caution}</p><div class="chips">${x.drug_details.map((d) => `<button onclick='showDrug(${JSON.stringify(JSON.stringify(d))})'>${d.generic_name || d.subclass}</button>`).join("")}</div><button>医生确认剂量</button></div>`;
}
function bsaCalculator() {
  return `<div class="bsa-panel">
    <h3>体表面积/体重与参考总量换算</h3>
    <p class="muted">Mosteller 公式：BSA = sqrt(身高cm x 体重kg / 3600)。支持 mg/m² 和 mg/kg 两种参考剂量换算，结果仅供核对，不生成医嘱。</p>
    <div class="grid">
      <label>身高 cm<input id="bsaHeight" type="number" value="160" oninput="calcBsaDose()"></label>
      <label>体重 kg<input id="bsaWeight" type="number" value="60" oninput="calcBsaDose()"></label>
      <label>参考剂量 mg/m²<input id="bsaDoseM2" type="number" placeholder="例如 75" oninput="calcBsaDose()"></label>
      <label>参考剂量 mg/kg<input id="bsaDoseKg" type="number" placeholder="例如 6" oninput="calcBsaDose()"></label>
    </div>
    <div id="bsaResult" class="ok">BSA：1.63 m²；体重：60.0 kg。请输入参考剂量计算总量。</div>
  </div>`;
}
function calcBsaDose() {
  const height = Number($("bsaHeight")?.value || 0);
  const weight = Number($("bsaWeight")?.value || 0);
  const doseM2 = Number($("bsaDoseM2")?.value || 0);
  const doseKg = Number($("bsaDoseKg")?.value || 0);
  if (!height || !weight) {
    $("bsaResult").textContent = "请先输入身高和体重。";
    return;
  }
  const bsa = Math.sqrt((height * weight) / 3600);
  const parts = [`BSA：${bsa.toFixed(2)} m²`, `体重：${weight.toFixed(1)} kg`];
  if (doseM2) parts.push(`按 ${doseM2} mg/m² 估算：${(bsa * doseM2).toFixed(1)} mg`);
  if (doseKg) parts.push(`按 ${doseKg} mg/kg 估算：${(weight * doseKg).toFixed(1)} mg`);
  if (!doseM2 && !doseKg) parts.push("请输入参考剂量计算总量");
  $("bsaResult").textContent = `${parts.join("；")}。请结合肝肾功能、血常规、心功能、合并症和本院规范确认。`;
}
function showDrug(json) {
  const d = JSON.parse(json);
  $("drugDetail").innerHTML = `<h2>${d.generic_name || d.subclass}</h2>${Object.entries(d).filter(([k]) => k !== "id").map(([k, v]) => `<p><b>${k}</b>：${v || "unknown"}</p>`).join("")}<div class="warning">参考剂量，不自动生成最终医嘱。如为 mg/m² 或 mg/kg 剂量，可在方案页面的体表面积/体重计算器中换算参考总量。</div>`;
  $("drugDialog").showModal();
}

let autoExtractTimer = null;
function attachReportAutoExtract() {
  document.querySelectorAll("[data-auto-extract]").forEach((el) => {
    el.addEventListener("input", () => scheduleReportAutoExtract(el.value));
    el.addEventListener("paste", () => setTimeout(() => scheduleReportAutoExtract(el.value), 80));
  });
}
function scheduleReportAutoExtract(text) {
  clearTimeout(autoExtractTimer);
  if (!text || text.trim().length < 12) return;
  const status = $("autoExtractStatus");
  if (status) status.textContent = "正在尝试自动抽取...";
  autoExtractTimer = setTimeout(() => autoFillFromReport(text), 650);
}
async function autoFillFromReport(text) {
  try {
    const result = await api("/extract", { method: "POST", body: JSON.stringify({ text }) });
    const filled = applyExtractedFields(result.extracted);
    const status = $("autoExtractStatus");
    if (status) status.textContent = filled.length ? `已自动回填：${filled.join("、")}` : "暂未识别到可回填字段。";
  } catch (err) {
    const status = $("autoExtractStatus");
    if (status) status.textContent = "自动抽取失败，可稍后重试或手工填写。";
  }
}
function setFieldIfEmpty(name, value, label, force = false) {
  if (value === undefined || value === null || value === "unknown" || value === "") return null;
  const field = document.querySelector(`[name="${name}"]`);
  if (!field) return null;
  if (!force && field.value) return null;
  field.value = value;
  field.dispatchEvent(new Event("change", { bubbles: true }));
  field.dispatchEvent(new Event("input", { bubbles: true }));
  return label;
}
function applyExtractedFields(extracted) {
  const filled = [];
  [
    setFieldIfEmpty("tumor_size_cm", extracted.tumor_size_cm, "肿瘤大小"),
    setFieldIfEmpty("clinical_node_status", extracted.clinical_node_status, "临床淋巴结"),
    setFieldIfEmpty("pathology_type", extracted.pathology_type, "病理类型"),
    setFieldIfEmpty("er_percent", extracted.er_percent, "ER"),
    setFieldIfEmpty("pr_percent", extracted.pr_percent, "PR"),
    setFieldIfEmpty("her2", extracted.her2, "HER2"),
    setFieldIfEmpty("her2_fish", extracted.her2_fish, "HER2 FISH/ISH"),
    setFieldIfEmpty("ki67_percent", extracted.ki67_percent, "Ki-67"),
    setFieldIfEmpty("histologic_grade", extracted.histologic_grade, "组织学分级"),
    setFieldIfEmpty("lymphovascular_invasion", extracted.lymphovascular_invasion, "脉管癌栓"),
  ].forEach((item) => item && filled.push(item));
  updateHer2FishHint();
  return filled;
}

function attachHer2FishHint() {
  const her2 = document.querySelector('[name="her2"]');
  const fish = document.querySelector('[name="her2_fish"]');
  her2?.addEventListener("change", updateHer2FishHint);
  her2?.addEventListener("input", updateHer2FishHint);
  fish?.addEventListener("change", updateHer2FishHint);
  updateHer2FishHint();
}

function updateHer2FishHint() {
  const her2 = document.querySelector('[name="her2"]')?.value || "";
  const fish = document.querySelector('[name="her2_fish"]')?.value || "";
  const hint = $("her2FishHint");
  if (!hint) return;
  hint.style.display = her2.includes("2+") && !fish ? "block" : "none";
}

async function renderExport() {
  setHeader("导出 MDT 摘要", state.caseId ? `<button class="primary" onclick="copyExport()">复制摘要</button>` : "");
  if (!state.caseId) { view.innerHTML = `<section>请先选择病例。</section>`; return; }
  state.exportData = await api(`/cases/${state.caseId}/export/mdt`);
  view.innerHTML = `<section><h2>病例摘要</h2><textarea class="copybox" readonly>${state.exportData.case_summary}\n${state.exportData.disclaimer}</textarea></section><section><h2>MDT 摘要</h2><textarea id="exportText" class="copybox" readonly>${state.exportData.mdt_summary}\n${state.exportData.disclaimer}</textarea></section>`;
}
async function copyExport() {
  await navigator.clipboard.writeText($("exportText").value);
  alert("已复制");
}
function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[m]));
}

async function render() {
  try {
    if (state.view === "cases") { await loadCases(); renderCases(); }
    if (state.view === "edit") renderEdit();
    if (state.view === "extract") renderExtract();
    if (state.view === "genomic") renderGenomic();
    if (state.view === "recommend") renderRecommend();
    if (state.view === "export") await renderExport();
  } catch (err) {
    view.innerHTML = `<section class="warning">${escapeHtml(err.message)}</section>`;
  }
}

Object.assign(window, { openCase, newCase, seedDemo, saveCase, saveThenRecommend, runExtract, applyExtract, saveGenomic, calcModel, generateRecommendation, showDrug, calcBsaDose, copyExport });
render();
