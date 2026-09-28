# Installable package phase

## Rule #1 before code

- Reuse `config.APP_NAME`, app identifier, version from package metadata, existing
  tool resolver and PyInstaller build. Do not create a second package build path.
- Put installer identity, artifact naming, paths and signing environment names in
  one packaging configuration module. Installer metadata consumes it.
- One icon source produces macOS and Windows assets; no separate hand-drawn variants.
- Add one frozen self-test entry point for native bundles. CI runs installed app
  through this entry point; Qt, bundled tools and real conversion must work without
  Python or Homebrew on PATH. This is a diagnostic CLI, not an end-user screen.
- Export additional platform builds through data in the CI matrix. Keep build logic
  in Python; workflow only provisions platform tools and invokes checks/build.
- Use private repository and prerelease assets for installable preview. Credentials
  stay outside source; signing and notarization read configured environment values.

## Acceptance and order

1. Extend and render test register before installer code changes.
2. Branded icon, version metadata, stable installer identity, Start Menu shortcut,
   optional desktop shortcut, per-user install and uninstall entry for Windows.
3. macOS drag-to-Applications DMG; Developer ID signing when identity exists;
   notarization only with an existing authenticated keychain profile.
4. Build Windows x64 and macOS arm64/x64 on appropriate GitHub runners.
5. Test frozen tool discovery/Qt load and media conversion; silently install,
   upgrade and uninstall Windows build; verify DMG integrity and copied Mac app.
6. Record SHA256 and build identity alongside packages. Review cleanup, correctness,
   reuse, security and architecture before merge or release.
7. Publish private prerelease downloads with accurate signing and test status.

No certificates or private keys are exported to CI. Windows signing remains a
separate credential gate; unsigned installer status is explicit.
