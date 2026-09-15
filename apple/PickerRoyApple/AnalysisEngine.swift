import AVFoundation
import CoreImage
import CoreImage.CIFilterBuiltins
import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers
import Vision

struct AnalysisEngine {
    private let context = CIContext(options: [.cacheIntermediates: true])

    func analyze(
        video: VideoItem,
        aspect: OutputAspect,
        profile: PreferenceProfile,
        control: AnalysisControl,
        progress: @escaping @Sendable (Double) -> Void
    ) async throws -> [FrameCandidate] {
        let accessed = video.url.startAccessingSecurityScopedResource()
        defer { if accessed { video.url.stopAccessingSecurityScopedResource() } }

        let asset = AVURLAsset(url: video.url)
        let seconds = CMTimeGetSeconds(try await asset.load(.duration))
        guard seconds.isFinite, seconds > 0 else {
            throw NSError(domain: "PickerRoy", code: 1, userInfo: [NSLocalizedDescriptionKey: "无法读取视频时长"])
        }

        let generator = AVAssetImageGenerator(asset: asset)
        generator.appliesPreferredTrackTransform = true
        generator.requestedTimeToleranceBefore = CMTime(seconds: 0.12, preferredTimescale: 600)
        generator.requestedTimeToleranceAfter = CMTime(seconds: 0.12, preferredTimescale: 600)
        generator.maximumSize = CGSize(width: 1280, height: 1280)

        let sampleCount = min(140, max(18, Int(seconds / 1.2)))
        let step = seconds / Double(sampleCount + 1)
        var scored: [FrameCandidate] = []
        var firstFrameError: Error?
        scored.reserveCapacity(sampleCount)

        for index in 0..<sampleCount {
            try control.checkpoint()
            let second = min(seconds - 0.03, step * Double(index + 1))
            let requested = CMTime(seconds: second, preferredTimescale: 600)
            let frame: CGImage
            do {
                frame = try await generator.image(at: requested).image
            } catch {
                if firstFrameError == nil { firstFrameError = error }
                progress(Double(index + 1) / Double(sampleCount))
                continue
            }
            autoreleasepool {
                guard let cropped = crop(frame, to: aspect.ratio) else { return }

                let evaluation = evaluate(cropped)
                let base = aestheticScore(evaluation.features, category: evaluation.category)
                let final = (base + profile.adjustment(for: evaluation.features)).clamped(to: 0...1)
                guard let preview = thumbnailData(cropped) else { return }
                scored.append(FrameCandidate(
                    id: UUID(),
                    videoID: video.id,
                    sourceURL: video.url,
                    time: second,
                    category: evaluation.category,
                    baseScore: base,
                    personalizedScore: final,
                    features: evaluation.features,
                    thumbnailData: preview,
                    selected: false
                ))
            }
            progress(Double(index + 1) / Double(sampleCount))
        }

        try control.checkpoint()
        guard !scored.isEmpty else {
            let detail = firstFrameError?.localizedDescription ?? "视频中没有可读取的画面"
            throw NSError(
                domain: "PickerRoy",
                code: 4,
                userInfo: [NSLocalizedDescriptionKey: "无法从视频读取画面：\(detail)"]
            )
        }
        return diverseTopFrames(from: scored, duration: seconds)
    }

    func export(
        _ candidates: [FrameCandidate],
        to folder: URL,
        optimized: Bool,
        aspect: OutputAspect,
        control: AnalysisControl,
        progress: @escaping @Sendable (Double) -> Void
    ) async throws {
        let accessed = folder.startAccessingSecurityScopedResource()
        defer { if accessed { folder.stopAccessingSecurityScopedResource() } }
        try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)

