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


def get_json(url: str) -> dict[str, object]:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def post_json_expect_bad_request(url: str, payload: dict[str, object]) -> dict[str, object]:
    try:
        post_json(url, payload)
    except urllib.error.HTTPError as exc:
        if exc.code != 400:
            raise SystemExit(f"GUI API 错误状态码不正确：{exc.code}") from exc
        return json.loads(exc.read().decode("utf-8"))
    raise SystemExit("GUI API 未拒绝无效输入")


def read_sse_until_done(url: str) -> tuple[bool, dict[str, object] | None]:
    saw_log = False
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
            if current_event in {"summary", "error"}:
                final_payload = payload
                break
    return saw_log, final_payload


def main() -> int:
    os.chdir(ROOT)
    port = find_port()
    base_url = f"http://127.0.0.1:{port}/"
    process = subprocess.Popen(
        [sys.executable, "-m", "sta_lite.gui.server", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        wait_ready(base_url, process)
        invalid = post_json_expect_bad_request(
            base_url + "api/run",
            {
                "top": "multi_top",
                "rtl": ["examples/multi_file/rtl/*.v"],
                "clock": "clk",
                "period": "abc",
                "liberty_file": "nangate45/lib/NangateOpenCellLibrary_typical.lib",
                "out_dir": "runs/gui_api_invalid",
                "yosys_bin": "yosys",
                "sta_bin": "sta",
            },
        )
        if "时钟周期必须是数字" not in str(invalid.get("error", "")):
            raise SystemExit(f"GUI API 无效周期错误不是中文可操作提示：{invalid}")
        payload = {
            "top": "multi_top",
            "rtl": ["examples/multi_file/rtl/*.v"],
            "clock": "clk",
            "period": "2.5",
            "liberty_file": "nangate45/lib/NangateOpenCellLibrary_typical.lib",
            "out_dir": "runs/gui_api_smoke_multi_file",
            "yosys_bin": "yosys",
            "sta_bin": "sta",
        }
        job = post_json(base_url + "api/run", payload)
        job_id = str(job["job_id"])
        saw_log, final_payload = read_sse_until_done(base_url + f"api/events?id={job_id}")
        if not saw_log:
            raise SystemExit("GUI SSE 没有收到实时 log 事件")
        if not final_payload or "summary" not in final_payload:
            raise SystemExit("GUI SSE 没有收到 summary 事件")
        snapshot = get_json(base_url + f"api/jobs/{job_id}")
        if snapshot.get("status") != "success":
            raise SystemExit(f"GUI API 分析未成功：{snapshot}")
        summary = snapshot.get("summary")
        if not isinstance(summary, dict):
            raise SystemExit("GUI API 没有返回 summary")
        for key in ("wns", "tns", "risk_level", "elapsed_seconds", "generated_netlist"):
            if key not in summary:
                raise SystemExit(f"GUI summary 缺少字段：{key}")
        if len(summary.get("rtl_files", [])) < 4:
            raise SystemExit("GUI summary 没有记录多个 RTL 文件")
        if not summary.get("worst_paths"):
            raise SystemExit("GUI summary 没有解析到 worst_paths")
        print("[gui_api_smoke] GUI API 启动多 RTL 分析、实时日志和 summary 校验通过。")
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
