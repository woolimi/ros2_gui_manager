"""Application bootstrap and entrypoint."""

import sys

from PyQt5.QtWidgets import QApplication

from .ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ROS2 GUI Manager")
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
