from __future__ import annotations

import re
from collections import defaultdict

from sta_lite.lint.ast_nodes import AlwaysBlock, Assignment, Module
from sta_lite.risk.feature_extractor import (
    RiskFeatures,
    assignment_expr_identifiers,
    block_read_identifiers,
    estimated_logic_depth,
    event_clock_names,
    event_pairs,
    event_reset_names,
    is_clock_name,
    is_control_name,
    is_reset_name,
    is_sync_name,
    module_symbols,
    operator_count,
    signal_width,
    token_identifiers,
    token_values,
)
from sta_lite.risk.models import RiskDiagnostic


DEFAULT_SETTINGS = {
    "long_comb_operator_threshold": 10,
    "high_fanout_context_threshold": 5,
    "wide_mux_branch_threshold": 6,
    "reset_register_threshold": 8,
    "reset_bit_threshold": 64,
    "clock_enable_register_threshold": 8,
    "clock_enable_bit_threshold": 64,
    "missing_pipeline_operator_threshold": 4,
}


def run_builtin_risk_rules(features: RiskFeatures, settings: dict[str, object] | None = None) -> list[RiskDiagnostic]:
    merged = dict(DEFAULT_SETTINGS)
    if settings:
        merged.update(settings)
    diagnostics: list[RiskDiagnostic] = []
    diagnostics.extend(_rule_async_reset_release_unsync(features))
    diagnostics.extend(
        _rule_excessive_reset(
            features,
            int(merged["reset_register_threshold"]),
            int(merged["reset_bit_threshold"]),
        )
    )
    diagnostics.extend(_rule_long_comb_path(features, int(merged["long_comb_operator_threshold"])))
    diagnostics.extend(_rule_latch_timing(features))
    diagnostics.extend(_rule_high_fanout_control(features, int(merged["high_fanout_context_threshold"])))
    diagnostics.extend(_rule_gated_or_derived_clock(features))
    diagnostics.extend(_rule_combinational_loop(features))
    diagnostics.extend(_rule_fsm_robustness(features))
    diagnostics.extend(_rule_wide_mux_priority_encoder(features, int(merged["wide_mux_branch_threshold"])))
    diagnostics.extend(_rule_arith_chain_no_pipeline(features))
    diagnostics.extend(_rule_ram_inference(features))
    diagnostics.extend(_rule_dsp_inference(features))
    diagnostics.extend(_rule_missing_pipeline(features, int(merged["missing_pipeline_operator_threshold"])))
    diagnostics.extend(
        _rule_high_fanout_clock_enable(
            features,
            int(merged["clock_enable_register_threshold"]),
            int(merged["clock_enable_bit_threshold"]),
        )
    )
    diagnostics.extend(_rule_async_data_control(features))
    diagnostics.extend(_rule_cdc_unsync_signal(features))
    diagnostics.extend(_rule_multicycle_without_constraint(features))
    diagnostics.extend(_rule_io_constraint_missing(features))
    diagnostics.extend(_rule_memory_or_dsp_chain_no_pipeline(features))
    return _dedupe(diagnostics)


def _rule_excessive_reset(
    features: RiskFeatures,
    register_threshold: int,
    bit_threshold: int,
) -> list[RiskDiagnostic]:
    """Estimate reset scope directly from clocked RTL reset branches.

    This deliberately reports structural scope only.  It does not infer reset
    tree buffering, routing, placement congestion, or signoff timing.
    """
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        symbols = module_symbols(module)
        grouped: dict[tuple[str, str, str], dict[str, object]] = {}
        for block in module.always_blocks:
            if not block.is_sequential():
                continue
            reset = _reset_branch_info(block)
            if reset is None:
                continue
            reset_name, reset_kind, polarity, branch_tokens = reset
            targets = _branch_assignment_targets(branch_tokens)
            if not targets:
                continue
            item = grouped.setdefault(
                (reset_name, reset_kind, polarity),
                {"targets": set(), "locations": [], "blocks": 0},
            )
            item["targets"].update(targets)  # type: ignore[index]
            item["locations"].append({"file": block.span.file, "line": block.span.line, "column": block.span.column})  # type: ignore[index]
            item["blocks"] = int(item["blocks"]) + 1  # type: ignore[index]
        for (reset_name, reset_kind, polarity), item in sorted(grouped.items()):
            targets = sorted(str(name) for name in item["targets"])  # type: ignore[index]
            widths = {name: signal_width(symbols.get(name)) or 1 for name in targets}
            bit_count = sum(widths.values())
            register_count = len(targets)
            if register_count < register_threshold and bit_count < bit_threshold:
                continue
            locations = list(item["locations"])  # type: ignore[index]
            first = locations[0] if locations else {"file": module.span.file, "line": module.span.line, "column": module.span.column}
            severity = "high" if register_count >= 2 * register_threshold or bit_count >= 2 * bit_threshold else "medium"
            diagnostics.append(
                RiskDiagnostic.make(
                    rule="RISK_EXCESSIVE_RESET",
                    severity=severity,
                    category="reset_usage",
                    file=str(first["file"]),
                    line=int(first["line"]),
                    column=int(first["column"]),
                    module=module.name,
                    message_zh=(
                        f"复位 `{reset_name}`（{reset_kind}、{polarity}）覆盖 {register_count} 个寄存器、"
                        f"估算 {bit_count} 个 reset 位，达到 RTL reset 范围风险阈值。"
                    ),
                    suggestion_zh="请确认数据通路寄存器是否都必须复位；可仅复位控制状态、使用初始化/有效位，或按时钟域拆分 reset。该提示不代表真实复位树时序或布线结论。",
                    confidence="high",
                    evidence={
                        "reset_signal": reset_name,
                        "reset_kind": reset_kind,
                        "polarity": polarity,
                        "affected_registers": targets,
                        "register_widths": widths,
                        "estimated_reset_bits": bit_count,
                        "thresholds": {"register_count": register_threshold, "reset_bits": bit_threshold},
                        "clocked_block_count": item["blocks"],
                        "locations": locations,
                        "scope": "RTL 结构统计；不建模物理 reset tree、布线或 signoff 时序。",
                    },
                )
            )
    return diagnostics


def _rule_async_reset_release_unsync(features: RiskFeatures) -> list[RiskDiagnostic]:
    reset_to_clocks: dict[str, set[str]] = defaultdict(set)
    reset_blocks: dict[str, list[tuple[Module, AlwaysBlock]]] = defaultdict(list)
    sync_like_resets: set[str] = set()
    for module in features.design.modules:
        for block in module.always_blocks:
            if not block.is_sequential():
                continue
            resets = event_reset_names(block)
            clocks = event_clock_names(block)
            if any(is_sync_name(assignment.target) for assignment in block.assignments):
                sync_like_resets.update(resets)
            for reset in resets:
                for clock in clocks:
                    reset_to_clocks[reset].add(clock)
                reset_blocks[reset].append((module, block))
    diagnostics: list[RiskDiagnostic] = []
    for reset, blocks in reset_blocks.items():
        if reset in sync_like_resets:
            continue
        module, block = blocks[0]
        clocks = sorted(reset_to_clocks.get(reset, set()))
        severity = "high" if len(clocks) > 1 else "medium"
        confidence = "medium" if len(clocks) > 1 else "low"
        diagnostics.append(
            _block_diag(
                block,
                module,
                rule="RISK_ASYNC_RESET_RELEASE_UNSYNC",
                severity=severity,
                category="reset_timing",
                message_zh=f"异步复位 `{reset}` 直接进入时序逻辑，未看到明显的复位释放同步器。",
                suggestion_zh="建议为每个接收时钟域使用异步置位、同步释放的 reset synchronizer，或在代码中标出已验证的复位同步结构。",
                confidence=confidence,
                evidence={"reset": reset, "clock_domains": clocks, "async_reset_block_count": len(blocks)},
            )
        )
    return diagnostics


