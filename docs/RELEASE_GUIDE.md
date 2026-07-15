# STA-Lite 稳定版本发布指南

## 发布边界

当前稳定版本为 `v0.2.0`。Windows 与 Ubuntu 安装包内置 Python 运行时、GUI 静态资源、RTL Review/Lint/Risk 引擎、示例和 Case Coverage 证据，不包含 `tools/`、`nangate45/`，也不要求安装任何 EDA 软件。

只有用户主动使用 `Yosys/OpenSTA Backend Analysis` 页面时，才需要自行提供 Yosys、OpenSTA、Liberty 与约束文件。该可选页面不影响其余四页。

## Windows 10 / Windows 11

PyInstaller 不是跨编译器，可信的 Windows EXE 必须在 Windows 上构建。仓库的 `.github/workflows/release.yml` 使用 `windows-2022` x64 构建机，执行以下流程：

1. 使用固定版本 PyInstaller 生成目录模式的 `STA-Lite.exe` 与 `sta-lite-cli.exe`。
2. 启动冻结后的 GUI，访问 `/api/case_coverage` 做 HTTP smoke test。
3. 使用 NSIS 生成当前用户级单文件 Setup EXE。
4. 分别输出到 `install_package/window10/` 和 `install_package/window11/`。
5. 生成 `DEPENDENCIES.txt` 与 `SHA256SUMS.txt`。

两个目标使用相同的 STA-Lite 源码与 x64 Python 运行时，安装器名称分别标识 Windows 10 和 Windows 11。GitHub 托管 runner 是 Windows Server 2022，因此这里只能声明构建和通用 Windows API 兼容性；严格的 Windows 10/11 真机认证应另配带 `win10`、`win11` 标签的自托管 runner。

在 Windows 构建机手工复现：

```powershell
python -m pip install -r packaging/requirements-build.txt
choco install nsis --no-progress -y
./packaging/build_windows.ps1 -Target window10
./packaging/build_windows.ps1 -Target window11
```

安装后快捷方式启动桌面 GUI，并自动打开浏览器。首次运行会在 `%USERPROFILE%\Documents\STA-Lite-Workspace` 创建可写工作区；卸载程序不会删除用户的 RTL、报告或 `runs/`。

## Ubuntu 20.04+

PyInstaller 不打包 glibc，因此 Linux 包必须在需要支持的最老系统上构建。发布 workflow 使用 Ubuntu 20.04 容器生成 `install_package/ubuntu20/STA-Lite-0.2.0-Ubuntu20+-x86_64.tar.gz`。

解压后执行：

```sh
./install_ubuntu.sh
sta-lite-gui
```

程序安装到 `~/.local/opt/sta-lite`，命令链接放在 `~/.local/bin`，不需要 root 权限。

## 稳定发布检查

发布标签前必须完成：

```sh
./scripts/check_lint.sh
./scripts/check_risk.sh
python3 -m unittest -v tests.test_packaging_release
git diff --check
```

然后提交全部预期改动并创建 annotated tag：

```sh
git tag -a v0.2.0 -m "STA-Lite v0.2.0 stable"
git push origin main
git push origin v0.2.0
```

标签会触发 Windows、Ubuntu 构建和 GitHub Release。Release 任务只在所有回归、冻结程序 smoke test和安装包构建均通过后上传 EXE、Ubuntu 压缩包与统一 SHA-256 文件。

## 合规说明

二进制发行的第三方运行时声明见 [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md)。仓库历史已包含外部 EDA 工具与 Liberty 数据；项目所有者在公开源码归档前应单独确认这些历史资产的再分发授权。无论源码仓库采取何种策略，本发布流程都明确排除这些资产，不把它们带入 STA-Lite 安装包。
