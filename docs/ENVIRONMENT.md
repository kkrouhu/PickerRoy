# Development environment detected on 2026-09-14

- macOS 14.6.1, Apple Silicon arm64
- Apple M3 Max: 14 CPU cores, 30 GPU cores, 36 GB unified memory
- Python 3.12.3
- FFmpeg/FFprobe 7.0 with VideoToolbox support
- Git 2.44.0

The first implementation uses FFmpeg's stable CPU decode path and keeps hardware acceleration as an optimization seam. Scene analysis and previews are streamed. macOS Vision is attempted locally for semantic labels; any initialization or runtime failure switches once to the OpenCV CPU backend without rejecting valid frames.

