from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sta_lite.lint.lexer import Token


@dataclass
class Signal:
    name: str
    direction: str | None
    data_type: str | None
    span: Token
    width: str | None = None
    signedness: str = "unsigned"
    value: str | None = None


@dataclass
class Assignment:
    target: str
    op: str
    expr_tokens: list[Token]
    span: Token
    context: str


@dataclass
class AlwaysBlock:
    kind: str
    sensitivity_tokens: list[Token]
    body_tokens: list[Token]
    assignments: list[Assignment]
    span: Token

    def is_sequential(self) -> bool:
        if self.kind == "always_ff":
            return True
        values = {token.value for token in self.sensitivity_tokens}
        return "posedge" in values or "negedge" in values

    def is_combinational(self) -> bool:
        if self.kind in {"always_comb", "always_latch"}:
            return True
        if self.kind != "always":
            return False
        if self.is_sequential():
            return False
        return True


@dataclass
class Instance:
    module_type: str
    instance_name: str
    connection_tokens: list[Token]
    span: Token


@dataclass
class GenerateBlock:
    kind: str
    name: str | None
    body_tokens: list[Token]
    assignments: list[Assignment]
    instances: list[Instance]
    span: Token


@dataclass
class FunctionDecl:
    name: str
    automatic: bool
    body_tokens: list[Token]
    assignments: list[Assignment]
    span: Token


@dataclass
class TaskDecl:
    name: str
    automatic: bool
    body_tokens: list[Token]
    assignments: list[Assignment]
    span: Token


@dataclass
class Module:
    name: str
    span: Token
    ports: dict[str, Signal] = field(default_factory=dict)
    declarations: dict[str, Signal] = field(default_factory=dict)
    parameters: dict[str, Signal] = field(default_factory=dict)
    continuous_assigns: list[Assignment] = field(default_factory=list)
    always_blocks: list[AlwaysBlock] = field(default_factory=list)
    instances: list[Instance] = field(default_factory=list)
    generate_blocks: list[GenerateBlock] = field(default_factory=list)
    functions: dict[str, FunctionDecl] = field(default_factory=dict)
    tasks: dict[str, TaskDecl] = field(default_factory=dict)
    body_tokens: list[Token] = field(default_factory=list)

    def declared_names(self) -> set[str]:
        return set(self.ports) | set(self.declarations) | set(self.parameters) | set(self.functions) | set(self.tasks)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "file": self.span.file,
            "line": self.span.line,
            "ports": sorted(self.ports),
            "declarations": sorted(self.declarations),
            "parameters": sorted(self.parameters),
            "always_blocks": [
                {
                    "kind": block.kind,
                    "file": block.span.file,
                    "line": block.span.line,
                    "assignments": [assignment.target for assignment in block.assignments],
                }
                for block in self.always_blocks
            ],
            "continuous_assigns": [assignment.target for assignment in self.continuous_assigns],
            "instances": [
                {"module_type": instance.module_type, "instance_name": instance.instance_name}
                for instance in self.instances
            ],
            "generate_blocks": [
                {
                    "kind": block.kind,
                    "name": block.name,
                    "file": block.span.file,
                    "line": block.span.line,
                    "assignments": [assignment.target for assignment in block.assignments],
                    "instances": [instance.instance_name for instance in block.instances],
                }
                for block in self.generate_blocks
            ],
            "functions": sorted(self.functions),
            "tasks": sorted(self.tasks),
        }


@dataclass
class Design:
    modules: list[Module] = field(default_factory=list)

    def module_names(self) -> set[str]:
        return {module.name for module in self.modules}

    def top_module(self, top: str | None) -> Module | None:
        if top:
            for module in self.modules:
                if module.name == top:
                    return module
            return None
        return self.modules[0] if self.modules else None

    def to_dict(self) -> dict[str, Any]:
        return {"modules": [module.to_dict() for module in self.modules]}
