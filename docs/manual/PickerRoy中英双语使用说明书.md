# PickerRoy 中英双语使用说明书

版本 / Version 0.3.5 · macOS 与 Windows / macOS and Windows · 2026 年 9 月 / September 2026

文档状态：v0.3.5 本地 Mac 测试包与实图验证完成；新功能不在 v0.3.4 中。其他系统以对应发布资产为准，真机与商店验收未完成。/ Status: local v0.3.5 Mac package and real-image checks completed. These features are not in v0.3.4. Other systems depend on their published assets; physical-device and store acceptance are pending.

![PickerRoy Logo](素材/PickerRoy-logo.png)

从视频中精选好照片。/ Select great photos from video.

上架顺序：先 Mac App Store，再 iPhone；本包为 GitHub 桌面测试版。/ Planned store rollout: Mac App Store first, then iPhone. This package is a GitHub desktop test release.

v0.3.4 已修复新 macOS 上 Apple Vision 参数桥接异常导致的分类降级，自检记录分析后真正使用的后端。/ v0.3.4 fixed an Apple Vision options-bridging error on newer macOS; smoke tests record the backend actually used after analysis.

快速筛选清晰、自然、适合使用的画面，保存到本地。/ Quickly shortlist clear, natural, useful frames and save them locally.

本版重点是镂空 ROY 光圈标志与自适应“增强画质”，并讲清收藏与本机个性化的用途。增强不放大图片，也不对所有画面固定锐化。不宣称本版提升识别准确率或速度。/ This candidate focuses on an outlined ROY aperture identity and adaptive Enhance export, with clearer guidance on Favorite and local personalization. Enhance does not enlarge images or sharpen every frame. No increased recognition accuracy or speed is claimed.

桌面测试包采用兼容图标；Apple 原生版的 Liquid Glass 分层图标属于另一条构建路径。/ The desktop test package uses compatible icon assets; the native Apple target's layered Liquid Glass icon is a separate build path.

升级前先导出并退出旧版，再替换应用；保留旧安装包和本机数据以便回退。/ Finish exporting and quit the old app before replacing it. Keep the previous installer and local data for rollback.

这是未经过 Developer ID 公证的 GitHub 桌面测试包，不是 App Store 版本。不要关闭系统安全保护。/ This is a GitHub desktop test build without Developer ID notarization, not an App Store release. Do not disable system protections.

视频处理无需网络；下载安装包、系统更新和云盘原件可能需要联网。/ Video processing needs no network; app downloads, system updates, and cloud-stored originals may require internet access.

PickerRoy 是本地运行的视频静帧智能筛选工具。它结合技术质量、主题审美、离线热门视觉与每位用户的本机偏好，输出更少、更精、更不重复的候选照片。/ PickerRoy is a local-first intelligent still-frame selector. It combines technical quality, theme-aware aesthetics, an offline social-visual signal, and each user's local preferences to produce a smaller, sharper, less repetitive shortlist.

普通用户下载 App 后即可使用，不需要 Codex、Python、单独安装 FFmpeg、账号、订阅或持续联网。/ The standalone App needs no Codex, Python, separate FFmpeg installation, account, subscription, or ongoing internet connection.

Apple App Store V1.0 计划免费提供当前核心功能，不包含订阅、App 内购买或付费墙。观察期不会自动收费或锁定。iPhone 仅在保存结果时申请“添加照片”权限，不读取整个图库；真机飞行模式仍是上架前必测项。目前不开发 iPad、Apple Watch 或 Vision Pro。/ The planned Apple App Store V1.0 release provides current core features for free, without subscriptions, In-App Purchase, or paywalls. The observation period never triggers automatic charges or locking. iPhone requests add-only Photos access when saving results, without reading the full library. A physical-device airplane-mode run remains a pre-release test. iPad, Apple Watch, and Vision Pro are not current targets.

## 1. 产品理念 / Product idea

越选，越懂你的眼光。PickerRoy 在你的设备上学习你的选择，让视频选图逐渐贴近你的拍摄习惯与审美。/ A shortlist that learns your taste. PickerRoy learns from your decisions on your own device, gradually adapting video-frame recommendations to your shooting habits and visual taste.

