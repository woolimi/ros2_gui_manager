"""Application-level controller logic for the main window."""

import os
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox

from ..config_store import ensure_bashrc_prompt, load_config, save_config, write_domain_id
from ..integrations import launch_ros_tool, open_terminal as open_external_terminal
from ..project_index import populate_tree
from ..ros_env import find_setup_bash, get_ros2_distros, get_ros_env, ros_source_prefix
from ..workers import WorkerThread


class AppController:
    def __init__(self, window):
        self.window = window

    def detect_ros2(self):
        distros = get_ros2_distros()
        if not distros:
            self.window._log(
                "[WARN] No ROS2 installation found (checked: /opt/ros, $CONDA_PREFIX/opt/ros, Homebrew paths)"
            )
            self.window.distro_combo.addItem("(not found)")
        else:
            self.window.distro_combo.addItems(distros)
            for preferred in ["jazzy", "humble", "iron"]:
                if preferred in distros:
                    self.window.distro_combo.setCurrentText(preferred)
                    break
        self.load_workspaces()

    def ros_setup(self):
        if not self.window.current_distro:
            return ""
        return find_setup_bash(self.window.current_distro) or ""

    def ros_src(self):
        return ros_source_prefix(self.window.current_distro)

    def update_tool_buttons(self):
        enabled = bool(self.window.current_distro and self.window.current_workspace)
        for button in self.window.tool_btns:
            button.setEnabled(enabled)

    def on_distro_changed(self, distro):
        if not distro or distro == "(not found)":
            return
        self.window.current_distro = distro
        self.window.ros_env = get_ros_env(distro)
        self.apply_domain_id_to_env()
        self.window._log(f"[INFO] ROS2 {distro} sourced")
        self.window.statusBar().showMessage(f"ROS2 {distro} active")
        self.update_tool_buttons()

    def setup_bashrc_prompt(self):
        ensure_bashrc_prompt(self.window.domain_spin.value())

    def on_domain_id_changed(self, value):
        os.environ["ROS_DOMAIN_ID"] = str(value)
        if self.window.ros_env is not None:
            self.window.ros_env["ROS_DOMAIN_ID"] = str(value)
        try:
            write_domain_id(value)
        except Exception:
            pass
        self.window._log(f"[INFO] ROS_DOMAIN_ID -> {value}")
        self.window.statusBar().showMessage(f"ROS_DOMAIN_ID = {value}", 3000)

    def apply_domain_id_to_env(self):
        if self.window.ros_env is not None:
            self.window.ros_env["ROS_DOMAIN_ID"] = str(self.window.domain_spin.value())

    def cfg(self):
        return load_config()

    def save_cfg(self, config):
        save_config(config)

    def load_workspaces(self):
        self.window.ws_combo.blockSignals(True)
        self.window.ws_combo.clear()
        self.window.ws_combo.addItem("(select workspace)")
        for workspace in self.cfg().get("workspaces", []):
            if Path(workspace).exists():
                self.window.ws_combo.addItem(workspace)
        self.window.ws_combo.blockSignals(False)
        self.refresh_tree()

    def on_workspace_changed(self, path):
        if not path or path == "(select workspace)":
            self.window.current_workspace = None
            self.update_tool_buttons()
            return

        self.window.current_workspace = Path(path)
        self.window._log(f"[INFO] Workspace: {path}")
        self.refresh_tree()
        self.update_tool_buttons()
        self.auto_select_workspace_in_tree(self.window.current_workspace)

    def auto_select_workspace_in_tree(self, workspace_path):
        for index in range(self.window.tree.topLevelItemCount()):
            item = self.window.tree.topLevelItem(index)
            if item.data(0, Qt.UserRole + 1) == str(workspace_path):
                self.window.tree.setCurrentItem(item)
                self.window.ws_info_name.setText(f"Name:  {workspace_path.name}")
                self.window.ws_info_path.setText(f"Path:  {workspace_path}")
                self.window.stack.setCurrentIndex(1)
                item.setExpanded(True)
                break

    def refresh_tree(self):
        populate_tree(
            self.window.tree,
            self.cfg().get("workspaces", []),
            self.window.current_workspace,
            log_fn=self.window._log,
        )

    def open_terminal(self, cwd=None):
        cwd = cwd or self.window.current_workspace or Path.home()
        ok = open_external_terminal(
            cwd,
            distro=self.window.current_distro or "",
            workspace_path=self.window.current_workspace,
            domain_id=os.environ.get("ROS_DOMAIN_ID", "0"),
        )
        if not ok:
            self.window._log("[WARN] No terminal emulator found (gnome-terminal / xterm / konsole)")

    def open_rviz(self):
        if not self.require_distro():
            return
        env = self.window.ros_env or get_ros_env(self.window.current_distro)
        launch_ros_tool("rviz2", self.ros_setup(), env)
        self.window._log("[INFO] RViz2 launched")

    def open_rqt(self):
        if not self.require_distro():
            return
        env = self.window.ros_env or get_ros_env(self.window.current_distro)
        launch_ros_tool("rqt", self.ros_setup(), env)
        self.window._log("[INFO] rqt launched")

    def run_cmd(self, cmd, cwd=None, on_finish=None):
        self.window._log(f"\n{'─' * 52}")
        self.window._log(f"$ {cmd.split('&&')[-1].strip()}")
        self.window._log(f"{'─' * 52}")

        self.window._symlink_conflict_detected = False
        self.window.worker = WorkerThread(cmd, env=self.window.ros_env, cwd=cwd)

        def _check_output(line):
            self.window._log(line)
            if (
                "existing path cannot be removed: Is a directory" in line
                or "failed to create symbolic link" in line
            ):
                self.window._symlink_conflict_detected = True

        def _on_finish(code):
            self.window._log(
                f"\n{'─' * 52}\n[{'✓  OK' if code == 0 else '✗  FAILED'}] exit code: {code}\n"
            )
            if code != 0 and self.window._symlink_conflict_detected:
                answer = QMessageBox.question(
                    self.window,
                    "빌드 오류 감지",
                    "심볼릭 링크 충돌이 감지됐습니다.\n\n이전 빌드 캐시와 충돌이 발생했습니다.\nClean 후 재빌드할까요?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if answer == QMessageBox.Yes:
                    self.window.workspace_actions.clean_and_build()

        self.window.worker.output_signal.connect(_check_output)
        self.window.worker.finished_signal.connect(_on_finish)
        if on_finish:
            self.window.worker.finished_signal.connect(lambda _: on_finish())
        self.window.worker.start()

    def require_ws(self):
        if not self.window.current_workspace:
            self.window._log("[ERROR] No workspace selected.")
            return False
        if not self.window.current_distro:
            self.window._log("[ERROR] No ROS2 distro selected.")
            return False
        return True

    def require_distro(self):
        if not self.window.current_distro:
            self.window._log("[ERROR] No ROS2 distro selected.")
            return False
        return True
