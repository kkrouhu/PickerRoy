from __future__ import annotations

import threading


class AnalysisCancelled(RuntimeError):
    """Raised when a user cooperatively cancels an analysis."""

    def __init__(self) -> None:
        super().__init__("用户已取消分析")


class AnalysisControl:
    """Thread-safe pause/resume/cancel state shared by the GUI and analyzer."""

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._paused = False
        self._cancelled = False

    @property
    def is_paused(self) -> bool:
        with self._condition:
            return self._paused

    @property
    def is_cancelled(self) -> bool:
        with self._condition:
            return self._cancelled

    def pause(self) -> None:
        with self._condition:
            if not self._cancelled:
                self._paused = True

    def resume(self) -> None:
        with self._condition:
            self._paused = False
            self._condition.notify_all()

    def cancel(self) -> None:
        with self._condition:
            self._cancelled = True
            self._paused = False
            self._condition.notify_all()

    def checkpoint(self) -> None:
        """Wait while paused and raise promptly when cancellation is requested."""
        with self._condition:
            while self._paused and not self._cancelled:
                self._condition.wait(timeout=0.12)
            if self._cancelled:
                raise AnalysisCancelled()
