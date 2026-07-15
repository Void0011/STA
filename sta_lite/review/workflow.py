from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from sta_lite.core.errors import UserError
from sta_lite.lint.workflow import LintConfig, run_lint
from sta_lite.review.case_registry import case_registry, classify_diagnostic, coverage_summary
from sta_lite.review.coverage import p0_coverage, p0_coverage_summary, p1_roadmap, report_location_status
from sta_lite.risk.workflow import RiskConfig, run_risk


ReviewLogCallback = Callable[[str], None]


@dataclass
class ReviewConfig:
    rtl: list[str]
    out_dir: str
    top: str | None = None
    sdc_file: str | None = None
    include_dirs: list[str] = field(default_factory=list)
    defines: dict[str, str] = field(default_factory=dict)
    rules_file: str | None = None
    gold_dir: str | None = None
    debug: bool = False


def run_review(config: ReviewConfig, on_log: ReviewLogCallback | None = None) -> dict[str, Any]:
    started = time.monotonic()
    out_dir = Path(config.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "review.log"
    log_lines: list[str] = []

    def emit(message: str) -> None:
        log_lines.append(message)
        if on_log:
            on_log(message)

    emit("[sta-lite review] 开始 RTL Review：内部 lint_v0 + RTL timing-risk profiling。")
    emit("[sta-lite review] 该流程不会调用 Yosys/OpenSTA/OpenROAD/Vivado/Quartus 或商业 EDA 工具。")

    lint_dir = out_dir / "lint"
    risk_dir = out_dir / "risk"
    lint_summary: dict[str, Any] | None = None
    lint_error_zh: str | None = None
    lint_started = time.monotonic()
    try:
        lint_summary = run_lint(
            LintConfig(
                rtl=config.rtl,
                out_dir=str(lint_dir),
                top=config.top,
                include_dirs=config.include_dirs,
                defines=config.defines,
                rules_file=config.rules_file,
                sdc_file=config.sdc_file,
                debug=config.debug,
            ),
            on_log=emit,
        )
        emit("[sta-lite review] RTL Lint 阶段完成，继续运行 RTL Timing Risk Profiling。")
    except UserError as exc:
        lint_error_zh = str(exc)
        emit(f"[sta-lite review] RTL Lint 阶段未完成：{lint_error_zh}")
    except Exception as exc:  # noqa: BLE001 - review must preserve the other sub-flow.
        lint_error_zh = f"RTL Lint 阶段内部错误：{exc}"
        emit(f"[sta-lite review] {lint_error_zh}")
    lint_elapsed = time.monotonic() - lint_started

    risk_summary: dict[str, Any] | None = None
    risk_error_zh: str | None = None
    risk_started = time.monotonic()
    try:
        risk_summary = run_risk(
            RiskConfig(
                rtl=config.rtl,
                out_dir=str(risk_dir),
                top=config.top,
                sdc_file=config.sdc_file,
                include_dirs=config.include_dirs,
                defines=config.defines,
                gold_dir=config.gold_dir or None,
            ),
            on_log=emit,
        )
    except UserError as exc:
        risk_error_zh = str(exc)
        emit(f"[sta-lite review] RTL risk 阶段未完成：{risk_error_zh}")
    except Exception as exc:  # noqa: BLE001 - review should still expose lint result.
        risk_error_zh = f"RTL risk 阶段内部错误：{exc}"
        emit(f"[sta-lite review] {risk_error_zh}")
    risk_elapsed = time.monotonic() - risk_started

    elapsed = time.monotonic() - started
    summary = _make_summary(
        config=config,
        lint_summary=lint_summary,
        lint_error_zh=lint_error_zh,
        lint_elapsed=lint_elapsed,
        risk_summary=risk_summary,
        risk_error_zh=risk_error_zh,
        risk_elapsed=risk_elapsed,
        elapsed=elapsed,
        out_dir=out_dir,
    )
    summary_path = out_dir / "review_summary.json"
    report_path = out_dir / "review_report.md"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    emit(f"[sta-lite review] 已写出 summary：{summary_path}")
    emit(f"[sta-lite review] 已写出报告：{report_path}")
    emit(
        "[sta-lite review] 完成："
        f"lint 问题 {summary['lint_issue_count']}，risk 风险 {summary['risk_count']}，"
        f"总计 {summary['total_issue_count']}，整体等级 {summary['risk_level']}。"
    )
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return summary


def _make_summary(
    *,
    config: ReviewConfig,
    lint_summary: dict[str, Any] | None,
    lint_error_zh: str | None,
    lint_elapsed: float,
    risk_summary: dict[str, Any] | None,
    risk_error_zh: str | None,
    risk_elapsed: float,
    elapsed: float,
    out_dir: Path,
) -> dict[str, Any]:
    lint_items = [_lint_item(item) for item in (lint_summary or {}).get("diagnostics", []) if isinstance(item, dict)]
    risk_items = [_risk_item(item) for item in (risk_summary or {}).get("risks", []) if isinstance(item, dict)]
    runtime_items: list[dict[str, Any]] = []
    if lint_error_zh:
        runtime_items.append(_runtime_item("lint", "LINT_WORKFLOW_BLOCKED", lint_error_zh))
    if risk_error_zh:
        runtime_items.append(_runtime_item("profiling", "RISK_WORKFLOW_BLOCKED", risk_error_zh))

    items = _correlate_items(lint_items + risk_items + runtime_items)
    lint_error_count = int((lint_summary or {}).get("error_count") or 0)
    lint_warning_count = int((lint_summary or {}).get("warning_count") or 0)
    lint_unsupported_count = int((lint_summary or {}).get("unsupported_count") or 0)
    lint_issue_count = len((lint_summary or {}).get("diagnostics", []))
    risk_count = int((risk_summary or {}).get("risk_count") or 0)
    total_issue_count = lint_issue_count + risk_count + len(runtime_items)
    level = _overall_level(
        (lint_summary or {}).get("risk_level"),
        (risk_summary or {}).get("risk_level"),
        lint_error_count,
        lint_unsupported_count,
        int(bool(lint_error_zh)) + int(bool(risk_error_zh)),
    )
    lint_status = "success" if lint_summary is not None else "failure"
    profiling_status = "success" if risk_summary is not None else "failure"
    if lint_status == "success" and profiling_status == "success":
        run_status = "success"
    elif lint_status == "success" or profiling_status == "success":
        run_status = "partial_success"
    else:
        run_status = "failure"
    artifacts = {
        "review_log": str(out_dir / "review.log"),
        "review_summary_json": str(out_dir / "review_summary.json"),
        "review_report_md": str(out_dir / "review_report.md"),
        "lint_log": (lint_summary or {}).get("artifacts", {}).get("lint_log") if isinstance((lint_summary or {}).get("artifacts"), dict) else None,
        "lint_summary_json": (lint_summary or {}).get("artifacts", {}).get("lint_summary_json") if isinstance((lint_summary or {}).get("artifacts"), dict) else None,
    }
    if isinstance((risk_summary or {}).get("artifacts"), dict):
        artifacts.update(
            {
                "risk_log": risk_summary["artifacts"].get("risk_log"),
                "risk_summary_json": risk_summary["artifacts"].get("risk_summary_json"),
                "risk_report_md": risk_summary["artifacts"].get("risk_report_md"),
            }
        )
    return {
        "tool": "sta_lite_review",
        "status": run_status,
        "rtl_files": (lint_summary or {}).get("rtl_files") or (risk_summary or {}).get("rtl_files", []),
        "top": config.top,
        "sdc_file": (lint_summary or {}).get("sdc_file") or ((risk_summary or {}).get("sdc_file")),
        "include_dirs": (lint_summary or {}).get("include_dirs") or (risk_summary or {}).get("include_dirs", []),
        "defines": config.defines,
        "elapsed_seconds": round(elapsed, 3),
        "lint_issue_count": lint_issue_count,
        "lint_error_count": lint_error_count,
        "lint_warning_count": lint_warning_count,
        "lint_unsupported_count": lint_unsupported_count,
        "risk_count": risk_count,
        "runtime_error_count": len(runtime_items),
        "total_issue_count": total_issue_count,
        "risk_level": level,
        "risk_explanation_zh": _risk_explanation(level, lint_issue_count, risk_count, len(runtime_items)),
        "subflows": {
            "lint": {
                "status": lint_status,
                "elapsed_seconds": round(lint_elapsed, 3),
                "issue_count": lint_issue_count,
                "error_zh": lint_error_zh,
            },
            "profiling": {
                "status": profiling_status,
                "elapsed_seconds": round(risk_elapsed, 3),
                "issue_count": risk_count,
                "error_zh": risk_error_zh,
            },
        },
        "items": items,
        "lint_summary": lint_summary,
        "lint_error_zh": lint_error_zh,
        "risk_summary": risk_summary,
        "risk_error_zh": risk_error_zh,
        "gold_compare": (risk_summary or {}).get("gold_compare"),
        "case_registry": case_registry(),
        "coverage_summary": coverage_summary(),
        "p0_coverage": p0_coverage(),
        "p0_coverage_summary": p0_coverage_summary(),
        "p1_roadmap": p1_roadmap(),
        "report_location_status": report_location_status(),
        "artifacts": artifacts,
    }


def _lint_item(item: dict[str, Any]) -> dict[str, Any]:
    classification = classify_diagnostic(item.get("rule"), item.get("category"), "lint") or {}
    evidence = {
        "tool": item.get("tool") or "sta_lite_lint",
        "category": item.get("category"),
        "message": item.get("message"),
    }
    if isinstance(item.get("evidence"), dict):
        evidence.update(item["evidence"])
    if item.get("source_excerpt"):
        evidence["source_excerpt"] = item.get("source_excerpt")
    return {
        "source": "lint",
        "rule": item.get("rule"),
        "case_id": classification.get("case_id"),
        "case_name_zh": classification.get("case_name_zh"),
        "priority": classification.get("priority"),
        "category": classification.get("case_category") or item.get("category"),
        "owner": classification.get("owner"),
        "support_status": classification.get("support_status"),
        "related_case_ids": classification.get("related_case_ids", []),
        "severity": item.get("severity"),
        "file": item.get("file"),
        "line": item.get("line"),
        "column": item.get("column"),
        "confidence": item.get("confidence") or "medium",
        "message_zh": item.get("message_zh"),
        "suggestion_zh": item.get("suggestion_zh"),
        "evidence": evidence,
    }


def _risk_item(item: dict[str, Any]) -> dict[str, Any]:
    classification = classify_diagnostic(item.get("rule"), item.get("category"), "profiling") or {}
    evidence = dict(item.get("evidence") or {})
    evidence["tool"] = item.get("tool") or "sta_lite_risk"
    evidence["category"] = item.get("category")
    if item.get("module"):
        evidence["module"] = item.get("module")
    if item.get("source_excerpt"):
        evidence["source_excerpt"] = item.get("source_excerpt")
    return {
        "source": "profiling",
        "rule": item.get("rule"),
        "case_id": classification.get("case_id"),
        "case_name_zh": classification.get("case_name_zh"),
        "priority": classification.get("priority"),
        "category": classification.get("case_category") or item.get("category"),
        "owner": classification.get("owner"),
        "support_status": classification.get("support_status"),
        "related_case_ids": classification.get("related_case_ids", []),
        "severity": item.get("severity"),
        "file": item.get("file"),
        "line": item.get("line"),
        "column": item.get("column"),
        "confidence": item.get("confidence") or "medium",
        "message_zh": item.get("message_zh"),
        "suggestion_zh": item.get("suggestion_zh"),
        "evidence": evidence,
    }


def _runtime_item(source: str, rule: str, message_zh: str) -> dict[str, Any]:
    return {
        "source": source,
        "rule": rule,
        "case_id": None,
        "case_name_zh": None,
        "priority": None,
        "category": "workflow",
        "owner": source,
        "support_status": None,
        "related_case_ids": [],
        "severity": "high" if source == "profiling" else "error",
        "file": f"<{source}>",
        "line": 1,
        "column": 1,
        "confidence": "high",
        "message_zh": message_zh,
        "suggestion_zh": "请检查该子流程的输入、top、规则配置和 RTL 文件，然后重新运行 RTL Review。",
        "evidence": {"stage": source, "error_zh": message_zh},
    }


def _correlate_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[object, object, object], list[dict[str, Any]]] = {}
    for item in items:
        case_id = item.get("case_id") or item.get("rule")
        key = (case_id, item.get("file"), item.get("line"))
        groups.setdefault(key, []).append(item)
    for index, group in enumerate(groups.values(), start=1):
        sources = sorted({str(item.get("source")) for item in group})
        correlation_id = f"CORR-{index:04d}"
        for item in group:
            item["correlation_id"] = correlation_id
            item["correlated_sources"] = sources
            item["overlap_count"] = len(group)
    return items


