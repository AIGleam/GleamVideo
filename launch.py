#!/usr/bin/env python3
"""
Cross-platform launcher for GleamVideo Studio Enhanced
Works on Windows, macOS, and Linux
"""

import os
import sys
import subprocess
import platform
import time
import webbrowser
from pathlib import Path

def print_colored(text, color="white"):
    """Print colored text (works on all platforms)"""
    colors = {
        "red": "\033[91m",
        "green": "\033[92m", 
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "reset": "\033[0m"
    }
    
    if platform.system() == "Windows":
        # Windows may not support ANSI colors in older versions
        print(f"  {text}")
    else:
        print(f"{colors.get(color, colors['white'])}{text}{colors['reset']}")

def check_python():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_colored("❌ Python 3.8+ required. Current version: {}.{}.{}".format(
            version.major, version.minor, version.micro), "red")
        return False
    
    print_colored(f"✅ Python {version.major}.{version.minor}.{version.micro} found", "green")
    return True

def install_dependencies():
    """Install required Python packages"""
    print_colored("📦 Installing dependencies...", "cyan")
    
    packages = [
        "fastapi", "uvicorn", "python-multipart", "aiohttp",
        "opencv-python-headless", "pillow", "pytz", "selenium", 
        "pydantic", "requests", "beautifulsoup4", "feedparser", 
        "openai", "webdriver-manager"
    ]
    
    try:
        for package in packages:
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         capture_output=True, check=True)
        print_colored("✅ Dependencies installed successfully", "green")
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"⚠️ Some dependencies may have failed to install: {e}", "yellow")
        return True  # Continue anyway

def check_browser():
    """Check if a compatible browser is available"""
    print_colored("🦊 Checking browser availability...", "cyan")
    
    system = platform.system()
    
    if system == "Windows":
        # Check for Firefox or Chrome on Windows
        firefox_paths = [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
        ]
        
        for path in firefox_paths:
            if os.path.exists(path):
                print_colored("✅ Firefox found", "green")
                return True
        
        print_colored("⚠️ Firefox not found. Please install Firefox for best compatibility.", "yellow")
        
    elif system == "Darwin":  # macOS
        try:
            subprocess.run(["which", "firefox"], capture_output=True, check=True)
            print_colored("✅ Firefox found", "green")
            return True
        except subprocess.CalledProcessError:
            print_colored("⚠️ Firefox not found. Install with: brew install firefox", "yellow")
            
    else:  # Linux
        try:
            subprocess.run(["which", "firefox"], capture_output=True, check=True)
            print_colored("✅ Firefox found", "green")
            return True
        except subprocess.CalledProcessError:
            print_colored("⚠️ Firefox not found. Install with: sudo apt install firefox", "yellow")
    
    return True  # Continue even without Firefox

def setup_directories():
    """Create required directories"""
    print_colored("📁 Setting up directories...", "cyan")
    
    directories = ["videos", "screenshots", "temp"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print_colored("✅ Directories created", "green")

def start_application():
    """Start the GleamVideo application"""
    print_colored("🚀 Starting GleamVideo Studio Enhanced...", "cyan")
    
    # Start the application
    if platform.system() == "Windows":
        # On Windows, use subprocess.Popen to start in background
        process = subprocess.Popen([sys.executable, "gleamvideo.py"], 
                                 creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        # On Unix-like systems
        process = subprocess.Popen([sys.executable, "gleamvideo.py"])
    
    # Wait for startup
    print_colored("⏳ Waiting for application to start...", "cyan")
    time.sleep(5)
    
    # Test if application is responding
    try:
        import requests
        response = requests.get("http://localhost:8000/progress", timeout=10)
        if response.status_code == 200:
            print_colored("✅ Application started successfully!", "green")
            return True
    except:
        pass
    
    print_colored("❌ Application may have failed to start", "red")
    return False

def main():
    """Main launcher function"""
    system = platform.system()
    
    print_colored("🎬 GleamVideo Studio Enhanced Launcher", "cyan")
    print_colored("=" * 45, "cyan")
    print_colored(f"Platform: {system}", "white")
    print()
    
    # Check Python version
    if not check_python():
        input("Press Enter to exit...")
        return
    
    # Install dependencies
    install_dependencies()
    
    # Check browser
    check_browser()
    
    # Setup directories
    setup_directories()
    
    # Start application
    if start_application():
        print()
        print_colored("🎉 GleamVideo Studio Enhanced is running!", "green")
        print()
        print_colored("📱 Web Interface: http://localhost:8000", "cyan")
        print()
        print_colored("📋 Quick Start:", "white")
        print_colored("  1. Configure your OpenRouter API key", "white")
        print_colored("  2. Set up Auto Mode with your subreddit", "white")
        print_colored("  3. Start generating videos!", "white")
        print()
        
        # Open browser
        try:
            print_colored("🌐 Opening web interface...", "cyan")
            webbrowser.open("http://localhost:8000")
        except:
            print_colored("Please open http://localhost:8000 manually", "yellow")
        
        print()
        print_colored("🛑 Press Ctrl+C to stop the application", "yellow")
        
        # Keep script running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print_colored("\n👋 Shutting down...", "yellow")
    
    else:
        print()
        print_colored("💡 Troubleshooting tips:", "yellow")
        print_colored("  - Ensure all dependencies are installed", "white")
        print_colored("  - Check if port 8000 is available", "white")
        print_colored("  - Install Firefox browser", "white")
        if system == "Windows":
            print_colored("  - Try running as Administrator", "white")
        
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()