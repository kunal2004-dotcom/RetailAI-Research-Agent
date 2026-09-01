@echo off
echo Starting RetailAI Backend...
start cmd /k "python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"

echo Waiting 5 seconds for backend to start...
timeout /t 5 /nobreak

echo Starting RetailAI Frontend...
set BACKEND_API_URL=http://127.0.0.1:8000
start cmd /k "streamlit run frontend/streamlit_app.py"
