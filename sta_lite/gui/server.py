from __future__ import annotations

import json
import argparse
import errno
import queue
import threading
import time
import uuid
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from sta_lite.core.runner import AnalysisConfig, ProcessController, UserError, analyze
from sta_lite.lint.workflow import LintConfig, run_lint
from sta_lite.parsers.reports import read_text


STATIC_DIR = Path(__file__).resolve().parent / "static"


@dataclass
class GuiJob:
    job_id: str
    config: AnalysisConfig
    events: "queue.Queue[dict[str, Any]]" = field(default_factory=queue.Queue)
    controller: ProcessController = field(default_factory=ProcessController)
    status: str = "queued"
    summary: dict[str, Any] | None = None
    error: str | None = None
    started_at: float = field(default_factory=time.monotonic)
    finished_at: float | None = None

    def elapsed(self) -> float:
        end = self.finished_at if self.finished_at is not None else time.monotonic()
        return max(0.0, end - self.started_at)


class JobManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, GuiJob] = {}

    def create(self, payload: dict[str, Any]) -> GuiJob:
        config = self._config_from_payload(payload)
        job = GuiJob(job_id=uuid.uuid4().hex[:12], config=config)
        with self._lock:
            self._jobs[job.job_id] = job
        thread = threading.Thread(target=self._run_job, args=(job,), daemon=True)
        thread.start()
        return job

    def get(self, job_id: str) -> GuiJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def stop(self, job_id: str) -> bool:
        job = self.get(job_id)
        if not job:
            return False
        job.controller.request_stop()
        job.events.put({"type": "log", "line": "[sta-lite] 已请求停止当前分析。"})
        return True

    def snapshot(self, job: GuiJob) -> dict[str, Any]:
        return {
            "job_id": job.job_id,
            "status": job.status,
            "elapsed_seconds": round(job.elapsed(), 3),
            "summary": job.summary,
            "error": job.error,
            "out_dir": str(Path(job.config.out_dir).resolve()),
        }

    def _run_job(self, job: GuiJob) -> None:
        job.status = "running"
        job.events.put({"type": "status", "status": "running", "message": "分析运行中。"})

        def on_log(line: str) -> None:
            job.events.put({"type": "log", "line": line, "elapsed_seconds": round(job.elapsed(), 3)})

        try:
            summary = analyze(job.config, on_log=on_log, controller=job.controller)
            job.summary = summary
            job.status = "success"
            job.finished_at = time.monotonic()
            job.events.put({"type": "summary", "summary": summary, "elapsed_seconds": round(job.elapsed(), 3)})
        except UserError as exc:
            job.error = str(exc)
            job.status = "failure"
            job.finished_at = time.monotonic()
            job.summary = self._read_summary_if_exists(job)
            job.events.put(
                {
                    "type": "error",
                    "message": job.error,
                    "summary": job.summary,
                    "elapsed_seconds": round(job.elapsed(), 3),
                }
            )
        except Exception as exc:  # noqa: BLE001 - GUI must surface unexpected failures.
            job.error = f"内部错误：{exc}"
            job.status = "failure"
            job.finished_at = time.monotonic()
            job.summary = self._read_summary_if_exists(job)
            job.events.put(
                {
                    "type": "error",
                    "message": job.error,
                    "summary": job.summary,
                    "elapsed_seconds": round(job.elapsed(), 3),
                }
            )

    def _read_summary_if_exists(self, job: GuiJob) -> dict[str, Any] | None:
        summary_path = Path(job.config.out_dir) / "summary.json"
        try:
            text = read_text(summary_path)
            return json.loads(text) if text else None
        except json.JSONDecodeError:
            return None

    def _config_from_payload(self, payload: dict[str, Any]) -> AnalysisConfig:
        rtl = payload.get("rtl") or []
        if isinstance(rtl, str):
            rtl = [item.strip() for item in rtl.replace(",", "\n").splitlines() if item.strip()]
        clock = (payload.get("clock") or "").strip() or None
        period_raw = payload.get("period")
        if period_raw in (None, ""):
            period = None
        else:
            try:
                period = float(period_raw)
            except (TypeError, ValueError) as exc:
                raise UserError("时钟周期必须是数字。") from exc
        sdc = (payload.get("sdc") or "").strip() or None
        top = (payload.get("top") or "").strip()
        liberty_file = (payload.get("liberty_file") or "").strip()
        out_dir = (payload.get("out_dir") or "").strip()
        yosys_bin = (payload.get("yosys_bin") or "yosys").strip()
        sta_bin = (payload.get("sta_bin") or "sta").strip()
        if not top:
            raise UserError("请填写顶层模块。")
        if not rtl:
            raise UserError("请至少填写一个 RTL Verilog 文件或 glob。")
        if not liberty_file:
            raise UserError("请填写 Liberty 文件路径。")
        if not out_dir:
            raise UserError("请填写输出目录。")
        if not yosys_bin:
            raise UserError("请填写 Yosys 命令。")
        if not sta_bin:
            raise UserError("请填写 OpenSTA 命令。")
        if not sdc:
            if not clock or period is None:
                raise UserError("未提供 SDC 时必须同时提供时钟名和时钟周期。")
            if period <= 0:
                raise UserError("时钟周期必须是正数。")
        try:
            max_paths = int(payload.get("max_paths") or 5)
        except (TypeError, ValueError) as exc:
            raise UserError("最大路径数量必须是整数。") from exc
        if max_paths <= 0:
            raise UserError("最大路径数量必须是正整数。")
        return AnalysisConfig(
            top=top,
            rtl=rtl,
            liberty_file=liberty_file,
            out_dir=out_dir,
            clock=clock,
            period=period,
            sdc_file=sdc,
            max_paths=max_paths,
            yosys_bin=yosys_bin,
            sta_bin=sta_bin,
            cwd=Path.cwd(),
        )


