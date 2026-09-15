import Foundation
import SwiftUI
#if os(iOS)
import Photos
#endif

@MainActor
final class PickerRoyModel: ObservableObject {
    @Published var videos: [VideoItem] = []
    @Published var candidates: [FrameCandidate] = []
    @Published var aspect: OutputAspect = .original
    @Published var isAnalyzing = false
    @Published var isPaused = false
    @Published var isExporting = false
    @Published var progress = 0.0
    @Published var statusMessage = "请选择视频开始"
    @Published var errorMessage: String?
    @Published private(set) var profile: PreferenceProfile

    private let store = PreferenceStore()
    private let accessPolicy: FeatureAccessPolicy
    private var task: Task<Void, Never>?
    private var control: AnalysisControl?

    init(accessPolicy: FeatureAccessPolicy = .v1Free) {
        self.accessPolicy = accessPolicy
        profile = store.load()
        #if DEBUG
        if let demoPath = ProcessInfo.processInfo.environment["PICKERROY_DEMO_VIDEO"],
           FileManager.default.fileExists(atPath: demoPath) {
            videos = [VideoItem(url: URL(fileURLWithPath: demoPath))]
            statusMessage = "测试视频已导入，可开始分析"
        }
        #endif
    }

    var importedSummary: String {
        guard !videos.isEmpty else { return "尚未导入视频" }
        let done = videos.filter { $0.state == .completed }.count
        return "已成功导入 \(videos.count) 条 · 已完成 \(done) 条 · 待处理 \(videos.count - done) 条"
    }

    var selectedCandidates: [FrameCandidate] { candidates.filter(\.selected) }

    func canUse(_ feature: PickerRoyFeature) -> Bool {
        accessPolicy.allows(feature)
    }

    func addVideos(_ urls: [URL]) {
        let existing = Set(videos.map { $0.url.standardizedFileURL })
        let newURLs = urls.filter { !existing.contains($0.standardizedFileURL) }
        videos.append(contentsOf: newURLs.map { VideoItem(url: $0) })
        if newURLs.isEmpty {
            statusMessage = urls.isEmpty ? "没有选择视频" : "这些视频已经在列表中"
        } else if isAnalyzing {
            statusMessage = "已追加 \(newURLs.count) 条视频，本轮结束后可继续分析"
        } else {
            statusMessage = "导入成功：新增 \(newURLs.count) 条，共 \(videos.count) 条"
        }
    }

    func removeVideo(_ id: UUID) {
        guard !isAnalyzing else { return }
        videos.removeAll { $0.id == id }
        candidates.removeAll { $0.videoID == id }
        statusMessage = videos.isEmpty ? "请选择视频开始" : importedSummary
    }

    func startAnalysis() {
        guard canUse(.analysis) else { return }
        guard !isAnalyzing else { return }
        let batch = videos.filter { $0.state != .completed }
        guard !batch.isEmpty else {
            statusMessage = videos.isEmpty ? "请先导入视频" : "所有视频都已分析完成"
            return
        }

        let runControl = AnalysisControl()
        control = runControl
        isAnalyzing = true
        isPaused = false
        progress = 0
        errorMessage = nil
        let selectedAspect = aspect
        let currentProfile = profile

        task = Task { [weak self] in
            guard let self else { return }
            var finished = 0
            for item in batch {
                if Task.isCancelled { break }
                self.setState(.analyzing, for: item.id)
                self.statusMessage = "正在分析：\(item.name)"
                do {
                    let finishedCount = finished
                    let batchCount = batch.count
                    let progressHandler: @Sendable (Double) -> Void = { [weak self] value in
                        Task { @MainActor in
                            self?.progress = (Double(finishedCount) + value) / Double(batchCount)
                        }
                    }
                    let result = try await Task.detached(priority: .userInitiated) {
                        try await AnalysisEngine().analyze(
                            video: item,
                            aspect: selectedAspect,
                            profile: currentProfile,
                            control: runControl
                        ) { value in progressHandler(value) }
                    }.value

                    let autoSelectCount = min(8, max(1, result.count / 3))
                    let autoIDs = Set(result.sorted { $0.personalizedScore > $1.personalizedScore }
                        .prefix(autoSelectCount).map(\.id))
                    let prepared = result.map { frame -> FrameCandidate in
                        var value = frame
                        value.selected = autoIDs.contains(frame.id)
                        return value
                    }
                    self.candidates.removeAll { $0.videoID == item.id }
                    self.candidates.append(contentsOf: prepared)
                    self.setState(.completed, for: item.id, count: prepared.count)
                    self.profile.analyzedVideos += 1
                    self.store.save(self.profile)
                    finished += 1
                    self.progress = Double(finished) / Double(batch.count)
                } catch is CancellationError {
                    self.setState(.cancelled, for: item.id)
                    break
                } catch {
                    self.setState(.failed, for: item.id, error: error.localizedDescription)
                    self.errorMessage = "\(item.name)：\(error.localizedDescription)"
                    finished += 1
                }
            }
            self.isAnalyzing = false
            self.isPaused = false
            self.control = nil
            self.statusMessage = Task.isCancelled || finished < batch.count
                ? "分析已停止；已完成的结果已保留"
                : "分析完成：共生成 \(self.candidates.count) 张候选画面"
        }
    }

