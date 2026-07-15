from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES_ROOT = ROOT / "risk_profile" / "cases"
OUT_ROOT = ROOT / "runs" / "p0_remaining_cases"


COMB_LOOP_CASES = [
    "comb_loop_two_signal",
    "comb_loop_self",
    "comb_loop_always",
    "comb_loop_ternary",
    "comb_loop_always_comb_sv",
]

COMB_SAFE_CASES = [
    "comb_loop_seq_feedback_safe",
    "comb_chain_safe",
]

FSM_CASES = {
    "fsm_missing_reset": "missing_reset",
    "fsm_missing_case_default": "missing_case_default",
    "fsm_unsafe_default": "unsafe_default_recovery",
    "fsm_missing_state": "declared_state_not_handled",
    "fsm_incomplete_next_assign": "incomplete_next_state_assignment",
    "fsm_terminal_state": "obvious_terminal_state",
}

FSM_SAFE_CASES = [
    "fsm_robust_safe",
    "non_fsm_safe",
]


def run_risk_case(case_name: str) -> dict[str, object]:
    case_dir = CASES_ROOT / case_name
    meta = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    cmd = [
        sys.executable,
        str(ROOT / "sta-lite"),
        "risk",
        "--rtl",
    ]
    cmd.extend(str(case_dir / str(item)) for item in meta["files"])
    cmd.extend(["--top", str(meta["top"]), "--out", str(OUT_ROOT / case_name), "--format", "json"])
    env = os.environ.copy()
    env["PATH"] = "/tmp/sta-lite-no-external-eda-tools"
    result = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if result.returncode != 0:
        raise SystemExit(f"{case_name} STA-lite risk 运行失败：\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    summary = json.loads(result.stdout)
    if int(summary.get("parse_note_count", 0)) != 0:
        raise SystemExit(f"{case_name} 不应产生解析告警：{summary.get('parse_notes')}")
    return summary


def risk_items(summary: dict[str, object], rule: str) -> list[dict[str, object]]:
    risks = summary.get("risks")
    if not isinstance(risks, list):
        return []
    return [item for item in risks if isinstance(item, dict) and item.get("rule") == rule]


def require_rule(case_name: str, summary: dict[str, object], rule: str) -> list[dict[str, object]]:
    items = risk_items(summary, rule)
    if not items:
        rules = [item.get("rule") for item in summary.get("risks", []) if isinstance(item, dict)]
        raise SystemExit(f"{case_name} 未触发期望规则 {rule}，实际：{rules}")
    return items


def forbid_rule(case_name: str, summary: dict[str, object], rule: str) -> None:
    items = risk_items(summary, rule)
    if items:
        raise SystemExit(f"{case_name} 不应触发规则 {rule}，实际诊断：{items}")


def check_comb_loop_cases() -> None:
    for case_name in COMB_LOOP_CASES:
        summary = run_risk_case(case_name)
        items = require_rule(case_name, summary, "RISK_COMBINATIONAL_LOOP")
        evidence = items[0].get("evidence")
        if not isinstance(evidence, dict) or not evidence.get("scc_nodes") or not evidence.get("cycle_path"):
            raise SystemExit(f"{case_name} 组合环路证据缺少 SCC/cycle_path：{items[0]}")
    for case_name in COMB_SAFE_CASES:
        forbid_rule(case_name, run_risk_case(case_name), "RISK_COMBINATIONAL_LOOP")


def check_fsm_cases() -> None:
    for case_name, expected_issue in FSM_CASES.items():
        summary = run_risk_case(case_name)
        items = require_rule(case_name, summary, "RISK_FSM_ROBUSTNESS")
        issues = {
            str((item.get("evidence") or {}).get("issue"))
            for item in items
            if isinstance(item.get("evidence"), dict)
        }
        if expected_issue not in issues:
            raise SystemExit(f"{case_name} 未触发期望 FSM issue {expected_issue}，实际：{sorted(issues)}")
    for case_name in FSM_SAFE_CASES:
        forbid_rule(case_name, run_risk_case(case_name), "RISK_FSM_ROBUSTNESS")


def check_review_and_registry() -> None:
    sys.path.insert(0, str(ROOT))
    from sta_lite.review.case_registry import case_registry
    from sta_lite.review.workflow import ReviewConfig, run_review

    cases = {item["case_id"]: item for item in case_registry(ROOT)}
    comb_loop = cases["P0_COMBINATIONAL_LOOP"]
    if comb_loop["support_status"] != "supported" or "RISK_COMBINATIONAL_LOOP" not in comb_loop["rule_ids"]:
        raise SystemExit(f"P0_COMBINATIONAL_LOOP 应标记为 supported：{comb_loop}")
    if comb_loop["test_status"] != "passed":
        raise SystemExit(f"P0_COMBINATIONAL_LOOP 缺少可执行验证证据：{comb_loop}")

    fsm = cases["P0_FSM_ROBUSTNESS"]
    if fsm["support_status"] != "partially_supported" or "RISK_FSM_ROBUSTNESS" not in fsm["rule_ids"]:
        raise SystemExit(f"P0_FSM_ROBUSTNESS 应按 Rules.md 标记为 partially_supported：{fsm}")
    if fsm["test_status"] != "partial":
        raise SystemExit(f"P0_FSM_ROBUSTNESS 应显示部分验证状态：{fsm}")

    comb_case = CASES_ROOT / "comb_loop_two_signal"
    comb_review = run_review(
        ReviewConfig(
            rtl=[str(comb_case / "comb_loop_two_signal.v")],
            top="top",
            out_dir=str(OUT_ROOT / "review_comb_loop"),
            gold_dir=None,
        )
    )
    comb_ids = {item.get("case_id") for item in comb_review.get("items", []) if isinstance(item, dict)}
    if "P0_COMBINATIONAL_LOOP" not in comb_ids:
        raise SystemExit(f"RTL Review 未把组合环路归类到 P0_COMBINATIONAL_LOOP：{comb_review.get('items')}")

    fsm_case = CASES_ROOT / "fsm_missing_case_default"
    fsm_review = run_review(
        ReviewConfig(
            rtl=[str(fsm_case / "fsm_missing_case_default.v")],
            top="top",
            out_dir=str(OUT_ROOT / "review_fsm"),
            gold_dir=None,
        )
    )
    fsm_ids = {item.get("case_id") for item in fsm_review.get("items", []) if isinstance(item, dict)}
    if "P0_FSM_ROBUSTNESS" not in fsm_ids:
        raise SystemExit(f"RTL Review 未把 FSM 鲁棒性诊断归类到 P0_FSM_ROBUSTNESS：{fsm_review.get('items')}")


def main() -> int:
    check_comb_loop_cases()
    check_fsm_cases()
    check_review_and_registry()
    print("[test_p0_remaining_cases] P0 组合环路和 FSM 鲁棒性正负例、Review 归类、Coverage 状态校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
