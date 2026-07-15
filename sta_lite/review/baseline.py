from __future__ import annotations

from typing import Any


STATUS_ZH = {
    "supported": "支持",
    "partially_supported": "部分支持",
    "unsupported_diagnostic": "明确诊断不支持",
    "unsupported_by_design": "设计上不支持",
    "not_covered": "未覆盖",
}


def render_coverage_baseline(cases: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    p0 = summary["priorities"]["P0"]
    p1 = summary["priorities"]["P1"]
    lines = [
        "# STA-lite P0/P1 Case 覆盖基线",
        "",
        "> 本文件由 `scripts/generate_coverage_baseline.py` 根据 `sta_lite/review/case_registry.py` 生成；变更登记表后请同步更新并运行 `--check`。",
        "",
        "## 汇总",
        "",
        f"- 总数：{summary['total']}（P0 {p0['total']}，P1 {p1['total']}）",
        f"- P0：支持 {p0['supported']}，部分支持 {p0['partially_supported']}，覆盖率 {p0['coverage_percent']}%",
        f"- P1：支持 {p1['supported']}，部分支持 {p1['partially_supported']}，覆盖率 {p1['coverage_percent']}%",
        f"- Owner：lint {summary['owner_counts']['lint']}，profiling {summary['owner_counts']['profiling']}，both {summary['owner_counts']['both']}",
        "",
        "## 逐项基线",
        "",
        "| Case ID | 名称 | Owner | 状态 | 内部规则 | 验证证据 | Golden/reference | 后续边界 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in cases:
        golden = item.get("golden_reference") or {}
        rules = "<br>".join(item.get("rule_ids") or ["-"])
        evidence = "<br>".join(item.get("test_paths") or ["-"])
        next_step = _escape(str(item.get("next_improvement_zh") or "-"))
        lines.append(
            "| {case_id} | {name} | {owner} | {status} | {rules} | {evidence} | {golden} | {next_step} |".format(
                case_id=item["case_id"],
                name=_escape(str(item["name_zh"])),
                owner=item["owner"],
                status=STATUS_ZH.get(str(item["support_status"]), str(item["support_status"])),
                rules=rules,
                evidence=evidence,
                golden=_escape(str(golden.get("status") or "not_configured")),
                next_step=next_step,
            )
        )
    lines.extend(
        [
            "",
            "## 诚实边界",
            "",
            "- `P0_FSM_ROBUSTNESS` 保持“部分支持”：当前只覆盖清晰的两进程 FSM 子集，不宣称支持 one-process FSM、复杂 enum/package、generate FSM 或完整可达性分析。",
            "- P1 的“支持”均指已文档化的 RTL 结构筛查范围，不代表目标器件推断、物理扇出、CDC signoff 或真实 STA slack 结论。",
            "- Yosys、OpenSTA、Verilator 等仅用于 Backend 页面或测试/开发期 reference；内部 lint、profiling、Review、Coverage 的生产运行不依赖这些工具。",
            "",
        ]
    )
    return "\n".join(lines)


def _escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", "<br>")
