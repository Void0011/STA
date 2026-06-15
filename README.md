# STA-lite

本工程是一个 WSL2 Ubuntu 本地使用的 STA-lite 工具。当前包含两个能力：

1. 内部 Verilog/SystemVerilog Lint：不调用外部 EDA 工具。
2. GUI/CLI 本地 STA 闭环：Verilog RTL -> Yosys -> OpenSTA -> summary.json。

Lint 当前优先用于早期 RTL 风险检查；STA 闭环用于后续本地综合和 OpenSTA 报告生成。

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

最近一次内置差分语料规模为 130 个 case，其中 Verilog 90 个、SystemVerilog 40 个；期望检出但 STA-lite 漏报为 0。报告中还会生成 `coverage_matrix.json` 和中文 `coverage_matrix.md`，用于查看各语法区域的支持状态、漏检项和下一步建议。

Lint v0 当前覆盖重点：

- Verilog 常见语法、声明、端口、表达式、赋值、过程块、预处理、例化、位宽和 warning-like 风险。
- Verilog `generate/endgenerate`、`genvar`、generate-for/if/case、命名 generate 块、`function/endfunction`、`task/endtask` 和函数调用的语法级结构化识别。
- 未使用/未连接风险：未用声明、赋值未读、输入未用、输出未驱动、实例输出悬空和 `.out()` 空连接。
- SystemVerilog 常见 RTL 前端语法级识别，以及 `class`、assertion、covergroup 等非 RTL 构造的明确 `UNSUPPORTED_SYSTEMVERILOG` 诊断。

`iverilog` 只作为 Verilog 开发期 golden，命令形态为 `iverilog -g2005 -Wall -tnull -s <top> <files>`；不会运行 `vvp`，因为本项目的 lint 回归只做编译期/诊断对比，不执行功能仿真。

验证 GUI Lint API 和实时日志：

```sh
python3 tests/lint_gui_api_smoke.py
```

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

- RTL Lint 面板：输入 RTL/include/define/SDC/规则文件，显示 lint 日志、耗时、计数和诊断表
- 输入 RTL、top、Liberty、clock/period、可选 SDC、输出目录
- 启动 Yosys/OpenSTA 分析
- 实时显示综合和 STA 日志
- 显示运行耗时
- 展示 WNS、TNS、风险等级、输出路径
- 在独立区域展示负 slack 路径和高风险提示
- 启动前进行中文输入校验，并展示可复制的等效 CLI 命令

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
