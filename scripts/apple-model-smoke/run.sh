#!/bin/bash
set -euo pipefail

# Run with: bash scripts/apple-model-smoke/run.sh
# The binary uses injected, disposable preferences and nonexistent media URLs.
# Compilation artifacts and module cache stay beneath the repository's work/.
pickerroy_repo="$(cd "$(dirname "$0")/../.." && pwd)"
pickerroy_smoke_parent="$pickerroy_repo/work/apple-model-smoke"
mkdir -p "$pickerroy_smoke_parent" "$pickerroy_repo/work/swift-module-cache"
pickerroy_smoke_run="$(mktemp -d "$pickerroy_smoke_parent/run.XXXXXX")"

CLANG_MODULE_CACHE_PATH="$pickerroy_repo/work/swift-module-cache" \
xcrun swiftc -module-cache-path "$pickerroy_repo/work/swift-module-cache" \
    "$pickerroy_repo/apple/PickerRoyApple/Models.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/AnalysisControl.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/AnalysisEngine.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/PreferenceStore.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/FeatureAccessPolicy.swift" \
    "$pickerroy_repo/apple/PickerRoyApple/PickerRoyModel.swift" \
    "$pickerroy_repo/scripts/apple-model-smoke/ModelSmoke.swift" \
    -o "$pickerroy_smoke_run/apple-model-smoke"

"$pickerroy_smoke_run/apple-model-smoke" "$pickerroy_smoke_run"
