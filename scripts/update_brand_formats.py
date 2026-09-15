"""Generate platform image formats from the reviewed ROY artwork (no user media)."""
from pathlib import Path
import shutil
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
# Static assets remain useful for the Python desktop package and older tooling.
# The native Xcode target now selects AppIcon.icon and generates its own legacy
# renditions; never recreate a competing AppIcon inside Assets.xcassets.
catalog = ROOT / "apple/CompatibilityAssets/AppIcon.appiconset"
catalog.mkdir(parents=True, exist_ok=True)
with Image.open(ROOT / "assets/PickerRoy-logo.png") as source:
    source.save(ROOT / "assets/PickerRoy.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    # iOS supplies its own icon mask: the 1024px source must be opaque and square.
    opaque = Image.new("RGB", (1024, 1024), "white")
    opaque.paste(source, mask=source.getchannel("A"))
    opaque.save(catalog / "icon-ios-1024.png")

iconset = ROOT / "work/PickerRoy.iconset"
for pixels, source in [(16, "icon_16x16.png"), (32, "icon_32x32.png"), (64, "icon_32x32@2x.png"),
                       (128, "icon_128x128.png"), (256, "icon_256x256.png"),
                       (512, "icon_512x512.png"), (1024, "icon_512x512@2x.png")]:
    if (iconset / source).is_file():
        shutil.copy2(iconset / source, catalog / f"icon-{pixels}.png")
