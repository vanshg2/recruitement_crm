@echo off
title BLACKWOODS CRM
echo Starting BLACKWOODS CRM...
cd /d "%~dp0"
call venv\Scripts\activate.bat
net start MySQL80
timeout /t 3
start http://localhost:8501
streamlit run app.py