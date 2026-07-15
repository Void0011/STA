# STA-lite Lint 示例

这些示例用于验证内部 Verilog/SystemVerilog lint 引擎，不依赖 Verilator、Icarus Verilog、Yosys、OpenSTA、slang 或 Verible。

- `clean_ok`：语法和核心 lint 应通过。
- `clean_counter`：当前可用于手动注入语法错误并和 iverilog gold 对比。
- `syntax_error`：应产生 `SYNTAX001`。
- `latch_risk`：应产生 `RTL003_LATCH_RISK`。
- `gated_clock`：应产生 `RTL004_GATED_CLOCK_RISK`。
- `long_comb`：应产生 `RTL005_LONG_COMB_HEURISTIC`。
- `blocking_seq`：应产生 `RTL006_BLOCKING_IN_SEQUENTIAL`。
- `nonblocking_comb`：应产生 `RTL007_NONBLOCKING_IN_COMB`。
- `multi_driver`：应产生 `RTL008_MULTI_DRIVER_RISK`。
- `async_reset`：应产生 `RTL009_ASYNC_RESET_RELEASE_RISK`。
- `constraint_mismatch`：配合 `bad_clock.sdc` 应产生 `RTL010_CONSTRAINT_CLOCK_MISMATCH`。
- `lint/verilog_warning_example/width_range`：覆盖 `RTL013_PORT_WIDTH_MISMATCH`、`RTL014_SELECT_RANGE` 和 `RTL020_ASSIGN_WIDTH_MISMATCH`。
- `lint/verilog_warning_example/latch_risk`：覆盖 `RTL003_LATCH_RISK` 和 `RTL021_INCOMPLETE_CASE_DEFAULT` 的正负例。
- `lint/verilog_warning_example/synthesizability`：覆盖 `RTL025_SYNTHESIZABILITY_RISK` 的 initial/延时/仿真任务正例和普通寄存器负例。
- `lint/verilog_warning_example/generate_elaboration`：覆盖 `RTL026_COMPLEX_GENERATE_RISK` 的参数化复杂 generate 正负例。
- `lint/verilog_warning_example/parameter_width`：覆盖 `RTL027_PARAMETER_WIDTH_RISK` 的零参数派生负下标与合法宽度负例。
- `default_nettype_missing`：应产生 `RTL001_DEFAULT_NETTYPE`。
- `implicit_net`：应产生 `RTL002_IMPLICIT_NET_RISK`。
- `preprocessor`：验证 include、define、ifdef。
- `unsupported`：`.v` 中应产生 `UNSUPPORTED_VERILOG`，`.sv` 中应产生 `UNSUPPORTED_SYSTEMVERILOG`。
- `custom_rule`：配合 `custom_rules.json` 应产生 `CUSTOM001`。
