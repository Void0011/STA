from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from sta_lite.core.errors import UserError
from sta_lite.lint.lexer import Lexer
from sta_lite.lint.parser import Parser
from sta_lite.lint.preprocessor import Preprocessor
from sta_lite.lint.symbol_table import build_context
from sta_lite.lint.workflow import expand_rtl_files
from sta_lite.risk.builtin_rules import run_builtin_risk_rules
from sta_lite.risk.feature_extractor import extract_features
from sta_lite.risk.gold_compare import compare_with_gold
from sta_lite.risk.models import RiskDiagnostic, risk_explanation, risk_level


RiskLogCallback = Callable[[str], None]


@dataclass
class RiskConfig:
    rtl: list[str]
    out_dir: str
    top: str | None = None
    sdc_file: str | None = None
    include_dirs: list[str] = field(default_factory=list)
    defines: dict[str, str] = field(default_factory=dict)
    gold_dir: str | None = "risk_profile/gold/opensta"
    settings: dict[str, object] = field(default_factory=dict)


def run_risk(config: RiskConfig, on_log: RiskLogCallback | None = None) -> dict[str, Any]:
    started = time.monotonic()
    out_dir = Path(config.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "risk.log"
    log_lines: list[str] = []

    def emit(message: str) -> None:
        log_lines.append(message)
        if on_log:
            on_log(message)

    emit("[sta-lite risk] 开始 RTL timing-risk profiling：不会调用 Yosys/OpenSTA/OpenROAD/Vivado/Quartus。")
    rtl_files = expand_rtl_files(config.rtl)
    emit(f"[sta-lite risk] RTL 文件数：{len(rtl_files)}")

    parse_notes: list[dict[str, Any]] = []
    preprocess = Preprocessor(config.include_dirs, config.defines).preprocess(rtl_files)
    parse_notes.extend(item.to_dict() for item in preprocess.diagnostics)
    emit(f"[sta-lite risk] 预处理完成：输出行数 {len(preprocess.lines)}")

    lex_result = Lexer().lex(preprocess.lines)
    parse_notes.extend(item.to_dict() for item in lex_result.diagnostics)
    emit(f"[sta-lite risk] 词法分析完成：token 数 {max(0, len(lex_result.tokens) - 1)}")

    parse_result = Parser(lex_result.tokens).parse()
    parse_notes.extend(item.to_dict() for item in parse_result.diagnostics)
    design = parse_result.design
    emit(f"[sta-lite risk] 语法解析完成：模块数 {len(design.modules)}")
    if config.top and config.top not in design.module_names():
        raise UserError(f"找不到指定顶层模块 `{config.top}`。请检查 --top 或 --rtl 输入。")

    context = build_context(design)
    features = extract_features(design, context, config.top, config.sdc_file)
    risks = run_builtin_risk_rules(features, config.settings)
    risks = _attach_source_excerpts(risks)
    emit(f"[sta-lite risk] 内置风险规则完成：发现 {len(risks)} 条风险。")

    gold_compare = compare_with_gold(risks, config.gold_dir)
    emit(f"[sta-lite risk] gold 对比：{gold_compare.get('message_zh')}")

    elapsed = time.monotonic() - started
    summary = _make_summary(
        config=config,
        rtl_files=rtl_files,
        parse_notes=parse_notes,
        risks=risks,
        elapsed=elapsed,
        out_dir=out_dir,
        gold_compare=gold_compare,
    )
    summary_path = out_dir / "risk_summary.json"
    report_path = out_dir / "risk_report.md"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(summary), encoding="utf-8")
    emit(f"[sta-lite risk] 已写出 summary：{summary_path}")
    emit(f"[sta-lite risk] 已写出报告：{report_path}")
    emit(f"[sta-lite risk] 完成：风险等级 {summary['risk_level']}，风险数 {summary['risk_count']}。")
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return summary