def _rule_long_comb_path(features: RiskFeatures, threshold: int) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        for block in module.always_blocks:
            if not block.is_combinational():
                continue
            count = operator_count(block.body_tokens)
            depth = estimated_logic_depth(block.body_tokens)
            if count < threshold:
                continue
            severity = "high" if count >= threshold + 5 or depth >= threshold + 8 else "medium"
            diagnostics.append(
                _block_diag(
                    block,
                    module,
                    rule="RISK_LONG_COMB_PATH",
                    severity=severity,
                    category="timing_setup",
                    message_zh="组合 always 块中的算术、比较或选择操作较多，可能形成 setup 关键路径。",
                    suggestion_zh="考虑插入流水寄存器、拆分表达式、降低单周期逻辑深度，或在后端报告中重点观察对应路径。",
                    confidence="medium",
                    evidence={"operator_count": count, "estimated_logic_depth": depth},
                )
            )
        for assignment in module.continuous_assigns:
            count = operator_count(assignment.expr_tokens)
            depth = estimated_logic_depth(assignment.expr_tokens)
            if count < threshold:
                continue
            severity = "high" if count >= threshold + 5 or depth >= threshold + 8 else "medium"
            diagnostics.append(
                _assignment_diag(
                    assignment,
                    module,
                    rule="RISK_LONG_COMB_PATH",
                    severity=severity,
                    category="timing_setup",
                    message_zh=f"连续赋值 `{assignment.target}` 的组合表达式较复杂，可能形成长组合路径。",
                    suggestion_zh="考虑把表达式拆分到寄存器边界之间，或在后端 STA 中确认该逻辑是否为关键路径。",
                    confidence="medium",
                    evidence={"target": assignment.target, "operator_count": count, "estimated_logic_depth": depth},
                )
            )
    return diagnostics


def _rule_latch_timing(features: RiskFeatures) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        for block in module.always_blocks:
            if not block.is_combinational() or not block.assignments:
                continue
            values = token_values(block.body_tokens)
            risky_targets = _conditional_targets_without_default(block)
            if not risky_targets:
                continue
            if values.count("if") > values.count("else"):
                targets = ", ".join(sorted(risky_targets))
                diagnostics.append(
                    _block_diag(
                        block,
                        module,
                        rule="RISK_LATCH_TIMING",
                        severity="high",
                        category="latch_timing",
                        message_zh=f"组合逻辑中目标 `{targets}` 存在未覆盖 else/default 的 if 分支，可能推断 latch 并引入难收敛时序路径。",
                        suggestion_zh="为组合输出添加默认赋值，或补齐所有 if/else 分支，避免非预期锁存器。",
                        confidence="high",
                        evidence={"if_count": values.count("if"), "else_count": values.count("else"), "targets_without_default": sorted(risky_targets)},
                    )
                )
            elif any(value in {"case", "casez", "casex"} for value in values) and "default" not in values:
                targets = ", ".join(sorted(risky_targets))
                diagnostics.append(
                    _block_diag(
                        block,
                        module,
                        rule="RISK_LATCH_TIMING",
                        severity="high",
                        category="latch_timing",
                        message_zh=f"组合 case 语句缺少 default，目标 `{targets}` 可能推断 latch。",
                        suggestion_zh="添加 default 分支，或在 case 前给目标信号默认赋值。",
                        confidence="high",
                        evidence={"has_case": True, "has_default": False, "targets_without_default": sorted(risky_targets)},
                    )
                )
    return diagnostics


def _rule_high_fanout_control(features: RiskFeatures, threshold: int) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        symbols = module_symbols(module)
        usage: dict[str, set[str]] = defaultdict(set)
        first_block: dict[str, AlwaysBlock] = {}
        first_assignment: dict[str, Assignment] = {}
        for block_index, block in enumerate(module.always_blocks):
            names = set(token_identifiers(block.sensitivity_tokens)) | block_read_identifiers(block)
            for name in names:
                if name in symbols and is_control_name(name):
                    usage[name].add(f"always:{block_index}")
                    first_block.setdefault(name, block)
        for assign_index, assignment in enumerate(module.continuous_assigns):
            for name in assignment_expr_identifiers(assignment):
                if name in symbols and is_control_name(name):
                    usage[name].add(f"assign:{assign_index}")
                    first_assignment.setdefault(name, assignment)
        for inst_index, instance in enumerate(module.instances):
            for name in token_identifiers(instance.connection_tokens):
                if name in symbols and is_control_name(name):
                    usage[name].add(f"instance:{inst_index}")
        for name, contexts in sorted(usage.items()):
            if len(contexts) < threshold:
                continue
            evidence = {"signal": name, "fanout_context_count": len(contexts), "contexts": sorted(contexts)[:20]}
            if name in first_block:
                diagnostics.append(
                    _block_diag(
                        first_block[name],
                        module,
                        rule="RISK_HIGH_FANOUT_CONTROL",
                        severity="medium",
                        category="fanout_timing",
                        message_zh=f"控制/复位/使能信号 `{name}` 在多个逻辑上下文中使用，可能形成高扇出控制路径。",
                        suggestion_zh="后端若出现该信号相关关键路径，可考虑控制信号复制、局部使能寄存器或层次化分发。",
                        confidence="low",
                        evidence=evidence,
                    )
                )
            else:
                diagnostics.append(
                    _assignment_diag(
                        first_assignment[name],
                        module,
                        rule="RISK_HIGH_FANOUT_CONTROL",
                        severity="medium",
                        category="fanout_timing",
                        message_zh=f"控制/复位/使能信号 `{name}` 使用范围较广，可能形成高扇出控制路径。",
                        suggestion_zh="检查该控制信号是否需要局部寄存或分层复制，避免单点扇出过大。",
                        confidence="low",
                        evidence=evidence,
                    )
                )
    return diagnostics


def _rule_gated_or_derived_clock(features: RiskFeatures) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    derived_clock_targets: set[str] = set()
    for module in features.design.modules:
        for assignment in module.continuous_assigns:
            expr_values = token_values(assignment.expr_tokens)
            expr_ids = token_identifiers(assignment.expr_tokens)
            creates_clock = is_clock_name(assignment.target) and (
                any(op in expr_values for op in {"&", "|", "^", "?", "~"}) or any(is_clock_name(name) for name in expr_ids)
            )
            if not creates_clock:
                continue
            derived_clock_targets.add(assignment.target)
            diagnostics.append(
                _assignment_diag(
                    assignment,
                    module,
                    rule="RISK_GATED_OR_DERIVED_CLOCK",
                    severity="high" if any(op in expr_values for op in {"&", "|", "^", "?"}) else "medium",
                    category="clock_timing",
                    message_zh=f"信号 `{assignment.target}` 由 RTL 逻辑生成，疑似门控或派生时钟。",
                    suggestion_zh="优先使用时钟使能或专用时钟门控单元；若确实是 generated clock，需要在约束中明确声明。",
                    confidence="medium",
                    evidence={"target": assignment.target, "expr_identifiers": expr_ids, "operators": sorted(set(expr_values) & {"&", "|", "^", "?", "~"})},
                )
            )
        for block in module.always_blocks:
            if not block.is_sequential():
                continue
            sens_values = token_values(block.sensitivity_tokens)
            if any(op in sens_values for op in {"&", "|", "^", "?", "~"}):
                diagnostics.append(
                    _block_diag(
                        block,
                        module,
                        rule="RISK_GATED_OR_DERIVED_CLOCK",
                        severity="high",
                        category="clock_timing",
                        message_zh="时序 always 的事件控制中出现逻辑表达式，疑似门控时钟。",
                        suggestion_zh="事件控制应使用简单时钟边沿，条件逻辑放到 always 块内部用 clock enable 表达。",
                        confidence="high",
                        evidence={"sensitivity": " ".join(sens_values)},
                    )
                )
                continue
            for clock in event_clock_names(block):
                if clock in derived_clock_targets:
                    diagnostics.append(
                        _block_diag(
                            block,
                            module,
                            rule="RISK_GATED_OR_DERIVED_CLOCK",
                            severity="medium",
                            category="clock_timing",
                            message_zh=f"时序逻辑使用派生时钟 `{clock}`。",
                            suggestion_zh="请确认该时钟来自安全时钟资源；否则建议改为原始时钟加 clock enable。",
                            confidence="medium",
                            evidence={"clock": clock},
                    )
                )
    return diagnostics