def _overall_level(
    lint_level: object,
    risk_level: object,
    lint_error_count: int,
    lint_unsupported_count: int,
    runtime_error_count: int,
) -> str:
    levels = {str(lint_level or "LOW"), str(risk_level or "LOW")}
    if lint_error_count or lint_unsupported_count or runtime_error_count or "HIGH" in levels:
        return "HIGH"
    if "MEDIUM" in levels:
        return "MEDIUM"
    return "LOW"


def _risk_explanation(level: str, lint_issue_count: int, risk_count: int, runtime_error_count: int) -> str:
    if runtime_error_count:
        return "RTL Review 的 risk 阶段未完整完成，通常需要先处理 lint/top/输入问题。"
    if level == "HIGH":
        return "发现高优先级 lint 或 RTL timing-risk 问题，建议进入综合/后端前先处理。"
    if level == "MEDIUM":
        return "发现需要代码审查的 lint 或 RTL timing-risk 提示，建议结合目标频率和约束确认。"
    if lint_issue_count == 0 and risk_count == 0:
        return "当前 lint_v0 与 P0 risk 规则未发现明显问题；这不等价于 signoff STA 通过。"
    return "仅发现低优先级提示，可作为代码审查参考。"


def _render_report(summary: dict[str, Any]) -> str:
    artifacts = summary.get("artifacts") if isinstance(summary.get("artifacts"), dict) else {}
    lines = [
        "# STA-lite RTL Review 报告",
        "",
        f"- 顶层模块：{summary.get('top') or '未指定'}",
        f"- RTL 文件数：{len(summary.get('rtl_files', []))}",
        f"- 耗时：{summary.get('elapsed_seconds')} 秒",
        f"- lint 问题数：{summary.get('lint_issue_count')}",
        f"- risk 风险数：{summary.get('risk_count')}",
        f"- 总问题数：{summary.get('total_issue_count')}",
        f"- 整体等级：{summary.get('risk_level')}",
        f"- RTL Lint 状态：{summary.get('subflows', {}).get('lint', {}).get('status')}",
        f"- RTL Timing Risk Profiling 状态：{summary.get('subflows', {}).get('profiling', {}).get('status')}",
        f"- 说明：{summary.get('risk_explanation_zh')}",
        "",
        "## 输出文件",
        "",
        f"- review_summary.json：{artifacts.get('review_summary_json') or '-'}",
        f"- review_report.md：{artifacts.get('review_report_md') or '-'}",
        f"- review.log：{artifacts.get('review_log') or '-'}",
        f"- lint_summary.json：{artifacts.get('lint_summary_json') or '-'}",
        f"- risk_summary.json：{artifacts.get('risk_summary_json') or '-'}",
        "",
        "## Lint/Risk 诊断",
        "",
    ]
    items = summary.get("items", [])
    if not items:
        lines.append("当前规则未发现明显 lint 或 RTL timing-risk 问题。")
    elif isinstance(items, list):
        for index, item in enumerate(items[:120], start=1):
            if not isinstance(item, dict):
                continue
            lines.extend(
                [
                    f"### {index}. [{item.get('source')}] {item.get('rule')}",
                    "",
                    f"- Case：{item.get('case_id') or '-'} / {item.get('priority') or '-'}",
                    f"- 类别：{item.get('category') or '-'}",
                    f"- 级别：{item.get('severity')}",
                    f"- 位置：{item.get('file')}:{item.get('line')}:{item.get('column')}",
                    f"- 置信度：{item.get('confidence')}",
                    f"- 说明：{item.get('message_zh')}",
                    f"- 建议：{item.get('suggestion_zh')}",
                    f"- 证据：`{json.dumps(item.get('evidence') or {}, ensure_ascii=False)}`",
                    "",
                ]
            )
        if len(items) > 120:
            lines.append(f"其余 {len(items) - 120} 条请查看 review_summary.json。")
    lines.extend(["", "## P0 覆盖状态", ""])
    for item in summary.get("p0_coverage", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- {item.get('case_id')} {item.get('name_zh')}："
            f"{item.get('support_status')}，owner={item.get('owner')}，test={item.get('test_status')}。"
        )
    lines.extend(["", "## P1 路线图", ""])
    for item in summary.get("p1_roadmap", []):
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- {item.get('case_id')} {item.get('name_zh')}："
            f"{item.get('support_status')}，owner={item.get('owner')}，test={item.get('test_status')}。"
        )
    location = summary.get("report_location_status")
    if isinstance(location, dict):
        lines.extend(
            [
                "",
                "## 后端报告反向定位状态",
                "",
                location.get("message_zh", ""),
                "",
                f"下一步：{location.get('next_step_zh') or '-'}",
                "",
            ]
        )
    lines.extend(
        [
            "## 限制",
            "",
            "RTL Review 是综合/STA 前的早期风险检查，不等价于 signoff STA。它不建模真实单元延迟、布线 RC、时钟树、PVT、MCMM 或完整 CDC/RDC。",
            "",
        ]
    )
    return "\n".join(lines)
