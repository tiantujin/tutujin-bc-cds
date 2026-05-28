# 乳腺癌临床决策支持系统 MVP

本项目是本地运行、仅供医生个人使用的乳腺癌病例整理与规则匹配 MVP。系统不识别医学影像、不提供患者端、不替代临床判断。

免责声明：本系统仅供医生个人参考，不替代临床判断，不作为自动诊疗依据。

## 功能

- 新建、编辑、删除病例
- 录入患者基本信息、肿瘤信息、影像报告、病理和免疫组化
- 粘贴中文报告文本并自动抽取 ER、PR、HER2、Ki-67、肿瘤大小、淋巴结状态、病理类型等字段
- 医生确认和修改抽取结果后写入病例
- 后端规则引擎输出分子分型、临床 TNM、治疗路径方向、缺失信息和 MDT 提醒
- 录入 Oncotype DX、MammaPrint、72基因、EndoPredict、Prosigna、BCI 等检测机构已出具结果并生成解释
- 计算 CTS5、NPI、RCB；PREDICT Breast 预留手动结果录入
- 导入本地 Word 药物表到 `chemo_drugs`，并在推荐结果中关联常用化疗/系统治疗方案
- 一键复制病例摘要和 MDT 讨论摘要

## 目录

```text
backend/
  app/
    rules/
      molecular_subtype.py
      staging.py
      surgery.py
      neoadjuvant.py
      axillary_management.py
      adjuvant_treatment.py
      risk_flags.py
    extraction.py
    recommendation_service.py
    main.py
    models.py
    schemas.py
    crud.py
    database.py
  tests/
frontend/
  src/
    pages/
    components/
```

## 数据库 Schema

- `patients`: 姓名/编号、年龄、绝经状态、家族史、合并症
- `breast_cancer_cases`: 侧别、部位、大小、病灶类型、临床淋巴结、远处转移
- `pathology_reports`: 病理类型、ER、PR、HER2、Ki-67、组织学分级、脉管癌栓、原始报告
- `imaging_reports`: 超声、钼靶、MRI 原文
- `recommendations`: 推荐结果 JSON、病例摘要、MDT 摘要、免责声明
- `guideline_versions`: 指南名、版本、来源文件、备注
- `genomic_tests`: 商业/多基因检测外部结果录入
- `risk_model_results`: CTS5、NPI、RCB、PREDICT 手动结果
- `chemotherapy_regimens`: 常见方案模板
- `chemo_drugs`: 从 `化疗药物(2).docx` 导入的药物资料

SQLite 文件默认生成在 `backend/data/breast_cancer_cds.db`。
后端使用 Python 标准库 `sqlite3` 管理本地数据库，避免本地 MVP 依赖额外 ORM 编译组件。

## API 路由

```text
GET    /api/cases
POST   /api/cases
GET    /api/cases/{case_id}
PUT    /api/cases/{case_id}
DELETE /api/cases/{case_id}
POST   /api/extract
POST   /api/cases/{case_id}/apply-extraction
POST   /api/cases/{case_id}/recommendations
GET    /api/cases/{case_id}/recommendations/latest
GET    /api/cases/{case_id}/export
GET    /api/cases/{case_id}/export/mdt
GET    /api/guidelines
POST   /api/demo/seed
GET    /api/cases/{case_id}/genomic-tests
POST   /api/cases/{case_id}/genomic-tests
PUT    /api/genomic-tests/{test_id}
DELETE /api/genomic-tests/{test_id}
POST   /api/genomic-tests/interpret
GET    /api/cases/{case_id}/risk-model-results
POST   /api/cases/{case_id}/risk-models/cts5
POST   /api/cases/{case_id}/risk-models/npi
POST   /api/cases/{case_id}/risk-models/rcb
POST   /api/cases/{case_id}/risk-models/predict-manual
GET    /api/chemo/drugs
GET    /api/chemo/drugs/{drug_id}
GET    /api/chemo/regimens
GET    /api/chemo/regimens/{regimen_id}
POST   /api/admin/import-chemo-drugs
POST   /api/admin/seed-chemo-regimens
```

## 本地运行

### 后端

```bash
cd breast-cancer-cds/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

后端接口文档：http://127.0.0.1:8000/docs

### 前端

当前机器检测到有 `node` 但没有 `npm`。如果本机安装了 npm、pnpm 或 yarn，可运行：

```bash
cd breast-cancer-cds/frontend
npm install
npm run dev
```

前端地址：http://127.0.0.1:5173

## 测试

```bash
cd breast-cancer-cds/backend
source .venv/bin/activate
PYTHONPATH=. pytest
```

## 导入化疗药物表

```bash
cd breast-cancer-cds/backend
source .venv/bin/activate
python scripts/import_chemo_drugs.py
```

导入脚本读取 `/Users/chelseatian/Desktop/化疗药物(2).docx`，保留原始剂量文本；缺失字段写入 `unknown`。

## 规则引擎说明

规则不写在前端，全部在 `backend/app/rules/`。每个模块返回统一结构：

```json
{
  "recommendation": "建议",
  "rationale": "原因",
  "evidence_level": "MVP规则/指南要点",
  "guideline_version": "CBCS 2026 精要版 + breast.pdf 本地参考",
  "missing_fields": [],
  "caution_flags": []
}
```

当前 MVP 已实现的提示包括：

- HER2 阳性且肿瘤 >=2 cm 或临床淋巴结阳性：考虑新辅助化疗联合抗 HER2 治疗
- TNBC 且肿瘤 >=2 cm 或临床淋巴结阳性：考虑新辅助系统治疗
- HR+/HER2-、早期低危：可优先考虑手术，术后结合病理风险决定辅助治疗
- 存在远处转移：不属于早期手术路径，建议 MDT 讨论
- 信息不完整：不作强推荐，提示补充检查或字段

商业基因检测说明：系统不复现 Oncotype DX、21基因、70/72基因、MammaPrint、EndoPredict、Prosigna、BCI 等内部算法，只解释医生录入的检测机构报告结果。
