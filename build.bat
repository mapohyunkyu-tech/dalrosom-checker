@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
  set "PY=py"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo Python was not found.
    echo Use the GitHub Actions method in README.txt to build without Python on this PC.
    pause
    exit /b 1
  )
  set "PY=python"
)

%PY% -m venv .buildvenv
call .buildvenv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements-build.txt
pyinstaller --noconfirm --clean MarketScout.spec

if exist "release" rmdir /s /q "release"
mkdir release
xcopy /e /i /y "dist\MarketScout" "release\MarketScout"
powershell -NoProfile -Command "Compress-Archive -Path 'release\MarketScout\*' -DestinationPath 'release\MarketScout_Windows.zip' -Force"

echo.
echo Build complete:
echo release\MarketScout_Windows.zip
pause
