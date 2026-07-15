#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"
VERSION="$(python3 -c 'from sta_lite import __version__; print(__version__)')"
RELEASE_ROOT="${PROJECT_ROOT}/build/release/ubuntu20"
PAYLOAD_DIR="${RELEASE_ROOT}/payload"
OUTPUT_DIR="${PROJECT_ROOT}/install_package/ubuntu20"
PACKAGE_NAME="STA-Lite-${VERSION}-Ubuntu20+-x86_64"

rm -rf "${RELEASE_ROOT}"
mkdir -p "${PAYLOAD_DIR}" "${OUTPUT_DIR}"
rm -f "${OUTPUT_DIR}"/*.tar.gz "${OUTPUT_DIR}/SHA256SUMS.txt" "${OUTPUT_DIR}/DEPENDENCIES.txt"

DATA_ARGS=(
  --add-data "sta_lite/gui/static:sta_lite/gui/static"
  --add-data "examples:examples"
  --add-data "lint:lint"
  --add-data "risk_profile:risk_profile"
  --add-data "tests:tests"
  --add-data "README.md:."
)

python3 -m PyInstaller --noconfirm --clean --onedir --name STA-Lite \
  --distpath "${PAYLOAD_DIR}" --workpath "${RELEASE_ROOT}/work-desktop" \
  --specpath "${RELEASE_ROOT}" "${DATA_ARGS[@]}" sta-lite-desktop
python3 -m PyInstaller --noconfirm --clean --onedir --name sta-lite-cli \
  --distpath "${PAYLOAD_DIR}" --workpath "${RELEASE_ROOT}/work-cli" \
  --specpath "${RELEASE_ROOT}" "${DATA_ARGS[@]}" sta-lite

"${PAYLOAD_DIR}/sta-lite-cli/sta-lite-cli" --version

PACKAGE_DIR="${RELEASE_ROOT}/${PACKAGE_NAME}"
mkdir -p "${PACKAGE_DIR}"
cp -a "${PAYLOAD_DIR}/STA-Lite" "${PAYLOAD_DIR}/sta-lite-cli" "${PACKAGE_DIR}/"
cp packaging/install_ubuntu.sh THIRD_PARTY_NOTICES.md "${PACKAGE_DIR}/"
chmod +x "${PACKAGE_DIR}/install_ubuntu.sh"

cat > "${PACKAGE_DIR}/DEPENDENCIES.txt" <<EOF
STA-Lite ${VERSION} / Ubuntu 20.04+ x86_64
运行时依赖：无须另装 Python、Yosys 或 OpenSTA。
构建基线：Ubuntu 20.04 glibc，内含 CPython 3.8 运行时与 PyInstaller 6.21.0 冻结依赖。
可选 Backend Analysis：仅在用户主动使用该页面时需要另装 Yosys/OpenSTA 和 Liberty。
EOF

tar -C "${RELEASE_ROOT}" -czf "${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz" "${PACKAGE_NAME}"
(cd "${OUTPUT_DIR}" && sha256sum "${PACKAGE_NAME}.tar.gz" > SHA256SUMS.txt)
cp "${PACKAGE_DIR}/DEPENDENCIES.txt" "${OUTPUT_DIR}/DEPENDENCIES.txt"
echo "[sta-lite] 已生成 ${OUTPUT_DIR}/${PACKAGE_NAME}.tar.gz"
