# PickerRoy third-party notices

PickerRoy combines its own application code with separately maintained open-source components. The notices below are provided for attribution and license compliance; the exact versions in a release can be inspected in the build workflow and the bundled binaries.

## FFmpeg and FFprobe

PickerRoy invokes FFmpeg and FFprobe as separate command-line programs for local video decoding, metadata inspection, frame extraction, cropping, and image export.

- Project: <https://ffmpeg.org/>
- Source: <https://ffmpeg.org/download.html>
- License information: <https://ffmpeg.org/legal.html>
- macOS release builds use the Homebrew FFmpeg formula; Windows builds use the Chocolatey FFmpeg package.
- The distributed builds may enable GPL components. A copy of GNU GPL v3 is included at `licenses/FFmpeg-GPLv3.txt`.

PickerRoy does not modify FFmpeg source code. Run the bundled `ffmpeg -version` to see the exact version and configuration used in a particular package.

## Intrinsic Image Popularity Assessment (IIPA)

The bundled ONNX model was converted from the ResNet-50 weights released with “Intrinsic Image Popularity Assessment” by Keyan Ding, Kede Ma, and Shiqi Wang (ACM Multimedia 2019).

- Upstream repository and weights: <https://github.com/dingkeyan93/Intrinsic-Image-Popularity>
- Paper: <https://arxiv.org/abs/1907.01985>
- Upstream repository states that the project uses the MIT License.
- Conversion provenance and hashes: `models/INTRINSIC_POPULARITY.md`

## Python runtime libraries

- Qt for Python / PySide6: LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only (with a commercial-license option from Qt).
- OpenCV Python: Apache-2.0, with bundled third-party notices supplied by the package.
- NumPy: BSD-3-Clause.
- Pillow: HPND.
- PySceneDetect: BSD-3-Clause.
- PyInstaller: GPL-2.0-or-later with a special exception that permits distributing bundled applications under the application's own terms.
- PyObjC components in supported macOS builds: MIT.

For authoritative terms, consult each component's source distribution and metadata included by the build tooling.
