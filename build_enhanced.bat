@echo off
echo ====================================================
echo Network IP Changer - Enhanced Build Script
echo ====================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Check if PySide6 is installed
echo Checking PySide6 installation...
python -c "import PySide6.QtCore; print('PySide6 found')" 2>nul
if errorlevel 1 (
    echo ERROR: PySide6 is not installed
    echo Installing PySide6...
    pip install PySide6
    if errorlevel 1 (
        echo ERROR: Failed to install PySide6
        pause
        exit /b 1
    )
)

:: Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

:: Clean previous build
echo Cleaning previous build files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

:: Build the executable with verbose output and collect all dependencies
echo.
echo Building executable with enhanced dependency collection...
echo This may take several minutes...
echo.

pyinstaller --clean ^
    --onefile ^
    --windowed ^
    --uac-admin ^
    --icon=ip.ico ^
    --name=NetworkIPChanger ^
    --add-data "i18n;i18n" ^
    --add-data "ip.ico;." ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=shiboken6 ^
    --collect-all=PySide6 ^
    --collect-all=shiboken6 ^
    --noupx ^
    ipchanger.py

if errorlevel 1 (
    echo ERROR: Build failed with PyInstaller command line
    echo Trying with spec file...
    pyinstaller NetworkIPChanger.spec
    if errorlevel 1 (
        echo ERROR: Build failed completely
        pause
        exit /b 1
    )
)

echo.
echo Checking build results...
if not exist "dist\NetworkIPChanger.exe" (
    echo ERROR: Executable was not created
    pause
    exit /b 1
)

:: Get file size
for /f %%i in ('powershell -command "(Get-Item 'dist\NetworkIPChanger.exe').Length"') do set filesize=%%i
set /a filesizeMB=%filesize%/1048576

echo.
echo ====================================================
echo Build completed successfully!
echo ====================================================
echo.
echo Executable: dist\NetworkIPChanger.exe
echo Size: %filesizeMB% MB
echo.
echo Testing basic import (this should show no errors)...
dist\NetworkIPChanger.exe --version 2>nul || echo Note: Version check not implemented, this is normal.

echo.
echo The executable is ready! To test:
echo 1. Right-click dist\NetworkIPChanger.exe
echo 2. Select "Run as administrator"
echo 3. Application should start without PySide6 errors
echo.
pause