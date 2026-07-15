# STA-lite

本工程是一个可在 Windows 10、Windows 11 和 Ubuntu 20.04+ 本地使用的 STA-lite 工具。当前稳定版本为 `v0.2.0`，定位是 RTL 阶段后端风险预警和报告定位辅助，不是 signoff STA。

当前 GUI 分为五个职责清晰的页面：

1. `RTL Review`：统一运行并汇总 RTL Lint 与 RTL Timing Risk Profiling。
2. `RTL Lint`：单独运行内部 lint_v0，查看语法、语义和 RTL 质量诊断。
3. `RTL Timing Risk Profiling`：单独查看源码级结构和早期时序风险。
4. `Yosys/OpenSTA Backend Analysis`：运行本地 Yosys/OpenSTA 后端参考分析，生成 WNS/TNS、违例路径和 `summary.json`。
5. `Case Coverage`：只读展示 29 个 P0/P1 Case 的 owner、支持状态、规则和验证证据。

`RTL Review = RTL Lint + RTL Timing Risk Profiling`。前三个页面共享同一套内部 workflow，不复制规则，也不要求 Yosys/OpenSTA；后端分析保持为可选、本地、可复现的参考流程。RTL Review 的结果是早期 warning，不等价于真实物理 timing closure 或 signoff STA。

## 安装发行版

Windows 10/11 x64 用户优先使用 GitHub Release 中对应的 Setup EXE。安装器内置 Python 运行时、STA-Lite GUI、RTL Review/Lint/Risk 引擎、示例和 Case Coverage 资源，安装后从桌面或开始菜单启动即可；核心四页不需要安装任何 EDA 软件。首次启动会创建 `%USERPROFILE%\Documents\STA-Lite-Workspace`，用户报告不会随卸载删除。

Ubuntu 20.04+ x86_64 用户使用 `STA-Lite-0.2.0-Ubuntu20+-x86_64.tar.gz`，解压后执行：

```sh
./install_ubuntu.sh
sta-lite-gui
```

发布目录结构、校验方法、兼容性边界和复现命令见 [`install_package/README.md`](install_package/README.md) 与 [`docs/RELEASE_GUIDE.md`](docs/RELEASE_GUIDE.md)。Windows EXE 必须在 Windows 构建机生成；仓库中的 tag workflow 会分别形成 `window10`、`window11` artifact，并在全部回归通过后发布为 GitHub Release Assets。

从源码运行仍可使用：

```sh
./sta-lite gui --open-browser
./sta-lite review --rtl <rtl.v> --top <top> --out runs/review
```

## 内部 Lint 流程

`sta-lite lint` 使用项目内部 Python 代码实现：

```text
RTL -> preprocessing -> lexer -> parser -> AST/symbol context -> built-in/custom rules -> lint_summary.json
```

该流程不会调用 Verilator、Icarus Verilog、Yosys、OpenSTA、slang、Verible 或商业 EDA 工具。

基本命令：

```sh
./sta-lite lint \
  --rtl examples/lint/clean_counter/clean_counter.sv \
  --top clean_counter \
  --out runs/lint_clean
```

带 include、define、SDC 和自定义规则：

```sh
./sta-lite lint \
  --rtl examples/lint/preprocessor/preprocessor.sv \
  --top preprocessor_example \
  --include examples/lint/preprocessor \
  --define USE_FF=1 \
  --rules examples/lint/custom_rule/custom_rules.json \
  --sdc examples/lint/constraint_mismatch/bad_clock.sdc \
  --out runs/lint_full
```

输出 JSON 到终端：

```sh
./sta-lite lint \
  --rtl examples/lint/latch_risk/latch_risk.sv \
  --top latch_risk \
  --out runs/lint_latch \
  --format json \
  --fail-on never
```

每次 lint 会在输出目录生成：

- `lint.log`：lint 过程日志
- `lint_summary.json`：结构化诊断摘要
- `tokens.json`：使用 `--debug` 时生成
- `ast.json`：使用 `--debug` 时生成

`lint_summary.json` 包含 RTL 文件、top、include、define、SDC、耗时、错误/警告/unsupported 计数、诊断列表、自定义规则结果、通过状态和风险说明。

第一版内置规则：

