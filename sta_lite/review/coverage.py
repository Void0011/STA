from __future__ import annotations

from typing import Any

from sta_lite.review.case_registry import case_registry, coverage_summary


def p0_coverage() -> list[dict[str, Any]]:
    return [item for item in case_registry() if item["priority"] == "P0"]


def p1_roadmap() -> list[dict[str, Any]]:
    return [item for item in case_registry() if item["priority"] == "P1"]


def p0_coverage_summary() -> dict[str, Any]:
    return coverage_summary()["priorities"]["P0"]


def report_location_status() -> dict[str, Any]:
    return {
        "feature": "backend_report_to_rtl_location",
        "status": "todo",
        "message_zh": (
            "当前版本已在后端参考分析中解析 OpenSTA startpoint、endpoint、slack、"
            "path group 和报告文件路径；尚未完成 netlist path/token 到 RTL 源码行的可靠反向映射。"
        ),
        "direction": [
            "backend report path/token",
            "module/instance/signal/register name",
            "RTL source index",
            "likely file/line candidate",
            "confidence/evidence",
        ],
        "next_step_zh": "下一步应新增 sta_lite/mapping 源码索引与候选排序，并在后端违例表中显示 RTL 候选位置。",
    }
