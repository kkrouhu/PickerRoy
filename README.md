# PickerRoy

PickerRoy 是一款完全在本机运行的视频静帧智能筛选工具，面向摄影师和内容创作者。它不会简单地每隔几秒截图，而是先识别镜头，再从每个镜头的多个候选画面中挑选清晰、有代表性且彼此不同的瞬间。

![PickerRoy 中文结果界面](docs/GUI_PREVIEW.png)

## 直接使用

这台电脑已经安装完成。双击 **PickerRoy.app** 即可启动。

如果把整个项目移动到另一台 Mac，请先双击 **安装 PickerRoy.command**，安装完成后再打开应用。

## 使用流程

1. 在“导入”页面拖入一个视频、多个视频或包含视频的文件夹。
2. 看到绿色“导入成功”提示后，确认本次新增数量和等待分析总数。
3. 在开始分析前选择生成画面比例：原视频比例、1:1、3:2、2:3、4:3、3:4、16:9 或 9:16。智能裁切只作用于预览和导出，不会改变原视频。
4. 如有需要，在“设置”中选择综合、人像、动作、风景或产品模式。
5. 点击“开始分析”。界面会显示当前视频、镜头进度和候选画面数量。
6. 在“筛选结果”中按人物、动作、风景、动物、产品/装备或细节/特写筛选。
7. 把需要的画面标记为“保留”或“收藏”，不需要的标记为“淘汰”。
8. 点击“导出已选画面”，选择 PNG 或 JPEG。导出使用原视频分辨率，并按所选画幅裁切。
9. 在“偏好训练”中选择 A 或 B，帮助下一轮学习你的选帧偏好。

## 隐私与颜色

视频、缓存、导出图片和偏好数据都不会上传。缓存、数据库、日志、私有测试素材和导出图片均已排除在 Git 之外。

Rec.709 视频直接通过 FFmpeg 解码。检测到 HDR/BT.2020 时会记录警告；当前版本不会擅自给视频套调色。

## 开发与评测命令

```bash
.venv/bin/pytest
.venv/bin/pickerroy-analyze /视频路径/示例.mov --data-dir work/data
.venv/bin/pickerroy-evaluate evaluation/private/ground_truth.json
.venv/bin/python scripts/run_synthetic_benchmark.py
```

详细资料：[技术架构](docs/ARCHITECTURE.md)、[测试说明](docs/TESTING.md)、[人工标准答案格式](evaluation/README.md)、[首轮调试报告](docs/FIRST_ROUND_REPORT.md)。

## 仓库规则

当前没有替用户决定开源许可证。不要提交私人视频、私有 Ground Truth、缓存、导出图片、数据库、日志、Token、API Key 或个人路径。
