from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "runs" / "lint_tests"


def run_lint(
    name: str,
    rtl: str,
    top: str,
    *,
    extra: list[str] | None = None,
) -> dict[str, object]:
    out_dir = OUT_ROOT / name
    cmd = [
        sys.executable,
        str(ROOT / "sta-lite"),
        "lint",
        "--rtl",
        str(ROOT / rtl),
        "--top",
        top,
        "--out",
        str(out_dir),
        "--fail-on",
        "never",
        "--format",
        "json",
    ]
    if extra:
        cmd.extend(extra)
    env = os.environ.copy()
    env["PATH"] = "/tmp/sta-lite-no-external-eda-tools"
    result = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if result.returncode != 0:
        raise SystemExit(f"{name} lint 命令失败：\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")
    try:
        summary = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{name} lint JSON 输出无法解析：{exc}\n{result.stdout}") from exc
    summary_path = out_dir / "lint_summary.json"
    if not summary_path.is_file():
        raise SystemExit(f"{name} 未生成 lint_summary.json")
    return summary


def rules(summary: dict[str, object]) -> set[str]:
    diagnostics = summary.get("diagnostics")
    if not isinstance(diagnostics, list):
        return set()
    return {str(item.get("rule")) for item in diagnostics if isinstance(item, dict)}


def require_rule(name: str, summary: dict[str, object], rule: str) -> None:
    found = rules(summary)
    if rule not in found:
        raise SystemExit(f"{name} 未触发规则 {rule}，实际规则：{sorted(found)}")


def main() -> int:
    clean = run_lint("clean_ok", "examples/lint/clean_ok/clean_ok.sv", "clean_ok")
    if not clean.get("passed") or clean.get("warning_count") != 0 or clean.get("error_count") != 0:
        raise SystemExit(f"clean_ok 期望完全通过，实际：{clean}")

    syntax_error = run_lint("syntax_error", "examples/lint/syntax_error/syntax_error.sv", "syntax_error")
    require_rule("syntax_error", syntax_error, "SYNTAX001")
    if int(syntax_error.get("error_count", 0)) < 1:
        raise SystemExit("syntax_error 应至少产生一个 error")

    cases = [
        ("default_nettype_missing", "examples/lint/default_nettype_missing/default_nettype_missing.sv", "default_nettype_missing", "RTL001_DEFAULT_NETTYPE", []),
        ("implicit_net", "examples/lint/implicit_net/implicit_net.sv", "implicit_net", "SEM003_UNDECLARED_IDENTIFIER", []),
        ("latch_risk", "examples/lint/latch_risk/latch_risk.sv", "latch_risk", "RTL003_LATCH_RISK", []),
        ("gated_clock", "examples/lint/gated_clock/gated_clock.sv", "gated_clock", "RTL004_GATED_CLOCK_RISK", []),
        ("long_comb", "examples/lint/long_comb/long_comb.sv", "long_comb", "RTL005_LONG_COMB_HEURISTIC", []),
        ("blocking_seq", "examples/lint/blocking_seq/blocking_seq.sv", "blocking_seq", "RTL006_BLOCKING_IN_SEQUENTIAL", []),
        ("nonblocking_comb", "examples/lint/nonblocking_comb/nonblocking_comb.sv", "nonblocking_comb", "RTL007_NONBLOCKING_IN_COMB", []),
        ("multi_driver", "examples/lint/multi_driver/multi_driver.sv", "multi_driver", "RTL008_MULTI_DRIVER_RISK", []),
        ("async_reset", "examples/lint/async_reset/async_reset.sv", "async_reset", "RTL009_ASYNC_RESET_RELEASE_RISK", []),
        (
            "constraint_mismatch",
            "examples/lint/constraint_mismatch/constraint_mismatch.sv",
            "constraint_mismatch",
            "RTL010_CONSTRAINT_CLOCK_MISMATCH",
            ["--sdc", str(ROOT / "examples/lint/constraint_mismatch/bad_clock.sdc")],
        ),
    ]
    for name, rtl, top, rule, extra in cases:
        summary = run_lint(name, rtl, top, extra=extra)
        require_rule(name, summary, rule)

    preprocessor = run_lint(
        "preprocessor",
        "examples/lint/preprocessor/preprocessor.sv",
        "preprocessor_example",
        extra=["--include", str(ROOT / "examples/lint/preprocessor"), "--define", "USE_FF=1"],
    )
    if not preprocessor.get("passed"):
        raise SystemExit(f"preprocessor 示例应通过：{preprocessor}")

    unsupported = run_lint("unsupported", "examples/lint/unsupported/unsupported.sv", "unsupported_top")
    require_rule("unsupported", unsupported, "UNSUPPORTED_SYSTEMVERILOG")
    if int(unsupported.get("unsupported_count", 0)) < 1:
        raise SystemExit("unsupported 示例应产生 unsupported_count")

    custom = run_lint(
        "custom_rule",
        "examples/lint/custom_rule/custom_rule.sv",
        "custom_rule",
        extra=["--rules", str(ROOT / "examples/lint/custom_rule/custom_rules.json")],
    )
    require_rule("custom_rule", custom, "CUSTOM001")

    print("[test_lint_engine] 内部 lint 引擎回归通过，未依赖外部 EDA 工具。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
