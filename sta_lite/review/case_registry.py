from __future__ import annotations

from pathlib import Path
from typing import Any

from sta_lite.resources import resource_root


VALID_PRIORITIES = {"P0", "P1"}
VALID_OWNERS = {"lint", "profiling", "both"}
VALID_SUPPORT_STATUSES = {"supported", "partially_supported", "unsupported_diagnostic", "unsupported_by_design", "not_covered"}
PROJECT_ROOT = resource_root()


def _case(
    case_id: str,
    priority: str,
    name_zh: str,
    category: str,
    owner: str,
    support_status: str,
    rule_ids: list[str],
    test_paths: list[str],
    next_improvement_zh: str,
    *,
    support_note_zh: str = "",
    unsupported_reason_zh: str = "",
    golden_reference: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "priority": priority,
        "name_zh": name_zh,
        "category": category,
        "owner": owner,
        "support_status": support_status,
        "rule_ids": rule_ids,
        "test_paths": test_paths,
        "next_improvement_zh": next_improvement_zh,
        "support_note_zh": support_note_zh,
        "unsupported_reason_zh": unsupported_reason_zh,
        "golden_reference": golden_reference or {"status": "not_configured", "tool": None, "note_zh": "该 Case 暂未配置独立 golden/reference。"},
    }


LINT_MATRIX = "reports/lint_diff/coverage_matrix.json"
RISK_CASE = "risk_profile/cases"


