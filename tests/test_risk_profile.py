from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES_ROOT = ROOT / "risk_profile" / "cases"
OUT_ROOT = ROOT / "runs" / "risk_tests"

MUST_DETECT = {
    "async_reset_release_unsync",
    "combinational_loop",
    "fsm_robustness",
    "long_comb_path",
    "latch_inference_timing",
    "high_fanout_control",
    "gated_or_derived_clock",
}


def load_cases() -> list[tuple[Path, dict[str, object]]]:
    cases: list[tuple[Path, dict[str, object]]] = []
    for case_json in sorted(CASES_ROOT.glob("*/case.json")):
        with case_json.open(encoding="utf-8") as fh:
            cases.append((case_json.parent, json.load(fh)))
    if len(cases) < 11:
        raise SystemExit(f"risk_profile/cases 下至少应发现 11 个 case，实际 {len(cases)} 个。")
    return cases


def run_case(case_dir: Path, meta: dict[str, object]) -> dict[str, object]:
    files = meta.get("files")
    if not isinstance(files, list) or not files:
        raise SystemExit(f"{case_dir} 的 case.json 缺少 files。")
    top = str(meta.get("top") or "")
    if not top:
        raise SystemExit(f"{case_dir} 的 case.json 缺少 top。")
    out_dir = OUT_ROOT / str(meta.get("id"))
    cmd = [
        sys.executable,
        str(ROOT / "sta-lite"),
        "risk",
        "--rtl",
    ]
    cmd.extend(str(case_dir / str(item)) for item in files)
    cmd.extend(["--top", top, "--out", str(out_dir), "--format", "json"])
    sdc = meta.get("sdc")
    if isinstance(sdc, str) and sdc:
        cmd.extend(["--sdc", str(case_dir / sdc)])
    env = os.environ.copy()
    env["PATH"] = "/tmp/sta-lite-no-external-eda-tools"
    result = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if result.returncode != 0:
        raise SystemExit(f"{case_dir.name} risk 命令失败：\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    try:
        summary = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{case_dir.name} risk JSON 输出无法解析：{exc}\n{result.stdout}") from exc
    for artifact in ("risk_summary.json", "risk_report.md", "risk.log"):
        if not (out_dir / artifact).is_file():
            raise SystemExit(f"{case_dir.name} 未生成 {artifact}。")
    report = (out_dir / "risk_report.md").read_text(encoding="utf-8")
    if "RTL 时序风险报告" not in report:
        raise SystemExit(f"{case_dir.name} 的 risk_report.md 缺少中文报告标题。")
    gold = summary.get("gold_compare")
    if not isinstance(gold, dict) or gold.get("available") is not False:
        raise SystemExit(f"{case_dir.name} 在没有 gold 报告时应正常跳过对比：{gold}")
    return summary


def risk_rules(summary: dict[str, object]) -> set[str]:
    risks = summary.get("risks")
    if not isinstance(risks, list):
        return set()
    return {str(item.get("rule")) for item in risks if isinstance(item, dict)}


def main() -> int:
    cases = load_cases()
    discovered = {str(meta.get("category")) for _case_dir, meta in cases}
    missing = MUST_DETECT - discovered
    if missing:
        raise SystemExit(f"缺少 smoke 必测风险目录：{sorted(missing)}")

    for case_dir, meta in cases:
        summary = run_case(case_dir, meta)
        category = str(meta.get("category"))
        expected = {str(item) for item in meta.get("expected_risks", []) if isinstance(item, str)}
        if category in MUST_DETECT:
            found = risk_rules(summary)
            missed = expected - found
            if missed:
                raise SystemExit(f"{case_dir.name} 未触发期望风险 {sorted(missed)}，实际：{sorted(found)}")
        absent = {str(item) for item in meta.get("expected_absent_risks", []) if isinstance(item, str)}
        if absent:
            found = risk_rules(summary)
            unexpected = absent & found
            if unexpected:
                raise SystemExit(f"{case_dir.name} 不应触发风险 {sorted(unexpected)}，实际：{sorted(found)}")
        if int(summary.get("parse_note_count", 0)) > 0:
            raise SystemExit(f"{case_dir.name} 示例应保持语法干净，实际 parse notes：{summary.get('parse_notes')}")

    print("[test_risk_profile] RTL 时序风险 smoke 回归通过，未依赖外部 EDA 工具。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
