# 训练说明

## 当前真正启用的模型

### 1. 社交媒体热门视觉

PickerRoy 已集成 Intrinsic Image Popularity Assessment（IIPA）的 ResNet-50。该研究使用 Instagram 中热度可区分的图片对训练，目标是估计图片本身带来的受欢迎程度，尽量减少发布者影响。上游提供训练图片短码、推理代码和模型权重。

- [上游代码与权重](https://github.com/dingkeyan93/Intrinsic-Image-Popularity)
- [ACM Multimedia 2019 论文](https://arxiv.org/abs/1907.01985)

PickerRoy 使用安全的纯权重读取方式把模型转换为 ONNX。运行时只通过 OpenCV 在本机推理，不安装 PyTorch、不上传画面。原始输出只适合相对比较，因此界面显示的是当前视频内 0%–100% 的相对排名，而不是预计点赞数。

### 2. 用户自己的偏好训练

“偏好训练”中的每次 A/B 选择会保存胜出和落选画面的技术、构图、内容、时序与热门视觉特征。下次分析时，本机用正则化 Bradley-Terry 成对排序训练个人模型。

为了避免一两次误点破坏结果，个人权重会随样本数从约 6% 缓慢增加，最高限制为 16%。所有数据与参数均留在本机 SQLite 数据库中。

## 已研究、但尚未声称已用于训练的数据

- [TPIC 2017](https://github.com/social-media-prediction/TPIC2017)：68 万条 Flickr 社交帖子，提供按浏览量归一化的热度标签和匿名用户信息。官方旧下载端点当前网络不可达。
- [SMPD 2019](https://smp-challenge.com/2019/download.html)：超过 48 万条帖子，热度标签为 log-views，并包含图片地址和内容分类。当前官方分发需要接受数据许可。
- [FLICKR-AES](https://xiaohuishen.github.io/assets/iccv2017_personalizedaesthetics.pdf)：4 万张 Creative Commons 图片，每张由五名标注者给出 1–5 分审美评分。它更适合补充审美质量，不等同于社交热度。

在没有完成下载、许可核对、训练/验证拆分和独立评测前，PickerRoy 不会把这些数据写成“已经训练”。后续扩充应优先使用公开许可或用户明确授权的数据，并保留来源、许可和评测记录。

## 当前边界

- 热度不只由画面决定；账号影响力、发布时间、标题文案、受众和推荐机制都不在本地静帧模型的输入中。
- Instagram 训练分布不能代表所有平台、文化和题材，所以热门视觉只占综合分的一部分。
- 植物、动物、户外与人物已经分别分类和融合，但尚未拥有各自独立的大规模专用模型。
- 合成视频测试证明工程链路有效，不能替代真实用户视频的人工 Top-K 标注评测。
