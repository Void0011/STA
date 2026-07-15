"""源码运行与冻结发行版共用的资源定位。"""

from __future__ import annotations

import sys
from pathlib import Path


def resource_root() -> Path:
    """返回只读发行资源根目录。"""

    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root).resolve()
    return Path(__file__).resolve().parents[1]


def resource_path(*parts: str) -> Path:
    return resource_root().joinpath(*parts)
