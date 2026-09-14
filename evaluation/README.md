# 人工标准答案评测

私人原视频和人工标签应放在 `evaluation/private/`，该目录不会被 Git 收录。

每个 target 代表一个真正想保留的瞬间，tolerance 允许视觉上等价的相邻帧：

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

运行 `pickerroy-evaluate evaluation/private/ground_truth.json`。报告会计算 Top-1/3/5/10 命中率、重复率、技术废片淘汰率、类别覆盖率和展示候选数量。
