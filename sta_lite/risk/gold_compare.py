from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from sta_lite.risk.models import RiskDiagnostic


KEYWORD_TO_CATEGORY = {
    "slack": "timing_setup",
    "violated": "timing_setup",
    "critical path": "timing_setup",
    "latch": "latch_timing",
    "fanout": "fanout_timing",
    "gated clock": "clock_timing",
    "generated clock": "clock_timing",
    "cdc": "cdc_timing",
    "reset": "reset_timing",
    "unconstrained": "constraint_timing",
    "input delay": "constraint_timing",
    "output delay": "constraint_timing",
}


def compare_with_gold(risks: list[RiskDiagnostic], gold_dir: str | Path | None) -> dict[str, Any]:
    if gold_dir is None:
        return {
            "available": False,
            "message_zh": "未配置 OpenSTA/backend gold 报告或目录，已跳过对比。",
        }
    path = Path(gold_dir)
    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = sorted(item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in {".rpt", ".txt", ".log", ".json"})
    else:
        return {
            "available": False,
            "gold_path": str(path),
            "message_zh": "未发现 OpenSTA/backend gold 报告，已跳过对比。",
        }
    if not files:
        return {
            "available": False,
            "gold_path": str(path),
            "message_zh": "OpenSTA/backend gold 目录为空，已跳过对比。",
        }
    text_parts: list[str] = []
    for file in files:
        try:
            text_parts.append(file.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    gold_text = "\n".join(text_parts).lower()
    gold_categories = _gold_categories(gold_text)
    risk_categories = {risk.category for risk in risks}
    confirmed = [risk.rule for risk in risks if risk.category in gold_categories or risk.rule.lower() in gold_text]
    unconfirmed = [risk.rule for risk in risks if risk.rule not in confirmed]
    unpredicted_categories = sorted(gold_categories - risk_categories)
    precision = round(len(set(confirmed)) / max(1, len({risk.rule for risk in risks})), 3) if risks else None
    recall = round(len(gold_categories & risk_categories) / max(1, len(gold_categories)), 3) if gold_categories else None
    return {
        "available": True,
        "gold_path": str(path),
        "gold_files": [str(file) for file in files],
        "gold_categories": sorted(gold_categories),
        "confirmed_risk_rules": sorted(set(confirmed)),
        "unconfirmed_risk_rules": sorted(set(unconfirmed)),
        "gold_categories_not_predicted": unpredicted_categories,
        "category_precision": precision,
        "category_recall": recall,
        "message_zh": "已基于文本关键字完成 OpenSTA/backend gold 粗粒度对比；该结果只用于开发期评估。",
    }


def _gold_categories(text: str) -> set[str]:
    categories: set[str] = set()
    for keyword, category in KEYWORD_TO_CATEGORY.items():
        if keyword in text:
            categories.add(category)
    for match in re.finditer(r"slack\s*[:=]?\s*(-?\d+(?:\.\d+)?)", text):
        if float(match.group(1)) < 0:
            categories.add("timing_setup")
    return categories
