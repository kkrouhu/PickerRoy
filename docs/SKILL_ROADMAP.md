# 后续 Codex Skill 打包路线

核心分析器、命令行、图形界面、导出器、SQLite 数据库和评测器都不依赖 Codex。以后可以让 Skill 直接调用稳定的 `pickerroy-analyze` 和 `pickerroy-evaluate`，而不需要把产品逻辑塞进 Skill 指令。

打包顺序：

1. 使用私人真实视频验证选帧质量。
2. 根据 A/B 选择训练并版本化轻量偏好排序器。
3. 固定命令行接口和缓存结构。
4. 添加轻量 Codex Skill 包装。
5. 构建经过签名的 macOS 和 Windows 发布包。
