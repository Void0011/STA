from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sta_lite.lint.workflow import LintConfig, run_lint  # noqa: E402
from sta_lite.review.case_registry import case_registry  # noqa: E402
from sta_lite.review.workflow import ReviewConfig, run_review  # noqa: E402
from sta_lite.risk.workflow import RiskConfig, run_risk  # noqa: E402


OUT_ROOT = ROOT / "runs" / "p1_case_upgrades"
TARGETS = {
    "P1_EXCESSIVE_RESET",
    "P1_XPROP_CASEX_CASEZ",
    "P1_SIGNED_UNSIGNED",
    "P1_MULTI_CLOCK_ALWAYS",
}


def lint_summary(relative: str, top: str = "top") -> dict[str, object]:
    return run_lint(
        LintConfig(
            rtl=[str(ROOT / relative)],
            top=top,
            out_dir=str(OUT_ROOT / "lint" / Path(relative).parent.name),
        )
    )


def lint_diagnostics(relative: str) -> list[dict[str, object]]:
    summary = lint_summary(relative)
    return [item for item in summary.get("diagnostics", []) if isinstance(item, dict)]


def require_rule(name: str, diagnostics: list[dict[str, object]], rule: str) -> list[dict[str, object]]:
    hits = [item for item in diagnostics if item.get("rule") == rule]
    if not hits:
        raise SystemExit(f"{name} 未触发期望规则 {rule}，实际：{[item.get('rule') for item in diagnostics]}")
    return hits


def forbid_rule(name: str, diagnostics: list[dict[str, object]], rule: str) -> None:
    if any(item.get("rule") == rule for item in diagnostics):
        raise SystemExit(f"{name} 不应触发规则 {rule}，实际：{[item.get('rule') for item in diagnostics]}")


def risk_summary(case_name: str) -> dict[str, object]:
    case_dir = ROOT / "risk_profile" / "cases" / case_name
    meta = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    return run_risk(
        RiskConfig(
            rtl=[str(case_dir / name) for name in meta["files"]],
            top=str(meta["top"]),
            out_dir=str(OUT_ROOT / "risk" / case_name),
            gold_dir=None,
        )
    )


def risk_hits(case_name: str) -> list[dict[str, object]]:
    return [item for item in risk_summary(case_name).get("risks", []) if isinstance(item, dict)]


