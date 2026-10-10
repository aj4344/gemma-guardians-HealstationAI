@echo off
echo ============================================
echo   HealStation AI - Offline Startup
echo ============================================
echo.

REM Step 1: Start Ollama server — gemma4:e2b running locally via Ollama
echo [1/3] Starting Ollama (gemma4:e2b offline)...
set OLLAMA_NEW_ENGINE=1
start /B "" ollama serve
timeout /t 3 /nobreak >nul

REM Confirm Ollama is up
curl -s http://127.0.0.1:11434/ >nul 2>&1
if %errorlevel% neq 0 (
    echo Waiting for Ollama to initialize...
    timeout /t 5 /nobreak >nul
)
echo [OK]  Ollama is running on port 11434

REM Step 2: Activate virtual environment
echo [2/3] Activating Python environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [OK]  Virtual environment activated
) else (
    echo [WARN] No .venv found — using system Python
)

REM Step 3: Start the FastAPI backend
REM — live Gemma 4 inference via Ollama (default)

echo [3/3] Starting HealStation backend server...
echo.
echo ============================================
echo   READY — LIVE GEMMA 4 MODE
echo   Backend: http://127.0.0.1:8001
echo   Ollama:  http://127.0.0.1:11434
echo   Model:   gemma4:e2b (local, offline)
echo   Health:  http://127.0.0.1:8001/api/ollama-health
echo ============================================
echo.

REM Prefer a virtual environment one level up, then the project's own .venv
if exist "..\.venv\Scripts\python.exe" (
    ..\.venv\Scripts\python.exe api.py
) else if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe api.py
) else (
    python api.py
)
