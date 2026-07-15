from __future__ import annotations

import shutil
from typing import Any


def backend_tool_status(yosys_bin: str = "yosys", sta_bin: str = "sta") -> dict[str, Any]:
    tools = {
        "yosys": {"command": yosys_bin, "path": shutil.which(yosys_bin)},
        "opensta": {"command": sta_bin, "path": shutil.which(sta_bin)},
    }
    missing = [name for name, item in tools.items() if not item["path"]]
    available = not missing
    if available:
        message = "Yosys 和 OpenSTA 均可用，可以运行本地后端参考分析。"
    else:
        labels = {"yosys": "Yosys", "opensta": "OpenSTA"}
        message = f"后端可选工具不可用：{', '.join(labels[name] for name in missing)}。RTL Review、RTL Lint、RTL Timing Risk Profiling、Case Coverage 和已有报告查看仍可独立运行。"
    return {
        "available": available,
        "status": "available" if available else "unavailable_optional",
        "message_zh": message,
        "tools": tools,
    }
