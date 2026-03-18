"""Project tree interaction helpers."""

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMenu


class TreeController:
    def __init__(self, window):
        self.window = window

    def on_item_clicked(self, item, _col):
        role = item.data(0, Qt.UserRole)
        path = item.data(0, Qt.UserRole + 1)

        if role == "workspace":
            workspace = Path(path)
            self.window.current_workspace = workspace
            self.window.ws_combo.setCurrentText(str(workspace))
            self.window.ws_info_name.setText(f"Name:  {workspace.name}")
            self.window.ws_info_path.setText(f"Path:  {workspace}")
            self.window.stack.setCurrentIndex(1)
        elif role == "package":
            package = Path(path)
            self.window.pkg_info_name.setText(f"Name:  {package.name}")
            self.window.pkg_info_path.setText(f"Path:  {package}")
            self.window.stack.setCurrentIndex(2)
        elif role == "node":
            node_name = item.text(0).split("  ", 1)[-1].strip()
            package_name = item.parent().text(0).split("  ", 1)[-1].strip()
            self.window.node_info_name.setText(f"Name:     {node_name}")
            self.window.node_info_pkg.setText(f"Package:  {package_name}")
            self.window.stack.setCurrentIndex(3)
        elif role == "launch":
            launch_file_name = Path(path).name
            package_name = item.data(0, Qt.UserRole + 2)
            self.window.launch_info_name.setText(f"File:     {launch_file_name}")
            self.window.launch_info_pkg.setText(f"Package:  {package_name}")
            self.window.launch_info_path.setText(f"Path:     {path}")
            self.window.stack.setCurrentIndex(4)

    def context_menu(self, pos):
        item = self.window.tree.itemAt(pos)
        if not item:
            return

        role = item.data(0, Qt.UserRole)
        menu = QMenu(self.window)

        if role == "workspace":
            menu.addAction("Build", self.window.workspace_actions.build_workspace)
            menu.addAction("Source", self.window.workspace_actions.source_workspace)
            menu.addAction("Add Package", self.window.workspace_actions.create_package)
            menu.addSeparator()
            menu.addAction("Remove from list", lambda: self.window.workspace_actions.remove_workspace(item))
        elif role == "package":
            menu.addAction("Build Package", self.window.workspace_actions.build_package)
            menu.addAction("Add Node", self.window.process_actions.create_node)
            menu.addAction("Open Terminal", self.window.workspace_actions.open_package_terminal)
        elif role == "node":
            menu.addAction("Run", self.window.process_actions.run_node)
            menu.addAction("Edit Source", self.window.process_actions.edit_node)
        elif role == "launch":
            menu.addAction("Run Launch", self.window.process_actions.run_launch)
            menu.addAction("Edit Source", self.window.process_actions.edit_launch)

        menu.exec_(self.window.tree.viewport().mapToGlobal(pos))

    def selected_package(self):
        item = self.window.tree.currentItem()
        if not item:
            return None

        role = item.data(0, Qt.UserRole)
        if role == "package":
            return Path(item.data(0, Qt.UserRole + 1)).name
        if role == "node":
            return item.parent().text(0).split("  ", 1)[-1].strip()
        return None
