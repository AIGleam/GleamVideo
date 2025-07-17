#!/bin/bash

echo "🎬 Starting GleamVideo Studio Enhanced..."
echo "==========================================="

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import fastapi, uvicorn, selenium, opencv as cv2, openai, feedparser, webdriver_manager" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install --break-system-packages fastapi uvicorn python-multipart aiohttp opencv-python-headless pillow pytz selenium pydantic requests beautifulsoup4 feedparser openai webdriver-manager
fi

# Create required directories
mkdir -p videos screenshots temp

# Start virtual display for headless browser (optional)
echo "🖥️  Starting virtual display..."
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
export DISPLAY=:99

# Start the application
echo "🚀 Starting application on http://localhost:8000"
echo ""
echo "Features available:"
echo "  ✨ Modern Dark UI with Tailwind CSS"
echo "  🤖 Gemini 2.5 Flash AI Integration via OpenRouter"
echo "  🔄 Auto Mode with Reddit RSS feeds"
echo "  📱 Responsive design"
echo "  🎥 Enhanced video generation with Ken Burns effect"
echo ""
echo "Access the application at: http://localhost:8000"
echo "Press Ctrl+C to stop the server"
echo ""

python3 gleamvideo.py