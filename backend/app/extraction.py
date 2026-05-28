from __future__ import annotations

import re
from typing import Any


UNKNOWN = "unknown"


def _percent(pattern: str, text: str) -> float | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if not match:
        return None
    return float(match.group(1))


def _ihc_percent(label: str, text: str) -> float | None:
    patterns = [
        rf"{label}\s*[- ]?\s*[:：]?\s*[\(（]?\s*[^0-9%\n]{{0,24}}\s*(\d+(?:\.\d+)?)\s*%",
        rf"{label}\s*[- ]?\s*[:：]?\s*[\(（]?\s*(?:阳性|positive)?\s*[\)）]?\s*(\d+(?:\.\d+)?)\s*%",
        rf"{label}\s*[- ]?\s*[\(（]\s*(\d+(?:\.\d+)?)\s*%\s*[\)）]",
        rf"{label}\s*[- ]?\s*[:：]?\s*(?:约|约为|阳性细胞约)?\s*(\d+(?:\.\d+)?)\s*%",
    ]
    for pattern in patterns:
        value = _percent(pattern, text)
        if value is not None:
            return value
    return None


def _first(patterns: list[str], text: str) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _tumor_size(text: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:cm|厘米)", text, flags=re.IGNORECASE)
    if match:
        return float(match.group(1))
    mm = re.search(r"(\d+(?:\.\d+)?)\s*(?:mm|毫米)", text, flags=re.IGNORECASE)
    if mm:
        return round(float(mm.group(1)) / 10, 2)
    dims = re.search(r"(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)\s*(?:cm|厘米)", text, flags=re.IGNORECASE)
    if dims:
        return max(float(dims.group(1)), float(dims.group(2)))
    dims_mm = re.search(r"(\d+(?:\.\d+)?)\s*[x×*]\s*(\d+(?:\.\d+)?)\s*(?:mm|毫米)", text, flags=re.IGNORECASE)
    if dims_mm:
        return round(max(float(dims_mm.group(1)), float(dims_mm.group(2))) / 10, 2)
    return None


def extract_report(text: str) -> dict[str, Any]:
    compact = (
        text.replace("：", ":")
        .replace("（", "(")
        .replace("）", ")")
        .replace("＋", "+")
        .replace("－", "-")
        .replace("，", ",")
        .replace("；", ";")
    )
    er = _ihc_percent("ER", compact)
    pr = _ihc_percent("PR", compact)
    ki67 = _ihc_percent(r"Ki\s*[- ]?\s*67", compact)
    her2 = _first(
        [
            r"HER\s*[- ]?2\s*[:：]?\s*\(?\s*([0-3]\+|[+]{1,3}|阳性|阴性|positive|negative)\s*\)?",
            r"HER\s*[- ]?2\s*\(([0-3]\+|[+]{1,3})\)",
        ],
        compact,
    )
    if her2 in {"+", "++", "+++"}:
        her2 = {" +": "1+"}.get(her2, None) or {"+": "1+", "++": "2+", "+++": "3+"}[her2]
    her2_fish = None
    fish_sentence = re.search(r"(?:FISH|ISH|原位杂交|HER2基因)[^。\n]*", compact, flags=re.IGNORECASE)
    if fish_sentence and re.search(r"未扩增|阴性|negative", fish_sentence.group(0), flags=re.IGNORECASE):
        her2_fish = "阴性"
    elif fish_sentence and re.search(r"扩增|阳性|positive", fish_sentence.group(0), flags=re.IGNORECASE):
        her2_fish = "阳性"
    if her2_fish is None:
        her2_fish = _first(
            [
                r"(未扩增|阳性|阴性|扩增|positive|negative)[^。\n;；,，]*(?:FISH|ISH|HER2基因扩增|原位杂交)",
            ],
            compact,
        )
    if her2_fish:
        if "未扩增" in her2_fish or "阴" in her2_fish or "negative" in her2_fish.lower():
            her2_fish = "阴性"
        elif "扩增" in her2_fish or "阳" in her2_fish or "positive" in her2_fish.lower():
            her2_fish = "阳性"
    pathology_type = _first(
        [
            r"(浸润性导管癌|浸润性小叶癌|导管原位癌|乳腺癌|黏液癌|髓样癌)",
            r"病理诊断\s*[:：]?\s*([^。\n,，；;]+)",
        ],
        compact,
    )
    node_status = None
    if re.search(r"淋巴结[^。\n]*(未见.*转移|未查见.*转移|无.*转移|阴性|-)", compact):
        node_status = "阴性"
    elif re.search(r"淋巴结[^。\n]*(转移|阳性|\+)", compact):
        node_status = "阳性"

    size = _tumor_size(compact)
    histologic_grade = _first([r"(?:组织学)?(?:分级|级别)\s*[:：]?\s*([IⅡIIⅢIII123一二三]+级?)"], compact)
    lvi = None
    if re.search(r"(脉管癌栓|淋巴血管侵犯)[^。\n]*(阳性|有|见)", compact):
        lvi = "有"
    elif re.search(r"(脉管癌栓|淋巴血管侵犯)[^。\n]*(阴性|无|未见)", compact):
        lvi = "无"

    extracted = {
        "er_percent": er if er is not None else UNKNOWN,
        "pr_percent": pr if pr is not None else UNKNOWN,
        "her2": her2 or UNKNOWN,
        "her2_fish": her2_fish or UNKNOWN,
        "ki67_percent": ki67 if ki67 is not None else UNKNOWN,
        "tumor_size_cm": size if size is not None else UNKNOWN,
        "clinical_node_status": node_status or UNKNOWN,
        "pathology_type": pathology_type or UNKNOWN,
        "histologic_grade": histologic_grade or UNKNOWN,
        "lymphovascular_invasion": lvi or UNKNOWN,
    }
    return extracted


def unknown_fields(extracted: dict[str, Any]) -> list[str]:
    return [key for key, value in extracted.items() if value == UNKNOWN]