def _rule_combinational_loop(features: RiskFeatures) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        graph, edge_records = _combinational_dependency_graph(module)
        for scc in _tarjan_scc(graph):
            members = sorted(scc)
            member_set = set(members)
            has_self_loop = len(members) == 1 and members[0] in graph.get(members[0], set())
            if len(members) < 2 and not has_self_loop:
                continue
            edges: list[dict[str, object]] = []
            for (target, source), records in sorted(edge_records.items()):
                if target not in member_set or source not in member_set:
                    continue
                edges.extend(records[:3])
            first_edge = edges[0] if edges else {
                "file": module.span.file,
                "line": module.span.line,
                "column": module.span.column,
            }
            cycle_path = _cycle_path(members, graph)
            diagnostics.append(
                RiskDiagnostic.make(
                    rule="RISK_COMBINATIONAL_LOOP",
                    severity="high",
                    category="combinational_loop",
                    file=str(first_edge.get("file") or module.span.file),
                    line=int(first_edge.get("line") or module.span.line or 1),
                    column=int(first_edge.get("column") or module.span.column or 1),
                    module=module.name,
                    message_zh=f"组合逻辑依赖图中发现环路：{' -> '.join(cycle_path)}。",
                    suggestion_zh="请在该反馈路径中加入明确寄存器边界，或重写组合赋值，避免综合后形成不稳定的组合环。",
                    confidence="high" if edges else "medium",
                    evidence={
                        "scc_nodes": members,
                        "cycle_path": cycle_path,
                        "edge_count": len(edges),
                        "edges": edges[:20],
                        "runtime_dependency": "STA-lite 内部 RTL 图分析；正常运行不依赖 Yosys。",
                    },
                )
            )
    return diagnostics


def _rule_fsm_robustness(features: RiskFeatures) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        parameter_values = _parameter_value_map(module)
        for seq_block, state_reg in _state_register_candidates(module):
            next_state = _next_state_signal(seq_block, state_reg, module)
            if not next_state:
                continue
            transition = _find_transition_case(module, state_reg, next_state)
            if not transition:
                continue
            comb_block, case_info = transition
            reset_state = _reset_state_from_block(seq_block, state_reg, next_state)
            declared_states = _declared_fsm_states(module, state_reg, next_state, case_info, parameter_values)
            handled_states = set(case_info["handled_labels"])
            reset_state_label = _normalize_state_expr(reset_state, parameter_values)

            if reset_state is None:
                diagnostics.append(
                    _fsm_diag(
                        seq_block,
                        module,
                        state_reg=state_reg,
                        next_state=next_state,
                        issue="missing_reset",
                        severity="high",
                        confidence="high",
                        message_zh=f"状态寄存器 `{state_reg}` 未看到明确 reset/default 初始化。",
                        suggestion_zh="建议在时序 always 中把状态寄存器复位到已知安全状态，避免上电或复位释放后进入未知状态。",
                        evidence={
                            "state_register": state_reg,
                            "next_state_signal": next_state,
                            "reset_state": None,
                            "clock_events": event_clock_names(seq_block),
                        },
                    )
                )

            if not case_info["has_default"]:
                diagnostics.append(
                    _fsm_diag(
                        comb_block,
                        module,
                        state_reg=state_reg,
                        next_state=next_state,
                        issue="missing_case_default",
                        severity="high",
                        confidence="high",
                        message_zh=f"FSM `{state_reg}` 的 next-state case 缺少 default 分支。",
                        suggestion_zh="建议添加 default 分支并恢复到已知安全状态，覆盖非法状态和编码扰动。",
                        evidence=_fsm_case_evidence(state_reg, next_state, reset_state, declared_states, handled_states, case_info),
                    )
                )
            elif reset_state is not None:
                default_status = _default_recovery_status(case_info["default_tokens"], state_reg, next_state, reset_state, parameter_values)
                if default_status["unsafe"]:
                    diagnostics.append(
                        _fsm_diag(
                            comb_block,
                            module,
                            state_reg=state_reg,
                            next_state=next_state,
                            issue="unsafe_default_recovery",
                            severity="medium",
                            confidence="high",
                            message_zh=f"FSM `{state_reg}` 的 default 分支没有恢复到已知安全状态。",
                            suggestion_zh="建议让 default 明确跳转到 reset/IDLE 等安全状态，而不是保持当前状态或不赋值。",
                            evidence={
                                **_fsm_case_evidence(state_reg, next_state, reset_state, declared_states, handled_states, case_info),
                                "default_assignment": default_status["assignment"],
                                "reason_zh": default_status["reason_zh"],
                            },
                        )
                    )

            incomplete_targets = _conditional_targets_without_default(comb_block)
            if next_state in incomplete_targets:
                diagnostics.append(
                    _fsm_diag(
                        comb_block,
                        module,
                        state_reg=state_reg,
                        next_state=next_state,
                        issue="incomplete_next_state_assignment",
                        severity="high",
                        confidence="high",
                        message_zh=f"FSM `{state_reg}` 的组合 next-state 逻辑可能没有覆盖 `{next_state}` 的所有赋值路径。",
                        suggestion_zh="建议在 case/if 前给 next-state 默认赋值，或补齐所有分支，避免 latch 和不可预期状态保持。",
                        evidence={
                            **_fsm_case_evidence(state_reg, next_state, reset_state, declared_states, handled_states, case_info),
                            "targets_without_default": sorted(incomplete_targets),
                        },
                    )
                )

            missing_states = _missing_declared_states(declared_states, handled_states, parameter_values)
            if missing_states:
                diagnostics.append(
                    _fsm_diag(
                        comb_block,
                        module,
                        state_reg=state_reg,
                        next_state=next_state,
                        issue="declared_state_not_handled",
                        severity="medium",
                        confidence="medium",
                        message_zh=f"FSM `{state_reg}` 有声明状态未在转移 case 中显式处理：{', '.join(missing_states)}。",
                        suggestion_zh="建议为每个声明状态添加明确转移，default 只作为非法状态恢复路径。",
                        evidence={
                            **_fsm_case_evidence(state_reg, next_state, reset_state, declared_states, handled_states, case_info),
                            "missing_states": missing_states,
                        },
                    )
                )

            for terminal_state in _obvious_terminal_states(case_info, next_state, parameter_values):
                if reset_state_label and _same_state_value(terminal_state, reset_state_label, parameter_values):
                    continue
                diagnostics.append(
                    _fsm_diag(
                        comb_block,
                        module,
                        state_reg=state_reg,
                        next_state=next_state,
                        issue="obvious_terminal_state",
                        severity="medium",
                        confidence="medium",
                        message_zh=f"FSM `{state_reg}` 的状态 `{terminal_state}` 只看到自环转移，可能成为终止/死状态。",
                        suggestion_zh="若该状态不是有意终止状态，请添加明确退出条件；若有意保持，建议用注释或后续 waiver 机制说明。",
                        evidence={
                            **_fsm_case_evidence(state_reg, next_state, reset_state, declared_states, handled_states, case_info),
                            "terminal_state": terminal_state,
                        },
                    )
                )
    return diagnostics


def _rule_wide_mux_priority_encoder(features: RiskFeatures, threshold: int) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        symbols = module_symbols(module)
        for block in module.always_blocks:
            if not block.is_combinational():
                continue
            values = token_values(block.body_tokens)
            target_counts: dict[str, int] = defaultdict(int)
            for assignment in block.assignments:
                target_counts[assignment.target] += 1
            branch_count = max(
                values.count("if") + values.count("?") + values.count("case") + values.count("casez") + values.count("casex"),
                max(target_counts.values(), default=0),
            )
            if branch_count < threshold:
                continue
            output_width = max((signal_width(symbols.get(assignment.target)) or 1 for assignment in block.assignments), default=1)
            severity = "high" if branch_count >= threshold + 3 and output_width >= 16 else "medium"
            diagnostics.append(
                _block_diag(
                    block,
                    module,
                    rule="RISK_WIDE_MUX_PRIORITY_ENCODER",
                    severity=severity,
                    category="timing_setup",
                    message_zh=f"组合逻辑中分支/选择结构较多，估算输出宽度 {output_width}，可能综合成宽 mux 或优先级编码器。",
                    suggestion_zh="如果不需要优先级，优先使用明确 case/default；必要时拆分选择网络或增加流水。",
                    confidence="medium",
                    evidence={"branch_count": branch_count, "estimated_output_width": output_width, "selector_tokens": values.count("if") + values.count("case")},
                )
            )
    return diagnostics


