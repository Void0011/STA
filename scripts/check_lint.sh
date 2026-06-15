#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"

echo "[check_lint] 检查 Python 语法。"
python3 -m py_compile \
  sta-lite \
  sta_lite/cli.py \
  sta_lite/models/diagnostic.py \
  sta_lite/lint/*.py \
  tests/test_lint_engine.py \
  tests/test_lint_iverilog_gold.py

echo "[check_lint] 运行内部 lint 示例回归。"
python3 tests/test_lint_engine.py

echo "[check_lint] 运行 iverilog gold 对比回归。"
python3 tests/test_lint_iverilog_gold.py

echo "[check_lint] lint 回归检查通过。"
