# Latch 时序风险

该 case 的组合逻辑在 `sel=0` 时没有给 `y` 赋值，综合可能推断 latch。Latch 会引入透明窗口、复杂时序路径和不易定位的 timing/debug 问题。