- `RTL001_DEFAULT_NETTYPE`
- `RTL002_IMPLICIT_NET_RISK`
- `RTL003_LATCH_RISK`
- `RTL004_GATED_CLOCK_RISK`
- `RTL005_LONG_COMB_HEURISTIC`
- `RTL006_BLOCKING_IN_SEQUENTIAL`
- `RTL007_NONBLOCKING_IN_COMB`
- `RTL008_MULTI_DRIVER_RISK`
- `RTL009_ASYNC_RESET_RELEASE_RISK`
- `RTL010_CONSTRAINT_CLOCK_MISMATCH`
- `RTL011_TIMESCALE_INCONSISTENT`
- `RTL012_INSTANCE_PORT_UNCONNECTED`
- `RTL013_PORT_WIDTH_MISMATCH`
- `RTL014_SELECT_RANGE`
- `RTL015_UNUSED_SIGNAL`
- `RTL016_ASSIGNED_NOT_READ`
- `RTL017_UNUSED_INPUT`
- `RTL018_UNDRIVEN_OUTPUT`
- `RTL019_INSTANCE_OUTPUT_UNCONNECTED`
- `RTL020_ASSIGN_WIDTH_MISMATCH`
- `RTL021_INCOMPLETE_CASE_DEFAULT`
- `SEM002_PORT_NOT_DECLARED`
- `SEM003_UNDECLARED_IDENTIFIER`
- `SEM004_PROCEDURAL_WIRE_ASSIGN`
- `SEM005_UNRESOLVED_MODULE`
- `SEM006_UNKNOWN_INSTANCE_PORT`
- `UNSUPPORTED_VERILOG`
- `UNSUPPORTED_SYSTEMVERILOG`

自定义规则当前使用 JSON，例如：

```json
{
  "rules": [
    {
      "id": "CUSTOM001",
      "severity": "warning",
      "match": {
        "kind": "signal_name_regex",
        "pattern": "^tmp_"
      },
      "message_zh": "发现 tmp_ 前缀信号，请确认是否只是临时调试命名。",
      "suggestion_zh": "建议使用更明确的业务命名。"
    }
  ]
}
```

当前支持的 `match.kind`：

- `identifier_regex`
- `module_name_regex`
- `signal_name_regex`
- `always_block_kind`
- `forbidden_keyword`

Lint 示例目录：

- `examples/lint/clean_counter`
- `examples/lint/syntax_error`
- `examples/lint/latch_risk`
- `examples/lint/gated_clock`
- `examples/lint/long_comb`
- `examples/lint/blocking_seq`
- `examples/lint/nonblocking_comb`
- `examples/lint/multi_driver`
- `examples/lint/async_reset`
- `examples/lint/default_nettype_missing`
- `examples/lint/implicit_net`
- `examples/lint/constraint_mismatch`
- `examples/lint/preprocessor`
- `examples/lint/unsupported`
- `examples/lint/custom_rule`

运行 lint 回归：

```sh
./scripts/check_lint.sh
```

该回归会把 `PATH` 指向不存在的目录来验证 lint 流程没有依赖外部 EDA 命令。

支持的独立运行环境是 Python 3 标准库加本仓库源码；`./sta-lite lint`、`./sta-lite risk`、`./sta-lite review`、Case Coverage API/GUI 和已有报告读取均不要求安装 Yosys、OpenSTA、Verilator 或 iverilog。`tests/test_standalone_core.py` 还会禁止 `subprocess.run/Popen`，对比有无外部工具时的 lint/risk/review 诊断签名。只有 `analyze` 和 GUI 的 `Yosys/OpenSTA Backend Analysis` 页面需要外部后端工具；缺失时 `/api/backend_status` 与页面会显示中文可选工具状态，不阻塞其他四页。

本仓库也支持用 `iverilog` 作为语法 gold 做回归对比。当前 WSL2 未提供系统级 `iverilog` 时，已将 Ubuntu 官方包解包到工作区安全目录：

```text
tools/iverilog
```

可执行 wrapper：

```sh
tools/bin/iverilog -g2012 -tnull -Wall -s clean_ok examples/lint/clean_ok/clean_ok.sv
```

gold 对比回归：

```sh
python3 tests/test_lint_iverilog_gold.py
```

这项测试只用 `iverilog` 判定 gold 通过/失败，`sta-lite lint` 的实际实现仍走内部 preprocessor/lexer/parser/rule engine。

本轮 P0 位宽和不完整 case/if 加固还使用 Verilator 与 Yosys 作为开发期参考：

