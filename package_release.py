"""Create a portable release with license notices and the corresponding app source."""
import hashlib
from pathlib import Path
import zipfile

root = Path(__file__).resolve().parent
version = "1.0.1"
distribution = root / "dist"
executable = distribution / "Better SMTC Bridge.exe"
if not executable.is_file():
    raise SystemExit("Build the standalone executable first.")
archive = distribution / f"Better-SMTC-Bridge-{version}-Windows-x64.zip"
source_files = ["bridge.py", "audio.py", "server.py", "metadata.py", "artwork.py", "prefs.py", "control.html", "make_icon.py",
                "smtc-bridge.pyw", "smtc-bridge.ico", "icon.png", "icon.af", "smtc-bridge.spec", "settings.ini", "build.bat", "launch.bat",
                "install_deps.py", "build.ps1", "package_release.py", "windows-version-info.txt", "requirements.txt",
                "requirements-build.txt", "requirements-lock.txt", "Start Better SMTC Bridge.bat"]
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as release:
    release.write(executable, executable.name)
    for name in ("README.md", "LICENSE", "LICENSE-MIT", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md", "RELEASE_NOTES.md"):
        path = root / name
        if path.is_file():
            release.write(path, name)
    for folder in ("licenses", "docs"):
        for path in sorted((root / folder).rglob("*")):
            if path.is_file():
                release.write(path, path.relative_to(root).as_posix())
    for name in source_files:
        release.write(root / name, "source/" + name)
    for folder in ("tests", "assets", "docs"):
        for path in sorted((root / folder).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                release.write(path, "source/" + path.relative_to(root).as_posix())
    # The extracted source can build without finding license files in its parent.
    for name in ("LICENSE", "LICENSE-MIT", "THIRD_PARTY_NOTICES.md"):
        release.write(root / name, "source/" + name)
    for path in sorted((root / "licenses").rglob("*")):
        if path.is_file():
            release.write(path, "source/" + path.relative_to(root).as_posix())
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(distribution / "SHA256SUMS.txt").write_text(f"{digest}  {archive.name}\n", encoding="ascii")
print(f"Release ZIP: {archive.name} ({archive.stat().st_size / 1024 / 1024:.1f} MiB)")
