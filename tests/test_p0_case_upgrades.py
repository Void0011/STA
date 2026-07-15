from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sta_lite.lint.workflow import LintConfig, run_lint  # noqa: E402
from sta_lite.review.case_registry import case_registry  # noqa: E402
from sta_lite.review.workflow import ReviewConfig, run_review  # noqa: E402
from sta_lite.risk.workflow import RiskConfig, run_risk  # noqa: E402


OUT_ROOT = ROOT / "runs" / "p0_case_upgrades"
INITIAL_P0_PARTIAL_CASES = {
    "P0_WIDTH_MISMATCH",
    "P0_SIMPLE_CDC",
    "P0_INCOMPLETE_CASE_IF",
    "P0_LARGE_MUX_PRIORITY",
    "P0_ARITHMETIC_CHAIN",
}


def lint_rules(relative_path: str, top: str = "top") -> set[str]:
    summary = run_lint(
        LintConfig(
            rtl=[str(ROOT / relative_path)],
            top=top,
            out_dir=str(OUT_ROOT / "lint" / Path(relative_path).parent.name),
        )
    )
    return {str(item.get("rule")) for item in summary.get("diagnostics", []) if isinstance(item, dict)}


def risk_summary(case_name: str) -> dict[str, object]:
    case_dir = ROOT / "risk_profile" / "cases" / case_name
    import json

    meta = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    files = [str(case_dir / item) for item in meta["files"]]
    return run_risk(
        RiskConfig(
            rtl=files,
            top=str(meta["top"]),
            out_dir=str(OUT_ROOT / "risk" / case_name),
            gold_dir=None,
        )
    )


def risk_rules(case_name: str) -> set[str]:
    summary = risk_summary(case_name)
    return {str(item.get("rule")) for item in summary.get("risks", []) if isinstance(item, dict)}


def require_rule(name: str, rules: set[str], rule: str) -> None:
    if rule not in rules:
        raise SystemExit(f"{name} 未触发期望规则 {rule}，实际：{sorted(rules)}")


def forbid_rule(name: str, rules: set[str], rule: str) -> None:
    if rule in rules:
        raise SystemExit(f"{name} 不应触发规则 {rule}，实际：{sorted(rules)}")


def main() -> int:
    cases = {item["case_id"]: item for item in case_registry(ROOT)}
    for case_id in INITIAL_P0_PARTIAL_CASES:
        item = cases[case_id]
        if item["support_status"] != "supported":
            raise SystemExit(f"{case_id} 应已从 partially_supported 升级为 supported：{item}")
        if not item.get("golden_reference") or item["golden_reference"].get("status") not in {"passed", "metadata_reference"}:
            raise SystemExit(f"{case_id} 缺少 golden/metadata 参考状态：{item}")
        if item["test_status"] != "passed":
            raise SystemExit(f"{case_id} 缺少可执行测试证据：{item}")

    require_rule(
        "assign_truncation",
        lint_rules("lint/verilog_warning_example/width_range/verilog_warning_assign_truncation_002/assign_truncation.v"),
        "RTL020_ASSIGN_WIDTH_MISMATCH",
    )
    require_rule(
        "assign_extension",
        lint_rules("lint/verilog_warning_example/width_range/verilog_warning_assign_extension_003/assign_extension.v"),
        "RTL020_ASSIGN_WIDTH_MISMATCH",
    )
    forbid_rule(
        "explicit_extension_safe",
        lint_rules("lint/verilog_warning_example/width_range/verilog_warning_explicit_extension_safe_004/explicit_extension_safe.v"),
        "RTL020_ASSIGN_WIDTH_MISMATCH",
    )
    require_rule(
        "case_missing_default",
        lint_rules("lint/verilog_warning_example/latch_risk/verilog_warning_case_missing_default_002/case_missing_default.v"),
        "RTL003_LATCH_RISK",
    )
    forbid_rule(
        "default_assignment_safe",
        lint_rules("lint/verilog_warning_example/latch_risk/verilog_warning_default_assignment_safe_003/default_assignment_safe.v"),
        "RTL003_LATCH_RISK",
    )
    forbid_rule(
        "default_assignment_safe",
        lint_rules("lint/verilog_warning_example/latch_risk/verilog_warning_default_assignment_safe_003/default_assignment_safe.v"),
        "RTL021_INCOMPLETE_CASE_DEFAULT",
    )

    require_rule("cdc_unsync_signal", risk_rules("cdc_unsync_signal"), "RISK_CDC_UNSYNC_SIGNAL")
    require_rule("cdc_multibit_unsync_signal", risk_rules("cdc_multibit_unsync_signal"), "RISK_CDC_UNSYNC_SIGNAL")
    forbid_rule("cdc_two_ff_sync_safe", risk_rules("cdc_two_ff_sync_safe"), "RISK_CDC_UNSYNC_SIGNAL")
    require_rule("wide_mux_priority_encoder", risk_rules("wide_mux_priority_encoder"), "RISK_WIDE_MUX_PRIORITY_ENCODER")
    require_rule("wide_mux_case_vector", risk_rules("wide_mux_case_vector"), "RISK_WIDE_MUX_PRIORITY_ENCODER")
    forbid_rule("small_mux_safe", risk_rules("small_mux_safe"), "RISK_WIDE_MUX_PRIORITY_ENCODER")
    require_rule("arithmetic_chain_no_pipeline", risk_rules("arithmetic_chain_no_pipeline"), "RISK_ARITH_CHAIN_NO_PIPELINE")
    forbid_rule("arithmetic_pipelined_safe", risk_rules("arithmetic_pipelined_safe"), "RISK_ARITH_CHAIN_NO_PIPELINE")

    review = run_review(
        ReviewConfig(
            rtl=[str(ROOT / "lint/verilog_warning_example/width_range/verilog_warning_assign_truncation_002/assign_truncation.v")],
            top="top",
            out_dir=str(OUT_ROOT / "review_width"),
            gold_dir=None,
        )
    )
    review_cases = {item.get("case_id") for item in review.get("items", []) if isinstance(item, dict)}
    if "P0_WIDTH_MISMATCH" not in review_cases:
        raise SystemExit(f"RTL Review 未把赋值位宽诊断归类到 P0_WIDTH_MISMATCH：{review.get('items')}")

    print("[test_p0_case_upgrades] 5 个 P0 partial 升级项的正负例、Review 归类和 Coverage 状态校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
