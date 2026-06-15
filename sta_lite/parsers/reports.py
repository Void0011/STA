from __future__ import annotations

import re
from pathlib import Path
from typing import Any


WARNING_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("negative_slack_violation", re.compile(r"slack\s+\(VIOLATED\)|\bslack\b.*-\d", re.IGNORECASE)),
    ("latch_inference", re.compile(r"\blatch\b|Latch inferred", re.IGNORECASE)),
    ("multi_driver", re.compile(r"multi.?driver|multiple drivers|conflicting drivers", re.IGNORECASE)),
    ("unconnected_or_unused", re.compile(r"unconnected|unused|no driver|has no load", re.IGNORECASE)),
    ("missing_module_or_reference", re.compile(r"missing module|not found|unresolved|can't resolve", re.IGNORECASE)),
    ("no_clock_or_missing_clock", re.compile(r"no clock|missing clock|clock.*not found|no clocks", re.IGNORECASE)),
    ("unconstrained_paths", re.compile(r"unconstrained|not constrained|no path", re.IGNORECASE)),
    ("link_error", re.compile(r"link_design|link error|link failed", re.IGNORECASE)),
    ("missing_liberty_cell_or_pin", re.compile(r"cell.*not found|pin.*not found|liberty.*not found|cannot find cell", re.IGNORECASE)),
    ("tool_error", re.compile(r"\bERROR\b|^Error:", re.IGNORECASE)),
    ("tool_warning", re.compile(r"\bWARNING\b|^Warning:", re.IGNORECASE)),
]


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def classify_line(line: str) -> str | None:
    for category, pattern in WARNING_RULES:
        if pattern.search(line):
            return category
    return None


def extract_warnings(text: str) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    explicit_marker = re.compile(r"(^Warning:|^Error:|\bWARNING\b|\bERROR\b)", re.IGNORECASE)
    risk_without_marker = {
        "negative_slack_violation",
        "latch_inference",
        "multi_driver",
        "missing_module_or_reference",
        "no_clock_or_missing_clock",
        "unconstrained_paths",
        "link_error",
        "missing_liberty_cell_or_pin",
    }
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        category = classify_line(line)
        if not category:
            continue
        if not explicit_marker.search(line) and category not in risk_without_marker:
            continue
        key = (category, line)
        if key in seen:
            continue
        warnings.append({"category": category, "message": line})
        seen.add(key)
    return warnings


def parse_metric(path: Path, name: str) -> float | None:
    text = read_text(path)
    match = re.search(rf"\b{name}\s+([-+]?\d+(?:\.\d+)?)", text, re.IGNORECASE)
    if not match:
        return None
    return float(match.group(1))


def parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_worst_paths(checks_rpt: Path) -> list[dict[str, Any]]:
    text = read_text(checks_rpt)
    paths: list[dict[str, Any]] = []
    for block in re.split(r"(?=^Startpoint:)", text, flags=re.MULTILINE):
        if "Startpoint:" not in block:
            continue
        startpoint = re.search(r"^Startpoint:\s*(.+)$", block, re.MULTILINE)
        endpoint = re.search(r"^Endpoint:\s*(.+)$", block, re.MULTILINE)
        path_group = re.search(r"^Path Group:\s*(.+)$", block, re.MULTILINE)
        arrival = re.findall(r"([-+]?\d+(?:\.\d+)?)\s+data arrival time", block)
        required = re.findall(r"([-+]?\d+(?:\.\d+)?)\s+data required time", block)
        slack = re.search(r"([-+]?\d+(?:\.\d+)?)\s+slack\s+\(([^)]+)\)", block)
        paths.append(
            {
                "startpoint": startpoint.group(1).strip() if startpoint else None,
                "endpoint": endpoint.group(1).strip() if endpoint else None,
                "path_group": path_group.group(1).strip() if path_group else None,
                "slack": parse_float(slack.group(1) if slack else None),
                "slack_status": slack.group(2).strip() if slack else None,
                "arrival_time": parse_float(arrival[-1]) if arrival else None,
                "required_time": parse_float(required[-1]) if required else None,
            }
        )
    return paths


def determine_risk(
    wns: float | None,
    tns: float | None,
    worst_paths: list[dict[str, Any]],
    yosys_warnings: list[dict[str, str]],
    opensta_warnings: list[dict[str, str]],
    failure: str | None,
) -> tuple[str, str]:
    hard_categories = {
        "tool_error",
        "missing_module_or_reference",
        "no_clock_or_missing_clock",
        "link_error",
        "missing_liberty_cell_or_pin",
        "negative_slack_violation",
    }
    categories = {item["category"] for item in yosys_warnings + opensta_warnings}
    negative_paths = [path for path in worst_paths if path.get("slack") is not None and path["slack"] < 0]

    if failure:
        return "HIGH", f"流程执行失败：{failure}"
    if wns is not None and wns < 0:
        return "HIGH", f"WNS 为 {wns:.4g} ns，存在 setup 时序违例。"
    if tns is not None and tns < 0:
        return "HIGH", f"TNS 为 {tns:.4g} ns，存在累计负裕量。"
    if negative_paths:
        return "HIGH", f"发现 {len(negative_paths)} 条负 slack 路径，需要优先检查。"
    if categories & hard_categories:
        return "HIGH", "日志中出现缺失模块、缺失时钟、链接错误、负 slack 或工具错误，需要优先处理。"
    if wns is None or tns is None or not worst_paths:
        return "MEDIUM", "未能解析完整 WNS/TNS 或最差路径，建议检查 OpenSTA 报告约束是否完整。"
    if yosys_warnings or opensta_warnings:
        return "MEDIUM", "流程完成但日志中存在警告，建议复核综合和约束质量。"
    return "LOW", "流程完成且未发现负裕量或关键工具警告。"
