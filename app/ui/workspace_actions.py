"""Workspace and package action handlers."""

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFileDialog, QMessageBox

from ..services import (
    add_workspace_to_config,
    clean_package_artifacts,
    clean_workspace_dirs,
    create_workspace,
    inspect_workspace,
    remove_workspace_from_config,
)
from .dialogs import (
    confirm_workspace_registration,
    show_new_package_dialog,
    show_new_workspace_dialog,
)


class WorkspaceActions:
    def __init__(self, window):
        self.window = window

    def create_workspace(self):
        workspace_spec = show_new_workspace_dialog(self.window)
        if not workspace_spec:
            return

        workspace_path = create_workspace(workspace_spec["location"], workspace_spec["name"])
        config = self.window.app_controller.cfg()
        if add_workspace_to_config(config, workspace_path):
            self.window.app_controller.save_cfg(config)

        self.window._log(f"[OK] Workspace created: {workspace_path}")
        self.window.app_controller.load_workspaces()
        self.window.ws_combo.setCurrentText(str(workspace_path))

    def open_workspace(self):
        path_str = QFileDialog.getExistingDirectory(
            self.window,
            "기존 워크스페이스 선택",
            str(Path.home()),
        )
        if not path_str:
            return

        workspace_path = Path(path_str)
        warnings, has_install = inspect_workspace(workspace_path)
        if not confirm_workspace_registration(self.window, warnings):
            return

        config = self.window.app_controller.cfg()
        if str(workspace_path) in config.get("workspaces", []):
            QMessageBox.information(
                self.window,
                "알림",
                f"이미 등록된 워크스페이스입니다.\n{workspace_path}",
            )
            self.window.ws_combo.setCurrentText(str(workspace_path))
            return

        add_workspace_to_config(config, workspace_path)
        self.window.app_controller.save_cfg(config)

        status = "빌드됨" if has_install else "빌드 필요"
        self.window._log(f"[OK] 워크스페이스 등록: {workspace_path}  [{status}]")
        self.window.app_controller.load_workspaces()
        self.window.ws_combo.setCurrentText(str(workspace_path))

    def build_workspace(self):
        if not self.window.app_controller.require_ws():
            return
        self.window.app_controller.run_cmd(
            f"{self.window.app_controller.ros_src()}colcon build --symlink-install 2>&1",
            cwd=self.window.current_workspace,
        )

    def source_workspace(self):
        if not self.window.app_controller.require_ws():
            return
        setup = self.window.current_workspace / "install" / "setup.bash"
        if not setup.exists():
            self.window._log("[WARN] No install/setup.bash - build workspace first.")
            return
        from ..ros_env import get_ws_env

        self.window.ros_env = get_ws_env(self.window.current_distro, self.window.current_workspace)
        self.window.app_controller.apply_domain_id_to_env()
        self.window._log(f"[OK] Workspace sourced: {setup}")

    def clean_workspace(self):
        if not self.window.app_controller.require_ws():
            return
        if (
            QMessageBox.question(
                self.window,
                "Clean Workspace",
                "Delete build/, install/, log/ ?",
                QMessageBox.Yes | QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return
        for path in clean_workspace_dirs(self.window.current_workspace):
            self.window._log(f"[OK] Removed {path}")

    def clean_and_build(self):
        if not self.window.app_controller.require_ws():
            return
        if (
            QMessageBox.question(
                self.window,
                "Clean & Build",
                "build/, install/, log/ 를 삭제 후 전체 빌드합니다.\n계속하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return

        for path in clean_workspace_dirs(self.window.current_workspace):
            self.window._log(f"[OK] Removed {path}")
        self.build_workspace()

    def clean_package(self):
        package_name = self.window.tree_controller.selected_package()
        if not package_name:
            return
        if (
            QMessageBox.question(
                self.window,
                "Clean Package",
                f"패키지 '{package_name}' 의 빌드 캐시를 삭제합니다.\n"
                f"  build/{package_name}\n  install/{package_name}\n\n계속하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
            )
            != QMessageBox.Yes
        ):
            return

        removed = clean_package_artifacts(self.window.current_workspace, package_name)
        if not removed:
            self.window._log(f"[INFO] '{package_name}' 에 대한 빌드 캐시가 없습니다.")
            return
        for path in removed:
            self.window._log(f"[OK] Removed {path}")

    def open_workspace_terminal(self):
        self.window.app_controller.open_terminal(cwd=self.window.current_workspace)

    def create_package(self):
        if not self.window.app_controller.require_ws():
            return

        package_spec = show_new_package_dialog(self.window)
        if not package_spec:
            return

        deps_flag = (
            f"--dependencies {package_spec['dependencies']}"
            if package_spec["dependencies"]
            else ""
        )
        source_dir = self.window.current_workspace / "src"
        self.window.app_controller.run_cmd(
            f"{self.window.app_controller.ros_src()}ros2 pkg create --build-type {package_spec['build_type']} {deps_flag} {package_spec['name']} 2>&1",
            cwd=source_dir,
            on_finish=self.window.app_controller.refresh_tree,
        )

    def build_package(self):
        package_name = self.window.tree_controller.selected_package()
        if not package_name:
            return
        self.window.app_controller.run_cmd(
            f"{self.window.app_controller.ros_src()}colcon build --packages-select {package_name} --symlink-install 2>&1",
            cwd=self.window.current_workspace,
        )

    def open_package_terminal(self):
        package_name = self.window.tree_controller.selected_package()
        if package_name:
            self.window.app_controller.open_terminal(cwd=self.window.current_workspace / "src" / package_name)

    def remove_workspace(self, item):
        path = item.data(0, Qt.UserRole + 1)
        config = self.window.app_controller.cfg()
        self.window.app_controller.save_cfg(remove_workspace_from_config(config, path))
        self.window.app_controller.load_workspaces()
