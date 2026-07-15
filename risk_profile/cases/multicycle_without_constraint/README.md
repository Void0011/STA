# 多周期行为缺少约束

该 case 通过计数器延后更新结果，命名中包含 `slow`。如果设计意图依赖多周期路径，需要在 SDC 中明确 `set_multicycle_path` 并验证 hold 侧约束。
