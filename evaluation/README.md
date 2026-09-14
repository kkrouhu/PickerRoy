# Ground-truth evaluation

Private source videos and private labels belong in `evaluation/private/`, which Git ignores.

Each target is a desired moment. The tolerance permits equivalent neighboring frames:

```json
{
  "videos": [
    {
      "name": "walk-through-forest",
      "analysis": "private/data/cache/VIDEO_ID/analysis.json",
      "targets": [
        {"timestamp": 3.42, "tolerance_ms": 350},
        {"timestamp": 11.08, "tolerance_ms": 500}
      ]
    }
  ]
}
```

Run `framepick-evaluate evaluation/private/ground_truth.json`. The report includes Top-1/3/5/10 hit rate, duplicate rate, technical rejection rate, category coverage, and the number of recommendations shown.

