param([switch]$SkipInstall)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path -LiteralPath '.venv/Scripts/python.exe')) {
    & py -3.14 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.14 is required to build.' }
}
$bridgePython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not $SkipInstall) {
    & $bridgePython install_deps.py requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
& $bridgePython -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Bridge tests failed.' }
& $bridgePython make_icon.py
if ($LASTEXITCODE -ne 0) { throw 'Icon generation failed.' }

$bundleArguments = @(
    '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile', '--windowed',
    '--name', 'Better SMTC Bridge', '--icon', 'smtc-bridge.ico',
    '--version-file', 'windows-version-info.txt',
    '--add-data', 'control.html:.', '--add-data', 'assets:assets',
    '--add-data', 'smtc-bridge.pyw:.', '--add-data', 'smtc-bridge.ico:.',
    '--add-data', 'licenses:licenses', '--add-data', 'LICENSE:.',
    '--add-data', 'THIRD_PARTY_NOTICES.md:.',
    '--collect-submodules', 'winrt', '--collect-submodules', 'aiohttp',
    '--hidden-import', 'pystray._win32', '--hidden-import', 'plyer.platforms.win.notification',
    'bridge.py'
)
& $bridgePython @bundleArguments
if ($LASTEXITCODE -ne 0) { throw 'Executable build failed.' }
& $bridgePython package_release.py
if ($LASTEXITCODE -ne 0) { throw 'Release packaging failed.' }
Write-Output 'Built dist/Better-SMTC-Bridge-1.0.0-Windows-x64.zip'
