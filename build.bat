@echo off
setlocal

echo Building NoorMarket executable...
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON=%~dp0.venv\Scripts\python.exe"
    "%PYTHON%" -m pyinstaller --version >nul 2>&1
    if errorlevel 1 (
        echo PyInstaller not found in .venv; falling back to system python.
        set "PYTHON=python"
    )
) else (
    set "PYTHON=python"
)
%PYTHON% -m PyInstaller --clean build.spec
if errorlevel 1 (
    echo.
    echo Build failed.
    pause
    exit /b 1
)
echo.
echo Build complete. See dist\NoorMarket\NoorMarket.exe
echo Note: This is a one-folder build. Distribute the full dist\NoorMarket folder, not just the NoorMarket.exe file.
pause
