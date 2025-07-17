@echo off
echo 🎬 Starting GleamVideo Studio Enhanced (Windows)
echo =============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip not found. Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo ✅ pip found
echo.

REM Install dependencies
echo 📦 Installing/checking dependencies...
pip install fastapi uvicorn python-multipart aiohttp opencv-python-headless pillow pytz selenium pydantic requests beautifulsoup4 feedparser openai webdriver-manager

if %errorlevel% neq 0 (
    echo ⚠️ Some packages may have failed to install. Continuing anyway...
)
echo.

REM Create required directories
echo 📁 Creating directories...
if not exist "videos" mkdir videos
if not exist "screenshots" mkdir screenshots
if not exist "temp" mkdir temp
echo ✅ Directories created
echo.

REM Check for existing process
echo 🔍 Checking for existing application...
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *gleamvideo*" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️ GleamVideo may already be running. Please close any existing instances.
    echo Press any key to continue anyway...
    pause >nul
)

REM Start the application
echo 🚀 Starting GleamVideo Studio Enhanced...
echo.
echo ⏳ Please wait for the application to start...
echo.

start /B python gleamvideo.py

REM Wait for startup
timeout /t 5 /nobreak >nul

REM Check if application is responding
curl -s http://localhost:8000/progress >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Application started successfully!
    echo.
    echo 🎉 GleamVideo Studio Enhanced is now running!
    echo.
    echo 📱 Web Interface: http://localhost:8000
    echo.
    echo 📋 Quick Start Guide:
    echo   1. Open http://localhost:8000 in your browser
    echo   2. Configure your OpenRouter API key for Gemini 2.5 Flash
    echo   3. Set up Auto Mode with your preferred subreddit
    echo   4. Start generating amazing videos!
    echo.
    echo 🛑 To stop: Close this window or press Ctrl+C
    echo.
    echo Opening web interface in your default browser...
    start http://localhost:8000
    echo.
    echo Press any key to exit this setup window...
    pause >nul
) else (
    echo ❌ Failed to start the application. 
    echo Please check for error messages above and ensure all dependencies are installed.
    echo.
    echo Common solutions:
    echo - Install Firefox browser
    echo - Install FFmpeg from https://ffmpeg.org/download.html
    echo - Run as Administrator if needed
    echo.
    pause
)