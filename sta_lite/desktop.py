"""STA-Lite 桌面发行入口。"""

from __future__ import annotations

import ctypes
import argparse
import os
import shutil
import sys
from pathlib import Path

from sta_lite.gui.server import run_server
from sta_lite.resources import resource_path


def default_workspace() -> Path:
    if sys.platform == "win32":
        documents = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Documents"
        return documents / "STA-Lite-Workspace"
    return Path.home() / "STA-Lite-Workspace"


def _copy_missing_tree(source: Path, destination: Path) -> None:
    if not source.is_dir():
        return
    for item in source.rglob("*"):
        relative = item.relative_to(source)
        target = destination / relative
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def prepare_workspace(workspace: Path | None = None) -> Path:
    target = (workspace or default_workspace()).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    _copy_missing_tree(resource_path("examples"), target / "examples")
    _copy_missing_tree(resource_path("risk_profile", "cases"), target / "risk_profile" / "cases")
    _copy_missing_tree(resource_path("risk_profile", "gold"), target / "risk_profile" / "gold")
    (target / "runs").mkdir(exist_ok=True)
    return target


def _show_error(message: str) -> None:
    if sys.platform == "win32":
        ctypes.windll.user32.MessageBoxW(0, message, "STA-Lite 启动失败", 0x10)
    else:
        print(f"[sta-lite] 错误：{message}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="启动 STA-Lite 桌面 GUI")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器（用于自动化测试）")
    parser.add_argument("--port", type=int, default=8765, help="首选监听端口")
    parser.add_argument("--workspace", type=Path, help="用户工作区目录")
    args = parser.parse_args(argv)
    try:
        workspace = prepare_workspace(args.workspace)
        os.chdir(workspace)
        run_server(
            host="127.0.0.1",
            port=args.port,
            open_browser=not args.no_browser,
            probe_ports=20 if args.port == 8765 else 0,
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - desktop users must see startup failures.
        _show_error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
