# Windows 10 x64 发布包

GitHub Actions 构建完成后，本目录对应的 artifact 包含：

- `STA-Lite-0.2.0-Windows10-x64-Setup.exe`
- `DEPENDENCIES.txt`
- `SHA256SUMS.txt`

安装器为当前用户安装，无须管理员权限。STA-Lite GUI、Python 运行时和 RTL Review 所需资源均已内置；不需要安装 Yosys、OpenSTA 或其他 EDA 软件。Windows 10 真机认证需要带 `win10` 标签的自托管测试机，当前托管构建机仅完成 Windows Server 2022 构建与 HTTP smoke test。
