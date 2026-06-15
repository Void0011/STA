# Verilog Warning 语料

本目录保存 Verilog warning/lint-like 语料。部分 warning 可由 `iverilog -Wall` 作为 golden 观察，部分属于 STA-lite 内部早期风险规则。

## 用途

- 覆盖隐式网线、端口连接、位宽/越界、timescale、未使用/未连接、多驱动、latch 风险和长组合路径风险。
- 分离 warning 与 error 语料，避免 warning 样例污染语法错误覆盖率。
- 继续运行 Verilog iverilog golden，但允许部分 STA-lite 产品规则使用 metadata 期望。

## 当前类别

- `implicit_net`：未声明信号形成隐式 wire。
- `port_connection`：子模块输入端口悬空。
- `width_range`：端口位宽不匹配、常量 select 越界。
- `timescale`：缺失或继承 timescale。
- `unused_unconnected`：未用声明、赋值未读、输入未用、输出未驱动、实例输出悬空和 `.out()` 空连接。
- `multiple_driver`：同一信号多源驱动风险。
- `latch_risk`：组合逻辑分支覆盖不完整。
- `style_timing_risk`：长组合表达式早期时序风险。

## 运行

```sh
PATH="$PWD/tools/bin:$PATH" ./sta-lite lint-diff \
  --cases lint/verilog_warning_example \
  --out reports/lint_diff_verilog_warning \
  --iverilog iverilog
```

## 当前状态

当前内置 16 个 Verilog warning case。最近一次完整差分中，本目录没有发现 STA-lite 漏报。

## 限制

- `iverilog -Wall` 不覆盖所有 STA-lite 风险规则，例如 latch 风险和长组合路径主要由 STA-lite metadata 期望驱动。
- warning 级规则是工程启发式，不等价于综合或 STA 结论。
