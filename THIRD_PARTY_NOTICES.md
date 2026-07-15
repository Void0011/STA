# 第三方组件声明

STA-Lite 的 RTL Review、RTL Lint 和 RTL Timing Risk Profiling 运行时只使用 Python 标准库。二进制发行包通过以下组件生成或携带其运行时：

- CPython：Python Software Foundation License Version 2。发行包携带与构建平台匹配的 CPython 运行时；许可证见 [Python 官方许可页](https://docs.python.org/3/license.html)。
- PyInstaller 6.21.0：GPL-2.0-or-later，并带有允许分发闭源或开源冻结应用的 Bootloader Exception；详情见 [PyInstaller COPYING](https://github.com/pyinstaller/pyinstaller/blob/v6.21.0/COPYING.txt)。
- NSIS：仅用于生成 Windows 安装器；其许可证允许商业和非商业使用，详情见 [NSIS License](https://nsis.sourceforge.io/Docs/AppendixI.html)。

Windows 和 Ubuntu 安装包不包含仓库 `tools/` 下的 EDA 二进制，也不包含 `nangate45/` 下的 Liberty 文件。Yosys、OpenSTA 与 Liberty 只属于可选 Backend Analysis 工作流，用户应按各自许可单独安装和提供。

本文件不替代各组件随附的完整许可证。正式对外发行前，项目所有者仍需确定 STA-Lite 自身采用的许可证。
