from __future__ import annotations

from dataclasses import dataclass
import re

from sta_lite.models.diagnostic import Diagnostic


KEYWORDS = {
    "always",
    "always_comb",
    "always_ff",
    "always_latch",
    "assert",
    "assume",
    "assign",
    "automatic",
    "begin",
    "bit",
    "byte",
    "case",
    "casex",
    "casez",
    "class",
    "cover",
    "covergroup",
    "default",
    "else",
    "end",
    "endcase",
    "endclass",
    "endgroup",
    "endmodule",
    "endgenerate",
    "endinterface",
    "endpackage",
    "endprogram",
    "endproperty",
    "endprimitive",
    "endspecify",
    "endtask",
    "endfunction",
    "enum",
    "for",
    "forever",
    "function",
    "generate",
    "genvar",
    "if",
    "import",
    "initial",
    "inout",
    "input",
    "inside",
    "int",
    "interface",
    "integer",
    "longint",
    "localparam",
    "logic",
    "modport",
    "module",
    "negedge",
    "or",
    "output",
    "package",
    "packed",
    "parameter",
    "posedge",
    "priority",
    "primitive",
    "program",
    "property",
    "real",
    "realtime",
    "reg",
    "repeat",
    "shortint",
    "shortreal",
    "signed",
    "specify",
    "string",
    "struct",
    "table",
    "task",
    "time",
    "typedef",
    "union",
    "unique",
    "unsigned",
    "void",
    "while",
    "wire",
}

OPERATORS = [
    "<<<",
    ">>>",
    "===",
    "!==",
    "<<",
    ">>",
    "<=",
    ">=",
    "==",
    "!=",
    "&&",
    "||",
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    "&=",
    "|=",
    "^=",
    "->",
    "=>",
    "::",
    "++",
    "--",
]

SINGLE_SYMBOLS = set("()[]{};,:.@#?+-*/%&|^~!<>='")
BASED_NUMBER_RE = re.compile(r"^\d*'[sS]?[bBoOdDhH][0-9a-fA-FxXzZ?_]+$")
DECIMAL_NUMBER_RE = re.compile(r"^\d(?:[0-9_]*\d)?$")


@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    file: str
    line: int
    column: int

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "value": self.value,
            "file": self.file,
            "line": self.line,
            "column": self.column,
        }


@dataclass(frozen=True)
class SourceLine:
    text: str
    file: str
    line: int


@dataclass
class LexResult:
    tokens: list[Token]
    diagnostics: list[Diagnostic]


def _is_ident_start(ch: str) -> bool:
    return ch.isalpha() or ch in {"_", "$"}


def _is_ident_char(ch: str) -> bool:
    return ch.isalnum() or ch in {"_", "$"}