- Verilator 官方 warning 文档用于参考 `WIDTH`、`CASEINCOMPLETE`、`LATCH` 等 lint 分类。
- 本地 Verilator 已从 Ubuntu 官方包下载并解包到 `tools/verilator/`，可用命令为 `tools/verilator/usr/bin/verilator --lint-only --language 1364-2005 <file.v>`。
- Yosys 使用系统级 `/usr/bin/yosys`，用于 `read_verilog; proc; opt; check` 这类 latch 结构参考。
- 这些工具只在测试/对比中使用，不会成为 `RTL Review`、`RTL Lint`、`RTL Timing Risk Profiling` 或 `Case Coverage` 的运行依赖。

P0 golden/reference 对比：

```sh
python3 tests/test_p0_golden_reference.py
```

输出报告：

```text
reports/p0_upgrade_golden/golden_results.json
```

标准化 lint 语料差分回归：

```sh
./scripts/check_lint_diff.sh
```

该命令会扫描四个 canonical 语料根目录：

```text
lint/verilog_error_example/
lint/verilog_warning_example/
lint/system_verilog_error_examplr/
lint/system_verilog_warning_example/
```

Verilog 用例使用 `iverilog -g2005 -Wall -tnull -s <top> <files>` 作为开发期 golden；SystemVerilog 用例默认使用 `case.json` metadata 做 expected-vs-actual 对比。报告输出到 `reports/lint_diff/`。

最近一次内置差分语料规模为 147 个 case，其中 Verilog 106 个、SystemVerilog 41 个；期望检出但 STA-lite 漏报为 0。报告中还会生成 `coverage_matrix.json` 和中文 `coverage_matrix.md`，用于查看各语法区域的支持状态、漏检项和下一步建议。

Lint v0 当前覆盖重点：

- Verilog 常见语法、声明、端口、表达式、赋值、过程块、预处理、例化、位宽和 warning-like 风险。
- Verilog `generate/endgenerate`、`genvar`、generate-for/if/case、命名 generate 块、`function/endfunction`、`task/endtask` 和函数调用的语法级结构化识别。
- 未使用/未连接风险：未用声明、赋值未读、输入未用、输出未驱动、实例输出悬空和 `.out()` 空连接。
- P0 位宽加固：端口宽度不匹配、常量位选择越界、赋值截断、多比特隐式扩展，以及显式拼接扩展负例。
- P0 控制流加固：组合 if/case 可能 latch、case 缺 default 但已有默认赋值的可疑结构，以及显式 default 负例。
- SystemVerilog 常见 RTL 前端语法级识别，以及 `class`、assertion、covergroup 等非 RTL 构造的明确 `UNSUPPORTED_SYSTEMVERILOG` 诊断。

`iverilog` 只作为 Verilog 开发期 golden，命令形态为 `iverilog -g2005 -Wall -tnull -s <top> <files>`；不会运行 `vvp`，因为本项目的 lint 回归只做编译期/诊断对比，不执行功能仿真。

验证 GUI Lint API 和实时日志：

```sh
python3 tests/lint_gui_api_smoke.py
```

## RTL 时序风险 Profiling

`sta-lite risk` 使用项目内部 RTL 前端和内置启发式规则运行：

```text
RTL -> preprocessing -> lexer -> parser -> AST/symbol context -> timing-risk rules -> risk_summary.json/risk_report.md
```

该流程不会调用 Yosys、OpenSTA、OpenROAD、Vivado、Quartus 或商业 EDA 工具。OpenSTA/backend 报告只作为可选开发期 gold，用于评估 RTL 风险提示和真实后端违例之间的相关性；没有 gold 报告时不会阻塞运行。

基本命令：

```sh
./sta-lite risk \
  --rtl risk_profile/cases/long_comb_path/long_comb_path.v \
  --top top \
  --out runs/risk_long_comb
```

带 SDC 的约束类风险检查：

```sh
./sta-lite risk \
  --rtl risk_profile/cases/io_constraint_missing/io_constraint_missing.v \
  --top top \
  --sdc risk_profile/cases/io_constraint_missing/missing_io.sdc \
  --out runs/risk_io_constraint
```

每次 risk 运行会在输出目录生成：

- `risk.log`：中文运行日志
- `risk_summary.json`：结构化风险摘要
- `risk_report.md`：中文 Markdown 报告

第一版已实现 smoke 检测：

