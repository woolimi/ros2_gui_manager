"""Background worker threads for commands and nodes."""

import os
import signal
import subprocess
import threading

from PyQt5.QtCore import QThread, pyqtSignal

from .ros_env import BASH

MAX_TAB_LINES = 1000
FLUSH_INTERVAL_MS = 500
MAX_BUF_LINES = 200


class WorkerThread(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)

    def __init__(self, cmd, env=None, cwd=None):
        super().__init__()
        self.cmd = cmd
        self.env = env
        self.cwd = str(cwd) if cwd else None

    def run(self):
        try:
            proc = subprocess.Popen(
                [BASH, "-c", self.cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=self.env,
                cwd=self.cwd,
                text=True,
                bufsize=1,
            )
            for line in iter(proc.stdout.readline, ""):
                self.output_signal.emit(line.rstrip())
            proc.wait()
            self.finished_signal.emit(proc.returncode)
        except Exception as exc:
            self.output_signal.emit(f"[ERROR] {exc}")
            self.finished_signal.emit(1)


class NodeWorkerThread(QThread):
    batch_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)

    def __init__(self, cmd, env=None, cwd=None):
        super().__init__()
        self.cmd = cmd
        self.env = env
        self.cwd = str(cwd) if cwd else None
        self.proc = None
        self._buf = []
        self._lock = threading.Lock()

    def run(self):
        import time

        try:
            self.proc = subprocess.Popen(
                [BASH, "-c", self.cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=self.env,
                cwd=self.cwd,
                text=True,
                bufsize=1,
                preexec_fn=os.setsid,
            )

            last_flush = time.monotonic()
            for line in iter(self.proc.stdout.readline, ""):
                with self._lock:
                    self._buf.append(line.rstrip())
                    if len(self._buf) > MAX_BUF_LINES:
                        drop = len(self._buf) - MAX_BUF_LINES
                        del self._buf[:drop]

                now = time.monotonic()
                if now - last_flush >= FLUSH_INTERVAL_MS / 1000:
                    self._flush()
                    last_flush = now

            self._flush()
            self.proc.wait()
            self.finished_signal.emit(self.proc.returncode)
        except Exception as exc:
            self.batch_signal.emit(f"[ERROR] {exc}")
            self.finished_signal.emit(1)

    def _flush(self):
        with self._lock:
            if not self._buf:
                return
            batch = "\n".join(self._buf)
            self._buf.clear()
        self.batch_signal.emit(batch)

    def kill_node(self):
        """SIGINT -> wait -> SIGTERM -> wait -> SIGKILL."""
        if not self.proc:
            return
        try:
            process_group_id = os.getpgid(self.proc.pid)
        except (ProcessLookupError, OSError):
            return

        def _do_kill():
            import time

            for sig, wait_sec in [
                (signal.SIGINT, 3),
                (signal.SIGTERM, 2),
                (signal.SIGKILL, 0),
            ]:
                try:
                    if self.proc.poll() is not None:
                        break
                    os.killpg(process_group_id, sig)
                except (ProcessLookupError, OSError):
                    break

                if wait_sec:
                    deadline = time.time() + wait_sec
                    while time.time() < deadline:
                        if self.proc.poll() is not None:
                            break
                        time.sleep(0.1)

            try:
                self.proc.wait(timeout=1)
            except Exception:
                pass

        threading.Thread(target=_do_kill, daemon=True).start()
