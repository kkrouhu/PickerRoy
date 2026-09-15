# v0.3.5 验证记录 / Validation record

日期 / Date: 2026-09-15

## 桌面测试版 / Desktop test build

- 最终源码自动测试：87 passed。涵盖增强、偏好真实数据库到后续排序、旧样本压力、A/B 改选、CLEAR、候选时间/裁切标识、并发与同名导出、首次素材须知。
- 新增学习回归在旧版实现内存回放时失败，在新实现通过；测试没有切换生产文件或删改用户历史。
- Apple Silicon 独立 Mac App 构建成功，版本 0.3.5。内含视频引擎、分类支持及本地热门视觉模型，不依赖项目 Python 环境运行。
- 最终 ZIP 解压后，实际打开并核对设置页 0.3.5、运行环境就绪、内置引擎位置与新标志。首次须知未勾选、继续禁用、取消队列为空和设置内回看均已验证，没有代替真实用户同意。
- 构建目录与解压后的 App 均完成 3 秒合成视频分析：1 镜头、4 候选、4 推荐，直接 PNG 与增强 JPEG 成功；实际分类后端 apple-vision。合成数据只验证工程链路，不代表真实素材准确率。
- `codesign --verify --deep --strict` 通过，属于 ad-hoc 本机签名，不是 Developer ID 签名或公证。

本机 ZIP / Local ZIP: `PickerRoy-macOS-Apple-Silicon-v0.3.5.zip`

SHA-256: `3b6fa4529dc565c3ff8353335ec21b6884a8f10634baa068641cb8c7d7a5559a`

ICNS SHA-256: `761665cc536699cf0c2d36a832836d60fe2ca772c2472d23397491da959196ad`

In-app mark SHA-256: `2b95a8cbe39e27021015e66e17d2f2b7bb35224e6aa7d6c9a8c1a3b476381ea0`

CI 会重新构建各平台资产，因此对应 ZIP 哈希以各资产附带的 `.sha256` 为准，不能拿本机哈希去验证另一次构建。

## 真实图像 / Real-image evidence

桌面导出链路产生六组同帧、同裁切、3840 × 2880 的原画 PNG 与增强 PNG。全部实际查看，改善集中于可用阴影层次，天空高光保持克制；六组锐化均为零，不新增 0/255 通道剪切。包含保留轻微变化的例子，不将所有画面描述为同等改善。

本次设备单张直接导出约 0.60–0.72 秒、增强约 2.04–2.23 秒。该时间记录来自真实对比生成时的处理链路，不是跨设备性能承诺。

12 张源 PNG、来源哈希、同坐标局部图、8 页中英附录及 3 张宣传候选只保存在本地交付目录。公开使用授权待确认；公共仓库不包含这些私人抽帧或本机来源路径。商店使用前还需针对最终 Apple 原生输出核验。

## Apple 原生目标 / Native Apple targets

- macOS Release arm64 + x86_64：无签名 BUILD SUCCEEDED。
- iPhone Release arm64：无签名 BUILD SUCCEEDED。
- 15 类增强图像及小/大尺寸测试通过，包括亮天空与暗前景、带色阴影、防过锐与不放大。
- 5 组导出保真、9 组模型互斥/取消检查与首次须知纯状态测试通过。

## 尚未完成 / Not established

真实 iPhone 安装与系统相册授权、全部辅助功能/大字号交互、原生真实素材审美验收、HDR/广色域专项、大历史数据库性能、法律审查、Developer ID 公证和 App Store 提交均不能由上述工程测试代替。

In summary: 87 desktop tests, final local Mac launch and bundled exports, icon/signature checks, six real desktop image comparisons, and unsigned native builds/regressions passed. Private media remain local. These results do not establish aesthetic accuracy, pixel-equivalent native output, legal clearance, notarization, physical-device acceptance, or App Store approval.
