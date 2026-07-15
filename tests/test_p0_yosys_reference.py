from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "p0_remaining_yosys"


def run_cmd(cmd: list[str]) -> dict[str, object]:
    started = time.monotonic()
    result = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {
        "command": cmd,
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }


def has_scc(text: str) -> bool:
    if "Found 0 SCCs" in text:
        return False
    return "Found an SCC" in text or "found logic loop" in text or bool(re.search(r"Found [1-9][0-9]* SCCs", text))


def main() -> int:
    yosys = shutil.which("yosys")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "tool": "Yosys",
        "available": bool(yosys),
        "note_zh": "Yosys 仅作为开发期 reference；STA-lite 正常 risk/review 运行不依赖 Yosys。",
        "results": [],
    }
    if not yosys:
        report["status"] = "skipped"
        report["skip_reason_zh"] = "本机 PATH 中没有 yosys，已跳过开发期 golden/reference。"
        (REPORT_DIR / "yosys_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("[test_p0_yosys_reference] 未找到 yosys，已按可选 reference 规则跳过。")
        return 0

    version = run_cmd([yosys, "-V"])
    report["version"] = (str(version["stdout"]) + str(version["stderr"])).strip()

    checks = [
        {
            "name": "comb_loop_two_signal",
            "script": "read_verilog -sv risk_profile/cases/comb_loop_two_signal/comb_loop_two_signal.v; hierarchy -top top; proc; opt; check; scc",
            "expected_scc": True,
        },
        {
            "name": "comb_loop_seq_feedback_safe",
            "script": "read_verilog -sv risk_profile/cases/comb_loop_seq_feedback_safe/comb_loop_seq_feedback_safe.v; hierarchy -top top; proc; opt; check; scc",
            "expected_scc": False,
        },
        {
            "name": "fsm_robust_safe",
            "script": "read_verilog -sv risk_profile/cases/fsm_robust_safe/fsm_robust_safe.v; hierarchy -top top; proc; opt; fsm_detect; fsm_extract; fsm_info",
            "expected_fsm": True,
        },
    ]

    failures: list[str] = []
    results: list[dict[str, object]] = []
    for check in checks:
        run = run_cmd([yosys, "-p", str(check["script"])])
        text = str(run["stdout"]) + str(run["stderr"])
        item = {
            "name": check["name"],
            "command": run["command"],
            "exit_code": run["exit_code"],
            "elapsed_seconds": run["elapsed_seconds"],
            "stdout": run["stdout"],
            "stderr": run["stderr"],
        }
        if "expected_scc" in check:
            observed = has_scc(text)
            item["observed_scc"] = observed
            item["expected_scc"] = check["expected_scc"]
            item["passed"] = run["exit_code"] == 0 and observed is check["expected_scc"]
        else:
            observed = "Found FSM state register" in text and "FSM `" in text
            item["observed_fsm"] = observed
            item["expected_fsm"] = check["expected_fsm"]
            item["passed"] = run["exit_code"] == 0 and observed is check["expected_fsm"]
        if not item["passed"]:
            failures.append(str(check["name"]))
        results.append(item)

    report["results"] = results
    report["status"] = "passed" if not failures else "failed"
    (REPORT_DIR / "yosys_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if failures:
        raise SystemExit(f"Yosys reference 对比失败：{failures}，详见 {REPORT_DIR / 'yosys_results.json'}")
    print(f"[test_p0_yosys_reference] Yosys scc/FSM reference 校验通过，结果已写入 {REPORT_DIR / 'yosys_results.json'}。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
