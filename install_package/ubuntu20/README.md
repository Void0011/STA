# Ubuntu 20.04+ x86_64 发布包

GitHub Actions 在 Ubuntu 20.04 容器中构建以下文件：

- `STA-Lite-0.2.0-Ubuntu20+-x86_64.tar.gz`
- `DEPENDENCIES.txt`
- `SHA256SUMS.txt`

解压后运行 `./install_ubuntu.sh`，程序安装到 `~/.local/opt/sta-lite`，命令链接放到 `~/.local/bin`。使用 Ubuntu 20.04 作为构建基线是为了保证 glibc 对 Ubuntu 20.04 及更新版本的向前兼容。
