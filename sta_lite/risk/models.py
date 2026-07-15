from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


VALID_RISK_SEVERITIES = {"high", "medium", "low"}
VALID_CONFIDENCE = {"high", "medium", "low"}


@dataclass
class RiskDiagnostic:
    rule: str
    severity: str
    category: str
    file: str
    line: int
    column: int
    message_zh: str
    suggestion_zh: str
    confidence: str = "medium"
    module: str | None = None
    evidence: dict[str, Any] = field(default_factory=dict)
    source_excerpt: str | None = None

    def __post_init__(self) -> None:
        if self.severity not in VALID_RISK_SEVERITIES:
            raise ValueError(f"非法风险级别：{self.severity}")
        if self.confidence not in VALID_CONFIDENCE:
            raise ValueError(f"非法置信度：{self.confidence}")
        self.line = max(1, int(self.line or 1))
        self.column = max(1, int(self.column or 1))

    @classmethod
    def make(
        cls,
        *,
        rule: str,
        severity: str,
        category: str,
        file: str | Path,
        line: int,
        column: int,
        message_zh: str,
        suggestion_zh: str,
        confidence: str = "medium",
        module: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> "RiskDiagnostic":
        return cls(
            rule=rule,
            severity=severity,
            category=category,
            file=str(file),
            line=line,
            column=column,
            message_zh=message_zh,
            suggestion_zh=suggestion_zh,
            confidence=confidence,
            module=module,
            evidence=evidence or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": "sta_lite_risk",
            "rule": self.rule,
            "severity": self.severity,
            "category": self.category,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "message_zh": self.message_zh,
            "suggestion_zh": self.suggestion_zh,
            "confidence": self.confidence,
            "module": self.module,
            "evidence": self.evidence,
            "source_excerpt": self.source_excerpt,
        }


def risk_level(diagnostics: list[RiskDiagnostic]) -> str:
    if any(item.severity == "high" for item in diagnostics):
        return "HIGH"
    if any(item.severity == "medium" for item in diagnostics):
        return "MEDIUM"
    return "LOW"


def risk_explanation(level: str, count: int) -> str:
    if count == 0:
        return "未发现当前规则覆盖范围内的明显 RTL 时序风险。"
    if level == "HIGH":
        return "发现高优先级 RTL 时序风险，建议在进入综合、布局布线或 OpenSTA 前先审查。"
    if level == "MEDIUM":
        return "发现中等 RTL 时序风险，建议结合目标频率、约束和后端报告继续确认。"
    return "仅发现低置信或低优先级风险，可作为代码审查提示。"