- `RISK_ASYNC_RESET_RELEASE_UNSYNC`
- `RISK_LONG_COMB_PATH`
- `RISK_LATCH_TIMING`
- `RISK_HIGH_FANOUT_CONTROL`
- `RISK_GATED_OR_DERIVED_CLOCK`

并已放入语料/占位检测：

- `RISK_WIDE_MUX_PRIORITY_ENCODER`
- `RISK_ARITH_CHAIN_NO_PIPELINE`
- `RISK_CDC_UNSYNC_SIGNAL`
- `RISK_MULTICYCLE_WITHOUT_CONSTRAINT`
- `RISK_IO_CONSTRAINT_MISSING`
- `RISK_MEMORY_OR_DSP_CHAIN_NO_PIPELINE`

风险语料位于：

```text
risk_profile/cases/
```

运行 risk 回归：

```sh
./scripts/check_risk.sh
```

这项回归会把 `PATH` 指向不存在的目录，验证 `sta-lite risk` 不依赖外部 EDA 命令。

## RTL Review 工作流

`sta-lite review` 是当前版本推荐的综合前入口。它按顺序运行内部 lint_v0 和 RTL timing-risk profiling，把 lint 诊断与 risk 发现合并成统一的中文表格、结构化 JSON 和 Markdown 报告：

```text
RTL -> sta-lite lint_v0 -> sta-lite risk -> review_summary.json / review_report.md
```

该流程不会调用 Yosys、OpenSTA、OpenROAD、Vivado、Quartus 或商业 EDA 工具。可选 OpenSTA/backend 报告只用于 gold 相关性对比；不提供 gold 时会显示“已跳过”，不会阻塞 RTL Review。

基本命令：

```sh
./sta-lite review \
  --rtl risk_profile/cases/long_comb_path/long_comb_path.v \
  --top top \
  --out runs/review_long_comb
```

带 include、define、SDC、自定义 lint 规则和可选 gold：

```sh
./sta-lite review \
  --rtl src/*.v \
  --top top \
  --include include \
  --define SYNTHESIS=1 \
  --sdc constraints/top.sdc \
  --rules rules/custom_rules.json \
  --gold-dir reports/opensta \
  --out runs/review_top
```

每次 review 会生成：

- `review.log`
- `review_summary.json`
- `review_report.md`
- `lint/lint_summary.json`
- `risk/risk_summary.json`
- `risk/risk_report.md`

`review_summary.json` 重点字段包括：

- `lint_issue_count`、`risk_count`、`total_issue_count`
- `subflows.lint`、`subflows.profiling`：各自的状态、耗时、数量和中文错误
- `risk_level` 和中文 `risk_explanation_zh`
- 合并后的 `items` 表，包含来源、P0/P1、Case ID、规则、类别、级别、文件、行号、置信度、中文说明、建议、证据和关联组
- `case_registry`、`coverage_summary`、`p0_coverage`、`p1_roadmap`
- `report_location_status`

Lint 与 Profiling 彼此隔离：其中一条子流程失败时，Review 返回 `partial_success`，保留另一条子流程已生成的结果和报告。重叠发现不会被静默删除，而是通过 `correlation_id`、`correlated_sources` 和 `overlap_count` 标记。

GUI 默认进入 `RTL Review` 页面。该页面支持：

- 一键加载 `risk_profile/cases/` 用例
- 实时中文日志和耗时显示
- Lint/Profiling 独立状态、耗时和数量，以及合并总数、整体等级和输出文件路径
- 按来源、P0/P1、规则、类别、文件和级别筛选合并诊断表
- 报告反向定位的当前状态/TODO 展示

`Case Coverage` 页面从 `sta_lite.review.case_registry` 读取共享注册表，不在 GUI 中维护第二份列表。当前注册表固定包含 17 个 P0 和 12 个 P1，并使用以下状态：

- `supported`：已有规则实现和可执行验证证据。
- `partially_supported`：只覆盖部分常见场景。
- `unsupported_diagnostic`：能明确输出暂不支持诊断，但没有完整语义支持。
- `not_covered`：尚无检测，不能因为文档提到就算作已支持。
- `unsupported_by_design`：需要物理、signoff 或当前 RTL-only 边界外的数据；当前没有 P0 使用该状态。

每个 Case 的 owner 为 `lint`、`profiling` 或 `both`。页面提供优先级、owner、类别和支持状态筛选，并展示规则、测试/元数据路径、当前存在的验证证据和下一步改进。

P0 当前状态摘要：

