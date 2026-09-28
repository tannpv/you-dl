# You-DL

A local desktop app for saving YouTube videos and playlists as MP3 audio or
MP4 video. Runs on macOS and Windows. No account or server required.

## Use

1. Open You-DL, paste a YouTube video, Shorts or playlist URL.
2. Enable **Download playlist** for playlists (up to 500 entries).
3. Choose MP3 192/320 kbps or MP4 up to 720p/1080p and a save folder.
4. Click **Download**, then **Open folder** when finished.

Cancel stops the worker and conversion processes. Retry uses the same settings
and resumes partial transfers where supported. Completed files are not overwritten.
Playlist failures appear in the details panel and result in a failed/partial status.
Files use title + video ID; playlists get their own folder and ordered filenames.

MP4 selects H.264/AAC streams for native playback. If YouTube does not offer those
streams, the app reports a format error rather than saving an incompatible codec.
MP3 bitrate cannot improve the source audio quality. Download only content you own
or have permission to save. Private, paid, DRM-protected and login-required content
are outside this version's scope.

## Develop

Install Python 3.12+, [uv](https://docs.astral.sh/uv/), FFmpeg (with ffprobe), and
Node.js 22+ on PATH. Then:

```sh
uv sync --frozen --extra dev
uv run you-dl
```

macOS media tools: `brew install ffmpeg node`.
Windows media tools: `winget install Gyan.FFmpeg` and
`winget install OpenJS.NodeJS.LTS`; reopen terminal afterward.

```sh
uv run ruff check .
uv run mypy
QT_QPA_PLATFORM=offscreen uv run pytest -q
uv run -m scripts.build
uv run -m scripts.verify_package
```

On PowerShell set `$env:QT_QPA_PLATFORM="offscreen"` before running pytest.
Windows packaging also needs Inno Setup 6's `iscc` on PATH.
Build on each target OS: macOS creates `.app` and `.dmg`; Windows creates installer
`.exe`. Bundles include Python, Qt, yt-dlp/EJS, FFmpeg, ffprobe and Node.js.
End users do not install those tools separately.

## Status and release gates

See [verification](docs/verification.md) for actual checks and remaining gates.
Set `MACOS_SIGN_IDENTITY` to an installed Developer ID identity to sign Mac builds.
Set `MACOS_NOTARY_PROFILE` to an existing notarytool keychain profile to notarize.
No private keys or credentials belong in source. Public distribution needs
Apple notarization, Windows signing, native platform QA, and a review
of notices/source obligations for bundled Qt, FFmpeg builds and other dependencies.
Private repository: https://github.com/tannpv/you-dl. GitHub workflow builds Mac
Apple Silicon, Mac Intel and Windows x64 installers. Windows CI uses Windows Server
2025; Windows 11 interactive desktop QA remains a separate check.
See [installation steps](docs/INSTALL.md). Package manifests identify signing status.

YouTube changes can break downloads. Update the locked yt-dlp dependency, rerun
tests and rebuild. Never download and execute updates silently inside the app.

## Sources

- [yt-dlp API and options](https://github.com/yt-dlp/yt-dlp#embedding-yt-dlp)
- [YouTube JavaScript runtime requirements](https://github.com/yt-dlp/yt-dlp/wiki/EJS)
- [PyInstaller native platform builds](https://pyinstaller.org/en/stable/)
