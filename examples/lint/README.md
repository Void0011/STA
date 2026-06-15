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
- `default_nettype_missing`：应产生 `RTL001_DEFAULT_NETTYPE`。
- `implicit_net`：应产生 `RTL002_IMPLICIT_NET_RISK`。
- `preprocessor`：验证 include、define、ifdef。
- `unsupported`：`.v` 中应产生 `UNSUPPORTED_VERILOG`，`.sv` 中应产生 `UNSUPPORTED_SYSTEMVERILOG`。
- `custom_rule`：配合 `custom_rules.json` 应产生 `CUSTOM001`。
