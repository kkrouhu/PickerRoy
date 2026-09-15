"""Keep layered app-icon input separate from archived compatibility artwork."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_layered_icon_package_has_all_referenced_artwork():
    package = ROOT / "apple/PickerRoyApple/AppIcon.icon"
    document = json.loads((package / "icon.json").read_text(encoding="utf-8"))
    layers = [layer for group in document["groups"] for layer in group["layers"]]
    assert layers, "The system app icon must contain foreground artwork"
    for layer in layers:
        if name := layer.get("image-name"):
            asset = package / "Assets" / name
            assert asset.is_file(), f"Missing Icon Composer artwork: {name}"
    foreground = next(layer for layer in layers if layer.get("name") == "PickerRoy-foreground")
    fills = {
        item["appearance"]: item["value"].get("solid")
        for item in foreground["fill-specializations"]
    }
    # Automatic mono conversion obscured the outlined wordmark in device-style
    # previews. Preserve the reviewed white overrides for dark and tinted modes.
    white = "extended-srgb:1.00000,1.00000,1.00000,1.00000"
    assert fills.get("dark") == white
    assert fills.get("tinted") == white
    assert not document["supported-platforms"].get("circles")
    assert not (ROOT / "apple/PickerRoyApple/Assets.xcassets/AppIcon.appiconset").exists()


def test_static_compatibility_archive_remains_complete():
    catalog = ROOT / "apple/CompatibilityAssets/AppIcon.appiconset"
    document = json.loads((catalog / "Contents.json").read_text(encoding="utf-8"))
    images = document["images"]
    assert images, "Keep the static icon set available for rollback and older tooling"
    for entry in images:
        if filename := entry.get("filename"):
            assert (catalog / filename).is_file(), f"Missing compatibility icon: {filename}"
    for name in ("BrandForeground", "BrandMark"):
        assert (ROOT / f"apple/PickerRoyApple/Assets.xcassets/{name}.imageset").is_dir()
