@echo off
rem Better SMTC Bridge build entry point, extending the original SMTC Bridge project.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1"
if errorlevel 1 pause
