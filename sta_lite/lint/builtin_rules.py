from __future__ import annotations

import re
from pathlib import Path

from sta_lite.lint.ast_nodes import AlwaysBlock, Assignment, Design, Module, Signal
from sta_lite.lint.lexer import Token
from sta_lite.lint.preprocessor import PreprocessResult
from sta_lite.lint.sdc_checker import parse_create_clocks
from sta_lite.lint.symbol_table import DesignContext
from sta_lite.models.diagnostic import Diagnostic


CLOCK_NAME_RE = re.compile(r"(clk|clock)", re.IGNORECASE)
RESET_NAME_RE = re.compile(r"(rst|reset)", re.IGNORECASE)
LONG_COMB_OPS = {
    "+",
    "-",
    "*",
    "/",
    "%",
    "&",
    "|",
    "^",
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


def run_builtin_rules(
    *,
    design: Design,
    context: DesignContext,
    preprocess: PreprocessResult,
    top: str | None,
    sdc_file: str | None,
    settings: dict[str, object] | None = None,
) -> list[Diagnostic]:
    settings = settings or {}
    threshold = int(settings.get("long_comb_operator_threshold", 10))
    diagnostics: list[Diagnostic] = []
    diagnostics.extend(_rule_default_nettype(preprocess, design))
    diagnostics.extend(_rule_timescale_consistency(preprocess))
    diagnostics.extend(_rule_port_declaration_consistency(design))
    diagnostics.extend(_rule_implicit_net(context, preprocess.default_nettype_none))
    diagnostics.extend(_rule_procedural_assignment_targets(design))
    diagnostics.extend(_rule_unresolved_instances(design))
    diagnostics.extend(_rule_instance_port_connections(design))
    diagnostics.extend(_rule_constant_select_range(design))
    diagnostics.extend(_rule_latch_risk(design))
    diagnostics.extend(_rule_gated_clock(design))
    diagnostics.extend(_rule_long_comb(design, threshold))
    diagnostics.extend(_rule_blocking_in_seq(design))
    diagnostics.extend(_rule_nonblocking_in_comb(design))
    diagnostics.extend(_rule_multi_driver(design))
    diagnostics.extend(_rule_async_reset_release(design))
    diagnostics.extend(_rule_unused_unconnected(design, context))
    if sdc_file:
        diagnostics.extend(_rule_constraint_clock_mismatch(design, top, sdc_file))
    return diagnostics


def _rule_port_declaration_consistency(design: Design) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for module in design.modules:
        for name, signal in module.ports.items():
            declared = module.declarations.get(name)
            if signal.direction is None and (declared is None or declared.direction is None):
                diagnostics.append(
                    Diagnostic.make(
                        severity="error",
                        rule="SEM002_PORT_NOT_DECLARED",
                        category="module_port",
                        file=signal.span.file,
                        line=signal.span.line,
                        column=signal.span.column,
                        message=f"port is not declared with direction: {name}",
                        message_zh=f"端口 `{name}` 出现在模块端口列表中，但没有 input/output/inout 方向声明。",
                        suggestion_zh="非 ANSI 端口列表中的每个端口都需要在模块体内声明方向，例如 `output y;`。",
                        confidence="high",
                    )
                )
    return diagnostics


def _rule_default_nettype(preprocess: PreprocessResult, design: Design) -> list[Diagnostic]:
    if preprocess.default_nettype_none:
        return []
    token = design.modules[0].span if design.modules else None
    file = token.file if token else (preprocess.source_files[0] if preprocess.source_files else "<unknown>")
    line = token.line if token else 1
    column = token.column if token else 1
    return [
        Diagnostic.make(
            severity="warning",
            rule="RTL001_DEFAULT_NETTYPE",
            category="style",
            file=file,
            line=line,
            column=column,
            message="default_nettype none is missing",
            message_zh="未发现 `default_nettype none`，存在隐式网线被静默创建的风险。",
            suggestion_zh="建议在源码开头加入 `default_nettype none`，并显式声明所有信号。",
            confidence="high",
        )
    ]


def _rule_timescale_consistency(preprocess: PreprocessResult) -> list[Diagnostic]:
    timescales = getattr(preprocess, "source_file_timescales", {})
    if not timescales:
        return []
    declared = {file: value for file, value in timescales.items() if value}
    if not declared:
        return []
    diagnostics: list[Diagnostic] = []
    values = set(declared.values())
    if len(values) > 1:
        first_file = next(iter(declared))
        diagnostics.append(
            Diagnostic.make(
                severity="warning",
                rule="RTL011_TIMESCALE_INCONSISTENT",
                category="semantic",
                file=first_file,
                line=1,
                column=1,
                message="inconsistent timescale directives",
                message_zh="多个 Verilog 源文件的 `timescale 设置不一致。",
                suggestion_zh="请为同一编译单元中的文件设置一致的 `timescale，或明确确认该差异是有意的。",
                confidence="medium",
            )
        )
    for file in preprocess.source_files:
        if file in declared:
            continue
        diagnostics.append(
            Diagnostic.make(
                severity="warning",
                rule="RTL011_TIMESCALE_INCONSISTENT",
                category="semantic",
                file=file,
                line=1,
                column=1,
                message="missing timescale directive",
                message_zh="该 Verilog 源文件缺少 `timescale，可能继承其他文件的时间单位。",
                suggestion_zh="请在文件开头添加明确的 `timescale，或确认该文件不依赖仿真时间单位。",
                confidence="medium",
            )
        )
    return diagnostics


def _rule_implicit_net(context: DesignContext, default_nettype_none: bool) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for module_context in context.modules.values():
        seen: set[tuple[str, str, int]] = set()
        for token in module_context.expression_identifier_tokens:
            name = token.value
            if name in context.module_names or module_context.is_declared(name):
                continue
            key = (name, token.file, token.line)
            if key in seen:
                continue
            seen.add(key)
            severity = "error" if default_nettype_none else "warning"
            rule = "SEM003_UNDECLARED_IDENTIFIER" if default_nettype_none else "RTL002_IMPLICIT_NET_RISK"
            diagnostics.append(
                Diagnostic.make(
                    severity=severity,
                    rule=rule,
                    category="semantic",
                    file=token.file,
                    line=token.line,
                    column=token.column,
                    message=f"identifier appears undeclared: {name}",
                    message_zh=f"信号 `{name}` 未声明，可能形成隐式网线或拼写错误。",
                    suggestion_zh="请显式声明该信号，或检查是否拼写错误、include/宏条件是否遗漏。",
                    confidence="medium",
                )
            )
    return diagnostics


def _rule_procedural_assignment_targets(design: Design) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for module in design.modules:
        symbols = _module_symbols(module)
        for block in module.always_blocks:
            for assignment in block.assignments:
                signal = symbols.get(assignment.target)
                if signal is None:
                    continue
                if signal.data_type in {"reg", "logic"}:
                    continue
                diagnostics.append(
                    Diagnostic.make(
                        severity="error",
                        rule="SEM004_PROCEDURAL_WIRE_ASSIGN",
                        category="assignment",
                        file=assignment.span.file,
                        line=assignment.span.line,
                        column=assignment.span.column,
                        message=f"procedural assignment to non-reg target: {assignment.target}",
                        message_zh=f"过程块中对 `{assignment.target}` 赋值，但该信号不是 reg/logic 类型。",
                        suggestion_zh="如果该信号需要在 always 中赋值，请声明为 `reg`；如果是纯组合连接，请改用连续赋值。",
                        confidence="high",
                    )
                )
    return diagnostics


def _rule_unresolved_instances(design: Design) -> list[Diagnostic]:
    module_names = design.module_names()
    primitives = {
        "and",
        "nand",
        "or",
        "nor",
        "xor",
        "xnor",
        "buf",
        "not",
        "bufif0",
        "bufif1",
        "notif0",
        "notif1",
        "pmos",
        "nmos",
        "cmos",
        "pullup",
        "pulldown",
    }
    diagnostics: list[Diagnostic] = []
    for module in design.modules:
        for instance in module.instances:
            if instance.module_type in module_names or instance.module_type in primitives:
                continue
            diagnostics.append(
                Diagnostic.make(
                    severity="error",
                    rule="SEM005_UNRESOLVED_MODULE",
                    category="instantiation",
                    file=instance.span.file,
                    line=instance.span.line,
                    column=instance.span.column,
                    message=f"unknown module type: {instance.module_type}",
                    message_zh=f"例化了未定义模块 `{instance.module_type}`。",
                    suggestion_zh="请确认子模块源码已加入 lint 文件列表，或检查模块名拼写。",
                    confidence="high",
                )
            )
    return diagnostics


def _rule_instance_port_connections(design: Design) -> list[Diagnostic]:
    module_map = {module.name: module for module in design.modules}
    diagnostics: list[Diagnostic] = []
    for module in design.modules:
        caller_symbols = _module_symbols(module)
        for instance in module.instances:
            child = module_map.get(instance.module_type)
            if child is None:
                continue
            child_ports = list(child.ports.values())
            child_port_map = {port.name: port for port in child_ports}
            segments = _split_top_level(instance.connection_tokens, ",")
            if _uses_named_connections(segments):
                connected: set[str] = set()
                for segment in segments:
                    if not segment:
                        continue
                    port_name = _named_port(segment)
                    if port_name is None:
                        continue
                    connected.add(port_name)
                    child_port = child_port_map.get(port_name)
                    if child_port is None:
                        diagnostics.append(
                            Diagnostic.make(
                                severity="error",
                                rule="SEM006_UNKNOWN_INSTANCE_PORT",
                                category="instantiation",
                                file=segment[0].file,
                                line=segment[0].line,
                                column=segment[0].column,
                                message=f"unknown named port: {port_name}",
                                message_zh=f"例化 `{instance.instance_name}` 连接了子模块不存在的端口 `{port_name}`。",
                                suggestion_zh="请检查命名端口是否与子模块声明一致。",
                                confidence="high",
                            )
                        )
                        continue
                    expr = _named_connection_expr(segment)
                    if child_port.direction in {"output", "inout"} and not expr:
                        diagnostics.append(_unconnected_instance_output_diag(instance, child_port, segment[0]))
                        continue
                    diagnostics.extend(_port_width_diagnostics(module, caller_symbols, instance, child_port, expr))
                for child_port in child_ports:
                    if child_port.direction in {"input", "inout"} and child_port.name not in connected:
                        diagnostics.append(_unconnected_port_diag(instance, child_port))
                    elif child_port.direction in {"output", "inout"} and child_port.name not in connected:
                        diagnostics.append(_unconnected_instance_output_diag(instance, child_port, instance.span))
                continue
            for index, child_port in enumerate(child_ports):
                expr = segments[index] if index < len(segments) else []
                if child_port.direction in {"input", "inout"} and not expr:
                    diagnostics.append(_unconnected_port_diag(instance, child_port))
                    continue
                if child_port.direction in {"output", "inout"} and not expr:
                    diagnostics.append(_unconnected_instance_output_diag(instance, child_port, instance.span))
                    continue
                diagnostics.extend(_port_width_diagnostics(module, caller_symbols, instance, child_port, expr))
    return diagnostics


def _rule_constant_select_range(design: Design) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for module in design.modules:
        symbols = _module_symbols(module)
        for assignment in module.continuous_assigns:
            diagnostics.extend(_select_range_diagnostics(symbols, assignment.expr_tokens))
        for block in module.always_blocks:
            for assignment in block.assignments:
                diagnostics.extend(_select_range_diagnostics(symbols, assignment.expr_tokens))
    return diagnostics


def _rule_latch_risk(design: Design) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for module in design.modules:
        for block in module.always_blocks:
            if not block.is_combinational() or not block.assignments:
                continue
            values = [token.value for token in block.body_tokens]
            if values.count("if") > values.count("else"):
                diagnostics.append(_block_diag(block, "RTL003_LATCH_RISK", "latch", "组合 always 块中存在没有 else 覆盖的 if 分支，可能推断 latch。", "请为组合逻辑中的每个输出提供默认赋值，或补齐所有 if/else 分支。", confidence="medium"))
            elif any(value in {"case", "casez", "casex"} for value in values) and "default" not in values:
                diagnostics.append(_block_diag(block, "RTL003_LATCH_RISK", "latch", "组合 case 语句缺少 default 分支，可能推断 latch。", "请添加 default 分支，或在 case 前给目标信号默认赋值。", confidence="medium"))
    return diagnostics


def _rule_gated_clock(design: Design) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    derived_clock_targets: set[str] = set()
    for module in design.modules:
        for assignment in module.continuous_assigns:
            expr_values = [token.value for token in assignment.expr_tokens]
            if CLOCK_NAME_RE.search(assignment.target) and any(op in expr_values for op in {"&", "|", "^", "?", "~"}):
                derived_clock_targets.add(assignment.target)
                diagnostics.append(
                    Diagnostic.make(
                        severity="warning",
                        rule="RTL004_GATED_CLOCK_RISK",
                        category="clock",
                        file=assignment.span.file,
                        line=assignment.span.line,
                        column=assignment.span.column,
                        message="derived or gated clock assignment",
                        message_zh=f"信号 `{assignment.target}` 像是由逻辑表达式生成的派生/门控时钟。",
                        suggestion_zh="建议使用时钟使能替代门控时钟，或确认该时钟由专用时钟门控单元生成。",
                        confidence="medium",
                    )
                )
        for block in module.always_blocks:
            if not block.is_sequential():
                continue
            values = [token.value for token in block.sensitivity_tokens]
            if any(op in values for op in {"&", "|", "^", "?", "~"}):
                diagnostics.append(_block_diag(block, "RTL004_GATED_CLOCK_RISK", "clock", "时序 always 的事件控制中出现逻辑表达式，疑似门控时钟。", "请将事件控制改为简单时钟边沿，并把条件逻辑放入 always 块内部。", confidence="high"))
                continue
            event_signals = _event_signals(block)
            for signal in event_signals:
                if signal in derived_clock_targets:
                    diagnostics.append(_block_diag(block, "RTL004_GATED_CLOCK_RISK", "clock", f"时序 always 使用派生时钟 `{signal}`。", "请检查该时钟是否为安全的专用门控时钟；否则建议改为时钟使能。", confidence="medium"))
    return diagnostics


def _rule_long_comb(design: Design, threshold: int) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for module in design.modules:
        for block in module.always_blocks:
            if not block.is_combinational():
                continue
            count = _operator_count(block.body_tokens)
            if count >= threshold:
                diagnostics.append(_block_diag(block, "RTL005_LONG_COMB_HEURISTIC", "timing_risk", f"组合 always 块包含 {count} 个算术/比较/选择操作，可能形成较长组合路径。", "建议拆分组合逻辑、增加流水级，或检查是否存在过深的 mux/算术链。", confidence="low"))
        for assignment in module.continuous_assigns:
            count = _operator_count(assignment.expr_tokens)
            if count >= threshold:
                diagnostics.append(
                    Diagnostic.make(
                        severity="warning",
                        rule="RTL005_LONG_COMB_HEURISTIC",
                        category="timing_risk",
                        file=assignment.span.file,
                        line=assignment.span.line,
                        column=assignment.span.column,
                        message="long continuous combinational expression",
                        message_zh=f"连续赋值 `{assignment.target}` 包含 {count} 个组合操作，可能形成较长组合路径。",
                        suggestion_zh="建议拆分表达式或增加寄存器边界；该结果是早期启发式风险，不是 STA 结论。",
                        confidence="low",
                    )
                )
    return diagnostics


def _rule_blocking_in_seq(design: Design) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for module in design.modules:
        for block in module.always_blocks:
            if not block.is_sequential():
                continue
            for assignment in block.assignments:
                if assignment.op == "=":
                    diagnostics.append(
                        Diagnostic.make(
                            severity="warning",
                            rule="RTL006_BLOCKING_IN_SEQUENTIAL",
                            category="sequential",
                            file=assignment.span.file,
                            line=assignment.span.line,
                            column=assignment.span.column,
                            message="blocking assignment in sequential block",
                            message_zh=f"时序 always 中对 `{assignment.target}` 使用阻塞赋值。",
                            suggestion_zh="建议在时序逻辑中使用非阻塞赋值 `<=`，避免仿真和综合语义不一致。",
                            confidence="high",
                        )
                    )
    return diagnostics


def _rule_nonblocking_in_comb(design: Design) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for module in design.modules:
        for block in module.always_blocks:
            if not block.is_combinational():
                continue
            for assignment in block.assignments:
                if assignment.op == "<=":
                    diagnostics.append(
                        Diagnostic.make(
                            severity="warning",
                            rule="RTL007_NONBLOCKING_IN_COMB",
                            category="combinational",
                            file=assignment.span.file,
                            line=assignment.span.line,
                            column=assignment.span.column,
                            message="nonblocking assignment in combinational block",
                            message_zh=f"组合 always 中对 `{assignment.target}` 使用非阻塞赋值。",
                            suggestion_zh="建议在组合逻辑中使用阻塞赋值 `=`，并提供默认赋值覆盖所有分支。",
                            confidence="high",
                        )
                    )
    return diagnostics


def _rule_multi_driver(design: Design) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for module in design.modules:
        drivers: dict[str, list[Assignment]] = {}
        for assignment in module.continuous_assigns:
            drivers.setdefault(assignment.target, []).append(assignment)
        for block in module.always_blocks:
            context_targets: dict[str, Assignment] = {}
            for assignment in block.assignments:
                context_targets.setdefault(assignment.target, assignment)
            for assignment in context_targets.values():
                drivers.setdefault(assignment.target, []).append(assignment)
        for target, assignments in drivers.items():
            contexts = {assignment.context for assignment in assignments}
            if len(contexts) <= 1 and len(assignments) <= 1:
                continue
            first = assignments[0]
            diagnostics.append(
                Diagnostic.make(
                    severity="warning",
                    rule="RTL008_MULTI_DRIVER_RISK",
                    category="semantic",
                    file=first.span.file,
                    line=first.span.line,
                    column=first.span.column,
                    message=f"multiple drivers for {target}",
                    message_zh=f"信号 `{target}` 可能由多个过程块或连续赋值共同驱动。",
                    suggestion_zh="请确认是否存在多驱动；通常应让每个 reg/logic 只在一个 always 块中赋值。",
                    confidence="medium",
                )
            )
    return diagnostics


def _rule_async_reset_release(design: Design) -> list[Diagnostic]:
    reset_to_clocks: dict[str, dict[str, AlwaysBlock]] = {}
    for module in design.modules:
        for block in module.always_blocks:
            if not block.is_sequential():
                continue
            events = _event_pairs(block)
            clocks = [signal for edge, signal in events if edge == "posedge" and CLOCK_NAME_RE.search(signal)]
            resets = [signal for edge, signal in events if edge in {"posedge", "negedge"} and RESET_NAME_RE.search(signal)]
            if not clocks or not resets:
                continue
            clock = clocks[0]
            for reset in resets:
                reset_to_clocks.setdefault(reset, {})[clock] = block
    diagnostics: list[Diagnostic] = []
    for reset, clocks in reset_to_clocks.items():
        if len(clocks) <= 1:
            continue
        block = next(iter(clocks.values()))
        diagnostics.append(_block_diag(block, "RTL009_ASYNC_RESET_RELEASE_RISK", "reset", f"异步复位 `{reset}` 被多个时钟域使用，释放时可能存在跨域风险。", "请确认复位释放是否按时钟域同步，或增加明确的复位同步器。", confidence="low"))
    return diagnostics


def _rule_unused_unconnected(design: Design, context: DesignContext) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for module in design.modules:
        if not module.span.file.endswith(".v"):
            continue
        module_context = context.modules.get(module.name)
        if module_context is None:
            continue
        reads = _module_read_names(module, module_context)
        writes = _module_written_names(module, design)
        symbols = _module_symbols(module)
        for name, signal in sorted(symbols.items()):
            if signal.data_type == "genvar" or name in module.parameters:
                continue
            if signal.direction == "input":
                if name not in reads:
                    diagnostics.append(
                        Diagnostic.make(
                            severity="warning",
                            rule="RTL017_UNUSED_INPUT",
                            category="unused_unconnected",
                            file=signal.span.file,
                            line=signal.span.line,
                            column=signal.span.column,
                            message=f"module input is never used: {name}",
                            message_zh=f"模块 `{module.name}` 的输入端口 `{name}` 在当前模块内没有被使用。",
                            suggestion_zh="请检查该输入是否遗漏连接到逻辑，或删除无用端口以减少接口噪声。",
                            confidence="medium",
                        )
                    )
                continue
            if signal.direction == "output":
                if name not in writes:
                    diagnostics.append(
                        Diagnostic.make(
                            severity="warning",
                            rule="RTL018_UNDRIVEN_OUTPUT",
                            category="unused_unconnected",
                            file=signal.span.file,
                            line=signal.span.line,
                            column=signal.span.column,
                            message=f"module output is never driven: {name}",
                            message_zh=f"模块 `{module.name}` 的输出端口 `{name}` 没有被赋值或实例输出驱动。",
                            suggestion_zh="请为该输出添加连续赋值、过程赋值或明确的子模块输出连接。",
                            confidence="high",
                        )
                    )
                continue
            if signal.direction == "inout":
                continue
            if name not in reads and name not in writes:
                diagnostics.append(
                    Diagnostic.make(
                        severity="warning",
                        rule="RTL015_UNUSED_SIGNAL",
                        category="unused_unconnected",
                        file=signal.span.file,
                        line=signal.span.line,
                        column=signal.span.column,
                        message=f"declared signal is never used: {name}",
                        message_zh=f"信号 `{name}` 已声明但没有被读取或驱动。",
                        suggestion_zh="请确认该信号是否为遗留代码；若无用途，建议删除或补齐连接。",
                        confidence="medium",
                    )
                )
            elif name in writes and name not in reads:
                diagnostics.append(
                    Diagnostic.make(
                        severity="warning",
                        rule="RTL016_ASSIGNED_NOT_READ",
                        category="unused_unconnected",
                        file=signal.span.file,
                        line=signal.span.line,
                        column=signal.span.column,
                        message=f"assigned signal is never read: {name}",
                        message_zh=f"信号 `{name}` 被驱动但没有被后续逻辑读取。",
                        suggestion_zh="请检查该赋值是否遗漏连接到输出或后续逻辑；若无用途，建议删除相关逻辑。",
                        confidence="medium",
                    )
                )
    return diagnostics


def _rule_constraint_clock_mismatch(design: Design, top: str | None, sdc_file: str) -> list[Diagnostic]:
    sdc_path = Path(sdc_file)
    clocks = parse_create_clocks(sdc_path)
    constrained = {clock.port for clock in clocks}
    diagnostics: list[Diagnostic] = []
    top_module = design.top_module(top)
    if not top_module:
        return diagnostics
    port_names = set(top_module.ports)
    for clock in clocks:
        if clock.port not in port_names:
            diagnostics.append(
                Diagnostic.make(
                    severity="warning",
                    rule="RTL010_CONSTRAINT_CLOCK_MISMATCH",
                    category="constraint",
                    file=sdc_path,
                    line=clock.line,
                    column=1,
                    message="SDC clock port is not found in RTL top ports",
                    message_zh=f"SDC 约束的时钟端口 `{clock.port}` 不存在于顶层模块端口中。",
                    suggestion_zh="请检查 create_clock 的 get_ports 名称是否与 RTL 顶层端口一致。",
                    confidence="high",
                )
            )
    for port in sorted(port_names):
        if CLOCK_NAME_RE.search(port) and port not in constrained:
            span = top_module.ports[port].span
            diagnostics.append(
                Diagnostic.make(
                    severity="warning",
                    rule="RTL010_CONSTRAINT_CLOCK_MISMATCH",
                    category="constraint",
                    file=span.file,
                    line=span.line,
                    column=span.column,
                    message="clock-like RTL port is unconstrained",
                    message_zh=f"顶层端口 `{port}` 像时钟，但 SDC 中没有对应 create_clock。",
                    suggestion_zh="请为该时钟端口添加 create_clock，或确认它不是实际时钟。",
                    confidence="medium",
                )
            )
    return diagnostics


def _block_diag(block: AlwaysBlock, rule: str, category: str, message_zh: str, suggestion_zh: str, confidence: str) -> Diagnostic:
    return Diagnostic.make(
        severity="warning",
        rule=rule,
        category=category,
        file=block.span.file,
        line=block.span.line,
        column=block.span.column,
        message=message_zh,
        message_zh=message_zh,
        suggestion_zh=suggestion_zh,
        confidence=confidence,
    )


def _operator_count(tokens: list) -> int:
    return sum(1 for token in tokens if token.value in LONG_COMB_OPS)


def _event_signals(block: AlwaysBlock) -> list[str]:
    return [signal for _, signal in _event_pairs(block)]


def _event_pairs(block: AlwaysBlock) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    tokens = block.sensitivity_tokens
    for index, token in enumerate(tokens[:-1]):
        if token.value in {"posedge", "negedge"} and tokens[index + 1].kind == "identifier":
            pairs.append((token.value, tokens[index + 1].value))
    return pairs


def _module_read_names(module: Module, module_context) -> set[str]:
    reads = {token.value for token in module_context.expression_identifier_tokens}
    for block in module.always_blocks:
        for token in block.body_tokens:
            if token.kind == "identifier" and token.value in module.declared_names():
                reads.add(token.value)
    return reads


def _module_written_names(module: Module, design: Design) -> set[str]:
    writes = {assignment.target for assignment in module.continuous_assigns}
    for block in module.always_blocks:
        writes.update(assignment.target for assignment in block.assignments)
    for generate_block in module.generate_blocks:
        writes.update(assignment.target for assignment in generate_block.assignments)
    for task in module.tasks.values():
        writes.update(assignment.target for assignment in task.assignments)
    writes.update(_instance_output_connection_writes(module, design))
    return writes


def _instance_output_connection_writes(module: Module, design: Design) -> set[str]:
    module_map = {item.name: item for item in design.modules}
    writes: set[str] = set()
    symbols = _module_symbols(module)
    for instance in module.instances:
        child = module_map.get(instance.module_type)
        if child is None:
            continue
        child_ports = list(child.ports.values())
        segments = _split_top_level(instance.connection_tokens, ",")
        if _uses_named_connections(segments):
            child_port_map = {port.name: port for port in child_ports}
            for segment in segments:
                port_name = _named_port(segment)
                if port_name is None:
                    continue
                child_port = child_port_map.get(port_name)
                if child_port is None or child_port.direction not in {"output", "inout"}:
                    continue
                writes.update(_connection_signal_names(_named_connection_expr(segment), symbols))
            continue
        for index, child_port in enumerate(child_ports):
            if child_port.direction not in {"output", "inout"}:
                continue
            expr = segments[index] if index < len(segments) else []
            writes.update(_connection_signal_names(expr, symbols))
    return writes


def _connection_signal_names(tokens: list[Token], symbols: dict[str, Signal]) -> set[str]:
    result: set[str] = set()
    for token in tokens:
        if token.kind == "identifier" and token.value in symbols:
            result.add(token.value)
    return result


def _module_symbols(module: Module) -> dict[str, Signal]:
    symbols: dict[str, Signal] = {}
    symbols.update(module.ports)
    symbols.update(module.declarations)
    symbols.update(module.parameters)
    return symbols


def _split_top_level(tokens: list[Token], separator: str) -> list[list[Token]]:
    parts: list[list[Token]] = []
    current: list[Token] = []
    depth = 0
    for token in tokens:
        if token.value in {"(", "[", "{"}:
            depth += 1
        elif token.value in {")", "]", "}"}:
            depth = max(0, depth - 1)
        if depth == 0 and token.value == separator:
            parts.append(current)
            current = []
        else:
            current.append(token)
    parts.append(current)
    return parts


def _uses_named_connections(segments: list[list[Token]]) -> bool:
    return any(segment and segment[0].value == "." for segment in segments)


def _named_port(segment: list[Token]) -> str | None:
    if len(segment) < 2 or segment[0].value != ".":
        return None
    token = segment[1]
    return token.value if token.kind == "identifier" else None


def _named_connection_expr(segment: list[Token]) -> list[Token]:
    for index, token in enumerate(segment):
        if token.value != "(":
            continue
        inner, close_index = _balanced_group(segment, index, "(", ")")
        if close_index is not None:
            return inner
    return []


def _balanced_group(
    tokens: list[Token],
    open_index: int,
    open_value: str,
    close_value: str,
) -> tuple[list[Token], int | None]:
    if open_index >= len(tokens) or tokens[open_index].value != open_value:
        return [], None
    depth = 1
    inner: list[Token] = []
    cursor = open_index + 1
    while cursor < len(tokens):
        token = tokens[cursor]
        if token.value == open_value:
            depth += 1
        elif token.value == close_value:
            depth -= 1
            if depth == 0:
                return inner, cursor
        inner.append(token)
        cursor += 1
    return inner, None


def _unconnected_port_diag(instance, child_port: Signal) -> Diagnostic:
    return Diagnostic.make(
        severity="warning",
        rule="RTL012_INSTANCE_PORT_UNCONNECTED",
        category="instantiation",
        file=instance.span.file,
        line=instance.span.line,
        column=instance.span.column,
        message=f"input port is not connected: {child_port.name}",
        message_zh=f"例化 `{instance.instance_name}` 的输入端口 `{child_port.name}` 未连接。",
        suggestion_zh="请连接该输入端口，或确认悬空输入不会影响仿真/综合结果。",
        confidence="high",
    )


def _unconnected_instance_output_diag(instance, child_port: Signal, span: Token) -> Diagnostic:
    return Diagnostic.make(
        severity="warning",
        rule="RTL019_INSTANCE_OUTPUT_UNCONNECTED",
        category="unused_unconnected",
        file=span.file,
        line=span.line,
        column=span.column,
        message=f"output port is left unconnected: {child_port.name}",
        message_zh=f"例化 `{instance.instance_name}` 的输出端口 `{child_port.name}` 未连接或使用了空连接。",
        suggestion_zh="请连接该输出端口，或确认该子模块输出确实不需要被上层逻辑使用。",
        confidence="medium",
    )


def _port_width_diagnostics(
    module: Module,
    caller_symbols: dict[str, Signal],
    instance,
    child_port: Signal,
    expr_tokens: list[Token],
) -> list[Diagnostic]:
    expected_width = _signal_width(child_port)
    actual_width = _expression_width(expr_tokens, caller_symbols)
    if expected_width is None or actual_width is None or expected_width == actual_width:
        return []
    token = expr_tokens[0] if expr_tokens else instance.span
    return [
        Diagnostic.make(
            severity="warning",
            rule="RTL013_PORT_WIDTH_MISMATCH",
            category="instantiation",
            file=token.file,
            line=token.line,
            column=token.column,
            message=f"port width mismatch: {child_port.name}",
            message_zh=(
                f"例化 `{instance.instance_name}` 的端口 `{child_port.name}` 宽度为 {expected_width}，"
                f"连接表达式宽度为 {actual_width}。"
            ),
            suggestion_zh="请检查端口声明和连接信号位宽，必要时显式扩展、截断或调整声明。",
            confidence="medium",
        )
    ]


def _select_range_diagnostics(symbols: dict[str, Signal], tokens: list[Token]) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    index = 0
    while index + 1 < len(tokens):
        token = tokens[index]
        if token.kind != "identifier" or tokens[index + 1].value != "[":
            index += 1
            continue
        signal = symbols.get(token.value)
        bounds = _signal_bounds(signal) if signal else None
        inner, close_index = _balanced_group(tokens, index + 1, "[", "]")
        if close_index is None:
            index += 1
            continue
        if bounds and len(inner) == 1 and inner[0].kind == "number":
            select_index = _parse_int_literal(inner[0].value)
            if select_index is not None:
                low = min(bounds)
                high = max(bounds)
                if select_index < low or select_index > high:
                    diagnostics.append(
                        Diagnostic.make(
                            severity="warning",
                            rule="RTL014_SELECT_RANGE",
                            category="semantic",
                            file=inner[0].file,
                            line=inner[0].line,
                            column=inner[0].column,
                            message=f"constant select out of range: {token.value}[{select_index}]",
                            message_zh=f"信号 `{token.value}` 的常量位选择 [{select_index}] 超出声明范围 [{high}:{low}]。",
                            suggestion_zh="请检查位选择下标，或确认信号声明宽度是否正确。",
                            confidence="high",
                        )
                    )
        index = close_index + 1
    return diagnostics


def _signal_width(signal: Signal | None) -> int | None:
    if signal is None:
        return None
    bounds = _signal_bounds(signal)
    if bounds is None:
        return 1
    return abs(bounds[0] - bounds[1]) + 1


def _signal_bounds(signal: Signal | None) -> tuple[int, int] | None:
    if signal is None or not signal.width:
        return None
    match = re.fullmatch(r"\[\s*([0-9]+)\s*:\s*([0-9]+)\s*\]", signal.width)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def _expression_width(tokens: list[Token], symbols: dict[str, Signal]) -> int | None:
    meaningful = [token for token in tokens if token.value not in {"(", ")"}]
    if not meaningful:
        return None
    if meaningful[0].value in {"&", "|", "^", "~&", "~|", "~^", "^~"}:
        return 1
    if len(meaningful) == 1:
        token = meaningful[0]
        if token.kind == "identifier":
            return _signal_width(symbols.get(token.value))
        if token.kind == "number":
            return _number_literal_width(token.value)
    if len(meaningful) >= 4 and meaningful[0].kind == "identifier" and meaningful[1].value == "[":
        inner, close_index = _balanced_group(meaningful, 1, "[", "]")
        if close_index == len(meaningful) - 1:
            colon_positions = [index for index, token in enumerate(inner) if token.value == ":"]
            if len(colon_positions) == 1:
                left = _parse_int_literal("".join(token.value for token in inner[: colon_positions[0]]))
                right = _parse_int_literal("".join(token.value for token in inner[colon_positions[0] + 1 :]))
                if left is not None and right is not None:
                    return abs(left - right) + 1
            if len(inner) == 1:
                return 1
    return None


def _number_literal_width(value: str) -> int | None:
    if "'" in value:
        width_text = value.split("'", 1)[0]
        if not width_text:
            return None
        try:
            return int(width_text.replace("_", ""))
        except ValueError:
            return None
    parsed = _parse_int_literal(value)
    if parsed is None:
        return None
    return max(parsed.bit_length(), 1)


def _parse_int_literal(value: str) -> int | None:
    text = value.replace("_", "")
    if "'" not in text:
        try:
            return int(text, 10)
        except ValueError:
            return None
    base_and_digits = text.split("'", 1)[1].lower()
    if not base_and_digits:
        return None
    if base_and_digits.startswith("s"):
        if len(base_and_digits) < 2:
            return None
        base_char = base_and_digits[1]
        digits = base_and_digits[2:]
    else:
        base_char = base_and_digits[0]
        digits = base_and_digits[1:]
    if any(ch in digits.lower() for ch in {"x", "z", "?"}):
        return None
    base = {"b": 2, "o": 8, "d": 10, "h": 16}.get(base_char.lower())
    if base is None:
        return None
    try:
        return int(digits, base)
    except ValueError:
        return None
