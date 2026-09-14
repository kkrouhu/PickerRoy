# PickerRoy support reference

## App and Skill are different downloads

- Desktop app: the thing an ordinary user opens to process videos. It does not need Codex.
- Codex Skill: a small instruction bundle that teaches Codex how to install, explain, test, and troubleshoot PickerRoy. It requires Codex or another compatible agent that supports skills.

## Release files

- `PickerRoy-macOS-Apple-Silicon.zip`: M1/M2/M3/M4 and later Apple-chip Macs.
- `PickerRoy-macOS-Intel.zip`: older Intel Macs.
- `PickerRoy-Windows-x64.zip`: 64-bit Windows 10/11.
- `PickerRoy-Codex-Skill-vX.Y.Z.zip`: optional Codex helper skill, not the app.
- Matching `.sha256` files allow download-integrity verification.

## Installation

### macOS

Unzip the matching package, drag `PickerRoy.app` to Applications, then open it. The current community build is ad-hoc signed rather than Apple-notarized. If Gatekeeper blocks the first launch, Control-click the app, choose Open, then confirm Open. Do not disable Gatekeeper globally.

### Windows

Unzip the archive completely and keep the `PickerRoy` folder intact. Open the folder and double-click `PickerRoy.exe`. If SmartScreen appears on an unsigned community build, verify that the download came from the expected GitHub Release and that the SHA-256 matches before choosing to run it.

## Normal workflow

1. Open Settings. “运行环境自检” should show that video read/export and video info recognition are ready.
2. Drag in one or more videos or a folder. Confirm the green banner shows the newly added count and total count.
3. Choose original, 1:1, 3:2, 2:3, 4:3, 3:4, 16:9, or 9:16 before analysis.
4. Optionally choose Balanced, Portrait, Action, Landscape, or Product mode.
5. Start analysis and wait for the completion summary.
6. Filter by category, inspect large previews, and mark frames Keep, Reject, or Favorite.
7. Export kept/favorite frames as PNG or JPEG. Exports use source resolution and the selected crop.
8. In Preference Training, select A or B. New choices participate from the next analysis.

## Diagnosis

- Import button remains disabled: the environment check failed or no supported video was added.
- No supported video found: use MP4, MOV, M4V, MKV, AVI, WEBM, MTS, M2TS, or MXF.
- Analysis failure: open the run log from the left sidebar and preserve the final error lines.
- No export: first mark at least one frame Keep or Favorite.
- Missing Windows files: re-extract the full ZIP; do not move only the EXE out of its folder.
- Unexpected color with HDR/BT.2020: compare the PNG in a color-managed viewer; do not assume a social-media viewer is displaying HDR correctly.

## Developer verification

From the repository root:

```bash
python -m pytest
python scripts/build_standalone.py
```

The packaged executable supports a release smoke test:

```bash
PickerRoy --self-test /path/to/input.mp4 /path/to/output-directory
```

A successful run writes `self-test-report.json` and at least one full-resolution exported image.
