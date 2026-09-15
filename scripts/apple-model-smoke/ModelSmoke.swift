// Headless model guard checks compiled against the shipping Apple sources.
// Every PreferenceStore is explicitly injected with a disposable test path.
import Foundation

private struct SmokeFailure: Error, CustomStringConvertible {
    let description: String
}

private func expect(_ condition: @autoclosure () -> Bool, _ message: String) throws {
    guard condition() else { throw SmokeFailure(description: message) }
}

@MainActor
private struct ModelSnapshot: Equatable {
    let videos: [VideoItem]
    let candidates: [FrameCandidate]
    let analyzing: Bool
    let exporting: Bool
    let paused: Bool
    let progress: Double
    let status: String
    let error: String?

    init(_ model: PickerRoyModel) {
        videos = model.videos
        candidates = model.candidates
        analyzing = model.isAnalyzing
        exporting = model.isExporting
        paused = model.isPaused
        progress = model.progress
        status = model.statusMessage
        error = model.errorMessage
    }
}

@main
struct ModelSmoke {
    @MainActor
    static func main() async throws {
        guard CommandLine.arguments.count == 2 else {
            throw SmokeFailure(description: "Usage: apple-model-smoke <disposable test directory>")
        }
        let parent = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        let root = parent.appendingPathComponent("model-fixtures-\(UUID().uuidString)", isDirectory: true)
        try FileManager.default.createDirectory(at: root, withIntermediateDirectories: true)

        var passed = 0
        func pass(_ name: String) {
            passed += 1
            print("PASS: \(name)")
        }

        // Explicitly exercise the injected store; never instantiate the default
        // store, inspect Application Support, or use any existing user media.
        let isolatedPreference = root.appendingPathComponent("isolated-preferences.json")
        let isolatedStore = PreferenceStore(fileURL: isolatedPreference)
        var profile = PreferenceProfile()
        profile.decisions = 7
        isolatedStore.save(profile)
        let isolatedModel = PickerRoyModel(store: isolatedStore)
        try expect(isolatedModel.profile.decisions == 7, "Model must load the explicitly injected preference file")
        isolatedModel.resetPreferences()
        try expect(isolatedModel.profile.decisions == 0, "Reset must clear the injected model profile")
        try expect(!FileManager.default.fileExists(atPath: isolatedPreference.path), "Reset must remove only the injected test file")
        pass("isolated preference injection and reset")

        let dedup = makeModel(root: root)
        let first = root.appendingPathComponent("source-a.mov")
        let equivalent = root.appendingPathComponent("unused/../source-a.mov")
        let second = root.appendingPathComponent("source-b.mov")
        dedup.addVideos([first, first, equivalent])
        try expect(dedup.videos.count == 1, "One import batch must deduplicate exact and standardized equivalent URLs")
        let originalID = dedup.videos[0].id
        dedup.addVideos([first, second, second, equivalent])
        try expect(dedup.videos.count == 2, "Subsequent imports must deduplicate against both existing and newly imported URLs")
        try expect(dedup.videos[0].id == originalID, "Reimporting a URL must preserve its existing source identity")
        pass("same-batch and existing-source URL deduplication")

        for state in [
            (name: "analysis", analyzing: true, exporting: false),
            (name: "export", analyzing: false, exporting: true),
            (name: "both", analyzing: true, exporting: true),
        ] {
            let model = populatedModel(root: root)
            model.isAnalyzing = state.analyzing
            model.isExporting = state.exporting
            model.isPaused = state.analyzing
            model.progress = 0.37
            model.statusMessage = "Existing operation must remain intact"
            model.errorMessage = "Existing diagnostic must remain intact"
            let snapshot = ModelSnapshot(model)
            try expect(model.isBusy, "\(state.name): busy state must be derived from either operation flag")

            model.startAnalysis()
            try expect(ModelSnapshot(model) == snapshot, "\(state.name): busy startAnalysis must not reset or start any operation")

            for optimized in [false, true] {
                let output = root.appendingPathComponent("forbidden-\(state.name)-\(optimized)-\(UUID().uuidString)", isDirectory: true)
                model.export(to: output, optimized: optimized)
                try expect(ModelSnapshot(model) == snapshot, "\(state.name): busy export must not reset or start any operation")
                // Let accidentally scheduled MainActor work run before checking
                // again. No source video exists, so a regression still cannot
                // read private media; any output would stay in this test root.
                for _ in 0..<3 { await Task.yield() }
                try expect(ModelSnapshot(model) == snapshot, "\(state.name): a rejected operation must not schedule later model mutation")
                try expect(!FileManager.default.fileExists(atPath: output.path), "\(state.name): a rejected export must not create an output directory")
            }

            model.removeVideo(model.videos[0].id)
            try expect(ModelSnapshot(model) == snapshot, "\(state.name): busy removal must retain the source and its candidates")
            pass("\(state.name) busy guards: analysis, both export modes, removal, and deferred state")
        }

        let exporting = populatedModel(root: root)
        exporting.isExporting = true
        let exportSnapshot = ModelSnapshot(exporting)
        exporting.toggleSelection(exporting.candidates[0].id)
        exporting.toggleSelection(UUID())
        try expect(ModelSnapshot(exporting) == exportSnapshot, "Export in progress must preserve the selection snapshot")
        pass("selection cannot change during export")

        let idle = populatedModel(root: root)
        try expect(!idle.isBusy, "An idle model must not be busy")
        let candidateID = idle.candidates[0].id
        idle.toggleSelection(candidateID)
        try expect(idle.selectedCandidates.isEmpty, "Idle deselection must still work")
        idle.toggleSelection(candidateID)
        try expect(idle.selectedCandidates.count == 1, "Idle selection must still work")
        idle.removeVideo(idle.videos[0].id)
        try expect(idle.videos.isEmpty && idle.candidates.isEmpty, "Idle removal must still remove the source and its candidates")
        pass("idle selection and removal remain available")

        let empty = makeModel(root: root)
        let emptyOutput = root.appendingPathComponent("empty-export", isDirectory: true)
        empty.export(to: emptyOutput, optimized: false)
        try expect(!empty.isBusy && empty.statusMessage == "请先选择要导出的图片", "Empty export must stay idle and explain the missing selection")
        try expect(!FileManager.default.fileExists(atPath: emptyOutput.path), "Empty export must not create files or directories")
        empty.startAnalysis()
        try expect(!empty.isBusy && empty.statusMessage == "请先导入视频", "Empty analysis must stay idle and explain the missing video")
        pass("empty analysis and export stay idle")

        let completed = populatedModel(root: root)
        completed.videos[0].state = .completed
        completed.startAnalysis()
        try expect(!completed.isBusy && completed.statusMessage == "所有视频都已分析完成", "Completed videos must not silently restart through ordinary analysis")
        pass("ordinary analysis does not restart completed videos")

        print("SUCCESS: \(passed) Apple model smoke groups passed")
        print("Disposable fixtures: \(root.path)")
        print("Scope: macOS MainActor model guards only; no real media, GUI, signing, Photos access, or user preferences")
    }

    @MainActor
    private static func makeModel(root: URL) -> PickerRoyModel {
        PickerRoyModel(store: PreferenceStore(fileURL: root.appendingPathComponent("preferences-\(UUID().uuidString).json")))
    }

    @MainActor
    private static func populatedModel(root: URL) -> PickerRoyModel {
        let model = makeModel(root: root)
        let video = VideoItem(url: root.appendingPathComponent("nonexistent-source-\(UUID().uuidString).mov"))
        model.videos = [video]
        model.candidates = [FrameCandidate(
            id: UUID(), videoID: video.id, sourceURL: video.url, time: 0.5,
            category: .person, baseScore: 0.8, personalizedScore: 0.8,
            features: FrameFeatures(sharpness: 0.8, exposure: 0.8, contrast: 0.8,
                                    color: 0.8, composition: 0.8, faceQuality: 0.8, scenicQuality: 0.8),
            thumbnailData: Data(), selected: true
        )]
        return model
    }
}
