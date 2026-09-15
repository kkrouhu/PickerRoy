# Apple model smoke tests / 原生模型冒烟测试

在 macOS 上直接编译实际交付的 Swift 模型、引擎、数据结构、控制器、偏好存储和权限策略，在 MainActor 上测试同步操作保护。不创建 Xcode 测试工程，也不使用替代实现。

Compile the shipping Swift model, engine, data types, analysis control, preference store, and access policy directly on macOS. Tests exercise their synchronous operation guards on MainActor, without an Xcode test project or mocked implementation.

## 运行 / Run

需要可用的 Xcode Swift 编译器和 macOS SDK。在仓库根目录运行：

Requires the Xcode Swift compiler and macOS SDK. From the repository root:

```sh
bash scripts/apple-model-smoke/run.sh
```

成功时输出各组 `PASS` 和最终 `SUCCESS`；任何断言或编译失败都返回非零退出状态。每次测试的二进制与测试数据独立保留在 `work/apple-model-smoke/run.XXXXXX/`，模块缓存位于 `work/swift-module-cache/`。脚本不自动删除文件。

Each group prints `PASS`, followed by `SUCCESS`. Assertion or compilation failure returns a nonzero exit status. Each run retains its own binary and fixtures under `work/apple-model-smoke/run.XXXXXX/`; module caches remain in `work/swift-module-cache/`. No automatic cleanup occurs.

## 覆盖 / Coverage

- 注入专用偏好文件的读取与重置；isolated preference loading and reset.
- 单次导入及跨次导入重复 URL 去重，包括标准化后等价的路径；same-batch and cross-batch deduplication, including standardized equivalent paths.
- 分析中、导出中、两标志均为真时，不重启分析，不启动两种导出，不删除视频或候选，不重置现有进度、提示或错误；busy-state exclusion for analysis, both export modes, removal, and existing state.
- 拒绝的调用在让出 MainActor 后也不产生输出目录或延迟状态变化；rejected calls create neither output directories nor deferred state changes after yielding MainActor.
- 导出时锁定勾选；selection remains fixed while exporting.
- 空闲时选择和删除仍可用；idle selection and removal still work.
- 没有选图或视频时保持空闲；empty operations remain idle.
- 普通分析不会重新分析已完成视频；ordinary analysis does not restart completed videos.

## 安全边界与非覆盖项 / Safety and limits

所有模型均显式注入 `PreferenceStore(fileURL:)`，只使用新建的测试目录；不读取或改写实际用户偏好。所有源视频路径均为测试目录内不存在的文件，不访问真实媒体；不启动 GUI、不访问相册、不签名、不连接账户、也不生成付费操作。手动设置 `isAnalyzing` / `isExporting` 仅用于模拟已经有操作在运行。

Every model explicitly receives `PreferenceStore(fileURL:)` pointing inside its new test directory. Real preferences are neither read nor changed. Source URLs refer to nonexistent fixtures, never real media. No GUI, Photos access, signing, account connection, or payment occurs. Tests manually set the busy flags only to represent an operation already in progress.

本测试不证明真实解码、导出成功、iOS 相册权限路径、后台任务取消、旧操作进度回调过滤或 UI 行为正确；这些需要另外的引擎集成测试、异步操作注入测试和实机验证。对于不同操作 ID 的迟到回调，当前 private 回调没有测试入口，本脚本不会仅凭状态保护就宣称已覆盖。

This suite does not validate successful decoding/export, the iOS Photos authorization path, background-task cancellation, stale callbacks from a previous operation ID, or UI behavior. Those require engine integration tests, injectable asynchronous-operation tests, and device checks. Private progress callbacks are not exposed here; busy-state assertions must not be presented as coverage of stale-callback filtering.
