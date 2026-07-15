# P0_FSM_ROBUSTNESS 第一版设计说明

## 定位

`RISK_FSM_ROBUSTNESS` 是 STA-lite 的 RTL-only 启发式检查，用于在 RTL Review / RTL Timing Risk Profiling 阶段提前提示常见 FSM 鲁棒性风险。它不是 formal FSM verification，也不证明状态可达性、死锁自由或完整 SystemVerilog 类型语义。

## 状态寄存器识别

第一版只支持清晰两进程 FSM：

- 时序 `always @(posedge clk ...)` 或 `always_ff` 中给 `state`、`current_state`、`curr_state` 等状态名赋值。
- 状态寄存器 RHS 读取 `next_state` 风格信号。
- 组合 `always @(*)` 或 `always_comb` 中给 `next_state` 赋值。
- 组合块中存在 `case (state)` / `case (current_state)` 转移逻辑。

当前状态集合主要来自 `parameter` / `localparam` 声明，并结合 case label 和 state/next_state 表达式做轻量过滤。

## 已检查问题

第一版会在证据明确时报告：

- `missing_reset`：状态寄存器没有 reset/default 初始化。
- `missing_case_default`：转移 `case` 缺少 `default`。
- `unsafe_default_recovery`：`default` 没有恢复到 reset/IDLE 等已知安全状态，或保持当前状态。
- `incomplete_next_state_assignment`：组合 next-state 逻辑可能有未赋值路径，容易推断 latch。
- `declared_state_not_handled`：已声明状态未在转移 `case` 中显式处理。
- `obvious_terminal_state`：某个状态只看到无条件自环，可能是终止/死状态。

## 明确不覆盖

当前不声称覆盖：

- one-process FSM 或复杂 mixed-process FSM。
- package/import/enum 类型的完整 elaboration 和类型推导。
- generate 展开的 FSM、参数化状态空间和跨模块状态封装。
- formal reachability、死锁证明、互斥/完整性证明。
- 综合后重编码、物理时序、CDC/RDC signoff 语义。

遇到复杂 FSM 时，第一版倾向于不报 FSM 鲁棒性诊断，避免在证据不足时误导用户。

## 误报与漏报风险

- 误报风险：有意设计的错误锁存/终止状态可能被提示为 `obvious_terminal_state`；后续需要 waiver 或设计意图注解。
- 漏报风险：one-process FSM、状态名不含 `state`、状态通过函数/任务/generate/复杂 typedef enum 生成时，第一版可能无法识别。
- 状态覆盖只按当前 AST token 做局部判断，不做参数常量折叠或完整类型 elaboration。

## 开发期 reference

Yosys 只作为开发期参考，不是 STA-lite 生产运行依赖。

用于确认 FSM 可抽取的命令：

```sh
yosys -p "read_verilog -sv <files>; hierarchy -top <top>; proc; opt; fsm_detect; fsm_extract; fsm_info"
```

Yosys `fsm_detect` / `fsm_extract` 可以确认常见 state register 和 transition table；但缺 reset、default 恢复是否安全、声明状态未处理等鲁棒性 warning 并不是 Yosys 的完整 golden。因此 STA-lite 对这些 warning 使用 `risk_profile/cases/*/case.json` metadata 正负例做回归对比。

对应回归：

```sh
python3 tests/test_p0_remaining_cases.py
python3 tests/test_p0_yosys_reference.py
```
