from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict

from app import chemo, crud, genomics, schemas
from app.rules import (
    adjuvant_treatment,
    axillary_management,
    molecular_subtype,
    neoadjuvant,
    risk_flags,
    staging,
    surgery,
)
from app.schemas import EXTENDED_DISCLAIMER, RecommendationResponse


def _flatten_case(case: dict) -> dict:
    data = {
        **case["patient"],
        **case["case"],
        **(case.get("pathology") or {}),
    }
    lesions = []
    if data.get("lesion_details"):
        try:
            lesions = json.loads(data["lesion_details"])
        except (TypeError, json.JSONDecodeError):
            lesions = []
    data["lesions"] = lesions
    return data


def build_case_summary(data: dict) -> str:
    return (
        f"患者/编号：{data.get('name_or_code') or '未填写'}；年龄：{data.get('age') or '未填写'}；"
        f"绝经状态：{data.get('menopausal_status') or '未填写'}。"
        f"{data.get('laterality') or '未填写'}乳{data.get('tumor_location') or '部位未填写'}，"
        f"肿瘤大小：{data.get('tumor_size_cm') or '未填写'} cm，"
        f"病灶：{data.get('focality') or '未填写'}，"
        f"临床淋巴结：{data.get('clinical_node_status') or '未填写'}，"
        f"远处转移：{data.get('distant_metastasis') or '未填写'}。"
        f"TNM：{data.get('clinical_t_stage') or '自动估算'}{data.get('clinical_n_stage') or ''}{data.get('clinical_m_stage') or ''}；"
        f"PD-L1/CPS：{data.get('pdl1_cps') if data.get('pdl1_cps') is not None else '未填写'}；"
        f"BRCA：{data.get('brca_status') or '未填写'}。"
        f"病理：{data.get('pathology_type') or '未填写'}，ER {data.get('er_percent') if data.get('er_percent') is not None else '未填写'}%，"
        f"PR {data.get('pr_percent') if data.get('pr_percent') is not None else '未填写'}%，"
        f"HER2 {data.get('her2') or '未填写'}，FISH/ISH：{data.get('her2_fish') or '未填写'}，"
        f"Ki-67 {data.get('ki67_percent') if data.get('ki67_percent') is not None else '未填写'}%，"
        f"组织学分级：{data.get('histologic_grade') or '未填写'}，脉管癌栓：{data.get('lymphovascular_invasion') or '未填写'}。"
    )


def evaluate_case(conn: sqlite3.Connection, case_id: int) -> RecommendationResponse | None:
    case = crud.get_case(conn, case_id)
    if not case:
        return None
    data = _flatten_case(case)
    genomic_tests = crud.list_genomic_tests(conn, case_id)
    genomic_interpretations = [item.model_dump() for item in genomics.interpret_many(genomic_tests)]
    risk_results = crud.list_risk_model_results(conn, case_id)
    rule_sections = {
        "molecular_subtype": molecular_subtype.evaluate(data),
        "staging": staging.evaluate(data),
        "neoadjuvant": neoadjuvant.evaluate(data),
        "surgery": surgery.evaluate(data),
        "axillary_management": axillary_management.evaluate(data),
        "adjuvant_treatment": adjuvant_treatment.evaluate(data),
        "risk_flags": risk_flags.evaluate(data),
    }
    sections = {key: schemas.RuleResult(**asdict(value)) for key, value in rule_sections.items()}
    if genomic_interpretations and ((data.get("er_percent") or 0) >= 1 or (data.get("pr_percent") or 0) >= 1) and any(token in (data.get("her2") or "") for token in ["阴", "0", "1+"]):
        genomic_text = "；".join(item["interpretation"] for item in genomic_interpretations)
        sections["adjuvant_treatment"].recommendation = f"优先参考已录入基因检测解释；{sections['adjuvant_treatment'].recommendation}"
        sections["adjuvant_treatment"].rationale = (
            f"{genomic_text} 同时需结合年龄、绝经状态、淋巴结、肿瘤大小、分级、LVI 等临床病理因素。"
        )
    elif ((data.get("er_percent") or 0) >= 1 or (data.get("pr_percent") or 0) >= 1) and any(token in (data.get("her2") or "") for token in ["阴", "0", "1+"]):
        sections["adjuvant_treatment"].caution_flags.append("可考虑基因检测辅助 HR+/HER2- 辅助化疗决策")
    missing = sorted({item for section in sections.values() for item in section.missing_fields})
    flags = sorted({item for section in sections.values() for item in section.caution_flags})
    chemo.seed_regimens(conn)
    regimen_names = chemo.recommend_regimen_names(data, genomic_interpretations)
    chemo_regimens = chemo.get_regimens_by_names(conn, regimen_names)
    case_summary = build_case_summary(data)
    genomic_summary = "；".join(item["interpretation"] for item in genomic_interpretations) or "未录入基因检测结果。"
    risk_summary = "；".join(item["interpretation"] for item in risk_results) or "未录入公开风险模型结果。"
    regimen_summary = "；".join(item["regimen_name"] for item in chemo_regimens) or "暂无自动关联方案。"
    mdt_summary = (
        f"{case_summary}\n"
        f"基因检测：{genomic_summary}\n"
        f"风险模型：{risk_summary}\n"
        f"核心建议：{sections['neoadjuvant'].recommendation}；{sections['surgery'].recommendation}；"
        f"{sections['axillary_management'].recommendation}。"
        f"推荐化疗/系统治疗方案方向：{regimen_summary}。"
        f"MDT提醒：{('；'.join(flags) if flags else '暂无强制 MDT 提醒')}。"
    )
    response = RecommendationResponse(
        case_id=case_id,
        case_summary=case_summary,
        mdt_summary=mdt_summary,
        sections=sections,
        missing_fields=missing,
        caution_flags=flags,
        genomic_interpretations=genomic_interpretations,
        risk_model_results=risk_results,
        chemo_regimens=chemo_regimens,
    )
    crud.insert_recommendation(conn, case_id, response.model_dump_json(), case_summary, mdt_summary, EXTENDED_DISCLAIMER)
    return response


def latest_recommendation(conn: sqlite3.Connection, case_id: int) -> RecommendationResponse | None:
    output_json = crud.latest_recommendation_json(conn, case_id)
    if not output_json:
        return evaluate_case(conn, case_id)
    return RecommendationResponse(**json.loads(output_json))
