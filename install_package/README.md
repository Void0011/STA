# STA-Lite 安装包

稳定版本：`v0.2.0`。

- `window10/`：Windows 10 x64 安装器、依赖说明和 SHA-256 校验文件。
- `window11/`：Windows 11 x64 安装器、依赖说明和 SHA-256 校验文件。
- `ubuntu20/`：Ubuntu 20.04+ x86_64 自包含压缩包、安装脚本和 SHA-256 校验文件。

仓库保留目录、构建说明和发布流程；真正的二进制由对应操作系统上的 GitHub Actions 生成，并作为 GitHub Release Assets 发布。Windows EXE 不能由 Linux 交叉生成，否则无法形成可信的 Windows 发布验证。

详细构建、验证和发布方法见 [`docs/RELEASE_GUIDE.md`](../docs/RELEASE_GUIDE.md)。
