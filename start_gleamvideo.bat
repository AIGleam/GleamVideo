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

REM Check for FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ FFmpeg not found. Video generation may not work properly.
    echo Please install FFmpeg from https://ffmpeg.org/download.html
    echo and add it to your PATH.
    echo.
    echo Press any key to continue anyway...
    pause >nul
) else (
    echo ✅ FFmpeg found
)
echo.

REM Install dependencies
echo 📦 Installing/checking dependencies...
pip install --upgrade fastapi uvicorn[standard] python-multipart aiohttp aiofiles opencv-python-headless pillow pytz selenium pydantic requests beautifulsoup4 feedparser openai webdriver-manager numpy soundfile

if %errorlevel% neq 0 (
    echo ⚠️ Some packages may have failed to install. Trying with --user flag...
    pip install --user --upgrade fastapi uvicorn[standard] python-multipart aiohttp aiofiles opencv-python-headless pillow pytz selenium pydantic requests beautifulsoup4 feedparser openai webdriver-manager numpy soundfile
)

REM Try to install optional TTS support
echo 📦 Installing optional TTS support...
pip install kokoro-onnx >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Kokoro TTS not available. TTS features will use fallback mode.
)
echo.

REM Create required directories
echo 📁 Creating directories...
if not exist "videos" mkdir videos
if not exist "screenshots" mkdir screenshots
if not exist "temp" mkdir temp
echo ✅ Directories created
echo.

REM Check for Firefox browser
echo 🦊 Checking for Firefox browser...
if exist "C:\Program Files\Mozilla Firefox\firefox.exe" (
    echo ✅ Firefox found
) else if exist "C:\Program Files (x86)\Mozilla Firefox\firefox.exe" (
    echo ✅ Firefox found
) else (
    echo ⚠️ Firefox not found. Please install Firefox for best screenshot compatibility.
    echo Download from: https://firefox.com
    echo Press any key to continue...
    pause >nul
)
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
timeout /t 8 /nobreak >nul

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
    echo   3. Set up Auto Mode with your preferred settings
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
    echo.
    echo 🔧 Troubleshooting checklist:
    echo   ✓ Python 3.8+ installed
    echo   ✓ All dependencies installed
    echo   ✓ FFmpeg available in PATH
    echo   ✓ Firefox browser installed
    echo   ✓ Port 8000 is available
    echo   ✓ Run as Administrator if needed
    echo.
    echo 📝 Common solutions:
    echo   - Restart your command prompt as Administrator
    echo   - Install Visual Studio Build Tools if using conda
    echo   - Check Windows Defender/Antivirus settings
    echo   - Ensure no other applications are using port 8000
    echo.
    echo 📋 Manual start command:
    echo   python gleamvideo.py
    echo.
    pause
)