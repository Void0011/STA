from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sta_lite.lint.workflow import LintConfig, run_lint  # noqa: E402
from sta_lite.review.case_registry import case_registry, coverage_summary  # noqa: E402
from sta_lite.review.workflow import ReviewConfig, run_review  # noqa: E402
from sta_lite.risk.workflow import RiskConfig, run_risk  # noqa: E402


OUT = ROOT / "runs" / "long_task_coverage"
LINT_CASES = {
    "P0_SYNTHESIZABILITY": ("synthesizability/verilog_warning_simulation_constructs_001/simulation_constructs.v", "synthesizability/verilog_warning_synthesizable_safe_002/synthesizable_safe.v", "RTL025_SYNTHESIZABILITY_RISK"),
    "P1_COMPLEX_GENERATE": ("generate_elaboration/verilog_warning_complex_generate_001/complex_generate.v", "generate_elaboration/verilog_warning_simple_generate_safe_002/simple_generate_safe.v", "RTL026_COMPLEX_GENERATE_RISK"),
    "P1_PARAMETER_WIDTH": ("parameter_width/verilog_warning_parameter_width_001/parameter_width.v", "parameter_width/verilog_warning_parameter_width_safe_002/parameter_width_safe.v", "RTL027_PARAMETER_WIDTH_RISK"),
}
RISK_CASES = {
    "P1_RAM_INFERENCE": ("ram_inference_async_read", "ram_vector_safe", "RISK_RAM_INFERENCE"),
    "P1_DSP_INFERENCE": ("dsp_inference_mac", "dsp_no_multiply_safe", "RISK_DSP_INFERENCE"),
    "P1_MISSING_PIPELINE": ("missing_pipeline_compare_mux", "pipeline_registered_safe", "RISK_MISSING_PIPELINE"),
    "P1_HIGH_FANOUT_CLOCK_ENABLE": ("high_fanout_clock_enable", "clock_enable_small_safe", "RISK_HIGH_FANOUT_CLOCK_ENABLE"),
    "P1_ASYNC_DATA_CONTROL": ("async_data_control_event", "async_reset_control_safe", "RISK_ASYNC_DATA_CONTROL"),
}


def lint_rules(relative: str) -> tuple[set[str], list[dict[str, object]]]:
    source = ROOT / "lint" / "verilog_warning_example" / relative
    summary = run_lint(LintConfig(rtl=[str(source)], top="top", out_dir=str(OUT / "lint" / source.parent.name)))
    items = [item for item in summary.get("diagnostics", []) if isinstance(item, dict)]
    return {str(item.get("rule")) for item in items}, items


def risk_rules(case_name: str) -> tuple[set[str], list[dict[str, object]]]:
    case_dir = ROOT / "risk_profile" / "cases" / case_name
    metadata = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    summary = run_risk(RiskConfig(rtl=[str(case_dir / item) for item in metadata["files"]], top=metadata["top"], out_dir=str(OUT / "risk" / case_name), gold_dir=None))
    items = [item for item in summary.get("risks", []) if isinstance(item, dict)]
    return {str(item.get("rule")) for item in items}, items


def require_evidence(case_id: str, items: list[dict[str, object]], rule: str) -> None:
    hits = [item for item in items if item.get("rule") == rule]
    if not hits or not all(isinstance(item.get("evidence"), dict) and item["evidence"] for item in hits):
        raise SystemExit(f"{case_id} 的 {rule} 缺少非空结构证据：{hits}")


def main() -> int:
    registry = {item["case_id"]: item for item in case_registry(ROOT)}
    target_ids = set(LINT_CASES) | set(RISK_CASES)
    for case_id in target_ids:
        item = registry[case_id]
        if item["support_status"] != "supported" or item["test_status"] != "passed":
            raise SystemExit(f"{case_id} 应有内部规则、正负例和 supported 状态：{item}")
        if item["golden_reference"].get("status") not in {"passed", "metadata_reference"}:
            raise SystemExit(f"{case_id} 缺少开发期 golden/reference 说明：{item}")

    for case_id, (positive, negative, rule) in LINT_CASES.items():
        positive_rules, positive_items = lint_rules(positive)
        negative_rules, _ = lint_rules(negative)
        if rule not in positive_rules or rule in negative_rules:
            raise SystemExit(f"{case_id} 正负例边界失败：positive={positive_rules}, negative={negative_rules}")
        require_evidence(case_id, positive_items, rule)
        source = ROOT / "lint" / "verilog_warning_example" / positive
        review = run_review(ReviewConfig(rtl=[str(source)], top="top", out_dir=str(OUT / "review" / case_id.lower()), gold_dir=None))
        review_cases = {item.get("case_id") for item in review.get("items", []) if isinstance(item, dict)}
        if case_id not in review_cases:
            raise SystemExit(f"RTL Review 未复用并聚合 {case_id} 的 lint 规则：{review_cases}")

    for case_id, (positive, negative, rule) in RISK_CASES.items():
        positive_rules, positive_items = risk_rules(positive)
        negative_rules, _ = risk_rules(negative)
        if rule not in positive_rules or rule in negative_rules:
            raise SystemExit(f"{case_id} 正负例边界失败：positive={positive_rules}, negative={negative_rules}")
        require_evidence(case_id, positive_items, rule)
        if rule == "RISK_RAM_INFERENCE":
            ram_hit = next(item for item in positive_items if item.get("rule") == rule)
            evidence = ram_hit.get("evidence") or {}
            if not isinstance(evidence, dict) or evidence.get("unpacked_range") != "[0 : 255]" or evidence.get("declaration_line") != 2:
                raise SystemExit(f"RAM 声明证据未指向真实 unpacked declaration：{ram_hit}")
        case_dir = ROOT / "risk_profile" / "cases" / positive
        metadata = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
        review = run_review(ReviewConfig(rtl=[str(case_dir / source) for source in metadata["files"]], top=metadata["top"], out_dir=str(OUT / "review" / case_id.lower()), gold_dir=None))
        review_cases = {item.get("case_id") for item in review.get("items", []) if isinstance(item, dict)}
        if case_id not in review_cases:
            raise SystemExit(f"RTL Review 未复用并聚合 {case_id} 的 profiling 规则：{review_cases}")

    coverage = coverage_summary(list(registry.values()))
    if coverage["priorities"]["P1"]["supported"] != 12 or coverage["priorities"]["P1"]["coverage_percent"] != 100.0:
        raise SystemExit(f"12 个 P1 Case 应全部 supported：{coverage}")
    if registry["P0_FSM_ROBUSTNESS"]["support_status"] != "partially_supported":
        raise SystemExit("FSM 鲁棒性必须保留 Rules.md 指定的部分支持边界。")

    print("[test_long_task_coverage] 新增 8 个 Case 的内部规则、正负例、结构证据、Review 复用和 Coverage 状态校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
