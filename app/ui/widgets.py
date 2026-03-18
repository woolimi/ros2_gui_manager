"""Reusable UI widgets and helpers."""

from PyQt5.QtWidgets import QFrame


def make_separator():
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setFrameShadow(QFrame.Sunken)
    line.setStyleSheet("color: #2d2d44;")
    return line
