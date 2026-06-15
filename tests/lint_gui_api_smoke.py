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


def read_sse_until_done(url: str) -> tuple[bool, dict[str, object] | None]:
    saw_log = False
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
            if current_event in {"summary", "error"}:
                final_payload = payload
                break
    return saw_log, final_payload


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
        payload = {
            "top": "latch_risk",
            "rtl": ["examples/lint/latch_risk/latch_risk.sv"],
            "out_dir": "runs/gui_lint_api_smoke",
        }
        job = post_json(base_url + "api/lint_run", payload)
        job_id = str(job["job_id"])
        saw_log, final_payload = read_sse_until_done(base_url + f"api/lint_events?id={job_id}")
        if not saw_log:
            raise SystemExit("GUI Lint SSE 没有收到实时 log 事件")
        if not final_payload or "summary" not in final_payload:
            raise SystemExit("GUI Lint SSE 没有收到 summary 事件")
        summary = final_payload["summary"]
        if not isinstance(summary, dict):
            raise SystemExit("GUI Lint summary 格式不正确")
        rules = {item.get("rule") for item in summary.get("diagnostics", []) if isinstance(item, dict)}
        if "RTL003_LATCH_RISK" not in rules:
            raise SystemExit(f"GUI Lint 没有触发 latch 风险规则：{summary}")
        print("[lint_gui_api_smoke] GUI Lint API、实时日志和 summary 校验通过。")
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())

