# 标准异步复位负例

该用例是单时钟加异步 reset 的常见结构，用于确认 `RISK_ASYNC_DATA_CONTROL` 不会把明确的 reset 当成普通异步控制；复位释放同步风险由独立规则负责。
