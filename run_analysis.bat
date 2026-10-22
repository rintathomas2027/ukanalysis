@echo off
title UK Top 50 Data Preparation & Cleaning Pipeline
echo ======================================================================
echo Running UK Top 50 Data Extraction, Cleaning, and Feature Engineering...
echo ======================================================================
echo.

cd /d "%~dp0"

echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Executing prepare_data.py...
python prepare_data.py

echo.
echo ======================================================================
echo Data pipeline completed successfully!
echo Raw and Cleaned datasets ready in ./data/
echo ======================================================================
pause
