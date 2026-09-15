# PickerRoy 中英双语使用说明书

版本 / Version 0.3.4 · macOS 与 Windows / macOS and Windows · 2026 年 9 月 / September 2026

![PickerRoy Logo](素材/PickerRoy-logo.png)

从视频中精选好照片。/ Select great photos from video.

上架顺序：先 Mac App Store，再 iPhone；本包为 GitHub 桌面测试版。/ Planned store rollout: Mac App Store first, then iPhone. This package is a GitHub desktop test release.

另修复新 macOS 上 Apple Vision 参数桥接异常导致的分类降级，自检记录分析后真正使用的后端。/ Also fixes an Apple Vision options-bridging error on newer macOS; smoke tests record the backend actually used after analysis.

快速筛选清晰、自然、适合使用的画面，保存到本地。/ Quickly shortlist clear, natural, useful frames and save them locally.

本版更新白底 ROY 光圈标志、桌面品牌区、产品主标题、版本信息及三份说明书；保留原有筛选算法与本机学习能力，不宣称提升准确率或速度。/ This release updates the white ROY aperture identity, desktop branding, headline, version metadata, and all three manuals. Selection algorithms and local learning are unchanged; no increased accuracy or speed is claimed.

升级前先导出并退出旧版，再替换应用；保留旧安装包和本机数据以便回退。/ Finish exporting and quit the old app before replacing it. Keep the previous installer and local data for rollback.

这是未经过 Developer ID 公证的 GitHub 桌面测试包，不是 App Store 版本。不要关闭系统安全保护。/ This is a GitHub desktop test build without Developer ID notarization, not an App Store release. Do not disable system protections.

视频处理无需网络；下载安装包、系统更新和云盘原件可能需要联网。/ Video processing needs no network; app downloads, system updates, and cloud-stored originals may require internet access.

PickerRoy 是本地运行的视频静帧智能筛选工具。它结合技术质量、主题审美、离线热门视觉与每位用户的本机偏好，输出更少、更精、更不重复的候选照片。/ PickerRoy is a local-first intelligent still-frame selector. It combines technical quality, theme-aware aesthetics, an offline social-visual signal, and each user's local preferences to produce a smaller, sharper, less repetitive shortlist.

普通用户下载 App 后即可使用，不需要 Codex、Python、单独安装 FFmpeg、账号、订阅或持续联网。/ The standalone App needs no Codex, Python, separate FFmpeg installation, account, subscription, or ongoing internet connection.

Apple App Store V1.0 计划免费提供当前核心功能，不包含订阅、App 内购买或付费墙。观察期不会自动收费或锁定。iPhone 仅在保存结果时申请“添加照片”权限，不读取整个图库；真机飞行模式仍是上架前必测项。目前不开发 iPad、Apple Watch 或 Vision Pro。/ The planned Apple App Store V1.0 release provides current core features for free, without subscriptions, In-App Purchase, or paywalls. The observation period never triggers automatic charges or locking. iPhone requests add-only Photos access when saving results, without reading the full library. A physical-device airplane-mode run remains a pre-release test. iPad, Apple Watch, and Vision Pro are not current targets.

## 1. 产品理念 / Product idea

PickerRoy 不把一种固定审美强加给所有人。收藏、保留、淘汰和 A/B 选择都会形成真正的本机学习信号，从下一次分析开始影响排序。/ PickerRoy does not impose one fixed taste. Favorite, Keep, Reject, and A/B choices become real local learning signals that affect later analyses.

户外、城市、广告、室内、产品或人物创作者会逐渐得到不同的结果。**一千个人，可以形成一千种本机 PickerRoy。** / Outdoor, urban, advertising, indoor, product, and portrait creators gradually receive different results. **A thousand users can form a thousand local PickerRoy preference models.**

0.3.0 新增暂停、继续、取消、运行中追加队列、人像与风景主题审美、个性化进度、直接导出和优化后导出。/ Version 0.3.0 adds pause, resume, cancel, in-run queueing, portrait and landscape aesthetics, personalization progress, direct export, and optimized export.

## 2. 下载与安装 / Download and install

| 设备 / Device | 文件 / Asset |
|---|---|
| Apple 芯片 Mac / Apple Silicon Mac | `PickerRoy-macOS-Apple-Silicon.zip` |
| Intel Mac | `PickerRoy-macOS-Intel.zip` |
| Windows 10/11 x64 | `PickerRoy-Windows-x64.zip` |
| 可选 Codex 协助 / Optional Codex help | `PickerRoy-Codex-Skill-v0.3.4.zip` |

macOS：解压，把 App 拖入“应用程序”。本包尚未公证；如无法验证开发者，先核验来源和校验和，确认可信后查看“系统设置 → 隐私与安全性”中本应用的“仍要打开”。如提示损坏或恶意软件，停止并反馈。不要关闭系统保护。/ macOS: unzip and move the app to Applications. This build is not notarized. If the developer cannot be verified, verify the source and checksum before reviewing the app-specific Open Anyway option in System Settings → Privacy & Security. Stop and report any damage or malware warning. Do not disable system protections.

