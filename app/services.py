"""Workspace, package, and node filesystem operations."""

import shutil
from pathlib import Path

from .templates import NodeTemplates


def create_workspace(base_dir, name):
    workspace_path = Path(base_dir) / name
    workspace_path.mkdir(parents=True, exist_ok=True)
    (workspace_path / "src").mkdir(exist_ok=True)
    return workspace_path


def inspect_workspace(workspace_path):
    workspace_path = Path(workspace_path)
    warnings = []

    if not (workspace_path / "src").exists():
        warnings.append("src/ 폴더가 없습니다. ROS2 워크스페이스가 맞나요?")

    has_install = (workspace_path / "install" / "setup.bash").exists()
    if not has_install:
        warnings.append("install/setup.bash 없음 → 빌드가 필요합니다.")

    return warnings, has_install


def add_workspace_to_config(config, workspace_path):
    workspaces = config.setdefault("workspaces", [])
    if str(workspace_path) in workspaces:
        return False
    workspaces.append(str(workspace_path))
    return True


def remove_workspace_from_config(config, workspace_path):
    config["workspaces"] = [
        entry for entry in config.get("workspaces", []) if entry != str(workspace_path)
    ]
    return config


def clean_workspace_dirs(workspace_path):
    removed = []
    for name in ["build", "install", "log"]:
        path = Path(workspace_path) / name
        if path.exists():
            shutil.rmtree(path)
            removed.append(path)
    return removed


def clean_package_artifacts(workspace_path, package_name):
    removed = []
    for name in ["build", "install"]:
        path = Path(workspace_path) / name / package_name
        if path.exists():
            shutil.rmtree(path)
            removed.append(path)
    return removed


def create_python_node(workspace_path, package_name, node_name):
    package_path = Path(workspace_path) / "src" / package_name
    node_file = package_path / package_name / f"{node_name}.py"

    if node_file.exists():
        raise FileExistsError(node_file)

    node_file.parent.mkdir(parents=True, exist_ok=True)

    init_py = node_file.parent / "__init__.py"
    if not init_py.exists():
        init_py.write_text(NodeTemplates.init_py())

    node_file.write_text(NodeTemplates.python_node(package_name, node_name))
    node_file.chmod(0o644)
    NodeTemplates.update_setup_py(package_path / "setup.py", package_name, node_name)
    return node_file
