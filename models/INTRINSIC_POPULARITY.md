# 社交媒体视觉热度模型

`intrinsic_popularity_resnet50.onnx` 来自 Ding、Ma、Wang 在 ACM Multimedia 2019 提出的
Intrinsic Image Popularity Assessment（IIPA）ResNet-50 模型。原作者以 Instagram 中热度可区分的
图片对训练模型，使输出尽量反映图片本身的受欢迎程度，而不是发布账号规模等外部因素。

- 上游代码与权重：https://github.com/dingkeyan93/Intrinsic-Image-Popularity
- 论文：https://arxiv.org/abs/1907.01985
- 上游权重 SHA-256：`2b43c375ff8e75856aba1d4bbe713aa6b7f4d8fcce83c0f30e6558cb6d1d783f`
- 转换后 ONNX SHA-256：`691ce9c17040a932adf8fb9eaff52d7ce9865d891d5129c66aea33de23a8c304`
- PickerRoy 转换方式：`scripts/convert_intrinsic_popularity.py`，使用 `torch.load(..., weights_only=True)` 后导出 ONNX opset 17
- 输入：RGB、224×224、数值范围 0–1；与作者公开推理代码一致，不使用 ImageNet mean/std 标准化
- 用法：仅在已通过模糊、曝光、黑屏等技术检查的候选画面之间辅助排序

模型分数不是“必然获得多少点赞”的承诺。社交热度受账号、发布时间、文案、受众和平台机制影响；
PickerRoy 只使用画面本身可观察到的部分，并继续用本机偏好训练修正个人审美。