Windows：完整解压并保留整个文件夹，双击 `PickerRoy.exe`。如 SmartScreen 提示，先确认 GitHub Release 来源和 SHA-256。/ Windows: extract completely, keep the entire folder together, and open `PickerRoy.exe`. If SmartScreen appears, verify the GitHub Release source and SHA-256 first.

App 是普通用户直接运行的产品；Skill 是给 Codex 的专业说明，不是 App。/ The App is the product ordinary users run; the Skill is professional guidance for Codex, not the App.

## 3. 第一次使用 / First use

1. 打开设置，确认绿色环境自检。/ Open Settings and confirm the green environment check.
2. 拖入一个、多个视频或文件夹。/ Drag in one video, several videos, or a folder.
3. 确认绿色导入成功提示和数量。/ Confirm the green success banner and counts.
4. 开始前选择比例和模式。/ Choose aspect ratio and mode before analysis.
5. 开始分析；长视频可暂停、继续或取消。/ Start analysis; pause, resume, or cancel long jobs.
6. 在结果中保留、收藏或淘汰。/ Mark results Keep, Favorite, or Reject.
7. 选择 PNG/JPEG 与直接/优化后导出。/ Export PNG/JPEG directly or optimized.

![导入、比例与分析控制 / Import, ratio, and controls](素材/01-导入成功与画幅.png)

## 4. 队列与分析控制 / Queue and controls

支持 MP4、MOV、M4V、MKV、AVI、WEBM、MTS、M2TS 与 MXF。导入不修改原视频。/ Supported formats include MP4, MOV, M4V, MKV, AVI, WEBM, MTS, M2TS, and MXF. Import never modifies the source.

- 暂停会挂起当前分析和解码，按钮变为继续。/ Pause suspends active analysis and decoding; the button becomes Resume.
- 取消会安全停止；已完整完成的视频结果保留，未完成视频仍在队列。/ Cancel stops safely; completed-video results remain and unfinished videos stay queued.
- 分析过程中添加的新视频进入下一轮。/ Videos added during a run enter the next batch.
- 安全停止可能有极短延迟。/ Reaching a safe stop boundary may take a brief moment.

## 5. 比例与模式 / Ratios and modes

原视频、1:1、3:2、2:3、4:3、3:4、16:9、9:16 都必须在分析前选择。裁切同时用于预览与全分辨率导出，原视频不改变。/ Original, 1:1, 3:2, 2:3, 4:3, 3:4, 16:9, and 9:16 are selected before analysis. The crop is consistent across preview and full-resolution export; the source never changes.

综合适合混合内容；人物强化脸部和人物状态；动作强化时序峰值与运动；风景强化地平线、颜色与空间层次；产品强化清晰度、构图和细节。/ Balanced suits mixed content; Portrait emphasizes faces and human moments; Action emphasizes temporal peaks and motion; Landscape emphasizes horizon, color, and depth; Product emphasizes focus, composition, and detail.

重要商业画面仍应检查边缘人物、文字和产品是否被裁切。/ Important commercial frames should still be checked for cropped people, text, and products.

## 6. 排序逻辑 / Ranking logic

系统先排除黑场、空白转场、严重过曝、失焦和解码错误，再进行主题审美评分。/ The system first rejects black frames, blank transitions, severe overexposure, defocus, and decode errors, then applies theme-aware aesthetics.

人像指标包括脸与眼部可见度、表情、面部清晰度与曝光、主体位置。风景指标包括地平线三分构图、色彩协调、饱和度、明暗范围、空间层次与自然色彩。/ Portrait cues include face and eye visibility, expression, facial focus and exposure, and subject placement. Landscape cues include horizon thirds, color harmony, saturation, tonal range, depth layers, and natural-color cues.

内置 IIPA 模型本机估计 Instagram 风格的热门视觉潜力。百分比只是当前视频内部相对排名，不是点赞保证。/ The bundled IIPA model locally estimates Instagram-style visual popularity. Its percentage is only a relative rank within the current video, not a promised like count.

![推荐结果 / Ranked results](素材/02-推荐结果.png)

## 7. 个性化训练 / Personalization

先用 5-10 条代表你真实工作的素材。每轮都做真实选择：收藏代表最爱，保留代表可交付，淘汰代表明确不要，A/B 代表同镜头二选一。/ Start with 5-10 videos representative of your real work. Make honest choices each round: Favorite for your strongest taste, Keep for deliverable frames, Reject for deliberate exclusions, and A/B for a direct same-shot comparison.

建议完成 4-5 轮“分析 - 选择 - 再分析”。只是重复运行却不选择，不会训练。样本增加后个人权重逐渐上升，但限制在约 34% 的安全上限。/ Complete 4-5 analyze-choose-analyze cycles. Re-running without choices is not training. Personal influence rises gradually with samples but remains capped at about 34%.

