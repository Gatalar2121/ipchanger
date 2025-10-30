@echo off
setlocal enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════════════════════════════════════════╗
echo ║                  Network IP Changer v2.0.0 - Build Script                  ║
echo ╚══════════════════════════════════════════════════════════════════════════════╝
echo.

:: Check Python installation
python --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ Python not found. Please install Python 3.8 or higher.
    exit /b 1
)

echo ✅ Python found: 
python --version

:: Check PyInstaller
pip show pyinstaller >nul 2>&1
if !errorlevel! neq 0 (
    echo 📦 Installing PyInstaller...
    pip install pyinstaller
)

:: Check PySide6
pip show PySide6 >nul 2>&1
if !errorlevel! neq 0 (
    echo 📦 Installing PySide6...
    pip install PySide6
)

:: Create build directory
if not exist "build" mkdir build
if not exist "dist" mkdir dist

echo.
echo 🏗️  Building Network IP Changer v2.0.0...

:: Enhanced build with all features
echo Building enhanced version...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name="NetworkIPChanger_v2.0.0" ^
    --icon="ip.ico" ^
    --add-data="i18n;i18n" ^
    --add-data="*.json;." ^
    --collect-submodules=PySide6 ^
    --collect-all=PySide6 ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=ipchanger ^
    --hidden-import=ipchanger_enhanced ^
    --hidden-import=enhanced_gui ^
    --hidden-import=advanced_networking ^
    ipchanger_v2.py

if !errorlevel! neq 0 (
    echo ❌ Enhanced build failed!
    exit /b 1
)

:: Console version for CLI usage
echo Building CLI version...
pyinstaller ^
    --onefile ^
    --console ^
    --name="NetworkIPChanger_CLI_v2.0.0" ^
    --add-data="i18n;i18n" ^
    --add-data="*.json;." ^
    --hidden-import=ipchanger_enhanced ^
    --hidden-import=advanced_networking ^
    ipchanger_v2.py

if !errorlevel! neq 0 (
    echo ❌ CLI build failed!
    exit /b 1
)

:: Build original v1.0.0 compatible version
echo Building v1.0.0 compatible version...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name="NetworkIPChanger_v1_compatible" ^
    --icon="ip.ico" ^
    --add-data="i18n;i18n" ^
    --add-data="*.json;." ^
    --collect-submodules=PySide6 ^
    --collect-all=PySide6 ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtWidgets ^
    --hidden-import=PySide6.QtGui ^
    ipchanger.py

if !errorlevel! neq 0 (
    echo ❌ v1.0.0 compatible build failed!
    exit /b 1
)

echo.
echo ✅ Build complete! Created executables:

:: Check file sizes and display results
if exist "dist\NetworkIPChanger_v2.0.0.exe" (
    for %%I in ("dist\NetworkIPChanger_v2.0.0.exe") do (
        echo   📱 NetworkIPChanger_v2.0.0.exe - %%~zI bytes ^(Enhanced GUI + CLI^)
    )
)

if exist "dist\NetworkIPChanger_CLI_v2.0.0.exe" (
    for %%I in ("dist\NetworkIPChanger_CLI_v2.0.0.exe") do (
        echo   💻 NetworkIPChanger_CLI_v2.0.0.exe - %%~zI bytes ^(CLI Only^)
    )
)

if exist "dist\NetworkIPChanger_v1_compatible.exe" (
    for %%I in ("dist\NetworkIPChanger_v1_compatible.exe") do (
        echo   🔧 NetworkIPChanger_v1_compatible.exe - %%~zI bytes ^(v1.0.0 Compatible^)
    )
)

echo.
echo 📋 Build Summary:
echo   • Enhanced v2.0.0 with all features: GUI + CLI + VPN + Monitoring
echo   • CLI-only version for server/automation use
echo   • v1.0.0 compatible version for users who prefer the original interface
echo.
echo 📝 Usage:
echo   NetworkIPChanger_v2.0.0.exe                    # Enhanced GUI (default)
echo   NetworkIPChanger_v2.0.0.exe --cli             # Interactive CLI
echo   NetworkIPChanger_CLI_v2.0.0.exe               # Direct CLI access
echo   NetworkIPChanger_CLI_v2.0.0.exe list-adapters # Quick commands
echo.
echo ✅ All builds completed successfully!

pause