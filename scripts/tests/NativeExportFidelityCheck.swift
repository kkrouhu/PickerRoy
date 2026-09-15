// Integration checks using generated video only; no user media is read.
import AVFoundation
import CoreGraphics
import CoreVideo
import Darwin
import Foundation
import ImageIO

private struct CheckFailure: Error, CustomStringConvertible {
    let description: String
}

private func expect(_ condition: @autoclosure () -> Bool, _ message: String) throws {
    if !condition() { throw CheckFailure(description: message) }
}

@main
struct NativeExportFidelityCheck {
    static func main() async {
        do {
            try await run()
        } catch {
            FileHandle.standardError.write(Data("FAIL: \(error)\n".utf8))
            exit(1)
        }
    }

    private static func run() async throws {
        guard CommandLine.arguments.count == 2 else {
            throw CheckFailure(description: "Usage: native-export-fidelity-check <new test directory>")
        }
        let root = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
        let sourceA = root.appendingPathComponent("source-a/same-name.mov")
        let sourceB = root.appendingPathComponent("source-b/same-name.mov")
        for source in [sourceA, sourceB] {
            try FileManager.default.createDirectory(at: source.deletingLastPathComponent(), withIntermediateDirectories: true)
        }
        try await makeVideo(at: sourceA)
        try FileManager.default.copyItem(at: sourceA, to: sourceB)

        let engine = AnalysisEngine()
        let videoA = VideoItem(url: sourceA)
        let videoB = VideoItem(url: sourceB)
        let square = try await engine.analyze(
            video: videoA, aspect: .square, profile: PreferenceProfile(), control: AnalysisControl()
        ) { _ in }
        let original = try await engine.analyze(
            video: videoB, aspect: .original, profile: PreferenceProfile(), control: AnalysisControl()
        ) { _ in }
        try expect(!square.isEmpty && !original.isEmpty, "Synthetic analysis must produce candidates")
        try expect(square.allSatisfy { $0.outputAspect == .square }, "Square crop must be stored on every candidate")
        try expect(original.allSatisfy { $0.outputAspect == .original }, "Original crop must be stored on every candidate")
        try expect(square.allSatisfy { $0.captureTime.isNumeric && $0.captureTime.timescale > 0 }, "Keep valid exact presentation times")
        try expect(square.contains { abs($0.time * 600 - ($0.time * 600).rounded()) > 0.01 }, "Fixture must exercise times not representable at the former 600 time base")

        let generator = AVAssetImageGenerator(asset: AVURLAsset(url: sourceA))
        generator.requestedTimeToleranceBefore = .zero
        generator.requestedTimeToleranceAfter = .zero
        for candidate in square {
            let generated = try await generator.image(at: candidate.captureTime)
            try expect(CMTimeCompare(generated.actualTime, candidate.captureTime) == 0, "Candidate timestamp must decode exactly")
            let preview = try image(data: candidate.thumbnailData)
            try expect(preview.width == preview.height, "Square preview dimensions")
            try expect(colorDistance(preview, generated.image) < 0.04, "Preview must show the stored frame, not a neighboring frame")
        }
        print("PASS: candidate times retain the actual decoded presentation timestamp and frame identity")

        let mixed = [square[0], original[0]]
        let exports = root.appendingPathComponent("exports", isDirectory: true)
        // Deliberately pass a different current UI setting. The candidate's own
        // setting must win independently for each source in this export batch.
        try await engine.export(mixed, to: exports, optimized: false, aspect: .portraitNineSixteen, control: AnalysisControl()) { _ in }
        var files = try imageFiles(in: exports)
        try expect(files.count == 2, "Same-name videos from different directories must not overwrite")
        var firstExportData: [String: Data] = [:]
        for candidate in mixed {
            let sourceID = candidate.videoID.uuidString.prefix(12).lowercased()
            guard let url = files.first(where: { $0.lastPathComponent.contains(sourceID) }) else {
                throw CheckFailure(description: "Export must identify its source independently of the filename")
            }
            let data = try Data(contentsOf: url)
            firstExportData[url.lastPathComponent] = data
            let output = try image(data: data)
            let preview = try image(data: candidate.thumbnailData)
            try expect(output.width == preview.width && output.height == preview.height, "Export must retain each candidate's preview aspect")
            try expect(colorDistance(output, preview) < 0.04, "Export must match the preview's frame")
        }
        print("PASS: mixed-aspect export ignores changed UI aspect; same-name sources remain separate")

        try await engine.export(mixed, to: exports, optimized: false, aspect: .landscapeSixteenNine, control: AnalysisControl()) { _ in }
        files = try imageFiles(in: exports)
        try expect(files.count == 4, "Repeated export must create additional files")
        for (name, data) in firstExportData {
            let saved = try Data(contentsOf: exports.appendingPathComponent(name))
            try expect(saved == data, "Repeated export must leave every existing file unchanged")
        }

        // An unrelated file at the next collision name must be preserved too.
        guard let firstName = firstExportData.keys.sorted().first else { throw CheckFailure(description: "Missing export") }
        let blocked = exports.appendingPathComponent(firstName).deletingPathExtension().appendingPathExtension("3.png")
        let sentinel = Data("unrelated existing file — do not replace".utf8)
        try sentinel.write(to: blocked, options: .withoutOverwriting)
        try await engine.export(mixed, to: exports, optimized: false, aspect: .original, control: AnalysisControl()) { _ in }
        let preservedSentinel = try Data(contentsOf: blocked)
        try expect(preservedSentinel == sentinel, "Unrelated pre-existing file must not be replaced")
        let finalFiles = try imageFiles(in: exports)
        try expect(finalFiles.count == 7, "Collision fallback must find a fresh filename")
        print("PASS: repeated exports and unrelated collision files are never overwritten")

        let concurrent = root.appendingPathComponent("concurrent", isDirectory: true)
        async let first: Void = engine.export([square[0]], to: concurrent, optimized: false, aspect: .original, control: AnalysisControl()) { _ in }
        async let second: Void = engine.export([square[0]], to: concurrent, optimized: false, aspect: .original, control: AnalysisControl()) { _ in }
        _ = try await (first, second)
        let concurrentFiles = try imageFiles(in: concurrent)
        try expect(concurrentFiles.count == 2, "Concurrent exports of the same candidate must not overwrite")
        for url in concurrentFiles {
            let output = try image(data: Data(contentsOf: url))
            try expect(output.width == output.height, "Concurrent export must leave complete, decodable images")
        }
        print("PASS: concurrent collision handling preserves both complete files")

        let optimized = root.appendingPathComponent("optimized", isDirectory: true)
        try await engine.export([square[0]], to: optimized, optimized: true, aspect: .portraitNineSixteen, control: AnalysisControl()) { _ in }
        let jpegFiles = try imageFiles(in: optimized)
        try expect(jpegFiles.count == 1 && jpegFiles[0].pathExtension == "jpg", "Optimized export creates JPEG")
        let jpeg = try image(data: Data(contentsOf: jpegFiles[0]))
        try expect(jpeg.width == jpeg.height, "Optimized export retains candidate crop before enhancement")
        print("PASS: optimized export also retains the selected crop")
        print("All native export fidelity checks passed. Synthetic evidence: \(root.path)")
    }