def _rule_arith_chain_no_pipeline(features: RiskFeatures) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        symbols = module_symbols(module)
        for assignment in module.continuous_assigns:
            values = token_values(assignment.expr_tokens)
            arith_count = sum(1 for value in values if value in {"*", "/", "%", "+", "-", ">", "<", ">=", "<=", "==", "!="})
            mult_count = values.count("*")
            operand_width = _max_identifier_width(assignment.expr_tokens, symbols)
            if arith_count < 5 or mult_count < 1 or operand_width < 8:
                continue
            severity = "high" if mult_count >= 2 and operand_width >= 16 else "medium"
            diagnostics.append(
                _assignment_diag(
                    assignment,
                    module,
                    rule="RISK_ARITH_CHAIN_NO_PIPELINE",
                    severity=severity,
                    category="timing_setup",
                    message_zh=f"连续赋值 `{assignment.target}` 包含乘法/加法/比较链，可能缺少流水寄存器。",
                    suggestion_zh="检查目标频率下是否需要 DSP/算术链流水，避免把多级算术压在一个周期内。",
                    confidence="medium",
                    evidence={"target": assignment.target, "arithmetic_operator_count": arith_count, "multiply_count": mult_count, "max_operand_width": operand_width},
                )
            )
        for block in module.always_blocks:
            if not block.is_combinational():
                continue
            values = token_values(block.body_tokens)
            arith_count = sum(1 for value in values if value in {"*", "/", "%", "+", "-", ">", "<", ">=", "<=", "==", "!="})
            mult_count = values.count("*")
            operand_width = _max_identifier_width(block.body_tokens, symbols)
            if arith_count < 6 or mult_count < 1 or operand_width < 8:
                continue
            severity = "high" if mult_count >= 2 and operand_width >= 16 else "medium"
            diagnostics.append(
                _block_diag(
                    block,
                    module,
                    rule="RISK_ARITH_CHAIN_NO_PIPELINE",
                    severity=severity,
                    category="timing_setup",
                    message_zh="组合块包含乘法/加法/比较链，可能缺少流水寄存器。",
                    suggestion_zh="考虑在算术链中间加入寄存器，或利用目标器件的 DSP pipeline。",
                    confidence="medium",
                    evidence={"arithmetic_operator_count": arith_count, "multiply_count": mult_count, "max_operand_width": operand_width},
                )
            )
    return diagnostics


def _rule_ram_inference(features: RiskFeatures) -> list[RiskDiagnostic]:
    """识别常见 unpacked reg/logic 数组及其 RTL 读写形态。"""
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        for memory in _memory_declarations(module):
            name = str(memory["name"])
            indexed_reads = 0
            indexed_writes = 0
            sequential_writes = 0
            sequential_reads = 0
            asynchronous_reads = 0
            first_block: AlwaysBlock | None = None
            first_assignment: Assignment | None = None
            for block in module.always_blocks:
                values = token_values(block.body_tokens)
                uses = _indexed_identifier_count(block.body_tokens, name)
                if not uses:
                    continue
                first_block = first_block or block
                writes = sum(1 for assignment in block.assignments if assignment.target == name)
                reads = max(0, uses - writes)
                indexed_writes += writes
                indexed_reads += reads
                if block.is_sequential():
                    sequential_writes += writes
                    sequential_reads += reads
                else:
                    asynchronous_reads += reads
                if "[" in values and name in values:
                    indexed_reads = max(indexed_reads, 1)
            for assignment in module.continuous_assigns:
                uses = _indexed_identifier_count(assignment.expr_tokens, name)
                if uses:
                    indexed_reads += uses
                    asynchronous_reads += uses
                    first_assignment = first_assignment or assignment
            if not indexed_reads and not indexed_writes:
                continue
            evidence = {
                **memory,
                "indexed_read_count": indexed_reads,
                "indexed_write_count": indexed_writes,
                "sequential_write_count": sequential_writes,
                "sequential_read_count": sequential_reads,
                "asynchronous_read_count": asynchronous_reads,
                "scope": "常见 unpacked 数组结构识别；不承诺目标器件最终映射为 RAM 宏。",
            }
            severity = "medium" if asynchronous_reads or not sequential_writes else "low"
            message = f"数组 `{name}` 具有 RAM 推断形态"
            if asynchronous_reads:
                message += "，且存在组合/异步读"
            message += "。"
            if first_block is not None:
                diagnostics.append(
                    _block_diag(
                        first_block,
                        module,
                        rule="RISK_RAM_INFERENCE",
                        severity=severity,
                        category="memory_inference",
                        message_zh=message,
                        suggestion_zh="请根据目标器件 RAM 模板核对同步读写、读写冲突语义和输出寄存；最终映射以综合报告为准。",
                        confidence="medium",
                        evidence=evidence,
                    )
                )
            elif first_assignment is not None:
                diagnostics.append(
                    _assignment_diag(
                        first_assignment,
                        module,
                        rule="RISK_RAM_INFERENCE",
                        severity=severity,
                        category="memory_inference",
                        message_zh=message,
                        suggestion_zh="请根据目标器件 RAM 模板核对同步读写、读写冲突语义和输出寄存；最终映射以综合报告为准。",
                        confidence="medium",
                        evidence=evidence,
                    )
                )
    return diagnostics


def _rule_dsp_inference(features: RiskFeatures) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        symbols = module_symbols(module)
        for assignment in module.continuous_assigns:
            values = token_values(assignment.expr_tokens)
            multiply_count = values.count("*")
            width = _max_identifier_width(assignment.expr_tokens, symbols)
            if not multiply_count or width < 8:
                continue
            diagnostics.append(
                _assignment_diag(
                    assignment,
                    module,
                    rule="RISK_DSP_INFERENCE",
                    severity="medium" if width >= 16 or multiply_count > 1 else "low",
                    category="dsp_inference",
                    message_zh=f"连续赋值 `{assignment.target}` 包含 {width} bit 级乘法，具有 DSP 推断候选形态。",
                    suggestion_zh="核对目标器件 DSP 推断模板、输入/乘法/累加/输出寄存级；最终 DSP 映射以综合报告为准。",
                    confidence="medium",
                    evidence={"target": assignment.target, "multiply_count": multiply_count, "max_operand_width": width, "add_sub_count": values.count("+") + values.count("-"), "registered": False},
                )
            )
        for block in module.always_blocks:
            values = token_values(block.body_tokens)
            multiply_count = values.count("*")
            width = _max_identifier_width(block.body_tokens, symbols)
            if not multiply_count or width < 8:
                continue
            diagnostics.append(
                _block_diag(
                    block,
                    module,
                    rule="RISK_DSP_INFERENCE",
                    severity="medium" if width >= 16 or multiply_count > 1 else "low",
                    category="dsp_inference",
                    message_zh=f"过程块包含 {width} bit 级乘法，具有 DSP 推断候选形态。",
                    suggestion_zh="核对目标器件 DSP 推断模板和寄存器级；该提示不等价于综合后的 DSP 映射结论。",
                    confidence="medium",
                    evidence={"multiply_count": multiply_count, "max_operand_width": width, "add_sub_count": values.count("+") + values.count("-"), "registered": block.is_sequential()},
                )
            )
    return diagnostics


def _rule_missing_pipeline(features: RiskFeatures, threshold: int) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        symbols = module_symbols(module)
        candidates: list[tuple[Assignment | AlwaysBlock, list[object], str]] = []
        candidates.extend((assignment, assignment.expr_tokens, "continuous_assign") for assignment in module.continuous_assigns)
        candidates.extend((block, block.body_tokens, "combinational_block") for block in module.always_blocks if block.is_combinational())
        for owner, tokens, kind in candidates:
            values = token_values(tokens)
            ops = operator_count(tokens)
            branch_ops = sum(values.count(value) for value in ("?", "if", "case", "casez", "casex"))
            comparisons = sum(values.count(value) for value in (">", "<", ">=", "<=", "==", "!="))
            width = _max_identifier_width(tokens, symbols)
            complex_enough = ops >= threshold and width >= 8 and (branch_ops >= 2 or comparisons >= 2 or values.count("*") >= 1 or ops >= threshold + 2)
            if not complex_enough:
                continue
            evidence = {"context": kind, "operator_count": ops, "branch_operator_count": branch_ops, "comparison_count": comparisons, "multiply_count": values.count("*"), "max_operand_width": width, "register_boundary_in_context": False, "threshold": threshold}
            kwargs = dict(
                rule="RISK_MISSING_PIPELINE",
                severity="high" if ops >= threshold + 4 and width >= 16 else "medium",
                category="pipeline",
                message_zh="寄存器边界之间存在较深的宽组合算术、比较或选择网络，可能缺少流水。",
                suggestion_zh="结合目标频率检查该组合网络；必要时拆分表达式并加入流水寄存器。此规则只做 RTL 结构筛查，不预测真实 slack。",
                confidence="medium",
                evidence=evidence,
            )
            if isinstance(owner, Assignment):
                diagnostics.append(_assignment_diag(owner, module, **kwargs))
            else:
                diagnostics.append(_block_diag(owner, module, **kwargs))
    return diagnostics