收藏、保留、淘汰和 A/B 选择在形成有效比较后，会影响后续分析。这不是重新训练通用大模型，也不是导入或重复分析次数越多就自动更聪明。/ Favorite, Keep, Reject, and A/B decisions influence later analyses when usable comparisons can be formed. This is not retraining a general-purpose AI model; more imports or repeated analyses alone do not teach it your taste.

日常操作包括暂停、继续、取消、运行中追加队列、人像与风景主题审美、本机个性化，以及直接导出和增强画质。/ Everyday features include pause, resume, cancel, in-run queueing, portrait and landscape aesthetics, local personalization, Direct export, and Enhance.

## 2. 下载与安装 / Download and install

| 设备 / Device | 文件 / Asset |
|---|---|
| Apple 芯片 Mac / Apple Silicon Mac | `PickerRoy-macOS-Apple-Silicon.zip` |
| Intel Mac | `PickerRoy-macOS-Intel.zip` |
| Windows 10/11 x64 | `PickerRoy-Windows-x64.zip` |
| 可选 Codex 协助 / Optional Codex help | `PickerRoy-Codex-Skill-*.zip` |

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
7. 选择 PNG/JPEG 与“直接导出”或“增强画质”。/ Choose PNG/JPEG and Direct export or Enhance (“增强画质” in the Chinese interface).

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

### 收藏有什么意义？/ What is Favorite for?

| 操作 / Decision | 含义与作用 / Meaning and effect |
|---|---|
| 保留 / Keep | 这张可用，加入导出选择。/ I want to use this frame; add it to the export selection. |
| 收藏 / Favorite | 这张尤其符合我的审美；加入导出并记录比保留更强的偏好。/ Especially my kind of image; select it for export and record a stronger preference than Keep. |
| 淘汰 / Reject | 明确不要，不加入导出；不删除原视频或已导出的文件。/ Exclude it from export without deleting source videos or existing exports. |

收藏用来区分“可用”与“特别喜欢”。它保存的是本机标记，不是图片文件、云端同步或独立永久图库。要得到照片，仍须完成导出；备份偏好数据不能替代备份照片。/ Favorite separates “usable” from “especially liked.” It saves a local decision, not an image file, cloud sync, or a separate permanent photo library. You must still export to create a photo; backing up preferences is not a substitute for backing up photographs.

桌面版学习相对偏好：收藏高于保留，保留高于淘汰；同镜头中的部分未标记候选也可提供比较。只有形成有效学习对才参与后续分析。单独收藏但没有可比较候选，不保证增加学习对，也不会立即重排当前结果。/ The desktop app learns relative preferences: Favorite above Keep, and Keep above Reject; some unmarked same-shot candidates can also provide comparisons. Only usable pairs influence later analyses. An isolated Favorite without comparable candidates need not add a pair or instantly reorder current results.

### 如何教会它你的偏好 / Teach it your preferences

先用 5-10 条代表你真实工作的素材，完成真实选择或同镜头 A/B 比较。户外、人像、风光只是使用场景，不代表应用已经识别你的职业。/ Start with 5-10 videos representative of your real work and make honest decisions or same-shot A/B comparisons. Outdoor, portrait, and landscape are example uses, not claims that the app identifies your profession.

建议完成 4-5 轮“分析 - 选择 - 再分析”。桌面版从候选的已测量特征训练本机 Bradley–Terry 成对排序模型，不重训人脸检测器或通用大模型。仅重复运行而不选择，不会建立新的偏好。/ Try 4-5 analyze-choose-analyze cycles. The desktop version trains a local Bradley–Terry pairwise ranking model from measured candidate features, not a new face detector or general-purpose model. Re-running without choices does not build new preferences.

个人影响随有效样本增加而逐渐上升，上限约 34%。学习面板展示的是样本积累与选择记录，不是准确率；没有某个数量能保证“已经懂你”。新反馈从后续分析影响排序，是否更合适仍需你判断。/ Personal influence grows with usable examples, capped at about 34%. The learning panel describes examples and decisions, not accuracy; no count guarantees it has learned your taste. New feedback affects subsequent analyses, and you remain the judge of usefulness.