CASE_REGISTRY: list[dict[str, Any]] = [
    _case("P0_SYNTAX_GRAMMAR", "P0", "语法 lint 和基础语法错误", "syntax", "lint", "supported",
          ["LEX*", "PARSE*", "PP*", "SYN*", "SEM001_TOP_NOT_FOUND", "SEM002_PORT_NOT_DECLARED", "SEM003_UNDECLARED_IDENTIFIER"],
          [LINT_MATRIX, "tests/test_lint_engine.py"], "继续扩展 IEEE 1364 边界语法和常见 SystemVerilog RTL 前端语法。"),
    _case("P0_SYNTHESIZABILITY", "P0", "延时、仿真任务和不可综合构造", "synthesizability", "lint", "supported",
          ["RTL025_SYNTHESIZABILITY_RISK", "UNSUPPORTED_VERILOG", "UNSUPPORTED_SYSTEMVERILOG"],
          ["lint/verilog_warning_example/synthesizability", "tests/test_long_task_coverage.py", "tests/test_long_task_golden_reference.py"],
          "继续覆盖 force/release、事件触发、DPI/Pli 和更细粒度的工具特定综合边界。",
          support_note_zh="已独立诊断 initial、常量延时控制及常见仿真系统任务；普通边沿寄存器负例不报告。该支持范围是构造筛查，不等价于目标综合器完整可综合性判定。",
          golden_reference={
              "status": "metadata_reference",
              "tool": "Yosys / Verilator（可选开发期参考）+ case.json metadata",
              "source_url": "https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/read_verilog.html",
              "command_zh": "yosys -p \"read_verilog <case>.v; hierarchy -top top; proc; check\"；verilator --lint-only --Wall <case>.v；无工具时运行 python3 tests/test_long_task_golden_reference.py。",
              "note_zh": "外部工具只作为测试/开发期参考，生产 lint 不调用它们。",
          }),
    _case("P0_WIDTH_MISMATCH", "P0", "位宽不匹配、截断和隐式扩展", "width", "lint", "supported",
          ["RTL013_PORT_WIDTH_MISMATCH", "RTL014_SELECT_RANGE", "RTL020_ASSIGN_WIDTH_MISMATCH"],
          ["lint/verilog_warning_example/width_range", LINT_MATRIX, "tests/test_p0_case_upgrades.py", "tests/test_p0_golden_reference.py"],
          "继续扩展 signed/unsigned 表达式推导和参数化位宽求值。",
          support_note_zh="已覆盖端口连接宽度、常量位选择越界、赋值截断和多比特隐式扩展；常见显式拼接扩展不误报。",
          golden_reference={
              "status": "passed",
              "tool": "Verilator / Icarus Verilog",
              "source_url": "https://verilator.org/guide/latest/warnings.html",
              "command_zh": "tools/verilator/usr/bin/verilator --lint-only --language 1364-2005 <case>.v；tools/bin/iverilog -g2005 -Wall -tnull -s top <case>.v",
              "note_zh": "Verilator 用于宽度 lint 参考；Icarus 用于语法/编译期 sanity，不作为生产 lint 引擎。",
          }),
    _case("P0_LATCH_INFERENCE", "P0", "组合逻辑 latch 推断", "latch", "both", "supported",
          ["RTL003_LATCH_RISK", "RTL021_INCOMPLETE_CASE_DEFAULT", "RISK_LATCH_TIMING"],
          ["examples/lint/latch_risk", f"{RISK_CASE}/latch_inference_timing/case.json"],
          "增加复杂嵌套分支和函数内赋值覆盖分析。"),
    _case("P0_COMBINATIONAL_LOOP", "P0", "组合环路风险", "combinational_loop", "profiling", "supported",
          ["RISK_COMBINATIONAL_LOOP"],
          [
              f"{RISK_CASE}/comb_loop_two_signal/case.json",
              f"{RISK_CASE}/comb_loop_self/case.json",
              f"{RISK_CASE}/comb_loop_always/case.json",
              f"{RISK_CASE}/comb_loop_ternary/case.json",
              f"{RISK_CASE}/comb_loop_always_comb_sv/case.json",
              f"{RISK_CASE}/comb_loop_seq_feedback_safe/case.json",
              f"{RISK_CASE}/comb_chain_safe/case.json",
              "tests/test_p0_remaining_cases.py",
              "tests/test_p0_yosys_reference.py",
          ],
          "后续可加入实例层次、函数调用和参数 elaboration 后的更精确信号依赖。",
          support_note_zh="已基于连续赋值和组合 always/always_comb 构建 RTL 依赖图，并用 Tarjan SCC 检测自环与多信号环；时序 always 边界会切断依赖。",
          golden_reference={
              "status": "passed",
              "tool": "Yosys scc/check",
              "source_url": "https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/scc.html",
              "command_zh": "yosys -p \"read_verilog -sv <files>; hierarchy -top <top>; proc; opt; check; scc\"",
              "note_zh": "Yosys scc 用作开发期组合环路 reference；STA-lite 正常运行不调用 Yosys。",
          }),
    _case("P0_MULTI_DRIVER", "P0", "多驱动风险", "driver", "lint", "supported",
          ["RTL008_MULTI_DRIVER_RISK"], ["examples/lint/multi_driver", "lint/verilog_warning_example", LINT_MATRIX],
          "增加跨 generate、实例输出和连续/过程混合驱动分析。"),
    _case("P0_UNDRIVEN_UNUSED", "P0", "未驱动、未使用和未连接信号", "connectivity", "lint", "supported",
          ["RTL015_UNUSED_SIGNAL", "RTL016_ASSIGNED_NOT_READ", "RTL017_UNUSED_INPUT", "RTL018_UNDRIVEN_OUTPUT", "RTL019_INSTANCE_OUTPUT_UNCONNECTED"],
          ["lint/verilog_warning_example", LINT_MATRIX], "增加层次化连接和参数化实例下的可达性分析。"),
    _case("P0_LONG_COMBINATIONAL_PATH", "P0", "长组合逻辑链", "timing_setup", "both", "supported",
          ["RTL005_LONG_COMB_HEURISTIC", "RISK_LONG_COMB_PATH"],
          ["examples/lint/long_comb", f"{RISK_CASE}/long_comb_path/case.json"],
          "基于表达式 DAG 改进逻辑深度估计并识别寄存器边界。"),
    _case("P0_HIGH_FANOUT_CONTROL", "P0", "高扇出控制、复位或使能信号", "fanout", "profiling", "supported",
          ["RISK_HIGH_FANOUT_CONTROL"], [f"{RISK_CASE}/high_fanout_control/case.json"],
          "结合实例端口和层次结构估算更接近综合后的逻辑扇出。"),
    _case("P0_ASYNC_RESET_RELEASE", "P0", "异步复位释放同步风险", "reset", "both", "supported",
          ["RTL009_ASYNC_RESET_RELEASE_RISK", "RISK_ASYNC_RESET_RELEASE_UNSYNC"],
          ["examples/lint/async_reset", f"{RISK_CASE}/async_reset_release_unsync/case.json"],
          "识别标准两级 reset synchronizer 和 reset-domain crossing 结构。"),
    _case("P0_SIMPLE_CDC", "P0", "简单跨时钟域信号传递", "cdc", "profiling", "supported",
          ["RISK_CDC_UNSYNC_SIGNAL"],
          [f"{RISK_CASE}/cdc_unsync_signal/case.json", f"{RISK_CASE}/cdc_multibit_unsync_signal/case.json", f"{RISK_CASE}/cdc_two_ff_sync_safe/case.json", "tests/test_p0_case_upgrades.py"],
          "后续可扩展握手、异步 FIFO、灰码计数器和 CDC waiver 识别。",
          support_note_zh="已覆盖简单单 bit/多 bit 直接跨域采样，并识别目标域两级同步器安全形态；仍不是 signoff CDC。",
          golden_reference={
              "status": "metadata_reference",
              "tool": "case.json metadata",
              "source_url": None,
              "command_zh": "python3 tests/test_p0_case_upgrades.py",
              "note_zh": "开源通用 CDC signoff golden 不适合作为本仓库轻量依赖，本 Case 使用正负例 metadata 对比。",
          }),
    _case("P0_GATED_DERIVED_CLOCK", "P0", "门控时钟和 RTL 派生时钟", "clock", "both", "supported",
          ["RTL004_GATED_CLOCK_RISK", "RISK_GATED_OR_DERIVED_CLOCK"],
          ["examples/lint/gated_clock", f"{RISK_CASE}/gated_or_derived_clock/case.json"],
          "区分安全 clock gating wrapper、generated clock 和普通逻辑门控。"),
    _case("P0_INCOMPLETE_CASE_IF", "P0", "不完整或可疑 case/if", "control_flow", "both", "supported",
          ["RTL003_LATCH_RISK", "RISK_LATCH_TIMING"],
          ["examples/lint/latch_risk", "lint/verilog_warning_example/latch_risk", f"{RISK_CASE}/latch_inference_timing/case.json", "tests/test_p0_case_upgrades.py", "tests/test_p0_golden_reference.py"],
          "后续可扩展 SystemVerilog unique/priority、枚举全覆盖和 full_case pragma 语义。",
          support_note_zh="已覆盖组合 if 缺 else、case 缺 default，并识别 if/case 前默认赋值以减少误报。",
          golden_reference={
              "status": "passed",
              "tool": "Yosys / Verilator",
              "source_url": "https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/index_passes_status.html",
              "command_zh": "yosys -q -p 'read_verilog <case>.v; proc; opt; check'；tools/verilator/usr/bin/verilator --lint-only --language 1364-2005 <case>.v",
              "note_zh": "Yosys proc/check 可作为 latch 结构参考；Verilator CASEINCOMPLETE/LATCH 类 warning 作为 lint 参考。",
          }),
    _case("P0_FSM_ROBUSTNESS", "P0", "简单 FSM 鲁棒性", "fsm", "profiling", "partially_supported",
          ["RISK_FSM_ROBUSTNESS"],
          [
              f"{RISK_CASE}/fsm_robust_safe/case.json",
              f"{RISK_CASE}/fsm_missing_reset/case.json",
              f"{RISK_CASE}/fsm_missing_case_default/case.json",
              f"{RISK_CASE}/fsm_unsafe_default/case.json",
              f"{RISK_CASE}/fsm_missing_state/case.json",
              f"{RISK_CASE}/fsm_incomplete_next_assign/case.json",
              f"{RISK_CASE}/fsm_terminal_state/case.json",
              f"{RISK_CASE}/non_fsm_safe/case.json",
              "risk_profile/FSM_ROBUSTNESS_DESIGN.md",
              "tests/test_p0_remaining_cases.py",
              "tests/test_p0_yosys_reference.py",
          ],
          "后续可支持 one-process FSM、复杂 enum/package、generate FSM 和更精确的 reachability/waiver 机制。",
          support_note_zh="已覆盖清晰两进程 FSM：clocked state register、组合 next-state、parameter/localparam 状态和 case(state) 转移；诊断缺 reset、缺 default、不安全 default、next-state 不完整、声明状态未处理和明显终止状态。",
          golden_reference={
              "status": "passed",
              "tool": "Yosys fsm_detect/fsm_extract/fsm_info + case metadata",
              "source_url": "https://yosyshq.readthedocs.io/projects/yosys/en/latest/using_yosys/synthesis/fsm.html",
              "command_zh": "yosys -p \"read_verilog -sv <files>; hierarchy -top <top>; proc; opt; fsm_detect; fsm_extract; fsm_info\"；鲁棒性 warning 使用 case.json metadata 对比",
              "note_zh": "Yosys 用于确认可抽取 FSM；缺 reset/默认恢复等鲁棒性诊断由 STA-lite metadata 正负例验证。",
          }),
    _case("P0_ASSIGNMENT_STYLE", "P0", "阻塞和非阻塞赋值误用", "assignment_style", "lint", "supported",
          ["RTL006_BLOCKING_IN_SEQUENTIAL", "RTL007_NONBLOCKING_IN_COMB"],
          ["examples/lint/blocking_seq", "examples/lint/nonblocking_comb"],
          "增加同一变量混用和跨过程赋值风格分析。"),
    _case("P0_LARGE_MUX_PRIORITY", "P0", "大 mux 或长优先级链", "mux_priority", "profiling", "supported",
          ["RISK_WIDE_MUX_PRIORITY_ENCODER"],
          [f"{RISK_CASE}/wide_mux_priority_encoder/case.json", f"{RISK_CASE}/wide_mux_case_vector/case.json", f"{RISK_CASE}/small_mux_safe/case.json", "tests/test_p0_case_upgrades.py"],
          "后续可结合参数 elaboration 和目标频率调整阈值。",
          support_note_zh="已基于分支数、同目标赋值次数和估算输出宽度识别宽 mux/优先级链，并提供小 mux 负例。",
          golden_reference={
              "status": "metadata_reference",
              "tool": "case.json metadata",
              "source_url": None,
              "command_zh": "python3 tests/test_p0_case_upgrades.py",
              "note_zh": "宽 mux 是否成为 timing 问题依赖综合和目标频率，本 RTL-only 规则用正负例 metadata 验证。",
          }),
    _case("P0_ARITHMETIC_CHAIN", "P0", "宽算术链和缺少流水", "arithmetic_pipeline", "profiling", "supported",
          ["RISK_ARITH_CHAIN_NO_PIPELINE"],
          [f"{RISK_CASE}/arithmetic_chain_no_pipeline/case.json", f"{RISK_CASE}/arithmetic_pipelined_safe/case.json", "tests/test_p0_case_upgrades.py"],
          "后续可结合目标频率、DSP 原语和多级流水结构进一步降低误报。",
          support_note_zh="已基于算术操作数、乘法数量和最大操作数宽度识别宽算术链，并提供流水负例。",
          golden_reference={
              "status": "metadata_reference",
              "tool": "case.json metadata",
              "source_url": None,
              "command_zh": "python3 tests/test_p0_case_upgrades.py",
              "note_zh": "是否缺流水是目标频率相关的早期风险，当前使用 metadata 正负例作为轻量参考。",
          }),
    _case("P1_RAM_INFERENCE", "P1", "RAM 推断风险", "memory_inference", "profiling", "supported",
          ["RISK_RAM_INFERENCE", "RISK_MEMORY_OR_DSP_CHAIN_NO_PIPELINE"],
          [f"{RISK_CASE}/ram_inference_async_read/case.json", f"{RISK_CASE}/ram_vector_safe/case.json", "tests/test_long_task_coverage.py", "tests/test_long_task_golden_reference.py"],
          "扩展多端口 RAM、byte enable、read-during-write 模式和参数化深度求值。",
          support_note_zh="已识别常见 unpacked reg/logic 数组、索引读写、同步/异步读写上下文；普通 packed 向量负例不报告。规则提示推断候选，不承诺目标器件宏映射。",
          golden_reference={"status": "metadata_reference", "tool": "Yosys memory_dff/memory_collect（可选）+ case.json metadata", "source_url": "https://yosyshq.readthedocs.io/projects/yosys/en/v0.56/using_yosys/synthesis/memory.html", "command_zh": "yosys -p \"read_verilog <case>.v; hierarchy -top top; proc; memory_dff; memory_collect; stat\"", "note_zh": "Yosys 仅用于开发期确认 memory lowering；生产 profiling 无外部工具依赖。"}),
    _case("P1_DSP_INFERENCE", "P1", "DSP 推断风险", "dsp_inference", "profiling", "supported",
          ["RISK_DSP_INFERENCE", "RISK_ARITH_CHAIN_NO_PIPELINE"],
          [f"{RISK_CASE}/dsp_inference_mac/case.json", f"{RISK_CASE}/dsp_no_multiply_safe/case.json", "tests/test_long_task_coverage.py", "tests/test_long_task_golden_reference.py"],
          "增加目标器件 DSP 模板、pre-adder、级联和更精确的寄存器级识别。",
          support_note_zh="已识别 8 bit 及以上乘法/乘加的 DSP 候选形态，并记录操作数宽度、乘法数及是否处于时序过程；无乘法负例不报告。最终映射仍以综合报告为准。",
          golden_reference={"status": "metadata_reference", "tool": "Yosys alumacc/stat（可选）+ case.json metadata", "source_url": "https://yosyshq.readthedocs.io/projects/yosys/en/v0.51/cmd/xilinx_dsp.html", "command_zh": "yosys -p \"read_verilog <case>.v; hierarchy -top top; proc; alumacc; stat\"", "note_zh": "通用算术 lowering 用作开发期参考；不把器件专用 DSP 映射结论冒充为 RTL 事实。"}),
    _case("P1_MISSING_PIPELINE", "P1", "宽算术、比较树或 mux 树缺少流水", "pipeline", "profiling", "supported",
          ["RISK_MISSING_PIPELINE", "RISK_ARITH_CHAIN_NO_PIPELINE", "RISK_MEMORY_OR_DSP_CHAIN_NO_PIPELINE", "RISK_WIDE_MUX_PRIORITY_ENCODER"],
          [f"{RISK_CASE}/missing_pipeline_compare_mux/case.json", f"{RISK_CASE}/pipeline_registered_safe/case.json", "tests/test_long_task_coverage.py"],
          "构建跨赋值的组合 DAG，并结合目标频率和已知单元延迟校准阈值。",
          support_note_zh="已覆盖寄存器边界之间的宽算术、比较和多级选择组合网络，记录操作数宽度与操作/分支数量；连续时序流水负例不报告。该启发式不预测真实 slack。",
          golden_reference={"status": "metadata_reference", "tool": "case.json metadata", "source_url": None, "command_zh": "python3 tests/test_long_task_coverage.py", "note_zh": "缺流水与目标频率相关，使用正负例和结构证据验证，不将任一综合器阈值作为生产依赖。"}),
    _case("P1_EXCESSIVE_RESET", "P1", "数据通路寄存器过度 reset", "reset_usage", "profiling", "supported",
          ["RISK_EXCESSIVE_RESET"],
          [f"{RISK_CASE}/excessive_reset_fanout/case.json", f"{RISK_CASE}/excessive_reset_wide_sync/case.json", f"{RISK_CASE}/excessive_reset_small_safe/case.json", f"{RISK_CASE}/excessive_reset_clock_enable_safe/case.json", "tests/test_p1_case_upgrades.py", "tests/test_p1_golden_reference.py"],
          "后续支持 generate、数组、interface 和参数化宽度的更精确 reset 位统计。",
          support_note_zh="已覆盖常见同步/异步 reset 分支，统计受影响寄存器、可解析声明宽度和估算 reset 位；clock enable 不会被当作 reset。默认阈值为 8 个寄存器或 64 个 reset 位，可由 RiskConfig.settings 调整。",
          golden_reference={
              "status": "passed",
              "tool": "Yosys proc/opt/stat + case.json metadata",
              "source_url": "https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/proc.html",
              "command_zh": "yosys -p \"read_verilog <case>.v; hierarchy -top top; proc; opt; stat\"；阈值判断使用 case.json metadata。",
              "note_zh": "Yosys 用于确认 resettable process 的结构 lowering；STA-lite 的 reset 范围阈值由内部 RTL 规则和 metadata 正负例验证。",
          }),
    _case("P1_HIGH_FANOUT_CLOCK_ENABLE", "P1", "高扇出 clock enable", "clock_enable", "profiling", "supported",
          ["RISK_HIGH_FANOUT_CLOCK_ENABLE", "RISK_HIGH_FANOUT_CONTROL"],
          [f"{RISK_CASE}/high_fanout_clock_enable/case.json", f"{RISK_CASE}/clock_enable_small_safe/case.json", "tests/test_long_task_coverage.py"],
          "扩展嵌套 enable、数组/generate 寄存器和综合后门级扇出关联。",
          support_note_zh="已从时序过程首个 enable 分支统计受控寄存器数量和估算 bit 数；默认阈值为 8 个寄存器或 64 bit，可配置。小范围 CE 和 reset 不误报。",
          golden_reference={"status": "metadata_reference", "tool": "case.json metadata", "source_url": None, "command_zh": "python3 tests/test_long_task_coverage.py", "note_zh": "RTL 负载统计不等于布局后物理扇出；正负例用于验证规则边界。"}),
    _case("P1_XPROP_CASEX_CASEZ", "P1", "X 传播和 casez/casex 风险", "x_propagation", "lint", "supported",
          ["RTL022_CASEX_CASEZ_XPROP_RISK"],
          ["lint/verilog_warning_example/x_propagation/verilog_warning_casex_casez_001/case.json", "lint/verilog_warning_example/x_propagation/verilog_warning_xprop_safe_002/case.json", "tests/test_p1_case_upgrades.py", "tests/test_p1_golden_reference.py"],
          "后续支持宏展开后的 case 形式和更完整的 SystemVerilog unique/priority case 上下文。",
          support_note_zh="已逐个报告 casex；仅在 casez 具有 ? 或 z 字面量通配证据时报告，不会把普通 case 或显式掩码比较误报为该风险。",
          golden_reference={
              "status": "passed",
              "tool": "Verilator --lint-only --Wall + case.json metadata",
              "source_url": "https://verilator.org/guide/latest/warnings.html",
              "command_zh": "tools/verilator/usr/bin/verilator --lint-only --Wall --language 1364-2005 <case>.v；casez 策略由 case.json metadata 对比。",
              "note_zh": "Verilator 的 CASEX warning 用作 casex 开发期 reference；casez 通配风险在不同版本间不稳定，使用 metadata 正负例确认。",
          }),
    _case("P1_SIGNED_UNSIGNED", "P1", "signed/unsigned 混合表达式", "signedness", "lint", "supported",
          ["RTL023_SIGNED_UNSIGNED_RISK"],
          ["lint/verilog_warning_example/signedness/verilog_warning_signed_unsigned_001/case.json", "lint/verilog_warning_example/signedness/verilog_warning_signed_safe_002/case.json", "tests/test_p1_case_upgrades.py", "tests/test_p1_golden_reference.py"],
          "后续增加 parameter 宽度求值、typedef/enum/packed struct/interface 和完整 SystemVerilog cast 类型模型。",
          support_note_zh="已覆盖具名信号的 signed/unsigned 声明、算术、比较、移位、三目与赋值转换；显式 $signed/$unsigned 转换和同 signedness 负例不报告。",
          golden_reference={
              "status": "passed",
              "tool": "Verilator --lint-only --Wall + case.json metadata",
              "source_url": "https://verilator.org/guide/latest/warnings.html",
              "command_zh": "tools/verilator/usr/bin/verilator --lint-only --Wall --language 1364-2005 <case>.v；未被版本稳定诊断的 mixed-sign 模式使用 case.json metadata。",
              "note_zh": "Verilator UNSIGNED/WIDTH 类输出用于开发期参考；STA-lite 不把 Verilator 作为运行时依赖。",
          }),
    _case("P1_COMPLEX_GENERATE", "P1", "复杂 generate 和参数 elaboration", "generate_elaboration", "lint", "supported",
          ["RTL026_COMPLEX_GENERATE_RISK", "UNSUPPORTED_VERILOG", "UNSUPPORTED_SYSTEMVERILOG"],
          ["lint/verilog_warning_example/generate_elaboration", "tests/test_long_task_coverage.py", "tests/test_long_task_golden_reference.py"],
          "实现完整参数组合 elaboration、宏展开 generate 和分支内层次连接检查。",
          support_note_zh="已识别参数相关的循环/条件组合 generate，记录分支数、嵌套深度和参数引用；简单无分支 generate 负例不报告。支持状态指风险筛查，不表示完整 elaborator。",
          golden_reference={"status": "metadata_reference", "tool": "Yosys hierarchy/proc（可选）+ case.json metadata", "source_url": "https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/hierarchy.html", "command_zh": "yosys -p \"read_verilog <case>.v; hierarchy -top top; proc; check\"", "note_zh": "可选 Yosys 用于开发期确认参数组合可 elaboration；生产 lint 不调用 Yosys。"}),
    _case("P1_PARAMETER_WIDTH", "P1", "参数派生位宽非法或可疑", "parameter_width", "lint", "supported",
          ["RTL027_PARAMETER_WIDTH_RISK", "RTL014_SELECT_RANGE"],
          ["lint/verilog_warning_example/parameter_width", "tests/test_long_task_coverage.py", "tests/test_long_task_golden_reference.py"],
          "扩展函数、宏、$clog2、条件表达式和参数覆盖后的常量求值。",
          support_note_zh="已对常见整数 parameter/localparam 和安全算术表达式做常量求值，诊断负下标及异常巨大范围；WIDTH=8 负例不报告。暂不支持 $clog2/函数等高级常量表达式。",
          golden_reference={"status": "metadata_reference", "tool": "Yosys / Verilator（可选）+ case.json metadata", "source_url": "https://verilator.org/guide/latest/warnings.html", "command_zh": "verilator --lint-only --Wall <case>.v；yosys -p \"read_verilog <case>.v; hierarchy -top top; check\"", "note_zh": "外部前端输出仅作开发期参考；内部正负例固定零宽度策略。"}),
    _case("P1_INSTANCE_PORT_CONNECTION", "P1", "模块例化和端口连接风险", "instantiation", "lint", "supported",
          ["RTL012_INSTANCE_PORT_UNCONNECTED", "RTL013_PORT_WIDTH_MISMATCH", "RTL019_INSTANCE_OUTPUT_UNCONNECTED", "SEM005_UNRESOLVED_MODULE", "SEM006_UNKNOWN_INSTANCE_PORT"],
          ["lint/verilog_warning_example", LINT_MATRIX], "增加参数覆盖、接口连接和数组端口 elaboration。"),
    _case("P1_MULTI_CLOCK_ALWAYS", "P1", "多时钟 always 块", "multi_clock", "lint", "supported",
          ["RTL024_MULTI_CLOCK_ALWAYS"],
          ["lint/verilog_warning_example/multi_clock/verilog_warning_multi_clock_001/case.json", "lint/system_verilog_warning_example/multi_clock/system_verilog_warning_multi_clock_always_ff_001/case.json", "tests/test_p1_case_upgrades.py", "tests/test_p1_golden_reference.py"],
          "后续支持宏生成 event control、复杂事件表达式和更完整的 SystemVerilog procedural 语义。",
          support_note_zh="已检测 always/always_ff 中两个及以上独立时钟边沿；只有同时出现于首个 if reset 条件且具 reset 命名证据的事件会被视为标准异步复位，不会报告单时钟加异步复位。",
          golden_reference={
              "status": "passed",
              "tool": "Yosys proc/check + Verilator lint",
              "source_url": "https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/proc.html",
              "command_zh": "yosys -p \"read_verilog -sv <case>.v; hierarchy -top top; proc; check\"；可选 tools/verilator/usr/bin/verilator --lint-only --Wall <case>.v。",
              "note_zh": "Yosys process lowering 用于开发期 structural reference；标准时钟加异步复位的负例用 metadata 确认。",
          }),
    _case("P1_ASYNC_DATA_CONTROL", "P1", "复位之外的异步数据或控制路径", "async_path", "profiling", "supported",
          ["RISK_ASYNC_DATA_CONTROL", "RISK_CDC_UNSYNC_SIGNAL"],
          [f"{RISK_CASE}/async_data_control_event/case.json", f"{RISK_CASE}/async_reset_control_safe/case.json", f"{RISK_CASE}/cdc_unsync_signal/case.json", f"{RISK_CASE}/cdc_multibit_unsync_signal/case.json", "tests/test_long_task_coverage.py"],
          "扩展异步脉冲丢失分析、握手协议、异步 FIFO 和多位 coherency 检查。",
          support_note_zh="已覆盖非 reset 信号直接作为时序事件，以及简单单/多 bit 跨时钟域直接采样；标准异步 reset 和两级同步器负例不报告。仍不是 signoff CDC。",
          golden_reference={"status": "metadata_reference", "tool": "case.json metadata", "source_url": None, "command_zh": "python3 tests/test_long_task_coverage.py", "note_zh": "使用可复现正负例验证事件控制和简单 CDC 边界，不引入外部 CDC 工具运行时依赖。"}),
]


