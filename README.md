# GleamVideo - AI Video Generator

**A tool that automates video creation using AI-generated voiceovers and Ken Burns-style image transitions.**  
🚀 **First version - Still in early development!**

---

## 📌 How to Use Tutorial:
[![How to Use](https://img.youtube.com/vi/IGe9tGyIcH8/0.jpg)](https://www.youtube.com/watch?v=IGe9tGyIcH8)

---

## 📽️ Demo Videos:

### Video 1:
[![Video 1](https://img.youtube.com/vi/t9HFhj7VhuA/0.jpg)](https://www.youtube.com/watch?v=t9HFhj7VhuA)

### Video 2:
[![Video 2](https://img.youtube.com/vi/Vk5TUNNpF4M/0.jpg)](https://www.youtube.com/watch?v=Vk5TUNNpF4M)

---

## 🔥 Features

✅ **Automated Video Generation** - Convert text paragraphs into AI-generated video.  
✅ **Ken Burns Effect** - Smooth pan and zoom on background images or screenshots.  
✅ **Custom AI Voices** - Modify TTS parameters for different styles.  
✅ **Web-Based UI** - Easy-to-use FastAPI-powered interface.  
✅ **Screenshot Integration** - Uses Selenium to grab website screenshots as video backgrounds.  

🚨 **Current Limitations:**  
❌ **Background music is currently broken.**  
❌ **No AI text generation yet**, but you can use external AI tools for scripts.  

---

## 🛠️ Installation & Setup

### **Prerequisites**
- **Python 3.8+**
- **FFmpeg** (for audio/video processing)
- **Selenium & ChromeDriver** (for website screenshots)
- **Required Python Packages** (see `requirements.txt`)
- **Get the Onnx file you need wget https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v0_19.onnx


### **Clone the Repository**
```sh
git clone git@github.com:AIGleam/GleamVideo.git
cd GleamVideo
```

### **Install Dependencies**
```sh
pip install -r requirements.txt
```

### **Run the Application**
```sh
python gleamvideo.py
```
The app will start a web server at:  
🌐 `http://localhost:8000`

---

## 🎬 Usage

1. Open `http://localhost:8000` in your browser.
2. Enter text paragraphs to generate a voiceover.
3. Add background images or URLs for screenshots.
4. *(Optional)* Upload background music (not working yet).
5. Click **Generate Video**.
6. Your final video will be saved in the output folder.

---

## 🎤 Customizing AI Voice

Modify `gleamvideo.py` to change the TTS voice:
```python
DEFAULT_VOICE = "am_adam"
DEFAULT_LANGUAGE = "en-us"
DEFAULT_SPEED = 1.2
```
Change `DEFAULT_VOICE` to other supported voices.

---

## 🛠 Troubleshooting

🔹 **No Video Output?** Ensure FFmpeg is installed.  
🔹 **Voice Sounds Robotic?** Adjust `DEFAULT_SPEED` in TTS settings.  
🔹 **Screenshots Not Working?** Make sure ChromeDriver matches your browser version.  
🔹 **Background Music Not Adding?** This feature is currently broken.  

---

## 🔮 Roadmap

✅ **Basic AI video generation with TTS**  
🚧 **Fix background music support** *(Planned)*  
🚧 **Improve UI and add real-time preview** *(Planned)*  
🚧 **Optional AI Integration with Ollama for Scripts+Titles+Descriptions** *(Planned)*  
🚧 **Enhance video rendering speed** *(Planned)*  

---

## 🤝 Contributing

Fork this repo and submit pull requests!  
Feedback and bug reports welcome.

---

## 📜 License

Licensed under the **MIT License**.

---

