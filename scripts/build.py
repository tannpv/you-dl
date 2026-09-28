"""Build on the target OS; bundle tools and emit installable packages."""

import hashlib
import importlib.metadata
import json
import os
import platform
import plistlib
import shutil
import subprocess
from pathlib import Path

import PyInstaller.__main__

from scripts.installer import installer_script
from scripts.package_assets import generate_icons
from scripts.package_config import (
    BUILD,
    DIST,
    NOTARY_PROFILE_ENV,
    ROOT,
    SIGN_IDENTITY_ENV,
    VERSION,
    artifact_stem,
)
from you_dl.config import APP_BUNDLE_ID, APP_NAME
from you_dl.core import resolve_tools
from you_dl.resources import ASSET_DIR


def collect_notices() -> Path:
    """Preserve installed package notices; record native provenance separately."""
    directory = BUILD / "notices"
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    packages = {}
    for distribution in importlib.metadata.distributions():
        name = distribution.metadata["Name"]
        packages[name] = distribution.version
        for item in distribution.files or []:
            if any(
                part.lower().startswith(("license", "copying", "notice")) for part in item.parts
            ):
                source = Path(distribution.locate_file(item))
                if source.is_file():
                    safe_parts = [part for part in item.parts if part not in {"..", "."}]
                    target = directory / name / Path(*safe_parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
    (directory / "python-packages.json").write_text(json.dumps(packages, indent=2))
    shutil.copyfile(ROOT / "docs" / "THIRD-PARTY-NOTICES.md", directory / "README.md")
    return directory


def windows_version_file() -> Path:
    version = tuple(int(part) for part in VERSION.split(".")) + (0,)
    entries = {
        "FileDescription": APP_NAME,
        "FileVersion": VERSION,
        "InternalName": APP_NAME,
        "OriginalFilename": f"{APP_NAME}.exe",
        "ProductName": APP_NAME,
        "ProductVersion": VERSION,
    }
    table = ",".join(f"StringStruct({key!r}, {value!r})" for key, value in entries.items())
    text = f"""VSVersionInfo(
      ffi=FixedFileInfo(filevers={version!r}, prodvers={version!r}, mask=0x3f,
        flags=0, OS=0x40004, fileType=0x1, subtype=0, date=(0, 0)),
      kids=[StringFileInfo([StringTable('040904B0', [{table}])]),
            VarFileInfo([VarStruct('Translation', [1033, 1200])])])"""
    path = BUILD / "version.txt"
    path.write_text(text, encoding="utf-8")
    return path


def package_mac(identity: str | None) -> Path:
    app = DIST / f"{APP_NAME}.app"
    info_path = app / "Contents" / "Info.plist"
    with info_path.open("rb") as file:
        info = plistlib.load(file)
    info.update(CFBundleShortVersionString=VERSION, CFBundleVersion=VERSION)
    with info_path.open("wb") as file:
        plistlib.dump(info, file)
    sign = ["codesign", "--force", "--deep", "--sign", identity or "-"]
    if identity:
        sign += [
            "--options",
            "runtime",
            "--timestamp",
            "--entitlements",
            str(ROOT / "packaging" / "entitlements.plist"),
        ]
    subprocess.run([*sign, str(app)], check=True)
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app)], check=True)
    stage = BUILD / "dmg"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir()
    subprocess.run(["ditto", str(app), str(stage / app.name)], check=True)
    (stage / "Applications").symlink_to("/Applications")
    shutil.copyfile(ROOT / "docs" / "INSTALL.md", stage / "Install.txt")
    artifact = DIST / f"{artifact_stem()}.dmg"
    subprocess.run(
        [
            "hdiutil",
            "create",
            "-volname",
            APP_NAME,
            "-srcfolder",
            str(stage),
            "-ov",
            "-format",
            "UDZO",
            str(artifact),
        ],
        check=True,
    )
    if identity:
        subprocess.run(
            ["codesign", "--force", "--sign", identity, "--timestamp", str(artifact)], check=True
        )
    profile = os.environ.get(NOTARY_PROFILE_ENV)
    if profile:
        if not identity:
            raise ValueError("Notarization requires a Developer ID signing identity")
        response = subprocess.check_output(
            [
                "xcrun",
                "notarytool",
                "submit",
                str(artifact),
                "--keychain-profile",
                profile,
                "--wait",
                "--output-format",
                "json",
            ]
        )
        result = json.loads(response)
        if result["status"] != "Accepted":
            raise RuntimeError(f"Notarization failed: {result['id']}: {result['status']}")
        subprocess.run(["xcrun", "stapler", "staple", str(artifact)], check=True)
    return artifact


def write_manifest(artifact: Path, identity: str | None) -> None:
    with artifact.open("rb") as file:
        digest = hashlib.file_digest(file, "sha256").hexdigest()
    manifest = {
        "name": APP_NAME,
        "version": VERSION,
        "platform": platform.system(),
        "architecture": platform.machine(),
        "artifact": artifact.name,
        "sha256": digest,
        "signing": "Developer ID"
        if identity
        else "ad-hoc"
        if platform.system() == "Darwin"
        else "unsigned",
        "notarized": bool(os.environ.get(NOTARY_PROFILE_ENV)),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
    }
    artifact.with_suffix(artifact.suffix + ".json").write_text(json.dumps(manifest, indent=2))
    artifact.with_suffix(artifact.suffix + ".sha256").write_text(f"{digest}  {artifact.name}\n")


def build() -> None:
    BUILD.mkdir(exist_ok=True)
    icons = generate_icons(BUILD / "icons")
    system = platform.system()
    identity = os.environ.get(SIGN_IDENTITY_ENV) if system == "Darwin" else None
    args = [
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        APP_NAME,
        "--paths",
        str(ROOT / "src"),
        "--distpath",
        str(DIST),
        "--workpath",
        str(BUILD),
        "--specpath",
        str(BUILD),
        "--collect-all",
        "yt_dlp",
        "--collect-all",
        "yt_dlp_ejs",
        "--copy-metadata",
        "you-dl",
        "--osx-bundle-identifier",
        APP_BUNDLE_ID,
        "--icon",
        str(icons["icns" if system == "Darwin" else "ico"]),
        "--add-data",
        f"{ASSET_DIR}:you_dl/assets",
        "--add-data",
        f"{collect_notices()}:notices",
    ]
    if system == "Windows":
        args += ["--version-file", str(windows_version_file())]
    if identity:
        args += [
            "--codesign-identity",
            identity,
            "--osx-entitlements-file",
            str(ROOT / "packaging" / "entitlements.plist"),
        ]
    for path in resolve_tools().values():
        args += ["--add-binary", f"{Path(path).resolve()}:tools"]
    args.append(str(ROOT / "scripts" / "launch.py"))
    PyInstaller.__main__.run(args)
    if system == "Darwin":
        artifact = package_mac(identity)
    elif system == "Windows":
        spec = BUILD / "installer.iss"
        spec.write_text(installer_script(icons["ico"]), encoding="utf-8")
        subprocess.run(["iscc", str(spec)], check=True)
        artifact = DIST / f"{artifact_stem()}-Setup.exe"
    else:
        raise ValueError(f"Unsupported installer platform: {system}")
    write_manifest(artifact, identity)


if __name__ == "__main__":
    build()
