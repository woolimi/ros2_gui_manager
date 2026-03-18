# ROS2 GUI Manager

A PyQt5 desktop tool for managing ROS2 workspaces, packages, and nodes from one window, without memorizing terminal commands.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![ROS2](https://img.shields.io/badge/ROS2-Humble%20%7C%20Iron%20%7C%20Jazzy-brightgreen)
![PyQt5](https://img.shields.io/badge/PyQt5-5.x-orange)
![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS-lightgrey)

---

## Table of Contents

- [Requirements](#requirements)
- [Installation & Launch](#installation--launch)
- [UI Overview](#ui-overview)
- [Features](#features)
  - [ROS_DOMAIN_ID Control](#ros_domain_id-control)
  - [Workspace Management](#workspace-management)
  - [Package Management](#package-management)
  - [Node Management](#node-management)
  - [Launch File Management](#launch-file-management)
  - [External Tool Integration](#external-tool-integration)
  - [Tabbed Terminal](#tabbed-terminal)
- [Platform Notes](#platform-notes)
- [Configuration File](#configuration-file)
- [Architecture Overview](#architecture-overview)
- [Known Limitations](#known-limitations)

---

## Requirements

| Item | Minimum Version |
|------|----------------|
| OS | Ubuntu 20.04+ / macOS 12+ |
| Python | 3.8+ |
| ROS2 | Humble / Iron / Jazzy |
| PyQt5 | 5.x (auto-installed on first run if missing) |

> **Auto-install**: On first launch, if PyQt5 is not found, the tool prompts you to install it automatically via `pip`.
> Works correctly inside a **Python virtual environment** — installs into the active venv automatically.

---

## Installation & Launch

No installation required. Just run the launcher script.

```bash
# Run directly
python3 ros2_gui_manager.py

# Or grant execute permission and run
chmod +x ros2_gui_manager.py
./ros2_gui_manager.py

# Inside a virtual environment
source ~/venv/ros/bin/activate
python3 ros2_gui_manager.py
```

### macOS Prerequisites

macOS ships with `/bin/bash` v3.2, which cannot run ROS2 setup scripts (requires bash 4.3+).
Install a modern bash via Homebrew before running:

```bash
brew install bash
```

---

## UI Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│  ◈ ROS2 GUI Manager  Distro [jazzy▾]  Workspace [~/ws▾]  Domain ID [0]│  ← Top Bar
│                                          Terminal  RViz2  rqt         │
├──────────────┬───────────────────────────────────────────────────────┤
│ PROJECT TREE │                                                        │
│              │          Action Panel (context-sensitive)              │
│  📁 ros2_ws  │    (Workspace / Package / Node / Launch)               │
│  ├ 📦 pkg_a  │                                                        │
│  │  🔵 node1 │                                                        │
│  │  📜 launch│                                                        │
│  └ 📦 pkg_b  │                                                        │
│              │                                                        │
│  [+ New] [Open]                                                       │
├──────────────┴───────────────────────────────────────────────────────┤
│ OUTPUT  ● 🔵 pkg_a/node1  ■ pkg_b/node2                               │  ← Tabbed Terminal
│  $ colcon build ...                                                   │
│  [✓  OK] exit code: 0                                                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Features

### ROS_DOMAIN_ID Control

A **Domain ID** spinbox (range 0–232) is always visible in the top bar.

- Changing the value immediately updates `ROS_DOMAIN_ID` for all child processes (nodes, launch files, terminal, RViz2, rqt)
- The value is saved to `~/.ros_domain_id` so **all currently open terminals** reflect the change at the next prompt — no restart needed
- On first run, `PROMPT_COMMAND` is automatically added to `~/.bashrc` to keep every terminal in sync

**Terminal prompt integration**
If your `~/.bashrc` sets `PS1` with `${ROS_DOMAIN_ID}`, the prompt will show the updated value after the next Enter key press in any terminal:

```
(ID: 5) user:~/ros2_ws$
```

To enable this, add the following to `~/.bashrc` (done automatically on first run):

```bash
PROMPT_COMMAND='export ROS_DOMAIN_ID=$(cat ~/.ros_domain_id 2>/dev/null || echo 0)'
```

---

### Workspace Management

**Auto-detection**
Scans multiple paths to detect installed ROS2 distributions:

| Path | Environment |
|------|-------------|
| `/opt/ros/` | Linux standard / Homebrew |
| `$CONDA_PREFIX/opt/ros/` | RoboStack (conda) |
| `/opt/homebrew/opt/ros/` | Homebrew Apple Silicon |
| `/usr/local/opt/ros/` | Homebrew Intel Mac |
| `$ROS_DISTRO` + `$AMENT_PREFIX_PATH` | Already-sourced environment |

Default selection priority: Jazzy → Humble → Iron.

**Create a New Workspace**
Enter a name and location — the tool creates `<path>/<name>/src/` and registers it in the config.

**Open an Existing Workspace**
When selecting a folder, the tool validates the presence of `src/` and `install/setup.bash`, displaying warnings if anything looks off.

**Build / Clean Actions**

| Action | Internal Command |
|--------|-----------------|
| Build Workspace | `colcon build --symlink-install` |
| Clean Workspace | Removes `build/` `install/` `log/` |
| Clean & Build | Clean followed by immediate rebuild |
| Source Workspace | Sources `install/setup.bash` into the current environment |

> **Symlink conflict auto-detection**: If `failed to create symbolic link` is detected in build output, a dialog automatically suggests running Clean & Build.

---

### Package Management

Select a workspace in the project tree, then use **Add Package** or the right-click context menu.

**Package Creation Options**

| Field | Details |
|-------|---------|
| Build type | `ament_python` or `ament_cmake` |
| Dependencies | Space-separated (e.g. `rclpy std_msgs`) |
| Internal command | `ros2 pkg create --build-type <type> --dependencies <deps> <name>` |

**Per-package Build / Clean**

- **Build Package**: Builds only the selected package via `colcon build --packages-select <pkg>`
- **Clean Package**: Removes only `build/<pkg>` and `install/<pkg>`, leaving the rest of the workspace intact

---

### Node Management

**Create a Node**
Select a package, enter a node name, and the tool generates a ready-to-run Python node boilerplate.

Files created automatically:
- `src/<pkg>/<pkg>/<node_name>.py` — Python node with ROS2 Publisher template
- `src/<pkg>/<pkg>/__init__.py` — Package init file (if not present)
- `setup.py` — `console_scripts` entry point added automatically

Generated node template:
```python
class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        self.timer = self.create_timer(0.5, self.timer_callback)
```

**Run a Node**
Select a node in the tree → click **Run Node**:
1. A parameter dialog appears (`param:=value` format)
2. The node runs in a dedicated tab via `ros2 run <pkg> <node>`
3. Tab icon reflects the process state (`●` running / `■` stopped)

**Edit Source**
Installed editors (VS Code, Gedit, Kate, etc.) are auto-detected and used to open the node source file.

---

### Launch File Management

`.py` and `.xml` launch files are displayed in the project tree under their respective packages.

**Run a Launch File**
Before execution, the tool parses launch arguments and displays them in a dialog.

| File Format | Parsed Target |
|-------------|--------------|
| `.py` | `DeclareLaunchArgument(...)` |
| `.xml` | `<arg name="..." default="..."/>` |
| `.yaml` | Top-level key-value pairs |

Defaults are pre-filled and can be edited before launch.
Internal command: `ros2 launch <pkg> <launch_file> [args...]`

---

### External Tool Integration

Toolbar buttons are activated once both a **Distro** and a **Workspace** are selected.

| Button | Action |
|--------|--------|
| Terminal | Opens a ROS2-sourced terminal with current `ROS_DOMAIN_ID` injected |
| RViz2 | Launches `rviz2` |
| rqt | Launches `rqt` |

**Terminal launcher behavior by platform**

| Platform | Priority |
|----------|----------|
| Linux | gnome-terminal → xterm → konsole → x-terminal-emulator |
| macOS | iTerm2 (if installed) → Terminal.app |

---

### Tabbed Terminal

The bottom panel is a VS Code-style tabbed terminal.

- **OUTPUT tab**: Dedicated to build logs and general workspace commands
- **Node / Launch tabs**: Each running process gets its own tab

**Tab Icon Reference**

| Icon | Meaning |
|------|---------|
| `●` | Process running |
| `■` | Process exited |
| `🔵` | Python node |
| `⚙` | C++ node |
| `📜` | Launch file |

**Graceful Process Shutdown**
Clicking the close button (X) on a running tab sends signals in sequence:

```
SIGINT → wait 3s → SIGTERM → wait 2s → SIGKILL
```

**Output Buffering**
To prevent GUI freezes from high-frequency log output, a batched update strategy is used.

| Setting | Value |
|---------|-------|
| GUI update interval | 500 ms |
| Max buffer lines | 200 (older lines dropped on overflow) |
| Max lines per tab | 1,000 |

---

## Platform Notes

### Linux (Ubuntu 20.04+)

Fully supported. All features available out of the box.

```bash
# PyQt5 (if not installed)
pip install PyQt5
# or
sudo apt install python3-pyqt5
```

### macOS (12+)

Supported with the following prerequisites:

```bash
# Required: modern bash (macOS default is v3.2, incompatible with ROS2)
brew install bash

# ROS2 installation options:
# Option 1 — Homebrew
brew install ros-jazzy/ros/ros-base

# Option 2 — RoboStack (conda)
conda create -n ros2 python=3.11
conda activate ros2
conda install -c robostack-staging ros-jazzy-desktop
```

> The GUI auto-detects ROS2 in all of the above locations.
> For RoboStack, activate the conda environment before launching the GUI.

### Virtual Environment (venv / conda)

Running inside a virtual environment is fully supported.
PyQt5 auto-install uses `sys.executable`, so it installs into the active environment automatically.

```bash
source ~/venv/ros/bin/activate
python3 ros2_gui_manager.py
```

---

## Configuration File

The workspace list is persisted as a JSON file.

**Location**: `~/.config/ros2_gui_manager/config.json`

```json
{
  "workspaces": [
    "/home/user/ros2_ws",
    "/home/user/swarm_ws"
  ]
}
```

**ROS_DOMAIN_ID persistence**: `~/.ros_domain_id`
Written by the GUI on every Domain ID change. Read by `PROMPT_COMMAND` in `~/.bashrc`.

---

## Architecture Overview

The app now keeps the user-facing launcher while splitting implementation into a small package:

```text
ros2_gui_manager.py              # launcher script + dependency check
app/
├── bootstrap.py                 # QApplication setup and app startup
├── deps.py                      # PyQt5 dependency check / install prompt
├── constants.py                 # shared platform/font constants
├── ros_env.py                   # ROS2 distro discovery and sourced env helpers
├── config_store.py              # config.json / .ros_domain_id persistence
├── workers.py                   # WorkerThread / NodeWorkerThread
├── templates.py                 # generated ROS2 Python node templates
├── services.py                  # workspace/package/node filesystem operations
├── project_index.py             # package/node/launch scanning and tree building
├── integrations.py              # editor / terminal / RViz / rqt launchers
└── ui/
    ├── main_window.py           # MainWindow UI composition and event routing
    └── widgets.py               # small reusable UI helpers
```

High-level flow:

```text
ros2_gui_manager.py
  -> app.deps.check_and_install_dependencies()
  -> app.bootstrap.main()
  -> app.ui.main_window.MainWindow
     -> ros_env / services / project_index / integrations / workers
```

---

## Known Limitations

- **Windows**: Not supported. Relies on bash and POSIX process management.
- **Python nodes only**: Node boilerplate generation is Python-only. C++ nodes must be written manually after package creation.
- **One process per tab**: Each node run opens a new tab. Running the same node multiple times creates multiple tabs.
- **Launch argument parsing**: Complex conditional arguments (`IfCondition`, dynamically generated args, etc.) may not be parsed correctly.
- **macOS — bash required**: Homebrew bash must be installed (`brew install bash`) for ROS2 setup scripts to run correctly.
- **RoboStack**: The conda environment must be activated before launching the GUI for auto-detection to work.

---

## License

MIT