    func togglePause() {
        guard isAnalyzing, let control else { return }
        if isPaused {
            control.resume()
            isPaused = false
            statusMessage = "已继续分析"
        } else {
            control.pause()
            isPaused = true
            statusMessage = "分析已暂停，可以稍后继续或取消"
        }
    }

    func cancelAnalysis() {
        guard isAnalyzing else { return }
        control?.cancel()
        task?.cancel()
        statusMessage = "正在安全停止……"
    }

    func toggleSelection(_ id: UUID) {
        guard let index = candidates.firstIndex(where: { $0.id == id }) else { return }
        candidates[index].selected.toggle()
    }

    func learn(_ id: UUID, liked: Bool) {
        guard canUse(.personalization) else { return }
        guard let frame = candidates.first(where: { $0.id == id }) else { return }
        profile.learn(features: frame.features, liked: liked)
        store.save(profile)
        statusMessage = liked ? "已记住：你喜欢这张画面" : "已记住：减少推荐这类画面"
    }

    func resetPreferences() {
        profile = PreferenceProfile()
        store.reset()
        statusMessage = "本地审美偏好已清除"
    }

    func export(to folder: URL, optimized: Bool) {
        guard canUse(optimized ? .optimizedExport : .directExport) else { return }
        let selected = selectedCandidates
        guard !selected.isEmpty, !isExporting else {
            statusMessage = "请先选择要导出的图片"
            return
        }
        isExporting = true
        progress = 0
        statusMessage = optimized ? "正在优化并导出……" : "正在导出原始截图……"
        let exportControl = AnalysisControl()
        let selectedAspect = aspect
        task = Task { [weak self] in
            guard let self else { return }
            do {
                let progressHandler: @Sendable (Double) -> Void = { [weak self] value in
                    Task { @MainActor in self?.progress = value }
                }
                try await Task.detached(priority: .userInitiated) {
                    try await AnalysisEngine().export(
                        selected,
                        to: folder,
                        optimized: optimized,
                        aspect: selectedAspect,
                        control: exportControl
                    ) { value in progressHandler(value) }
                }.value
                self.statusMessage = "导出完成：\(selected.count) 张图片"
            } catch {
                self.errorMessage = error.localizedDescription
                self.statusMessage = "导出失败"
            }
            self.isExporting = false
        }
    }

    #if os(iOS)
    func exportToPhotoLibrary(optimized: Bool) {
        guard canUse(optimized ? .optimizedExport : .directExport) else { return }
        let selected = selectedCandidates
        guard !selected.isEmpty, !isExporting else {
            statusMessage = "请先选择要保存的图片"
            return
        }

        isExporting = true
        progress = 0
        statusMessage = optimized ? "正在优化并保存到相册……" : "正在保存到相册……"
        let exportControl = AnalysisControl()
        let selectedAspect = aspect
        task = Task { [weak self] in
            guard let self else { return }
            let temporaryFolder = FileManager.default.temporaryDirectory
                .appendingPathComponent("PickerRoy-Photo-Export-\(UUID().uuidString)", isDirectory: true)
            defer { try? FileManager.default.removeItem(at: temporaryFolder) }

            do {
                let progressHandler: @Sendable (Double) -> Void = { [weak self] value in
                    Task { @MainActor in self?.progress = value * 0.82 }
                }
                try await Task.detached(priority: .userInitiated) {
                    try await AnalysisEngine().export(
                        selected,
                        to: temporaryFolder,
                        optimized: optimized,
                        aspect: selectedAspect,
                        control: exportControl
                    ) { value in progressHandler(value) }
                }.value

                let authorization = await PHPhotoLibrary.requestAuthorization(for: .addOnly)
                guard authorization == .authorized || authorization == .limited else {
                    throw NSError(
                        domain: "PickerRoy",
                        code: 20,
                        userInfo: [NSLocalizedDescriptionKey: "需要允许 PickerRoy 添加照片，才能保存到系统相册"]
                    )
                }

                let imageURLs = try FileManager.default.contentsOfDirectory(
                    at: temporaryFolder,
                    includingPropertiesForKeys: nil,
                    options: [.skipsHiddenFiles]
                )
                try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
                    PHPhotoLibrary.shared().performChanges {
                        for url in imageURLs {
                            PHAssetChangeRequest.creationRequestForAssetFromImage(atFileURL: url)
                        }
                    } completionHandler: { success, error in
                        if success {
                            continuation.resume()
                        } else {
                            continuation.resume(throwing: error ?? NSError(
                                domain: "PickerRoy",
                                code: 21,
                                userInfo: [NSLocalizedDescriptionKey: "系统相册保存失败"]
                            ))
                        }
                    }
                }
                self.progress = 1
                self.statusMessage = "已保存到相册：\(imageURLs.count) 张图片"
            } catch {
                self.errorMessage = error.localizedDescription
                self.statusMessage = "保存失败"
            }
            self.isExporting = false
        }
    }
    #endif

    private func setState(_ state: VideoState, for id: UUID, count: Int = 0, error: String? = nil) {
        guard let index = videos.firstIndex(where: { $0.id == id }) else { return }
        videos[index].state = state
        videos[index].candidateCount = count
        videos[index].errorMessage = error
    }
}
