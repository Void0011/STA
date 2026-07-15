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


def post_json(url: str, payload: dict[str, object], expect_ok: bool = True) -> dict[str, object]:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode("utf-8"))
        if expect_ok:
            raise
        return body


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
    with urllib.request.urlopen(url, timeout=30) as response:
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
        for marker in (
            "navReview",
            "navLint",
            "navProfiling",
            "navBackend",
            "navCoverage",
            "RTL Review",
            "RTL Lint",
            "RTL Timing Risk Profiling",
            "Yosys/OpenSTA Backend Analysis",
            "Case Coverage",
            "reviewRunBtn",
            "reviewPriorityFilter",
            "reviewRuleFilter",
            "reviewCategoryFilter",
            "reviewFileFilter",
            "reviewReportLocationStatus",
            "coveragePriorityFilter",
            "coverageOwnerFilter",
            "coverageCategoryFilter",
            "coverageStatusFilter",
            "coverageRows",
            "backendToolStatus",
        ):
            if marker not in html:
                raise SystemExit(f"GUI 页面缺少五页面/筛选标记：{marker}")

        coverage = get_json(base_url + "api/case_coverage")
        cases = coverage.get("cases")
        coverage_summary = coverage.get("summary")
        p0 = coverage.get("p0_coverage")
        p1 = coverage.get("p1_roadmap")
        location = coverage.get("report_location_status")
        if not isinstance(cases, list) or len(cases) != 29:
            raise SystemExit(f"Case Coverage 注册表数量不正确：{coverage}")
        if not isinstance(p0, list) or len(p0) != 17:
            raise SystemExit(f"P0 覆盖状态数量不正确：{coverage}")
        if not isinstance(p1, list) or len(p1) != 12:
            raise SystemExit(f"P1 路线图数量不正确：{coverage}")
        if not isinstance(coverage_summary, dict) or coverage_summary.get("total") != 29:
            raise SystemExit(f"Case Coverage 汇总数量不正确：{coverage_summary}")
        priorities = coverage_summary.get("priorities")
        if not isinstance(priorities, dict) or priorities.get("P0", {}).get("total") != 17:
            raise SystemExit(f"Case Coverage P0 汇总不正确：{priorities}")
        if priorities.get("P1", {}).get("total") != 12:
            raise SystemExit(f"Case Coverage P1 汇总不正确：{priorities}")
        if priorities.get("P1", {}).get("supported") != 12 or priorities.get("P1", {}).get("coverage_percent") != 100.0:
            raise SystemExit(f"Case Coverage P1 应为 12/12 supported：{priorities}")
        valid_statuses = {"supported", "partially_supported", "unsupported_diagnostic", "unsupported_by_design", "not_covered"}
        if {item.get("support_status") for item in cases} - valid_statuses:
            raise SystemExit("Case Coverage 出现非法支持状态。")
        comb_loop = next((item for item in cases if item.get("case_id") == "P0_COMBINATIONAL_LOOP"), None)
        if not isinstance(comb_loop, dict) or comb_loop.get("support_status") != "supported":
            raise SystemExit(f"P0_COMBINATIONAL_LOOP 应显示为 supported：{comb_loop}")
        fsm_case = next((item for item in cases if item.get("case_id") == "P0_FSM_ROBUSTNESS"), None)
        if not isinstance(fsm_case, dict) or fsm_case.get("support_status") != "partially_supported":
            raise SystemExit(f"P0_FSM_ROBUSTNESS 应显示为 partially_supported：{fsm_case}")
        supported = [item for item in cases if item.get("support_status") == "supported"]
        if not supported or any(not item.get("verification_evidence") for item in supported):
            raise SystemExit("supported Case 必须带验证证据。")
        if any(not item.get("latest_verification_evidence") for item in supported):
            raise SystemExit("supported Case 必须带最新验证证据。")
        if not isinstance(location, dict) or location.get("status") != "todo":
            raise SystemExit(f"报告反向定位状态应明确暴露 TODO：{location}")

        backend_error = post_json(
            base_url + "api/run",
            {
                "top": "top",
                "rtl": ["risk_profile/cases/long_comb_path/long_comb_path.v"],
                "liberty_file": "",
                "clock": "clk",
                "period": "2.0",
                "out_dir": "runs/gui_review_backend_probe",
            },
            expect_ok=False,
        )
        if "启动分析失败" not in str(backend_error.get("error")):
            raise SystemExit(f"后端分析 API 应保留中文错误处理：{backend_error}")

        payload = {
            "top": "top",
            "rtl": ["risk_profile/cases/long_comb_path/long_comb_path.v"],
            "gold_dir": "",
            "out_dir": "runs/gui_review_api_long_comb",
        }
        job = post_json(base_url + "api/review_run", payload)
        job_id = str(job["job_id"])
        saw_log, saw_elapsed, final_payload = read_sse_until_done(base_url + f"api/review_events?id={job_id}")
        if not saw_log:
            raise SystemExit("GUI RTL Review SSE 未收到实时 log 事件")
        if not final_payload or "summary" not in final_payload:
            raise SystemExit("GUI RTL Review SSE 未收到 summary 事件")
        snapshot = get_json(base_url + f"api/review_jobs/{job_id}")
        if snapshot.get("status") != "success":
            raise SystemExit(f"GUI RTL Review 任务未成功：{snapshot}")
        summary = snapshot.get("summary")
        if not isinstance(summary, dict):
            raise SystemExit("GUI RTL Review API 没有返回 summary")
        rules = {item.get("rule") for item in summary.get("items", []) if isinstance(item, dict)}
        if "RISK_LONG_COMB_PATH" not in rules:
            raise SystemExit(f"RTL Review 未合并 long_comb 风险：{sorted(rules)}")
        if int(summary.get("risk_count", 0)) < 1:
            raise SystemExit(f"RTL Review risk_count 不正确：{summary}")
        if "lint_issue_count" not in summary or "total_issue_count" not in summary:
            raise SystemExit(f"RTL Review summary 缺少计数字段：{summary}")
        subflows = summary.get("subflows")
        if not isinstance(subflows, dict):
            raise SystemExit(f"RTL Review summary 缺少独立子流程状态：{summary}")
        if subflows.get("lint", {}).get("status") != "success":
            raise SystemExit(f"RTL Review Lint 子流程状态不正确：{subflows}")
        if subflows.get("profiling", {}).get("status") != "success":
            raise SystemExit(f"RTL Review Profiling 子流程状态不正确：{subflows}")
        review_items = [item for item in summary.get("items", []) if isinstance(item, dict)]
        long_comb_items = [item for item in review_items if item.get("case_id") == "P0_LONG_COMBINATIONAL_PATH"]
        if not long_comb_items:
            raise SystemExit("RTL Review 结果缺少 P0/Case ID 归类。")
        if not any(item.get("source") == "profiling" for item in long_comb_items):
            raise SystemExit("RTL Review 结果缺少 profiling 来源。")
        if any(not item.get("correlation_id") for item in review_items):
            raise SystemExit("RTL Review 结果缺少重复/重叠诊断关联标识。")
        if not isinstance(summary.get("p0_coverage"), list) or not isinstance(summary.get("p1_roadmap"), list):
            raise SystemExit("RTL Review summary 缺少 P0/P1 状态")
        artifacts = summary.get("artifacts")
        if not isinstance(artifacts, dict):
            raise SystemExit("RTL Review summary 缺少 artifacts")
        for key in ("review_summary_json", "review_report_md", "review_log", "lint_summary_json", "risk_summary_json", "risk_report_md"):
            path = Path(str(artifacts.get(key) or ""))
            if not path.is_file():
                raise SystemExit(f"RTL Review 未生成 {key}：{path}")
        if saw_elapsed:
            print("[review_gui_api_smoke] 已接收 elapsed 事件。")
        print("[review_gui_api_smoke] 五页面、RTL Review API、实时日志、合并结果和 Case Coverage 校验通过。")
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
