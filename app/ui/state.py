"""Shared UI state for the main window."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class WindowState:
    ros_env: dict[str, str] | None = None
    current_distro: str | None = None
    current_workspace: Path | None = None
    worker: Any = None
    symlink_conflict_detected: bool = False
