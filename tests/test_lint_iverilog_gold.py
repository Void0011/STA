from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IVERILOG = ROOT / "tools" / "bin" / "iverilog"
OUT_ROOT = ROOT / "runs" / "lint_iverilog_gold"


def run_iverilog(name: str, rtl: str, top: str, extra: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [str(IVERILOG), "-g2012", "-tnull", "-Wall", "-s", top]
    if extra:
        cmd.extend(extra)
    cmd.append(str(ROOT / rtl))
    return subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def run_sta_lite(name: str, rtl: str, top: str, extra: list[str] | None = None) -> dict[str, object]:
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
    result = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise SystemExit(f"{name} sta-lite lint 执行失败：\n{result.stdout}\n{result.stderr}")
    return json.loads(result.stdout)


def main() -> int:
    if not IVERILOG.is_file():
        raise SystemExit(f"找不到本地 iverilog wrapper：{IVERILOG}")

    cases = [
        {
            "name": "clean_ok",
            "rtl": "examples/lint/clean_ok/clean_ok.sv",
            "top": "clean_ok",
            "expect_iverilog_ok": True,
        },
        {
            "name": "clean_counter_injected_bug",
            "rtl": "examples/lint/clean_counter/clean_counter.sv",
            "top": "clean_counter",
            "expect_iverilog_ok": False,
        },
        {
            "name": "syntax_error",
            "rtl": "examples/lint/syntax_error/syntax_error.sv",
            "top": "syntax_error",
            "expect_iverilog_ok": False,
        },
        {
            "name": "preprocessor",
            "rtl": "examples/lint/preprocessor/preprocessor.sv",
            "top": "preprocessor_example",
            "expect_iverilog_ok": True,
            "iverilog_extra": ["-I", str(ROOT / "examples/lint/preprocessor"), "-DUSE_FF=1"],
            "sta_extra": ["--include", str(ROOT / "examples/lint/preprocessor"), "--define", "USE_FF=1"],
        },
    ]

    for case in cases:
        compare_case(case)

    mutation_dir = OUT_ROOT / "mutations"
    mutation_dir.mkdir(parents=True, exist_ok=True)
    clean_text = (ROOT / "examples/lint/clean_ok/clean_ok.sv").read_text(encoding="utf-8")
    mutations = {
        "missing_semicolon_proc": clean_text.replace("count <= count + 4'd1;", "count <= count + 4'd1"),
        "malformed_based_number": clean_text.replace("4'd1;", "4'd;"),
        "missing_endmodule": clean_text.replace("endmodule", "", 1),
        "bad_port_comma": clean_text.replace("input  logic       en,", "input  logic       en"),
        "bad_expr": clean_text.replace("count <= count + 4'd1;", "count <= count + ;"),
        "extra_else": clean_text.replace("    end\nendmodule", "    end else begin\n    end\nendmodule"),
    }
    for name, text in mutations.items():
        path = mutation_dir / f"{name}.sv"
        path.write_text(text, encoding="utf-8")
        compare_case(
            {
                "name": f"mutation_{name}",
                "rtl": str(path.relative_to(ROOT)),
                "top": "clean_ok",
                "expect_iverilog_ok": False,
            }
        )

    print("[test_lint_iverilog_gold] sta-lite lint 与 iverilog gold 的通过/失败结果一致。")
    return 0


def compare_case(case: dict[str, object]) -> None:
    name = str(case["name"])
    rtl = str(case["rtl"])
    top = str(case["top"])
    iverilog = run_iverilog(name, rtl, top, extra=case.get("iverilog_extra"))  # type: ignore[arg-type]
    summary = run_sta_lite(name, rtl, top, extra=case.get("sta_extra"))  # type: ignore[arg-type]
    iverilog_ok = iverilog.returncode == 0
    if iverilog_ok != bool(case["expect_iverilog_ok"]):
        raise SystemExit(f"{name} 的 iverilog gold 结果与预期不符：returncode={iverilog.returncode}\n{iverilog.stdout}")
    sta_has_error = int(summary.get("error_count", 0)) > 0 or int(summary.get("unsupported_count", 0)) > 0
    if iverilog_ok and sta_has_error:
        raise SystemExit(f"{name}：iverilog 通过，但 sta-lite lint 报 error/unsupported：{summary}")
    if not iverilog_ok and not sta_has_error:
        raise SystemExit(
            f"{name}：iverilog gold 报错，但 sta-lite lint 未报 error/unsupported。\n"
            f"iverilog 输出：\n{iverilog.stdout}\nsta-lite summary：{summary}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
