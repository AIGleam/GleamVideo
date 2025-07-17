#!/bin/bash

echo "🎬 Starting GleamVideo Studio Enhanced"
echo "======================================"
echo ""

# Function to print colored output
print_status() {
    echo -e "\033[1;32m✅ $1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m⚠️  $1\033[0m"
}

print_error() {
    echo -e "\033[1;31m❌ $1\033[0m"
}

print_info() {
    echo -e "\033[1;36mℹ️  $1\033[0m"
}

# Check Python version
echo "🐍 Checking Python..."
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version | cut -d' ' -f2)
    print_status "Python $python_version found"
else
    print_error "Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check if dependencies are installed
echo ""
echo "📦 Checking dependencies..."
missing_deps=()

python3 -c "import fastapi" 2>/dev/null || missing_deps+=("fastapi")
python3 -c "import uvicorn" 2>/dev/null || missing_deps+=("uvicorn")
python3 -c "import selenium" 2>/dev/null || missing_deps+=("selenium")
python3 -c "import cv2" 2>/dev/null || missing_deps+=("opencv-python-headless")
python3 -c "import openai" 2>/dev/null || missing_deps+=("openai")
python3 -c "import feedparser" 2>/dev/null || missing_deps+=("feedparser")

if [ ${#missing_deps[@]} -gt 0 ]; then
    print_warning "Missing dependencies detected: ${missing_deps[*]}"
    echo "Installing missing packages..."
    pip install --break-system-packages "${missing_deps[@]}"
else
    print_status "All dependencies are installed"
fi

# Check for Firefox
echo ""
echo "🦊 Checking Firefox..."
if command -v firefox &> /dev/null; then
    print_status "Firefox found"
elif command -v firefox-esr &> /dev/null; then
    print_status "Firefox ESR found"
else
    print_warning "Firefox not found. Installing..."
    sudo apt update && sudo apt install -y firefox
fi

# Create required directories
echo ""
echo "📁 Setting up directories..."
mkdir -p videos screenshots temp
print_status "Directories created"

# Check if virtual display is available (for headless operation)
echo ""
echo "🖥️  Setting up virtual display..."
if command -v Xvfb &> /dev/null; then
    # Start virtual display if not already running
    if ! pgrep -f "Xvfb :99" > /dev/null; then
        Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
        export DISPLAY=:99
        print_status "Virtual display started on :99"
    else
        print_status "Virtual display already running"
    fi
else
    print_warning "Xvfb not found. Installing for headless browser support..."
    sudo apt install -y xvfb
    Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
    export DISPLAY=:99
fi

# Check if application is already running
echo ""
echo "🔍 Checking for existing application..."
if pgrep -f "gleamvideo.py" > /dev/null; then
    print_warning "GleamVideo is already running. Stopping existing instance..."
    pkill -f gleamvideo.py
    sleep 2
fi

# Start the application
echo ""
echo "🚀 Starting GleamVideo Studio Enhanced..."
echo ""

# Export display for selenium
export DISPLAY=:99

# Start the application
python3 gleamvideo.py &
APP_PID=$!

# Wait for the application to start
echo "⏳ Waiting for application to start..."
sleep 5

# Check if the application is running
if curl -s http://localhost:8000/progress > /dev/null 2>&1; then
    print_status "Application started successfully!"
    echo ""
    echo "🎉 GleamVideo Studio Enhanced is now running!"
    echo ""
    echo "📱 Web Interface: http://localhost:8000"
    echo "🔧 Process ID: $APP_PID"
    echo ""
    echo "📋 Quick Start Guide:"
    echo "  1. Open http://localhost:8000 in your browser"
    echo "  2. Configure your OpenRouter API key for Gemini 2.5 Flash"
    echo "  3. Set up Auto Mode with your preferred subreddit"
    echo "  4. Start generating amazing videos!"
    echo ""
    echo "🛑 To stop the application: pkill -f gleamvideo.py"
    echo ""
    print_info "Application is running in the background. Check the logs if needed."
else
    print_error "Failed to start the application. Check the logs for errors."
    exit 1
fi