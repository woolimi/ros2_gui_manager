"""Node, launch, and editor action handlers."""

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox

from ..integrations import detect_editors, launch_editor
from ..project_index import node_type_badge
from ..services import create_python_node
from ..workers import NodeWorkerThread
from .dialogs import choose_editor_dialog, show_run_arguments_dialog


class ProcessActions:
    def __init__(self, window):
        self.window = window

    def create_node(self):
        node_name = self.window.new_node_input.text().strip()
        if not node_name:
            QMessageBox.warning(self.window, "Warning", "Enter a node name.")
            return

        package_name = self.window.tree_controller.selected_package()
        if not package_name:
            return

        try:
            node_file = create_python_node(self.window.current_workspace, package_name, node_name)
        except FileExistsError:
            QMessageBox.warning(self.window, "Warning", f"Node '{node_name}' already exists.")
            return

        self.window._log(f"[OK] Node created: {node_file}")
        self.window.new_node_input.clear()
        self.window.app_controller.refresh_tree()

    def start_process_tab(self, tab_label, cmd, log_message):
        tab_index, tab_output = self.window.process_tabs.add_process_tab(tab_label)
        worker = NodeWorkerThread(cmd, env=self.window.ros_env, cwd=self.window.current_workspace)
        self.window.process_tabs.attach_worker(tab_index, tab_output, worker)
        worker.start()
        self.window._log(log_message)

    def run_node(self):
        item = self.window.tree.currentItem()
        if not item or item.data(0, Qt.UserRole) != "node":
            return

        node_name = item.text(0).split("  ", 1)[-1].strip()
        package_name = item.parent().text(0).split("  ", 1)[-1].strip()
        node_type = item.data(0, Qt.UserRole + 2) or "python"
        setup = self.window.current_workspace / "install" / "setup.bash"

        if not setup.exists():
            if (
                QMessageBox.question(
                    self.window,
                    "Build Required",
                    "Build workspace first?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                == QMessageBox.Yes
            ):
                self.window.workspace_actions.build_workspace()
            return

        extra_args, accepted = show_run_arguments_dialog(
            self.window,
            f"{package_name}/{node_name}",
            f"ros2 run {package_name} {node_name}",
            param_style="node",
        )
        if not accepted:
            return

        tab_label = f"[RUN] {node_type_badge(node_type)} {package_name}/{node_name}"
        cmd = (
            f"{self.window.app_controller.ros_src()}"
            f"source {setup} "
            f"&& ros2 run {package_name} {node_name}"
            f"{' ' + extra_args if extra_args else ''}"
        )
        self.start_process_tab(
            tab_label,
            cmd,
            f"[RUN] {package_name}/{node_name} ({node_type})",
        )

    def open_with_editor(self, file_path):
        if not file_path or not Path(file_path).exists():
            self.window._log(f"[ERROR] 파일 없음: {file_path}")
            return

        editors = detect_editors()
        config = self.window.app_controller.cfg()
        preferred_cmd = config.get("preferred_editor", "")
        valid_cmds = {cmd for _, cmd in editors}

        if preferred_cmd and preferred_cmd not in valid_cmds:
            self.window._log(f"[INFO] 저장된 편집기 설정 초기화: {preferred_cmd}")
            config.pop("preferred_editor", None)
            self.window.app_controller.save_cfg(config)
            preferred_cmd = ""

        if not editors:
            QMessageBox.warning(
                self.window,
                "편집기 없음",
                "설치된 텍스트 편집기를 찾을 수 없습니다.\nVS Code, Gedit, Kate 등을 설치 후 다시 시도해주세요.",
            )
            return

        selection = choose_editor_dialog(self.window, file_path, editors, preferred_cmd)
        if not selection:
            return

        chosen_cmd = selection["command"]
        if selection["remember"]:
            config["preferred_editor"] = chosen_cmd
            self.window.app_controller.save_cfg(config)

        launch_editor(chosen_cmd, file_path)
        self.window._log(f"[EDIT] {chosen_cmd} {file_path}")

    def edit_node(self):
        item = self.window.tree.currentItem()
        if not item or item.data(0, Qt.UserRole) != "node":
            return
        self.open_with_editor(item.data(0, Qt.UserRole + 1))

    def run_launch(self):
        item = self.window.tree.currentItem()
        if not item or item.data(0, Qt.UserRole) != "launch":
            return

        launch_file_path = item.data(0, Qt.UserRole + 1)
        package_name = item.data(0, Qt.UserRole + 2)
        launch_file_name = Path(launch_file_path).name
        setup = self.window.current_workspace / "install" / "setup.bash"

        if not setup.exists():
            if (
                QMessageBox.question(
                    self.window,
                    "Build Required",
                    "Build workspace first?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                == QMessageBox.Yes
            ):
                self.window.workspace_actions.build_workspace()
            return

        extra_args, accepted = show_run_arguments_dialog(
            self.window,
            f"{package_name}/{launch_file_name}",
            f"ros2 launch {package_name} {launch_file_name}",
            param_style="launch",
        )
        if not accepted:
            return

        tab_label = f"[LAUNCH] {package_name}/{launch_file_name}"
        cmd = (
            f"{self.window.app_controller.ros_src()}"
            f"source {setup} "
            f"&& ros2 launch {package_name} {launch_file_name}"
            f"{' ' + extra_args if extra_args else ''}"
        )
        self.start_process_tab(
            tab_label,
            cmd,
            f"[LAUNCH] {package_name}/{launch_file_name}",
        )

    def edit_launch(self):
        item = self.window.tree.currentItem()
        if not item or item.data(0, Qt.UserRole) != "launch":
            return
        self.open_with_editor(item.data(0, Qt.UserRole + 1))
