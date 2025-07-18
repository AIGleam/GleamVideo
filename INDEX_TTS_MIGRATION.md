# Index-TTS Migration Guide

## Overview

This document outlines the complete migration from Kokoro TTS to Index-TTS in the GleamVideo application. The migration provides better voice quality, more voice options, and improved local processing capabilities.

## Changes Made

### 1. Dependencies Updated

**Added:**
- `huggingface_hub>=0.20.0` - For downloading models from HuggingFace
- `torch>=2.0.0` - PyTorch for neural network operations
- `torchaudio>=2.0.0` - Audio processing with PyTorch

**Removed:**
- `kokoro-onnx==0.2.3` - Old TTS engine
- `onnxruntime==1.16.3` - No longer needed

### 2. Installation Scripts

**New Files:**
- `download_index_tts.py` - Downloads Index-TTS models to `./checkpoints/`
- `install_index_tts.py` - Handles Index-TTS package installation

**Installation Commands:**
```bash
pip install huggingface_hub
pip install git+https://github.com/index-tts/index-tts.git
# Torch/TorchAudio should be CUDA-matched for your system
```

### 3. Code Changes

#### GleamVideo.py
- **Import Change:** 
  - From: `import kokoro_onnx`
  - To: `from indextts.infer import IndexTTS`

- **TTSManager Class:**
  - Replaced `kokoro_model` with `index_tts_model`
  - Updated initialization: `IndexTTS(model_dir="checkpoints", cfg_path="checkpoints/config.yaml")`
  - Added dynamic voice discovery from checkpoints directory
  - Updated API: `tts.infer(voice, text, output_path)` (drop-in replacement)

- **Gemini Model Fixed:**
  - Corrected from `google/gemini-2.0-flash-exp:free` to `google/gemini-2.5-flash`

#### Launch.py
- Added Index-TTS installation check and setup
- Added model download during startup
- Added `checkpoints` directory creation

#### HTML Interface (index.html)
- Added voice selection dropdown in video generation form
- Added dynamic voice loading from `/api/voices/list` endpoint
- Updated form submission to include voice parameter

### 4. New API Endpoints

**Added:**
- `GET /api/voices/list` - Returns available TTS voices

**Updated:**
- `POST /generate_video` - Now accepts `voice` parameter

### 5. File Structure

```
gleamvideo/
├── checkpoints/           # New: Index-TTS models directory
│   ├── config.yaml       # TTS configuration
│   └── [voice models]    # Voice model files
├── download_index_tts.py  # New: Model download script
├── install_index_tts.py   # New: Installation script
├── gleamvideo.py         # Updated: Index-TTS integration
├── launch.py             # Updated: Setup automation
├── index.html            # Updated: Voice selection UI
└── requirements.txt      # Updated: New dependencies
```

## Features

### Voice Selection
- Dynamic voice discovery from downloaded models
- UI dropdown with available voices
- Support for custom voice models
- Fallback to default voices (female, male, neutral)

### Model Management
- Automatic model download on first run
- Checkpoints directory for model storage
- HuggingFace Hub integration for model fetching

### Compatibility
- Drop-in API replacement (same `infer` signature)
- Existing video generation workflows unchanged
- Both manual and automated video creation supported

## Usage

### Manual Video Creation
1. Select desired voice from dropdown in UI
2. Enter video content and parameters
3. Generate video with chosen voice

### Automated Video Creation
- Uses default "female" voice for auto-generated videos
- Can be customized by modifying the `voice` parameter in `generate_auto_video()`

## Troubleshooting

### Installation Issues
- Ensure CUDA-compatible PyTorch if using GPU
- Check internet connection for model downloads
- Verify HuggingFace Hub access

### Model Loading
- Check `checkpoints/config.yaml` exists
- Ensure model files are properly downloaded
- Review logs for specific error messages

### Voice Selection
- Refresh browser if voices don't load
- Check `/api/voices/list` endpoint directly
- Verify TTSManager initialization in logs

## Migration Benefits

1. **Better Quality:** Index-TTS provides higher quality voice synthesis
2. **More Voices:** Support for custom and additional voice models
3. **Local Processing:** All processing happens locally on your PC
4. **Extensibility:** Easy to add new voice models via HuggingFace
5. **Performance:** Optimized for local GPU acceleration
6. **Future-Proof:** Active development and community support

## Development Notes

- The `infer()` method signature is identical to Kokoro, ensuring seamless migration
- Voice discovery is automatic but can be customized in `get_available_voices()`
- Model downloading is handled gracefully with fallbacks
- UI updates are backward-compatible with existing form structure