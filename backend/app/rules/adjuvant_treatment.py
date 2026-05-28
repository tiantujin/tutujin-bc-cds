from __future__ import annotations

from app.rules.common import RuleResult, has_distant_metastasis, is_node_positive, is_positive_percent, normalized, result


def evaluate(data: dict) -> RuleResult:
    missing = [field for field in ["er_percent", "pr_percent", "her2", "clinical_node_status"] if data.get(field) in (None, "")]
    if missing:
        return result("系统治疗方向待补充", "辅助/系统治疗方向依赖 HR、HER2、淋巴结、分级、Ki-67 和术后病理风险。", missing)
    er = is_positive_percent(data.get("er_percent"))
    pr = is_positive_percent(data.get("pr_percent"))
    hr_positive = bool(er or pr)
    her2 = normalized(data.get("her2"))
    fish = normalized(data.get("her2_fish"))
    metastatic = has_distant_metastasis(data.get("distant_metastasis")) or normalized(data.get("clinical_m_stage")) == "cm1"
    pdl1_cps = data.get("pdl1_cps")
    brca = normalized(data.get("brca_status"))
    her2_positive = "3+" in her2 or "阳" in her2 or "positive" in her2 or ("2+" in her2 and ("阳" in fish or "扩增" in fish or "positive" in fish))
    her2_negative = "0" in her2 or "1+" in her2 or "阴" in her2 or "negative" in her2 or ("2+" in her2 and ("阴" in fish or "未扩增" in fish or "negative" in fish))
    if metastatic:
        directions = ["M1/IV期优先进入晚期系统治疗路径，不输出早期辅助治疗强推荐"]
        rationale = ["依据cM1/M1信息，治疗目标需结合疾病负荷、症状、既往治疗、器官功能和患者意愿。"]
        cautions = ["M1建议MDT讨论：病理复核、转移灶活检可及性、ER/PR/HER2复测、PD-L1/CPS、BRCA/HRD/NGS、骨保护和局部姑息治疗需求"]
        if her2_positive:
            directions.append("HER2阳性晚期：考虑抗HER2治疗联合化疗；进展后结合T-DXd、T-DM1、吡咯替尼/卡培他滨等线序")
            rationale.append("HER2阳性晚期通常以抗HER2为系统治疗核心，需结合既往曲妥珠/帕妥珠/T-DM1/T-DXd暴露。")
        elif hr_positive and her2_negative:
            directions.append("HR+/HER2-晚期：内分泌治疗联合CDK4/6抑制剂通常优先；内脏危象或快速进展时讨论化疗")
            rationale.append("HR阳性HER2阴性晚期应区分内分泌敏感、内分泌耐药和内脏危象。")
            if "突变" in brca or "brca" in brca:
                directions.append("BRCA突变：可讨论PARP抑制剂适用性")
        elif (not hr_positive) and her2_negative:
            directions.append("TNBC晚期：需根据PD-L1/CPS、BRCA状态和既往治疗线数选择免疫联合化疗、铂类、PARP抑制剂或ADC")
            if pdl1_cps is None:
                cautions.append("TNBC晚期缺少PD-L1/CPS，免疫治疗适应证判断不完整")
            elif pdl1_cps >= 10:
                directions.append("PD-L1 CPS达到常用免疫治疗阈值时，可讨论PD-1/PD-L1抑制剂联合化疗")
            if "突变" in brca or "brca" in brca:
                directions.append("BRCA突变：可讨论奥拉帕利/氟唑帕利等PARP抑制剂")
        return result("；".join(directions), " ".join(rationale), caution_flags=cautions)
    node_positive = bool(is_node_positive(data.get("clinical_node_status")))
    directions = []
    if hr_positive:
        directions.append("内分泌治疗")
    if her2_positive:
        directions.append("抗 HER2 治疗联合化疗评估")
    if not hr_positive and her2_negative:
        directions.append("化疗/免疫治疗适应证评估")
    if node_positive:
        directions.append("结合淋巴结阳性进行强化辅助治疗风险评估")
    if not directions:
        directions.append("结合术后病理进行个体化系统治疗评估")
    return result("；".join(directions), "依据 HR/HER2 状态、淋巴结状态和复发风险因素形成系统治疗方向，最终需结合术后病理。")