@dataclass
class LintGuiJob:
    job_id: str
    config: LintConfig
    events: "queue.Queue[dict[str, Any]]" = field(default_factory=queue.Queue)
    status: str = "queued"
    summary: dict[str, Any] | None = None
    error: str | None = None
    started_at: float = field(default_factory=time.monotonic)
    finished_at: float | None = None

    def elapsed(self) -> float:
        end = self.finished_at if self.finished_at is not None else time.monotonic()
        return max(0.0, end - self.started_at)


class LintJobManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, LintGuiJob] = {}

    def create(self, payload: dict[str, Any]) -> LintGuiJob:
        config = self._config_from_payload(payload)
        job = LintGuiJob(job_id=uuid.uuid4().hex[:12], config=config)
        with self._lock:
            self._jobs[job.job_id] = job
        thread = threading.Thread(target=self._run_job, args=(job,), daemon=True)
        thread.start()
        return job

    def get(self, job_id: str) -> LintGuiJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def snapshot(self, job: LintGuiJob) -> dict[str, Any]:
        return {
            "job_id": job.job_id,
            "status": job.status,
            "elapsed_seconds": round(job.elapsed(), 3),
            "summary": job.summary,
            "error": job.error,
            "out_dir": str(Path(job.config.out_dir).resolve()),
        }

    def _run_job(self, job: LintGuiJob) -> None:
        job.status = "running"
        job.events.put({"type": "status", "status": "running", "message": "RTL Lint 运行中。"})

        def on_log(line: str) -> None:
            job.events.put({"type": "log", "line": line, "elapsed_seconds": round(job.elapsed(), 3)})

        try:
            summary = run_lint(job.config, on_log=on_log)
            job.summary = summary
            job.status = "success"
            job.finished_at = time.monotonic()
            job.events.put({"type": "summary", "summary": summary, "elapsed_seconds": round(job.elapsed(), 3)})
        except UserError as exc:
            job.error = str(exc)
            job.status = "failure"
            job.finished_at = time.monotonic()
            job.summary = self._read_summary_if_exists(job)
            job.events.put({"type": "error", "message": job.error, "summary": job.summary, "elapsed_seconds": round(job.elapsed(), 3)})
        except Exception as exc:  # noqa: BLE001 - GUI must surface unexpected failures.
            job.error = f"内部错误：{exc}"
            job.status = "failure"
            job.finished_at = time.monotonic()
            job.summary = self._read_summary_if_exists(job)
            job.events.put({"type": "error", "message": job.error, "summary": job.summary, "elapsed_seconds": round(job.elapsed(), 3)})

    def _read_summary_if_exists(self, job: LintGuiJob) -> dict[str, Any] | None:
        summary_path = Path(job.config.out_dir) / "lint_summary.json"
        try:
            text = read_text(summary_path)
            return json.loads(text) if text else None
        except json.JSONDecodeError:
            return None

    def _config_from_payload(self, payload: dict[str, Any]) -> LintConfig:
        rtl = _split_path_list(payload.get("rtl") or [])
        include_dirs = _split_path_list(payload.get("include_dirs") or [])
        define_items = _split_path_list(payload.get("defines") or [])
        top = (payload.get("top") or "").strip() or None
        out_dir = (payload.get("out_dir") or "").strip()
        rules_file = (payload.get("rules_file") or "").strip() or None
        sdc_file = (payload.get("sdc_file") or "").strip() or None
        if not rtl:
            raise UserError("请至少填写一个 RTL Verilog/SystemVerilog 文件或 glob。")
        if not out_dir:
            raise UserError("请填写 lint 输出目录。")
        defines: dict[str, str] = {}
        for item in define_items:
            if "=" in item:
                name, value = item.split("=", 1)
            else:
                name, value = item, "1"
            name = name.strip()
            if not name:
                raise UserError("宏定义中存在空宏名。")
            defines[name] = value
        return LintConfig(
            rtl=rtl,
            out_dir=out_dir,
            top=top,
            include_dirs=include_dirs,
            defines=defines,
            rules_file=rules_file,
            sdc_file=sdc_file,
            debug=bool(payload.get("debug") or False),
            cwd=Path.cwd(),
        )


