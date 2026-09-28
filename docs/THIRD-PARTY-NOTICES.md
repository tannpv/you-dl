# Third-party components

You-DL bundles external components. Their licenses remain with their owners.
Installed Python distribution license/notice files are copied into the app's
`notices` directory, with a package/version inventory.

| Component | Upstream source / license information |
|---|---|
| Python | https://www.python.org/psf/license/ |
| Qt / PySide6 | https://doc.qt.io/qtforpython-6/licenses.html |
| yt-dlp | https://github.com/yt-dlp/yt-dlp/blob/master/LICENSE |
| yt-dlp EJS | https://github.com/yt-dlp/ejs |
| FFmpeg | https://ffmpeg.org/legal.html |
| Node.js | https://github.com/nodejs/node/blob/main/LICENSE |
| psutil | https://github.com/giampaolo/psutil/blob/master/LICENSE |

Build provenance: FFmpeg comes from Homebrew on macOS or Chocolatey on Windows;
Node comes from configured Node installation / actions/setup-node. FFmpeg's
license and codec dependencies depend on selected build. Frozen self-test records
bundled versions, and installer SHA256 accompanies packages.

Private preview builds. Public redistribution requires checking selected native
binaries' notices, corresponding source and relinking obligations; this file does
not claim that audit has been completed.
