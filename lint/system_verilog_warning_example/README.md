# SystemVerilog Warning 语料

本目录保存 SystemVerilog warning/lint-like 语料，用于验证 STA-lite 对常见 SV RTL 风险的内部诊断能力。

## 用途

- 覆盖 `.sv` 文件中的 warning 级风险。
- 使用 `case.json` metadata 作为默认 reference。
- 不强制依赖外部 SystemVerilog 工具。

## 当前类别

- `implicit_cast_width`：隐式网线、端口位宽不匹配、常量 select 越界。
- `always_comb_latch_risk`：`always_comb` 分支覆盖不完整导致 latch 风险。
- `enum_usage`：enum typedef 使用的语法级不误报覆盖。
- `interface_connection`：interface 实例连接形状的语法级不误报覆盖。
- `style_timing_risk`：`always_comb` 中长组合表达式导致早期时序风险。

## 运行

```sh
./sta-lite lint-diff \
  --cases lint/system_verilog_warning_example \
  --out reports/lint_diff_sv_warning
```

## 当前状态

当前内置 9 个 SystemVerilog warning case。最近一次完整差分中，本目录没有发现 STA-lite 漏报。

## 限制

- 当前不做完整 SV 类型转换、signedness、enum coverage、interface connection elaboration。
- warning 级规则是早期风险提示，不等价于综合器或仿真器的完整诊断。
