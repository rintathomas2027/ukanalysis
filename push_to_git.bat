@echo off
title Push UK Top 50 Project to GitHub - rintathomas2027/ukanalysis
echo ======================================================================
echo Synchronizing UK Top 50 Analytics Project to GitHub...
echo Repository: https://github.com/rintathomas2027/ukanalysis.git
echo ======================================================================
echo.

cd /d "%~dp0"

echo 1. Checking Git repository status...
if not exist ".git" (
    echo Initializing new Git repository...
    git init
    git branch -M main
)

echo 2. Configuring remote origin...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/rintathomas2027/ukanalysis.git

echo 3. Staging all project deliverables...
git add .

echo 4. Committing changes...
git commit -m "feat: complete UK Top 50 playlist market structure, artist diversity & content localization analysis suite"

echo 5. Pushing to GitHub (main branch)...
git push -u origin main

echo.
echo ======================================================================
echo Git push completed! Check: https://github.com/rintathomas2027/ukanalysis
echo ======================================================================
pause
