# 两级同步器安全例

该 case 中 `pulse_a` 从 `clk_a` 域进入 `clk_b` 域，但目标时钟域中存在 `pulse_meta` 和 `pulse_sync` 两级采样。STA-lite 的简单 CDC 规则应识别该同步结构并避免报告 `RISK_CDC_UNSYNC_SIGNAL`。

该检查仍然不是 signoff CDC，只用于降低明显两级同步器场景的误报。
