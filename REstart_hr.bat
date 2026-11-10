@echo off

echo Stopping old Python processes...
taskkill /F /IM python.exe

echo Starting FastAPI...
start /B .\.venv\Scripts\uvicorn main:app --reload

echo Waiting for FastAPI to initialize...
timeout /t 3 /nobreak 

echo Starting Streamlit...
start /B .\.venv\Scripts\streamlit run frontend.py

echo HR Hiring System started.

