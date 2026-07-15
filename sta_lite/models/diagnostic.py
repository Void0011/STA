from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


VALID_SEVERITIES = {"error", "warning", "info"}
VALID_CONFIDENCE = {"high", "medium", "low"}


@dataclass(frozen=True)
class SourceLocation:
    file: str
    line: int
    column: int


@dataclass
class Diagnostic:
    tool: str
    severity: str
    rule: str
    category: str
    file: str
    line: int
    column: int
    message: str
    message_zh: str
    suggestion_zh: str
    confidence: str = "medium"
    source_excerpt: str | None = None
    evidence: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(f"非法诊断级别：{self.severity}")
        if self.confidence not in VALID_CONFIDENCE:
            raise ValueError(f"非法置信度：{self.confidence}")

    @classmethod
    def make(
        cls,
        *,
        severity: str,
        rule: str,
        category: str,
        file: str | Path,
        line: int,
        column: int,
        message: str,
        message_zh: str,
        suggestion_zh: str,
        confidence: str = "medium",
        source_excerpt: str | None = None,
        evidence: dict[str, Any] | None = None,
    ) -> "Diagnostic":
        return cls(
            tool="sta_lite_lint",
            severity=severity,
            rule=rule,
            category=category,
            file=str(file),
            line=max(1, int(line or 1)),
            column=max(1, int(column or 1)),
            message=message,
            message_zh=message_zh,
            suggestion_zh=suggestion_zh,
            confidence=confidence,
            source_excerpt=source_excerpt,
            evidence=evidence,
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "tool": self.tool,
            "severity": self.severity,
            "rule": self.rule,
            "category": self.category,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "message": self.message,
            "message_zh": self.message_zh,
            "suggestion_zh": self.suggestion_zh,
            "confidence": self.confidence,
            "source_excerpt": self.source_excerpt,
        }
        if self.evidence:
            result["evidence"] = self.evidence
        return result


def count_by_severity(diagnostics: list[Diagnostic]) -> dict[str, int]:
    return {
        "error": sum(1 for item in diagnostics if item.severity == "error"),
        "warning": sum(1 for item in diagnostics if item.severity == "warning"),
        "info": sum(1 for item in diagnostics if item.severity == "info"),
    }
