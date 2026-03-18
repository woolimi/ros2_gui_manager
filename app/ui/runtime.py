"""Runtime helpers for output tabs and running processes."""

import threading

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMessageBox, QPlainTextEdit

from ..workers import MAX_TAB_LINES


class ProcessTabManager:
    def __init__(self, tab_widget, font_family):
        self.tab_widget = tab_widget
        self.font_family = font_family
        self.output = self._create_output_widget()
        self.tab_widget.addTab(self.output, "OUTPUT")
        self.node_tabs = {}

    def _create_output_widget(self):
        widget = QPlainTextEdit()
        widget.setReadOnly(True)
        widget.setObjectName("output_text")
        widget.setFont(QFont(self.font_family, 10))
        widget.setMaximumBlockCount(MAX_TAB_LINES)
        return widget

    def log_output(self, text):
        self.output.appendPlainText(text)

    def add_process_tab(self, label):
        tab_output = self._create_output_widget()
        tab_index = self.tab_widget.addTab(tab_output, label)
        self.tab_widget.setCurrentIndex(tab_index)
        return tab_index, tab_output

    def attach_worker(self, tab_index, tab_output, worker):
        def _append(batch, widget=tab_output):
            widget.appendPlainText(batch)

        def _on_finish(code, widget=tab_output):
            status = "✓ 완료" if code == 0 else f"✗ 종료({code})"
            for index in range(self.tab_widget.count()):
                if self.tab_widget.widget(index) is widget:
                    base = self.tab_widget.tabText(index).replace("[RUN] ", "").replace("[LAUNCH] ", "").replace("[DONE] ", "")
                    self.tab_widget.setTabText(index, f"[DONE] {base}")
                    break
            widget.appendPlainText(f"\n{'─' * 48}\n[{status}]")

        worker.batch_signal.connect(_append)
        worker.finished_signal.connect(_on_finish)
        self.node_tabs[tab_index] = worker

    def poll_processes(self):
        for index, worker in list(self.node_tabs.items()):
            if worker.proc and worker.proc.poll() is not None:
                tab_text = self.tab_widget.tabText(index)
                if not tab_text.startswith("[DONE] "):
                    base = tab_text.replace("[RUN] ", "").replace("[LAUNCH] ", "").replace("[DONE] ", "")
                    self.tab_widget.setTabText(index, f"[DONE] {base}")

    def handle_tab_close_request(self, parent, index):
        tab_name = self.tab_widget.tabText(index)
        worker = self.node_tabs.get(index)
        is_running = worker and worker.proc and worker.proc.poll() is None

        if index == 0:
            if (
                QMessageBox.question(
                    parent,
                    "탭 닫기",
                    "OUTPUT 탭을 닫으면 빌드 로그가 사라집니다.\n정말 닫을까요?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                != QMessageBox.Yes
            ):
                return
            self.close_tab(index)
            return

        if is_running:
            answer = QMessageBox.question(
                parent,
                "탭 닫기",
                f"'{tab_name}' 이 실행 중입니다.\n"
                "프로세스에 종료 신호를 보낼까요?\n\n"
                "출력창에서 [완료] 확인 후 탭이 자동으로 닫힙니다.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                tab_output = self.tab_widget.widget(index)
                if isinstance(tab_output, QPlainTextEdit):
                    tab_output.appendPlainText(
                        "\n─────────────────────────────────────\n"
                        "[안내] 노드가 실행 중입니다.\n"
                        "       출력창에서 [완료] 확인 후 X 버튼을 눌러 닫아주세요.\n"
                        "─────────────────────────────────────"
                    )
                self.tab_widget.setCurrentIndex(index)
                return

            tab_output = self.tab_widget.widget(index)
            if isinstance(tab_output, QPlainTextEdit):
                tab_output.appendPlainText(
                    "\n─────────────────────────────────────\n"
                    "[종료 요청 중...] SIGINT 전송\n"
                    "─────────────────────────────────────"
                )

            def _wait_and_close():
                import time

                deadline = time.time() + 5
                worker.kill_node()
                while time.time() < deadline:
                    if worker.proc and worker.proc.poll() is not None:
                        break
                    time.sleep(0.2)
                QTimer.singleShot(300, lambda: self.close_tab_by_worker(worker))

            threading.Thread(target=_wait_and_close, daemon=True).start()
            return

        tab_output = self.tab_widget.widget(index)
        finished = True
        if isinstance(tab_output, QPlainTextEdit):
            content = tab_output.toPlainText()
            finished = "[완료]" in content or "[종료" in content or "✓" in content

        if not finished:
            answer = QMessageBox.question(
                parent,
                "탭 닫기",
                f"'{tab_name}'\n출력창에서 [완료] 가 확인되지 않았습니다.\n그래도 닫을까요?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return

        self.close_tab(index)

    def close_tab_by_worker(self, worker):
        for index, current_worker in list(self.node_tabs.items()):
            if current_worker is worker:
                self.close_tab(index)
                return

    def close_tab(self, index):
        self.tab_widget.removeTab(index)

        if index == 0:
            self.output = self._create_output_widget()
            self.tab_widget.insertTab(0, self.output, "OUTPUT")
            self.tab_widget.setCurrentIndex(0)

        new_tabs = {}
        for old_index, worker in self.node_tabs.items():
            new_index = old_index if old_index < index else old_index - 1
            if old_index != index:
                new_tabs[new_index] = worker
        self.node_tabs = new_tabs
