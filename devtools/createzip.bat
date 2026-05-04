@echo off
setlocal

rem Creates the distributable addon zip for Blender / GitHub Releases.
rem Run from the repo root:  devtools\createzip.bat

rem Always operate relative to the repo root, regardless of CWD
cd /d "%~dp0.."

set OUTPUT=orbiter-blender-2.zip
set STAGEDIR=orbiter-blender-2

if exist "%OUTPUT%" del "%OUTPUT%"
if exist "%STAGEDIR%" rd /s /q "%STAGEDIR%"

mkdir "%STAGEDIR%"
copy blender_manifest.toml "%STAGEDIR%\" > nul
copy __init__.py            "%STAGEDIR%\" > nul
copy orbiter_tools.py       "%STAGEDIR%\" > nul
copy import_tools.py        "%STAGEDIR%\" > nul
copy LICENSE                "%STAGEDIR%\" > nul

powershell -NoProfile -Command ^
  "Compress-Archive -Path '%STAGEDIR%' -DestinationPath '%OUTPUT%'"

rd /s /q "%STAGEDIR%"

if %errorlevel% neq 0 (
    echo ERROR: Failed to create %OUTPUT%
    exit /b 1
)

echo Created %OUTPUT%
