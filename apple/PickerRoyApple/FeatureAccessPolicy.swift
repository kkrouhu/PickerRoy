import Foundation

/// The single feature-access boundary for the app.
///
/// V1.0 is intentionally and completely free. A future commercial release can
/// provide a different policy backed by StoreKit without adding scattered
/// `isPro` checks to views or the media-processing engine.
enum PickerRoyFeature: CaseIterable, Sendable {
    case analysis
    case personalization
    case directExport
    case optimizedExport
}

struct FeatureAccessPolicy: Sendable {
    private let availableFeatures: Set<PickerRoyFeature>

    static let v1Free = FeatureAccessPolicy(
        availableFeatures: Set(PickerRoyFeature.allCases)
    )

    func allows(_ feature: PickerRoyFeature) -> Bool {
        availableFeatures.contains(feature)
    }
}
