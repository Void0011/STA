# 门控或派生时钟

该 case 使用 `clk & enable` 生成 `gated_clk` 并驱动触发器。普通 RTL 逻辑生成的时钟可能带来毛刺、skew、约束缺失和 clock tree 不可控问题。
