"""Main application window."""

from PyQt5.QtWidgets import QApplication, QMainWindow

from ..constants import MONO_FONT_FAMILY
from .app_controller import AppController
from .page_builders import MainWindowUiBuilder
from .process_actions import ProcessActions
from .state import WindowState
from .theme import build_main_window_stylesheet, is_dark_palette
from .tree_controller import TreeController
from .workspace_actions import WorkspaceActions


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ROS2 GUI Manager")
        self.setMinimumSize(1280, 820)

        self.state = WindowState()
        self.app_controller = AppController(self)
        self.workspace_actions = WorkspaceActions(self)
        self.process_actions = ProcessActions(self)
        self.tree_controller = TreeController(self)
        self.ui_builder = MainWindowUiBuilder(self)

        self.ui_builder.build_ui()
        self._apply_theme()
        self.app_controller.detect_ros2()
        self.app_controller.setup_bashrc_prompt()

    @property
    def ros_env(self):
        return self.state.ros_env

    @ros_env.setter
    def ros_env(self, value):
        self.state.ros_env = value

    @property
    def current_distro(self):
        return self.state.current_distro

    @current_distro.setter
    def current_distro(self, value):
        self.state.current_distro = value

    @property
    def current_workspace(self):
        return self.state.current_workspace

    @current_workspace.setter
    def current_workspace(self, value):
        self.state.current_workspace = value

    @property
    def worker(self):
        return self.state.worker

    @worker.setter
    def worker(self, value):
        self.state.worker = value

    @property
    def _symlink_conflict_detected(self):
        return self.state.symlink_conflict_detected

    @_symlink_conflict_detected.setter
    def _symlink_conflict_detected(self, value):
        self.state.symlink_conflict_detected = value

    def _is_dark_system(self):
        return is_dark_palette(QApplication.palette())

    def _apply_theme(self):
        self.setStyleSheet(
            build_main_window_stylesheet(self._is_dark_system(), MONO_FONT_FAMILY)
        )

    def _log(self, text):
        self.process_tabs.log_output(text)
