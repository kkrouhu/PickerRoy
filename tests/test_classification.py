from framepick.classification import ResilientClassifier, categories_from_observations


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
