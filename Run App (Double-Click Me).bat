@echo off
title AI Social Media Agent
color 0A
echo.
echo  Starting AI Social Media Agent...
echo  Your browser will open automatically.
echo  Keep this window open while using the app.
echo.

:: Install deps silently on first run
pip install streamlit requests pillow apscheduler tweepy --quiet 2>nul

:: Launch
cd /d "%~dp0app"
python -m streamlit run social_media_agent.py ^
  --server.headless true ^
  --browser.gatherUsageStats false

pause
