# Verilog Error 语料

本目录保存 Verilog 错误级语料，目标是向 IEEE 1364 实用合规覆盖靠近。每个 case 都应尽量“小而单一”，用于驱动 STA-lite 内部 parser/rule 能力补齐。

## 用途

- 覆盖常见 Verilog 语法和编译期错误。
- 使用 `iverilog -g2005 -Wall -tnull -s <top> <files>` 作为开发期 golden。
- 对比 STA-lite 是否能用内部 lint 引擎检出同类问题。

`iverilog` 不会被产品 lint 调用，只用于回归参考；不要运行 `vvp`。

## 当前类别

- `lexical`：字符串、块注释等词法/预处理边界。
- `syntax`：分号、逗号、括号、`begin/end`、`endmodule`、非法 token。
- `declaration`：重复声明、非法 net/reg 组合、parameter 空 RHS、range 错误、关键字标识符。
- `module_port`：模块头、端口方向、重复端口、非 ANSI 端口声明、端口重声明。
- `expression`：数字常量、拼接、三目、缺操作数、part-select。
- `assignment`：连续赋值/过程赋值 RHS、非法 lvalue、wire 过程赋值、混合驱动。
- `procedural_block`：always 事件控制、if/else、case/endcase、非阻塞赋值拼写。
- `preprocessor`：include、macro、ifdef/endif、未定义宏。
- `instantiation`：实例名、命名连接、位置/命名混用、未定义模块。
- `generate`：generate/endgenerate 结构。
- `function_task`：function/task 结构。
- `specify_udp`：specify/UDP/table 识别或 unsupported。

## 运行

```sh
PATH="$PWD/tools/bin:$PATH" ./sta-lite lint-diff \
  --cases lint/verilog_error_example \
  --out reports/lint_diff_verilog_error \
  --iverilog iverilog
```

## 当前状态

当前内置 74 个 Verilog error case。最近一次完整差分中，本目录没有发现 STA-lite 漏报。

## 限制

- 该语料还不是完整 IEEE 1364 conformance suite。
- generate、function/task 当前已有语法级结构化识别，尚未做完整 elaboration。
- specify、UDP 当前主要以结构错误或 `UNSUPPORTED_VERILOG` 显式诊断覆盖，尚未实现完整语义。
