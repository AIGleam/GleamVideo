# 🌍 Cross-Platform Compatibility Guide
## GleamVideo Studio Enhanced

### ✅ **YES, it works on Windows, Ubuntu, and macOS!**

The enhanced GleamVideo application has been designed with cross-platform compatibility in mind. Here's how to run it on each operating system:

## 🪟 **Windows Support**

### **Requirements**
- **Python 3.8+** (Download from [python.org](https://python.org))
- **Firefox Browser** (Download from [mozilla.org](https://mozilla.org))
- **FFmpeg** (Download from [ffmpeg.org](https://ffmpeg.org) or use `choco install ffmpeg`)

### **Installation Options**

#### **Option 1: Double-click Setup (Easiest)**
```batch
# Simply double-click:
start_gleamvideo.bat
```

#### **Option 2: Universal Launcher**
```batch
python launch.py
```

#### **Option 3: Manual**
```batch
pip install -r requirements.txt
python gleamvideo.py
```

### **Windows-Specific Features**
- ✅ **Automatic dependency checking**
- ✅ **Browser detection and guidance**
- ✅ **Windows-style progress indicators**
- ✅ **Automatic browser opening**
- ✅ **Background process management**

---

## 🐧 **Ubuntu/Linux Support**

### **Requirements**
- **Python 3.8+** (`sudo apt install python3 python3-pip`)
- **Firefox** (`sudo apt install firefox`)
- **FFmpeg** (`sudo apt install ffmpeg`)
- **Xvfb** for headless operation (`sudo apt install xvfb`)

### **Installation Options**

#### **Option 1: Automated Setup (Recommended)**
```bash
chmod +x start_gleamvideo.sh
./start_gleamvideo.sh
```

#### **Option 2: Universal Launcher**
```bash
python3 launch.py
```

#### **Option 3: Manual**
```bash
pip install -r requirements.txt
python3 gleamvideo.py
```

### **Linux-Specific Features**
- ✅ **Virtual display (Xvfb) support for headless operation**
- ✅ **Proper signal handling**
- ✅ **Service-style background operation**
- ✅ **Package manager integration**
- ✅ **Permission management**

---

## 🍎 **macOS Support**

### **Requirements**
- **Python 3.8+** (`brew install python`)
- **Firefox** (`brew install firefox` or download from mozilla.org)
- **FFmpeg** (`brew install ffmpeg`)

### **Installation Options**

#### **Option 1: Universal Launcher (Recommended)**
```bash
python3 launch.py
```

#### **Option 2: Homebrew + Manual**
```bash
# Install dependencies
brew install python firefox ffmpeg

# Install Python packages
pip3 install -r requirements.txt

# Run application
python3 gleamvideo.py
```

### **macOS-Specific Features**
- ✅ **Homebrew integration support**
- ✅ **macOS-style notifications**
- ✅ **Native browser opening**
- ✅ **Unix-style process management**

---

## 🔄 **Universal Features (All Platforms)**

### **Core Functionality**
- ✅ **Modern Web Interface** - Browser-based, works everywhere
- ✅ **FastAPI Backend** - Pure Python, cross-platform
- ✅ **OpenRouter API Integration** - Cloud-based, platform independent
- ✅ **Reddit RSS Processing** - Network-based, universal
- ✅ **Video Generation** - Uses cross-platform libraries

### **Smart Detection**
The launcher automatically detects:
- **Operating System** (Windows/Linux/macOS)
- **Python version** and availability
- **Required packages** and installs missing ones
- **Browser availability** (Firefox recommended)
- **System capabilities** (virtual display, etc.)

---

## 🛠️ **Platform-Specific Installation Tips**

### **Windows**
- Install Python from [python.org](https://python.org) (make sure to check "Add to PATH")
- Install Firefox from [mozilla.org](https://mozilla.org)
- For FFmpeg: Download from [ffmpeg.org](https://ffmpeg.org) or use Chocolatey: `choco install ffmpeg`
- Run Command Prompt as Administrator if you encounter permission issues

### **Ubuntu/Linux**
```bash
# One-line setup for Ubuntu:
sudo apt update && sudo apt install -y python3 python3-pip firefox ffmpeg xvfb
```

### **macOS**
```bash
# One-line setup with Homebrew:
brew install python firefox ffmpeg
```

---

## 🌐 **Web Interface Compatibility**

The web interface works on **any modern browser** on any platform:
- ✅ **Chrome/Chromium** (Windows, Linux, macOS)
- ✅ **Firefox** (Windows, Linux, macOS) - Recommended
- ✅ **Safari** (macOS)
- ✅ **Edge** (Windows)
- ✅ **Mobile browsers** (responsive design)

---

## 📱 **Mobile/Tablet Access**

The web interface is **fully responsive** and works on:
- ✅ **iOS Safari** (iPhone/iPad)
- ✅ **Android Chrome**
- ✅ **Tablet browsers**
- ✅ **Any device with a modern browser**

Simply access `http://[computer-ip]:8000` from your mobile device when connected to the same network.

---

## 🚀 **Performance Considerations**

### **Minimum Requirements (All Platforms)**
- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4GB (8GB+ recommended)
- **Storage**: 2GB free space
- **Network**: Stable internet for API calls

### **Recommended Setup**
- **CPU**: 4+ cores with good single-thread performance
- **RAM**: 8GB+ for smooth video processing
- **Storage**: SSD for faster file operations
- **Network**: Reliable broadband for RSS feeds and API calls

---

## 🎯 **Summary**

**✅ Full cross-platform compatibility achieved!**

| Feature | Windows | Linux | macOS |
|---------|---------|-------|-------|
| **Core App** | ✅ | ✅ | ✅ |
| **Modern UI** | ✅ | ✅ | ✅ |
| **Auto Mode** | ✅ | ✅ | ✅ |
| **AI Integration** | ✅ | ✅ | ✅ |
| **Video Generation** | ✅ | ✅ | ✅ |
| **Background Operation** | ✅ | ✅ | ✅ |
| **Easy Setup** | ✅ | ✅ | ✅ |

**The application will work seamlessly on Windows, Ubuntu, and macOS with the same great experience!** 🎬✨