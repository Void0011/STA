from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MUST_CASES = {
    "async_reset_release_unsync": "RISK_ASYNC_RESET_RELEASE_UNSYNC",
    "long_comb_path": "RISK_LONG_COMB_PATH",
    "latch_inference_timing": "RISK_LATCH_TIMING",
    "high_fanout_control": "RISK_HIGH_FANOUT_CONTROL",
    "gated_or_derived_clock": "RISK_GATED_OR_DERIVED_CLOCK",
}


def find_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_ready(base_url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 10
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise SystemExit(f"GUI 服务提前退出：\n{output}")
        try:
            with urllib.request.urlopen(base_url, timeout=1) as response:
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            time.sleep(0.2)
    raise SystemExit(f"GUI 服务未就绪：{last_error}")


def post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def get_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def get_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.read().decode("utf-8")


def read_sse_until_done(url: str) -> tuple[bool, bool, dict[str, object] | None]:
    saw_log = False
    saw_elapsed = False
    current_event = "message"
    final_payload: dict[str, object] | None = None
    with urllib.request.urlopen(url, timeout=20) as response:
        for raw_line in response:
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            if line.startswith("event:"):
                current_event = line.split(":", 1)[1].strip()
                continue
            if not line.startswith("data:"):
                continue
            payload = json.loads(line.split(":", 1)[1].strip())
            if current_event == "log":
                saw_log = True
            if current_event == "elapsed":
                saw_elapsed = True
            if current_event in {"summary", "error"}:
                final_payload = payload
                break
    return saw_log, saw_elapsed, final_payload


def load_case_payload(case_name: str, out_suffix: str, gold_dir: Path | None = None) -> dict[str, object]:
    case_dir = ROOT / "risk_profile" / "cases" / case_name
    meta = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    payload: dict[str, object] = {
        "top": meta["top"],
        "rtl": [str(case_dir / str(item)) for item in meta["files"]],
        "out_dir": str(ROOT / "runs" / f"gui_risk_api_{out_suffix}"),
    }
    if meta.get("sdc"):
        payload["sdc_file"] = str(case_dir / str(meta["sdc"]))
    if gold_dir is not None:
        payload["gold_dir"] = str(gold_dir)
    return payload


def run_risk_case(base_url: str, case_name: str, expected_rule: str, out_suffix: str, gold_dir: Path | None = None) -> dict[str, object]:
    job = post_json(base_url + "api/risk_run", load_case_payload(case_name, out_suffix, gold_dir=gold_dir))
    job_id = str(job["job_id"])
    saw_log, _saw_elapsed, final_payload = read_sse_until_done(base_url + f"api/risk_events?id={job_id}")
    if not saw_log:
        raise SystemExit(f"GUI Risk SSE 未收到实时 log 事件：{case_name}")
    if not final_payload or "summary" not in final_payload:
        raise SystemExit(f"GUI Risk SSE 未收到 summary 事件：{case_name}")
    snapshot = get_json(base_url + f"api/risk_jobs/{job_id}")
    if snapshot.get("status") != "success":
        raise SystemExit(f"GUI Risk 任务未成功：{snapshot}")
    summary = snapshot.get("summary")
    if not isinstance(summary, dict):
        raise SystemExit("GUI Risk API 没有返回 summary")
    rules = {item.get("rule") for item in summary.get("risks", []) if isinstance(item, dict)}
    if expected_rule not in rules:
        raise SystemExit(f"{case_name} 未触发期望风险 {expected_rule}，实际：{sorted(rules)}")
    artifacts = summary.get("artifacts")
    if not isinstance(artifacts, dict):
        raise SystemExit(f"{case_name} summary 缺少 artifacts")
    for key in ("risk_summary_json", "risk_report_md", "risk_log"):
        path = Path(str(artifacts.get(key) or ""))
        if not path.is_file():
            raise SystemExit(f"{case_name} 未生成 {key}：{path}")
    return summary


def main() -> int:
    os.chdir(ROOT)
    port = find_port()
    base_url = f"http://127.0.0.1:{port}/"
    env = os.environ.copy()
    env["PATH"] = "/tmp/sta-lite-no-external-eda-tools"
    process = subprocess.Popen(
        [sys.executable, "-m", "sta_lite.gui.server", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    try:
        wait_ready(base_url, process)
        html = get_text(base_url)
        for marker in ("riskCaseSelect", "riskLoadCase", "riskRuleFilter", "riskSeverityFilter", "backendToolStatus"):
            if marker not in html:
                raise SystemExit(f"GUI Risk 页面缺少控件：{marker}")
        backend = get_json(base_url + "api/backend_status")
        if backend.get("available") is not False or backend.get("status") != "unavailable_optional":
            raise SystemExit(f"无工具 PATH 下 Backend 应返回中文可选工具不可用状态：{backend}")
        if "RTL Review" not in str(backend.get("message_zh") or ""):
            raise SystemExit(f"Backend 状态未说明核心页面仍可用：{backend}")
        risk_cases = get_json(base_url + "api/risk_cases")
        cases = risk_cases.get("cases")
        if not isinstance(cases, list) or len(cases) < 11:
            raise SystemExit(f"GUI Risk 用例发现数量不正确：{risk_cases}")
        categories = {item.get("category") for item in cases if isinstance(item, dict)}
        missing_categories = set(MUST_CASES) - categories
        if missing_categories:
            raise SystemExit(f"GUI Risk 用例发现缺少必测目录：{sorted(missing_categories)}")

        missing_gold_summary = run_risk_case(
            base_url,
            "async_reset_release_unsync",
            "RISK_ASYNC_RESET_RELEASE_UNSYNC",
            "async_reset_missing_gold",
        )
        gold = missing_gold_summary.get("gold_compare")
        if not isinstance(gold, dict) or gold.get("available") is not False:
            raise SystemExit(f"缺失 gold 时应正常跳过对比：{gold}")

        gold_dir = ROOT / "runs" / "gui_risk_api_gold"
        gold_dir.mkdir(parents=True, exist_ok=True)
        gold_file = gold_dir / "opensta_fake.rpt"
        gold_file.write_text("critical path\nslack -0.125\nfanout warning\n", encoding="utf-8")
        gold_summary = run_risk_case(base_url, "long_comb_path", "RISK_LONG_COMB_PATH", "long_comb_with_gold", gold_dir=gold_file)
        gold_compare = gold_summary.get("gold_compare")
        if not isinstance(gold_compare, dict) or gold_compare.get("available") is not True:
            raise SystemExit(f"提供单个 gold 报告文件时应输出可用对比：{gold_compare}")

        for case_name, expected_rule in MUST_CASES.items():
            if case_name in {"async_reset_release_unsync", "long_comb_path"}:
                continue
            run_risk_case(base_url, case_name, expected_rule, case_name)

        print("[risk_gui_api_smoke] GUI Risk API、实时日志、summary、gold 对比和必测风险规则校验通过。")
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