![个性化进度 / Personalization progress](素材/03-偏好训练.png)

v0.3.5 优先近期有效决定，并轮流参考不同视频及反馈类型，最多用 800 组训练；历史不删除，同一 A/B 以最近选择为准。新的时间与裁切标识防止换采样模式后串帧，旧标记不猜测迁移。/ v0.3.5 prioritizes recent usable decisions, alternating across videos and feedback types within an 800-pair training cap. History remains; the latest choice wins for the same A/B. Time- and crop-specific identities prevent changed sampling from attaching old labels to the wrong frame; old labels are not guessed onto new candidates.

## 8. 导出 / Export

只有当前类别筛选中可见、已保留或收藏的画面会导出；要导出全部类别的选择，先切回“全部”。/ Only visible Keep and Favorite frames export. Switch the category filter to All to export selections across every category.

### 直接导出 / Direct export

保留原有处理：从原视频重新解码，按所选比例裁切，不增加增强调整。适合归档、后续自己调色或保留原片风格。生成静帧仍需解码和图片编码，并非复制视频压缩数据。/ The existing path is unchanged: decode the source, apply the chosen crop, and add no Enhance adjustments. Use it for archiving, your own grading, or preserving the original look. A still is decoded and image-encoded, not copied bit-for-bit from compressed video data.

### 增强画质 / Enhance

![增强导出选项 / Enhance export option](素材/06-导出画面.png)

这是 PickerRoy 的重点特色功能：根据原片状态温和整理画面观感，不提高分辨率，不把每张图片都变得更锐利。界面只显示“增强画质”，解释放在说明书里。/ A key PickerRoy feature: restrained adjustments based on the source image, without raising resolution or making every frame sharper. The Chinese interface says only “增强画质”; the explanation belongs in the manual.

- 发灰、对比不足时，适度加强明暗层次，保留黑白两端余量。/ Gently increase contrast in flat images while leaving room at the darkest and lightest ends.
- 暗部有可用信号时，适度整理暗部表现，不伪造纯黑中的细节。/ Make restrained shadow adjustments where usable signal exists, without inventing detail in pure black.
- 色彩偏淡时，适量增加饱和度；对已鲜艳画面和温暖肤色保持克制。/ Add modest saturation to muted color, with restraint around vivid images and warm skin tones.
- 只对适合的画面做少量锐化；噪点明显、严重失焦或已锐利的画面不强行处理。/ Add a small amount of sharpening only where suitable, not to noisy, severely defocused, or already sharp images.

同一裁切下，两种模式保留相同像素宽高，不再插值放大。增强不能恢复缺失的毛发、皮肤、文字或失焦细节，不是生成式修复或超分辨率。/ With the same crop, both modes keep the same pixel dimensions, without interpolation enlargement. Enhance cannot restore absent hair, skin, text, or focus detail; it is neither generative repair nor super-resolution.

额外处理通常比直接导出更慢，随像素尺寸、数量和电脑性能变化。原片已经合适或可用信号有限时，变化可能很小；不保证每张图都更好看。/ Extra processing generally takes longer than Direct export, depending on dimensions, image count, and hardware. Suitable originals or limited usable signal may yield little change; not every image is guaranteed to look better.

### 怎样比较 / How to compare

用同一帧、同一裁切、同像素尺寸比较，先看整图层次与色彩，再以 100% 查看脸部、细线条和暗部。以自然为准，不以更亮、更艳、更锐为唯一标准。示例只代表所选画面。/ Compare the same frame, crop, and pixel dimensions. Assess overall tone and color, then faces, fine lines, and shadows at 100%. Judge naturalness rather than simply brightness, saturation, or sharpness. Examples represent only the selected frames.

增强基于现有导出链路，不是完整 HDR 重建或 HDR 转 SDR 流程。HDR、Log 或有意低对比的素材建议保留直接导出，在支持色彩管理的软件里检查。/ Enhance uses the existing export pipeline, not full HDR reconstruction or HDR-to-SDR grading. Retain Direct exports for HDR, Log, or intentionally flat grades and inspect them in a color-managed editor.

## 9. 配置、隐私与速度 / Hardware, privacy, and speed

