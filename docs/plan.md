# Desktop downloader plan

Build a local-only Qt desktop app for macOS and Windows. Accept YouTube video,
Shorts and playlist links. Export MP3 audio or MP4 (H.264/AAC, up to 1080p).
Allow destination selection, progress, cancellation and retry. Download only
media the user owns or has permission to save. No login, cloud service or DRM bypass.

## Rule #1 before coding

1. Existing ownership: repository was empty. yt-dlp owns extraction, playlist
   traversal, resumable transfers and filename sanitization; FFmpeg owns conversion.
2. Reuse: call those libraries rather than implement scraping or codecs.
3. Third case: format profiles are data; UI and engine consume the same registry.
4. Meaningful values: central settings, UI copy and format definitions; no shell
   interpolation. Paths derive from OS locations or user choice.
5. Boundaries: URL validation and option building in core; isolated download
   subprocess owns network/conversion; GUI owns lifecycle. Tests exercise these
   boundaries, malicious inputs, error/cancel outcomes and actual conversion.

## Execution and acceptance

1. Generate and render docs/test-cases.xlsx before implementation.
2. Implement core and tests, then Qt UI using a child process so cancellation
   can terminate FFmpeg and download work without freezing the window.
3. Persist destination/format preferences through Qt settings.
4. Bundle Python, Qt, yt-dlp, FFmpeg/ffprobe and JS runtime; build macOS app/DMG
   locally and define Windows installer pipeline on Windows.
5. Run lint, type checking, unit/UI and real local-media conversion tests;
   visually inspect UI. Exercise public YouTube only using a suitable test clip.
6. Clean unused code/dependencies and temporary files; full review of correctness,
   security and Rule #1. Fix findings and record evidence before any merge.

## Release boundaries

No remote or existing release infrastructure exists. Local build is a testing
artifact. Windows native validation, Apple notarization and Windows signing
require corresponding runners/credentials and remain explicit release gates.
