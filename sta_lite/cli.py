from __future__ import annotations

import argparse
import json
import sys

from sta_lite import __version__
from sta_lite.core.errors import UserError
from sta_lite.lint.workflow import LintConfig, run_lint
from sta_lite.review.workflow import ReviewConfig, run_review
from sta_lite.risk.workflow import RiskConfig, run_risk


def log(message: str) -> None:
    print(message, flush=True)


def cmd_analyze(args: argparse.Namespace) -> int:
    from sta_lite.core.runner import AnalysisConfig, analyze

    config = AnalysisConfig(
        top=args.top,
        rtl=args.rtl,
        liberty_file=args.lib,
        out_dir=args.out,
        clock=args.clock,
        period=args.period,
        sdc_file=args.sdc,
        max_paths=args.max_paths,
        yosys_bin=args.yosys_bin,
        sta_bin=args.sta_bin,
    )
    analyze(config, on_log=log)
    return 0


def cmd_gui(args: argparse.Namespace) -> int:
    from sta_lite.gui.server import run_server

    run_server(host=args.host, port=args.port, open_browser=args.open_browser)
    return 0


def cmd_lint_diff(args: argparse.Namespace) -> int:
    from sta_lite.lint.diff_runner import main as lint_diff_main

    argv = ["--out", args.out, "--iverilog", args.iverilog]
    if args.cases:
        argv.append("--cases")
        argv.extend(args.cases)
    if args.write_corpus:
        argv.append("--write-corpus")
    return lint_diff_main(argv)


def parse_define(values: list[str]) -> dict[str, str]:
    defines: dict[str, str] = {}
    for item in values:
        if "=" in item:
            name, value = item.split("=", 1)
        else:
            name, value = item, "1"
        name = name.strip()
        if not name:
            raise UserError("--define 中存在空宏名。")
        defines[name] = value
    return defines


def cmd_lint(args: argparse.Namespace) -> int:
    config = LintConfig(
        rtl=args.rtl,
        out_dir=args.out,
        top=args.top,
        include_dirs=args.include,
        defines=parse_define(args.define),
        rules_file=args.rules,
        sdc_file=args.sdc,
        debug=args.debug,
    )
    summary = run_lint(config, on_log=log if args.format == "text" else None)
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_lint_summary(summary)
    if args.fail_on == "never":
        return 0
    if args.fail_on == "warning" and (summary["error_count"] or summary["warning_count"] or summary["unsupported_count"]):
        return 1
    if args.fail_on == "error" and (summary["error_count"] or summary["unsupported_count"]):
        return 1
    return 0


def cmd_risk(args: argparse.Namespace) -> int:
    config = RiskConfig(
        rtl=args.rtl,
        out_dir=args.out,
        top=args.top,
        sdc_file=args.sdc,
        include_dirs=args.include,
        defines=parse_define(args.define),
        gold_dir=args.gold_dir,
    )
    summary = run_risk(config, on_log=log if args.format == "text" else None)
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_risk_summary(summary)
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    config = ReviewConfig(
        rtl=args.rtl,
        out_dir=args.out,
        top=args.top,
        sdc_file=args.sdc,
        include_dirs=args.include,
        defines=parse_define(args.define),
        rules_file=args.rules,
        gold_dir=args.gold_dir,
        debug=args.debug,
    )
    summary = run_review(config, on_log=log if args.format == "text" else None)
    if args.format == "json":
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print_review_summary(summary)
    return 0


def print_lint_summary(summary: dict[str, object]) -> None:
    print("\n[sta-lite lint] 结果摘要")
    print(f"  通过：{'是' if summary.get('passed') else '否'}")
    print(f"  错误：{summary.get('error_count')}")
    print(f"  警告：{summary.get('warning_count')}")
    print(f"  信息：{summary.get('info_count')}")
    print(f"  暂不支持：{summary.get('unsupported_count')}")
    print(f"  风险等级：{summary.get('risk_level')}")
    print(f"  风险说明：{summary.get('risk_explanation_zh')}")
    print(f"  summary：{summary.get('artifacts', {}).get('lint_summary_json') if isinstance(summary.get('artifacts'), dict) else '-'}")
    diagnostics = summary.get("diagnostics")
    if isinstance(diagnostics, list) and diagnostics:
        print("\n[sta-lite lint] 诊断列表")
        for item in diagnostics[:80]:
            if not isinstance(item, dict):
                continue
            print(
                "  "
                f"[{item.get('severity')}] {item.get('rule')} "
                f"{item.get('file')}:{item.get('line')}:{item.get('column')} "
                f"{item.get('message_zh')}"
            )
            suggestion = item.get("suggestion_zh")
            if suggestion:
                print(f"      建议：{suggestion}")
        if len(diagnostics) > 80:
            print(f"  其余 {len(diagnostics) - 80} 条诊断请查看 lint_summary.json。")


