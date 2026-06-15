from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sta_lite.lint.lexer import SourceLine
from sta_lite.models.diagnostic import Diagnostic


@dataclass
class PreprocessResult:
    lines: list[SourceLine]
    diagnostics: list[Diagnostic]
    source_files: list[str]
    default_nettype_none: bool
    source_file_timescales: dict[str, str | None]


@dataclass
class _ConditionalFrame:
    parent_active: bool
    active: bool
    branch_taken: bool


class Preprocessor:
    def __init__(self, include_dirs: list[str] | None = None, defines: dict[str, str] | None = None) -> None:
        self.include_dirs = [Path(item).resolve() for item in (include_dirs or [])]
        self.defines = dict(defines or {})
        self.diagnostics: list[Diagnostic] = []
        self.source_files: list[str] = []
        self.source_file_timescales: dict[str, str | None] = {}
        self.default_nettype_none = False
        self._include_stack: list[Path] = []
        self._block_comment = False

    def preprocess(self, rtl_files: list[Path]) -> PreprocessResult:
        output: list[SourceLine] = []
        for file_path in rtl_files:
            self._process_file(file_path.resolve(), output)
        return PreprocessResult(
            lines=output,
            diagnostics=self.diagnostics,
            source_files=self.source_files,
            default_nettype_none=self.default_nettype_none,
            source_file_timescales=self.source_file_timescales,
        )

    def _current_active(self, stack: list[_ConditionalFrame]) -> bool:
        return stack[-1].active if stack else True

    def _process_file(self, path: Path, output: list[SourceLine]) -> None:
        if path in self._include_stack:
            self.diagnostics.append(
                Diagnostic.make(
                    severity="error",
                    rule="PP001_INCLUDE",
                    category="preprocess",
                    file=path,
                    line=1,
                    column=1,
                    message="recursive include detected",
                    message_zh=f"预处理错误：检测到递归 include：{path}",
                    suggestion_zh="请检查 include 文件之间是否互相包含。",
                    confidence="high",
                )
            )
            return
        if not path.is_file():
            self.diagnostics.append(
                Diagnostic.make(
                    severity="error",
                    rule="PP001_INCLUDE",
                    category="preprocess",
                    file=path,
                    line=1,
                    column=1,
                    message="source file not found",
                    message_zh=f"预处理错误：找不到源文件：{path}",
                    suggestion_zh="请检查 --rtl 路径或 glob 是否正确。",
                    confidence="high",
                )
            )
            return

        path_text = str(path)
        self.source_files.append(path_text)
        self.source_file_timescales.setdefault(path_text, None)
        self._include_stack.append(path)
        try:
            raw_lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            raw_lines = path.read_text(encoding="latin-1").splitlines()

        conditional_stack: list[_ConditionalFrame] = []
        for line_no, raw in enumerate(raw_lines, start=1):
            stripped_comments = self._remove_comments(raw)
            stripped = stripped_comments.strip()
            directive_match = re.match(r"^`([A-Za-z_][A-Za-z0-9_$]*)\b(.*)$", stripped)
            if directive_match:
                self._handle_directive(
                    directive_match.group(1),
                    directive_match.group(2).strip(),
                    current_file=path,
                    line_no=line_no,
                    output=output,
                    conditional_stack=conditional_stack,
                )
                continue
            if not self._current_active(conditional_stack):
                continue
            expanded = self._expand_macros(stripped_comments, path, line_no)
            output.append(SourceLine(text=expanded, file=str(path), line=line_no))

        if conditional_stack:
            frame = conditional_stack[-1]
            self.diagnostics.append(
                Diagnostic.make(
                    severity="error",
                    rule="PP002_CONDITIONAL",
                    category="preprocess",
                    file=path,
                    line=len(raw_lines),
                    column=1,
                    message="unterminated conditional compilation block",
                    message_zh="预处理错误：条件编译块没有用 `endif 结束。",
                    suggestion_zh="请检查 `ifdef/`ifndef/`elsif/`else/`endif 是否成对出现。",
                    confidence="high",
                    source_excerpt=f"active={frame.active}",
                )
            )
        if self._block_comment:
            self.diagnostics.append(
                Diagnostic.make(
                    severity="error",
                    rule="PP004_COMMENT",
                    category="preprocess",
                    file=path,
                    line=len(raw_lines),
                    column=1,
                    message="unterminated block comment",
                    message_zh="预处理错误：块注释没有用 */ 结束。",
                    suggestion_zh="请检查 /* 和 */ 是否成对出现。",
                    confidence="high",
                )
            )
            self._block_comment = False
        self._include_stack.pop()

    def _handle_directive(
        self,
        name: str,
        arg: str,
        *,
        current_file: Path,
        line_no: int,
        output: list[SourceLine],
        conditional_stack: list[_ConditionalFrame],
    ) -> None:
        active = self._current_active(conditional_stack)
        if name in {"ifdef", "ifndef"}:
            macro = arg.split()[0] if arg.split() else ""
            condition = macro in self.defines
            if name == "ifndef":
                condition = not condition
            conditional_stack.append(
                _ConditionalFrame(parent_active=active, active=active and condition, branch_taken=condition)
            )
            return
        if name == "elsif":
            if not conditional_stack:
                self._conditional_error(current_file, line_no, "`elsif 没有匹配的 `ifdef/`ifndef。")
                return
            frame = conditional_stack[-1]
            macro = arg.split()[0] if arg.split() else ""
            condition = macro in self.defines
            frame.active = frame.parent_active and (not frame.branch_taken) and condition
            frame.branch_taken = frame.branch_taken or condition
            return
        if name == "else":
            if not conditional_stack:
                self._conditional_error(current_file, line_no, "`else 没有匹配的 `ifdef/`ifndef。")
                return
            frame = conditional_stack[-1]
            frame.active = frame.parent_active and not frame.branch_taken
            frame.branch_taken = True
            return
        if name == "endif":
            if not conditional_stack:
                self._conditional_error(current_file, line_no, "`endif 没有匹配的 `ifdef/`ifndef。")
                return
            conditional_stack.pop()
            return
        if not active:
            return

        if name == "include":
            match = re.match(r'"([^"]+)"', arg)
            if not match:
                self.diagnostics.append(
                    Diagnostic.make(
                        severity="error",
                        rule="PP001_INCLUDE",
                        category="preprocess",
                        file=current_file,
                        line=line_no,
                        column=1,
                        message="invalid include directive",
                        message_zh="预处理错误：`include 需要使用双引号文件名。",
                        suggestion_zh='请使用类似 `include "defs.vh" 的写法。',
                        confidence="high",
                    )
                )
                return
            include_path = self._resolve_include(match.group(1), current_file.parent)
            if include_path is None:
                self.diagnostics.append(
                    Diagnostic.make(
                        severity="error",
                        rule="PP001_INCLUDE",
                        category="preprocess",
                        file=current_file,
                        line=line_no,
                        column=1,
                        message="include file not found",
                        message_zh=f"预处理错误：找不到 include 文件：{match.group(1)}",
                        suggestion_zh="请检查 include 文件路径，或通过 --include 添加搜索目录。",
                        confidence="high",
                    )
                )
                return
            self._process_file(include_path, output)
            return
        if name == "define":
            parts = arg.split(None, 1)
            if not parts:
                self.diagnostics.append(
                    Diagnostic.make(
                        severity="error",
                        rule="PP003_MACRO",
                        category="preprocess",
                        file=current_file,
                        line=line_no,
                        column=1,
                        message="empty define directive",
                        message_zh="预处理错误：`define 缺少宏名称。",
                        suggestion_zh="请补充宏名称，或删除空的 `define。",
                        confidence="high",
                    )
                )
                return
            macro_name = parts[0]
            if "(" in macro_name:
                unsupported_rule, unsupported_category = self._unsupported_rule_for_file(current_file)
                self.diagnostics.append(
                    Diagnostic.make(
                        severity="warning",
                        rule=unsupported_rule,
                        category=unsupported_category,
                        file=current_file,
                        line=line_no,
                        column=1,
                        message="function-like macro is unsupported",
                        message_zh="暂不支持函数式宏。",
                        suggestion_zh="当前 lint 仅支持对象式宏；请先改为对象式宏或展开宏后再检查。",
                        confidence="high",
                    )
                )
                return
            self.defines[macro_name] = parts[1] if len(parts) > 1 else "1"
            return
        if name == "undef":
            if arg:
                self.defines.pop(arg.split()[0], None)
            return
        if name == "default_nettype":
            if arg.split()[:1] == ["none"]:
                self.default_nettype_none = True
            return
        if name == "timescale":
            self.source_file_timescales[str(current_file)] = arg
            return
        if name in {"celldefine", "endcelldefine"}:
            return

        unsupported_rule, unsupported_category = self._unsupported_rule_for_file(current_file)
        self.diagnostics.append(
            Diagnostic.make(
                severity="warning",
                rule=unsupported_rule,
                category=unsupported_category,
                file=current_file,
                line=line_no,
                column=1,
                message=f"unsupported preprocessor directive `{name}",
                message_zh=f"暂不支持预处理指令 `{name}。",
                suggestion_zh="当前 lint 会继续分析后续代码；如该指令会改变语义，请先展开或简化后再检查。",
                confidence="medium",
            )
        )

    def _unsupported_rule_for_file(self, path: Path) -> tuple[str, str]:
        if path.suffix.lower() == ".sv":
            return "UNSUPPORTED_SYSTEMVERILOG", "unsupported_systemverilog"
        return "UNSUPPORTED_VERILOG", "unsupported"

    def _conditional_error(self, current_file: Path, line_no: int, message_zh: str) -> None:
        self.diagnostics.append(
            Diagnostic.make(
                severity="error",
                rule="PP002_CONDITIONAL",
                category="preprocess",
                file=current_file,
                line=line_no,
                column=1,
                message="invalid conditional compilation directive",
                message_zh=f"预处理错误：{message_zh}",
                suggestion_zh="请检查条件编译指令是否成对出现。",
                confidence="high",
            )
        )

    def _resolve_include(self, include_name: str, current_dir: Path) -> Path | None:
        candidates = [current_dir / include_name]
        candidates.extend(directory / include_name for directory in self.include_dirs)
        for candidate in candidates:
            if candidate.is_file():
                return candidate.resolve()
        return None

    def _remove_comments(self, line: str) -> str:
        result: list[str] = []
        index = 0
        in_string = False
        while index < len(line):
            ch = line[index]
            nxt = line[index + 1] if index + 1 < len(line) else ""
            if self._block_comment:
                if ch == "*" and nxt == "/":
                    result.extend([" ", " "])
                    index += 2
                    self._block_comment = False
                else:
                    result.append(" ")
                    index += 1
                continue
            if ch == '"' and (index == 0 or line[index - 1] != "\\"):
                in_string = not in_string
                result.append(ch)
                index += 1
                continue
            if not in_string and ch == "/" and nxt == "*":
                result.extend([" ", " "])
                index += 2
                self._block_comment = True
                continue
            if not in_string and ch == "/" and nxt == "/":
                result.extend(" " for _ in line[index:])
                break
            result.append(ch)
            index += 1
        return "".join(result)

    def _expand_macros(self, line: str, current_file: Path, line_no: int) -> str:
        def replace(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in self.defines:
                self.diagnostics.append(
                    Diagnostic.make(
                        severity="warning",
                        rule="PP003_MACRO",
                        category="preprocess",
                        file=current_file,
                        line=line_no,
                        column=match.start() + 1,
                        message=f"undefined macro `{name}",
                        message_zh=f"预处理警告：宏 `{name} 未定义。",
                        suggestion_zh="请通过源码 `define 或 CLI --define 提供宏定义。",
                        confidence="high",
                        source_excerpt=line.strip(),
                    )
                )
                return match.group(0)
            return self.defines[name]

        return re.sub(r"`([A-Za-z_][A-Za-z0-9_$]*)\b", replace, line)
