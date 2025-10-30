@echo off
echo ====================================================
echo Network IP Changer - Setup Script
echo ====================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or later from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python installation found.
echo.

:: Check Python version
echo Checking Python version...
python -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.7 or later is required
    echo Please update your Python installation
    pause
    exit /b 1
)

echo Python version is compatible.
echo.

:: Install pip if not available
echo Checking pip installation...
pip --version >nul 2>&1
if errorlevel 1 (
    echo Installing pip...
    python -m ensurepip --upgrade
    if errorlevel 1 (
        echo ERROR: Failed to install pip
        pause
        exit /b 1
    )
)

echo Pip is available.
echo.

:: Upgrade pip to latest version
echo Upgrading pip to latest version...
python -m pip install --upgrade pip

:: Install requirements
echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Please check your internet connection and try again
    pause
    exit /b 1
)

echo.
echo ====================================================
echo Setup completed successfully!
echo ====================================================
echo.
echo You can now run the application with:
echo   python ipchanger.py
echo.
echo To build an executable:
echo   pip install pyinstaller
echo   pyinstaller NetworkIPChanger.spec
echo.
echo IMPORTANT: The application requires administrator privileges
echo to modify network settings. Right-click and "Run as administrator"
echo.
pause