        for (index, candidate) in candidates.enumerated() {
            try control.checkpoint()
            let sourceAccessed = candidate.sourceURL.startAccessingSecurityScopedResource()
            do {
                defer { if sourceAccessed { candidate.sourceURL.stopAccessingSecurityScopedResource() } }
                let asset = AVURLAsset(url: candidate.sourceURL)
                let generator = AVAssetImageGenerator(asset: asset)
                generator.appliesPreferredTrackTransform = true
                generator.requestedTimeToleranceBefore = .zero
                generator.requestedTimeToleranceAfter = .zero
                let time = CMTime(seconds: candidate.time, preferredTimescale: 600)
                let frame = try await generator.image(at: time).image
                guard let cropped = crop(frame, to: aspect.ratio) else {
                    throw NSError(
                        domain: "PickerRoy",
                        code: 5,
                        userInfo: [NSLocalizedDescriptionKey: "无法按所选比例生成图片"]
                    )
                }

                let finalImage = optimized ? optimize(cropped) : cropped
                let sourceName = candidate.sourceURL.deletingPathExtension().lastPathComponent
                    .replacingOccurrences(of: "/", with: "-")
                let suffix = String(format: "%06d", Int(candidate.time * 1000))
                let ext = optimized ? "jpg" : "png"
                let destination = folder.appendingPathComponent("\(sourceName)-\(suffix)-\(candidate.category.rawValue).\(ext)")
                try write(finalImage, to: destination, jpeg: optimized)
            }
            progress(Double(index + 1) / Double(max(1, candidates.count)))
        }
    }

    private func diverseTopFrames(from frames: [FrameCandidate], duration: Double) -> [FrameCandidate] {
        let desired = min(36, max(8, Int(duration / 12.0)))
        let minimumGap = max(0.7, min(3.0, duration / Double(max(10, desired * 2))))
        var chosen: [FrameCandidate] = []
        for frame in frames.sorted(by: { $0.personalizedScore > $1.personalizedScore }) {
            if chosen.allSatisfy({ abs($0.time - frame.time) >= minimumGap }) {
                chosen.append(frame)
                if chosen.count == desired { break }
            }
        }
        return chosen.sorted(by: { $0.time < $1.time })
    }

    private func evaluate(_ image: CGImage) -> (features: FrameFeatures, category: VisualCategory) {
        let side = 144
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        var bytes = [UInt8](repeating: 0, count: side * side * 4)
        bytes.withUnsafeMutableBytes { raw in
            guard let bitmap = CGContext(
                data: raw.baseAddress,
                width: side,
                height: side,
                bitsPerComponent: 8,
                bytesPerRow: side * 4,
                space: colorSpace,
                bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
            ) else { return }
            bitmap.interpolationQuality = .medium
            bitmap.draw(image, in: CGRect(x: 0, y: 0, width: side, height: side))
        }

        var luminances = [Double](repeating: 0, count: side * side)
        var saturationSum = 0.0
        var luminanceSum = 0.0
        for pixel in 0..<(side * side) {
            let offset = pixel * 4
            let r = Double(bytes[offset]) / 255.0
            let g = Double(bytes[offset + 1]) / 255.0
            let b = Double(bytes[offset + 2]) / 255.0
            let maximum = max(r, max(g, b))
            let minimum = min(r, min(g, b))
            let luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            luminances[pixel] = luminance
            luminanceSum += luminance
            saturationSum += maximum > 0 ? (maximum - minimum) / maximum : 0
        }

        let mean = luminanceSum / Double(side * side)
        let variance = luminances.reduce(0.0) { $0 + pow($1 - mean, 2) } / Double(side * side)
        let contrast = (sqrt(variance) / 0.28).clamped(to: 0...1)
        let exposure = (1.0 - abs(mean - 0.52) / 0.52).clamped(to: 0...1)
        let color = (saturationSum / Double(side * side) / 0.48).clamped(to: 0...1)

        var edgeSum = 0.0
        var edgeWeight = 0.0
        var centroidX = 0.0
        var centroidY = 0.0
        for y in 1..<(side - 1) {
            for x in 1..<(side - 1) {
                let center = y * side + x
                let gx = luminances[center + 1] - luminances[center - 1]
                let gy = luminances[center + side] - luminances[center - side]
                let edge = sqrt(gx * gx + gy * gy)
                edgeSum += edge
                edgeWeight += edge
                centroidX += Double(x) * edge
                centroidY += Double(y) * edge
            }
        }
        let sharpness = (edgeSum / Double((side - 2) * (side - 2)) / 0.16).clamped(to: 0...1)
        let cx = edgeWeight > 0 ? centroidX / edgeWeight / Double(side) : 0.5
        let cy = edgeWeight > 0 ? centroidY / edgeWeight / Double(side) : 0.5
        let thirds = [(1.0 / 3.0, 1.0 / 3.0), (2.0 / 3.0, 1.0 / 3.0), (1.0 / 3.0, 2.0 / 3.0), (2.0 / 3.0, 2.0 / 3.0)]
        let thirdDistance = thirds.map { hypot(cx - $0.0, cy - $0.1) }.min() ?? 0.5
        let composition = (1.0 - thirdDistance / 0.48).clamped(to: 0...1)

        let faceRequest = VNDetectFaceRectanglesRequest()
        try? VNImageRequestHandler(cgImage: image, options: [:]).perform([faceRequest])
        let faces = faceRequest.results ?? []
        let bestFace = faces.map { observation -> Double in
            let area = Double(observation.boundingBox.width * observation.boundingBox.height)
            let centerX = Double(observation.boundingBox.midX)
            let centerY = Double(observation.boundingBox.midY)
            let placement = (1.0 - min(1.0, hypot(centerX - 0.5, centerY - 0.54) / 0.56))
            return min(1.0, sqrt(area) * 2.2) * 0.62 + placement * 0.38
        }.max() ?? 0

        let scenic = (contrast * 0.24 + color * 0.25 + composition * 0.30 + sharpness * 0.21)
            .clamped(to: 0...1)
        let category: VisualCategory
        if bestFace > 0 { category = .person }
        else if scenic > 0.48 { category = .landscape }
        else { category = .detail }

        return (FrameFeatures(
            sharpness: sharpness,
            exposure: exposure,
            contrast: contrast,
            color: color,
            composition: composition,
            faceQuality: bestFace,
            scenicQuality: scenic
        ), category)
    }

    private func aestheticScore(_ features: FrameFeatures, category: VisualCategory) -> Double {
        let technical = features.sharpness * 0.24 + features.exposure * 0.19 + features.contrast * 0.13
        switch category {
        case .person:
            return (technical + features.faceQuality * 0.27 + features.composition * 0.11 + features.color * 0.06)
                .clamped(to: 0...1)
        case .landscape:
            return (technical + features.scenicQuality * 0.26 + features.composition * 0.11 + features.color * 0.07)
                .clamped(to: 0...1)
        case .detail:
            return (technical + features.composition * 0.18 + features.color * 0.13 + features.scenicQuality * 0.06)
                .clamped(to: 0...1)
        }
    }

    private func crop(_ image: CGImage, to ratio: CGFloat?) -> CGImage? {
        guard let ratio else { return image }
        let width = CGFloat(image.width)
        let height = CGFloat(image.height)
        let current = width / height
        let rect: CGRect
        if current > ratio {
            let targetWidth = height * ratio
            rect = CGRect(x: (width - targetWidth) / 2, y: 0, width: targetWidth, height: height)
        } else {
            let targetHeight = width / ratio
            rect = CGRect(x: 0, y: (height - targetHeight) / 2, width: width, height: targetHeight)
        }
        return image.cropping(to: rect.integral)
    }

    private func thumbnailData(_ image: CGImage) -> Data? {
        let source = CIImage(cgImage: image)
        let scale = min(1.0, 520.0 / max(source.extent.width, source.extent.height))
        let transformed = source.transformed(by: CGAffineTransform(scaleX: scale, y: scale))
        guard let output = context.createCGImage(transformed, from: transformed.extent) else { return nil }
        let data = NSMutableData()
        guard let destination = CGImageDestinationCreateWithData(data, UTType.jpeg.identifier as CFString, 1, nil) else { return nil }
        CGImageDestinationAddImage(destination, output, [kCGImageDestinationLossyCompressionQuality: 0.82] as CFDictionary)
        guard CGImageDestinationFinalize(destination) else { return nil }
        return data as Data
    }

    private func optimize(_ image: CGImage) -> CGImage {
        var current = CIImage(cgImage: image)
        let controls = CIFilter.colorControls()
        controls.inputImage = current
        controls.contrast = 1.035
        controls.saturation = 1.045
        controls.brightness = 0.006
        current = controls.outputImage ?? current

        let sharpen = CIFilter.sharpenLuminance()
        sharpen.inputImage = current
        sharpen.sharpness = 0.34
        current = sharpen.outputImage ?? current

        let area = current.extent.width * current.extent.height
        let scale = min(2.0, max(1.0, sqrt(12_000_000.0 / max(1, area))))
        if scale > 1.01 {
            let lanczos = CIFilter.lanczosScaleTransform()
            lanczos.inputImage = current
            lanczos.scale = Float(scale)
            lanczos.aspectRatio = 1
            current = lanczos.outputImage ?? current
        }
        return context.createCGImage(current, from: current.extent) ?? image
    }

    private func write(_ image: CGImage, to url: URL, jpeg: Bool) throws {
        let type = jpeg ? UTType.jpeg.identifier : UTType.png.identifier
        guard let destination = CGImageDestinationCreateWithURL(url as CFURL, type as CFString, 1, nil) else {
            throw NSError(domain: "PickerRoy", code: 2, userInfo: [NSLocalizedDescriptionKey: "无法建立导出文件"])
        }
        let options: CFDictionary = jpeg
            ? [kCGImageDestinationLossyCompressionQuality: 0.94] as CFDictionary
            : [:] as CFDictionary
        CGImageDestinationAddImage(destination, image, options)
        guard CGImageDestinationFinalize(destination) else {
            throw NSError(domain: "PickerRoy", code: 3, userInfo: [NSLocalizedDescriptionKey: "图片写入失败"])
        }
    }
}
