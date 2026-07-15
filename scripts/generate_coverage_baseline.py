#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sta_lite.review.baseline import render_coverage_baseline  # noqa: E402
from sta_lite.review.case_registry import case_registry, coverage_summary  # noqa: E402


TARGET = ROOT / "risk_profile" / "COVERAGE_BASELINE.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="生成或校验 P0/P1 中文覆盖基线。")
    parser.add_argument("--check", action="store_true", help="只校验已有基线是否与登记表一致。")
    parser.add_argument("--stdout", action="store_true", help="把生成内容输出到标准输出。")
    args = parser.parse_args()
    cases = case_registry(ROOT)
    content = render_coverage_baseline(cases, coverage_summary(cases))
    if args.stdout:
        print(content, end="")
        return 0
    if args.check:
        actual = TARGET.read_text(encoding="utf-8") if TARGET.is_file() else ""
        if actual != content:
            print(f"[coverage_baseline] 基线已过期：{TARGET}", file=sys.stderr)
            return 1
        print(f"[coverage_baseline] 中文覆盖基线与 29 项登记表一致：{TARGET}")
        return 0
    TARGET.write_text(content, encoding="utf-8")
    print(f"[coverage_baseline] 已生成中文覆盖基线：{TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
