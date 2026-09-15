"""Package an Icon Composer preview as a static ICNS for the Qt Mac build.

The native Apple build still uses AppIcon.icon, not this flattened fallback.
No source-video material is read or changed.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("render", type=Path, help="1024px macOS Default export from Icon Composer")
    parser.add_argument("iconset", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.iconset.mkdir(parents=True, exist_ok=True)
    with Image.open(args.render) as source:
        tile = source.convert("RGBA")
        if tile.size != (1024, 1024):
            parser.error("Expected the reviewed 1024 × 1024 icon preview")
        for base in (16, 32, 128, 256, 512):
            for scale in (1, 2):
                pixels = base * scale
                side = round(pixels * 0.84)
                image = Image.new("RGBA", (pixels, pixels), (0, 0, 0, 0))
                image.alpha_composite(tile.resize((side, side), Image.Resampling.LANCZOS),
                                      ((pixels - side) // 2, (pixels - side) // 2))
                suffix = "@2x" if scale == 2 else ""
                image.save(args.iconset / f"icon_{base}x{base}{suffix}.png")
    subprocess.run(["iconutil", "-c", "icns", str(args.iconset), "-o", str(args.output)], check=True)


if __name__ == "__main__":
    main()
