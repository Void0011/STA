from __future__ import annotations

from dataclasses import dataclass, field

from sta_lite.lint.ast_nodes import Design, Module, Signal
from sta_lite.lint.lexer import KEYWORDS, Token


IGNORED_IDENTIFIERS = {
    "$bits",
    "$clog2",
    "$display",
    "$finish",
    "$signed",
    "$unsigned",
}


@dataclass
class ModuleContext:
    module: Module
    declarations: dict[str, Signal] = field(default_factory=dict)
    identifier_tokens: list[Token] = field(default_factory=list)
    expression_identifier_tokens: list[Token] = field(default_factory=list)

    def is_declared(self, name: str) -> bool:
        return name in self.declarations


@dataclass
class DesignContext:
    modules: dict[str, ModuleContext]
    module_names: set[str]


def build_context(design: Design) -> DesignContext:
    module_names = design.module_names()
    contexts: dict[str, ModuleContext] = {}
    for module in design.modules:
        declarations: dict[str, Signal] = {}
        declarations.update(module.ports)
        declarations.update(module.declarations)
        declarations.update(module.parameters)
        for function in module.functions.values():
            declarations[function.name] = Signal(function.name, None, "function", function.span)
        for task in module.tasks.values():
            declarations[task.name] = Signal(task.name, None, "task", task.span)
        context = ModuleContext(module=module, declarations=declarations)
        context.identifier_tokens.extend(_module_identifier_tokens(module))
        context.expression_identifier_tokens.extend(_module_expression_identifier_tokens(module))
        contexts[module.name] = context
    return DesignContext(modules=contexts, module_names=module_names)


def _module_identifier_tokens(module: Module) -> list[Token]:
    tokens: list[Token] = [signal.span for signal in module.ports.values()]
    tokens.extend(signal.span for signal in module.declarations.values())
    tokens.extend(signal.span for signal in module.parameters.values())
    tokens.extend(function.span for function in module.functions.values())
    tokens.extend(task.span for task in module.tasks.values())
    tokens.extend(token for token in module.body_tokens if token.kind == "identifier")
    return tokens


def _module_expression_identifier_tokens(module: Module) -> list[Token]:
    tokens: list[Token] = []
    for assignment in module.continuous_assigns:
        tokens.extend(token for token in assignment.expr_tokens if _is_real_identifier(token))
    for block in module.always_blocks:
        tokens.extend(token for token in block.sensitivity_tokens if _is_real_identifier(token))
        for assignment in block.assignments:
            tokens.extend(token for token in assignment.expr_tokens if _is_real_identifier(token))
    for generate_block in module.generate_blocks:
        for assignment in generate_block.assignments:
            tokens.extend(token for token in assignment.expr_tokens if _is_real_identifier(token))
        for instance in generate_block.instances:
            tokens.extend(_instance_connection_identifiers(instance.connection_tokens))
    for function in module.functions.values():
        for assignment in function.assignments:
            tokens.extend(token for token in assignment.expr_tokens if _is_real_identifier(token))
    for task in module.tasks.values():
        for assignment in task.assignments:
            tokens.extend(token for token in assignment.expr_tokens if _is_real_identifier(token))
    for instance in module.instances:
        tokens.extend(_instance_connection_identifiers(instance.connection_tokens))
    return tokens


def _instance_connection_identifiers(tokens: list[Token]) -> list[Token]:
    result: list[Token] = []
    for index, token in enumerate(tokens):
        if not _is_real_identifier(token):
            continue
        if index > 0 and tokens[index - 1].value == ".":
            continue
        result.append(token)
    return result


def _is_real_identifier(token: Token) -> bool:
    return token.kind == "identifier" and token.value not in KEYWORDS and token.value not in IGNORED_IDENTIFIERS
