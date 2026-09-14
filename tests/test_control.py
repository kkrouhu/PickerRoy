import threading
import time

import pytest

from framepick.control import AnalysisCancelled, AnalysisControl


def test_cancel_releases_a_paused_checkpoint():
    control = AnalysisControl()
    control.pause()
    outcome = []

    def wait_at_checkpoint():
        try:
            control.checkpoint()
        except AnalysisCancelled:
            outcome.append("cancelled")

    thread = threading.Thread(target=wait_at_checkpoint)
    thread.start()
    time.sleep(0.03)
    assert thread.is_alive()
    control.cancel()
    thread.join(timeout=1)
    assert outcome == ["cancelled"]
