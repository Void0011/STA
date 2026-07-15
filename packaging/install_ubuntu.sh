#!/usr/bin/env bash
set -euo pipefail

PACKAGE_ROOT="$(cd "$(dirname "$0")" && pwd)"
INSTALL_ROOT="${HOME}/.local/opt/sta-lite"
BIN_ROOT="${HOME}/.local/bin"

mkdir -p "${INSTALL_ROOT}" "${BIN_ROOT}"
cp -a "${PACKAGE_ROOT}/STA-Lite" "${PACKAGE_ROOT}/sta-lite-cli" "${INSTALL_ROOT}/"
ln -sfn "${INSTALL_ROOT}/sta-lite-cli/sta-lite-cli" "${BIN_ROOT}/sta-lite"
ln -sfn "${INSTALL_ROOT}/STA-Lite/STA-Lite" "${BIN_ROOT}/sta-lite-gui"

echo "[sta-lite] 安装完成。"
echo "[sta-lite] GUI：${BIN_ROOT}/sta-lite-gui"
echo "[sta-lite] CLI：${BIN_ROOT}/sta-lite"
echo "[sta-lite] 如果命令不可见，请把 ${BIN_ROOT} 加入 PATH。"
