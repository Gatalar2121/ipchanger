@echo off
echo ====================================================
echo Network IP Changer - Fixed Build Script
echo ====================================================
echo.

set PYTHON_EXE=C:/Users/PyxSara/AppData/Local/Programs/Python/Python313/python.exe

:: Test PySide6 availability
echo Testing PySide6 in correct Python environment...
%PYTHON_EXE% -c "import PySide6.QtCore; print('PySide6 OK')"
if errorlevel 1 (
    echo ERROR: PySide6 not available in Python 3.13
    pause
    exit /b 1
)

:: Clean previous build
echo Cleaning previous build files...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

:: Build using the correct Python
echo.
echo Building executable with correct Python environment...
echo Using: %PYTHON_EXE%
echo.

%PYTHON_EXE% -m PyInstaller --clean ^
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
    --hidden-import=PySide6.QtWidgets.QApplication ^
    --hidden-import=PySide6.QtWidgets.QWidget ^
    --hidden-import=PySide6.QtWidgets.QMainWindow ^
    --hidden-import=PySide6.QtWidgets.QVBoxLayout ^
    --hidden-import=PySide6.QtWidgets.QHBoxLayout ^
    --hidden-import=PySide6.QtWidgets.QLabel ^
    --hidden-import=PySide6.QtWidgets.QPushButton ^
    --hidden-import=PySide6.QtWidgets.QComboBox ^
    --hidden-import=PySide6.QtWidgets.QLineEdit ^
    --hidden-import=PySide6.QtWidgets.QTextEdit ^
    --hidden-import=PySide6.QtWidgets.QMessageBox ^
    --hidden-import=PySide6.QtWidgets.QFileDialog ^
    --hidden-import=PySide6.QtWidgets.QGroupBox ^
    --hidden-import=PySide6.QtWidgets.QRadioButton ^
    --hidden-import=PySide6.QtWidgets.QButtonGroup ^
    --hidden-import=PySide6.QtWidgets.QFormLayout ^
    --hidden-import=PySide6.QtWidgets.QListWidget ^
    --hidden-import=PySide6.QtWidgets.QListWidgetItem ^
    --hidden-import=PySide6.QtWidgets.QInputDialog ^
    --hidden-import=PySide6.QtWidgets.QSizePolicy ^
    --hidden-import=PySide6.QtWidgets.QSpacerItem ^
    --hidden-import=shiboken6 ^
    --collect-submodules=PySide6 ^
    --noupx ^
    ipchanger.py

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

:: Check results
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
echo This executable should now work without PySide6 errors!
echo.
echo To test:
echo 1. Copy dist\NetworkIPChanger.exe to another computer (without Python)
echo 2. Right-click and "Run as administrator"
echo 3. Application should start normally
echo.
pause