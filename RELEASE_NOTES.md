# STA-Lite v0.2.0

这是 STA-Lite 首个稳定安装发行版本。

主要能力：

- 五页 GUI：RTL Review、RTL Lint、RTL Timing Risk Profiling、Yosys/OpenSTA Backend Analysis、Case Coverage。
- RTL Review 复用内部 Lint 与 Risk workflow，不依赖 Yosys、OpenSTA 或其他 EDA 软件。
- P0/P1 RTL 风险用例、中文诊断、结构化 JSON/Markdown 报告和回归证据。
- Windows 10/11 x64 当前用户级安装器；内置 Python 运行时，双击即可启动并自动打开浏览器。
- Ubuntu 20.04+ x86_64 自包含发行包与用户级安装脚本。
- 冻结程序 HTTP smoke test、SHA-256 校验与可复现 GitHub Actions 发布流程。

边界说明：STA-Lite 提供 RTL 阶段早期风险预警，不是 signoff STA。Backend Analysis 仍是可选参考能力，只有使用该页面时才需要用户自行安装 Yosys/OpenSTA 并提供 Liberty。

兼容性说明：Windows 安装器由 GitHub `windows-2022` runner 构建并执行冻结程序 smoke test；Windows 10/11 严格真机认证仍需要相应自托管 runner。Ubuntu 包在 Ubuntu 20.04 容器构建，以兼容 Ubuntu 20.04 及更新版本。
