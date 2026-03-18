"""Project tree scanning and parameter parsing helpers."""

import re
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QTreeWidgetItem


def node_type_badge(node_type):
    if node_type == "python":
        return "[PY]"
    if node_type == "cpp":
        return "[C++]"
    return "[SH]"


def parse_node_params(node_path):
    params = []
    if not node_path or not Path(node_path).exists():
        return params

    try:
        content = Path(node_path).read_text(errors="ignore")

        pattern = r"declare_parameter\s*\(\s*['\"](\w+)['\"](?:\s*,\s*([^,\)]+))?"
        for match in re.finditer(pattern, content):
            name = match.group(1)
            default = match.group(2).strip() if match.group(2) else ""
            if default.startswith(("'", '"')):
                param_type = "string"
                default = default.strip("'\"")
            elif default in ("True", "False", "true", "false"):
                param_type = "bool"
            elif "." in default:
                param_type = "float"
            elif default.lstrip("-").isdigit():
                param_type = "int"
            else:
                param_type = "string"
            if name not in [item["name"] for item in params]:
                params.append({"name": name, "default": default, "type": param_type})

        pattern2 = r"add_argument\s*\(\s*['\"]--?([\w-]+)['\"].*?default\s*=\s*([^,\)]+)"
        for match in re.finditer(pattern2, content, re.DOTALL):
            name = match.group(1).replace("-", "_")
            default = match.group(2).strip().strip("'\"")
            if name not in [item["name"] for item in params]:
                params.append({"name": name, "default": default, "type": "string"})
    except Exception:
        pass

    return params


def parse_launch_params(launch_file_path, package_dir=None):
    params = []
    if not launch_file_path or not Path(launch_file_path).exists():
        return params

    def _resolve_default(default, pkg_dir):
        if not default or not pkg_dir:
            return default

        default = re.sub(
            r"\$\(find-pkg-share\s+[\w_]+\)",
            str(pkg_dir),
            default,
        )

        path = Path(default)
        if not path.is_absolute():
            candidate = pkg_dir / default
            if candidate.exists():
                return str(candidate)
        return default

    try:
        content = Path(launch_file_path).read_text(errors="ignore")
        extension = Path(launch_file_path).suffix.lower()

        if extension == ".xml":
            pattern = (
                r'<arg\s+name=["\'](\w+)["\'](?:[^>]*?default=["\']([^"\']*)["\'])?'
                r'(?:[^>]*?description=["\']([^"\']*)["\'])?'
            )
            for match in re.finditer(pattern, content):
                params.append(
                    {
                        "name": match.group(1),
                        "default": _resolve_default(match.group(2) or "", package_dir),
                        "description": match.group(3) or "",
                    }
                )
        elif extension in (".py", ""):
            pattern = (
                r"DeclareLaunchArgument\s*\(\s*['\"](\w+)['\"]"
                r"(?:.*?default_value\s*=\s*['\"]([^'\"]*)['\"])?"
                r"(?:.*?description\s*=\s*['\"]([^'\"]*)['\"])?"
            )
            for match in re.finditer(pattern, content, re.DOTALL):
                params.append(
                    {
                        "name": match.group(1),
                        "default": _resolve_default(match.group(2) or "", package_dir),
                        "description": match.group(3) or "",
                    }
                )
        elif extension in (".yaml", ".yml"):
            for line in content.splitlines():
                match = re.match(r"\s*([\w_]+)\s*:\s*(.+)", line)
                if not match:
                    continue
                params.append(
                    {
                        "name": match.group(1),
                        "default": _resolve_default(match.group(2).strip(), package_dir),
                        "description": "",
                    }
                )
    except Exception:
        pass

    return params


def scan_nodes(package_dir):
    nodes = {}
    package_name = package_dir.name

    setup_py = package_dir / "setup.py"
    if setup_py.exists():
        try:
            content = setup_py.read_text()
            pattern = r"['\"](\w+)\s*=\s*([\w.]+):(\w+)['\"]"
            for match in re.finditer(pattern, content):
                node_name, module_path, _ = match.group(1), match.group(2), match.group(3)
                relative = module_path.replace(".", "/") + ".py"
                candidates = [
                    package_dir / relative,
                    package_dir / package_name / (module_path.split(".")[-1] + ".py"),
                ]
                found_path = next((str(path) for path in candidates if path.exists()), "")
                nodes.setdefault(
                    node_name,
                    {
                        "name": node_name,
                        "path": found_path,
                        "type": "python",
                        "source": "setup.py",
                    },
                )
        except Exception:
            pass

    scripts_dir = package_dir / "scripts"
    if scripts_dir.exists():
        for script in sorted(scripts_dir.iterdir()):
            if script.suffix not in (".py", "") or not script.is_file() or script.name == "__init__.py":
                continue
            nodes.setdefault(
                script.stem,
                {
                    "name": script.stem,
                    "path": str(script),
                    "type": "script",
                    "source": "scripts/",
                },
            )

    python_dir = package_dir / package_name
    if python_dir.exists():
        for py_file in sorted(python_dir.glob("*.py")):
            if py_file.name == "__init__.py":
                continue
            nodes.setdefault(
                py_file.stem,
                {
                    "name": py_file.stem,
                    "path": str(py_file),
                    "type": "python",
                    "source": "pkg_dir",
                },
            )

    cmake = package_dir / "CMakeLists.txt"
    if cmake.exists():
        try:
            content = cmake.read_text()
            pattern = r"add_executable\s*\(\s*(\w+)\s+([^)]+)\)"
            for match in re.finditer(pattern, content):
                node_name = match.group(1)
                src_files = match.group(2).split()
                found_path = ""
                for src_file in src_files:
                    candidates = [package_dir / src_file, package_dir / "src" / src_file]
                    found = next((str(path) for path in candidates if path.exists()), "")
                    if found:
                        found_path = found
                        break
                nodes.setdefault(
                    node_name,
                    {
                        "name": node_name,
                        "path": found_path,
                        "type": "cpp",
                        "source": "CMakeLists.txt",
                    },
                )
        except Exception:
            pass

    return list(nodes.values())


