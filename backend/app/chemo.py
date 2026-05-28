from __future__ import annotations

import sqlite3
from typing import Any


CHEMO_DISCLAIMER = "请结合患者体表面积、肝肾功能、心功能、血常规、既往治疗和本院规范最终确认剂量。"


REGIMEN_TEMPLATES = [
    ("AC", "早期乳腺癌辅助/新辅助基础蒽环方案，具体需医生判断", "通用", "辅助/新辅助", "多柔比星/表柔比星;环磷酰胺", "每21天或剂量密集方案，常见4周期", "多柔比星60mg/m2或表柔比星75-100mg/m2 D1 + 环磷酰胺600mg/m2 D1", "蒽环类高度致吐预防；评估G-CSF适应证", "按药物说明书及本院规范", "心脏毒性;骨髓抑制;恶心呕吐;脱发;黏膜炎", "蒽环类损伤DNA，环磷酰胺烷化作用", "治疗前评估心功能；注意蒽环累积剂量、血常规、肝肾功能", "CBCS 2026摘要版/NCCN剂量表"),
    ("EC", "早期乳腺癌辅助/新辅助常用蒽环方案，具体需医生判断", "通用", "辅助/新辅助", "表柔比星;环磷酰胺", "每21天，常见4周期", "表柔比星75-100mg/m2 D1 + 环磷酰胺600mg/m2 D1", "蒽环类高度致吐预防；必要时G-CSF", "按药物说明书及本院规范", "心脏毒性;骨髓抑制;恶心呕吐;脱发", "DNA损伤 + 烷化作用", "治疗前和治疗中监测心功能、血常规、肝肾功能", "CBCS 2026摘要版"),
    ("AC-T", "早期乳腺癌辅助/新辅助蒽环序贯紫杉方案，具体需医生判断", "通用", "辅助/新辅助", "多柔比星/表柔比星;环磷酰胺;紫杉醇/多西他赛", "AC/EC后序贯紫杉类，常见总8周期或周疗紫杉12次", "蒽环+环磷酰胺后序贯紫杉醇80mg/m2周疗或多西他赛80-100mg/m2 q3w", "蒽环止吐 + 紫杉类过敏预处理；按风险使用G-CSF", "按药物说明书及本院规范", "心脏毒性;骨髓抑制;恶心呕吐;脱发;神经毒性;过敏反应", "DNA损伤 + 微管抑制", "蒽环与抗HER2药物同用需谨慎；注意心功能和周围神经毒性", "CBCS 2026摘要版/NCCN剂量表"),
    ("EC-T", "早期乳腺癌辅助/新辅助常用序贯方案，适用于中高复发风险场景", "通用", "辅助/新辅助", "表柔比星;环磷酰胺;紫杉醇/多西他赛", "EC q3w x4 后序贯多西他赛 q3w x4 或紫杉醇周疗", "表柔比星75-100mg/m2 D1 + 环磷酰胺600mg/m2 D1 x4；序贯多西他赛80-100mg/m2 D1 q21d x4或紫杉醇80mg/m2周疗", "蒽环止吐 + 紫杉类过敏预处理；评估G-CSF", "按药物说明书及本院规范", "心脏毒性;骨髓抑制;神经毒性;水肿;脱发", "DNA损伤 + 微管抑制", "治疗前评估心功能；按年龄、合并症和骨髓储备调整", "CBCS 2026摘要版"),
    ("ddEC-wP", "较高危早期乳腺癌辅助/新辅助剂量密集或序贯周疗紫杉方向", "通用/TNBC", "辅助/新辅助", "表柔比星;环磷酰胺;紫杉醇", "EC可为每14天x4，序贯紫杉醇周疗12次或D1/D8/D15 q21d x4", "表柔比星75-100mg/m2 + 环磷酰胺600mg/m2；序贯紫杉醇80mg/m2周疗", "剂量密集方案通常需G-CSF；紫杉类过敏预处理", "按药物说明书及本院规范", "骨髓抑制;发热性中性粒细胞减少;神经毒性;心脏毒性", "DNA损伤 + 微管抑制", "体能状态差、骨髓储备差或合并症多者需谨慎", "CBCS 2026摘要版"),
    ("TC", "HR+/HER2-等早期乳腺癌辅助治疗可选方案，需结合风险评估", "HR+/HER2-等", "辅助", "多西他赛;环磷酰胺", "每21天，常见4-6周期", "多西他赛75mg/m2 D1 + 环磷酰胺600mg/m2 D1", "多西他赛过敏/水肿预处理 + 止吐；评估G-CSF", "按药物说明书及本院规范", "骨髓抑制;过敏反应;水肿;脱发;恶心呕吐;神经毒性", "微管抑制 + 烷化作用", "注意发热性中性粒细胞减少、肝功能、过敏和水肿", "CBCS 2026摘要版"),
    ("TCb", "TNBC或部分新辅助场景可考虑紫杉类联合铂类，需医生确认", "TNBC", "新辅助", "多西他赛/紫杉醇;卡铂", "常见每21天或周疗方案，按本院规范", "多西他赛75mg/m2 q21d或紫杉醇80mg/m2周疗；卡铂按AUC计算", "紫杉类过敏预处理 + 铂类止吐", "卡铂剂量需按Calvert公式和肾功能计算", "骨髓抑制;血小板减少;神经毒性;恶心呕吐;过敏", "微管抑制 + 铂类DNA交联", "重点核对肾功能、血常规、神经毒性和BRCA/同源重组缺陷相关信息", "CBCS 2026摘要版"),
    ("紫杉类 + 卡铂", "TNBC新辅助或复发转移部分场景，需医生确认", "TNBC", "新辅助/晚期", "紫杉醇/白蛋白紫杉醇/多西他赛;卡铂", "周疗或q3w，按本院规范", "紫杉醇80mg/m2周疗或多西他赛75mg/m2 q21d；卡铂按AUC计算", "紫杉类过敏预处理 + 铂类止吐", "卡铂按肾功能和AUC计算", "骨髓抑制;神经毒性;恶心呕吐;过敏;肾功能相关风险", "微管抑制 + 铂类DNA交联", "需结合分期、PD-L1/CPS、BRCA状态和治疗目的判断", "CBCS 2026摘要版/NCCN"),
    ("wPCb-EC", "TNBC肿瘤较大或淋巴结阳性新辅助方向，需医生确认", "TNBC", "新辅助", "紫杉醇;卡铂;表柔比星;环磷酰胺", "紫杉/卡铂阶段后序贯EC，具体周期按本院规范", "紫杉醇80mg/m2 D1/D8/D15；卡铂按AUC；序贯EC：表柔比星75-100mg/m2 + 环磷酰胺600mg/m2", "紫杉类过敏预处理 + 铂类/蒽环止吐；评估G-CSF", "卡铂按AUC；其他按说明书及本院规范", "骨髓抑制;血小板减少;神经毒性;心脏毒性;恶心呕吐", "微管抑制 + 铂类DNA交联 + DNA损伤", "TNBC新辅助需评估免疫治疗适应证、BRCA状态和患者耐受性", "CBCS 2026摘要版"),
    ("帕博利珠单抗+PCb-EC", "符合适应证的高危早期TNBC新辅助/辅助延续治疗方向，需医生确认", "TNBC", "新辅助/辅助", "帕博利珠单抗;紫杉醇;卡铂;表柔比星/多柔比星;环磷酰胺", "PCb阶段序贯EC/AC，帕博利珠单抗可术后延续；按适应证和本院规范", "帕博利珠单抗200mg q3w或2mg/kg；紫杉醇80mg/m2；卡铂AUC；EC/AC阶段按蒽环环磷酰胺方案", "免疫治疗输注反应监测；化疗止吐和紫杉预处理", "按说明书及本院规范", "免疫相关不良反应;骨髓抑制;神经毒性;心脏毒性;恶心呕吐", "PD-1免疫治疗 + 化疗协同", "需核对PD-L1/CPS及当地适应证；警惕免疫性肺炎、肝炎、内分泌异常", "CBCS 2026摘要版/NCCN"),
    ("TH", "HER2阳性低肿瘤负荷辅助/部分新辅助场景，需医生确认", "HER2+", "辅助/新辅助", "紫杉醇/多西他赛;曲妥珠单抗", "周疗紫杉醇12次联合曲妥珠单抗，曲妥珠单抗总疗程常至1年", "紫杉醇80mg/m2周疗；曲妥珠单抗首剂4mg/kg后2mg/kg周疗，或首剂8mg/kg后6mg/kg q3w", "紫杉类过敏预处理；抗HER2输注反应管理", "按药物说明书及本院规范", "神经毒性;骨髓抑制;心功能下降;输注反应", "微管抑制 + HER2靶向", "治疗前和治疗中监测LVEF；避免与蒽环同步使用", "CBCS 2026摘要版/NCCN"),
    ("wPH", "HER2阳性低至中危场景可选紫杉醇联合曲妥珠单抗方向", "HER2+", "辅助/新辅助", "紫杉醇/白蛋白紫杉醇;曲妥珠单抗", "紫杉类D1/D8/D15 q21d或周疗，曲妥珠单抗维持至约1年", "紫杉醇80mg/m2或白蛋白紫杉醇100-125mg/m2；曲妥珠单抗首剂4mg/kg后2mg/kg周疗或8/6mg/kg q3w", "紫杉类预处理按制剂；曲妥珠单抗输注监测", "按药物说明书及本院规范", "神经毒性;骨髓抑制;心功能下降;输注反应", "微管抑制 + HER2靶向", "需定期心功能评估；白蛋白紫杉醇剂量按说明书和本院规范", "CBCS 2026摘要版"),
    ("TCH", "HER2阳性辅助/新辅助非蒽环方案，需医生确认", "HER2+", "辅助/新辅助", "多西他赛;卡铂;曲妥珠单抗", "每21天，常见6周期；曲妥珠单抗总疗程约1年", "多西他赛75mg/m2 D1 + 卡铂AUC=6 D1 + 曲妥珠单抗首剂8mg/kg后6mg/kg D1", "紫杉类过敏预处理 + 铂类止吐；抗HER2输注监测", "卡铂按AUC；其他按说明书及本院规范", "骨髓抑制;血小板减少;过敏;恶心呕吐;心功能下降", "微管抑制 + 铂类DNA交联 + HER2靶向", "核对肾功能、血常规和LVEF", "CBCS 2026摘要版/NCCN"),
    ("TCbHP", "HER2阳性肿瘤较大或淋巴结阳性新辅助优先考虑方向之一", "HER2+", "新辅助/辅助", "多西他赛;卡铂;曲妥珠单抗;帕妥珠单抗", "每21天，常见6周期；H/P可按场景维持至总疗程约1年", "多西他赛75mg/m2 D1 + 卡铂AUC=6 D1 + 曲妥珠单抗8/6mg/kg + 帕妥珠单抗840/420mg", "紫杉类过敏预处理 + 铂类止吐；双靶输注反应监测", "卡铂按AUC和肾功能；H/P按体重或固定剂量说明书", "腹泻;骨髓抑制;血小板减少;过敏;心功能下降;恶心呕吐", "微管抑制 + 铂类DNA交联 + 双HER2阻断", "需监测LVEF、腹泻、肾功能和血常规；适应证需医生确认", "CBCS 2026摘要版"),
    ("TCHP", "HER2阳性新辅助/辅助强化场景，TCbHP的常用简称", "HER2+", "新辅助/辅助", "多西他赛;卡铂;曲妥珠单抗;帕妥珠单抗", "每21天，常见6周期；H/P按场景维持", "同TCbHP：多西他赛75mg/m2 + 卡铂AUC=6 + 曲妥珠单抗8/6mg/kg + 帕妥珠单抗840/420mg", "紫杉类过敏预处理 + 铂类止吐；双靶输注监测", "按药物说明书及本院规范", "腹泻;骨髓抑制;心功能下降;恶心呕吐;过敏", "微管抑制 + 铂类DNA交联 + 双HER2阻断", "同TCbHP；需结合新辅助/辅助适应证和心功能", "CBCS 2026摘要版"),
    ("EC-THP", "HER2阳性新辅助/辅助蒽环序贯紫杉双靶方向，需医生确认", "HER2+", "新辅助/辅助", "表柔比星;环磷酰胺;多西他赛/紫杉醇;曲妥珠单抗;帕妥珠单抗", "EC x4 后序贯T+HP，具体周期按本院规范", "EC：表柔比星75-100mg/m2 + 环磷酰胺600mg/m2；序贯多西他赛80-100mg/m2或紫杉醇80mg/m2，并联合H/P", "蒽环止吐 + 紫杉预处理 + 双靶输注监测", "按说明书及本院规范", "心脏毒性;骨髓抑制;腹泻;神经毒性;过敏", "DNA损伤 + 微管抑制 + 双HER2阻断", "抗HER2治疗通常不与蒽环同步；需严密心功能监测", "CBCS 2026摘要版"),
    ("曲妥珠单抗 + 帕妥珠单抗", "HER2阳性相关场景，可与化疗或内分泌治疗联合，需医生确认", "HER2+", "新辅助/辅助/晚期", "曲妥珠单抗;帕妥珠单抗", "每21天，按治疗目的决定疗程", "曲妥珠单抗首剂8mg/kg后6mg/kg q3w；帕妥珠单抗首剂840mg后420mg q3w", "输注反应管理；必要时止泻支持", "按药物说明书及本院规范", "心功能下降;输注反应;腹泻;皮疹", "双HER2阻断", "治疗前和治疗中监测LVEF；合并蒽环用药需谨慎", "CBCS 2026摘要版/NCCN"),
    ("紫杉类+HP", "HER2阳性复发转移一线常见系统治疗方向，需医生确认", "HER2+", "晚期", "紫杉醇/多西他赛;曲妥珠单抗;帕妥珠单抗", "每21天或周疗紫杉，H/P q3w", "紫杉类按制剂；曲妥珠单抗8/6mg/kg；帕妥珠单抗840/420mg", "紫杉类预处理；H/P输注监测", "按说明书及本院规范", "神经毒性;骨髓抑制;腹泻;心功能下降;输注反应", "微管抑制 + 双HER2阻断", "晚期治疗需结合既往抗HER2暴露、疾病负荷和患者意愿", "CBCS 2026摘要版/NCCN"),
    ("PCbHP", "HER2阳性晚期或部分新辅助场景紫杉铂类双靶方向，需医生确认", "HER2+", "新辅助/晚期", "紫杉醇;卡铂;曲妥珠单抗;帕妥珠单抗", "周疗或q3w，H/P q3w", "紫杉醇80mg/m2周疗或按本院规范；卡铂AUC；曲妥珠单抗8/6mg/kg；帕妥珠单抗840/420mg", "紫杉类预处理 + 铂类止吐 + H/P输注监测", "卡铂按AUC和肾功能", "骨髓抑制;血小板减少;神经毒性;腹泻;心功能下降", "微管抑制 + 铂类DNA交联 + 双HER2阻断", "注意肾功能、血常规和心功能；需结合治疗线数", "CBCS 2026摘要版"),
    ("T-DM1", "HER2阳性新辅助后残余病灶强化或晚期后线治疗方向，需医生确认", "HER2+", "辅助强化/晚期", "恩美曲妥珠单抗/T-DM1", "每21天，辅助强化常见14周期或按适应证", "T-DM1 3.6mg/kg D1 q21d", "输注反应监测；常规无需化疗预处理", "按药物说明书及本院规范", "血小板减少;肝功能异常;周围神经病变;疲乏;出血风险", "HER2抗体偶联微管抑制药物", "需核对血小板、肝功能、出血风险和既往抗HER2治疗", "CBCS 2026摘要版/NCCN"),
    ("T-DXd", "HER2阳性或HER2-low晚期特定线数治疗方向，需医生确认", "HER2+/HER2-low", "晚期", "德曲妥珠单抗/T-DXd", "每21天，按适应证和治疗线数", "T-DXd 5.4mg/kg D1 q21d", "输注反应监测；按中高度致吐风险预防", "按药物说明书及本院规范", "间质性肺病/肺炎;恶心呕吐;骨髓抑制;脱发;疲乏", "HER2抗体偶联拓扑异构酶I抑制药物", "重点筛查和监测ILD/肺炎；出现可疑呼吸症状需及时处理", "CBCS 2026摘要版/NCCN"),
    ("帕博利珠单抗+白蛋白紫杉醇", "PD-L1阳性晚期TNBC一线免疫联合化疗方向，需医生确认", "TNBC", "晚期一线", "帕博利珠单抗;白蛋白紫杉醇/紫杉醇", "免疫治疗q3w或q6w，紫杉类周疗/按本院规范", "帕博利珠单抗200mg q3w或2mg/kg，或400mg/4mg/kg q6w；白蛋白紫杉醇100mg/m2或125mg/m2 D1/D8/D15 q28d", "免疫治疗输注反应监测；紫杉类按制剂预处理", "按药物说明书及本院规范", "免疫相关肺炎/肝炎/内分泌异常;骨髓抑制;神经毒性;脱发", "PD-1免疫治疗 + 微管抑制", "需核对PD-L1/CPS及当地适应证；治疗前记录甲状腺、肝肾功能和肺部基础情况", "CBCS 2026摘要版/NCCN"),
    ("特瑞普利单抗+白蛋白紫杉醇", "PD-L1阳性晚期TNBC免疫联合化疗可选方向，需医生确认", "TNBC", "晚期一线", "特瑞普利单抗;白蛋白紫杉醇", "按说明书及本院规范", "特瑞普利单抗联合白蛋白紫杉醇，剂量按药品说明书和本院规范确认", "免疫治疗输注反应监测", "按药物说明书及本院规范", "免疫相关不良反应;骨髓抑制;神经毒性;肝功能异常", "PD-1免疫治疗 + 微管抑制", "需核对PD-L1状态、医保/适应证和患者免疫相关风险", "CBCS 2026摘要版"),
    ("奥拉帕利", "gBRCA1/2突变HER2阴性晚期或高危早期特定场景，需医生确认", "HER2-/BRCA突变", "辅助强化/晚期", "奥拉帕利", "口服，按适应证决定疗程", "常见300mg bid po，需按说明书、肾功能和相互作用确认", "通常无需静脉预处理", "口服", "贫血;恶心;疲乏;白细胞/血小板减少;少见MDS/AML风险", "PARP抑制，利用同源重组修复缺陷", "仅在明确BRCA致病/疑似致病突变等适应证下考虑；监测血常规和肾功能", "CBCS 2026摘要版/NCCN"),
    ("氟唑帕利", "BRCA突变相关乳腺癌PARP抑制方向，需医生确认", "HER2-/BRCA突变", "晚期", "氟唑帕利", "口服，按说明书", "剂量按药品说明书、本院规范和肾功能确认", "通常无需静脉预处理", "口服", "贫血;恶心;疲乏;骨髓抑制", "PARP抑制", "需核对BRCA检测报告、适应证、血常规和肝肾功能", "CBCS 2026摘要版"),
    ("戈沙妥珠单抗", "晚期TNBC后线或特定HR+/HER2-晚期后线ADC方向，需医生确认", "TNBC/HR+/HER2-", "晚期后线", "戈沙妥珠单抗", "D1、D8，每21天", "戈沙妥珠单抗10mg/kg D1、D8 q21d", "按输注反应、恶心呕吐和中性粒细胞减少风险预处理/支持", "按药物说明书及本院规范", "中性粒细胞减少;腹泻;恶心呕吐;脱发;输注反应", "Trop-2抗体偶联拓扑异构酶I抑制药物", "需关注UGT1A1相关毒性风险、腹泻和骨髓抑制；结合治疗线数使用", "CBCS 2026摘要版/NCCN"),
    ("CDK4/6抑制剂联合内分泌", "HR+/HER2-晚期一线或内分泌敏感场景优先系统治疗方向，需医生确认", "HR+/HER2-", "晚期", "AI/氟维司群;CDK4/6抑制剂", "按具体药物方案", "AI或氟维司群联合哌柏西利/瑞波西利/阿贝西利等；剂量按药品说明书", "按具体药物；关注血常规、肝功能、心电图或腹泻管理", "口服/肌注", "中性粒细胞减少;肝功能异常;腹泻;QT延长;疲乏", "内分泌轴阻断 + 细胞周期抑制", "内脏危象、快速进展或明确内分泌耐药时需MDT讨论是否转化疗", "CBCS 2026摘要版/NCCN"),
    ("卡培他滨", "TNBC新辅助后残余病灶强化、辅助维持或复发转移场景，需医生确认", "TNBC/复发转移等", "辅助强化/晚期", "卡培他滨", "D1-D14 q21d 6-8周期，或节拍维持1年等", "新辅助后强化常见1000-1250mg/m2 bid po D1-D14 q21d；辅助维持可见650mg/m2 bid 1年", "通常无需静脉预处理；按需止吐/止泻", "口服", "手足综合征;腹泻;骨髓抑制;口腔炎;肝功能异常", "氟嘧啶类抗代谢", "需根据肾功能调整；注意手足综合征、腹泻和依从性", "CBCS 2026摘要版/NCCN"),
    ("内分泌治疗方案", "HR阳性相关场景", "HR+", "辅助/晚期", "他莫昔芬;AI;OFS + AI;OFS + 他莫昔芬;氟维司群;CDK4/6抑制剂联合内分泌", "按药物和指南场景", "参考方案需医生确认", "按具体药物", "口服/注射", "潮热;骨密度下降;血栓风险;关节痛;骨髓抑制", "内分泌轴调控及细胞周期抑制", "绝经状态、骨密度、血栓风险、血常规", "内置模板"),
]