def main() -> int:
    registry = {item["case_id"]: item for item in case_registry(ROOT)}
    for case_id in TARGETS:
        item = registry[case_id]
        if item["support_status"] != "supported" or not item["rule_ids"]:
            raise SystemExit(f"{case_id} 应有内部规则、测试与 supported 状态：{item}")
        if item["test_status"] != "passed" or item["golden_reference"].get("status") != "passed":
            raise SystemExit(f"{case_id} 缺少通过的验证/golden 证据：{item}")

    xprop = lint_diagnostics("lint/verilog_warning_example/x_propagation/verilog_warning_casex_casez_001/casex_casez.v")
    xprop_hits = require_rule("casex_casez", xprop, "RTL022_CASEX_CASEZ_XPROP_RISK")
    evidence = [item.get("evidence") for item in xprop_hits]
    if not any(isinstance(item, dict) and item.get("case_keyword") == "casex" for item in evidence):
        raise SystemExit(f"casex 未保留关键字证据：{xprop_hits}")
    if not any(isinstance(item, dict) and item.get("case_keyword") == "casez" and item.get("wildcard_items") for item in evidence):
        raise SystemExit(f"casez 未保留通配项证据：{xprop_hits}")
    forbid_rule("xprop_safe", lint_diagnostics("lint/verilog_warning_example/x_propagation/verilog_warning_xprop_safe_002/xprop_safe.v"), "RTL022_CASEX_CASEZ_XPROP_RISK")

    signed_hits = require_rule(
        "signed_unsigned",
        lint_diagnostics("lint/verilog_warning_example/signedness/verilog_warning_signed_unsigned_001/signed_unsigned.v"),
        "RTL023_SIGNED_UNSIGNED_RISK",
    )
    operators = {operator for item in signed_hits for operator in (item.get("evidence") or {}).get("operators", []) if isinstance(item.get("evidence"), dict)}
    if not {"+", "<", ">>>", "?"}.issubset(operators):
        raise SystemExit(f"mixed signedness 未覆盖算术/比较/移位/三目证据：{operators}")
    forbid_rule("signed_safe", lint_diagnostics("lint/verilog_warning_example/signedness/verilog_warning_signed_safe_002/signed_safe.v"), "RTL023_SIGNED_UNSIGNED_RISK")

    multi_hits = require_rule(
        "multi_clock",
        lint_diagnostics("lint/verilog_warning_example/multi_clock/verilog_warning_multi_clock_001/multi_clock.v"),
        "RTL024_MULTI_CLOCK_ALWAYS",
    )
    if len(multi_hits) != 2:
        raise SystemExit(f"两个独立 multi-clock always 应各有一条诊断，实际：{multi_hits}")
    require_rule(
        "multi_clock_always_ff",
        lint_diagnostics("lint/system_verilog_warning_example/multi_clock/system_verilog_warning_multi_clock_always_ff_001/multi_clock_always_ff.sv"),
        "RTL024_MULTI_CLOCK_ALWAYS",
    )

    fanout_hits = require_rule("excessive_reset_fanout", risk_hits("excessive_reset_fanout"), "RISK_EXCESSIVE_RESET")
    fanout_evidence = fanout_hits[0].get("evidence") or {}
    if not isinstance(fanout_evidence, dict) or fanout_evidence.get("reset_kind") != "asynchronous" or fanout_evidence.get("estimated_reset_bits", 0) < 64:
        raise SystemExit(f"异步 reset 范围统计证据不完整：{fanout_hits}")
    wide_hits = require_rule("excessive_reset_wide_sync", risk_hits("excessive_reset_wide_sync"), "RISK_EXCESSIVE_RESET")
    wide_evidence = wide_hits[0].get("evidence") or {}
    if not isinstance(wide_evidence, dict) or wide_evidence.get("reset_kind") != "synchronous" or wide_evidence.get("estimated_reset_bits") != 128:
        raise SystemExit(f"同步宽数据 reset 范围统计证据不完整：{wide_hits}")
    forbid_rule("excessive_reset_small_safe", risk_hits("excessive_reset_small_safe"), "RISK_EXCESSIVE_RESET")
    forbid_rule("clock_enable_only", risk_hits("excessive_reset_clock_enable_safe"), "RISK_EXCESSIVE_RESET")

    review = run_review(
        ReviewConfig(
            rtl=[str(ROOT / "lint/verilog_warning_example/x_propagation/verilog_warning_casex_casez_001/casex_casez.v")],
            top="top",
            out_dir=str(OUT_ROOT / "review_xprop"),
            gold_dir=None,
        )
    )
    review_cases = {item.get("case_id") for item in review.get("items", []) if isinstance(item, dict)}
    if "P1_XPROP_CASEX_CASEZ" not in review_cases:
        raise SystemExit(f"RTL Review 未聚合 Xprop lint 结果：{review.get('items')}")
    review_reset = run_review(
        ReviewConfig(
            rtl=[str(ROOT / "risk_profile/cases/excessive_reset_wide_sync/excessive_reset_wide_sync.v")],
            top="top",
            out_dir=str(OUT_ROOT / "review_reset"),
            gold_dir=None,
        )
    )
    reset_cases = {item.get("case_id") for item in review_reset.get("items", []) if isinstance(item, dict)}
    if "P1_EXCESSIVE_RESET" not in reset_cases:
        raise SystemExit(f"RTL Review 未聚合 excessive reset profiling 结果：{review_reset.get('items')}")

    print("[test_p1_case_upgrades] 4 个 P1 Case 的内部规则、正负例、证据、RTL Review 聚合和 Coverage 状态校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