RULE_TO_CASE_IDS: dict[str, list[str]] = {}
for _item in CASE_REGISTRY:
    for _rule in _item["rule_ids"]:
        if not _rule.endswith("*"):
            RULE_TO_CASE_IDS.setdefault(_rule, []).append(_item["case_id"])


def case_registry(root: Path | None = None) -> list[dict[str, Any]]:
    base = (root or PROJECT_ROOT).resolve()
    cases: list[dict[str, Any]] = []
    for item in CASE_REGISTRY:
        copied = dict(item)
        copied["rule_ids"] = list(item["rule_ids"])
        copied["test_paths"] = list(item["test_paths"])
        copied["golden_reference"] = dict(item["golden_reference"])
        copied["verification_evidence"] = [path for path in copied["test_paths"] if (base / path).exists()]
        copied["latest_verification_evidence"] = _latest_evidence(base, copied["verification_evidence"])
        copied["test_status"] = _test_status(copied["support_status"], copied["verification_evidence"])
        cases.append(copied)
    return cases


def coverage_summary(cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    data = cases or case_registry()
    result: dict[str, Any] = {
        "total": len(data),
        "owner_counts": {owner: sum(1 for item in data if item["owner"] == owner) for owner in ("lint", "profiling", "both")},
        "priorities": {},
    }
    for priority in ("P0", "P1"):
        selected = [item for item in data if item["priority"] == priority]
        supported = sum(item["support_status"] == "supported" for item in selected)
        unsupported = sum(item["support_status"] == "unsupported_diagnostic" for item in selected)
        partial = sum(item["support_status"] == "partially_supported" for item in selected)
        unsupported_by_design = sum(item["support_status"] == "unsupported_by_design" for item in selected)
        uncovered = sum(item["support_status"] == "not_covered" for item in selected)
        covered = supported + unsupported + unsupported_by_design
        result["priorities"][priority] = {
            "total": len(selected),
            "covered": covered,
            "supported": supported,
            "unsupported_diagnostic": unsupported,
            "unsupported_by_design": unsupported_by_design,
            "partially_supported": partial,
            "partially_covered": partial,
            "not_covered": uncovered,
            "uncovered": uncovered,
            "coverage_percent": round(100.0 * covered / len(selected), 1) if selected else 0.0,
        }
    return result


def classify_diagnostic(rule: str | None, category: str | None, source: str) -> dict[str, Any] | None:
    rule_text = str(rule or "")
    case_ids = list(RULE_TO_CASE_IDS.get(rule_text, []))
    if not case_ids and source == "lint":
        if rule_text.startswith(("LEX", "PARSE", "PP", "SYN", "SEM00")):
            case_ids = ["P0_SYNTAX_GRAMMAR"]
        elif rule_text.startswith("UNSUPPORTED"):
            case_ids = ["P0_SYNTHESIZABILITY", "P1_COMPLEX_GENERATE"]
    if not case_ids:
        return None
    by_id = {item["case_id"]: item for item in CASE_REGISTRY}
    primary = by_id[case_ids[0]]
    return {
        "case_id": primary["case_id"],
        "case_name_zh": primary["name_zh"],
        "priority": primary["priority"],
        "case_category": primary["category"],
        "owner": primary["owner"],
        "support_status": primary["support_status"],
        "related_case_ids": case_ids[1:],
        "diagnostic_category": category,
    }


def _test_status(support_status: str, evidence: list[str]) -> str:
    if support_status == "not_covered" or not evidence:
        return "missing"
    if support_status == "partially_supported":
        return "partial"
    return "passed"


def _latest_evidence(base: Path, evidence: list[str]) -> dict[str, Any] | None:
    if not evidence:
        return None
    path = max(evidence, key=lambda item: (base / item).stat().st_mtime)
    return {
        "path": path,
        "modified_timestamp": round((base / path).stat().st_mtime, 3),
    }