def seed_regimens(conn: sqlite3.Connection) -> int:
    changed = 0
    columns = (
        "regimen_name",
        "indication",
        "subtype",
        "setting",
        "drugs",
        "cycle",
        "dose_summary",
        "premedication",
        "dilution",
        "adverse_events",
        "mechanism",
        "caution",
        "source",
    )
    update_columns = columns[1:]
    for template in REGIMEN_TEMPLATES:
        existing = conn.execute("SELECT id FROM chemotherapy_regimens WHERE regimen_name = ? ORDER BY id LIMIT 1", (template[0],)).fetchone()
        if existing:
            assignments = ", ".join(f"{col} = ?" for col in update_columns)
            conn.execute(
                f"UPDATE chemotherapy_regimens SET {assignments} WHERE id = ?",
                (*template[1:], existing["id"]),
            )
        else:
            conn.execute(
                """
                INSERT INTO chemotherapy_regimens
                (regimen_name, indication, subtype, setting, drugs, cycle, dose_summary, premedication, dilution, adverse_events, mechanism, caution, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                template,
            )
        changed += 1
    conn.commit()
    return changed


def list_drugs(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute("SELECT * FROM chemo_drugs ORDER BY drug_class, subclass, generic_name, id").fetchall()]


def get_drug(conn: sqlite3.Connection, drug_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM chemo_drugs WHERE id = ?", (drug_id,)).fetchone()
    return dict(row) if row else None


def _drug_details(conn: sqlite3.Connection, drug_names: str | None) -> list[dict[str, Any]]:
    if not drug_names:
        return []
    names = []
    for item in drug_names.replace("/", ";").split(";"):
        item = item.strip()
        if item and item not in {"多柔比星", "表柔比星", "紫杉醇", "多西他赛"}:
            names.append(item)
        elif item:
            names.append(item)
    details = []
    for name in names:
        row = conn.execute(
            """
            SELECT * FROM chemo_drugs
            WHERE generic_name LIKE ? OR subclass LIKE ? OR brand_name LIKE ?
            ORDER BY id LIMIT 1
            """,
            (f"%{name}%", f"%{name}%", f"%{name}%"),
        ).fetchone()
        if row:
            details.append(dict(row))
    return details


def list_regimens(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    return [with_drug_details(conn, dict(row)) for row in conn.execute("SELECT * FROM chemotherapy_regimens ORDER BY id").fetchall()]


def get_regimen(conn: sqlite3.Connection, regimen_id: int) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM chemotherapy_regimens WHERE id = ?", (regimen_id,)).fetchone()
    return with_drug_details(conn, dict(row)) if row else None


def get_regimens_by_names(conn: sqlite3.Connection, names: list[str]) -> list[dict[str, Any]]:
    regimens = []
    for name in names:
        row = conn.execute("SELECT * FROM chemotherapy_regimens WHERE regimen_name = ?", (name,)).fetchone()
        if row:
            regimens.append(with_drug_details(conn, dict(row)))
    return regimens


def with_drug_details(conn: sqlite3.Connection, regimen: dict[str, Any]) -> dict[str, Any]:
    regimen["drug_details"] = _drug_details(conn, regimen.get("drugs"))
    regimen["caution"] = f"{regimen.get('caution') or ''}。{CHEMO_DISCLAIMER}".strip("。")
    return regimen


def recommend_regimen_names(data: dict[str, Any], genomic_interpretations: list[dict[str, Any]]) -> list[str]:
    her2 = (data.get("her2") or "").lower()
    fish = (data.get("her2_fish") or "").lower()
    hr_positive = (data.get("er_percent") or 0) >= 1 or (data.get("pr_percent") or 0) >= 1
    node_value = str(data.get("clinical_n_stage") or data.get("clinical_node_status") or "").lower()
    node_positive = any(token in node_value for token in ["阳", "n1", "n2", "n3"]) and "n0" not in node_value
    size = data.get("tumor_size_cm") or 0
    grade = str(data.get("histologic_grade") or "")
    lvi = str(data.get("lymphovascular_invasion") or "")
    metastatic = str(data.get("distant_metastasis") or "").lower() in {"有", "m1", "yes", "true"} or "转移" in str(data.get("distant_metastasis") or "")
    if str(data.get("clinical_m_stage") or "").lower() == "cm1":
        metastatic = True
    pdl1_cps = data.get("pdl1_cps")
    brca = str(data.get("brca_status") or "").lower()
    high_genomic = any(item.get("risk_group") in {"高风险", "高危", "High Risk"} or "较大" in item.get("chemo_benefit_hint", "") for item in genomic_interpretations)
    low_genomic = any(item.get("risk_group") in {"低风险", "低危", "Low Risk", "Ultra-low Risk"} for item in genomic_interpretations)

    her2_positive = "3+" in her2 or "阳" in her2 or "positive" in her2 or ("2+" in her2 and ("阳" in fish or "扩增" in fish or "positive" in fish))
    her2_negative = "阴" in her2 or "0" in her2 or "1+" in her2 or "negative" in her2 or ("2+" in her2 and ("阴" in fish or "未扩增" in fish or "negative" in fish))
    high_clinical_risk = bool(node_positive or size >= 2 or "3" in grade or "iii" in grade.lower() or "有" in lvi or "阳" in lvi)

    if metastatic:
        if her2_positive:
            return ["紫杉类+HP", "PCbHP", "T-DXd", "T-DM1", "曲妥珠单抗 + 帕妥珠单抗"]
        if hr_positive and her2_negative:
            names = ["CDK4/6抑制剂联合内分泌", "内分泌治疗方案"]
            if "突变" in brca or "brca1" in brca or "brca2" in brca:
                names.append("奥拉帕利")
            names.extend(["卡培他滨", "戈沙妥珠单抗", "T-DXd"])
            return names
        if not hr_positive and her2_negative:
            names = []
            if pdl1_cps is not None and pdl1_cps >= 10:
                names.extend(["帕博利珠单抗+白蛋白紫杉醇", "特瑞普利单抗+白蛋白紫杉醇"])
            elif pdl1_cps is None:
                names.append("帕博利珠单抗+白蛋白紫杉醇")
            if "突变" in brca or "brca1" in brca or "brca2" in brca:
                names.extend(["奥拉帕利", "氟唑帕利"])
            names.extend(["紫杉类 + 卡铂", "卡培他滨", "戈沙妥珠单抗"])
            return names
        return ["CDK4/6抑制剂联合内分泌", "紫杉类 + 卡铂", "卡培他滨"]

    if her2_positive:
        if size >= 2 or node_positive:
            return ["TCbHP", "EC-THP", "TCHP"]
        return ["TH", "wPH", "曲妥珠单抗 + 帕妥珠单抗"]

    if not hr_positive and her2_negative:
        if size >= 2 or node_positive:
            return ["帕博利珠单抗+PCb-EC", "wPCb-EC", "ddEC-wP", "TCb"]
        return ["TC", "EC-T", "紫杉类 + 卡铂"]

    if hr_positive and ("阴" in her2 or "0" in her2 or "1+" in her2):
        if low_genomic and not node_positive:
            return ["内分泌治疗方案"]
        if high_genomic or high_clinical_risk:
            return ["TC", "EC-T", "ddEC-wP"]
        return ["内分泌治疗方案", "TC"]

    return ["EC-T", "TC"]