- 已支持 16/17：语法 lint、常见不可综合构造、位宽/截断/扩展、latch/不完整 case-if、多驱动、未驱动/未使用、长组合逻辑、高扇出、异步复位、简单 CDC、门控/派生时钟、组合环路、阻塞/非阻塞误用、大 mux/优先级链、宽算术链。
- 部分覆盖：`P0_FSM_ROBUSTNESS` 已覆盖清晰两进程 FSM 的常见鲁棒性问题，但按 `Rules.md` 保持 `partially_supported`，因为它不是 formal FSM 证明，也不覆盖复杂 enum/package/generate FSM。
- 未覆盖：当前 P0 无 `not_covered`。`P0_COMBINATIONAL_LOOP` 已有 SCC 规则和 Yosys reference；`P0_FSM_ROBUSTNESS` 已有可执行用例、设计说明和 Yosys/metadata reference。

P1 当前 12/12 均在文档化 RTL-only 最小范围内标记为 `supported`。本轮新增专用规则包括 `RISK_RAM_INFERENCE`、`RISK_DSP_INFERENCE`、`RISK_MISSING_PIPELINE`、`RISK_HIGH_FANOUT_CLOCK_ENABLE`、`RISK_ASYNC_DATA_CONTROL`、`RTL025_SYNTHESIZABILITY_RISK`、`RTL026_COMPLEX_GENERATE_RISK` 和 `RTL027_PARAMETER_WIDTH_RISK`；每项都有正负例、结构证据与 metadata 或可选外部工具 reference。这里的 `supported` 是早期 RTL 筛查，不等价于器件 RAM/DSP 映射、物理扇出、CDC signoff、完整 elaboration 或真实 slack。

29 项中文基线见 [`risk_profile/COVERAGE_BASELINE.md`](risk_profile/COVERAGE_BASELINE.md)，可用以下命令防止登记表、GUI Coverage 与文档漂移：

```sh
python3 scripts/generate_coverage_baseline.py --check
```

新增 Case 集中验证与开发期 reference：

```sh
python3 tests/test_long_task_coverage.py
python3 tests/test_long_task_golden_reference.py
python3 tests/test_standalone_core.py
```

可选 Yosys reference 使用 `proc; memory_dff; memory_collect; stat` 检查 RAM lowering，使用 `proc; alumacc; stat` 检查宽乘加 lowering；可选 Verilator 使用 `--lint-only --Wall` 观察参数位宽/可综合性 warning。工具缺失时测试以中文跳过并保留 `case.json` metadata 对比，生产流程从不调用这些命令。

GUI 中也可以直接运行 RTL 时序风险 profiling。启动 GUI 后，在“RTL 时序风险 Profiling”面板填写 RTL、top、可选 SDC、输出目录和可选 OpenSTA/backend gold 报告文件或目录，然后点击“开始风险分析”。该面板会显示中文实时日志、耗时、风险数量、整体风险等级、gold 对比摘要、`risk_summary.json`/`risk_report.md`/`risk.log` 路径，以及包含规则、级别、文件、行号、置信度、中文说明、建议和证据字段的风险表。

GUI Risk 面板和 CLI 使用同一个 `sta_lite.risk.workflow`，不会在前端重复实现风险规则。gold 目录为空或不存在时，GUI 会显示“已跳过”而不是报错。面板还支持：

- 从 `risk_profile/cases/` 自动发现 case，并一键加载 RTL/top/SDC/output。
- 按风险规则 ID 筛选风险表。
- 按风险级别 `high`、`medium`、`low` 筛选风险表。
- 显示当前筛选命中数量，便于聚焦高优先级风险。

新增 P0 组合环路和 FSM 鲁棒性回归：

```sh
python3 tests/test_p0_remaining_cases.py
python3 tests/test_p0_yosys_reference.py
```

组合环路 reference 使用：

```sh
yosys -p "read_verilog -sv <files>; hierarchy -top <top>; proc; opt; check; scc"
```

FSM reference 使用：

```sh
yosys -p "read_verilog -sv <files>; hierarchy -top <top>; proc; opt; fsm_detect; fsm_extract; fsm_info"
```

这两个 Yosys 命令只用于开发期对比；STA-lite 正常 `risk`、`review` 和 GUI 不依赖 Yosys。

## GUI/STA 闭环

本地 STA GUI 用来跑通：

```text
Verilog RTL -> Yosys gate-level netlist -> OpenSTA timing report -> summary.json -> GUI result display
```

