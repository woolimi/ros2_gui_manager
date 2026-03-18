"""ROS environment discovery and sourcing helpers."""

import os
import subprocess
from pathlib import Path

from .constants import IS_MAC


def get_bash():
    """Return a usable bash binary for the current platform."""
    if IS_MAC:
        for path in ["/opt/homebrew/bin/bash", "/usr/local/bin/bash"]:
            if Path(path).exists():
                return path
    return "bash"


BASH = get_bash()


def get_ros2_search_paths():
    """Return candidate directories that may contain ROS2 installations."""
    paths = [Path("/opt/ros")]

    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        paths.append(Path(conda_prefix) / "opt" / "ros")

    if IS_MAC:
        paths.append(Path("/opt/homebrew/opt/ros"))
        paths.append(Path("/usr/local/opt/ros"))

    return paths


def find_setup_bash(distro):
    """Return the setup.bash path for a distro, if present."""
    for ros_path in get_ros2_search_paths():
        setup = ros_path / distro / "setup.bash"
        if setup.exists():
            return str(setup)
    return None


def get_ros2_distros():
    distros = set()
    for ros_path in get_ros2_search_paths():
        if not ros_path.exists():
            continue
        for distro_path in ros_path.iterdir():
            if distro_path.is_dir() and (distro_path / "setup.bash").exists():
                distros.add(distro_path.name)

    if os.environ.get("ROS_DISTRO") and os.environ.get("AMENT_PREFIX_PATH"):
        distros.add(os.environ["ROS_DISTRO"])

    return sorted(distros)


def get_ros_env(distro):
    env = os.environ.copy()
    setup_script = find_setup_bash(distro)
    if not setup_script:
        return env

    cmd = f"{BASH} -c 'source {setup_script} && env'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key] = value
    return env


def get_ws_env(distro, workspace):
    env = get_ros_env(distro)
    setup = Path(workspace) / "install" / "setup.bash"
    if not setup.exists():
        return env

    ros_setup = find_setup_bash(distro)
    ros_source = f"source {ros_setup} && " if ros_setup else ""
    cmd = f"{BASH} -c '{ros_source}source {setup} && env'"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        env[key] = value
    return env


def ros_source_prefix(distro):
    """Return a shell prefix that sources the requested distro."""
    setup = find_setup_bash(distro) if distro else None
    return f"source {setup} && " if setup else ""
