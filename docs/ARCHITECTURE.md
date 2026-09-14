# Architecture

FramePick is deliberately local-first and modular:

1. `ffprobe` records stream, frame-rate, resolution, and color metadata.
2. PySceneDetect's adaptive content detector separates shots.
3. Each shot gets a motion estimate from four tiny temporary probes.
4. Sampling density changes with shot duration and motion. Short and dynamic shots get denser competition.
5. Technical metrics reject blank, black, clipped, severely soft, and failed frames before aesthetic ranking.
6. macOS Vision supplies local semantic labels and face presence. An OpenCV CPU fallback keeps the pipeline portable.
7. Category-specific formulas separately rank portrait, action, landscape, animal, product, detail, and other frames.
8. Temporal peak scoring compares local frame-to-frame change and quality curves inside the same shot.
9. A 64-bit perceptual hash removes near duplicates; a diversity-aware ranker limits category and shot domination.
10. FFmpeg seeks back to the source only on export, producing a full-resolution PNG or high-quality JPEG.

The cache holds 960-pixel previews rather than decoded video. Processing is shot-by-shot and candidate-by-candidate, so long inputs do not accumulate in memory.

## Honest limitations of version 0.1

- Face presence is available, but reliable closed-eye, pose, limb-state, and occlusion scoring are not yet implemented.
- macOS Vision labels are broad. OpenCV fallback classification is intentionally conservative and will overuse `Other`.
- Perceptual hashing catches visually near-identical frames but is weaker than learned embeddings across camera movement.
- HDR/BT.2020 is detected and warned about, but a full managed HDR-to-SDR color pipeline is not included.
- The category weights are engineering priors, not trained preference weights. Pairwise data is stored but not learned from yet.