def _rule_high_fanout_clock_enable(features: RiskFeatures, register_threshold: int, bit_threshold: int) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        symbols = module_symbols(module)
        grouped: dict[str, dict[str, object]] = {}
        for block in module.always_blocks:
            if not block.is_sequential():
                continue
            info = _first_control_branch_info(block)
            if info is None:
                continue
            enable, branch_tokens = info
            if is_reset_name(enable) or is_clock_name(enable):
                continue
            targets = _branch_assignment_targets(branch_tokens)
            if not targets:
                continue
            item = grouped.setdefault(enable, {"targets": set(), "blocks": [], "first_block": block})
            item["targets"].update(targets)  # type: ignore[index]
            item["blocks"].append({"file": block.span.file, "line": block.span.line, "column": block.span.column})  # type: ignore[index]
        for enable, item in sorted(grouped.items()):
            targets = sorted(str(name) for name in item["targets"])  # type: ignore[index]
            widths = {name: signal_width(symbols.get(name)) or 1 for name in targets}
            bits = sum(widths.values())
            if len(targets) < register_threshold and bits < bit_threshold:
                continue
            block = item["first_block"]
            diagnostics.append(
                _block_diag(
                    block,
                    module,
                    rule="RISK_HIGH_FANOUT_CLOCK_ENABLE",
                    severity="high" if len(targets) >= 2 * register_threshold or bits >= 2 * bit_threshold else "medium",
                    category="clock_enable",
                    message_zh=f"时钟使能 `{enable}` 控制 {len(targets)} 个寄存器、估算 {bits} bit 数据，存在高扇出 CE 风险。",
                    suggestion_zh="确认使能是否需要覆盖全部数据寄存器；后端若出现 CE 相关关键路径，可分层复制或局部寄存使能。",
                    confidence="high" if is_control_name(enable) else "medium",
                    evidence={"clock_enable": enable, "affected_registers": targets, "register_widths": widths, "estimated_enable_bits": bits, "thresholds": {"register_count": register_threshold, "enable_bits": bit_threshold}, "locations": item["blocks"], "scope": "RTL 寄存器负载统计，不建模综合后的门级扇出与物理布线。"},
                )
            )
    return diagnostics


def _rule_async_data_control(features: RiskFeatures) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        for block in module.always_blocks:
            pairs = event_pairs(block)
            clocks = [signal for _edge, signal in pairs if is_clock_name(signal)]
            async_controls = [(edge, signal) for edge, signal in pairs if not is_clock_name(signal) and not is_reset_name(signal)]
            if not clocks or not async_controls:
                continue
            for edge, signal in async_controls:
                diagnostics.append(
                    _block_diag(
                        block,
                        module,
                        rule="RISK_ASYNC_DATA_CONTROL",
                        severity="high",
                        category="async_path",
                        message_zh=f"复位之外的信号 `{signal}` 作为异步事件控制进入时序过程。",
                        suggestion_zh="普通数据/控制信号不应直接进入触发事件；请在目标时钟域同步脉冲或电平，跨域多 bit 数据使用握手或异步 FIFO。",
                        confidence="high",
                        evidence={"async_signal": signal, "edge": edge, "clock_events": clocks, "all_events": [{"edge": event_edge, "signal": event_signal} for event_edge, event_signal in pairs]},
                    )
                )
    return diagnostics


def _rule_cdc_unsync_signal(features: RiskFeatures) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        symbols = module_symbols(module)
        writers: dict[str, set[str]] = defaultdict(set)
        writer_block: dict[str, AlwaysBlock] = {}
        readers: dict[str, set[str]] = defaultdict(set)
        reader_block: dict[str, AlwaysBlock] = {}
        for block in module.always_blocks:
            clocks = set(event_clock_names(block))
            if not clocks:
                continue
            for assignment in block.assignments:
                writers[assignment.target].update(clocks)
                writer_block.setdefault(assignment.target, block)
            for read_name in block_read_identifiers(block):
                readers[read_name].update(clocks)
                reader_block.setdefault(read_name, block)
        for signal, write_clocks in writers.items():
            read_clocks = readers.get(signal, set())
            crossing = read_clocks - write_clocks
            if not crossing or is_sync_name(signal) or is_reset_name(signal):
                continue
            block = reader_block.get(signal) or writer_block[signal]
            if _has_two_stage_sync_capture(block, signal):
                continue
            width = signal_width(symbols.get(signal)) or 1
            severity = "high" if width > 1 else "medium"
            diagnostics.append(
                _block_diag(
                    block,
                    module,
                    rule="RISK_CDC_UNSYNC_SIGNAL",
                    severity=severity,
                    category="cdc_timing",
                    message_zh=f"信号 `{signal}` 可能从 {sorted(write_clocks)} 跨到 {sorted(crossing)}，未看到明显同步器命名。",
                    suggestion_zh="跨时钟域单 bit 信号建议使用两级同步器，多 bit 数据建议使用握手、异步 FIFO 或明确 CDC 约束。",
                    confidence="medium",
                    evidence={"signal": signal, "source_clocks": sorted(write_clocks), "destination_clocks": sorted(crossing), "signal_width": width},
                )
            )
    return diagnostics


def _rule_multicycle_without_constraint(features: RiskFeatures) -> list[RiskDiagnostic]:
    if features.sdc.file and features.sdc.has_multicycle:
        return []
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        values = token_values(module.body_tokens)
        ids = token_identifiers(module.body_tokens)
        if not any("multi" in name.lower() or "slow" in name.lower() for name in ids):
            continue
        if not any(value in {">=", "==", "<=", "case"} for value in values):
            continue
        diagnostics.append(
            RiskDiagnostic.make(
                rule="RISK_MULTICYCLE_WITHOUT_CONSTRAINT",
                severity="low",
                category="constraint_timing",
                file=module.span.file,
                line=module.span.line,
                column=module.span.column,
                module=module.name,
                message_zh="RTL 命名/结构暗示多周期行为，但 SDC 中未看到 set_multicycle_path。",
                suggestion_zh="若该路径确实跨多个周期，请补充并验证 multicycle 约束；若只是普通逻辑，可忽略该低置信提示。",
                confidence="low",
                evidence={"sdc_file": features.sdc.file, "has_multicycle_constraint": features.sdc.has_multicycle},
            )
        )
    return diagnostics


def _rule_io_constraint_missing(features: RiskFeatures) -> list[RiskDiagnostic]:
    top = features.top_module
    if not top or not features.sdc.file:
        return []
    diagnostics: list[RiskDiagnostic] = []
    for name, signal in top.ports.items():
        if is_clock_name(name) or is_reset_name(name):
            continue
        if signal.direction == "input" and name not in features.sdc.input_delay_ports:
            diagnostics.append(
                RiskDiagnostic.make(
                    rule="RISK_IO_CONSTRAINT_MISSING",
                    severity="medium",
                    category="constraint_timing",
                    file=signal.span.file,
                    line=signal.span.line,
                    column=signal.span.column,
                    module=top.name,
                    message_zh=f"顶层输入端口 `{name}` 在 SDC 中未看到 set_input_delay。",
                    suggestion_zh="请按板级/上游时钟关系补充输入延迟约束，避免 I/O 路径未约束。",
                    confidence="medium",
                    evidence={"port": name, "sdc_file": features.sdc.file},
                )
            )
        elif signal.direction == "output" and name not in features.sdc.output_delay_ports:
            diagnostics.append(
                RiskDiagnostic.make(
                    rule="RISK_IO_CONSTRAINT_MISSING",
                    severity="medium",
                    category="constraint_timing",
                    file=signal.span.file,
                    line=signal.span.line,
                    column=signal.span.column,
                    module=top.name,
                    message_zh=f"顶层输出端口 `{name}` 在 SDC 中未看到 set_output_delay。",
                    suggestion_zh="请按下游采样关系补充输出延迟约束，避免 I/O 路径未约束。",
                    confidence="medium",
                    evidence={"port": name, "sdc_file": features.sdc.file},
                )
            )
    return diagnostics


