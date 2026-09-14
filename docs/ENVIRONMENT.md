# 2026-09-14 检测到的开发环境

- macOS 14.6.1，Apple Silicon arm64
- Apple M3 Max：14 核 CPU、30 核 GPU、36 GB 统一内存
- Python 3.12.3
- FFmpeg/FFprobe 7.0，支持 VideoToolbox
- Git 2.44.0

首版采用 FFmpeg 稳定的 CPU 解码路径，并保留硬件加速接口。镜头分析和预览均采用流式处理。本机会优先尝试 macOS Vision 进行语义分类；如果初始化或运行失败，系统会自动切换一次到 OpenCV CPU 后端，不会因此淘汰原本有效的画面。