def _split_path_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [item.strip() for item in value.replace(",", "\n").splitlines() if item.strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


MANAGER = JobManager()
LINT_MANAGER = LintJobManager()


class StaLiteGuiHandler(BaseHTTPRequestHandler):
    server_version = "STA-lite-GUI/0.1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_static("index.html")
            return
        if parsed.path.startswith("/static/"):
            self._send_static(parsed.path.removeprefix("/static/"))
            return
        if parsed.path == "/api/events":
            self._handle_events(parsed.query)
            return
        if parsed.path == "/api/lint_events":
            self._handle_lint_events(parsed.query)
            return
        if parsed.path.startswith("/api/jobs/"):
            self._handle_job(parsed.path.rsplit("/", 1)[-1])
            return
        if parsed.path.startswith("/api/lint_jobs/"):
            self._handle_lint_job(parsed.path.rsplit("/", 1)[-1])
            return
        self._send_json({"error": "未找到请求的资源。"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/run":
            self._handle_run()
            return
        if parsed.path == "/api/lint_run":
            self._handle_lint_run()
            return
        if parsed.path.startswith("/api/stop/"):
            job_id = parsed.path.rsplit("/", 1)[-1]
            stopped = MANAGER.stop(job_id)
            status = HTTPStatus.OK if stopped else HTTPStatus.NOT_FOUND
            self._send_json({"stopped": stopped}, status=status)
            return
        self._send_json({"error": "未找到请求的资源。"}, status=HTTPStatus.NOT_FOUND)

    def _handle_run(self) -> None:
        try:
            payload = self._read_json()
            job = MANAGER.create(payload)
            self._send_json(MANAGER.snapshot(job), status=HTTPStatus.CREATED)
        except Exception as exc:  # noqa: BLE001 - show actionable GUI error.
            self._send_json({"error": f"启动分析失败：{exc}"}, status=HTTPStatus.BAD_REQUEST)

    def _handle_lint_run(self) -> None:
        try:
            payload = self._read_json()
            job = LINT_MANAGER.create(payload)
            self._send_json(LINT_MANAGER.snapshot(job), status=HTTPStatus.CREATED)
        except Exception as exc:  # noqa: BLE001 - show actionable GUI error.
            self._send_json({"error": f"启动 RTL Lint 失败：{exc}"}, status=HTTPStatus.BAD_REQUEST)

    def _handle_job(self, job_id: str) -> None:
        job = MANAGER.get(job_id)
        if not job:
            self._send_json({"error": "找不到该分析任务。"}, status=HTTPStatus.NOT_FOUND)
            return
        self._send_json(MANAGER.snapshot(job))

    def _handle_lint_job(self, job_id: str) -> None:
        job = LINT_MANAGER.get(job_id)
        if not job:
            self._send_json({"error": "找不到该 RTL Lint 任务。"}, status=HTTPStatus.NOT_FOUND)
            return
        self._send_json(LINT_MANAGER.snapshot(job))

    def _handle_events(self, query: str) -> None:
        params = parse_qs(query)
        job_id = (params.get("id") or [""])[0]
        job = MANAGER.get(job_id)
        if not job:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        while True:
            try:
                event = job.events.get(timeout=1.0)
            except queue.Empty:
                event = {
                    "type": "elapsed",
                    "elapsed_seconds": round(job.elapsed(), 3),
                    "status": job.status,
                }
            self._write_sse(event["type"], event)
            if event["type"] in {"summary", "error"}:
                break

    def _handle_lint_events(self, query: str) -> None:
        params = parse_qs(query)
        job_id = (params.get("id") or [""])[0]
        job = LINT_MANAGER.get(job_id)
        if not job:
            self.send_response(HTTPStatus.NOT_FOUND)
            self.end_headers()
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        while True:
            try:
                event = job.events.get(timeout=1.0)
            except queue.Empty:
                event = {
                    "type": "elapsed",
                    "elapsed_seconds": round(job.elapsed(), 3),
                    "status": job.status,
                }
            self._write_sse(event["type"], event)
            if event["type"] in {"summary", "error"}:
                break

    def _write_sse(self, event_name: str, payload: dict[str, Any]) -> None:
        body = f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"
        self.wfile.write(body.encode("utf-8"))
        self.wfile.flush()

    def _send_static(self, relative_path: str) -> None:
        target = (STATIC_DIR / relative_path).resolve()
        if not str(target).startswith(str(STATIC_DIR.resolve())) or not target.is_file():
            self._send_json({"error": "静态资源不存在。"}, status=HTTPStatus.NOT_FOUND)
            return
        content_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
        }
        data = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_types.get(target.suffix, "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    try:
        server = ThreadingHTTPServer((host, port), StaLiteGuiHandler)
    except OSError as exc:
        if exc.errno == errno.EADDRINUSE:
            raise UserError(
                f"GUI 启动失败：{host}:{port} 已被占用。"
                "请先停止旧 GUI 服务，或使用 --port 指定未占用端口。"
            ) from exc
        if exc.errno in {errno.EACCES, errno.EPERM}:
            raise UserError(
                f"GUI 启动失败：当前环境不允许监听 {host}:{port}。"
                "请确认在 WSL2 终端直接运行，或换用 127.0.0.1 和普通用户端口。"
            ) from exc
        raise UserError(f"GUI 启动失败：无法监听 {host}:{port}：{exc}") from exc
    url = f"http://{host}:{port}/"
    print(f"[sta-lite] GUI 已启动：{url}", flush=True)
    print("[sta-lite] 按 Ctrl+C 停止服务。", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[sta-lite] GUI 服务已停止。", flush=True)
    finally:
        server.server_close()


def main() -> int:
    parser = argparse.ArgumentParser(description="启动 STA-lite 本地 Web GUI 服务")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=8765, help="监听端口")
    args = parser.parse_args()
    run_server(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
