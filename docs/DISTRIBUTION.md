# 下载、安装与发布

## 普通用户下载哪个文件

- Apple 芯片 Mac（M1/M2/M3/M4 及后续）：`PickerRoy-macOS-Apple-Silicon.zip`
- Intel Mac：`PickerRoy-macOS-Intel.zip`
- 64 位 Windows 10/11：`PickerRoy-Windows-x64.zip`
- `PickerRoy-Codex-Skill-*.zip` 不是应用，只给 Codex 增加 PickerRoy 的安装、使用与排错知识。

每次 Release 同时提供中文、English 和中英双语 PDF 使用说明书。Skill 还可帮助 Codex生成不包含媒体和路径的本机偏好摘要，并在用户明确要求时做源码级定向优化。

独立应用已经包含 Python、运行库、FFmpeg/FFprobe 和热门视觉模型。普通用户无需安装 Codex，也无需执行命令行安装。

## 首次打开

当前自动发布包没有使用 Roy 自己的 Apple Developer ID 或 Windows 代码签名证书，因此系统可能在首次启动时显示安全确认。

- macOS：解压后把 `PickerRoy.app` 拖到“应用程序”。如果双击被拦截，按住 Control 点按应用，选择“打开”，再次确认“打开”。不要全局关闭 Gatekeeper。
- Windows：完整解压 ZIP，保留整个 `PickerRoy` 文件夹，再双击文件夹内的 `PickerRoy.exe`。如 SmartScreen 提示，请先核对下载来源和 SHA-256。

要实现完全无提示的商业级安装，后续需要 Apple Developer ID 签名与公证，以及 Windows 代码签名证书；构建流程已经为后续接入留出位置。

## 自动发布

推送 `v*` 标签后，`.github/workflows/build-release.yml` 会在 macOS Intel、macOS Apple Silicon 和 Windows x64 环境分别测试、构建、运行独立应用自检、打包并创建 GitHub Release。PyInstaller 不是交叉编译器，因此三个包必须在对应系统分别构建。

每个 ZIP 都有同名 `.sha256` 文件。Windows 用户必须保留解压后的整个目录，不能只移动 EXE。
