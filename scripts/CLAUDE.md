# Packaging

Run `uv run -m scripts.build` on target OS. Tools resolved by application resolver,
then included as PyInstaller binaries (dependent libraries collected by PyInstaller).
`launch.py` dispatches multiprocessing before importing Qt, including frozen apps.
macOS produces app + DMG. Windows requires Inno Setup and produces per-user installer.
`package_config.py` owns artifact names and identity; `package_assets.py` derives icons
from the app SVG; `installer.py` owns Inno Setup generation. `verify_package.py`
installs/copies the package and runs offline frozen diagnostics with restricted PATH.
Release gates: native install/download tests, license/source notices, signing,
macOS notarization. CI artifacts are testing builds, not public releases.
