# RTL 时序风险语料与规则说明

`risk_profile/` 用于维护 STA-lite 的 RTL timing-risk profiling 语料。它和 lint 的职责不同：

- lint 关注语法、可综合性、声明/端口/表达式等前端质量问题。
- RTL timing-risk profiling 关注“即使语法正确，也可能在综合、布局布线或 STA 阶段变成时序风险”的代码结构。

本功能直接读取 Verilog/SystemVerilog RTL，复用 STA-lite 内部 preprocessor、lexer、parser、AST 和 symbol context，不调用 Yosys、OpenSTA、OpenROAD、Vivado、Quartus 或商业 EDA 工具。OpenSTA/backend 报告只作为可选离线 gold，用来评估 RTL 风险和真实后端违例之间的相关性。

当前 GUI 中这些语料有三个相关入口：

- `RTL Review`：推荐入口，统一运行 lint_v0 和 risk，并展示两个子流程的独立状态、合并诊断表和报告反向定位状态。
- `RTL 时序风险 Profiling`：只运行 risk workflow，适合单独调试某个 `RISK_*` 规则。
- `Case Coverage`：只读查看 P0/P1 Case 的 profiling/lint owner、支持状态、规则和验证证据。

两个入口都可以从 `risk_profile/cases/*/case.json` 自动发现用例并一键加载。

## 调研摘要

本轮实现前参考了公开资料，主要结论如下：

