from __future__ import annotations

import json
import math
from typing import Any

from app import schemas


def calculate_cts5(payload: schemas.CTS5Request) -> schemas.RiskModelResultRead:
    nodes = max(payload.positive_nodes, 0)
    score = 0.438 * nodes + 0.988 * (0.093 * payload.tumor_size_mm - 0.001 * payload.tumor_size_mm**2 + 0.375 * payload.histologic_grade + 0.017 * payload.age)
    score = round(score, 2)
    if score < 3.13:
        group = "低危"
    elif score <= 3.86:
        group = "中危"
    else:
        group = "高危"
    return schemas.RiskModelResultRead(
        model_name="CTS5",
        input_json=payload.model_dump(),
        score=score,
        risk_group=group,
        interpretation=f"CTS5 score {score}，{group}。用于讨论 HR+ 患者完成5年内分泌治疗后的5-10年远期复发风险和延长内分泌治疗价值。",
        limitations="仅适用于 HR阳性、已完成5年内分泌治疗后的远期复发风险评估；不替代商业检测或临床判断。",
    )


def calculate_npi(payload: schemas.NPIRequest) -> schemas.RiskModelResultRead:
    score = round(0.2 * payload.tumor_size_cm + payload.node_stage + payload.histologic_grade, 2)
    if score <= 2.4:
        group = "极低/优良预后"
    elif score <= 3.4:
        group = "低危"
    elif score <= 5.4:
        group = "中危"
    else:
        group = "高危"
    return schemas.RiskModelResultRead(
        model_name="NPI",
        input_json=payload.model_dump(),
        score=score,
        risk_group=group,
        interpretation=f"NPI = 0.2 x 肿瘤大小(cm) + 淋巴结分期 + 组织学分级 = {score}，预后分层：{group}。",
        limitations="NPI 为公开预后指数，需结合分子分型、年龄、治疗反应和现代系统治疗综合判断。",
    )


def calculate_rcb(payload: schemas.RCBRequest) -> schemas.RiskModelResultRead:
    if payload.tumor_bed_max_mm == 0 and payload.tumor_bed_second_mm == 0 and payload.positive_nodes == 0:
        score = 0.0
        group = "RCB-0 / pCR"
    else:
        invasive_area = payload.tumor_bed_max_mm * payload.tumor_bed_second_mm * max(payload.cellularity_percent - payload.dcis_percent, 0) / 10000
        nodal_component = payload.positive_nodes * 0.35 + math.log1p(max(payload.largest_nodal_met_mm, 0)) * 0.25
        score = round(invasive_area + nodal_component, 2)
        if score <= 1.36:
            group = "RCB-I"
        elif score <= 3.28:
            group = "RCB-II"
        else:
            group = "RCB-III"
    pcr = "是" if group.startswith("RCB-0") else "否"
    return schemas.RiskModelResultRead(
        model_name="RCB",
        input_json=payload.model_dump(),
        score=score,
        risk_group=group,
        interpretation=f"RCB score {score}，分级：{group}，是否 pCR：{pcr}。用于新辅助治疗后残余病灶负荷和复发风险提示。",
        limitations="MVP 中为透明近似计算和分层提示；正式 RCB 需按病理科标准工具和完整病理参数确认。",
    )


def predict_manual(payload: schemas.PredictManualRequest) -> schemas.RiskModelResultRead:
    return schemas.RiskModelResultRead(
        model_name="PREDICT Breast",
        input_json=payload.input_json,
        score=payload.score,
        risk_group=payload.risk_group or "手动录入",
        interpretation=payload.interpretation,
        limitations=payload.limitations or "本系统暂不复现 PREDICT Breast 自动算法，仅保存医生从官网或报告中录入的结果。",
    )


def serialize_result(result: schemas.RiskModelResultRead) -> tuple[str, float | None, str, str, str]:
    return json.dumps(result.input_json, ensure_ascii=False), result.score, result.risk_group, result.interpretation, result.limitations
