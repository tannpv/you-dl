# You-DL

Local macOS/Windows downloader. Python 3.12+, PySide6, yt-dlp and FFmpeg.
Rule #1 canonical source: `~/.claude/CLAUDE.md`.
Shared policy and profiles belong to config; extraction belongs to yt-dlp.

- `src/you_dl/CLAUDE.md`: application boundaries
- `scripts/CLAUDE.md`: packaging
- `docs/plan.md`: design and Rule #1 pass
- `docs/test-cases.xlsx`: acceptance register
- `docs/verification.md`: current evidence and release gates

Checks: `uv run ruff check .`, `uv run mypy`, `QT_QPA_PLATFORM=offscreen uv run pytest`.
Never claim a native platform tested from a different platform's build.