- AMD UG949 的 RTL coding guidelines 和 timing closure 章节把 reset、clock enable、高扇出、pipelining、priority encoder、RAM/DSP inference、clocking、CDC 和 I/O constraint 作为影响 timing closure 的关键主题。参考：[AMD UG949 Timing Closure](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Timing-Closure)、[Consider Pipelining Up Front](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Consider-Pipelining-Up-Front)、[Using Gated Clocks](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Using-Gated-Clocks)。
- Reset synchronizer 资料强调异步复位可以异步 assert，但 release 应按接收时钟同步，否则释放边沿靠近时钟边沿时可能产生亚稳态。参考：[fpgacpu.ca Reset Synchronizer](https://fpgacpu.ca/fpga/Reset_Synchronizer.html)。
- OpenSTA 文档说明 OpenSTA 是 gate-level static timing verifier，输入通常包括 gate-level Verilog netlist、Liberty、SDC、SPEF 等；因此 STA-lite 的 RTL 风险分析不能等价替代 OpenSTA，只能作为前置风险筛查。参考：[OpenROAD OpenSTA documentation](https://openroad.readthedocs.io/en/latest/main/src/sta/README.html)。
- 01signal timing closure 文章说明 timing closure 常围绕 negative slack、critical path、logic levels、fanout 和 timing report 异常展开；RTL 阶段应尽早避免明显难收敛结构。参考：[01signal The art of Timing Closure](https://www.01signal.com/constraints/timing/timing-closure/)。
- Yosys 官方 `scc` pass 用于识别 strongly connected components，也就是 logic loops；STA-lite 的组合环路规则采用同类 SCC 思路，但直接在 RTL AST 上运行。参考：[Yosys scc](https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/scc.html)。
- Yosys FSM 文档说明 `fsm_detect`、`fsm_extract`、`fsm_info` 可识别状态寄存器并抽取 FSM 信息；STA-lite 使用该流程做开发期 reference，鲁棒性 warning 仍以本仓库 metadata 正负例验证。参考：[Yosys FSM handling](https://yosyshq.readthedocs.io/projects/yosys/en/latest/using_yosys/synthesis/fsm.html)。
- Yosys memory 流程会用 `memory_dff` 合并读端寄存器、用 `memory_collect` 收集 memory cell，适合作为 RAM 结构的开发期 reference；STA-lite 的生产规则仍直接分析 RTL。参考：[Yosys memory synthesis](https://yosyshq.readthedocs.io/projects/yosys/en/v0.56/using_yosys/synthesis/memory.html)、[memory_collect](https://yosyshq.readthedocs.io/projects/yosys/en/0.34/cmd/memory_collect.html)。
- Yosys `alumacc`/器件 DSP passes 可作为宽乘加 lowering 的开发期观察，但实际 DSP 映射依赖器件架构和寄存器模板。参考：[Yosys xilinx_dsp](https://yosyshq.readthedocs.io/projects/yosys/en/v0.51/cmd/xilinx_dsp.html)。

## 目录结构

```text
risk_profile/
  README.md
  cases/
    async_reset_release_unsync/
    long_comb_path/
    latch_inference_timing/
    high_fanout_control/
    gated_or_derived_clock/
    wide_mux_priority_encoder/
    wide_mux_case_vector/
    small_mux_safe/
    arithmetic_chain_no_pipeline/
    arithmetic_pipelined_safe/
    cdc_unsync_signal/
    cdc_multibit_unsync_signal/
    cdc_two_ff_sync_safe/
    comb_loop_two_signal/
    comb_loop_self/
    comb_loop_always/
    comb_loop_ternary/
    comb_loop_always_comb_sv/
    comb_loop_seq_feedback_safe/
    comb_chain_safe/
    fsm_robust_safe/
    fsm_missing_reset/
    fsm_missing_case_default/
    fsm_unsafe_default/
    fsm_missing_state/
    fsm_incomplete_next_assign/
    fsm_terminal_state/
    non_fsm_safe/
    multicycle_without_constraint/
    io_constraint_missing/
    memory_or_dsp_chain_no_pipeline/
  gold/
    opensta/
  reports/
```

每个 case 目录包含：

- 最小 RTL 源码。
- `case.json`，记录语言、类别、top、文件、期望风险 ID、gold 状态。
- `README.md`，用中文解释为什么该结构可能带来时序风险。

## 当前规则覆盖

第一版 smoke 必测并实现：

- `RISK_ASYNC_RESET_RELEASE_UNSYNC`：异步复位直接进入时序逻辑，未看到明显释放同步器。
- `RISK_LONG_COMB_PATH`：组合块或连续赋值中算术、比较、选择操作较多。
- `RISK_LATCH_TIMING`：组合逻辑分支覆盖不完整，可能推断 latch。
- `RISK_HIGH_FANOUT_CONTROL`：控制/复位/使能类信号在多个逻辑上下文中使用。
- `RISK_GATED_OR_DERIVED_CLOCK`：RTL 中用逻辑表达式生成或使用门控/派生时钟。
- `RISK_COMBINATIONAL_LOOP`：连续赋值和组合 always/always_comb 构建信号依赖图，用 Tarjan SCC 检测自环和多信号组合环路；时序 always 边界会切断依赖。
- `RISK_FSM_ROBUSTNESS`：识别清晰两进程 FSM，检查缺 reset、缺 case default、不安全 default、next-state 不完整、声明状态未处理和明显终止状态。
- `RISK_EXCESSIVE_RESET`：分析常见同步/异步 reset 分支，收集 reset 信号、极性、受影响寄存器、可解析宽度和估算 reset 位数；默认在至少 8 个寄存器或 64 个 reset 位时报告。该规则只做 RTL 结构范围估算，不声称 reset-tree 物理时序、布线或拥塞结论。
- `RISK_RAM_INFERENCE`：识别常见 unpacked 存储数组、索引读写以及同步/异步上下文；不承诺综合后的 RAM 宏映射。
- `RISK_DSP_INFERENCE`：识别 8 bit 及以上乘法/乘加候选并记录宽度、操作数和寄存器上下文；不承诺目标 DSP 映射。
- `RISK_MISSING_PIPELINE`：检查寄存器边界之间的宽算术、比较和多级选择组合网络；阈值可配置，不预测真实 slack。
- `RISK_HIGH_FANOUT_CLOCK_ENABLE`：统计首个 CE 分支覆盖的寄存器数量和 bit 数，默认阈值为 8 个寄存器或 64 bit。
- `RISK_ASYNC_DATA_CONTROL`：报告复位之外的信号直接作为时序事件控制；与现有简单 CDC 规则共同覆盖 P1 异步数据/控制最小范围。

已放入语料并带有初步/占位检测：

- `RISK_WIDE_MUX_PRIORITY_ENCODER`
- `RISK_ARITH_CHAIN_NO_PIPELINE`
- `RISK_CDC_UNSYNC_SIGNAL`
- `RISK_MULTICYCLE_WITHOUT_CONSTRAINT`
- `RISK_IO_CONSTRAINT_MISSING`
- `RISK_MEMORY_OR_DSP_CHAIN_NO_PIPELINE`

P0 加固后的规则证据：

- `RISK_CDC_UNSYNC_SIGNAL`：覆盖单 bit 和多 bit 直接跨域采样，并识别 `*_meta`/`*_sync` 两级同步器负例；仍不是 signoff CDC。
- `RISK_WIDE_MUX_PRIORITY_ENCODER`：记录分支数、同目标赋值次数和估算输出宽度，覆盖 if/else 优先级链和 case 选择网络，并有小 mux 负例。
- `RISK_ARITH_CHAIN_NO_PIPELINE`：记录算术操作数、乘法数量和最大操作数宽度，覆盖宽乘加比较链，并有寄存器流水负例。
- `RISK_COMBINATIONAL_LOOP`：正例覆盖连续赋值双信号环、自环、组合过程块环、三目表达式环和 SystemVerilog `always_comb`；负例覆盖寄存器时序反馈和无环组合链。
- `RISK_FSM_ROBUSTNESS`：正例覆盖 missing reset、missing case default、unsafe default、declared state not handled、incomplete next-state assignment 和 obvious terminal state；负例覆盖稳健两进程 FSM 和普通非 FSM 计数器。

这些 P0 risk 规则使用 `case.json` metadata 正负例作为轻量参考；是否真的成为后端 timing violation 仍取决于目标频率、工艺/器件、综合和布局布线。

## 运行方式

运行单个 case：

```sh
./sta-lite risk \
  --rtl risk_profile/cases/long_comb_path/long_comb_path.v \
  --top top \
  --out runs/risk_long_comb
```

带 SDC 的约束类检查：

```sh
./sta-lite risk \
  --rtl risk_profile/cases/io_constraint_missing/io_constraint_missing.v \
  --top top \
  --sdc risk_profile/cases/io_constraint_missing/missing_io.sdc \
  --out runs/risk_io_constraint
```

运行 smoke 回归：

```sh
python3 tests/test_risk_profile.py
python3 tests/test_p0_remaining_cases.py
python3 tests/test_p1_case_upgrades.py
python3 tests/test_long_task_coverage.py
python3 tests/test_standalone_core.py
```

运行 Yosys 开发期 reference：

```sh
python3 tests/test_p0_yosys_reference.py
```

该测试会在本机存在 `yosys` 时执行：

```sh
yosys -p "read_verilog -sv <files>; hierarchy -top <top>; proc; opt; check; scc"
yosys -p "read_verilog -sv <files>; hierarchy -top <top>; proc; opt; fsm_detect; fsm_extract; fsm_info"
```

结果写入 `reports/p0_remaining_yosys/yosys_results.json`。Yosys 只用于开发期 reference，STA-lite 正常 `risk` / `review` / GUI 运行不会调用它。

P1 reset/multi-clock 开发期 reference 与 lint metadata 对比：

```sh
python3 tests/test_p1_golden_reference.py
```

该测试会优先使用工作区 `tools/verilator/usr/bin/verilator`（本次实际版本：`4.038`）和系统 `yosys`（本次实际版本：`0.9`）；若可选工具缺失，会以中文提示并回退到 `case.json` 正负例。Verilator 来源为 Ubuntu 官方包：`apt-get download verilator`，随后 `dpkg-deb -x verilator_<version>_amd64.deb tools/verilator`；Yosys 可通过 Ubuntu 包安装：`sudo apt-get install yosys`。记录的安装来源、版本、命令、标准化结果和耗时写入 `runs/p1_golden_reference/golden_results.json`。参考命令为：

```sh
tools/verilator/usr/bin/verilator --lint-only --Wall --language 1364-2005 -Wno-fatal <case>.v
yosys -p "read_verilog <reset_case>.v; hierarchy -top top; proc; opt; stat"
yosys -p "read_verilog -sv <multi_clock_case>.v; hierarchy -top top; proc; check"
```

Verilator 官方 warning 文档列出了 `CASEX`、`UNSIGNED`、`WIDTH` 等相关类别；Yosys `proc` 会将 process lower 为 mux、寄存器并识别异步 reset。二者仅作开发期 reference，阈值和 policy warning 使用本仓库 metadata 对比。

本轮剩余 P0/P1 Case 使用以下开发期 reference；若工具未安装，测试会用中文提示并使用 `case.json` 正负例，不影响生产运行：

```sh
python3 tests/test_long_task_golden_reference.py
yosys -p "read_verilog <ram_case>.v; hierarchy -top top; proc; memory_dff; memory_collect; stat"
yosys -p "read_verilog <dsp_case>.v; hierarchy -top top; proc; alumacc; stat"
verilator --lint-only --Wall <parameter_or_synth_case>.v
```

完整 29 项状态、规则、证据、reference 和后续边界见 [`COVERAGE_BASELINE.md`](COVERAGE_BASELINE.md)。当前 P0 为 16 项支持、1 项部分支持（FSM 两进程子集），P1 为 12/12 支持；这里的支持始终限定为登记表中说明的 RTL-only 筛查范围。

验证 GUI Risk API：

```sh
python3 tests/risk_gui_api_smoke.py
```

启动 GUI 后，可在“RTL 时序风险 Profiling”面板直接运行同一套 risk workflow：

```sh
./sta-lite gui
```

浏览器打开 `http://127.0.0.1:8765/`：

- 在 `RTL Review` 页面中，选择 risk case 后点击“开始 RTL Review”，GUI 会同时展示 lint 问题数、risk 风险数、两个子流程状态、合并诊断表和输出路径。
- 在 `RTL 时序风险 Profiling` 面板中，选择 risk case 后点击“开始风险分析”，GUI 会展示实时中文日志、耗时、风险等级、风险表、证据字段和输出文件路径。
- 在 `Case Coverage` 页面中，可以按 P0/P1、owner、类别和支持状态查看共享注册表。

GUI Risk 面板还会自动读取 `risk_profile/cases/*/case.json`，可以从下拉框一键加载用例；风险结果表支持按规则 ID 和风险级别筛选，适合先聚焦 `high` 级别或某一个 `RISK_*` 规则。

GUI RTL Review 面板会把 lint/profiling 统一成一个表格，支持按来源、P0/P1、规则 ID、类别、文件和级别筛选，适合综合前集中检查 P0 风险。重叠结果保留各自证据，并用关联组标识。

每次运行会生成：

- `risk.log`
- `risk_summary.json`
- `risk_report.md`

## Gold 对比

`risk_profile/gold/opensta/` 可放置后端 STA 文本报告；CLI/GUI 也可以直接填写单个 `.rpt/.txt/.log/.json` gold 报告文件。`sta-lite risk` 会尝试做粗粒度文本关键字对比，输出：

- STA-lite 发现且 gold 中有相似类别的风险。
- STA-lite 发现但 gold 中未体现的风险。
- gold 中出现但 STA-lite 未预测的类别。

如果 gold 目录不存在或为空，风险分析仍然正常完成。gold 对比只用于开发期评估，不是产品运行依赖。

## 当前限制

- 当前风险判断是启发式，不做真实门级延迟、布线 RC、时钟树、PVT、MCMM 或物理拥塞建模。
- Case Coverage 使用 `supported`、`partially_supported`、`unsupported_diagnostic`、`unsupported_by_design` 和 `not_covered` 五种状态；未实现项会明确标出，不应理解为已完整覆盖。
- 核心 Python 运行路径不启动外部 EDA 子进程；`tests/test_standalone_core.py` 会在无工具 `PATH` 下禁止 subprocess，并验证 lint/risk/review 结果与正常环境一致。Backend 工具缺失只显示中文可选状态。
- CDC/RDC、reset、multicycle 和 I/O 约束规则只做早期提示，不等价于专业 signoff CDC/RDC 或 STA 检查。
- SystemVerilog 支持取决于现有 lint 前端的语法覆盖；暂不做完整 SV elaboration、类型推导或接口语义分析。
- 组合环路检查只基于当前 RTL AST 的连续赋值和组合过程赋值依赖；暂不展开复杂函数、层次实例和完整参数 elaboration。
- FSM 鲁棒性检查仅覆盖清晰两进程 FSM；one-process FSM、复杂 enum/package/generate FSM 和 formal reachability 不在第一版范围内，详见 `risk_profile/FSM_ROBUSTNESS_DESIGN.md`。
- 高扇出只基于 RTL 使用上下文估算，不知道综合复制、物理扇出和 buffer tree。
- 过度 reset 仅覆盖常见时序过程的首个 reset 分支和可解析 packed 宽度；复杂 generate、数组、interface、宏生成结构和完整参数 elaboration 是下一步改进，不影响当前常见同步/异步 reset 子集。
- 后端报告反向定位到 RTL file/line 当前仍是 TODO 状态；已有后端路径解析，但还没有可靠的 netlist token 到 RTL source index 映射。

## 添加新 case

新增 case 时建议：

1. 一个目录只放一种风险。
2. RTL 保持小而单一。
3. `case.json` 中写清 `expected_risks`、`expected_severity` 和 `gold_available`。
4. 如果有 OpenSTA/backend 报告，把报告放到 `risk_profile/gold/opensta/` 或 case 自己的说明中，并注明来源。
