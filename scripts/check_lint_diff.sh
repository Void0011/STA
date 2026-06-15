#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"

export PATH="$root_dir/tools/bin:$PATH"

echo "[check_lint_diff] 生成并运行 Verilog/SystemVerilog lint 差分语料。"
python3 -m sta_lite.lint.diff_runner \
  --write-corpus \
  --out reports/lint_diff \
  --iverilog iverilog

echo "[check_lint_diff] 差分报告已生成：reports/lint_diff"
