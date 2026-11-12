# Replacing the LGPL tray library

Better SMTC Bridge uses pystray 0.19.5 under LGPLv3. The release contains the
complete upstream source archive at
`licenses/pystray-0.19.5/source/pystray-0.19.5.tar.gz`, together with the full
GPL and LGPL texts. All 13 installed pystray source files matched this archive
when the release notices were prepared. pystray has not been modified by this
project.

You may modify the library and rebuild the application with your compatible
version. The original application source, assets and build scripts accompany
the release in `source/`. The project adds no restriction on modifying the
library portions or reverse engineering to debug those modifications. The
separate rights in the original SMTC Bridge material still apply.

On Windows, install Python 3.14 x64. Work in the repository root, or the
extracted release's `source` folder. In PowerShell:

```powershell
py -3.14 -m venv .venv
& .\.venv\Scripts\python.exe install_deps.py requirements-lock.txt
New-Item -ItemType Directory -Path modified-library -Force
tar -xzf licenses/pystray-0.19.5/source/pystray-0.19.5.tar.gz -C modified-library
```

Make your changes in `modified-library/pystray-0.19.5/lib/pystray`. Then make
that library take precedence for this PowerShell session, confirm its path,
and rebuild without reinstalling pinned dependencies:

```powershell
$env:PYTHONPATH = (Resolve-Path .\modified-library\pystray-0.19.5\lib).Path
& .\.venv\Scripts\python.exe -c "import pystray; print(pystray.__file__)"
.\build.ps1 -SkipInstall
```

The printed path should point inside `modified-library`. PyInstaller receives
that same environment and packages your replacement library. The result is in
`dist/`. Close the existing bridge before testing your rebuilt application on
the same configured port. Closing the PowerShell session ends the temporary
`PYTHONPATH` override.

When redistributing a changed library, retain its copyright and license
notices, mark your changes, provide the corresponding source and refresh the
release inventory. The full LGPL terms in the included notices control these
rights and obligations.
