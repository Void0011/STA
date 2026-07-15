# Verilog Warning 语料

本目录保存 Verilog warning/lint-like 语料。部分 warning 可由 `iverilog -Wall` 作为 golden 观察，部分属于 STA-lite 内部早期风险规则。

## 用途

- 覆盖隐式网线、端口连接、位宽/越界、timescale、未使用/未连接、多驱动、latch 风险、可综合性、复杂 generate、参数位宽、`casex/casez` X 传播、多时钟 always、signed/unsigned 混合和长组合路径风险。
- 分离 warning 与 error 语料，避免 warning 样例污染语法错误覆盖率。
- 继续运行 Verilog iverilog golden，但允许部分 STA-lite 产品规则使用 metadata 期望。

## 当前类别

- `implicit_net`：未声明信号形成隐式 wire。
- `port_connection`：子模块输入端口悬空。
- `width_range`：端口位宽不匹配、赋值截断/扩展、常量 select 越界和显式扩展负例。
- `timescale`：缺失或继承 timescale。
- `unused_unconnected`：未用声明、赋值未读、输入未用、输出未驱动、实例输出悬空和 `.out()` 空连接。
- `multiple_driver`：同一信号多源驱动风险。
- `latch_risk`：组合逻辑分支覆盖不完整、case 缺 default 和显式 default 负例。
- `style_timing_risk`：长组合表达式早期时序风险。
- `x_propagation`：`casex` 以及带 `?`/`z` 通配项的 `casez` 风险；普通 `case` 和显式掩码比较为负例。
- `signedness`：具名 signed/unsigned 信号的算术、比较、移位、三目和赋值隐式转换；显式 `$signed/$unsigned` 为负例。
- `multi_clock`：一个过程块中出现两个独立时钟边沿；标准单时钟加异步 reset 为负例。
- `synthesizability`：`initial`、常量延时和仿真系统任务；普通时序寄存器为负例。
- `generate_elaboration`：参数相关循环/条件 generate；简单无分支 generate 为负例。
- `parameter_width`：常见整数参数派生范围的负下标/异常宽度；合法 `WIDTH=8` 为负例。

## 运行

```sh
PATH="$PWD/tools/bin:$PATH" ./sta-lite lint-diff \
  --cases lint/verilog_warning_example \
  --out reports/lint_diff_verilog_warning \
  --iverilog iverilog
```

## 当前状态

当前内置 32 个 Verilog warning case。最近一次完整差分中，本目录没有发现 STA-lite 漏报。

## 限制

- `iverilog -Wall` 不覆盖所有 STA-lite 风险规则，例如 assignment 位宽、latch 风险和长组合路径主要由 STA-lite metadata 或 Verilator/Yosys 开发期参考驱动。
- warning 级规则是工程启发式，不等价于综合或 STA 结论。
