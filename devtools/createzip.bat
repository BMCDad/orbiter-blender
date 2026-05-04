@echo off
setlocal

rem Creates the distributable addon zip for Blender / GitHub Releases.
rem Run from the repo root:  devtools\createzip.bat

rem Always operate relative to the repo root, regardless of CWD
cd /d "%~dp0.."

set OUTPUT=orbiter-blender-2.zip

if exist "%OUTPUT%" del "%OUTPUT%"

powershell -NoProfile -Command ^
  "Compress-Archive -Path 'blender_manifest.toml','__init__.py','orbiter_tools.py','import_tools.py','LICENSE' -DestinationPath '%OUTPUT%'"

if %errorlevel% neq 0 (
    echo ERROR: Failed to create %OUTPUT%
    exit /b 1
)

echo Created %OUTPUT%