def _rule_memory_or_dsp_chain_no_pipeline(features: RiskFeatures) -> list[RiskDiagnostic]:
    diagnostics: list[RiskDiagnostic] = []
    for module in features.design.modules:
        for block in module.always_blocks:
            values = token_values(block.body_tokens)
            ids = token_identifiers(block.body_tokens)
            has_mem_or_dsp_name = any(part in name.lower() for name in ids for part in ("mem", "ram", "dsp", "prod", "mul"))
            heavy_ops = sum(1 for value in values if value in {"*", "+", "-", "[", "]", "?", "case"})
            if not has_mem_or_dsp_name or heavy_ops < 7:
                continue
            diagnostics.append(
                _block_diag(
                    block,
                    module,
                    rule="RISK_MEMORY_OR_DSP_CHAIN_NO_PIPELINE",
                    severity="medium",
                    category="timing_setup",
                    message_zh="内存/DSP 风格数据后接较重组合逻辑，可能缺少输出寄存器或流水。",
                    suggestion_zh="检查 RAM/DSP 输出寄存器和后级流水，避免宏单元输出直接进入长组合链。",
                    confidence="low",
                    evidence={"heavy_operator_count": heavy_ops},
                )
            )
    return diagnostics


def _block_diag(
    block: AlwaysBlock,
    module: Module,
    *,
    rule: str,
    severity: str,
    category: str,
    message_zh: str,
    suggestion_zh: str,
    confidence: str,
    evidence: dict[str, object],
) -> RiskDiagnostic:
    return RiskDiagnostic.make(
        rule=rule,
        severity=severity,
        category=category,
        file=block.span.file,
        line=block.span.line,
        column=block.span.column,
        module=module.name,
        message_zh=message_zh,
        suggestion_zh=suggestion_zh,
        confidence=confidence,
        evidence=evidence,
    )


def _assignment_diag(
    assignment: Assignment,
    module: Module,
    *,
    rule: str,
    severity: str,
    category: str,
    message_zh: str,
    suggestion_zh: str,
    confidence: str,
    evidence: dict[str, object],
) -> RiskDiagnostic:
    return RiskDiagnostic.make(
        rule=rule,
        severity=severity,
        category=category,
        file=assignment.span.file,
        line=assignment.span.line,
        column=assignment.span.column,
        module=module.name,
        message_zh=message_zh,
        suggestion_zh=suggestion_zh,
        confidence=confidence,
        evidence=evidence,
    )


def _dedupe(diagnostics: list[RiskDiagnostic]) -> list[RiskDiagnostic]:
    result: list[RiskDiagnostic] = []
    seen: set[tuple[str, str, int, str]] = set()
    for item in diagnostics:
        key = (item.rule, item.file, item.line, item.message_zh)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _conditional_targets_without_default(block: AlwaysBlock) -> set[str]:
    control_tokens = [token for token in block.body_tokens if token.value in {"if", "case", "casez", "casex"}]
    if not control_tokens:
        return set()
    first_control = min(control_tokens, key=_token_position)
    default_targets = {
        assignment.target
        for assignment in block.assignments
        if _token_position(assignment.span) < _token_position(first_control)
    }
    conditional_targets = {
        assignment.target
        for assignment in block.assignments
        if _token_position(assignment.span) >= _token_position(first_control)
    }
    return conditional_targets - default_targets


def _token_position(token) -> tuple[int, int]:
    return int(token.line or 1), int(token.column or 1)


def _max_identifier_width(tokens, symbols) -> int:
    widths = [signal_width(symbols.get(name)) or 1 for name in token_identifiers(tokens) if name in symbols]
    return max(widths, default=1)


def _memory_declarations(module: Module) -> list[dict[str, object]]:
    """从声明 token 中抽取 ``reg [W:0] mem [D:0]`` 常见形态。"""
    tokens = module.body_tokens
    result: list[dict[str, object]] = []
    for index, token in enumerate(tokens):
        if token.kind != "identifier":
            continue
        name = token.value
        if name not in module.declarations or index + 1 >= len(tokens) or tokens[index + 1].value != "[":
            continue
        statement_start = index - 1
        while statement_start >= 0 and tokens[statement_start].value != ";":
            statement_start -= 1
        declaration_prefix = {item.value for item in tokens[statement_start + 1 : index]}
        if not declaration_prefix.intersection({"reg", "logic", "wire"}) or "assign" in declaration_prefix:
            continue
        unpacked, close_index = _balanced_group_from_tokens(tokens, index + 1, "[", "]")
        if close_index is None:
            continue
        tail_index = close_index + 1
        if tail_index >= len(tokens) or tokens[tail_index].value not in {";", ","}:
            continue
        range_text = "[" + " ".join(token.value for token in unpacked) + "]"
        result.append(
            {
                "memory": name,
                "name": name,
                "data_width": signal_width(module.declarations.get(name)),
                "unpacked_range": range_text,
                "declaration_file": token.file,
                "declaration_line": token.line,
            }
        )
    unique: dict[str, dict[str, object]] = {}
    for item in result:
        unique[str(item["name"])] = item
    return list(unique.values())


def _indexed_identifier_count(tokens, name: str) -> int:
    return sum(
        1
        for index, token in enumerate(tokens[:-1])
        if token.kind == "identifier" and token.value == name and tokens[index + 1].value == "["
    )


def _combinational_dependency_graph(module: Module) -> tuple[dict[str, set[str]], dict[tuple[str, str], list[dict[str, object]]]]:
    symbols = module_symbols(module)
    signal_names = (set(module.ports) | set(module.declarations)) - set(module.parameters)
    graph: dict[str, set[str]] = defaultdict(set)
    edge_records: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)

    def add_edge(target: str, source: str, assignment: Assignment, kind: str) -> None:
        if target not in signal_names or source not in signal_names:
            return
        if target not in symbols or source not in symbols:
            return
        graph[target].add(source)
        edge_records[(target, source)].append(
            {
                "target": target,
                "source": source,
                "kind": kind,
                "context": assignment.context,
                "file": assignment.span.file,
                "line": assignment.span.line,
                "column": assignment.span.column,
                "expr_identifiers": sorted(assignment_expr_identifiers(assignment)),
            }
        )

    for assignment in module.continuous_assigns:
        for source in assignment_expr_identifiers(assignment):
            add_edge(assignment.target, source, assignment, "continuous_assign")

    for block in module.always_blocks:
        if not block.is_combinational():
            continue
        control_ids = _control_condition_identifiers(block.body_tokens)
        for assignment in block.assignments:
            sources = assignment_expr_identifiers(assignment) | control_ids
            for source in sources:
                add_edge(assignment.target, source, assignment, block.kind)

    return graph, edge_records


def _control_condition_identifiers(tokens) -> set[str]:
    result: set[str] = set()
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.value not in {"if", "case", "casez", "casex"}:
            index += 1
            continue
        open_index = index + 1
        if open_index < len(tokens) and tokens[open_index].value == "(":
            group, close_index = _balanced_group_from_tokens(tokens, open_index, "(", ")")
            result.update(token_identifiers(group))
            index = close_index + 1 if close_index is not None else open_index + 1
            continue
        index += 1
    return result


