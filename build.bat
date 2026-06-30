@echo off
title Building NoorMarket...
color 0A

:: Change to the directory where this batch file is located
cd /d "%~dp0"

echo ======================================
echo      NoorMarket Build Script
echo ======================================
echo.

echo [1/7] Checking Python...

python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo ERROR: Python is not installed or not in PATH!
    pause
    exit /b
)

echo.
echo [2/7] Checking virtual environment...

if not exist ".venv\Scripts\activate.bat" (
    echo Virtual environment not found. Creating .venv...
    python -m venv .venv

    if errorlevel 1 (
        color 0C
        echo ERROR: Failed to create virtual environment!
        pause
        exit /b
    )
) else (
    echo Virtual environment found. Skipping creation.
)

echo.
echo [3/7] Activating virtual environment...

call ".venv\Scripts\activate.bat"

if errorlevel 1 (
    color 0C
    echo ERROR: Failed to activate virtual environment!
    pause
    exit /b
)

echo.
echo [4/7] Installing requirements.txt...

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if errorlevel 1 (
    color 0C
    echo ERROR: Failed to install requirements!
    pause
    exit /b
)

echo.
echo [5/7] Checking PyInstaller...

python -m pip show pyinstaller >nul 2>&1

if errorlevel 1 (
    echo PyInstaller is not installed.
    echo Installing PyInstaller...
    python -m pip install --upgrade pyinstaller

    if errorlevel 1 (
        color 0C
        echo ERROR: Failed to install PyInstaller!
        pause
        exit /b
    )
)

echo.
echo [6/7] Cleaning old build files...

if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist __pycache__ rmdir /s /q __pycache__
if exist ui\__pycache__ rmdir /s /q ui\__pycache__

echo.
echo [7/7] Building EXE from build.spec...
echo.

python -m PyInstaller --noconfirm --clean build.spec

if errorlevel 1 (
    echo.
    color 0C
    echo ========================================
    echo              BUILD FAILED
    echo ========================================
    echo Please check the error message above.
    pause
    exit /b
)

echo.
echo ========================================
echo      BUILD COMPLETED SUCCESSFULLY
echo ========================================
echo.
echo EXE Location:
echo dist\NoorMarket\NoorMarket.exe
echo.
echo Note: This is a one-folder build. Distribute the full
echo dist\NoorMarket folder, not just the NoorMarket.exe file.
echo.

pause
