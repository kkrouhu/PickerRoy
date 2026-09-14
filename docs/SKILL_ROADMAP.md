# Future Codex Skill packaging

The core analyzer, CLI, GUI, exporter, SQLite store, and evaluator have no Codex-specific dependency. That boundary allows a later skill to invoke the stable `framepick-analyze` and `framepick-evaluate` commands without moving product logic into skill instructions.

Packaging order:

1. Validate selection quality on private real footage.
2. Train and version a lightweight preference ranker from pairwise choices.
3. Freeze the CLI contract and cache schema.
4. Add a thin Codex Skill wrapper.
5. Build signed macOS and Windows release packages.

