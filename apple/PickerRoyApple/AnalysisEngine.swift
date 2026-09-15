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
            let captureTime: CMTime
            do {
                let generated = try await generator.image(at: requested)
                guard generated.actualTime.isNumeric else {
                    throw NSError(domain: "PickerRoy", code: 6, userInfo: [NSLocalizedDescriptionKey: "无法读取画面的准确时间"])
                }
                frame = generated.image
                captureTime = generated.actualTime
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
                    time: CMTimeGetSeconds(captureTime),
                    category: evaluation.category,
                    baseScore: base,
                    personalizedScore: final,
                    features: evaluation.features,
                    thumbnailData: preview,
                    selected: false,
                    captureTime: captureTime,
                    outputAspect: aspect
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

    // Keep the external aspect label for existing callers; the analyzed crop is
    // authoritative so changing the controls cannot change already chosen images.
    func export(
        _ candidates: [FrameCandidate],
        to folder: URL,
        optimized: Bool,
        aspect _: OutputAspect,
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
                let generated = try await generator.image(at: candidate.captureTime)
                guard generated.actualTime.isNumeric,
                      CMTimeCompare(generated.actualTime, candidate.captureTime) == 0 else {
                    throw NSError(
                        domain: "PickerRoy",
                        code: 6,
                        userInfo: [NSLocalizedDescriptionKey: "无法准确还原已选画面，请重新分析源视频后再导出"]
                    )
                }
                guard let cropped = crop(generated.image, to: candidate.outputAspect.ratio) else {
                    throw NSError(
                        domain: "PickerRoy",
                        code: 5,
                        userInfo: [NSLocalizedDescriptionKey: "无法按所选比例生成图片"]
                    )
                }

                let finalImage = optimized ? optimize(cropped) : cropped
                let sourceName = exportSourceName(candidate.sourceURL)
                let sourceID = candidate.videoID.uuidString.prefix(12).lowercased()
                let suffix = String(format: "%06d", Int(candidate.time * 1000))
                let ext = optimized ? "jpg" : "png"
                let destination = folder.appendingPathComponent("\(sourceName)-\(sourceID)-\(suffix)-\(candidate.category.rawValue).\(ext)")
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

    // Enhancement is a restrained photographic adjustment, not super-resolution.
    // Internal visibility lets generated-fixture tests exercise the shipping path.
    struct EnhancementRecipe {
        let contrast: Double
        let pivot: Double
        let shadows: Double
        let vibrance: Double
        let sharpness: Double
        let noise: Double
        let gradient: Double

        var isIdentity: Bool {
            contrast == 0 && shadows == 0 && vibrance == 0 && sharpness == 0
        }
    }

    func enhancementRecipe(for image: CGImage) -> EnhancementRecipe {
        let preview = enhancementPixels(image, maximumSide: 256)
        guard !preview.luminances.isEmpty else {
            return EnhancementRecipe(contrast: 0, pivot: 0.5, shadows: 0, vibrance: 0, sharpness: 0, noise: 0, gradient: 0)
        }
        let ordered = preview.luminances.sorted()
        func percentile(_ fraction: Double) -> Double { ordered[Int(Double(ordered.count - 1) * fraction)] }
        let low = percentile(0.05), high = percentile(0.95), median = percentile(0.5)
        let span = high - low
        let count = Double(ordered.count)
        let shadowPixels = ordered.filter { $0 > 0.025 && $0 < 0.28 }
        let shadowFraction = Double(shadowPixels.count) / count
        let shadowMedian = shadowPixels.isEmpty ? 0.28 : shadowPixels[(shadowPixels.count - 1) / 2]
        let meanLuminance = ordered.reduce(0, +) / count
        let clippedFraction = Double(ordered.filter { $0 < 0.015 || $0 > 0.985 }.count) / count
        let meanSaturation = preview.saturations.reduce(0, +) / count

        // Native-resolution patches keep high-frequency noise from disappearing
        // in the downscaled overview. This is a conservative noise proxy, not a
        // blur/noise classifier; an ambiguous patch should disable sharpening.
        let patchSide = min(192, min(image.width, image.height))
        var gradients: [Double] = [], residuals: [Double] = []
        for position in [0.25, 0.5, 0.75] {
            let x = Int(Double(image.width - patchSide) * position)
            let y = Int(Double(image.height - patchSide) * position)
            guard patchSide >= 3,
                  let patch = image.cropping(to: CGRect(x: x, y: y, width: patchSide, height: patchSide)) else { continue }
            let pixels = enhancementPixels(patch, maximumSide: patchSide)
            guard pixels.luminances.count == patchSide * patchSide else { continue }
            for row in 1..<(patchSide - 1) {
                for column in 1..<(patchSide - 1) {
                    let p = row * patchSide + column
                    let neighbors = pixels.luminances[p - 1] + pixels.luminances[p + 1]
                        + pixels.luminances[p - patchSide] + pixels.luminances[p + patchSide]
                    let gradient = (abs(pixels.luminances[p + 1] - pixels.luminances[p - 1])
                        + abs(pixels.luminances[p + patchSide] - pixels.luminances[p - patchSide])) / 4
                    gradients.append(gradient)
                    residuals.append(abs(pixels.luminances[p] - neighbors / 4))
                }
            }
        }
        let gradient = gradients.isEmpty ? 0 : gradients.reduce(0, +) / Double(gradients.count)
        // A mean catches distributed noise; the upper quartile avoids judging a
        // mostly flat frame from a single sharp object edge alone.
        residuals.sort()
        let noise = residuals.isEmpty ? 0 : max(
            residuals.reduce(0, +) / Double(residuals.count),
            residuals[Int(Double(residuals.count - 1) * 0.75)] * 0.65
        )
        let noiseSafety = ((0.018 - noise) / 0.015).clamped(to: 0...1)
        let usefulRange = span > 0.025 && high > 0.06 && low < 0.94
        let contrastNeed = ((0.70 - span) / 0.55).clamped(to: 0...1)
        let contrast = usefulRange ? 0.22 * contrastNeed * (0.55 + 0.45 * noiseSafety)
            * (1 - min(0.7, clippedFraction)) : 0
        // Judge usable shadows independently of a bright sky. A global median
        // exposure gate can otherwise disable exactly the foreground detail the
        // user wants to see. Nearly black/noisy frames still get no strong lift.
        let shadowNeed = ((0.28 - shadowMedian) / 0.15).clamped(to: 0...1)
        let shadowEvidence = (shadowFraction / 0.24).clamped(to: 0...1)
        let usableExposure = ((meanLuminance - 0.035) / 0.11).clamped(to: 0...1)
        let shadows = usefulRange ? 0.065 * shadowNeed * shadowEvidence * usableExposure * noiseSafety : 0
        let vibrance = usefulRange ? 0.18 * ((0.48 - meanSaturation) / 0.40).clamped(to: 0...1)
            * (0.6 + 0.4 * noiseSafety) : 0
        let structure = ((gradient - 0.004) / 0.009).clamped(to: 0...1)
        let softness = ((0.050 - gradient) / 0.030).clamped(to: 0...1)
        let sharpness = usefulRange && noise < 0.012 && gradient > 0.004 && gradient < 0.05
            ? 0.045 * structure * softness * noiseSafety : 0
        return EnhancementRecipe(
            contrast: contrast, pivot: median.clamped(to: 0.36...0.55), shadows: shadows,
            vibrance: vibrance, sharpness: sharpness, noise: noise, gradient: gradient
        )
    }

    func optimize(_ image: CGImage) -> CGImage {
        let recipe = enhancementRecipe(for: image)
        guard !recipe.isIdentity else { return image }
        let source = CIImage(cgImage: image)
        var current = source
        if recipe.sharpness > 0 {
            let sharpen = CIFilter.sharpenLuminance()
            sharpen.inputImage = current.clampedToExtent()
            sharpen.sharpness = Float(recipe.sharpness)
            current = (sharpen.outputImage ?? current).cropped(to: source.extent)
        }

        // A small 3D lookup table performs hue-preserving tonal/color changes.
        // Both statistics and this context use display-referred sRGB; without an
        // explicit working color space the same formula would run in linear light.
        let dimension = 33
        var cube = [Float]()
        cube.reserveCapacity(dimension * dimension * dimension * 4)
        for blue in 0..<dimension {
            for green in 0..<dimension {
                for red in 0..<dimension {
                    let rgb = enhancedColor(
                        red: Double(red) / Double(dimension - 1),
                        green: Double(green) / Double(dimension - 1),
                        blue: Double(blue) / Double(dimension - 1), recipe: recipe
                    )
                    cube.append(contentsOf: [Float(rgb.0), Float(rgb.1), Float(rgb.2), 1])
                }
            }
        }
        let lookup = CIFilter.colorCube()
        lookup.inputImage = current
        lookup.cubeDimension = Float(dimension)
        lookup.cubeData = cube.withUnsafeBytes { Data($0) }
        current = lookup.outputImage ?? current
        let sRGB = CGColorSpace(name: CGColorSpace.sRGB)!
        let enhancementContext = CIContext(options: [
            .workingColorSpace: sRGB, .outputColorSpace: sRGB, .cacheIntermediates: false
        ])
        // No resampling or upscaling: selected frame and crop dimensions remain
        // exactly the same. The original-quality branch never calls this method.
        return enhancementContext.createCGImage(
            current.cropped(to: source.extent), from: source.extent, format: .RGBA8, colorSpace: sRGB
        ) ?? image
    }

    private func enhancedColor(red r: Double, green g: Double, blue b: Double, recipe: EnhancementRecipe) -> (Double, Double, Double) {
        let luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        let maximum = max(r, max(g, b)), minimum = min(r, min(g, b))
        let saturation = maximum > 0 ? (maximum - minimum) / maximum : 0
        var contrastDelta = recipe.contrast * (luminance - recipe.pivot) * 4 * luminance * (1 - luminance)
        let shadowPosition = (luminance / 0.60).clamped(to: 0...1)
        let shadowBell = 6.75 * shadowPosition * pow(1 - shadowPosition, 2)
        // Avoid cancelling the requested shadow lift with the darker half of
        // the contrast curve; protect near-black and highlight endpoints.
        contrastDelta *= 1 - 0.75 * (recipe.shadows / 0.065) * shadowBell
        let endpointGuard = min(
            ((luminance - 0.012) / 0.055).clamped(to: 0...1),
            ((1 - luminance) / 0.10).clamped(to: 0...1)
        )
        let targetLuminance = (luminance + (contrastDelta + recipe.shadows * shadowBell) * endpointGuard).clamped(to: 0...1)
        // Scale RGB together for the tonal adjustment. Adding the same white
        // offset to each channel would wash color out of a lifted foreground.
        var toneGain = luminance > 0 ? targetLuminance / luminance : 1
        if maximum > 0 {
            let ceiling = maximum >= 1 ? 1 : max(maximum, 254.0 / 255)
            toneGain = min(toneGain, ceiling / maximum)
        }
        if minimum > 0 {
            toneGain = max(toneGain, min(1, (1.0 / 255) / minimum))
        }
        let newLuminance = luminance * toneGain
        // Warm skin-like colors get less saturation. This deliberately errs on
        // the protective side and is not face/identity recognition.
        let skinLike = r > g && g > b && r - b > 0.04 && r - g < 0.30
            && saturation > 0.08 && saturation < 0.65
        let colorGain = 1 + recipe.vibrance * pow(1 - saturation, 2) * (skinLike ? 0.25 : 1)
        var chroma = [(r - luminance) * toneGain * colorGain, (g - luminance) * toneGain * colorGain,
                      (b - luminance) * toneGain * colorGain]
        // Compress chroma only as far as needed to stay in gamut. Hard per-channel
        // clipping would shift hue and lose highlight color detail.
        var gamutScale = 1.0
        for component in chroma {
            if component > 0 { gamutScale = min(gamutScale, (1 - newLuminance) / component) }
            if component < 0 { gamutScale = min(gamutScale, -newLuminance / component) }
        }
        // A darker luminance can itself raise HSV saturation even without a
        // color boost. Bound that side effect too, especially on skin and reds.
        let saturationCeiling = saturation + saturation * recipe.vibrance
            * pow(1 - saturation, 2) * (skinLike ? 0.25 : 1)
        let highChroma = chroma.max() ?? 0, lowChroma = chroma.min() ?? 0
        let saturationDenominator = highChroma - lowChroma - saturationCeiling * highChroma
        if saturationDenominator > 0 {
            gamutScale = min(gamutScale, saturationCeiling * newLuminance / saturationDenominator)
        }
        chroma = chroma.map { (newLuminance + $0 * gamutScale).clamped(to: 0...1) }
        return (chroma[0], chroma[1], chroma[2])
    }

    private func enhancementPixels(_ image: CGImage, maximumSide: Int) -> (luminances: [Double], saturations: [Double]) {
        let scale = min(1.0, Double(maximumSide) / Double(max(image.width, image.height)))
        let width = max(1, Int(Double(image.width) * scale)), height = max(1, Int(Double(image.height) * scale))
        var bytes = [UInt8](repeating: 0, count: width * height * 4)
        let drawn = bytes.withUnsafeMutableBytes { raw -> Bool in
            guard let bitmap = CGContext(
                data: raw.baseAddress, width: width, height: height, bitsPerComponent: 8, bytesPerRow: width * 4,
                space: CGColorSpace(name: CGColorSpace.sRGB)!, bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue
            ) else { return false }
            bitmap.interpolationQuality = .medium
            bitmap.draw(image, in: CGRect(x: 0, y: 0, width: width, height: height))
            return true
        }
        guard drawn else { return ([], []) }
        var luminances: [Double] = [], saturations: [Double] = []
        luminances.reserveCapacity(width * height)
        saturations.reserveCapacity(width * height)
        for offset in stride(from: 0, to: bytes.count, by: 4) {
            let r = Double(bytes[offset]) / 255, g = Double(bytes[offset + 1]) / 255, b = Double(bytes[offset + 2]) / 255
            let maximum = max(r, max(g, b)), minimum = min(r, min(g, b))
            luminances.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
            saturations.append(maximum > 0 ? (maximum - minimum) / maximum : 0)
        }
        return (luminances, saturations)
    }

    private func exportSourceName(_ url: URL) -> String {
        // Leave space for IDs, timestamps and collision suffixes even for long
        // multibyte filenames. Do not copy path separators/control characters.
        let original = url.deletingPathExtension().lastPathComponent
        var name = ""
        for scalar in original.unicodeScalars {
            let part = CharacterSet.controlCharacters.contains(scalar) || "/\\:".unicodeScalars.contains(scalar)
                ? "-" : String(scalar)
            guard name.utf8.count + part.utf8.count <= 120 else { break }
            name.append(part)
        }
        return name.isEmpty ? "PickerRoy" : name
    }

    private func write(_ image: CGImage, to url: URL, jpeg: Bool) throws {
        let type = jpeg ? UTType.jpeg.identifier : UTType.png.identifier
        let data = NSMutableData()
        guard let destination = CGImageDestinationCreateWithData(data, type as CFString, 1, nil) else {
            throw NSError(domain: "PickerRoy", code: 2, userInfo: [NSLocalizedDescriptionKey: "无法建立导出文件"])
        }
        let options: CFDictionary = jpeg
            ? [kCGImageDestinationLossyCompressionQuality: 0.94] as CFDictionary
            : [:] as CFDictionary
        CGImageDestinationAddImage(destination, image, options)
        guard CGImageDestinationFinalize(destination) else {
            throw NSError(domain: "PickerRoy", code: 3, userInfo: [NSLocalizedDescriptionKey: "图片写入失败"])
        }

        // Exclusive creation protects both previous exports and unrelated files,
        // including when two export tasks happen to choose the same name.
        let encoded = data as Data
        var attempt = 1
        while true {
            let destinationURL = attempt == 1 ? url : url.deletingPathExtension()
                .appendingPathExtension("\(attempt).\(url.pathExtension)")
            do {
                try encoded.write(to: destinationURL, options: .withoutOverwriting)
                return
            } catch let error as NSError where error.domain == NSCocoaErrorDomain && error.code == NSFileWriteFileExistsError {
                attempt += 1
            }
        }
    }
}
