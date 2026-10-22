@echo off
title BritSound Intelligence - Push to GitHub (rintathomas2027/ukanalysis)
echo ======================================================================
echo  BritSound Intelligence - UK Top 50 Analytics
echo  Pushing to: https://github.com/rintathomas2027/ukanalysis.git
echo ======================================================================
echo.

cd /d "%~dp0"

echo [Step 1] Creating Streamlit Cloud config...
if not exist ".streamlit" mkdir .streamlit
(
echo [theme]
echo primaryColor = "#1DB954"
echo backgroundColor = "#121212"
echo secondaryBackgroundColor = "#1E1E1E"
echo textColor = "#FFFFFF"
echo font = "sans serif"
echo.
echo [server]
echo maxUploadSize = 200
echo headless = true
echo.
echo [browser]
echo gatherUsageStats = false
) > .streamlit\config.toml
echo Done.

echo [Step 2] Initializing Git repository...
if not exist ".git" (
    git init
    git branch -M main
)

echo [Step 3] Configuring remote origin...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/rintathomas2027/ukanalysis.git

echo [Step 4] Staging all project files...
git add .

echo [Step 5] Committing...
git commit -m "feat: BritSound Intelligence - UK Top 50 Market Analytics Dashboard (complete)"

echo [Step 6] Pushing to GitHub...
git branch -M main
git push -u origin main

echo.
echo ======================================================================
echo  SUCCESS! Your project is live on GitHub:
echo  https://github.com/rintathomas2027/ukanalysis
echo.
echo  Next: Deploy to Streamlit Cloud at https://share.streamlit.io
echo  Select repo: rintathomas2027/ukanalysis  |  Main file: app.py
echo ======================================================================
pause
