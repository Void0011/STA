# 多位 CDC 未同步信号

该 case 中 `data_a` 是 8 bit 总线，在 `clk_a` 域更新后被 `clk_b` 域直接采样。STA-lite 应报告 `RISK_CDC_UNSYNC_SIGNAL`，并在 evidence 中记录 `signal_width`。

多位跨域通常需要握手、异步 FIFO 或协议级保证；本规则只是早期 RTL 风险提示。
