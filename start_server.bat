@echo off
REM Startup script for Windows users
REM Multi-Agent AML Investigation System

echo 🚀 Starting Multi-Agent AML Investigation System...
echo 📡 Server will be available at: http://localhost:8000
echo 📚 API Documentation: http://localhost:8000/docs
echo 🔧 ReDoc Documentation: http://localhost:8000/redoc
echo ============================================================

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
