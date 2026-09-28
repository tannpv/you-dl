# Verification — 2026-09-28

## Evidence

- `uv run ruff check .`: pass; no unused imports or variables.
- `uv run mypy`: pass, 7 application modules.
- `QT_QPA_PLATFORM=offscreen uv run pytest -q`: 32 passed.
- Test register authored and rendered before application code. Added regression
  coverage for review findings and architecture guards during implementation.
- Qt render inspected: readable fields, correct labels, no clipped controls.
- Native macOS application launched through Computer Use. Download controls disabled
  during work; progress displayed; bundled worker completed a real MP3 download and
  controls re-enabled with Complete status. Restart restored destination.
- Actual YouTube video `YE7VzlLtp-4` (Big Buck Bunny) downloaded via application
  worker as MP3 and MP4. FFprobe: MP3, 596.474 s, 14,318,368 bytes; MP4 H.264 + AAC,
  596.521 s, 84,829,606 bytes.
- Actual public test playlist `PLt5yu3-wZAlSLRHmI1qNm0wjyVNWw1pCU` downloaded via
  application worker. One item, MP3, 634.578 s. Path:
  `single video playlist/001 - Big Buck Bunny 60fps 4K - Official Blender Foundation Short Film [aqz-KE-bpKQ].mp3`.
- The older yt-dlp fixture `BaW_jenozKc` was unavailable; it was not counted as a pass.
- Synthetic local media test verifies real conversion without relying on YouTube.
- Cancellation tests kill worker plus descendant subprocess and verify reap; Qt
  controller tests exercise completion, cancel and retry across spawned processes.

## Rule #1 Compliance

| Concern | Single owner | Machine evidence |
|---|---|---|
| Formats and quality values | `config.PROFILES`, generated labels and selectors | Every profile tested; additional FLAC profile requires data only |
| URL acceptance/canonicalization | `core.normalize_url` | Accepted and malicious URL vectors |
| Download options, file naming, retry | `core.download_options` | Profile and resume tests |
| Extraction/conversion | yt-dlp / FFmpeg through `worker` | Real local and YouTube conversions |
| Network/process boundaries | `worker` / `controller` | AST import guard blocks new unowned clients |
| Process ownership and cancellation | `Controller` | Spawned descendant termination and lifecycle tests |
| Preferences and product policy | `Preference`, config constants | Settings persistence test |
| Error/completion reporting | worker terminal event, controller finish | Partial and empty playlist regression tests |

Cleanup removed unused state enum members and duplicate pipe-draining logic.
Test doubles share one parameterized implementation. Build/test outputs stay ignored;
no credentials, downloaded media, node_modules or virtual environment enters source.
`tests/` explicitly overrides a machine-wide Git ignore so tests remain versioned.

## Release gates still open

- Native Windows installer build, installation and download tests. Private repository
  created at https://github.com/tannpv/you-dl; installer CI is being prepared.
- Intel macOS build/test; current machine and package target Apple Silicon.
- Apple Developer ID/notarization and Windows code signing.
- Public redistribution review of bundled Qt/FFmpeg/Node/Python notices and applicable
  source obligations. Current package is a local testing build.
- Large multi-item playlist/network-interruption testing. A live single-item playlist
  passed; partial failures and retry behavior have automated coverage.

No production deployment, merge, upload or public release performed.

## Installer phase

User authorized GitHub source upload and installer CI. Private repository created;
macOS arm64/x64 and Windows x64 workflow defined. Packaging tests increase suite to
34 passing tests; mypy covers 9 application modules. Source self-test passes Qt,
spawned worker, Node execution and MP3 conversion. CI install/upgrade/uninstall and
DMG tests are pending. Developer ID identity is available locally; no certificate
or private key exported. Notarization profile and Windows signing remain unconfigured.
