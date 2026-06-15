from __future__ import annotations

import glob
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from sta_lite.core.runner import UserError
from sta_lite.lint.builtin_rules import run_builtin_rules
from sta_lite.lint.lexer import Lexer
from sta_lite.lint.parser import Parser
from sta_lite.lint.preprocessor import Preprocessor
from sta_lite.lint.rule_engine import load_custom_rule_config, run_custom_rules
from sta_lite.lint.symbol_table import build_context
from sta_lite.models.diagnostic import Diagnostic, count_by_severity


LintLogCallback = Callable[[str], None]


@dataclass
class LintConfig:
    rtl: list[str]
    out_dir: str
    top: str | None = None
    include_dirs: list[str] = field(default_factory=list)
    defines: dict[str, str] = field(default_factory=dict)
    rules_file: str | None = None
    sdc_file: str | None = None
    debug: bool = False
    cwd: Path = Path.cwd()


def expand_rtl_files(patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    missing: list[str] = []
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            files.extend(Path(match).resolve() for match in matches if Path(match).is_file())
            continue
        candidate = Path(pattern)
        if candidate.is_file():
            files.append(candidate.resolve())
        else:
            missing.append(pattern)
    if missing:
        raise UserError("找不到 RTL 文件：" + ", ".join(missing))
    deduped: list[Path] = []
    seen: set[Path] = set()
    for file in files:
        if file not in seen:
            deduped.append(file)
            seen.add(file)
    if not deduped:
        raise UserError("没有可用的 RTL 输入文件。")
    return deduped


def run_lint(config: LintConfig, on_log: LintLogCallback | None = None) -> dict[str, Any]:
    started = time.monotonic()
    out_dir = Path(config.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = out_dir / "lint.log"

    log_lines: list[str] = []

    def emit(message: str) -> None:
        log_lines.append(message)
        if on_log:
            on_log(message)

    emit("[sta-lite lint] 开始内部 lint：不会调用 Yosys/OpenSTA/Verilator/Icarus/slang/Verible。")
    rtl_files = expand_rtl_files(config.rtl)
    emit(f"[sta-lite lint] RTL 文件数：{len(rtl_files)}")

    diagnostics: list[Diagnostic] = []
    custom_config = load_custom_rule_config(config.rules_file)
    diagnostics.extend(custom_config.diagnostics)

    preprocess = Preprocessor(config.include_dirs, config.defines).preprocess(rtl_files)
    diagnostics.extend(preprocess.diagnostics)
    emit(f"[sta-lite lint] 预处理完成：输出行数 {len(preprocess.lines)}")

    lex_result = Lexer().lex(preprocess.lines)
    diagnostics.extend(lex_result.diagnostics)
    emit(f"[sta-lite lint] 词法分析完成：token 数 {max(0, len(lex_result.tokens) - 1)}")

    parse_result = Parser(lex_result.tokens).parse()
    diagnostics.extend(parse_result.diagnostics)
    design = parse_result.design
    emit(f"[sta-lite lint] 语法解析完成：模块数 {len(design.modules)}")

    if config.top and config.top not in design.module_names():
        diagnostics.append(
            Diagnostic.make(
                severity="error",
                rule="SEM001_TOP_NOT_FOUND",
                category="semantic",
                file=str(rtl_files[0]),
                line=1,
                column=1,
                message="top module not found",
                message_zh=f"找不到指定顶层模块 `{config.top}`。",
                suggestion_zh="请检查 --top 是否拼写正确，或确认对应 RTL 文件已加入 --rtl。",
                confidence="high",
            )
        )

    context = build_context(design)
    diagnostics.extend(
        run_builtin_rules(
            design=design,
            context=context,
            preprocess=preprocess,
            top=config.top,
            sdc_file=config.sdc_file,
            settings=custom_config.settings,
        )
    )
    custom_diagnostics, custom_results = run_custom_rules(design, context, custom_config.rules)
    diagnostics.extend(custom_diagnostics)

    diagnostics = _attach_source_excerpts(diagnostics)
    elapsed = time.monotonic() - started
    summary = _make_summary(
        config=config,
        rtl_files=rtl_files,
        diagnostics=diagnostics,
        custom_results=custom_results,
        elapsed=elapsed,
        out_dir=out_dir,
    )
    (out_dir / "lint_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if config.debug:
        (out_dir / "tokens.json").write_text(
            json.dumps([token.to_dict() for token in lex_result.tokens], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        (out_dir / "ast.json").write_text(json.dumps(design.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    emit(
        "[sta-lite lint] 完成："
        f"错误 {summary['error_count']}，警告 {summary['warning_count']}，"
        f"unsupported {summary['unsupported_count']}，风险 {summary['risk_level']}。"
    )
    log_path.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    return summary


def _make_summary(
    *,
    config: LintConfig,
    rtl_files: list[Path],
    diagnostics: list[Diagnostic],
    custom_results: list[dict[str, Any]],
    elapsed: float,
    out_dir: Path,
) -> dict[str, Any]:
    counts = count_by_severity(diagnostics)
    unsupported_count = sum(1 for item in diagnostics if item.category == "unsupported" or item.rule.startswith("UNSUPPORTED"))
    error_count = counts["error"]
    warning_count = counts["warning"]
    info_count = counts["info"]
    passed = error_count == 0 and unsupported_count == 0
    if error_count or unsupported_count:
        risk_level = "HIGH"
        risk_text = "存在语法/语义错误或暂不支持的 RTL 构造，后续综合/STA 前需要处理。"
    elif warning_count:
        risk_level = "MEDIUM"
        risk_text = "lint 发现潜在 RTL 风险，建议在进入综合/STA 前审查。"
    else:
        risk_level = "LOW"
        risk_text = "未发现当前规则覆盖范围内的明显 RTL lint 风险。"
    return {
        "tool": "sta_lite_lint",
        "rtl_files": [str(path) for path in rtl_files],
        "top": config.top,
        "include_dirs": [str(Path(item).resolve()) for item in config.include_dirs],
        "defines": config.defines,
        "sdc_file": str(Path(config.sdc_file).resolve()) if config.sdc_file else None,
        "elapsed_seconds": round(elapsed, 3),
        "error_count": error_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "unsupported_count": unsupported_count,
        "diagnostics": [item.to_dict() for item in diagnostics],
        "custom_rule_results": custom_results,
        "passed": passed,
        "risk_level": risk_level,
        "risk_explanation_zh": risk_text,
        "artifacts": {
            "lint_log": str(out_dir / "lint.log"),
            "lint_summary_json": str(out_dir / "lint_summary.json"),
        },
    }


def _attach_source_excerpts(diagnostics: list[Diagnostic]) -> list[Diagnostic]:
    cache: dict[str, list[str]] = {}
    for diagnostic in diagnostics:
        if diagnostic.source_excerpt or diagnostic.file.startswith("<"):
            continue
        path = Path(diagnostic.file)
        if not path.is_file():
            continue
        if diagnostic.file not in cache:
            try:
                cache[diagnostic.file] = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                cache[diagnostic.file] = path.read_text(encoding="latin-1").splitlines()
        lines = cache[diagnostic.file]
        if 1 <= diagnostic.line <= len(lines):
            diagnostic.source_excerpt = lines[diagnostic.line - 1].strip()
    return diagnostics

