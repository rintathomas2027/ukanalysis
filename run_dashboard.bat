@echo off
title BritSound Intelligence - UK Top 50 Spotify Analytics Dashboard
echo ======================================================================
echo Launching BritSound Intelligence: UK Top 50 Analytics Dashboard...
echo Atlantic Recording Corporation / Unified Mentor Internship Project
echo ======================================================================
echo.

cd /d "%~dp0"

echo Checking and installing required dependencies...
pip install -r requirements.txt

echo.
echo Starting Streamlit Application on http://localhost:8501 ...
streamlit run app.py

pause
