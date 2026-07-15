# CDC 未同步信号

该 case 中 `pulse_a` 从 `clk_a` 域直接进入 `clk_b` 域。该规则只是早期提示，不替代 CDC signoff；真实项目应使用两级同步器、握手或异步 FIFO。