def scan_launch_files(package_dir):
    launch_dir = package_dir / "launch"
    if not launch_dir.exists():
        return []

    files = []
    for extension in ["*.launch.py", "*.launch.xml", "*.launch.yaml", "*.launch.yml"]:
        files.extend(sorted(launch_dir.glob(extension)))

    for path in sorted(launch_dir.iterdir()):
        if path.suffix in (".py", ".xml", ".yaml", ".yml") and path not in files:
            files.append(path)

    return [str(path) for path in files]


def discover_packages(workspace_path):
    package_dirs = []
    src = Path(workspace_path) / "src"
    if not src.exists():
        return package_dirs

    for item in sorted(src.iterdir()):
        if not item.is_dir():
            continue
        if (item / "package.xml").exists():
            package_dirs.append(item)
            continue
        for sub in sorted(item.iterdir()):
            if sub.is_dir() and (sub / "package.xml").exists():
                package_dirs.append(sub)
    return package_dirs


def populate_tree(tree_widget, workspaces, current_workspace, log_fn=None):
    tree_widget.clear()

    for workspace_str in workspaces:
        workspace = Path(workspace_str)
        if not workspace.exists():
            continue

        ws_item = QTreeWidgetItem([f"[WS]  {workspace.name}"])
        ws_item.setData(0, Qt.UserRole, "workspace")
        ws_item.setData(0, Qt.UserRole + 1, str(workspace))
        if current_workspace == workspace:
            ws_item.setForeground(0, QColor("#5b9cf6"))

        src = workspace / "src"
        if not src.exists():
            if log_fn:
                log_fn(f"[WARN] src/ 폴더 없음: {workspace}")
        else:
            package_dirs = discover_packages(workspace)
            if log_fn:
                log_fn(f"[INFO] {workspace.name}: 패키지 {len(package_dirs)}개 발견")

            for package_dir in package_dirs:
                is_cpp = (package_dir / "CMakeLists.txt").exists() and not (package_dir / "setup.py").exists()
                package_label = "[CMAKE]" if is_cpp else "[PKG]"

                pkg_item = QTreeWidgetItem([f"{package_label}  {package_dir.name}"])
                pkg_item.setData(0, Qt.UserRole, "package")
                pkg_item.setData(0, Qt.UserRole + 1, str(package_dir))

                for node_info in scan_nodes(package_dir):
                    label = f"{node_type_badge(node_info['type'])}  {node_info['name']}"
                    node_item = QTreeWidgetItem([label])
                    node_item.setData(0, Qt.UserRole, "node")
                    node_item.setData(0, Qt.UserRole + 1, node_info["path"])
                    node_item.setData(0, Qt.UserRole + 2, node_info["type"])
                    node_item.setToolTip(
                        0,
                        (
                            f"Name:   {node_info['name']}\n"
                            f"Type:   {node_info['type']}\n"
                            f"Source: {node_info['source']}\n"
                            f"Path:   {node_info['path'] or '(built binary)'}"
                        ),
                    )
                    pkg_item.addChild(node_item)

                for launch_file in scan_launch_files(package_dir):
                    extension = Path(launch_file).suffix
                    if extension == ".py":
                        icon = "[LPY]"
                    elif extension == ".xml":
                        icon = "[LXML]"
                    else:
                        icon = "[LYML]"

                    launch_item = QTreeWidgetItem([f"{icon}  {Path(launch_file).name}"])
                    launch_item.setData(0, Qt.UserRole, "launch")
                    launch_item.setData(0, Qt.UserRole + 1, launch_file)
                    launch_item.setData(0, Qt.UserRole + 2, package_dir.name)
                    launch_item.setToolTip(0, f"Launch: {launch_file}")
                    pkg_item.addChild(launch_item)

                ws_item.addChild(pkg_item)

        tree_widget.addTopLevelItem(ws_item)
        is_current = current_workspace == workspace
        ws_item.setExpanded(is_current)
        for index in range(ws_item.childCount()):
            ws_item.child(index).setExpanded(is_current)
