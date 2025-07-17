# 🎬 GleamVideo Studio Enhanced

**A Modern AI-Powered Video Generation Platform**

![Version](https://img.shields.io/badge/version-2.0-blue)
![Python](https://img.shields.io/badge/python-3.13+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

## ✨ New Features

### 🎨 Modern Dark UI
- **Tailwind CSS** powered interface with responsive design
- Beautiful gradient backgrounds and glass effects
- Icon-rich interface with Font Awesome integration
- Real-time progress tracking with animated progress bars
- Toast notifications for user feedback

### 🤖 AI Integration
- **Gemini 2.5 Flash** integration through OpenRouter API
- Intelligent content generation from Reddit RSS feeds
- Automated script writing and video ideas
- Smart screenshot timing suggestions

### 🔄 Auto Mode
- **Automated workflow** that monitors Reddit RSS feeds
- Background Firefox instances for website screenshots
- AI-powered content analysis and video script generation
- Scheduled video production with customizable intervals
- Support for multiple subreddit sources

### 📱 Enhanced UX
- **Real-time status updates** with WebSocket-like polling
- Video library with download management
- API key management with secure storage
- System information dashboard
- Responsive design for all screen sizes

## 🚀 Quick Start

### 1. Installation
```bash
# Clone or download the application
cd gleamvideo-studio

# Run the enhanced setup script
./run.sh
```

### 2. Access the Application
Open your browser and navigate to:
```
http://localhost:8000
```

### 3. Configure API Key
1. Get your OpenRouter API key from [OpenRouter.ai](https://openrouter.ai)
2. Click the API Configuration section
3. Enter your API key and save

### 4. Start Creating
- **Manual Mode**: Create videos by entering content and URLs
- **Auto Mode**: Enable automated video generation from Reddit feeds

## 🎯 Core Features

### Manual Video Generation
- **Script Editor**: Write your video content paragraph by paragraph
- **Background Sources**: Add website URLs for automatic screenshots
- **Video Settings**: Choose resolution, transition duration, and output format
- **Ken Burns Effect**: Automatic pan and zoom effects on static images

### Auto Mode Capabilities
- **Reddit RSS Monitoring**: Automatically fetches trending content
- **AI Content Analysis**: Uses Gemini 2.5 Flash to analyze and create scripts
- **Screenshot Automation**: Background Firefox captures relevant website screenshots
- **Intelligent Timing**: AI suggests optimal screenshot insertion points
- **Scheduled Generation**: Set intervals for automatic video production

### Video Output
- **Multiple Resolutions**: HD (1280x720), Full HD (1920x1080), 4K (3840x2160)
- **Ken Burns Effects**: Professional pan/zoom animations
- **Transition Control**: Customizable transition durations
- **MP4 Output**: Universal compatibility

## 🔧 Configuration

### Environment Variables
```bash
export OPENROUTER_API_KEY="your_api_key_here"
export DISPLAY=:99  # For headless browser operation
```

### Auto Mode Settings
- **Interval**: 5-1440 minutes between generations
- **Subreddit**: Target subreddit for content (default: technology)
- **AI Model**: Gemini 2.5 Flash through OpenRouter

## 📦 Dependencies

### Python Packages
- **FastAPI**: Modern web framework
- **Uvicorn**: ASGI server
- **Selenium**: Browser automation
- **OpenCV**: Video processing
- **Pillow**: Image manipulation
- **OpenAI**: API client for LLM integration
- **Feedparser**: RSS feed processing
- **BeautifulSoup4**: Web scraping
- **Webdriver Manager**: Automatic driver management

### System Requirements
- **Python 3.13+**
- **Firefox browser**
- **Xvfb** (for headless operation)
- **FFmpeg** (for video processing)

## 🎥 How It Works

### Manual Generation Flow
1. **Content Input**: User enters script paragraphs and website URLs
2. **Screenshot Capture**: Selenium captures website screenshots
3. **Ken Burns Processing**: OpenCV applies pan/zoom effects
4. **Video Assembly**: FFmpeg combines images with transitions
5. **Output Delivery**: MP4 file ready for download

### Auto Mode Flow
1. **RSS Monitoring**: Fetches latest posts from specified subreddit
2. **Content Analysis**: Gemini 2.5 Flash analyzes post content
3. **Script Generation**: AI creates video narrative and timing
4. **Screenshot Automation**: Background browser captures relevant sites
5. **Video Production**: Automatic assembly and processing
6. **Result Delivery**: Completed video added to library

## 🛠️ API Endpoints

### Core Endpoints
- `GET /` - Modern UI interface
- `POST /api/generate-video` - Manual video generation
- `GET /api/progress` - Real-time progress tracking
- `GET /api/videos/list` - Video library
- `GET /api/videos/download/{filename}` - Video download

### Auto Mode Endpoints
- `POST /api/auto-mode/start` - Start automated generation
- `POST /api/auto-mode/stop` - Stop automated generation
- `POST /api/auto-mode/run-now` - Trigger immediate generation
- `POST /api/config/api-key` - Configure OpenRouter API key

## 🎨 UI Components

### Dashboard Layout
- **Left Panel**: Configuration and generation controls
- **Right Panel**: Status monitoring and video library
- **Header**: Branding and feature indicators
- **Toast System**: Real-time notifications

### Key Components
- **API Configuration Card**: Secure key management
- **Auto Mode Panel**: Automation controls and settings
- **Manual Generation Form**: Content input and video settings
- **Status Monitor**: Real-time progress and system info
- **Video Library**: Generated content management

## 🔐 Security Features

- **API Key Encryption**: Secure storage of sensitive credentials
- **Input Validation**: Protection against malicious content
- **CORS Configuration**: Secure cross-origin requests
- **Rate Limiting**: Protection against API abuse

## 🌟 Advanced Features

### Ken Burns Video Engine
- **Dynamic Zoom**: Intelligent focus on image content
- **Smooth Panning**: Professional camera movement simulation
- **Transition Blending**: Seamless segment connections
- **Resolution Scaling**: Automatic quality optimization

### AI-Powered Analysis
- **Content Extraction**: Intelligent text and image analysis
- **Script Optimization**: Professional narrative structure
- **Timing Calculation**: Optimal pacing for engagement
- **Visual Enhancement**: Smart screenshot selection

## 📱 Browser Compatibility

- ✅ **Chrome/Chromium 90+**
- ✅ **Firefox 88+**
- ✅ **Safari 14+**
- ✅ **Edge 90+**

## 🐛 Troubleshooting

### Common Issues
1. **API Key Issues**: Ensure OpenRouter account has sufficient credits
2. **Browser Driver**: Webdriver-manager handles automatic updates
3. **Display Issues**: Xvfb required for headless operation
4. **Permission Errors**: Ensure write access to videos directory

### Debug Mode
```bash
# Run with detailed logging
python3 gleamvideo.py --debug
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Tailwind CSS** for the beautiful UI framework
- **Font Awesome** for the comprehensive icon library
- **OpenRouter** for providing access to Gemini 2.5 Flash
- **FastAPI** for the excellent web framework
- **Selenium** for robust browser automation

## 📞 Support

For issues and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

**Made with ❤️ for content creators and video enthusiasts**

