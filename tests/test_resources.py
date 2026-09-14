from framepick.resources import resource_path


def test_resource_path_uses_pyinstaller_bundle(tmp_path, monkeypatch):
    model = tmp_path / "models" / "test.onnx"
    model.parent.mkdir()
    model.write_bytes(b"model")
    monkeypatch.setattr("sys._MEIPASS", str(tmp_path), raising=False)
    assert resource_path("models/test.onnx") == model
