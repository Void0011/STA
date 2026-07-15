# comb_loop_seq_feedback_safe

该用例验证寄存器边界会切断组合依赖图。`q <= q ^ d` 是时序反馈，STA-lite 不应报告组合环路。
