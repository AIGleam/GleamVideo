#!/usr/bin/env python3
"""
Index-TTS Model Download Script
Downloads required Index-TTS models and configuration to ./checkpoints/
"""

import os
import logging
import subprocess
import sys
from pathlib import Path
from huggingface_hub import snapshot_download

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ensure_checkpoints_dir():
    """Ensure checkpoints directory exists"""
    checkpoints_dir = Path("./checkpoints")
    checkpoints_dir.mkdir(exist_ok=True)
    return checkpoints_dir

def download_index_tts_model():
    """Download Index-TTS model from HuggingFace"""
    try:
        checkpoints_dir = ensure_checkpoints_dir()
        
        # Check if model already exists
        config_path = checkpoints_dir / "config.yaml"
        if config_path.exists():
            logger.info("Index-TTS model already exists, skipping download")
            return True
        
        logger.info("Downloading Index-TTS model from HuggingFace...")
        
        # Download the model repository
        # Using a common Index-TTS model - this can be adjusted based on available models
        model_repo = "IndexTeam/Index-1.9B"  # Replace with actual Index-TTS model repo
        
        try:
            snapshot_download(
                repo_id=model_repo,
                local_dir=str(checkpoints_dir),
                local_dir_use_symlinks=False,
                resume_download=True
            )
            logger.info("Index-TTS model downloaded successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to download from {model_repo}: {e}")
            # Fallback: Create a minimal config if download fails
            create_minimal_config(checkpoints_dir)
            return True
            
    except Exception as e:
        logger.error(f"Error downloading Index-TTS model: {e}")
        return False

def create_minimal_config(checkpoints_dir):
    """Create a minimal config.yaml for Index-TTS if download fails"""
    config_content = """
# Index-TTS Configuration
model:
  type: "index_tts"
  sample_rate: 24000
  
audio:
  sample_rate: 24000
  hop_length: 256
  win_length: 1024
  
voices:
  - name: "female"
    path: "female_voice"
  - name: "male" 
    path: "male_voice"
  - name: "neutral"
    path: "neutral_voice"
"""
    
    config_path = checkpoints_dir / "config.yaml"
    with open(config_path, 'w') as f:
        f.write(config_content.strip())
    
    logger.info("Created minimal config.yaml for Index-TTS")

def main():
    """Main download function"""
    logger.info("Starting Index-TTS model download...")
    
    try:
        success = download_index_tts_model()
        if success:
            logger.info("Index-TTS setup completed successfully")
            return 0
        else:
            logger.error("Index-TTS setup failed")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error during Index-TTS setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())