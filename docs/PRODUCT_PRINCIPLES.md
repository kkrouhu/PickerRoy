# PickerRoy Product Principles

These principles govern PickerRoy V1.0 and future releases.

1. Best-frame selection is the core product value. Every major product decision should improve the chance of finding the frame a person genuinely wants to save or publish.
2. Privacy by Design. Privacy is an architectural requirement, not a marketing add-on.
3. Core media processing happens on-device whenever technically reasonable.
4. The complete core workflow works offline: import, decode, analyze, rank, select, personalize, render, and export.
5. User videos, photos, thumbnails, file paths, and visual preferences must not be uploaded unless a future feature clearly requires it and the product owner explicitly approves it.
6. Minimize data collection. V1.0 collects no user data.
7. Minimize permissions. Use system pickers for user-selected videos and add-only Photos access when saving on iPhone or iPad.
8. Do not introduce servers, cloud AI, analytics, advertising, or tracking without a clear product reason and explicit approval.
9. Do not sacrifice selection quality merely to claim offline operation. Evaluate better on-device models and algorithms first.
10. Privacy claims must always match actual technical behavior.
11. Core media processing and optional network services are separate modules. A future StoreKit purchase flow must never upload or remotely analyze user media.
12. Avoid unnecessary rewrites. Improve the working product through small, testable changes.

## V1.0 release facts

- PickerRoy V1.0 is free to download and all current core features are available.
- It contains no In-App Purchase, subscription, paywall, upgrade button, purchase button, or restore-purchase control.
- Its native Apple target uses only Apple system frameworks.
- Its media workflow uses AVFoundation, Vision, Core Image, ImageIO, and local application storage.
- A privacy claim may be published only after the release build and device test confirm it.

## Long-term selection priorities

Continue evaluating improvements to people, expression, pose, action completeness, composition, clarity, scenery, animals, objects, special moments, near-duplicate suppression, and the likelihood that a user will actually save or publish a frame.
