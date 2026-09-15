# PickerRoy Monetization Plan

## V1.0

Completely free.

- Free App Store download.
- All current core features available.
- No paid download.
- No In-App Purchase or subscription products.
- No StoreKit purchase implementation.
- No paywall, pricing, upgrade button, purchase button, or restore-purchase control.

Initial public observation period: approximately two weeks after public release.

The observation period is a product plan, not an in-app countdown. V1.0 must not automatically charge, lock features, or change behavior after two weeks. Any monetization change requires an explicitly approved app update and App Review.

## Future commercial model — tentative, disabled

- Pro Monthly: ¥18 per month, expected to use an auto-renewable subscription.
- Pro Yearly: ¥128 per year, expected to use an auto-renewable subscription.
- Lifetime: ¥258 one-time, expected to use a non-consumable In-App Purchase.
- Planned framework: Apple StoreKit 2.

These are planning prices only. They are not displayed or sold in V1.0. Exact App Store price points and localized storefront prices must be confirmed in App Store Connect when commercialization is explicitly approved.

Early-user migration policy: **NOT DECIDED**.

Possible future choices include grandfathered permanent access, a limited Pro period, migration to Free/Pro, or a Founder entitlement. Do not encode any of these choices until the product owner decides.

## Architecture boundary

V1.0 contains one lightweight `FeatureAccessPolicy` boundary. Every current feature is available through `v1Free`. A future release can replace that policy with an entitlement-backed implementation without changing the media analysis engine or scattering `isPro` checks through the interface.

Core media processing must remain independent of StoreKit and must not require a PickerRoy server. Apple handles App Store purchase transactions. If future entitlement verification needs network access, it stays an optional commerce service and must not transmit videos, frames, paths, or preferences.

**DO NOT ENABLE MONETIZATION UNTIL EXPLICITLY REQUESTED.**
