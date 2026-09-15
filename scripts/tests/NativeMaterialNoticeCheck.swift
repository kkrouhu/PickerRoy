import Darwin
import Foundation

private struct CheckFailure: Error, CustomStringConvertible { let description: String }
private func expect(_ condition: @autoclosure () -> Bool, _ message: String) throws {
    if !condition() { throw CheckFailure(description: message) }
}

@main
struct NativeMaterialNoticeCheck {
    static func main() {
        do { try run() }
        catch {
            FileHandle.standardError.write(Data("FAIL: \(error)\n".utf8))
            exit(1)
        }
    }

    private static func run() throws {
        // No ContentView, PickerRoyModel or UserDefaults instance is constructed.
        // Timestamps/acknowledgements below are only local test variables.
        let testTime = 1_000.0
        try expect(MaterialUsageNotice.version == "2026-09-15.1", "Expected notice content version")
        try expect(MaterialUsageNotice.paragraphs.count == 3, "Three notice paragraphs")
        try expect(MaterialUsageNotice.paragraphs[0].contains("版权、肖像和隐私授权"), "Rights are explicit")
        try expect(MaterialUsageNotice.paragraphs[1].contains("依法承担"), "Responsibility is qualified by law")
        try expect(MaterialUsageNotice.paragraphs[2].contains("画面增强"), "Do not hide image processing")
        try expect(MaterialUsageNotice.paragraphs[2].contains("不排除法律规定不得免除的责任"), "No absolute waiver")
        try expect(!MaterialUsageNotice.isAcknowledged(version: "", timestamp: 0), "Fresh launch requires notice")
        try expect(!MaterialUsageNotice.isAcknowledged(version: "2026-09-14.1", timestamp: testTime), "Older notice requires renewed acknowledgement")
        try expect(!MaterialUsageNotice.isAcknowledged(version: "2099-01-01.1", timestamp: testTime), "Unknown notice is not current acknowledgement")
        for invalid in [0.0, -1.0, Double.nan, Double.infinity] {
            try expect(!MaterialUsageNotice.isAcknowledged(version: MaterialUsageNotice.version, timestamp: invalid), "Missing/invalid time requires notice")
        }
        try expect(MaterialUsageNotice.isAcknowledged(version: MaterialUsageNotice.version, timestamp: testTime), "Current version and valid time are accepted")
        print("PASS: versioned local acknowledgement validation and bounded responsibility text")

        var firstImport = MaterialUsageNotice.ImportFlow()
        try expect(!firstImport.requestImport(acknowledged: false), "First import cannot open a picker immediately")
        try expect(firstImport.presentation == .confirmImport, "First import presents notice")
        try expect(!firstImport.importPendingAfterDismissal, "No pending import before acknowledgement")
        try expect(!firstImport.acknowledge(hasRead: false), "Unchecked action cannot acknowledge")
        try expect(firstImport.presentation == .confirmImport, "Unchecked action keeps the notice")
        try expect(!firstImport.importPendingAfterDismissal, "Unchecked action cannot queue picker")
        firstImport.cancel()
        try expect(firstImport.presentation == nil && !firstImport.importPendingAfterDismissal, "Cancel clears the request")
        try expect(!firstImport.didDismiss(acknowledged: false), "Cancel does not open a picker")
        print("PASS: first import, unchecked continue and cancel never open a picker")

        var confirmed = MaterialUsageNotice.ImportFlow()
        _ = confirmed.requestImport(acknowledged: false)
        try expect(confirmed.acknowledge(hasRead: true), "Explicit simulated check allows acknowledgement")
        try expect(confirmed.presentation == nil && confirmed.importPendingAfterDismissal, "Wait for sheet dismissal")
        try expect(confirmed.didDismiss(acknowledged: true), "Import becomes available once after dismissal")
        try expect(!confirmed.didDismiss(acknowledged: true), "Repeated dismissal cannot open another picker")
        try expect(confirmed.requestImport(acknowledged: true), "Next import with current acknowledgement opens normally")
        try expect(confirmed.presentation == nil, "No repeated notice on acknowledged import")
        print("PASS: acknowledged import waits for dismissal, fires once, and supports subsequent imports")

        var invalidated = MaterialUsageNotice.ImportFlow()
        _ = invalidated.requestImport(acknowledged: false)
        _ = invalidated.acknowledge(hasRead: true)
        try expect(!invalidated.didDismiss(acknowledged: false), "Missing persisted acknowledgement blocks queued import")
        try expect(!invalidated.importPendingAfterDismissal, "Failed queued import is not retained")

        var interactiveDismiss = MaterialUsageNotice.ImportFlow()
        _ = interactiveDismiss.requestImport(acknowledged: false)
        interactiveDismiss.presentation = nil
        try expect(!interactiveDismiss.didDismiss(acknowledged: false), "Interactive dismissal is not consent")

        var readOnly = MaterialUsageNotice.ImportFlow()
        readOnly.showReadOnly()
        try expect(readOnly.presentation == .readOnly, "Sidebar opens read-only notice")
        try expect(!readOnly.acknowledge(hasRead: true), "Read-only notice cannot change acknowledgement")
        readOnly.cancel()
        try expect(!readOnly.didDismiss(acknowledged: true), "Closing read-only notice cannot import")
        print("PASS: read-only, interactive dismissal and invalidated confirmation have no import side effects")
        print("All native material notice state checks passed. No real consent or preferences were changed.")
    }
}
