from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sta_lite.lint.workflow import LintConfig, run_lint  # noqa: E402
from sta_lite.review.workflow import ReviewConfig, run_review  # noqa: E402
from sta_lite.risk.workflow import RiskConfig, run_risk  # noqa: E402


OUT_ROOT = ROOT / "runs" / "review_tests"
RTL = str(ROOT / "risk_profile" / "cases" / "long_comb_path" / "long_comb_path.v")


def signature(items: list[dict[str, object]]) -> Counter[tuple[object, object, object]]:
    return Counter((item.get("rule"), item.get("file"), item.get("line")) for item in items)


def main() -> int:
    lint = run_lint(
        LintConfig(rtl=[RTL], top="top", out_dir=str(OUT_ROOT / "standalone_lint"))
    )
    profiling = run_risk(
        RiskConfig(rtl=[RTL], top="top", out_dir=str(OUT_ROOT / "standalone_profiling"), gold_dir=None)
    )
    review = run_review(
        ReviewConfig(rtl=[RTL], top="top", out_dir=str(OUT_ROOT / "combined"), gold_dir=None)
    )

    if review.get("status") != "success":
        raise SystemExit(f"RTL Review 应完整成功：{review.get('subflows')}")
    subflows = review.get("subflows")
    if not isinstance(subflows, dict) or subflows.get("lint", {}).get("status") != "success":
        raise SystemExit(f"RTL Review 缺少独立 Lint 成功状态：{subflows}")
    if subflows.get("profiling", {}).get("status") != "success":
        raise SystemExit(f"RTL Review 缺少独立 Profiling 成功状态：{subflows}")

    review_items = [item for item in review.get("items", []) if isinstance(item, dict)]
    review_lint = [item for item in review_items if item.get("source") == "lint"]
    review_profiling = [item for item in review_items if item.get("source") == "profiling"]
    lint_items = [item for item in lint.get("diagnostics", []) if isinstance(item, dict)]
    profiling_items = [item for item in profiling.get("risks", []) if isinstance(item, dict)]

    if signature(review_lint) != signature(lint_items):
        raise SystemExit("RTL Review 的 Lint 结果不等于独立 Lint 结果。")
    if signature(review_profiling) != signature(profiling_items):
        raise SystemExit("RTL Review 的 Profiling 结果不等于独立 Profiling 结果。")
    for item in review_items:
        if not item.get("correlation_id") or int(item.get("overlap_count") or 0) < 1:
            raise SystemExit(f"RTL Review 结果缺少关联标识：{item}")
    if not any(item.get("case_id") == "P0_LONG_COMBINATIONAL_PATH" for item in review_items):
        raise SystemExit("long_comb Review 结果缺少 P0 Case 归类。")

    partial = run_review(
        ReviewConfig(rtl=[RTL], top="missing_top", out_dir=str(OUT_ROOT / "partial"), gold_dir=None)
    )
    partial_flows = partial.get("subflows")
    if partial.get("status") != "partial_success":
        raise SystemExit(f"一个子流程失败时应返回 partial_success：{partial}")
    if partial_flows.get("lint", {}).get("status") != "success":
        raise SystemExit(f"Profiling 失败不应丢弃 Lint 结果：{partial_flows}")
    if partial_flows.get("profiling", {}).get("status") != "failure":
        raise SystemExit(f"缺失 top 时 Profiling 应明确失败：{partial_flows}")
    partial_items = [item for item in partial.get("items", []) if isinstance(item, dict)]
    if not any(item.get("source") == "lint" for item in partial_items):
        raise SystemExit("部分成功的 Review 丢失了 Lint 诊断。")
    if not any(item.get("rule") == "RISK_WORKFLOW_BLOCKED" for item in partial_items):
        raise SystemExit("部分成功的 Review 缺少 Profiling 失败诊断。")

    for out_dir in (OUT_ROOT / "combined", OUT_ROOT / "partial"):
        for artifact in ("review_summary.json", "review_report.md", "review.log"):
            if not (out_dir / artifact).is_file():
                raise SystemExit(f"RTL Review 未生成 {out_dir / artifact}。")

    print("[test_review_workflow] Review 并集、关联标识和子流程失败隔离校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
