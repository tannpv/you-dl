# Full Review — feature/desktop-downloader-20260928 (28 files, +2508/-0)

## Verdict

APPROVE WITH FIXES — local testing implementation reviewed; correctness fixes landed
and checked. Public release remains gated on Windows/native-platform and signing work.
File count describes the implementation/evidence snapshot before this report.

## Findings

| # | Sev | Phase | File:Line | Finding | Suggested fix |
|---|---|---|---|---|---|
| 1 | Warning, fixed | 1/2 | src/you_dl/controller.py:33 | Qt's inherited `event` method was shadowed by a signal | Renamed to `update`; type checker passes |
| 2 | Warning, fixed | 2/5 | src/you_dl/controller.py:68 | Duplicate drain logic and synchronous join complicated cancellation state | One bounded drain path; cancel state retained until async reap; lifecycle tests pass |
| 3 | Warning, fixed | 1/4 | src/you_dl/core.py:88 | Blank destination resolved implicitly to working directory | Reject blank before path resolution; regression test passes |
| 4 | Warning, fixed | 2 | src/you_dl/worker.py:46 | Zero downloader exit code could mark an empty playlist complete | Require final file hook as well; empty/existing/partial tests pass |
| 5 | Warning, fixed | 3/5 | src/you_dl/config.py:62 | Format labels duplicated bitrate/height values; bitrate implied media kind | Generate labels/selectors from numeric values; explicit export kind; extra format guard passes |
| 6 | Warning, fixed | 1 | .github/workflows/build.yml:29 | Chocolatey executable shims are not portable bundled tools | Select actual FFmpeg binary directory before packaging |
| 7 | Warning, release gate | 1/4 | scripts/build.py:71 | Windows installer has not been built or run natively | Run supplied Windows workflow and install/download QA before release |
| 8 | Warning, release gate | 4 | scripts/build.py:20 | Testing packages have no distribution signing/notarization or bundled license audit | Complete credentials/native signing and dependency redistribution review before public distribution |

## Duplicates removed

Cancellation issues from correctness and architecture review counted once (#2).
Format registry issues from quality and extensibility review counted once (#5).
No parallel extraction, conversion, URL-validation or subprocess implementation added.

## Phases run

| Phase | Method |
|---|---|
| 1. Project review | Inline fallback; root/scoped CLAUDE.md and Rule #1 |
| 2. Correctness + reuse | Inline fallback; URL, worker, cancellation, retry and error paths |
| 3. Quality / simplification | Inline fallback, report first; follow-up fixes within authorized development scope |
| 4. Security | Inline fallback; no shell interpolation, no credentials, plain-text untrusted titles, local-only UI |
| 5. Architecture duplication | Module map, profile extension test and AST boundary guard |

Evidence: 32 tests passed, Ruff clean, mypy clean (7 modules), real MP3/MP4 conversion,
real YouTube video and single-item playlist, native macOS bundled application download.
Largest file (`app.py`) re-read after fixes. No remote exists, so fetch/diff against an
existing integration branch was not possible; reviewed all new files using intent-to-add.

## What was NOT checked

Windows native installation, Intel macOS, signing/notarization, public distribution
license/source obligations, very large playlists, and real network interruption.
No merger or production release approved. Details in `verification.md`.

## Installer phase follow-up

User authorized private GitHub repository and installer CI. Reviewed shared packaging
config, icon generation, Inno Setup metadata, offline frozen diagnostics and native
install verification. Reused existing resolver, app identity and version metadata.
No signing keys exported. Native dependency license collection preserves notices;
public redistribution audit remains open. Fixed two type-check findings in frozen
diagnostics and verified SVG -> ICO/ICNS conversion. Ruff and mypy pass; 34 tests pass.
Source diagnostic verifies Qt, spawned Python worker, Node execution and real MP3
conversion. CI must still prove installed packages before release artifacts are offered.
