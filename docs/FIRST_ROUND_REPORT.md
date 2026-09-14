# First-round build and debug report

Date: 2026-09-14

## What was exercised

- Environment detection on an Apple M3 Max Mac
- Single-file and recursive folder discovery
- FFprobe metadata extraction
- Four-shot scene detection on generated H.264 test media
- Shot-adaptive sampling and 16 candidate analyses
- Black/blank-frame rejection
- Apple Vision execution outside the development sandbox
- Automatic OpenCV fallback when Vision is unavailable
- Temporal scoring, perceptual deduplication, and diversity ranking
- Full-resolution PNG export (1280 × 720 source remained 1280 × 720)
- SQLite analysis, feedback, and pairwise-preference writes
- Qt GUI construction and 1320 × 860 visual render
- Missing-video error handling

## Automated status

- Tests: 12 passed
- Synthetic input: 10.04 seconds, 4 detected shots
- Candidates analyzed: 16
- Candidates presented: 9
- Technical rejections: 3 (the intended black segment)
- Candidates removed as visually duplicate: 6
- Full-resolution exports verified: 2
- Feedback writes verified: 1
- Pairwise preference writes verified: 1
- Analysis time: about 3.2 seconds on this machine

## Synthetic ground-truth metrics

- Top-1 hit rate: 33.3%
- Top-3 hit rate: 66.7%
- Top-5 hit rate: 66.7%
- Top-10 hit rate: 100%
- Duplicate rate among presented recommendations: 0%
- Source candidates identified and pruned as duplicate: 30.8%
- Technical rejection rate: 18.8%
- Category coverage: 16.7% (the synthetic source only contains test graphics)
- Recommendations presented: 9

These figures validate plumbing, not photographic taste. No real-world accuracy claim is possible until real footage has human-labelled desired frames.

## Runtime defect found and fixed

The first full run exposed that macOS Vision can import successfully but fail at inference inside a restricted process. That exception initially caused otherwise valid candidates to be rejected. Classification is now isolated from technical analysis and automatically switches once to the OpenCV CPU backend. A second native run confirmed that Apple Vision works when the app is started normally.