    private static func imageFiles(in folder: URL) throws -> [URL] {
        try FileManager.default.contentsOfDirectory(at: folder, includingPropertiesForKeys: nil)
            .filter { ["png", "jpg"].contains($0.pathExtension) }
    }

    private static func image(data: Data) throws -> CGImage {
        guard let source = CGImageSourceCreateWithData(data as CFData, nil),
              let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
            throw CheckFailure(description: "Cannot decode generated test image")
        }
        return image
    }

    private static func colorDistance(_ a: CGImage, _ b: CGImage) -> Double {
        let colorA = centerColor(a)
        let colorB = centerColor(b)
        return zip(colorA, colorB).map { abs($0 - $1) }.max() ?? 1
    }

    private static func centerColor(_ image: CGImage) -> [Double] {
        let rect = CGRect(x: image.width / 2 - 4, y: image.height / 2 - 4, width: 8, height: 8)
        guard let patch = image.cropping(to: rect) else { return [-10, -10, -10] }
        var bytes = [UInt8](repeating: 0, count: 4)
        bytes.withUnsafeMutableBytes { memory in
            let context = CGContext(data: memory.baseAddress, width: 1, height: 1, bitsPerComponent: 8, bytesPerRow: 4,
                                    space: CGColorSpaceCreateDeviceRGB(), bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)!
            context.draw(patch, in: CGRect(x: 0, y: 0, width: 1, height: 1))
        }
        return bytes.prefix(3).map { Double($0) / 255 }
    }

    private static func makeVideo(at url: URL) async throws {
        let writer = try AVAssetWriter(outputURL: url, fileType: .mov)
        let input = AVAssetWriterInput(mediaType: .video, outputSettings: [
            AVVideoCodecKey: AVVideoCodecType.h264,
            AVVideoWidthKey: 320,
            AVVideoHeightKey: 180,
            AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 3_000_000]
        ])
        input.mediaTimeScale = 30_000
        let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: input, sourcePixelBufferAttributes: [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB,
            kCVPixelBufferWidthKey as String: 320,
            kCVPixelBufferHeightKey as String: 180
        ])
        writer.add(input)
        let started = writer.startWriting()
        try expect(started, "Synthetic writer must start: \(String(describing: writer.error))")
        writer.startSession(atSourceTime: .zero)
        for frameIndex in 0..<120 {
            var waits = 0
            while !input.isReadyForMoreMediaData {
                try expect(writer.status == .writing && waits < 10_000, "Synthetic writer stalled")
                try await Task.sleep(nanoseconds: 1_000_000)
                waits += 1
            }
            var optionalBuffer: CVPixelBuffer?
            let status = CVPixelBufferCreate(kCFAllocatorDefault, 320, 180, kCVPixelFormatType_32ARGB, nil, &optionalBuffer)
            try expect(status == kCVReturnSuccess, "Synthetic pixel buffer allocation")
            let buffer = optionalBuffer!
            CVPixelBufferLockBaseAddress(buffer, [])
            let pixels = CVPixelBufferGetBaseAddress(buffer)!.assumingMemoryBound(to: UInt8.self)
            let rowBytes = CVPixelBufferGetBytesPerRow(buffer)
            // Every adjacent frame has distinctly different color, including
            // frames whose 1001/30000 timestamp cannot survive rounding to 600.
            let r = UInt8(25 + frameIndex * 173 % 200)
            let g = UInt8(25 + frameIndex * 79 % 200)
            let b = UInt8(25 + frameIndex * 43 % 200)
            for y in 0..<180 {
                for x in 0..<320 {
                    let offset = y * rowBytes + x * 4
                    let border = x < 12 || x >= 308 || y < 12 || y >= 168
                    pixels[offset] = 255
                    pixels[offset + 1] = border ? 245 : r
                    pixels[offset + 2] = border ? 245 : g
                    pixels[offset + 3] = border ? 245 : b
                }
            }
            CVPixelBufferUnlockBaseAddress(buffer, [])
            try expect(adaptor.append(buffer, withPresentationTime: CMTime(value: Int64(frameIndex * 1001), timescale: 30_000)), "Synthetic frame append")
        }
        input.markAsFinished()
        await writer.finishWriting()
        try expect(writer.status == .completed, "Synthetic video encoding must complete: \(writer.error?.localizedDescription ?? "unknown")")
    }
}
