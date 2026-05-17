@echo off
title AI Social Media Agent — Builder
color 0A
echo.
echo  ============================================
echo   AI Social Media Agent — Windows EXE Builder
echo  ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found.
    echo  Download from https://python.org and make sure to tick "Add to PATH"
    pause
    exit /b 1
)

echo  [1/5] Installing dependencies...
pip install streamlit requests pillow apscheduler tweepy pyinstaller --quiet
if errorlevel 1 (
    echo  ERROR: pip install failed.
    pause
    exit /b 1
)

echo  [2/5] Creating app folder...
if not exist "dist\SocialMediaAgent\app" mkdir "dist\SocialMediaAgent\app"
copy /Y "app\social_media_agent.py" "dist\SocialMediaAgent\app\" >nul

echo  [3/5] Building launcher EXE with PyInstaller...
pyinstaller ^
  --noconfirm ^
  --onefile ^
  --windowed ^
  --name "SocialMediaAgent" ^
  --distpath "dist\SocialMediaAgent" ^
  --workpath "build_tmp" ^
  --specpath "build_tmp" ^
  launcher.py

if errorlevel 1 (
    echo  ERROR: PyInstaller build failed.
    pause
    exit /b 1
)

echo  [4/5] Copying app files...
copy /Y "app\social_media_agent.py" "dist\SocialMediaAgent\app\" >nul

echo  [5/5] Creating README...
(
echo AI Social Media Agent
echo =====================
echo.
echo REQUIREMENTS: Python 3.9+ must be installed on the PC.
echo Download free from: https://www.python.org/downloads/
echo Make sure to tick "Add Python to PATH" during install.
echo.
echo HOW TO USE:
echo 1. Double-click SocialMediaAgent.exe
echo 2. A small window appears while it starts
echo 3. Your browser opens automatically
echo 4. Use the app normally in your browser
echo.
echo The app runs LOCALLY on your PC — your data stays private.
echo Close the launcher window to stop the app.
) > "dist\SocialMediaAgent\README.txt"

echo.
echo  ============================================
echo   BUILD COMPLETE!
echo   Your distributable folder is:
echo   dist\SocialMediaAgent\
echo  ============================================
echo.
echo  Share the entire "SocialMediaAgent" folder with your manager.
echo  They just double-click SocialMediaAgent.exe to launch.
echo.
pause