![个性化进度 / Personalization progress](素材/03-偏好训练.png)

## 8. 导出 / Export

只有保留和收藏的画面会导出。直接导出从原视频重新解码并按比例裁切，不增加创意调色。/ Only Keep and Favorite frames export. Direct export decodes the source again and applies the crop without a creative grade.

优化后导出适合横转竖等裁切损失。它用高质量插值尽量补回原帧像素面积，单边最高 2 倍、总计最高 2400 万像素，再温和优化局部对比、饱和度和锐度。/ Optimized export is useful after crop loss such as landscape-to-portrait. It recovers pixel area toward the source with high-quality interpolation, capped at 2x per side and 24 MP, then gently adjusts local contrast, saturation, and sharpness.

它不是生成式超分辨率，不能创造原视频不存在的真实细节。/ It is not generative super-resolution and cannot invent true detail absent from the video.

## 9. 配置、隐私与速度 / Hardware, privacy, and speed

主要消耗 CPU、内存和硬盘，不强制独立显卡，不依赖网速。最低建议 8 GB 内存；长 4K/H.265 素材建议 16 GB 以上并预留缓存空间。/ PickerRoy mainly uses CPU, memory, and storage. It requires neither a discrete GPU nor network speed. Use at least 8 GB RAM; long 4K/H.265 work benefits from 16 GB or more and adequate cache space.

视频、预览、偏好、日志和导出默认不上传。设置页显示本机数据目录；换电脑前备份它即可保留偏好。/ Videos, previews, preferences, logs, and exports are not uploaded by default. Settings shows the local data directory; back it up to preserve preferences when moving computers.

## 10. App、Skill、Agent 与 vibe coding

- App 是普通用户直接运行的 PickerRoy 本体。/ The App is the PickerRoy product ordinary users open.
- Skill 是给 Codex 的专业说明，不是 App。/ The Skill is professional guidance for Codex, not the App.
- Agent 是能理解上下文、使用工具、完成多步目标的 AI 工作者。/ An Agent is an AI worker that understands context, uses tools, and completes multi-step goals.
- Vibe coding 是用自然语言描述目标，由 AI Agent 实现、测试和迭代代码。/ Vibe coding describes product goals in natural language while an AI agent implements, tests, and iterates.

内置个性化不需要 Codex。只有深入分析偏好、修改源码、重建或重新发布时才需要 Skill、Codex 与源码。Skill 的隐私摘要不包含路径、图片、视频、候选 ID 或时间点。/ Built-in personalization needs no Codex. The Skill, Codex, and source are needed only for deeper preference analysis, source changes, rebuilding, or republishing. Its privacy summary contains no paths, images, videos, candidate IDs, or timestamps.

## 11. 常见问题 / Troubleshooting

- 分析按钮不可用：检查导入是否成功和设置页环境自检。/ Disabled analysis: check successful import and the Settings environment check.
- 分析很慢：4K、H.265、高帧率和大量镜头更耗 CPU；可暂停、取消或先测试短片。/ Slow analysis: 4K, H.265, high frame rates, and many cuts use more CPU; pause, cancel, or test a short clip first.
- 没有导出：至少标记一张保留或收藏，并检查类别筛选。/ No export: mark at least one Keep or Favorite and check the category filter.
- HDR 色彩异常：0.3.0 会提示 HDR/BT.2020，但不执行完整 HDR 到 SDR 管线。/ Unexpected HDR color: 0.3.0 warns about HDR/BT.2020 but does not provide a full HDR-to-SDR pipeline.
- 推荐不合口味：确认模式与比例，再用真实反馈训练；稳定问题可让 Codex按 Skill 生成匿名偏好摘要并针对源码迭代。/ Poor recommendations: confirm mode and ratio, then train with honest feedback; for stable issues, ask Codex to create an anonymous profile and perform a targeted source iteration.

## 12. 能力边界 / Honest limitations

PickerRoy 是选片助手，不是审美裁判。社交热门不等于艺术价值，检测到笑容不等于最佳表情，构图规则也不能替代创作者意图。最终选择权始终属于用户。/ PickerRoy is an editing assistant, not an aesthetic judge. Social popularity is not artistic value, a detected smile is not always the best expression, and composition rules cannot replace creative intent. The user remains the final editor.

GitHub Release 的每个 ZIP 都有同名 `.sha256`。当前社区包未使用 Roy 自己的 Apple Developer ID 或商业 Windows 签名证书，因此首次启动可能出现安全确认。/ Every Release ZIP has a matching `.sha256`. Current community packages do not use Roy's own Apple Developer ID or commercial Windows signing certificate, so the operating system may request first-launch confirmation.

**先帮你少看一点废片，再让每一次真实选择，悄悄把工具变得更像你。/ Show you fewer unusable frames, then let every real decision quietly make the tool more like you.**