def _tarjan_scc(graph: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    result: list[list[str]] = []
    nodes = set(graph)
    for edges in graph.values():
        nodes.update(edges)

    def strongconnect(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for neighbor in graph.get(node, set()):
            if neighbor not in indices:
                strongconnect(neighbor)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
            elif neighbor in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[neighbor])
        if lowlinks[node] != indices[node]:
            return
        component: list[str] = []
        while stack:
            item = stack.pop()
            on_stack.remove(item)
            component.append(item)
            if item == node:
                break
        result.append(component)

    for node in sorted(nodes):
        if node not in indices:
            strongconnect(node)
    return result


def _cycle_path(members: list[str], graph: dict[str, set[str]]) -> list[str]:
    if len(members) == 1:
        return [members[0], members[0]]
    member_set = set(members)
    start = members[0]
    path = [start]
    current = start
    visited = {start}
    while True:
        next_nodes = sorted(node for node in graph.get(current, set()) if node in member_set)
        if not next_nodes:
            break
        next_node = next_nodes[0]
        path.append(next_node)
        if next_node == start:
            return path
        if next_node in visited:
            path.append(next_node)
            return path
        visited.add(next_node)
        current = next_node
    return members + [members[0]]


STATE_NAME_RE = re.compile(r"(?:^|_)(state|fsm)(?:_|$)|current_state|curr_state|next_state", re.IGNORECASE)


def _state_register_candidates(module: Module) -> list[tuple[AlwaysBlock, str]]:
    candidates: list[tuple[AlwaysBlock, str]] = []
    seen: set[tuple[int, str]] = set()
    for block in module.always_blocks:
        if not block.is_sequential():
            continue
        for assignment in block.assignments:
            if not STATE_NAME_RE.search(assignment.target):
                continue
            key = (id(block), assignment.target)
            if key in seen:
                continue
            seen.add(key)
            candidates.append((block, assignment.target))
    return candidates


def _next_state_signal(seq_block: AlwaysBlock, state_reg: str, module: Module) -> str | None:
    symbols = module_symbols(module)
    signal_names = set(module.ports) | set(module.declarations)
    for assignment in seq_block.assignments:
        if assignment.target != state_reg:
            continue
        expr_ids = assignment_expr_identifiers(assignment)
        preferred = sorted(
            name
            for name in expr_ids
            if name in signal_names and name != state_reg and "next" in name.lower() and "state" in name.lower()
        )
        if preferred:
            return preferred[0]
        fallback = sorted(name for name in expr_ids if name in signal_names and name != state_reg and name in symbols)
        if fallback:
            return fallback[0]
    return None


def _find_transition_case(module: Module, state_reg: str, next_state: str) -> tuple[AlwaysBlock, dict[str, object]] | None:
    for block in module.always_blocks:
        if not block.is_combinational():
            continue
        if not any(assignment.target == next_state for assignment in block.assignments):
            continue
        case_info = _case_info_for_state(block, state_reg)
        if case_info:
            return block, case_info
    return None


def _case_info_for_state(block: AlwaysBlock, state_reg: str) -> dict[str, object] | None:
    tokens = block.body_tokens
    for index, token in enumerate(tokens):
        if token.value not in {"case", "casez", "casex"}:
            continue
        open_index = index + 1
        if open_index >= len(tokens) or tokens[open_index].value != "(":
            continue
        selector_tokens, close_index = _balanced_group_from_tokens(tokens, open_index, "(", ")")
        if close_index is None or state_reg not in token_identifiers(selector_tokens):
            continue
        end_index = _matching_endcase(tokens, close_index + 1)
        if end_index is None:
            continue
        branches = _parse_simple_case_branches(tokens[close_index + 1 : end_index])
        handled = sorted(label for label in branches if label != "default")
        return {
            "case_kind": token.value,
            "case_line": token.line,
            "selector": " ".join(token_values(selector_tokens)),
            "handled_labels": handled,
            "has_default": "default" in branches,
            "default_tokens": branches.get("default", []),
            "branches": branches,
        }
    return None


def _matching_endcase(tokens, start_index: int) -> int | None:
    depth = 0
    for index in range(start_index, len(tokens)):
        value = tokens[index].value
        if value in {"case", "casez", "casex"}:
            depth += 1
        elif value == "endcase":
            if depth == 0:
                return index
            depth -= 1
    return None


def _parse_simple_case_branches(tokens) -> dict[str, list[object]]:
    colon_positions: list[int] = []
    depth = 0
    for index, token in enumerate(tokens):
        if token.value in {"(", "[", "{"}:
            depth += 1
        elif token.value in {")", "]", "}"}:
            depth = max(0, depth - 1)
        elif token.value == ":" and depth == 0:
            colon_positions.append(index)
    branches: dict[str, list[object]] = {}
    for offset, colon in enumerate(colon_positions):
        label_token = tokens[colon - 1] if colon > 0 else tokens[colon]
        label = label_token.value
        next_colon = colon_positions[offset + 1] if offset + 1 < len(colon_positions) else len(tokens)
        next_label_start = max(colon + 1, next_colon - 1) if next_colon < len(tokens) else len(tokens)
        branch_tokens = list(tokens[colon + 1 : next_label_start])
        branches[label] = branch_tokens
    return branches


def _parameter_value_map(module: Module) -> dict[str, str]:
    result: dict[str, str] = {}
    tokens = module.body_tokens
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.value not in {"parameter", "localparam"}:
            index += 1
            continue
        statement: list[object] = []
        index += 1
        while index < len(tokens) and tokens[index].value != ";":
            statement.append(tokens[index])
            index += 1
        for segment in _split_top_level(statement, ","):
            op_index = _first_assignment_operator(segment)
            if op_index is None:
                continue
            name = _last_identifier_value(segment[:op_index])
            if not name:
                continue
            expr = " ".join(token_values(segment[op_index + 1 :])).strip()
            if expr:
                result[name] = expr
        index += 1
    return result


def _reset_state_from_block(seq_block: AlwaysBlock, state_reg: str, next_state: str) -> str | None:
    values = token_values(seq_block.body_tokens)
    has_reset_context = bool(event_reset_names(seq_block)) or any(is_reset_name(value) for value in values)
    if not has_reset_context:
        return None
    for assignment in seq_block.assignments:
        if assignment.target != state_reg:
            continue
        expr_ids = assignment_expr_identifiers(assignment)
        if next_state in expr_ids:
            continue
        expr = _expr_state_key(assignment.expr_tokens)
        if expr:
            return expr
    return None


def _declared_fsm_states(
    module: Module,
    state_reg: str,
    next_state: str,
    case_info: dict[str, object],
    parameter_values: dict[str, str],
) -> list[str]:
    referenced: set[str] = set(case_info.get("handled_labels", []))
    for block in module.always_blocks:
        for assignment in block.assignments:
            if assignment.target in {state_reg, next_state}:
                referenced.update(assignment_expr_identifiers(assignment))
    for assignment in module.continuous_assigns:
        if assignment.target in {state_reg, next_state}:
            referenced.update(assignment_expr_identifiers(assignment))
    declared = [name for name in module.parameters if name in referenced or _looks_like_state_literal(name)]
    return sorted(dict.fromkeys(declared))


def _looks_like_state_literal(name: str) -> bool:
    return name.isupper() or name.startswith(("S_", "ST_")) or name.lower() in {"idle", "run", "done", "error", "wait"}


def _default_recovery_status(default_tokens, state_reg: str, next_state: str, reset_state: str | None, parameter_values: dict[str, str]) -> dict[str, object]:
    assignments = _assignments_in_tokens(default_tokens)
    state_assignments = [item for item in assignments if item["target"] in {state_reg, next_state}]
    if not state_assignments:
        return {"unsafe": True, "assignment": None, "reason_zh": "default 分支没有对状态或 next-state 赋值。"}
    assignment = state_assignments[0]
    expr_tokens = assignment["expr_tokens"]
    expr_key = _expr_state_key(expr_tokens)
    expr_ids = set(token_identifiers(expr_tokens))
    if state_reg in expr_ids:
        return {"unsafe": True, "assignment": assignment["text"], "reason_zh": "default 分支保持当前 state，不能作为非法状态恢复。"}
    if reset_state and _expr_matches_state(expr_key, reset_state, parameter_values):
        return {"unsafe": False, "assignment": assignment["text"], "reason_zh": "default 分支恢复到 reset 状态。"}
    return {"unsafe": True, "assignment": assignment["text"], "reason_zh": "default 分支目标与已知 reset 状态不一致。"}


def _fsm_case_evidence(
    state_reg: str,
    next_state: str,
    reset_state: str | None,
    declared_states: list[str],
    handled_states: set[str],
    case_info: dict[str, object],
) -> dict[str, object]:
    return {
        "state_register": state_reg,
        "next_state_signal": next_state,
        "reset_state": reset_state,
        "case_selector": case_info.get("selector"),
        "case_line": case_info.get("case_line"),
        "has_default": case_info.get("has_default"),
        "declared_states": declared_states,
        "handled_states": sorted(handled_states),
    }


def _missing_declared_states(declared_states: list[str], handled_states: set[str], parameter_values: dict[str, str]) -> list[str]:
    missing: list[str] = []
    for state in declared_states:
        if state in handled_states:
            continue
        value = parameter_values.get(state)
        if value and value in handled_states:
            continue
        missing.append(state)
    return missing


def _obvious_terminal_states(case_info: dict[str, object], next_state: str, parameter_values: dict[str, str]) -> list[str]:
    branches = case_info.get("branches")
    if not isinstance(branches, dict):
        return []
    result: list[str] = []
    for label, branch_tokens in branches.items():
        if label == "default":
            continue
        if not isinstance(branch_tokens, list):
            continue
        values = token_values(branch_tokens)
        if any(value in {"if", "case", "casez", "casex", "?"} for value in values):
            continue
        assignments = [item for item in _assignments_in_tokens(branch_tokens) if item["target"] == next_state]
        if not assignments:
            continue
        expr_keys = [_expr_state_key(item["expr_tokens"]) for item in assignments]
        if expr_keys and all(_expr_matches_state(expr, label, parameter_values) for expr in expr_keys):
            result.append(label)
    return result


def _fsm_diag(
    block: AlwaysBlock,
    module: Module,
    *,
    state_reg: str,
    next_state: str,
    issue: str,
    severity: str,
    confidence: str,
    message_zh: str,
    suggestion_zh: str,
    evidence: dict[str, object],
) -> RiskDiagnostic:
    evidence = dict(evidence)
    evidence.update(
        {
            "issue": issue,
            "state_register": state_reg,
            "next_state_signal": next_state,
            "scope_note_zh": "当前为 STA-lite RTL-only 启发式 FSM 鲁棒性检查，不做 formal reachability 证明。",
        }
    )
    return _block_diag(
        block,
        module,
        rule="RISK_FSM_ROBUSTNESS",
        severity=severity,
        category="fsm_robustness",
        message_zh=message_zh,
        suggestion_zh=suggestion_zh,
        confidence=confidence,
        evidence=evidence,
    )


def _assignments_in_tokens(tokens) -> list[dict[str, object]]:
    assignments: list[dict[str, object]] = []
    for index, token in enumerate(tokens):
        if token.value not in {"=", "<="}:
            continue
        if token.value == "=" and index > 0 and tokens[index - 1].value in {"<", ">", "!", "="}:
            continue
        target = _last_identifier_value(tokens[:index])
        if not target:
            continue
        expr_tokens = _tokens_until_semicolon(tokens[index + 1 :])
        assignments.append(
            {
                "target": target,
                "expr_tokens": expr_tokens,
                "text": f"{target} {token.value} {' '.join(token_values(expr_tokens)).strip()}",
            }
        )
    return assignments


def _tokens_until_semicolon(tokens) -> list[object]:
    result: list[object] = []
    depth = 0
    for token in tokens:
        if token.value in {"(", "[", "{"}:
            depth += 1
        elif token.value in {")", "]", "}"}:
            depth = max(0, depth - 1)
        if token.value == ";" and depth == 0:
            break
        result.append(token)
    return result


def _expr_state_key(tokens) -> str | None:
    identifiers = token_identifiers(tokens)
    if identifiers:
        return identifiers[0]
    values = [value for value in token_values(tokens) if value not in {"(", ")"}]
    return values[0] if values else None


def _normalize_state_expr(expr: str | None, parameter_values: dict[str, str]) -> str | None:
    if expr is None:
        return None
    return parameter_values.get(expr, expr)


def _expr_matches_state(expr: str | None, state: str, parameter_values: dict[str, str]) -> bool:
    if expr is None:
        return False
    return expr == state or parameter_values.get(expr) == state or parameter_values.get(state) == expr or parameter_values.get(expr) == parameter_values.get(state)


def _same_state_value(left: str, right: str, parameter_values: dict[str, str]) -> bool:
    return _expr_matches_state(left, right, parameter_values)


def _split_top_level(tokens, separator: str) -> list[list[object]]:
    segments: list[list[object]] = []
    current: list[object] = []
    depth = 0
    for token in tokens:
        if token.value in {"(", "[", "{"}:
            depth += 1
        elif token.value in {")", "]", "}"}:
            depth = max(0, depth - 1)
        if token.value == separator and depth == 0:
            segments.append(current)
            current = []
            continue
        current.append(token)
    segments.append(current)
    return segments


def _first_assignment_operator(tokens) -> int | None:
    for index, token in enumerate(tokens):
        if token.value in {"=", "<="}:
            return index
    return None


def _last_identifier_value(tokens) -> str | None:
    for token in reversed(tokens):
        if token.kind == "identifier":
            return token.value
    return None


def _balanced_group_from_tokens(tokens, open_index: int, open_value: str, close_value: str) -> tuple[list[object], int | None]:
    if open_index >= len(tokens) or tokens[open_index].value != open_value:
        return [], None
    depth = 0
    result: list[object] = []
    for index in range(open_index, len(tokens)):
        token = tokens[index]
        if token.value == open_value:
            depth += 1
            if depth == 1:
                continue
        elif token.value == close_value:
            depth -= 1
            if depth == 0:
                return result, index
        result.append(token)
    return result, None


def _has_two_stage_sync_capture(block: AlwaysBlock, source_signal: str) -> bool:
    first_stage_targets = [
        assignment.target
        for assignment in block.assignments
        if source_signal in assignment_expr_identifiers(assignment)
    ]
    for first_stage in first_stage_targets:
        if not (is_sync_name(first_stage) or "meta" in first_stage.lower() or "stage" in first_stage.lower()):
            continue
        for assignment in block.assignments:
            if assignment.target == first_stage:
                continue
            if first_stage in assignment_expr_identifiers(assignment) and (
                is_sync_name(assignment.target) or "stage" in assignment.target.lower()
            ):
                return True
    return False


def _reset_branch_info(block: AlwaysBlock) -> tuple[str, str, str, list[object]] | None:
    """Return the first reset branch for a conventional clocked process."""
    tokens = block.body_tokens
    try:
        if_index = next(index for index, token in enumerate(tokens) if token.value == "if")
    except StopIteration:
        return None
    if if_index + 1 >= len(tokens) or tokens[if_index + 1].value != "(":
        return None
    condition, close_index = _balanced_group_from_tokens(tokens, if_index + 1, "(", ")")
    if close_index is None:
        return None
    condition_names = [token.value for token in condition if token.kind == "identifier" and is_reset_name(token.value)]
    if not condition_names:
        return None
    reset_name = condition_names[0]
    event_map = {signal: edge for edge, signal in event_pairs(block)}
    reset_kind = "asynchronous" if reset_name in event_map else "synchronous"
    polarity = "active_low" if _condition_is_active_low(condition, reset_name) else "active_high"
    branch_tokens = _first_statement_tokens(tokens, close_index + 1)
    if not branch_tokens:
        return None
    return reset_name, reset_kind, polarity, branch_tokens


def _first_control_branch_info(block: AlwaysBlock) -> tuple[str, list[object]] | None:
    tokens = block.body_tokens
    try:
        if_index = next(index for index, token in enumerate(tokens) if token.value == "if")
    except StopIteration:
        return None
    if if_index + 1 >= len(tokens) or tokens[if_index + 1].value != "(":
        return None
    condition, close_index = _balanced_group_from_tokens(tokens, if_index + 1, "(", ")")
    if close_index is None:
        return None
    names = [token.value for token in condition if token.kind == "identifier"]
    if len(set(names)) != 1:
        return None
    branch_tokens = _first_statement_tokens(tokens, close_index + 1)
    return (names[0], branch_tokens) if branch_tokens else None


def _condition_is_active_low(tokens, signal: str) -> bool:
    for index, token in enumerate(tokens):
        if token.kind == "identifier" and token.value == signal:
            return index > 0 and tokens[index - 1].value in {"!", "~"}
    return signal.lower().endswith(("_n", "_b"))


def _first_statement_tokens(tokens, start: int) -> list[object]:
    if start >= len(tokens):
        return []
    if tokens[start].value != "begin":
        return _tokens_until_semicolon(tokens[start:])
    depth = 0
    result: list[object] = []
    for token in tokens[start + 1 :]:
        if token.value == "begin":
            depth += 1
        elif token.value == "end":
            if depth == 0:
                return result
            depth -= 1
        result.append(token)
    return result


def _branch_assignment_targets(tokens) -> set[str]:
    return {str(item["target"]) for item in _assignments_in_tokens(tokens) if item.get("target")}