def _make_summary(
    *,
    config: RiskConfig,
    rtl_files: list[Path],
    parse_notes: list[dict[str, Any]],
    risks: list[RiskDiagnostic],
    elapsed: float,
    out_dir: Path,
    gold_compare: dict[str, Any],
) -> dict[str, Any]:
    level = risk_level(risks)
    return {
        "tool": "sta_lite_risk",
        "rtl_files": [str(path) for path in rtl_files],
        "top": config.top,
        "sdc_file": str(Path(config.sdc_file).resolve()) if config.sdc_file else None,
        "include_dirs": [str(Path(item).resolve()) for item in config.include_dirs],
        "defines": config.defines,
        "elapsed_seconds": round(elapsed, 3),
        "risk_count": len(risks),
        "risks": [risk.to_dict() for risk in risks],
        "parse_note_count": len(parse_notes),
        "parse_notes": parse_notes,
        "risk_level": level,
        "risk_explanation_zh": risk_explanation(level, len(risks)),
        "gold_compare": gold_compare,
        "artifacts": {
            "risk_log": str(out_dir / "risk.log"),
            "risk_summary_json": str(out_dir / "risk_summary.json"),
            "risk_report_md": str(out_dir / "risk_report.md"),
        },
    }


def _render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# STA-lite RTL 时序风险报告",
        "",
        f"- 顶层模块：{summary.get('top') or '未指定'}",
        f"- RTL 文件数：{len(summary.get('rtl_files', []))}",
        f"- SDC：{summary.get('sdc_file') or '未提供'}",
        f"- 耗时：{summary.get('elapsed_seconds')} 秒",
        f"- 风险等级：{summary.get('risk_level')}",
        f"- 风险数量：{summary.get('risk_count')}",
        f"- 说明：{summary.get('risk_explanation_zh')}",
        "",
        "## 风险列表",
        "",
    ]
    risks = summary.get("risks", [])
    if not risks:
        lines.append("当前规则未发现明显 RTL 时序风险。")
    elif isinstance(risks, list):
        for index, risk in enumerate(risks, start=1):
            if not isinstance(risk, dict):
                continue
            lines.extend(
                [
                    f"### {index}. {risk.get('rule')}",
                    "",
                    f"- 级别：{risk.get('severity')}",
                    f"- 类别：{risk.get('category')}",
                    f"- 位置：{risk.get('file')}:{risk.get('line')}:{risk.get('column')}",
                    f"- 模块：{risk.get('module') or '-'}",
                    f"- 诊断：{risk.get('message_zh')}",
                    f"- 建议：{risk.get('suggestion_zh')}",
                    f"- 置信度：{risk.get('confidence')}",
                    f"- 证据：`{json.dumps(risk.get('evidence') or {}, ensure_ascii=False)}`",
                    "",
                ]
            )
            excerpt = risk.get("source_excerpt")
            if excerpt:
                lines.extend(["源码片段：", "", f"```verilog\n{excerpt}\n```", ""])
    gold = summary.get("gold_compare")
    lines.extend(["## Gold 对比", ""])
    if isinstance(gold, dict):
        lines.append(gold.get("message_zh", "未执行 gold 对比。"))
        if gold.get("available"):
            lines.append("")
            lines.append(f"- gold 类别：{', '.join(gold.get('gold_categories', [])) or '-'}")
            lines.append(f"- STA-lite 命中规则：{', '.join(gold.get('confirmed_risk_rules', [])) or '-'}")
            lines.append(f"- gold 未预测类别：{', '.join(gold.get('gold_categories_not_predicted', [])) or '-'}")
    lines.extend(
        [
            "",
            "## 限制",
            "",
            "本报告是 RTL 阶段启发式风险筛查，不等价于 signoff STA。它不建模真实单元延迟、布线 RC、时钟树、PVT 或 MCMM；后续仍需使用综合、布局布线和 OpenSTA/厂商 STA 报告确认。",
            "",
        ]
    )
    return "\n".join(lines)


def _attach_source_excerpts(risks: list[RiskDiagnostic]) -> list[RiskDiagnostic]:
    cache: dict[str, list[str]] = {}
    for risk in risks:
        if risk.source_excerpt or risk.file.startswith("<"):
            continue
        path = Path(risk.file)
        if not path.is_file():
            continue
        if risk.file not in cache:
            try:
                cache[risk.file] = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                cache[risk.file] = path.read_text(encoding="latin-1").splitlines()
        lines = cache[risk.file]
        if 1 <= risk.line <= len(lines):
            risk.source_excerpt = lines[risk.line - 1].strip()
    return risks