def print_risk_summary(summary: dict[str, object]) -> None:
    print("\n[sta-lite risk] 结果摘要")
    print(f"  风险等级：{summary.get('risk_level')}")
    print(f"  风险数量：{summary.get('risk_count')}")
    print(f"  风险说明：{summary.get('risk_explanation_zh')}")
    print(f"  summary：{summary.get('artifacts', {}).get('risk_summary_json') if isinstance(summary.get('artifacts'), dict) else '-'}")
    print(f"  report：{summary.get('artifacts', {}).get('risk_report_md') if isinstance(summary.get('artifacts'), dict) else '-'}")
    risks = summary.get("risks")
    if isinstance(risks, list) and risks:
        print("\n[sta-lite risk] 风险列表")
        for item in risks[:80]:
            if not isinstance(item, dict):
                continue
            print(
                "  "
                f"[{item.get('severity')}] {item.get('rule')} "
                f"{item.get('file')}:{item.get('line')}:{item.get('column')} "
                f"{item.get('message_zh')}"
            )
            suggestion = item.get("suggestion_zh")
            if suggestion:
                print(f"      建议：{suggestion}")
        if len(risks) > 80:
            print(f"  其余 {len(risks) - 80} 条风险请查看 risk_summary.json。")


def print_review_summary(summary: dict[str, object]) -> None:
    print("\n[sta-lite review] 结果摘要")
    print(f"  运行状态：{summary.get('status')}")
    print(f"  整体等级：{summary.get('risk_level')}")
    print(f"  lint 问题数：{summary.get('lint_issue_count')}")
    print(f"  risk 风险数：{summary.get('risk_count')}")
    print(f"  总问题数：{summary.get('total_issue_count')}")
    print(f"  说明：{summary.get('risk_explanation_zh')}")
    subflows = summary.get("subflows")
    if isinstance(subflows, dict):
        for name, label in (("lint", "RTL Lint"), ("profiling", "RTL Timing Risk Profiling")):
            item = subflows.get(name)
            if not isinstance(item, dict):
                continue
            print(
                f"  {label}：{item.get('status')}，"
                f"耗时 {item.get('elapsed_seconds')} 秒，问题 {item.get('issue_count')}"
            )
            if item.get("error_zh"):
                print(f"    错误：{item.get('error_zh')}")
    artifacts = summary.get("artifacts")
    if isinstance(artifacts, dict):
        print(f"  review summary：{artifacts.get('review_summary_json') or '-'}")
        print(f"  review report：{artifacts.get('review_report_md') or '-'}")
    location = summary.get("report_location_status")
    if isinstance(location, dict):
        print(f"  报告反向定位：{location.get('message_zh')}")
    items = summary.get("items")
    if isinstance(items, list) and items:
        print("\n[sta-lite review] Lint/Risk 列表")
        for item in items[:80]:
            if not isinstance(item, dict):
                continue
            print(
                "  "
                f"[{item.get('source')}/{item.get('priority') or '-'}/{item.get('severity')}] "
                f"{item.get('case_id') or '-'} {item.get('rule')} "
                f"{item.get('file')}:{item.get('line')}:{item.get('column')} "
                f"{item.get('message_zh')}"
            )
            suggestion = item.get("suggestion_zh")
            if suggestion:
                print(f"      建议：{suggestion}")
        if len(items) > 80:
            print(f"  其余 {len(items) - 80} 条请查看 review_summary.json。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sta-lite",
        description="本地 STA-lite：RTL Review、内部 lint、RTL risk 和 Yosys/OpenSTA 后端参考分析",
    )
    parser.add_argument("--version", action="version", version=f"STA-Lite {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    lint_parser = subparsers.add_parser("lint", help="运行内部 Verilog/SystemVerilog lint，不调用外部 EDA 工具")
    lint_parser.add_argument("--rtl", nargs="+", required=True, help="RTL Verilog/SystemVerilog 文件或 glob")
    lint_parser.add_argument("--out", required=True, help="lint 输出目录")
    lint_parser.add_argument("--top", help="顶层模块名")
    lint_parser.add_argument("--include", action="append", default=[], help="预处理 include 搜索目录，可重复指定")
    lint_parser.add_argument("--define", action="append", default=[], help="预处理宏定义，例如 SYNTHESIS=1，可重复指定")
    lint_parser.add_argument("--rules", help="JSON 自定义 lint 规则文件")
    lint_parser.add_argument("--sdc", help="可选 SDC 文件，用于检查 create_clock 与 RTL 端口是否匹配")
    lint_parser.add_argument("--format", choices=["text", "json"], default="text", help="CLI 输出格式")
    lint_parser.add_argument("--fail-on", choices=["error", "warning", "never"], default="error", help="返回非零退出码的阈值")
    lint_parser.add_argument("--debug", action="store_true", help="额外输出 tokens.json 和 ast.json")
    lint_parser.set_defaults(func=cmd_lint)

    lint_diff_parser = subparsers.add_parser("lint-diff", help="运行 STA-lite lint、Verilog iverilog golden 和 SV metadata 差分回归")
    lint_diff_parser.add_argument("--cases", nargs="*", default=None, help="语料根目录；不指定时扫描四个 canonical root")
    lint_diff_parser.add_argument("--out", default="reports/lint_diff", help="差分报告输出目录")
    lint_diff_parser.add_argument("--iverilog", default="iverilog", help="iverilog 命令名或路径")
    lint_diff_parser.add_argument("--write-corpus", action="store_true", help="先生成内置错误语料")
    lint_diff_parser.set_defaults(func=cmd_lint_diff)

    risk_parser = subparsers.add_parser("risk", help="运行 RTL timing-risk profiling，不调用综合或 STA 工具")
    risk_parser.add_argument("--rtl", nargs="+", required=True, help="RTL Verilog/SystemVerilog 文件或 glob")
    risk_parser.add_argument("--out", required=True, help="risk 输出目录")
    risk_parser.add_argument("--top", help="顶层模块名")
    risk_parser.add_argument("--sdc", help="可选 SDC 文件，用于检查约束相关风险")
    risk_parser.add_argument("--include", action="append", default=[], help="预处理 include 搜索目录，可重复指定")
    risk_parser.add_argument("--define", action="append", default=[], help="预处理宏定义，例如 SYNTHESIS=1，可重复指定")
    risk_parser.add_argument("--gold-dir", default="risk_profile/gold/opensta", help="可选 OpenSTA/backend gold 报告目录")
    risk_parser.add_argument("--format", choices=["text", "json"], default="text", help="CLI 输出格式")
    risk_parser.set_defaults(func=cmd_risk)

    review_parser = subparsers.add_parser("review", help="运行 RTL Review：协调 lint_v0 和 RTL risk，不调用后端 EDA 工具")
    review_parser.add_argument("--rtl", nargs="+", required=True, help="RTL Verilog/SystemVerilog 文件或 glob")
    review_parser.add_argument("--out", required=True, help="review 输出目录")
    review_parser.add_argument("--top", help="顶层模块名")
    review_parser.add_argument("--sdc", help="可选 SDC 文件，用于约束一致性和风险提示")
    review_parser.add_argument("--include", action="append", default=[], help="预处理 include 搜索目录，可重复指定")
    review_parser.add_argument("--define", action="append", default=[], help="预处理宏定义，例如 SYNTHESIS=1，可重复指定")
    review_parser.add_argument("--rules", help="JSON 自定义 lint 规则文件")
    review_parser.add_argument("--gold-dir", default=None, help="可选 OpenSTA/backend gold 报告文件或目录，仅用于相关性对比")
    review_parser.add_argument("--format", choices=["text", "json"], default="text", help="CLI 输出格式")
    review_parser.add_argument("--debug", action="store_true", help="lint 阶段额外输出 tokens.json 和 ast.json")
    review_parser.set_defaults(func=cmd_review)

    analyze_parser = subparsers.add_parser("analyze", help="运行一次 RTL 到 STA summary 的分析")
    analyze_parser.add_argument("--top", required=True, help="顶层模块名")
    analyze_parser.add_argument("--rtl", nargs="+", required=True, help="RTL Verilog 文件或 glob，例如 'src/*.v'")
    analyze_parser.add_argument("--lib", required=True, help="Liberty .lib 文件")
    analyze_parser.add_argument("--out", required=True, help="输出目录")
    analyze_parser.add_argument("--clock", help="自动生成 SDC 时使用的时钟端口/时钟名")
    analyze_parser.add_argument("--period", type=float, help="自动生成 SDC 时使用的时钟周期，单位 ns")
    analyze_parser.add_argument("--sdc", help="用户提供的 SDC 文件；提供后不再自动生成 clock")
    analyze_parser.add_argument("--max-paths", type=int, default=5, help="OpenSTA report_checks 最大路径数量")
    analyze_parser.add_argument("--yosys-bin", default="yosys", help="Yosys 可执行文件名或路径")
    analyze_parser.add_argument("--sta-bin", default="sta", help="OpenSTA 可执行文件名或路径")
    analyze_parser.set_defaults(func=cmd_analyze)

    gui_parser = subparsers.add_parser("gui", help="启动本地 STA-lite Web GUI")
    gui_parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    gui_parser.add_argument("--port", type=int, default=8765, help="监听端口")
    gui_parser.add_argument("--open-browser", action="store_true", help="GUI 启动后自动打开默认浏览器")
    gui_parser.set_defaults(func=cmd_gui)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except UserError as exc:
        print(f"[sta-lite] 错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