class Lexer:
    def lex(self, lines: list[SourceLine]) -> LexResult:
        tokens: list[Token] = []
        diagnostics: list[Diagnostic] = []
        for source_line in lines:
            text = source_line.text
            index = 0
            while index < len(text):
                ch = text[index]
                column = index + 1
                if ch.isspace():
                    index += 1
                    continue
                if ch == "\\":
                    start = index
                    index += 1
                    while index < len(text) and not text[index].isspace():
                        index += 1
                    tokens.append(Token("identifier", text[start:index], source_line.file, source_line.line, column))
                    continue
                if _is_ident_start(ch):
                    start = index
                    index += 1
                    while index < len(text) and _is_ident_char(text[index]):
                        index += 1
                    value = text[start:index]
                    kind = "keyword" if value in KEYWORDS else "identifier"
                    tokens.append(Token(kind, value, source_line.file, source_line.line, column))
                    continue
                if ch.isdigit():
                    start = index
                    index += 1
                    while index < len(text) and (text[index].isalnum() or text[index] in {"_", "'", "?", "x", "X", "z", "Z"}):
                        index += 1
                    value = text[start:index]
                    if not _valid_number(value):
                        diagnostics.append(
                            Diagnostic.make(
                                severity="error",
                                rule="SYNTAX001",
                                category="syntax",
                                file=source_line.file,
                                line=source_line.line,
                                column=column,
                                message=f"malformed number literal: {value}",
                                message_zh=f"语法错误：数字常量 `{value}` 格式不完整或非法。",
                                suggestion_zh="请检查 Verilog 数字常量是否包含位宽、进制和实际数字，例如 4'd0、8'hff。",
                                confidence="high",
                                source_excerpt=text.strip(),
                            )
                        )
                    tokens.append(Token("number", value, source_line.file, source_line.line, column))
                    continue
                if ch == "'" and index + 1 < len(text) and text[index + 1] in {"s", "S", "b", "B", "o", "O", "d", "D", "h", "H"}:
                    start = index
                    index += 1
                    while index < len(text) and (text[index].isalnum() or text[index] in {"_", "?", "x", "X", "z", "Z"}):
                        index += 1
                    value = text[start:index]
                    diagnostics.append(
                        Diagnostic.make(
                            severity="error",
                            rule="SYNTAX001",
                            category="syntax",
                            file=source_line.file,
                            line=source_line.line,
                            column=column,
                            message=f"malformed unsized based number literal: {value}",
                            message_zh=f"语法错误：数字常量 `{value}` 缺少实际数字或格式非法。",
                            suggestion_zh="请检查宏展开后的 Verilog 数字常量，例如 'd0、'hff，进制后必须有数字。",
                            confidence="high",
                            source_excerpt=text.strip(),
                        )
                    )
                    tokens.append(Token("number", value, source_line.file, source_line.line, column))
                    continue
                if ch == '"':
                    start = index
                    index += 1
                    escaped = False
                    while index < len(text):
                        current = text[index]
                        if current == '"' and not escaped:
                            index += 1
                            break
                        escaped = current == "\\" and not escaped
                        if current != "\\":
                            escaped = False
                        index += 1
                    else:
                        diagnostics.append(
                            Diagnostic.make(
                                severity="error",
                                rule="SYNTAX001",
                                category="syntax",
                                file=source_line.file,
                                line=source_line.line,
                                column=column,
                                message="unterminated string literal",
                                message_zh="语法错误：字符串没有结束。",
                                suggestion_zh="请检查该行字符串是否缺少右侧双引号。",
                                confidence="high",
                                source_excerpt=text.strip(),
                            )
                        )
                    tokens.append(Token("string", text[start:index], source_line.file, source_line.line, column))
                    continue

                matched = None
                for operator in OPERATORS:
                    if text.startswith(operator, index):
                        matched = operator
                        break
                if matched:
                    tokens.append(Token("operator", matched, source_line.file, source_line.line, column))
                    index += len(matched)
                    continue
                if ch in SINGLE_SYMBOLS:
                    kind = "operator" if ch in "+-*/%&|^~!<>=?:" else "symbol"
                    tokens.append(Token(kind, ch, source_line.file, source_line.line, column))
                    index += 1
                    continue

                diagnostics.append(
                    Diagnostic.make(
                        severity="error",
                        rule="SYNTAX001",
                        category="syntax",
                        file=source_line.file,
                        line=source_line.line,
                        column=column,
                        message=f"unknown character: {ch}",
                        message_zh=f"语法错误：无法识别字符 `{ch}`。",
                        suggestion_zh="请检查该字符是否来自不受支持的语法、编码或拼写错误。",
                        confidence="high",
                        source_excerpt=text.strip(),
                    )
                )
                index += 1
        eof_file = lines[-1].file if lines else "<empty>"
        eof_line = lines[-1].line + 1 if lines else 1
        tokens.append(Token("eof", "<eof>", eof_file, eof_line, 1))
        return LexResult(tokens=tokens, diagnostics=diagnostics)


def _valid_number(value: str) -> bool:
    if "'" in value:
        return bool(BASED_NUMBER_RE.match(value))
    return bool(DECIMAL_NUMBER_RE.match(value))
