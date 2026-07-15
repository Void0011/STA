#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"

echo "[check_risk] 检查 Python 语法。"
python3 -m py_compile \
  sta-lite \
  sta_lite/cli.py \
  sta_lite/gui/server.py \
  sta_lite/review/*.py \
  sta_lite/risk/*.py \
  tests/test_case_registry.py \
  tests/test_p0_case_upgrades.py \
  tests/test_p0_golden_reference.py \
  tests/test_p0_remaining_cases.py \
  tests/test_p0_yosys_reference.py \
  tests/test_p1_case_upgrades.py \
  tests/test_p1_golden_reference.py \
  tests/test_long_task_coverage.py \
  tests/test_long_task_golden_reference.py \
  tests/test_standalone_core.py \
  tests/test_review_workflow.py \
  tests/test_risk_profile.py \
  tests/review_gui_api_smoke.py \
  tests/risk_gui_api_smoke.py

echo "[check_risk] 运行 RTL 时序风险 smoke 回归。"
python3 tests/test_risk_profile.py

echo "[check_risk] 运行 P0/P1 Case Coverage 注册表回归。"
python3 tests/test_case_registry.py

echo "[check_risk] 运行 P0 partial 升级项正负例回归。"
python3 tests/test_p0_case_upgrades.py

echo "[check_risk] 运行 4 个 P1 Case 正负例、Review 聚合与可选 golden/reference 回归。"
python3 tests/test_p1_case_upgrades.py
python3 tests/test_p1_golden_reference.py

echo "[check_risk] 运行剩余 P0/P1 覆盖、golden metadata、独立核心与中文基线回归。"
python3 tests/test_long_task_coverage.py
python3 tests/test_long_task_golden_reference.py
python3 tests/test_standalone_core.py
python3 scripts/generate_coverage_baseline.py --check

echo "[check_risk] 运行 P0 golden/reference 对比回归。"
python3 tests/test_p0_golden_reference.py

echo "[check_risk] 运行剩余 P0 组合环路/FSM 正负例回归。"
python3 tests/test_p0_remaining_cases.py

echo "[check_risk] 运行剩余 P0 Yosys reference 回归。"
python3 tests/test_p0_yosys_reference.py

echo "[check_risk] 运行 RTL Review 并集与失败隔离回归。"
python3 tests/test_review_workflow.py

echo "[check_risk] 运行 GUI Risk API smoke 回归。"
python3 tests/risk_gui_api_smoke.py

echo "[check_risk] 运行 GUI RTL Review API smoke 回归。"
python3 tests/review_gui_api_smoke.py

echo "[check_risk] risk 回归检查通过。"
