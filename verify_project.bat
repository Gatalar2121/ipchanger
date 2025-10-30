@echo off
echo ====================================================
echo Network IP Changer - Pre-GitHub Verification
echo ====================================================
echo.

echo Checking Git repository status...
git status --porcelain
if errorlevel 1 (
    echo ERROR: Git repository not properly initialized
    pause
    exit /b 1
)

echo.
echo Checking Python syntax...
python -m py_compile ipchanger.py
if errorlevel 1 (
    echo ERROR: Python syntax errors found
    pause
    exit /b 1
)

echo.
echo Checking requirements file...
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found
    pause
    exit /b 1
)

echo.
echo Checking translation files...
if not exist "i18n\en.json" (
    echo ERROR: English translation file not found
    pause
    exit /b 1
)

echo.
echo Verifying PyInstaller spec file...
if not exist "NetworkIPChanger.spec" (
    echo ERROR: PyInstaller spec file not found
    pause
    exit /b 1
)

echo.
echo Testing setup script...
echo This would run: setup.bat
echo (Skipping actual execution to avoid installing dependencies)

echo.
echo ====================================================
echo ✅ All verification checks passed!
echo ====================================================
echo.
echo Your project is ready for GitHub! Next steps:
echo.
echo 1. Create a new repository on GitHub named 'ipchanger'
echo 2. Don't initialize with README (you already have one)
echo 3. Copy the remote URL from GitHub
echo 4. Run: git remote add origin [YOUR_GITHUB_URL]
echo 5. Run: git push -u origin main
echo.
echo Example GitHub URL format:
echo https://github.com/Gatalar2121/ipchanger.git
echo.
pause