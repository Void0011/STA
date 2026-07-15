from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from sta_lite.lint.ast_nodes import AlwaysBlock, Assignment, Design, Module, Signal
from sta_lite.lint.lexer import Token
from sta_lite.lint.sdc_checker import parse_create_clocks
from sta_lite.lint.symbol_table import DesignContext


CLOCK_NAME_RE = re.compile(r"(clk|clock)", re.IGNORECASE)
RESET_NAME_RE = re.compile(r"(rst|reset)", re.IGNORECASE)
CONTROL_NAME_RE = re.compile(r"(rst|reset|en|enable|valid|ready|sel|mode|flush|clear|load)", re.IGNORECASE)
SYNC_NAME_RE = re.compile(r"(sync|synced|synchronizer|cdc|rst_sync|reset_sync)", re.IGNORECASE)

LONG_COMB_OPS = {
    "+",
    "-",
    "*",
    "/",
    "%",
    "&",
    "|",
    "^",
    "~",
    "<<",
    ">>",
    "<<<",
    ">>>",
    "?",
    "&&",
    "||",
    "==",
    "!=",
    ">",
    "<",
    ">=",
    "<=",
}


@dataclass
class SdcInfo:
    file: str | None = None
    text: str = ""
    clock_ports: set[str] = field(default_factory=set)
    input_delay_ports: set[str] = field(default_factory=set)
    output_delay_ports: set[str] = field(default_factory=set)
    has_multicycle: bool = False


@dataclass
class RiskFeatures:
    design: Design
    context: DesignContext
    top: str | None
    top_module: Module | None
    sdc: SdcInfo


def extract_features(design: Design, context: DesignContext, top: str | None, sdc_file: str | None) -> RiskFeatures:
    top_module = design.top_module(top)
    return RiskFeatures(
        design=design,
        context=context,
        top=top,
        top_module=top_module,
        sdc=_parse_sdc(sdc_file),
    )


def _parse_sdc(sdc_file: str | None) -> SdcInfo:
    if not sdc_file:
        return SdcInfo()
    path = Path(sdc_file)
    text = ""
    if path.is_file():
        text = path.read_text(encoding="utf-8")
    clocks = parse_create_clocks(path)
    return SdcInfo(
        file=str(path.resolve()) if path.exists() else str(path),
        text=text,
        clock_ports={clock.port for clock in clocks},
        input_delay_ports=_delay_ports(text, "set_input_delay"),
        output_delay_ports=_delay_ports(text, "set_output_delay"),
        has_multicycle="set_multicycle_path" in text,
    )


def _delay_ports(text: str, command: str) -> set[str]:
    ports: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or command not in stripped:
            continue
        match = re.search(r"\[get_ports\s+\{?([A-Za-z_][A-Za-z0-9_$*]*)\}?\]", stripped)
        if match:
            ports.add(match.group(1))
    return ports


def module_symbols(module: Module) -> dict[str, Signal]:
    symbols: dict[str, Signal] = {}
    symbols.update(module.ports)
    symbols.update(module.declarations)
    symbols.update(module.parameters)
    return symbols


def signal_width(signal: Signal | None) -> int | None:
    if signal is None or not signal.width:
        return 1 if signal is not None else None
    match = re.fullmatch(r"\[\s*([0-9]+)\s*:\s*([0-9]+)\s*\]", signal.width)
    if not match:
        return None
    return abs(int(match.group(1)) - int(match.group(2))) + 1


def token_values(tokens: list[Token]) -> list[str]:
    return [token.value for token in tokens]


def token_identifiers(tokens: list[Token]) -> list[str]:
    return [token.value for token in tokens if token.kind == "identifier"]


def operator_count(tokens: list[Token]) -> int:
    return sum(1 for token in tokens if token.value in LONG_COMB_OPS)


def estimated_logic_depth(tokens: list[Token]) -> int:
    count = operator_count(tokens)
    mux_count = sum(1 for token in tokens if token.value in {"?", "case", "casez", "casex", "if"})
    mult_count = sum(1 for token in tokens if token.value in {"*", "/", "%"})
    return count + mux_count + mult_count


def event_pairs(block: AlwaysBlock) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    tokens = block.sensitivity_tokens
    for index, token in enumerate(tokens[:-1]):
        if token.value in {"posedge", "negedge"} and tokens[index + 1].kind == "identifier":
            pairs.append((token.value, tokens[index + 1].value))
    return pairs


def event_clock_names(block: AlwaysBlock) -> list[str]:
    result: list[str] = []
    for _edge, signal in event_pairs(block):
        if not is_reset_name(signal):
            result.append(signal)
    return result


def event_reset_names(block: AlwaysBlock) -> list[str]:
    return [signal for _edge, signal in event_pairs(block) if is_reset_name(signal)]


def is_clock_name(name: str) -> bool:
    return bool(CLOCK_NAME_RE.search(name))


def is_reset_name(name: str) -> bool:
    return bool(RESET_NAME_RE.search(name))


def is_control_name(name: str) -> bool:
    return bool(CONTROL_NAME_RE.search(name))


def is_sync_name(name: str) -> bool:
    return bool(SYNC_NAME_RE.search(name))


def assignment_expr_identifiers(assignment: Assignment) -> set[str]:
    return {token.value for token in assignment.expr_tokens if token.kind == "identifier"}


def block_read_identifiers(block: AlwaysBlock) -> set[str]:
    reads: set[str] = set()
    assigned = {assignment.target for assignment in block.assignments}
    for token in block.body_tokens:
        if token.kind == "identifier" and token.value not in assigned:
            reads.add(token.value)
    for assignment in block.assignments:
        reads.update(assignment_expr_identifiers(assignment))
    return reads