它不是 signoff STA 工具，当前目标是给早期 RTL 提供可复现、可视化的本地时序风险检查闭环。

## 环境假设

系统级命令需要已经在 `PATH` 中：

```sh
yosys -V
sta -version
```

Ubuntu 的 OpenSTA 包通常提供的命令名是 `sta`，不是 `opensta`。

Nangate45 Liberty 已安装在：

```sh
nangate45/lib
```

常用标准单元库：

```sh
nangate45/lib/NangateOpenCellLibrary_typical.lib
```

## 运行示例

启动本地 Web GUI：

```sh
./sta-lite gui
```

然后在浏览器打开：

```text
http://127.0.0.1:8765/
```

GUI 支持：

- 顶部五页面切换：
  - `RTL Review`：综合前 lint/risk 统一审查，不依赖后端 EDA 工具。
  - `RTL Lint`：独立 lint_v0 输入、日志、诊断和报告。
  - `RTL Timing Risk Profiling`：独立结构/时序风险输入、日志、证据和报告。
  - `Yosys/OpenSTA Backend Analysis`：本地 Yosys/OpenSTA 参考分析。
  - `Case Coverage`：只读查看 29 个 P0/P1 Case 的覆盖状态。
- `RTL Review` 页面：
  - 输入 RTL、top、include、define、SDC、custom lint rules、可选 gold、输出目录。
  - 一键加载 `risk_profile/cases/` 用例。
  - 显示实时中文日志、总耗时、两个子流程的独立状态/耗时/数量、整体等级、输出路径和 gold 对比状态。
  - 合并展示 lint/profiling 表格，并支持按来源、P0/P1、规则、类别、文件和级别筛选。
- `RTL Lint` 页面：保留单独 lint_v0 入口，便于只看语法/规则诊断。
- `RTL Timing Risk Profiling` 页面：保留单独 risk 入口，便于只看 RTL timing-risk 与 gold 相关性。
- `Yosys/OpenSTA Backend Analysis` 页面：
  - 输入 RTL、top、Liberty、clock/period、可选 SDC、输出目录。
  - 启动 Yosys/OpenSTA 分析，实时显示综合和 STA 日志。
  - 展示 WNS、TNS、风险等级、输出路径、负 slack 路径和高风险提示。
  - 显示报告反向定位的当前状态：当前已解析后端路径和 slack，netlist token 到 RTL file/line 的可靠映射仍是 TODO。
  - 启动前进行中文输入校验，并展示可复制的等效 CLI 命令。
  - 页面启动时显示 Yosys/OpenSTA 可选工具状态；工具缺失不会影响 Review、Lint、Profiling、Coverage 或已有报告查看。
- `Case Coverage` 页面：
  - 展示总 Case 数、P0/P1 覆盖数量和百分比，以及 lint/profiling/both owner 数量。
  - 展示 Case ID、中文名称、类别、owner、支持状态、测试状态、规则、测试路径、验证证据和下一步。
  - 支持按 P0/P1、owner、类别和支持状态筛选。

## 当前限制

- STA-lite 不是 signoff STA。当前 RTL risk profiling 只做源码级启发式风险提示，不建模真实门级延迟、布线 RC、时钟树、PVT、OCV/AOCV/POCV 或 MCMM。
- RTL Review 合并 lint_v0 和 risk，用于综合/STA 前代码审查；即使显示 LOW，也不代表后端 STA 或时序收敛已经通过。
- Case Coverage 是人工维护的 Case 分类加当前仓库验证证据，不是 IEEE 合规认证；`partially_supported` 和 `unsupported_diagnostic` 不代表完整实现。
- P0 中简单 CDC、宽 mux 和算术链仍是 RTL-only 启发式检查；它们被标记为 supported 表示当前定义的正负例和 metadata 通过，不代表 signoff CDC 或 timing closure。
- GUI/CLI 的 OpenSTA 闭环依赖本机已安装 Yosys、OpenSTA、Liberty 和合理 SDC；缺少这些环境时仍可运行 review/lint/risk/coverage 和查看已有报告，但不能发起新的后端 STA。
- RTL risk 的高扇出、CDC、reset、multicycle、I/O 约束和 memory/DSP 风险规则还不是 CDC/RDC/signoff timing 等价检查，可能有漏报和误报。
- SystemVerilog 支持是前端语法级增量覆盖，不包含完整 elaboration、interface 语义、class/testbench 语义或复杂类型系统。
- 后端报告反向定位到 RTL 仍处在早期阶段；目前主要解析 startpoint、endpoint、path group、slack、warning 和结构化 summary，尚未完成 netlist path/token 到 RTL 源码 file/line 的可靠映射。
- Web GUI 运行在本地 HTTP 服务上，当前没有项目级多用户权限、远程任务队列或持久化任务数据库。

