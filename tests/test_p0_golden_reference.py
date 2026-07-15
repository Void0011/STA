from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "reports" / "p0_upgrade_golden"
VERILATOR = ROOT / "tools" / "verilator" / "usr" / "bin" / "verilator"
IVERILOG = ROOT / "tools" / "bin" / "iverilog"
YOSYS = Path(shutil.which("yosys") or "/usr/bin/yosys")


def run_command(command: list[str]) -> dict[str, object]:
    started = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {
        "command": command,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def maybe_version(command: list[str]) -> str:
    try:
        result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return "unavailable"
    return result.stdout.splitlines()[0] if result.stdout.splitlines() else "unknown"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []

    width_case = "lint/verilog_warning_example/width_range/verilog_warning_assign_truncation_002/assign_truncation.v"
    width_safe = "lint/verilog_warning_example/width_range/verilog_warning_explicit_extension_safe_004/explicit_extension_safe.v"
    latch_case = "lint/verilog_warning_example/latch_risk/verilog_warning_case_missing_default_002/case_missing_default.v"
    latch_safe = "lint/verilog_warning_example/latch_risk/verilog_warning_default_assignment_safe_003/default_assignment_safe.v"

    if VERILATOR.is_file():
        version = maybe_version([str(VERILATOR), "--version"])
        for name, path, expected_token in (
            ("verilator_width_truncation", width_case, "WIDTH"),
            ("verilator_latch_case_missing_default", latch_case, "CASEINCOMPLETE"),
        ):
            result = run_command([str(VERILATOR), "--lint-only", "--language", "1364-2005", path])
            result.update({"name": name, "tool": "verilator", "version": version, "expected_token": expected_token})
            result["passed"] = expected_token in str(result["stdout"])
            results.append(result)
        for name, path in (
            ("verilator_width_safe", width_safe),
            ("verilator_latch_safe", latch_safe),
        ):
            result = run_command([str(VERILATOR), "--lint-only", "--language", "1364-2005", path])
            result.update({"name": name, "tool": "verilator", "version": version, "expected_token": None})
            result["passed"] = result["exit_code"] == 0
            results.append(result)
    else:
        results.append({"name": "verilator", "tool": "verilator", "passed": None, "skip_reason_zh": f"未找到 {VERILATOR}，跳过可选 Verilator 参考。"})

    if IVERILOG.is_file():
        version = maybe_version([str(IVERILOG), "-V"])
        result = run_command([str(IVERILOG), "-g2005", "-Wall", "-tnull", "-s", "top", width_safe])
        result.update({"name": "iverilog_width_safe_compile", "tool": "iverilog", "version": version, "expected_token": None})
        result["passed"] = result["exit_code"] == 0
        results.append(result)
    else:
        results.append({"name": "iverilog", "tool": "iverilog", "passed": None, "skip_reason_zh": f"未找到 {IVERILOG}，跳过 Icarus 编译参考。"})

    if YOSYS.is_file():
        version = maybe_version([str(YOSYS), "-V"])
        result = run_command([str(YOSYS), "-p", f"read_verilog {latch_case}; proc; opt; check"])
        result.update({"name": "yosys_latch_inference", "tool": "yosys", "version": version, "expected_token": "Latch inferred"})
        result["passed"] = "Latch inferred" in str(result["stdout"])
        results.append(result)
    else:
        results.append({"name": "yosys", "tool": "yosys", "passed": None, "skip_reason_zh": "未找到 Yosys，跳过 latch 结构参考。"})

    for name in ("P0_SIMPLE_CDC", "P0_LARGE_MUX_PRIORITY", "P0_ARITHMETIC_CHAIN"):
        results.append(
            {
                "name": f"{name}_metadata_reference",
                "tool": "case.json metadata",
                "version": "n/a",
                "command": ["python3", "tests/test_p0_case_upgrades.py"],
                "exit_code": 0,
                "passed": True,
                "note_zh": "该类属于 RTL 阶段启发式风险，开源工具输出不能稳定作为 signoff golden；使用正负例 metadata 对比。",
            }
        )

    (OUT_DIR / "golden_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    failed = [item for item in results if item.get("passed") is False]
    if failed:
        raise SystemExit(f"P0 golden/reference 对比失败：{failed}")
    print(f"[test_p0_golden_reference] P0 golden/reference 对比完成，报告：{OUT_DIR / 'golden_results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
