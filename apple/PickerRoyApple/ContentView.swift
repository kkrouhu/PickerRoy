import SwiftUI
import UniformTypeIdentifiers

struct ContentView: View {
    @EnvironmentObject private var model: PickerRoyModel
    @State private var showingVideoImporter = false
    @State private var showingExportFolder = false
    @State private var optimizedExport = false
    @State private var selectedCategory: VisualCategory?
    @State private var confirmingPreferenceReset = false

    private var displayedCandidates: [FrameCandidate] {
        guard let selectedCategory else { return model.candidates }
        return model.candidates.filter { $0.category == selectedCategory }
    }

    var body: some View {
        NavigationSplitView {
            sidebar
                .navigationSplitViewColumnWidth(min: 260, ideal: 310, max: 380)
        } detail: {
            VStack(spacing: 0) {
                header
                statusBar
                if model.candidates.isEmpty {
                    emptyState
                } else {
                    candidateGrid
                }
                exportBar
            }
            .background(Color.platformBackground)
        }
        .fileImporter(
            isPresented: $showingVideoImporter,
            allowedContentTypes: [.movie, .video, .mpeg4Movie, .quickTimeMovie],
            allowsMultipleSelection: true
        ) { result in
            switch result {
            case .success(let urls): model.addVideos(urls)
            case .failure(let error): model.errorMessage = error.localizedDescription
            }
        }
        .fileImporter(
            isPresented: $showingExportFolder,
            allowedContentTypes: [.folder],
            allowsMultipleSelection: false
        ) { result in
            if case .success(let urls) = result, let folder = urls.first {
                model.export(to: folder, optimized: optimizedExport)
            }
        }
        .alert("PickerRoy", isPresented: Binding(
            get: { model.errorMessage != nil },
            set: { if !$0 { model.errorMessage = nil } }
        )) {
            Button("知道了", role: .cancel) { model.errorMessage = nil }
        } message: {
            Text(model.errorMessage ?? "发生未知错误")
        }
        .confirmationDialog("清除所有本地审美偏好？", isPresented: $confirmingPreferenceReset) {
            Button("清除偏好", role: .destructive) { model.resetPreferences() }
            Button("取消", role: .cancel) {}
        } message: {
            Text("已分析视频不会被删除，但个性化学习将从零开始。")
        }
    }

    private var sidebar: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack(spacing: 10) {
                LogoMark(size: 42)
                VStack(alignment: .leading, spacing: 1) {
                    Text("PickerRoy").font(.title2.bold())
                    Text("从视频发现好照片").font(.caption).foregroundStyle(.secondary)
                }
            }
            .padding(.top, 8)

            Button {
                chooseVideos()
            } label: {
                Label(model.isAnalyzing ? "继续添加视频" : "导入视频", systemImage: "plus.rectangle.on.rectangle")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)

            VStack(alignment: .leading, spacing: 6) {
                Text("画面比例").font(.headline)
                Picker("画面比例", selection: $model.aspect) {
                    ForEach(OutputAspect.allCases) { item in Text(item.rawValue).tag(item) }
                }
                .labelsHidden()
                .disabled(model.isAnalyzing)
                Text("分析前选择，预览和导出使用相同比例")
                    .font(.caption).foregroundStyle(.secondary)
            }

            Divider()
            Text(model.importedSummary).font(.subheadline.bold())

            ScrollView {
                LazyVStack(spacing: 8) {
                    ForEach(model.videos) { video in
                        VideoRow(video: video) { model.removeVideo(video.id) }
                    }
                }
            }

            personalizationCard

