"""Dialog helpers used by the main window."""

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


def show_new_workspace_dialog(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("New Workspace")
    dialog.setFixedSize(420, 200)
    layout = QFormLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(12)

    name_input = QLineEdit("ros2_ws")
    layout.addRow("Name:", name_input)

    path_row = QHBoxLayout()
    path_input = QLineEdit(str(Path.home()))
    browse = QPushButton("Browse…")
    browse.setObjectName("action_default")
    browse.setFixedWidth(80)
    browse.clicked.connect(
        lambda: path_input.setText(
            QFileDialog.getExistingDirectory(dialog, "Select Location") or path_input.text()
        )
    )
    path_row.addWidget(path_input)
    path_row.addWidget(browse)
    layout.addRow("Location:", path_row)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() != QDialog.Accepted:
        return None

    return {
        "name": name_input.text().strip() or "ros2_ws",
        "location": path_input.text().strip(),
    }


def confirm_workspace_registration(parent, warnings):
    if not warnings:
        return True

    msg = "\n".join(f"  • {warning}" for warning in warnings)
    answer = QMessageBox.question(
        parent,
        "워크스페이스 확인",
        f"경고 사항이 있습니다:\n\n{msg}\n\n그래도 등록하시겠습니까?",
        QMessageBox.Yes | QMessageBox.No,
    )
    return answer == QMessageBox.Yes


def show_new_package_dialog(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("New Package")
    dialog.setFixedSize(420, 240)
    layout = QFormLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(12)

    name_input = QLineEdit()
    name_input.setPlaceholderText("my_package")
    layout.addRow("Package Name:", name_input)

    build_type = QComboBox()
    build_type.addItems(["ament_python", "ament_cmake"])
    build_type.setObjectName("bar_combo")
    layout.addRow("Build Type:", build_type)

    deps_input = QLineEdit()
    deps_input.setPlaceholderText("rclpy std_msgs  (space separated)")
    layout.addRow("Dependencies:", deps_input)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)

    if dialog.exec_() != QDialog.Accepted:
        return None

    name = name_input.text().strip()
    if not name:
        return None

    return {
        "name": name,
        "build_type": build_type.currentText(),
        "dependencies": deps_input.text().strip(),
    }


def show_run_arguments_dialog(parent, title, cmd_preview, param_style="node"):
    dialog = QDialog(parent)
    dialog.setWindowTitle(f"실행 - {title}")
    dialog.setMinimumWidth(560)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(16, 16, 16, 12)
    layout.setSpacing(10)

    preview_label = QLabel("실행 명령:")
    preview_label.setObjectName("info_label")
    layout.addWidget(preview_label)

    preview = QLabel(f"  {cmd_preview} ...")
    preview.setObjectName("info_label")
    preview.setStyleSheet("font-family: monospace; color: #888;")
    layout.addWidget(preview)

    param_label = QLabel("파라미터 (없으면 비워두고 실행):")
    param_label.setObjectName("info_label")
    layout.addWidget(param_label)

    param_input = QLineEdit()
    if param_style == "node":
        param_input.setPlaceholderText("예: param1:=value1 param2:=value2")
    else:
        param_input.setPlaceholderText("예: map:=my_map.yaml use_sim_time:=true")
    layout.addWidget(param_input)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.button(QDialogButtonBox.Ok).setText("실행")
    buttons.button(QDialogButtonBox.Cancel).setText("취소")
    buttons.button(QDialogButtonBox.Ok).setAutoDefault(False)
    buttons.button(QDialogButtonBox.Ok).setDefault(False)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)

    if dialog.exec_() != QDialog.Accepted:
        return None, False

    params_str = param_input.text().strip()
    if param_style == "node" and params_str:
        parts = params_str.split()
        ros_args = " ".join(f"-p '{part}'" for part in parts)
        return f"--ros-args {ros_args}", True
    if param_style == "launch" and params_str:
        parts = params_str.split()
        quoted = " ".join(f"'{part}'" for part in parts)
        return quoted, True
    return "", True


def choose_editor_dialog(parent, file_path, editors, preferred_cmd):
    dialog = QDialog(parent)
    dialog.setWindowTitle("편집기 선택")
    dialog.setFixedSize(380, 320)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 16)
    layout.setSpacing(10)

    label = QLabel(f"편집기를 선택하세요:\n{Path(file_path).name}")
    label.setObjectName("info_label")
    layout.addWidget(label)

    editor_list = QListWidget()
    editor_list.setObjectName("proj_tree")
    editor_list.setFocusPolicy(Qt.ClickFocus)
    for display_label, cmd in editors:
        item = QListWidgetItem(display_label)
        item.setData(Qt.UserRole, cmd)
        if cmd == preferred_cmd:
            item.setSelected(True)
        editor_list.addItem(item)
    if not editor_list.selectedItems() and editor_list.count() > 0:
        editor_list.item(0).setSelected(True)
    editor_list.setMinimumHeight(160)
    layout.addWidget(editor_list)

    remember_box = QCheckBox("이 편집기를 기본으로 저장")
    remember_box.setChecked(True)
    layout.addWidget(remember_box)

    buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    ok_btn = buttons.button(QDialogButtonBox.Ok)
    if ok_btn:
        ok_btn.setAutoDefault(False)
        ok_btn.setDefault(False)
    layout.addWidget(buttons)

    if dialog.exec_() != QDialog.Accepted:
        return None

    selected = editor_list.selectedItems()
    if not selected:
        return None

    return {
        "command": selected[0].data(Qt.UserRole),
        "remember": remember_box.isChecked(),
    }