请仅使用你有权处理的素材，并自行确认截图及发布所需授权。违法或侵权使用，由使用者依法承担相应责任。PickerRoy 不授予任何素材使用权，不排除法律规定不得免除的责任。/ Use only media you are entitled to process, and confirm any permissions required to extract or publish stills. Users bear responsibility for unlawful or infringing use as applicable under law. PickerRoy does not grant rights to any media or exclude liability that cannot legally be excluded.

首次导入前显示须知，默认不勾选；取消不导入，设置中可以重看。本机仅记录须知版本与确认时间，不向我们发送，也不验证素材版权。命令行与开发接口不显示图形确认窗口。/ At first import, the notice starts unchecked. Canceling does not import media; revisit it in Settings. Only the version and acknowledgment time are stored locally, not sent to us. This does not verify media ownership. Command-line and developer interfaces do not show the graphical acknowledgment.

![首次使用须知 / First-import notice](素材/05-素材与使用须知.png)

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
- 收藏后没有照片文件：收藏只是偏好标记，仍须选择导出文件夹并完成导出。/ No file after Favorite: Favorite is a preference decision; choose an export folder and finish the export to create a photo.
- 增强变化很小：原片已合适、噪点明显或信号不足时会克制处理；不会放大分辨率或修复严重失焦。/ Little change after Enhance: processing is restrained for suitable originals, noise, or limited signal; it does not raise resolution or repair severe defocus.
- HDR 色彩异常：0.3.0 会提示 HDR/BT.2020，但不执行完整 HDR 到 SDR 管线。/ Unexpected HDR color: 0.3.0 warns about HDR/BT.2020 but does not provide a full HDR-to-SDR pipeline.
- 推荐不合口味：确认模式与比例，再用真实反馈训练；稳定问题可让 Codex按 Skill 生成匿名偏好摘要并针对源码迭代。/ Poor recommendations: confirm mode and ratio, then train with honest feedback; for stable issues, ask Codex to create an anonymous profile and perform a targeted source iteration.

## 12. 能力边界 / Honest limitations

v0.3.5 已通过 87 项桌面测试、Apple 芯片 Mac 独立包分析及两种导出、实际启动、图标一致性、临时签名及素材须知检查。原生 Mac/iPhone 无签名构建与工程回归通过；真机与 App Store 验收未完成。/ v0.3.5 passed 87 desktop tests, standalone Apple Silicon analysis and both export modes, launch, icon consistency, ad-hoc signature and notice checks. Native Mac/iPhone unsigned builds and engineering regressions passed; physical-device and App Store acceptance remain pending.

六组真实户外同帧对比保持 3840 × 2880、同裁切、锐化为零。本机单张直接导出约 0.60–0.72 秒，增强约 2.04–2.23 秒，不代表所有素材或设备。完整图文附录只附本地说明书，待公开素材授权；不把桌面实图当作原生版逐像素一致的证据。同名导出会自动编号，不覆盖旧文件。/ Six real outdoor comparisons retain the same frame, crop, 3840 × 2880 dimensions, and zero sharpening. On this device, Direct took about 0.60–0.72 seconds and Enhance 2.04–2.23 seconds per image, not a universal benchmark. The illustrated appendix is local-only pending public-media permission; desktop evidence does not establish pixel-equivalent native output. Existing export files are preserved with numbered new filenames.

PickerRoy 是选片助手，不是审美裁判。社交热门不等于艺术价值，检测到笑容不等于最佳表情，构图规则也不能替代创作者意图。最终选择权始终属于用户。/ PickerRoy is an editing assistant, not an aesthetic judge. Social popularity is not artistic value, a detected smile is not always the best expression, and composition rules cannot replace creative intent. The user remains the final editor.

GitHub Release 的每个 ZIP 都有同名 `.sha256`。当前社区包未使用 Roy 自己的 Apple Developer ID 或商业 Windows 签名证书，因此首次启动可能出现安全确认。/ Every Release ZIP has a matching `.sha256`. Current community packages do not use Roy's own Apple Developer ID or commercial Windows signing certificate, so the operating system may request first-launch confirmation.

**先缩短海选，再用你的选择塑造下一轮推荐。/ Start with a focused shortlist, then shape future recommendations through your own choices.**