            HStack {
                Button("开始分析") { model.startAnalysis() }
                    .buttonStyle(.borderedProminent)
                    .disabled(model.isAnalyzing || model.videos.isEmpty)
                if model.isAnalyzing {
                    Button(model.isPaused ? "继续" : "暂停") { model.togglePause() }
                    Button("取消", role: .destructive) { model.cancelAnalysis() }
                }
            }
        }
        .padding()
    }

    private var personalizationCard: some View {
        VStack(alignment: .leading, spacing: 5) {
            HStack {
                Label("你的本地审美", systemImage: "sparkles")
                    .font(.subheadline.bold())
                Spacer()
                Button("重置") { confirmingPreferenceReset = true }
                    .buttonStyle(.plain).font(.caption).foregroundStyle(.secondary)
            }
            Text("已学习 \(model.profile.decisions) 次选择 · 分析 \(model.profile.analyzedVideos) 条视频")
                .font(.caption)
            ProgressView(value: min(1, Double(model.profile.decisions) / 40.0))
            Text("喜欢与不喜欢都只保存在这台设备上")
                .font(.caption2).foregroundStyle(.secondary)
        }
        .padding(11)
        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))
    }

    private var header: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("精选画面").font(.title2.bold())
                Text("点击图片选择；用喜欢/减少推荐训练你的 PickerRoy")
                    .font(.caption).foregroundStyle(.secondary)
            }
            Spacer()
            Picker("分类", selection: $selectedCategory) {
                Text("全部").tag(Optional<VisualCategory>.none)
                ForEach(VisualCategory.allCases, id: \.self) { value in
                    Text(value.rawValue).tag(Optional(value))
                }
            }
            .pickerStyle(.segmented)
            .frame(maxWidth: 360)
        }
        .padding()
        .background(.regularMaterial)
    }

    private var statusBar: some View {
        VStack(spacing: 4) {
            HStack {
                Image(systemName: model.isAnalyzing ? "viewfinder" : "checkmark.circle")
                Text(model.statusMessage).font(.subheadline)
                Spacer()
                if model.isAnalyzing || model.isExporting {
                    Text("\(Int(model.progress * 100))%")
                        .font(.caption.monospacedDigit())
                }
            }
            if model.isAnalyzing || model.isExporting {
                ProgressView(value: model.progress)
            }
        }
        .padding(.horizontal)
        .padding(.vertical, 9)
        .background(Color.accentColor.opacity(0.09))
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Spacer()
            LogoMark(size: 86)
            Text(model.videos.isEmpty ? "导入一条视频，开始发现好照片" : "准备就绪，选择比例后开始分析")
                .font(.title3.bold())
            Text("人物表情、风景构图、清晰度与色彩全部在本机分析，无需上传。")
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
            Button("选择视频") { chooseVideos() }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)
            Spacer()
        }
        .padding(28)
    }

    private var candidateGrid: some View {
        ScrollView {
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 210), spacing: 14)], spacing: 14) {
                ForEach(displayedCandidates) { frame in
                    CandidateCard(frame: frame,
                                  onSelect: { model.toggleSelection(frame.id) },
                                  onLike: { model.learn(frame.id, liked: true) },
                                  onReject: { model.learn(frame.id, liked: false) })
                }
            }
            .padding()
        }
    }

    private var exportBar: some View {
        HStack(spacing: 12) {
            Text("已选择 \(model.selectedCandidates.count) 张").font(.headline)
            Spacer()
            Button("直接导出") {
                optimizedExport = false
                chooseExportFolder()
            }
            .disabled(model.selectedCandidates.isEmpty || model.isExporting)
            Button("优化后导出") {
                optimizedExport = true
                chooseExportFolder()
            }
            .buttonStyle(.borderedProminent)
            .disabled(model.selectedCandidates.isEmpty || model.isExporting)
            .help("温和提升尺寸、色彩和锐度；不会凭空恢复原视频中不存在的真实细节")
        }
        .padding()
        .background(.regularMaterial)
    }

    private func chooseVideos() {
        #if os(macOS)
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.movie, .video, .mpeg4Movie, .quickTimeMovie]
        panel.allowsMultipleSelection = true
        panel.canChooseDirectories = false
        panel.begin { response in
            if response == .OK { model.addVideos(panel.urls) }
        }
        #else
        showingVideoImporter = true
        #endif
    }

    private func chooseExportFolder() {
        #if os(macOS)
        let panel = NSOpenPanel()
        panel.allowedContentTypes = [.folder]
        panel.allowsMultipleSelection = false
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.canCreateDirectories = true
        panel.prompt = "选择导出文件夹"
        panel.begin { response in
            if response == .OK, let folder = panel.url {
                model.export(to: folder, optimized: optimizedExport)
            }
        }
        #else
        showingExportFolder = true
        #endif
    }
}

private struct VideoRow: View {
    let video: VideoItem
    let remove: () -> Void