使用自动生成的简单 SDC：

```sh
./sta-lite analyze \
  --top counter \
  --rtl examples/counter/counter.v \
  --clock clk \
  --period 2.0 \
  --lib nangate45/lib/NangateOpenCellLibrary_typical.lib \
  --out runs/counter
```

多 `.v` 联合输入示例：

```sh
./sta-lite analyze \
  --top multi_top \
  --rtl 'examples/multi_file/rtl/*.v' \
  --clock clk \
  --period 2.5 \
  --lib nangate45/lib/NangateOpenCellLibrary_typical.lib \
  --out runs/multi_file
```

GUI 中也可以点击“填入 multi_file 示例”，该示例由多个 RTL 文件共同组成一个顶层设计。

运行本地 MVP 回归检查：

```sh
./scripts/check_mvp.sh
```

使用自定义 SDC：

```sh
./sta-lite analyze \
  --top counter \
  --rtl examples/counter/counter.v \
  --sdc constraints.sdc \
  --lib nangate45/lib/NangateOpenCellLibrary_typical.lib \
  --out runs/counter_sdc
```

## 输出文件

每次分析会在 `--out` 指定目录中生成：

- `synth.v`：Yosys 生成的门级网表
- `constraints.sdc`：本次运行使用的 SDC，自动生成或从用户 SDC 复制
- `synth.ys`：本次运行使用的 Yosys 脚本
- `opensta.tcl`：本次运行使用的 OpenSTA 脚本
- `yosys.log`：原始 Yosys 日志
- `opensta.log`：原始 OpenSTA 日志
- `checks.rpt`：OpenSTA `report_checks` 原始报告
- `wns.rpt`：OpenSTA `report_wns` 原始报告
- `tns.rpt`：OpenSTA `report_tns` 原始报告
- `summary.json`：解析后的结构化摘要

`summary.json` 至少包含：

- 顶层模块、RTL 文件、Liberty 文件、SDC 文件、生成网表路径
- `wns`、`tns`
- 最差路径的 startpoint、endpoint、path group、slack、arrival time、required time
- Yosys/OpenSTA 警告分类
- `risk_level`：`LOW`、`MEDIUM` 或 `HIGH`
- `risk_explanation_zh`：中文风险说明
- `elapsed_seconds`：本次运行耗时
- `timing_violations`：负 slack 路径列表

## 示例目录

- `examples/lint`：内部 lint 示例和期望触发规则说明
- `examples/counter`：干净的寄存器基线设计
- `examples/multi_file`：多个 `.v` 文件联合组成一个顶层设计；`rtl/` 用于 STA，`tb/` 提供可选功能仿真 testbench
- `examples/long_comb`：组合逻辑较长的寄存器路径
- `examples/latch`：用于触发 latch 相关综合风险
- `examples/no_clock`：用于验证缺失 clock/SDC 的错误处理

## 当前限制

第一版 MVP 暂不实现：

- FPGA 真实物理互连延迟建模
- placement/routing 估计
- ML 时序预测
- 多 corner / 多 mode signoff STA
- 复杂 CDC/RDC 分析
- PrimeTime 命令兼容

GUI 当前使用 Python 标准库 HTTP 服务和浏览器页面实现，不依赖 tkinter、PyQt 或 Flask。

内部 lint 当前是实用 RTL 子集，不覆盖完整 IEEE 1364/IEEE 1800。暂不支持的 Verilog 构造会输出 `UNSUPPORTED_VERILOG`，暂不支持的 SystemVerilog 构造会输出 `UNSUPPORTED_SYSTEMVERILOG`，而不是静默通过或崩溃。

## 旧版最小脚本

仓库仍保留早期最小闭环脚本：

```sh
./run_sta.sh
```

它使用 `rtl/top.v`、`lib/example.lib`、`scripts/synth.ys` 和 `scripts/sta.tcl`，主要用于快速 sanity check。新的 MVP 流程请优先使用 `./sta-lite analyze`。
