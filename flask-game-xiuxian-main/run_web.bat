@echo off
REM Script chạy Flask Web App trên Windows

echo ══════════════════════════════════════════════════
echo    Tu Tiên Ký - Flask Web Application
echo ══════════════════════════════════════════════════

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python không được cài đặt!
    pause
    exit /b 1
)

echo ✓ Python đã được cài đặt

REM Install dependencies
echo.
echo Đang cài đặt dependencies...
pip install -r requirements.txt

REM Set environment
set FLASK_APP=flask_app.py
set FLASK_ENV=development
set FLASK_DEBUG=1

REM Run Flask app
echo.
echo ══════════════════════════════════════════════════
echo    Khởi động Flask server...
echo    Mở trình duyệt: http://localhost:5000
echo ══════════════════════════════════════════════════
echo.

python flask_app.py
