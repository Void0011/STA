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
  tests/test_lint_iverilog_gold.py \
  tests/test_p1_case_upgrades.py \
  tests/test_p1_golden_reference.py \
  tests/test_long_task_coverage.py \
  tests/test_long_task_golden_reference.py \
  tests/test_standalone_core.py

echo "[check_lint] 运行内部 lint 示例回归。"
python3 tests/test_lint_engine.py

echo "[check_lint] 运行 iverilog gold 对比回归。"
python3 tests/test_lint_iverilog_gold.py

echo "[check_lint] 运行 P1 lint 规则与可选 golden/reference 回归。"
python3 tests/test_p1_case_upgrades.py
python3 tests/test_p1_golden_reference.py

echo "[check_lint] 运行长期覆盖新增规则、基线与无外部工具核心回归。"
python3 tests/test_long_task_coverage.py
python3 tests/test_long_task_golden_reference.py
python3 tests/test_standalone_core.py
python3 scripts/generate_coverage_baseline.py --check

echo "[check_lint] lint 回归检查通过。"