    var body: some View {
        HStack(spacing: 9) {
            Image(systemName: stateIcon).foregroundStyle(stateColor)
            VStack(alignment: .leading, spacing: 2) {
                Text(video.name).lineLimit(1).font(.caption.bold())
                Text(video.candidateCount > 0 ? "\(video.state.rawValue) · \(video.candidateCount) 张" : video.state.rawValue)
                    .font(.caption2).foregroundStyle(.secondary)
            }
            Spacer()
            if video.state != .analyzing {
                Button(action: remove) { Image(systemName: "xmark.circle.fill") }
                    .buttonStyle(.plain).foregroundStyle(.secondary)
            }
        }
        .padding(9)
        .background(Color.secondary.opacity(0.08), in: RoundedRectangle(cornerRadius: 10))
    }

    private var stateIcon: String {
        switch video.state {
        case .queued: return "clock"
        case .analyzing: return "viewfinder"
        case .completed: return "checkmark.circle.fill"
        case .cancelled: return "pause.circle.fill"
        case .failed: return "exclamationmark.triangle.fill"
        }
    }
    private var stateColor: Color {
        switch video.state {
        case .completed: return .green
        case .failed: return .red
        case .cancelled: return .orange
        default: return .accentColor
        }
    }
}

private struct CandidateCard: View {
    let frame: FrameCandidate
    let onSelect: () -> Void
    let onLike: () -> Void
    let onReject: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            ZStack(alignment: .topTrailing) {
                Thumbnail(data: frame.thumbnailData)
                    .frame(maxWidth: .infinity)
                    .aspectRatio(4 / 3, contentMode: .fill)
                    .clipped()
                    .contentShape(Rectangle())
                    .onTapGesture(perform: onSelect)
                Image(systemName: frame.selected ? "checkmark.circle.fill" : "circle")
                    .font(.title2).symbolRenderingMode(.palette)
                    .foregroundStyle(frame.selected ? Color.white : Color.white.opacity(0.8), Color.accentColor)
                    .shadow(radius: 2).padding(9)
            }
            HStack {
                Text(frame.category.rawValue).font(.caption.bold())
                Text(frame.timeText).font(.caption.monospacedDigit()).foregroundStyle(.secondary)
                Spacer()
                Label(frame.scoreText, systemImage: "sparkles").font(.caption.bold())
            }
            .padding(.horizontal, 10).padding(.top, 8)
            HStack {
                Button(action: onLike) { Label("喜欢", systemImage: "hand.thumbsup") }
                Spacer()
                Button(action: onReject) { Label("减少", systemImage: "hand.thumbsdown") }
            }
            .buttonStyle(.borderless).font(.caption).padding(10)
        }
        .background(Color.platformCard, in: RoundedRectangle(cornerRadius: 13))
        .overlay(RoundedRectangle(cornerRadius: 13).stroke(frame.selected ? Color.accentColor : .clear, lineWidth: 3))
        .clipShape(RoundedRectangle(cornerRadius: 13))
    }
}

private struct Thumbnail: View {
    let data: Data
    var body: some View {
        #if os(macOS)
        if let image = NSImage(data: data) { Image(nsImage: image).resizable() }
        else { Color.gray }
        #else
        if let image = UIImage(data: data) { Image(uiImage: image).resizable() }
        else { Color.gray }
        #endif
    }
}

private struct LogoMark: View {
    let size: CGFloat
    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: size * 0.22).fill(Color.white)
            RoundedRectangle(cornerRadius: size * 0.22).stroke(Color.black.opacity(0.14), lineWidth: 1)
            HStack(spacing: 0) {
                Text("R").font(.system(size: size * 0.35, weight: .black, design: .rounded))
                ZStack {
                    Circle().stroke(Color.black, lineWidth: max(2, size * 0.055))
                    ForEach(0..<6, id: \.self) { index in
                        Capsule().fill(Color.black)
                            .frame(width: size * 0.045, height: size * 0.19)
                            .offset(y: -size * 0.09)
                            .rotationEffect(.degrees(Double(index) * 60))
                    }
                    Circle().fill(Color.white).frame(width: size * 0.10)
                }.frame(width: size * 0.34, height: size * 0.34)
                Text("Y").font(.system(size: size * 0.35, weight: .black, design: .rounded))
            }.foregroundStyle(.black)
        }
        .frame(width: size, height: size)
    }
}

private extension Color {
    static var platformBackground: Color {
        #if os(macOS)
        Color(nsColor: .windowBackgroundColor)
        #else
        Color(uiColor: .systemGroupedBackground)
        #endif
    }
    static var platformCard: Color {
        #if os(macOS)
        Color(nsColor: .controlBackgroundColor)
        #else
        Color(uiColor: .secondarySystemGroupedBackground)
        #endif
    }
}
