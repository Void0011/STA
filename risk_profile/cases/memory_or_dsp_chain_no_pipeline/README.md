# Memory/DSP 后级无流水

该 case 让 `mem` 读数据和乘法结果继续进入组合加法、移位和选择。真实 FPGA/ASIC 设计中，RAM/DSP 输出寄存和后级流水常是 timing closure 的关键。
