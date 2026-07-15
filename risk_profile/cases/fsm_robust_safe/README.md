# fsm_robust_safe

该用例是 FSM 负例：状态寄存器有 reset，组合 next-state 有默认赋值、完整 case 和安全 default。STA-lite 不应报告 `RISK_FSM_ROBUSTNESS`。
