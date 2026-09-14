# PickerRoy

PickerRoy 是一款完全在本机运行的视频静帧智能筛选工具，面向摄影师和内容创作者。它不会简单地每隔几秒截图，而是先识别镜头，再结合技术质量、内容类型、社交媒体热门视觉模型和你的本机偏好，挑选清晰、有代表性且彼此不同的瞬间。

![PickerRoy 中文结果界面](docs/GUI_PREVIEW.png)

## 直接使用

普通用户从 GitHub Releases 下载与电脑匹配的 ZIP：Apple 芯片 Mac、Intel Mac 或 Windows x64。解压后直接打开 PickerRoy；独立应用已经包含 Python、视频引擎和热门视觉模型，不需要安装 Codex。

Codex Skill 是另外一个可选下载，只用于让 Codex 更了解 PickerRoy 的安装、使用、测试与排错方式。它不是桌面应用，单独下载 Skill 不能代替 PickerRoy。

首次启动和系统安全提示见[下载、安装与发布说明](docs/DISTRIBUTION.md)。

完整资料提供[中文 PDF](docs/manual/PickerRoy中文使用说明书.pdf)、[English PDF](docs/manual/PickerRoy-English-User-Manual.pdf)和[中英双语 PDF](docs/manual/PickerRoy中英双语使用说明书.pdf)，同时保留可在线阅读的 Markdown 版本。

## 使用流程

1. 在“导入”页面拖入一个视频、多个视频或包含视频的文件夹。
2. 看到绿色“导入成功”提示后，确认本次新增数量和等待分析总数。
3. 在开始分析前选择生成画面比例：原视频比例、1:1、3:2、2:3、4:3、3:4、16:9 或 9:16。智能裁切只作用于预览和导出，不会改变原视频。
4. 如有需要，在“设置”中选择综合、人像、动作、风景或产品模式。
5. 点击“开始分析”。界面会显示当前视频、镜头进度和候选画面数量；分析中可暂停、继续或取消，也可以把新视频加入下一轮。
6. 在“筛选结果”中按人物、动作、风景、动物、植物、产品/装备或细节/特写筛选。结果卡上的“热门视觉”是当前视频内部的相对热度排名。
7. 把需要的画面标记为“保留”或“收藏”，不需要的标记为“淘汰”。
8. 点击“导出已选画面”，选择 PNG/JPEG，并选择忠实的直接导出或像素补足、色彩/对比/锐度温和处理的优化后导出。
9. 保留、收藏、淘汰和“偏好训练”A/B 都会形成有效的本机学习对；从下一次分析开始逐步参与排序。

## 已启用的训练能力

- 社交媒体热门视觉：使用 IIPA 在 Instagram 热度图片对上训练的 ResNet-50 模型，本地 ONNX 推理，不联网。
- 个人偏好学习：收藏、保留、淘汰和同镜头 A/B 共同训练轻量级成对排序模型；样本少时影响较轻，最高受约 34% 安全上限约束。
- 主题审美：人物增加脸部/眼部可见度、表情、面部清晰度与曝光、主体位置；风景增加地平线、色彩协调、明暗范围、空间层次与自然色彩线索。
- 内容分层：人物、动作、风景、动物、植物、产品和细节使用不同融合权重；严重模糊、黑屏和过曝始终先被技术过滤。

## 一千个人，一千种本机偏好

PickerRoy 不需要用户会编程。先用 5–10 条代表自己题材的视频，完成几轮“分析—真实选择—再分析”，本机模型就会逐渐适应户外、城市、广告、室内、人物或产品等不同方向。重复运行而不做选择不会被误称为训练。普通个性化不需要 Codex；可选 Skill 用于让 Codex生成隐私摘要、做源码级定向优化、测试与重建。

模型来源、边界和后续数据计划见[训练说明](docs/TRAINING.md)。

## 隐私与颜色

视频、缓存、导出图片和偏好数据都不会上传。缓存、数据库、日志、私有测试素材和导出图片均已排除在 Git 之外。

Rec.709 视频直接通过 FFmpeg 解码。检测到 HDR/BT.2020 时会记录警告；当前版本不会擅自给视频套调色。

## 开发与评测命令

```bash
.venv/bin/pytest
.venv/bin/pickerroy-analyze /视频路径/示例.mov --data-dir work/data
.venv/bin/pickerroy-evaluate evaluation/private/ground_truth.json
.venv/bin/python scripts/run_synthetic_benchmark.py
.venv/bin/python scripts/run_preference_smoke.py /视频路径/示例.mov work/preference-smoke
```

详细资料：[技术架构](docs/ARCHITECTURE.md)、[测试说明](docs/TESTING.md)、[人工标准答案格式](evaluation/README.md)、[首轮调试报告](docs/FIRST_ROUND_REPORT.md)、[第三方许可说明](THIRD_PARTY_NOTICES.md)。

## 仓库规则

当前没有替用户决定开源许可证。不要提交私人视频、私有 Ground Truth、缓存、导出图片、数据库、日志、Token、API Key 或个人路径。
