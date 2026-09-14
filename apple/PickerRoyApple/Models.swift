import Foundation
import CoreGraphics

enum OutputAspect: String, CaseIterable, Identifiable, Codable {
    case original = "原视频尺寸"
    case square = "1:1"
    case portraitTwoThree = "2:3 竖版"
    case portraitThreeFour = "3:4 竖版"
    case landscapeSixteenNine = "16:9 横版"
    case portraitNineSixteen = "9:16 竖版"

    var id: String { rawValue }

    var ratio: CGFloat? {
        switch self {
        case .original: return nil
        case .square: return 1
        case .portraitTwoThree: return 2.0 / 3.0
        case .portraitThreeFour: return 3.0 / 4.0
        case .landscapeSixteenNine: return 16.0 / 9.0
        case .portraitNineSixteen: return 9.0 / 16.0
        }
    }
}

enum VideoState: String, Codable {
    case queued = "等待分析"
    case analyzing = "正在分析"
    case completed = "分析完成"
    case cancelled = "已取消"
    case failed = "失败"
}

struct VideoItem: Identifiable, Hashable {
    let id = UUID()
    let url: URL
    var state: VideoState = .queued
    var candidateCount = 0
    var errorMessage: String?

    var name: String { url.lastPathComponent }
}

enum VisualCategory: String, Codable, CaseIterable {
    case person = "人物"
    case landscape = "风景"
    case detail = "细节"
}

struct FrameFeatures: Codable, Hashable {
    var sharpness: Double
    var exposure: Double
    var contrast: Double
    var color: Double
    var composition: Double
    var faceQuality: Double
    var scenicQuality: Double

    var vector: [Double] {
        [sharpness, exposure, contrast, color, composition, faceQuality, scenicQuality]
    }
}

struct FrameCandidate: Identifiable, Hashable {
    let id: UUID
    let videoID: UUID
    let sourceURL: URL
    let time: Double
    let category: VisualCategory
    let baseScore: Double
    let personalizedScore: Double
    let features: FrameFeatures
    let thumbnailData: Data
    var selected: Bool

    var scoreText: String { String(format: "%.0f", personalizedScore * 100) }
    var timeText: String {
        let total = max(0, Int(time.rounded()))
        return String(format: "%02d:%02d", total / 60, total % 60)
    }
}

struct PreferenceProfile: Codable {
    var weights: [Double] = Array(repeating: 0, count: 7)
    var decisions = 0
    var analyzedVideos = 0

    mutating func learn(features: FrameFeatures, liked: Bool) {
        let direction = liked ? 1.0 : -1.0
        let learningRate = min(0.06, 0.24 / sqrt(Double(decisions + 4)))
        for (index, value) in features.vector.enumerated() {
            weights[index] = (weights[index] + direction * learningRate * (value - 0.5))
                .clamped(to: -0.45...0.45)
        }
        decisions += 1
    }

    func adjustment(for features: FrameFeatures) -> Double {
        let raw = zip(weights, features.vector).reduce(0.0) { partial, pair in
            partial + pair.0 * (pair.1 - 0.5)
        }
        let maturity = min(1.0, Double(decisions) / 40.0)
        return raw * 0.34 * maturity
    }
}

extension Comparable {
    func clamped(to range: ClosedRange<Self>) -> Self {
        min(max(self, range.lowerBound), range.upperBound)
    }
}
