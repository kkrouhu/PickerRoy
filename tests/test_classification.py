from framepick.classification import ResilientClassifier, categories_from_observations
import platform
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
    labels, faces = AppleVisionClassifier().classify(path)
    assert labels and len(labels) <= 20
    assert all(isinstance(item["label"], str) and 0 <= item["confidence"] <= 1 for item in labels)
    assert faces >= 0
