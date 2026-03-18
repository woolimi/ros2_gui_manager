"""UI builder helpers for the main window."""

import os

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from ..constants import MONO_FONT_FAMILY
from .runtime import ProcessTabManager
from .widgets import make_separator


class MainWindowUiBuilder:
    def __init__(self, window):
        self.window = window

    def build_ui(self):
        root = QWidget()
        self.window.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setSpacing(0)
        root_layout.setContentsMargins(0, 0, 0, 0)

        root_layout.addWidget(self.make_topbar())

        body = QSplitter(Qt.Horizontal)
        body.setHandleWidth(2)
        root_layout.addWidget(body, stretch=1)

        body.addWidget(self.make_left_panel())

        right = QSplitter(Qt.Vertical)
        right.setHandleWidth(2)
        body.addWidget(right)

        right.addWidget(self.make_action_area())
        right.addWidget(self.make_output_panel())

        body.setSizes([280, 1000])
        right.setSizes([560, 260])

        self.window.statusBar().showMessage("Ready  -  ROS2 GUI Manager")

    def make_topbar(self):
        bar = QWidget()
        bar.setFixedHeight(56)
        bar.setObjectName("topbar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        logo = QLabel("◈  ROS2 GUI Manager")
        logo.setObjectName("logo")
        layout.addWidget(logo)
        layout.addStretch()

        distro_label = QLabel("Distro")
        distro_label.setObjectName("bar_label")
        self.window.distro_combo = QComboBox()
        self.window.distro_combo.setMinimumWidth(120)
        self.window.distro_combo.setObjectName("bar_combo")
        self.window.distro_combo.currentTextChanged.connect(self.window.app_controller.on_distro_changed)
        layout.addWidget(distro_label)
        layout.addWidget(self.window.distro_combo)

        sep = QLabel("│")
        sep.setObjectName("bar_sep")
        layout.addWidget(sep)

        ws_label = QLabel("Workspace")
        ws_label.setObjectName("bar_label")
        self.window.ws_combo = QComboBox()
        self.window.ws_combo.setMinimumWidth(220)
        self.window.ws_combo.setObjectName("bar_combo")
        self.window.ws_combo.currentTextChanged.connect(self.window.app_controller.on_workspace_changed)
        layout.addWidget(ws_label)
        layout.addWidget(self.window.ws_combo)

        sep2 = QLabel("│")
        sep2.setObjectName("bar_sep")
        layout.addWidget(sep2)

        domain_label = QLabel("Domain ID")
        domain_label.setObjectName("bar_label")
        self.window.domain_spin = QSpinBox()
        self.window.domain_spin.setRange(0, 232)
        self.window.domain_spin.setFixedWidth(72)
        self.window.domain_spin.setObjectName("bar_combo")
        self.window.domain_spin.setValue(int(os.environ.get("ROS_DOMAIN_ID", "0")))
        self.window.domain_spin.valueChanged.connect(self.window.app_controller.on_domain_id_changed)
        layout.addWidget(domain_label)
        layout.addWidget(self.window.domain_spin)

        sep3 = QLabel("│")
        sep3.setObjectName("bar_sep")
        layout.addWidget(sep3)

        self.window.tool_btns = []
        for label, slot in [
            ("Terminal", self.window.app_controller.open_terminal),
            ("RViz2", self.window.app_controller.open_rviz),
            ("rqt", self.window.app_controller.open_rqt),
        ]:
            button = QPushButton(label)
            button.setObjectName("topbar_btn")
            button.clicked.connect(slot)
            button.setEnabled(False)
            layout.addWidget(button)
            self.window.tool_btns.append(button)

        return bar

    def make_left_panel(self):
        panel = QWidget()
        panel.setObjectName("left_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel("  PROJECT TREE")
        header.setObjectName("section_header")
        header.setFixedHeight(36)
        layout.addWidget(header)

        self.window.tree = QTreeWidget()
        self.window.tree.setHeaderHidden(True)
        self.window.tree.setObjectName("proj_tree")
        self.window.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.window.tree.customContextMenuRequested.connect(self.window.tree_controller.context_menu)
        self.window.tree.itemClicked.connect(self.window.tree_controller.on_item_clicked)
        layout.addWidget(self.window.tree, stretch=1)

        btn_area = QWidget()
        btn_area.setObjectName("tree_btn_area")
        btn_layout = QHBoxLayout(btn_area)
        btn_layout.setContentsMargins(8, 6, 8, 6)
        btn_layout.setSpacing(6)

        button_specs = [
            ("+ New", self.window.workspace_actions.create_workspace),
            ("Open WS", self.window.workspace_actions.open_workspace),
            ("+ Package", self.window.workspace_actions.create_package),
        ]
        for label, slot in button_specs:
            button = QPushButton(label)
            button.setObjectName("tree_add_btn")
            button.clicked.connect(slot)
            btn_layout.addWidget(button)

        layout.addWidget(btn_area)
        return panel

    def make_action_area(self):
        self.window.stack = QStackedWidget()
        self.window.stack.setObjectName("action_stack")

        self.window.stack.addWidget(self.page_welcome())
        self.window.stack.addWidget(self.page_workspace())
        self.window.stack.addWidget(self.page_package())
        self.window.stack.addWidget(self.page_node())
        self.window.stack.addWidget(self.page_launch())

        return self.window.stack

    def page_welcome(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel("Select an item from the tree\nor create a new workspace")
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("welcome_hint")
        layout.addWidget(label)
        return page

    def page_workspace(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("[WS]  Workspace")
        title.setObjectName("page_title")
        layout.addWidget(title)

        self.window.ws_info_name = QLabel("Name: -")
        self.window.ws_info_path = QLabel("Path: -")
        self.window.ws_info_name.setObjectName("info_label")
        self.window.ws_info_path.setObjectName("info_label")
        layout.addWidget(self.window.ws_info_name)
        layout.addWidget(self.window.ws_info_path)
        layout.addWidget(make_separator())

        grid = QGridLayout()
        grid.setSpacing(10)
        actions = [
            ("Build Workspace", "primary", self.window.workspace_actions.build_workspace),
            ("Clean & Build", "primary", self.window.workspace_actions.clean_and_build),
            ("Source Workspace", "default", self.window.workspace_actions.source_workspace),
            ("Open in Terminal", "default", self.window.workspace_actions.open_workspace_terminal),
            ("Clean (build/install/log)", "danger", self.window.workspace_actions.clean_workspace),
        ]
        for index, (label, style, slot) in enumerate(actions):
            button = QPushButton(label)
            button.setObjectName(f"action_{style}")
            button.clicked.connect(slot)
            grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(grid)
        layout.addStretch()
        return page

    def page_package(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("[PKG]  Package")
        title.setObjectName("page_title")
        layout.addWidget(title)

        self.window.pkg_info_name = QLabel("Name: -")
        self.window.pkg_info_path = QLabel("Path: -")
        self.window.pkg_info_name.setObjectName("info_label")
        self.window.pkg_info_path.setObjectName("info_label")
        layout.addWidget(self.window.pkg_info_name)
        layout.addWidget(self.window.pkg_info_path)
        layout.addWidget(make_separator())

        group = QGroupBox("  Add New Node")
        group.setObjectName("card_group")
        group_layout = QFormLayout(group)
        group_layout.setSpacing(10)
        group_layout.setContentsMargins(14, 18, 14, 14)

        self.window.new_node_input = QLineEdit()
        self.window.new_node_input.setPlaceholderText("e.g. my_publisher")
        group_layout.addRow("Node name:", self.window.new_node_input)

        create_button = QPushButton("＋  Create Node")
        create_button.setObjectName("action_primary")
        create_button.clicked.connect(self.window.process_actions.create_node)
        group_layout.addRow("", create_button)
        layout.addWidget(group)

        layout.addWidget(make_separator())

        grid = QGridLayout()
        grid.setSpacing(10)
        for index, (label, style, slot) in enumerate(
            [
                ("Build Package", "default", self.window.workspace_actions.build_package),
                ("Clean Package", "danger", self.window.workspace_actions.clean_package),
                ("Open in Terminal", "default", self.window.workspace_actions.open_package_terminal),
            ]
        ):
            button = QPushButton(label)
            button.setObjectName(f"action_{style}")
            button.clicked.connect(slot)
            grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(grid)
        layout.addStretch()
        return page

    def page_node(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("[NODE]  Node")
        title.setObjectName("page_title")
        layout.addWidget(title)

        self.window.node_info_name = QLabel("Name: -")
        self.window.node_info_pkg = QLabel("Package: -")
        self.window.node_info_name.setObjectName("info_label")
        self.window.node_info_pkg.setObjectName("info_label")
        layout.addWidget(self.window.node_info_name)
        layout.addWidget(self.window.node_info_pkg)
        layout.addWidget(make_separator())

        grid = QGridLayout()
        grid.setSpacing(10)
        for index, (label, style, slot) in enumerate(
            [
                ("Run Node", "primary", self.window.process_actions.run_node),
                ("Edit Source", "default", self.window.process_actions.edit_node),
            ]
        ):
            button = QPushButton(label)
            button.setObjectName(f"action_{style}")
            button.clicked.connect(slot)
            grid.addWidget(button, 0, index)
        layout.addLayout(grid)
        layout.addStretch()
        return page

    def page_launch(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("[LAUNCH]  Launch File")
        title.setObjectName("page_title")
        layout.addWidget(title)

        self.window.launch_info_name = QLabel("File: -")
        self.window.launch_info_pkg = QLabel("Package: -")
        self.window.launch_info_path = QLabel("Path: -")
        for label in [self.window.launch_info_name, self.window.launch_info_pkg, self.window.launch_info_path]:
            label.setObjectName("info_label")
            layout.addWidget(label)
        layout.addWidget(make_separator())

        grid = QGridLayout()
        grid.setSpacing(10)
        for index, (label, style, slot) in enumerate(
            [
                ("Run Launch", "primary", self.window.process_actions.run_launch),
                ("Edit Source", "default", self.window.process_actions.edit_launch),
            ]
        ):
            button = QPushButton(label)
            button.setObjectName(f"action_{style}")
            button.setAutoDefault(False)
            button.setDefault(False)
            button.clicked.connect(slot)
            grid.addWidget(button, 0, index)
        layout.addLayout(grid)
        layout.addStretch()
        return page

    def make_output_panel(self):
        panel = QWidget()
        panel.setObjectName("output_panel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.window.tab_widget = QTabWidget()
        self.window.tab_widget.setObjectName("terminal_tabs")
        self.window.tab_widget.setTabsClosable(True)
        layout.addWidget(self.window.tab_widget)

        self.window.process_tabs = ProcessTabManager(self.window.tab_widget, MONO_FONT_FAMILY)
        self.window.tab_widget.tabCloseRequested.connect(
            lambda index: self.window.process_tabs.handle_tab_close_request(self.window, index)
        )

        self.window.poll_timer = QTimer()
        self.window.poll_timer.setInterval(1000)
        self.window.poll_timer.timeout.connect(self.window.process_tabs.poll_processes)
        self.window.poll_timer.start()
        return panel
