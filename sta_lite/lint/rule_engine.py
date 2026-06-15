from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sta_lite.lint.ast_nodes import Design
from sta_lite.lint.symbol_table import DesignContext
from sta_lite.models.diagnostic import Diagnostic


@dataclass
class CustomRuleConfig:
    rules: list[dict[str, Any]]
    settings: dict[str, object]
    diagnostics: list[Diagnostic]


def load_custom_rule_config(path: str | None) -> CustomRuleConfig:
    if not path:
        return CustomRuleConfig(rules=[], settings={}, diagnostics=[])
    rule_path = Path(path)
    if not rule_path.is_file():
        return CustomRuleConfig(
            rules=[],
            settings={},
            diagnostics=[
                Diagnostic.make(
                    severity="error",
                    rule="CUSTOM_RULE_CONFIG",
                    category="custom_rule",
                    file=rule_path,
                    line=1,
                    column=1,
                    message="custom rule file not found",
                    message_zh=f"自定义规则文件不存在：{rule_path}",
                    suggestion_zh="请检查 --rules 指定路径是否正确。",
                    confidence="high",
                )
            ],
        )
    if rule_path.suffix.lower() not in {".json", ""}:
        return CustomRuleConfig(
            rules=[],
            settings={},
            diagnostics=[
                Diagnostic.make(
                    severity="warning",
                    rule="CUSTOM_RULE_UNSUPPORTED",
                    category="unsupported",
                    file=rule_path,
                    line=1,
                    column=1,
                    message="only JSON custom rule config is supported",
                    message_zh="当前版本仅支持 JSON 自定义规则配置。",
                    suggestion_zh="请将规则文件保存为 JSON 格式，例如 custom_rules.json。",
                    confidence="high",
                )
            ],
        )
    try:
        data = json.loads(rule_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return CustomRuleConfig(
            rules=[],
            settings={},
            diagnostics=[
                Diagnostic.make(
                    severity="error",
                    rule="CUSTOM_RULE_CONFIG",
                    category="custom_rule",
                    file=rule_path,
                    line=exc.lineno,
                    column=exc.colno,
                    message="invalid custom rule JSON",
                    message_zh=f"自定义规则 JSON 解析失败：{exc.msg}",
                    suggestion_zh="请检查 JSON 语法，例如逗号、引号和括号是否正确。",
                    confidence="high",
                )
            ],
        )
    rules = data.get("rules", []) if isinstance(data, dict) else []
    settings = data.get("settings", {}) if isinstance(data, dict) else {}
    if not isinstance(rules, list):
        return CustomRuleConfig(
            rules=[],
            settings={},
            diagnostics=[
                Diagnostic.make(
                    severity="error",
                    rule="CUSTOM_RULE_CONFIG",
                    category="custom_rule",
                    file=rule_path,
                    line=1,
                    column=1,
                    message="custom rule config requires rules array",
                    message_zh="自定义规则配置需要 `rules` 数组。",
                    suggestion_zh="请参考 README 中的 custom_rules.json 示例。",
                    confidence="high",
                )
            ],
        )
    return CustomRuleConfig(rules=rules, settings=settings if isinstance(settings, dict) else {}, diagnostics=[])


def run_custom_rules(design: Design, context: DesignContext, rules: list[dict[str, Any]]) -> tuple[list[Diagnostic], list[dict[str, Any]]]:
    diagnostics: list[Diagnostic] = []
    results: list[dict[str, Any]] = []
    for rule in rules:
        rule_id = str(rule.get("id") or "CUSTOM_UNKNOWN")
        severity = str(rule.get("severity") or "warning")
        if severity not in {"error", "warning", "info"}:
            severity = "warning"
        match = rule.get("match") if isinstance(rule.get("match"), dict) else {}
        kind = str(match.get("kind") or "")
        produced: list[Diagnostic] = []
        if kind in {"identifier_regex", "signal_name_regex", "module_name_regex"}:
            produced.extend(_regex_rule(design, context, rule, rule_id, severity, kind, str(match.get("pattern") or "")))
        elif kind == "always_block_kind":
            produced.extend(_always_kind_rule(design, rule, rule_id, severity, str(match.get("value") or "")))
        elif kind == "forbidden_keyword":
            produced.extend(_forbidden_keyword_rule(design, rule, rule_id, severity, str(match.get("keyword") or "")))
        else:
            produced.append(
                Diagnostic.make(
                    severity="warning",
                    rule="CUSTOM_RULE_UNSUPPORTED",
                    category="custom_rule",
                    file="<custom_rules>",
                    line=1,
                    column=1,
                    message="unsupported custom rule match kind",
                    message_zh=f"自定义规则 `{rule_id}` 使用了暂不支持的 match kind：{kind}",
                    suggestion_zh="当前支持 identifier_regex、module_name_regex、signal_name_regex、always_block_kind、forbidden_keyword。",
                    confidence="high",
                )
            )
        diagnostics.extend(produced)
        results.append({"id": rule_id, "match_kind": kind, "hit_count": len(produced)})
    return diagnostics, results


def _regex_rule(
    design: Design,
    context: DesignContext,
    rule: dict[str, Any],
    rule_id: str,
    severity: str,
    kind: str,
    pattern: str,
) -> list[Diagnostic]:
    try:
        regex = re.compile(pattern)
    except re.error as exc:
        return [
            Diagnostic.make(
                severity="error",
                rule="CUSTOM_RULE_CONFIG",
                category="custom_rule",
                file="<custom_rules>",
                line=1,
                column=1,
                message="invalid custom regex",
                message_zh=f"自定义规则 `{rule_id}` 的正则表达式非法：{exc}",
                suggestion_zh="请修正规则中的 pattern 字段。",
                confidence="high",
            )
        ]
    hits: list[tuple[str, str, int, int]] = []
    if kind == "module_name_regex":
        hits.extend((module.name, module.span.file, module.span.line, module.span.column) for module in design.modules if regex.search(module.name))
    elif kind == "signal_name_regex":
        for module_context in context.modules.values():
            for name, signal in module_context.declarations.items():
                if regex.search(name):
                    hits.append((name, signal.span.file, signal.span.line, signal.span.column))
    else:
        seen: set[tuple[str, str, int, int]] = set()
        for module_context in context.modules.values():
            for token in module_context.identifier_tokens:
                key = (token.value, token.file, token.line, token.column)
                if key not in seen and regex.search(token.value):
                    hits.append(key)
                    seen.add(key)
    return [_custom_diag(rule, rule_id, severity, name, file, line, column) for name, file, line, column in hits]


def _always_kind_rule(design: Design, rule: dict[str, Any], rule_id: str, severity: str, value: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for module in design.modules:
        for block in module.always_blocks:
            block_kind = "seq" if block.is_sequential() else "comb" if block.is_combinational() else block.kind
            if value in {block.kind, block_kind}:
                diagnostics.append(_custom_diag(rule, rule_id, severity, block.kind, block.span.file, block.span.line, block.span.column))
    return diagnostics


def _forbidden_keyword_rule(design: Design, rule: dict[str, Any], rule_id: str, severity: str, keyword: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for module in design.modules:
        for token in module.body_tokens:
            if token.value == keyword:
                diagnostics.append(_custom_diag(rule, rule_id, severity, keyword, token.file, token.line, token.column))
    return diagnostics


def _custom_diag(rule: dict[str, Any], rule_id: str, severity: str, name: str, file: str, line: int, column: int) -> Diagnostic:
    return Diagnostic.make(
        severity=severity,
        rule=rule_id,
        category="custom_rule",
        file=file,
        line=line,
        column=column,
        message=f"custom rule hit: {name}",
        message_zh=str(rule.get("message_zh") or f"自定义规则 `{rule_id}` 命中 `{name}`。"),
        suggestion_zh=str(rule.get("suggestion_zh") or "请按团队规则检查该 RTL 写法。"),
        confidence=str(rule.get("confidence") or "medium"),
    )
