from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sta_lite.review.case_registry import (  # noqa: E402
    VALID_OWNERS,
    VALID_PRIORITIES,
    VALID_SUPPORT_STATUSES,
    case_registry,
    coverage_summary,
)


def main() -> int:
    cases = case_registry(ROOT)
    by_id = {item["case_id"]: item for item in cases}

    if len(cases) != 29:
        raise SystemExit(f"Case registry 总数应为 29，实际为 {len(cases)}。")
    if len(by_id) != len(cases):
        raise SystemExit("Case registry 存在重复 case_id。")

    priorities = Counter(item["priority"] for item in cases)
    if priorities != {"P0": 17, "P1": 12}:
        raise SystemExit(f"P0/P1 数量不正确：{dict(priorities)}")

    for item in cases:
        if item["priority"] not in VALID_PRIORITIES:
            raise SystemExit(f"{item['case_id']} 的优先级非法：{item['priority']}")
        if item["owner"] not in VALID_OWNERS:
            raise SystemExit(f"{item['case_id']} 的 owner 非法：{item['owner']}")
        if item["support_status"] not in VALID_SUPPORT_STATUSES:
            raise SystemExit(f"{item['case_id']} 的支持状态非法：{item['support_status']}")
        if item["support_status"] == "supported":
            if not item["rule_ids"]:
                raise SystemExit(f"{item['case_id']} 标记为 supported，但没有规则 ID。")
            if item["test_status"] != "passed" or not item["verification_evidence"]:
                raise SystemExit(f"{item['case_id']} 标记为 supported，但没有可执行验证证据。")
            if not item["latest_verification_evidence"]:
                raise SystemExit(f"{item['case_id']} 标记为 supported，但没有最新验证证据。")

    for case_id in (item["case_id"] for item in cases if item["priority"] == "P1"):
        item = by_id[case_id]
        if item["support_status"] != "supported" or not item["rule_ids"]:
            raise SystemExit(f"{case_id} 应已具备内部规则、可执行测试和 supported 状态：{item}")
        if item["golden_reference"].get("status") not in {"passed", "metadata_reference", "not_configured"}:
            raise SystemExit(f"{case_id} golden/reference 状态非法：{item}")

    comb_loop = by_id["P0_COMBINATIONAL_LOOP"]
    if comb_loop["support_status"] != "supported" or "RISK_COMBINATIONAL_LOOP" not in comb_loop["rule_ids"]:
        raise SystemExit(f"P0_COMBINATIONAL_LOOP 应已完成 supported 升级：{comb_loop}")
    if comb_loop["golden_reference"].get("status") != "passed":
        raise SystemExit(f"P0_COMBINATIONAL_LOOP 缺少通过的 golden/reference 状态：{comb_loop}")

    fsm = by_id["P0_FSM_ROBUSTNESS"]
    if fsm["support_status"] != "partially_supported" or "RISK_FSM_ROBUSTNESS" not in fsm["rule_ids"]:
        raise SystemExit(f"P0_FSM_ROBUSTNESS 应按 Rules.md 标记为 partially_supported：{fsm}")
    if fsm["golden_reference"].get("status") != "passed":
        raise SystemExit(f"P0_FSM_ROBUSTNESS 缺少通过的 golden/reference 状态：{fsm}")

    summary = coverage_summary(cases)
    if summary["total"] != len(cases):
        raise SystemExit(f"覆盖汇总总数与注册表不一致：{summary}")
    if sum(summary["owner_counts"].values()) != len(cases):
        raise SystemExit(f"owner 汇总与注册表不一致：{summary['owner_counts']}")
    for priority, expected_total in (("P0", 17), ("P1", 12)):
        item = summary["priorities"][priority]
        if item["total"] != expected_total:
            raise SystemExit(f"{priority} 汇总总数不正确：{item}")
        classified = item["supported"] + item["unsupported_diagnostic"] + item["unsupported_by_design"] + item["partially_supported"] + item["not_covered"]
        if classified != expected_total:
            raise SystemExit(f"{priority} 支持状态汇总不守恒：{item}")

    print("[test_case_registry] 29 个 P0/P1 Case、owner、状态和验证证据校验通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
