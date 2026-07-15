# fsm_incomplete_next_assign

该用例没有在组合块入口给 `next_state` 默认赋值，且 `if (start)` 缺少 else。STA-lite 应提示可能推断 latch。
