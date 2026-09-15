from framepick.classification import ResilientClassifier, categories_from_observations
import platform
import os
import pytest


class Broken:
    name = "broken"

    def __init__(self):
        self.calls = 0

    def classify(self, path):
        self.calls += 1
        raise RuntimeError("backend unavailable")


class Working:
    name = "working"

    def classify(self, path):
        return [{"label": "person", "confidence": 0.8}], 1


def test_classifier_falls_back_once_and_stays_healthy():
    broken = Broken()
    classifier = ResilientClassifier(broken, Working())
    assert classifier.classify("unused") == ([{"label": "person", "confidence": 0.8}], 1)
    assert classifier.classify("unused") == ([{"label": "person", "confidence": 0.8}], 1)
    assert broken.calls == 1
    assert classifier.active_name == "working"


def test_plant_observation_has_its_own_category():
    labels, confidence = categories_from_observations(
        [{"label": "flower botanical garden", "confidence": 0.88}], 0, 0.1, 0.08, 0.75
    )
    assert "Plant" in labels
    assert confidence["Plant"] == 0.88


@pytest.mark.skipif(platform.system() != "Darwin", reason="Apple Vision requires macOS")
def test_apple_vision_native_options_bridge(tmp_path):
    pytest.importorskip("Vision")
    import cv2
    import numpy as np
    from framepick.classification import AppleVisionClassifier
    image = np.zeros((128, 128, 3), dtype=np.uint8)
    image[:, :, 0] = np.arange(128, dtype=np.uint8)[None, :] * 2
    image[:, :, 1] = np.arange(128, dtype=np.uint8)[:, None] * 2
    image[:, :, 2] = 110
    path = tmp_path / "vision-bridge.png"
    assert cv2.imwrite(str(path), image)
    try:
        labels, faces = AppleVisionClassifier().classify(path)
    except RuntimeError as exc:
        # Some hosted ARM macOS VMs have no usable Vision inference context.
        # This is not the NSDictionary regression: all other errors still fail.
        # The bridge contract is independently covered without Apple hardware below.
        if os.environ.get("GITHUB_ACTIONS") == "true" and 'Domain=com.apple.Vision Code=9 "Could not create inference context"' in str(exc):
            pytest.skip("Hosted runner has no Vision inference context; real-Mac integration required")
        raise
    assert labels and len(labels) <= 20
    assert all(isinstance(item["label"], str) and 0 <= item["confidence"] <= 1 for item in labels)
    assert faces >= 0


@pytest.mark.parametrize("perform_result", [True, (True, None)])
def test_vision_uses_native_options_not_python_dict(tmp_path, perform_result):
    from framepick.classification import AppleVisionClassifier
    from types import SimpleNamespace

    native_options = object()
    received = []

    class Request:
        @classmethod
        def alloc(cls):
            return cls()

        def init(self):
            return self

        def results(self):
            return []

    class Handler(Request):
        def initWithURL_options_(self, url, options):
            received.append(options)
            assert options is native_options
            return self

        def performRequests_error_(self, requests, error):
            assert len(requests) == 2
            return perform_result

    classifier = AppleVisionClassifier.__new__(AppleVisionClassifier)
    classifier.NSURL = SimpleNamespace(fileURLWithPath_=lambda path: path)
    classifier.NSDictionary = SimpleNamespace(dictionary=lambda: native_options)
    classifier.VNClassifyImageRequest = Request
    classifier.VNDetectFaceRectanglesRequest = Request
    classifier.VNImageRequestHandler = Handler
    assert classifier.classify(tmp_path / "unused.png") == ([], 0)
    assert received == [native_options]
