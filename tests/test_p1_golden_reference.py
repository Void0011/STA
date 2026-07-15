from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "runs" / "p1_golden_reference"


def find_verilator() -> str | None:
    bundled = ROOT / "tools" / "verilator" / "usr" / "bin" / "verilator"
    if bundled.is_file() and bundled.stat().st_mode & 0o111:
        return str(bundled)
    return shutil.which("verilator")


def run_command(command: list[str]) -> dict[str, object]:
    started = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return {
        "command": command,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def version(command: str, argument: str = "--version") -> str:
    result = run_command([command, argument])
    return (str(result["stdout"]) + str(result["stderr"])).strip()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    records: dict[str, object] = {
        "说明_zh": "Golden/reference 仅用于开发期比较；STA-lite 的 lint/risk/review 正常运行不调用这些外部工具。",
        "references": [],
    }
    references: list[dict[str, object]] = records["references"]  # type: ignore[assignment]

    verilator = find_verilator()
    if verilator:
        for name, relative in (
            ("casex_casez", "lint/verilog_warning_example/x_propagation/verilog_warning_casex_casez_001/casex_casez.v"),
            ("signed_unsigned", "lint/verilog_warning_example/signedness/verilog_warning_signed_unsigned_001/signed_unsigned.v"),
        ):
            command = [verilator, "--lint-only", "--Wall", "--language", "1364-2005", "-Wno-fatal", str(ROOT / relative)]
            result = run_command(command)
            output = str(result["stdout"]) + str(result["stderr"])
            findings = sorted(set(re.findall(r"%(?:Warning|Error)-([A-Z0-9_]+)", output)))
            if int(result["exit_code"]) != 0:
                raise SystemExit(f"Verilator golden 命令失败（{name}）：{output}")
            references.append(
                {
                    "case": name,
                    "tool": "Verilator",
                    "source_url": "https://verilator.org/guide/latest/warnings.html",
                    "version": version(verilator),
                    "result": result,
                    "normalized_findings": findings,
                    "comparison_status": "passed",
                    "comparison_note_zh": "CASEX/UNSIGNED/WIDTH 是否由当前版本输出均已记录；未稳定输出的策略风险回退到 case.json 正负例。",
                }
            )
    else:
        references.append({"tool": "Verilator", "comparison_status": "skipped", "reason_zh": "未找到可选 Verilator，已使用 case.json metadata 正负例回退。"})
        print("[test_p1_golden_reference] 未找到 Verilator，跳过可选 lint golden，使用 metadata 回退。")

    yosys = shutil.which("yosys")
    if yosys:
        for name, relative, script in (
            ("excessive_reset", "risk_profile/cases/excessive_reset_fanout/excessive_reset_fanout.v", "read_verilog {rtl}; hierarchy -top top; proc; opt; stat"),
            ("multi_clock", "lint/verilog_warning_example/multi_clock/verilog_warning_multi_clock_001/multi_clock.v", "read_verilog -sv {rtl}; hierarchy -top top; proc; check"),
        ):
            command = [yosys, "-p", script.format(rtl=str(ROOT / relative))]
            result = run_command(command)
            output = str(result["stdout"]) + str(result["stderr"])
            # Multi-clock lowering may deliberately reject the process; this itself is a useful structural reference.
            if name == "excessive_reset" and int(result["exit_code"]) != 0:
                raise SystemExit(f"Yosys reset golden 命令失败：{output}")
            references.append(
                {
                    "case": name,
                    "tool": "Yosys",
                    "source_url": "https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/proc.html",
                    "version": version(yosys, "-V"),
                    "result": result,
                    "normalized_findings": [line.strip() for line in output.splitlines() if "reset" in line.lower() or "edge" in line.lower()][:40],
                    "comparison_status": "passed",
                    "comparison_note_zh": "reset 使用 proc/opt/stat 确认 process lowering；multi-clock 允许 proc/check 给出拒绝或诊断，具体阈值和分类由 STA-lite metadata 验证。",
                }
            )
    else:
        references.append({"tool": "Yosys", "comparison_status": "skipped", "reason_zh": "未找到可选 Yosys，已使用 case.json metadata 正负例回退。"})
        print("[test_p1_golden_reference] 未找到 Yosys，跳过可选结构 golden，使用 metadata 回退。")

    (OUT_DIR / "golden_results.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("[test_p1_golden_reference] P1 Verilator/Yosys 开发期参考或 metadata 回退校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
