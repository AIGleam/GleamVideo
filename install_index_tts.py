#!/usr/bin/env python3
"""
Install Index-TTS and dependencies
This script handles the installation of Index-TTS with proper dependencies
"""

import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_package(package_name, install_command=None):
    """Install a package using pip or custom command"""
    try:
        if install_command:
            logger.info(f"Installing {package_name} with custom command...")
            result = subprocess.run(install_command, shell=True, check=True, capture_output=True, text=True)
        else:
            logger.info(f"Installing {package_name}...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                                  check=True, capture_output=True, text=True)
        
        logger.info(f"Successfully installed {package_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {package_name}: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def main():
    """Main installation function"""
    logger.info("Starting Index-TTS installation...")
    
    packages = [
        ("huggingface_hub", None),
        ("torch", None),  # Will use the version from requirements.txt
        ("torchaudio", None),
        ("Index-TTS", "pip install git+https://github.com/index-tts/index-tts.git")
    ]
    
    failed_packages = []
    
    for package_name, install_command in packages:
        if not install_package(package_name, install_command):
            failed_packages.append(package_name)
    
    if failed_packages:
        logger.error(f"Failed to install: {', '.join(failed_packages)}")
        return 1
    else:
        logger.info("All packages installed successfully!")
        return 0

if __name__ == "__main__":
    sys.exit(main())