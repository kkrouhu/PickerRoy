import Foundation

final class AnalysisControl: @unchecked Sendable {
    private let lock = NSLock()
    private var paused = false
    private var cancelled = false

    func pause() {
        lock.lock(); paused = true; lock.unlock()
    }

    func resume() {
        lock.lock(); paused = false; lock.unlock()
    }

    func cancel() {
        lock.lock(); cancelled = true; paused = false; lock.unlock()
    }

    func checkpoint() throws {
        while true {
            lock.lock()
            let shouldPause = paused
            let shouldCancel = cancelled
            lock.unlock()
            if shouldCancel || Task.isCancelled { throw CancellationError() }
            if !shouldPause { return }
            Thread.sleep(forTimeInterval: 0.08)
        }
    }
}
