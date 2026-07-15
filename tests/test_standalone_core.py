from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sta_lite.core.tool_status import backend_tool_status  # noqa: E402
from sta_lite.lint.workflow import LintConfig, run_lint  # noqa: E402
from sta_lite.parsers.reports import read_text  # noqa: E402
from sta_lite.review.workflow import ReviewConfig, run_review  # noqa: E402
from sta_lite.risk.workflow import RiskConfig, run_risk  # noqa: E402


OUT = ROOT / "runs" / "standalone_core"
NO_TOOLS_PATH = "/tmp/sta-lite-no-external-eda-tools"


def signature(items: object) -> list[tuple[str, str, int]]:
    if not isinstance(items, list):
        return []
    return sorted((str(item.get("rule")), Path(str(item.get("file"))).name, int(item.get("line") or 0)) for item in items if isinstance(item, dict))


def run_core(suffix: str) -> dict[str, object]:
    source = ROOT / "risk_profile/cases/missing_pipeline_compare_mux/missing_pipeline_compare_mux.v"
    lint = run_lint(LintConfig(rtl=[str(source)], top="top", out_dir=str(OUT / suffix / "lint")))
    risk = run_risk(RiskConfig(rtl=[str(source)], top="top", out_dir=str(OUT / suffix / "risk"), gold_dir=None))
    review = run_review(ReviewConfig(rtl=[str(source)], top="top", out_dir=str(OUT / suffix / "review"), gold_dir=None))
    return {"lint": lint, "risk": risk, "review": review}


def main() -> int:
    if "sta_lite.core.runner" in sys.modules or "sta_lite.lint.diff_runner" in sys.modules:
        raise SystemExit("内部 workflow 导入阶段不应加载 Backend runner 或开发期 lint-diff adapter。")
    normal = run_core("normal")
    if "sta_lite.core.runner" in sys.modules or "sta_lite.lint.diff_runner" in sys.modules:
        raise SystemExit("内部 lint/risk/review 运行不应加载 Backend runner 或开发期 lint-diff adapter。")
    with patch.dict(os.environ, {"PATH": NO_TOOLS_PATH}, clear=False), patch(
        "subprocess.run", side_effect=AssertionError("内部 RTL 核心不得调用外部子进程")
    ), patch("subprocess.Popen", side_effect=AssertionError("内部 RTL 核心不得启动外部子进程")):
        isolated = run_core("isolated")
        backend = backend_tool_status()

    comparisons = (
        ("lint", "diagnostics"),
        ("risk", "risks"),
        ("review", "items"),
    )
    for workflow, key in comparisons:
        before = signature(normal[workflow].get(key))
        after = signature(isolated[workflow].get(key))
        if before != after:
            raise SystemExit(f"{workflow} 在无外部工具 PATH 下结果不一致：normal={before}, isolated={after}")

    if backend.get("available") is not False or backend.get("status") != "unavailable_optional":
        raise SystemExit(f"无外部工具时 Backend 状态不正确：{backend}")
    message = str(backend.get("message_zh") or "")
    for text in ("后端可选工具不可用", "RTL Review", "RTL Lint", "RTL Timing Risk Profiling", "Case Coverage"):
        if text not in message:
            raise SystemExit(f"Backend 中文状态未说明独立可用能力：{message}")

    review_report = Path(str(isolated["review"]["artifacts"]["review_report_md"]))
    if not read_text(review_report).startswith("# STA-lite RTL Review"):
        raise SystemExit("无外部工具环境不能读取已生成的 Review 报告。")
    summary_path = Path(str(isolated["risk"]["artifacts"]["risk_summary_json"]))
    if not json.loads(read_text(summary_path)).get("risks"):
        raise SystemExit("无外部工具环境不能读取已生成的 Risk summary。")

    print("[test_standalone_core] 无外部 EDA 工具时 lint/risk/review 结果一致，且 Backend 缺失状态与已有报告读取正常。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
