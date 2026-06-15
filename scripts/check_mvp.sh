#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out_dir="$root_dir/runs/check_counter"
summary="$out_dir/summary.json"
cli_log="$out_dir/check_mvp_analyze.log"
multi_out_dir="$root_dir/runs/check_multi_file"
multi_summary="$multi_out_dir/summary.json"
multi_cli_log="$multi_out_dir/check_mvp_analyze.log"

cd "$root_dir"

echo "[check_mvp] 检查 Python 语法。"
python3 -m py_compile sta-lite sta_lite/cli.py sta_lite/core/runner.py sta_lite/parsers/reports.py sta_lite/gui/server.py tests/gui_api_smoke.py

echo "[check_mvp] 运行 counter 端到端示例。"
mkdir -p "$out_dir"
if ! ./sta-lite analyze \
  --top counter \
  --rtl examples/counter/counter.v \
  --clock clk \
  --period 2.0 \
  --lib nangate45/lib/NangateOpenCellLibrary_typical.lib \
  --out "$out_dir" > "$cli_log" 2>&1; then
  echo "[check_mvp] counter 示例运行失败，最近日志如下："
  tail -n 80 "$cli_log"
  exit 1
fi
echo "[check_mvp] counter 示例运行完成，完整日志：$cli_log"

echo "[check_mvp] 校验 summary.json 关键字段。"
python3 - "$summary" <<'PY'
import json
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
data = json.loads(summary_path.read_text(encoding="utf-8"))
required = [
    "top",
    "rtl_files",
    "liberty_file",
    "sdc_file",
    "generated_netlist",
    "wns",
    "tns",
    "worst_paths",
    "yosys_warnings",
    "opensta_warnings",
    "risk_level",
    "risk_explanation_zh",
    "elapsed_seconds",
    "timing_violations",
]
missing = [key for key in required if key not in data]
if missing:
    raise SystemExit("summary.json 缺少字段：" + ", ".join(missing))
if data["top"] != "counter":
    raise SystemExit("summary.json top 字段不正确")
if data["risk_level"] not in {"LOW", "MEDIUM", "HIGH"}:
    raise SystemExit("summary.json risk_level 字段不合法")
if not data["worst_paths"]:
    raise SystemExit("summary.json 没有解析到 worst_paths")
print("[check_mvp] summary.json 校验通过。")
PY

echo "[check_mvp] 运行 multi_file 多 RTL 端到端示例。"
mkdir -p "$multi_out_dir"
if ! ./sta-lite analyze \
  --top multi_top \
  --rtl 'examples/multi_file/rtl/*.v' \
  --clock clk \
  --period 2.5 \
  --lib nangate45/lib/NangateOpenCellLibrary_typical.lib \
  --out "$multi_out_dir" > "$multi_cli_log" 2>&1; then
  echo "[check_mvp] multi_file 示例运行失败，最近日志如下："
  tail -n 80 "$multi_cli_log"
  exit 1
fi
python3 - "$multi_summary" <<'PY'
import json
import sys
from pathlib import Path

summary_path = Path(sys.argv[1])
data = json.loads(summary_path.read_text(encoding="utf-8"))
if data["top"] != "multi_top":
    raise SystemExit("multi_file summary top 字段不正确")
if len(data["rtl_files"]) < 4:
    raise SystemExit("multi_file 没有记录多个 RTL 文件")
if not data["worst_paths"]:
    raise SystemExit("multi_file 没有解析到 worst_paths")
print("[check_mvp] multi_file 多 RTL 示例校验通过。")
PY

echo "[check_mvp] 运行 GUI API smoke 测试。"
python3 tests/gui_api_smoke.py

echo "[check_mvp] MVP 回归检查通过：$summary"
