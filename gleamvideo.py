#!/usr/bin/env python3
"""
GleamVideo Enhanced - AI-Powered Video Generation Platform
Author: GleamVideo Team
License: MIT

Advanced video generation with AI integration, multiple backends,
and enhanced automation features.
"""

import os
import sys
import asyncio
import uvicorn
import requests
import aiohttp
import aiofiles
import tempfile
import zipfile
import time
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from io import BytesIO
import subprocess
import pytz
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import json
import hashlib
import logging
import tempfile
import shutil
from urllib.parse import urlparse, unquote
import re
import threading
from concurrent.futures import ThreadPoolExecutor
import feedparser
from bs4 import BeautifulSoup

# FastAPI imports
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

# Selenium imports
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.firefox import GeckoDriverManager

# Pydantic for data validation
from pydantic import BaseModel

# TTS Integration
try:
    import kokoro_onnx
    KOKORO_AVAILABLE = True
except ImportError:
    KOKORO_AVAILABLE = False
    print("Warning: Kokoro TTS not available. Install with: pip install kokoro-onnx")

# Audio processing
import soundfile as sf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration and Global Variables
# ---------------------------------------------------------------------------

class AppConfig:
    def __init__(self):
        self.openrouter_api_key = None
        self.reddit_rss_feeds = [
            "https://www.reddit.com/r/technology/.rss",
            "https://www.reddit.com/r/science/.rss",
            "https://www.reddit.com/r/worldnews/.rss",
            "https://www.reddit.com/r/dataisbeautiful/.rss",
            "https://www.reddit.com/r/futurology/.rss"
        ]
        self.auto_mode_enabled = False
        self.auto_mode_interval = 3600  # 1 hour

app_config = AppConfig()

# Enhanced progress tracking
progress_data = {
    "status": "idle",  # idle, working, done, error
    "message": "",
    "pct": 0,
    "current_task": "",
    "auto_mode": False,
    "last_auto_run": None
}

def update_progress(status: str, message: str, pct: float, current_task: str = ""):
    progress_data["status"] = status
    progress_data["message"] = message
    progress_data["pct"] = pct
    progress_data["current_task"] = current_task
    logger.info(f"Progress: {status} - {message} ({pct}%)")

# ---------------------------------------------------------------------------
# Gemini 2.5 Flash Integration via OpenRouter
# ---------------------------------------------------------------------------
class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "google/gemini-2.0-flash-exp:free"
    
    async def generate_content(self, prompt: str, system_prompt: str = None) -> str:
        """Generate content using Gemini via OpenRouter"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://gleamvideo.com",
            "X-Title": "GleamVideo Enhanced"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 4000
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                        raise Exception(f"API Error: {response.status}")
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            raise

# ---------------------------------------------------------------------------
# Enhanced Screenshot System with Multiple Angles
# ---------------------------------------------------------------------------
class AdvancedScreenshotManager:
    def __init__(self):
        self.driver = None
        self.driver_initialized = False
        
    def initialize_driver(self):
        """Initialize Firefox WebDriver with optimal settings"""
        if self.driver_initialized:
            return
            
        try:
            options = FirefoxOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            
            # Enhanced preferences for better screenshots
            options.set_preference("general.useragent.override", 
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            options.set_preference("dom.webnotifications.enabled", False)
            options.set_preference("media.autoplay.default", 0)
            
            # Use webdriver-manager for automatic driver management
            service = FirefoxService(GeckoDriverManager().install())
            
            self.driver = webdriver.Firefox(service=service, options=options)
            self.driver_initialized = True
            logger.info("Screenshot driver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize screenshot driver: {e}")
            self.driver = None
    
    def capture_advanced_screenshot(self, url: str, filename: str) -> bool:
        """Capture screenshot with enhanced techniques"""
        try:
            if not self.driver_initialized:
                self.initialize_driver()
            
            if not self.driver:
                logger.error("Driver not available for screenshot")
                return False
            
            # Navigate and wait for load
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(3)
            
            # Execute JS to remove overlays and improve visibility
            self.driver.execute_script("""
                // Remove common overlay elements
                document.querySelectorAll('[class*="overlay"], [class*="modal"], [class*="popup"]').forEach(el => el.remove());
                document.querySelectorAll('[id*="overlay"], [id*="modal"], [id*="popup"]').forEach(el => el.remove());
                
                // Remove cookie banners
                document.querySelectorAll('[class*="cookie"], [class*="gdpr"], [class*="consent"]').forEach(el => el.remove());
                
                // Scroll to top
                window.scrollTo(0, 0);
            """)
            
            time.sleep(1)
            
            # Take screenshot
            screenshot_taken = self.driver.save_screenshot(filename)
            
            if screenshot_taken:
                logger.info(f"Screenshot saved: {filename}")
                return True
            else:
                logger.error("Failed to take screenshot")
                return False
                
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return False
    
    def cleanup(self):
        """Clean up driver resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.driver_initialized = False
                logger.info("Screenshot driver cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up driver: {e}")

# ---------------------------------------------------------------------------
# Enhanced TTS with Multiple Voices
# ---------------------------------------------------------------------------
class TTSManager:
    def __init__(self):
        self.kokoro_model = None
        self.available_voices = []
        self.initialize_tts()
    
    def initialize_tts(self):
        """Initialize TTS engines"""
        if KOKORO_AVAILABLE:
            try:
                # Initialize Kokoro TTS
                self.kokoro_model = kokoro_onnx.Kokoro()
                self.available_voices = ["female", "male", "neutral"]
                logger.info("Kokoro TTS initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Kokoro TTS: {e}")
                self.kokoro_model = None
        else:
            logger.warning("Kokoro TTS not available")
    
    def generate_speech(self, text: str, output_file: str, voice: str = "female") -> bool:
        """Generate speech from text"""
        try:
            if self.kokoro_model and voice in self.available_voices:
                # Use Kokoro TTS
                audio_data = self.kokoro_model.generate(text, voice=voice)
                sf.write(output_file, audio_data, 24000)
                logger.info(f"Speech generated: {output_file}")
                return True
            else:
                # Fallback to system TTS or silence
                logger.warning("TTS not available, generating silence")
                duration = len(text) * 0.1  # Rough estimate
                silence = np.zeros(int(24000 * duration))
                sf.write(output_file, silence, 24000)
                return True
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return False

# ---------------------------------------------------------------------------
# Enhanced Auto Mode Manager
# ---------------------------------------------------------------------------
class AutoModeManager:
    def __init__(self):
        self.auto_task = None
        self.is_running = False
        self.last_run_time = None
        
    async def start_auto_mode(self) -> bool:
        """Start automated video generation"""
        try:
            if self.is_running:
                logger.warning("Auto mode already running")
                return False
            
            self.is_running = True
            self.auto_task = asyncio.create_task(self.auto_mode_loop())
            logger.info("Auto mode started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting auto mode: {e}")
            self.is_running = False
            return False
    
    def stop_auto_mode(self):
        """Stop automated video generation"""
        if self.auto_task:
            self.auto_task.cancel()
            self.auto_task = None
        self.is_running = False
        logger.info("Auto mode stopped")
    
    async def auto_mode_loop(self):
        """Main auto mode loop"""
        try:
            while self.is_running:
                logger.info("Auto mode cycle starting")
                
                # Check if enough time has passed
                if (self.last_run_time and 
                    datetime.now() - self.last_run_time < timedelta(seconds=app_config.auto_mode_interval)):
                    await asyncio.sleep(60)  # Check every minute
                    continue
                
                try:
                    # Run auto generation
                    await self.run_auto_generation()
                    self.last_run_time = datetime.now()
                    
                except Exception as e:
                    logger.error(f"Error in auto generation: {e}")
                
                # Wait for next cycle
                await asyncio.sleep(app_config.auto_mode_interval)
                
        except asyncio.CancelledError:
            logger.info("Auto mode loop cancelled")
        except Exception as e:
            logger.error(f"Error in auto mode loop: {e}")
            self.is_running = False
    
    async def run_auto_generation(self):
        """Run a single auto generation cycle"""
        if not app_config.openrouter_api_key:
            logger.error("OpenRouter API key not set")
            return
        
        try:
            update_progress("working", "Fetching trending content...", 10, "Auto Generation")
            
            # Fetch trending content from RSS feeds
            content = await self.fetch_trending_content()
            
            if not content:
                logger.warning("No trending content found")
                return
            
            update_progress("working", "Generating video content with AI...", 30, "AI Processing")
            
            # Generate video using AI
            await self.generate_auto_video(content)
            
            update_progress("done", "Auto generation completed", 100, "Complete")
            
        except Exception as e:
            logger.error(f"Error in auto generation: {e}")
            update_progress("error", f"Auto generation failed: {str(e)}", 0, "Error")
    
    async def fetch_trending_content(self) -> Optional[Dict]:
        """Fetch trending content from RSS feeds"""
        try:
            for feed_url in app_config.reddit_rss_feeds[:2]:  # Limit to 2 feeds
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(feed_url) as response:
                            if response.status == 200:
                                feed_data = await response.text()
                                feed = feedparser.parse(feed_data)
                                
                                if feed.entries:
                                    # Get first trending entry
                                    entry = feed.entries[0]
                                    return {
                                        "title": entry.title,
                                        "summary": entry.summary if hasattr(entry, 'summary') else entry.title,
                                        "link": entry.link,
                                        "source": feed_url
                                    }
                except Exception as e:
                    logger.error(f"Error fetching from {feed_url}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching trending content: {e}")
            return None
    
    async def generate_auto_video(self, content: Dict):
        """Generate video from trending content"""
        try:
            # Initialize AI client
            ai_client = GeminiClient(app_config.openrouter_api_key)
            
            # Generate script
            system_prompt = """You are a content creator for engaging video scripts. 
            Create a compelling, informative script based on the provided content. 
            The script should be engaging, factual, and suitable for a 2-3 minute video.
            Format the response as a clear narrative without special formatting."""
            
            prompt = f"Create an engaging video script about: {content['title']}\n\nSummary: {content['summary']}"
            
            script = await ai_client.generate_content(prompt, system_prompt)
            
            # Create video with generated content
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"auto_video_{timestamp}.mp4"
            
            # Use the main video generation function
            paragraphs = [script[:500], script[500:1000]] if len(script) > 500 else [script]
            links = [content.get('link', '')] if content.get('link') else []
            
            video_generator = EnhancedVideoGenerator()
            success = await video_generator.create_video(
                paragraphs=paragraphs,
                links=links,
                output_name=output_name,
                resolution="1920x1080",
                transition_duration=2.0
            )
            
            if success:
                logger.info(f"Auto video generated successfully: {output_name}")
            else:
                logger.error("Auto video generation failed")
                
        except Exception as e:
            logger.error(f"Error generating auto video: {e}")

# ---------------------------------------------------------------------------
# Enhanced Video Generation with Ken Burns Effect
# ---------------------------------------------------------------------------
class EnhancedVideoGenerator:
    def __init__(self):
        self.screenshot_manager = AdvancedScreenshotManager()
        self.tts_manager = TTSManager()
        
    def apply_ken_burns_effect(self, image_path: str, output_path: str, duration: float = 3.0) -> bool:
        """Apply Ken Burns pan and zoom effect to image"""
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Could not load image: {image_path}")
                return False
            
            height, width = img.shape[:2]
            
            # Calculate zoom and pan parameters
            start_scale = 1.0
            end_scale = 1.3
            fps = 30
            total_frames = int(duration * fps)
            
            # Create video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            for frame_num in range(total_frames):
                progress = frame_num / total_frames
                
                # Calculate current scale
                current_scale = start_scale + (end_scale - start_scale) * progress
                
                # Calculate pan offset (subtle movement)
                pan_x = int(width * 0.05 * progress)
                pan_y = int(height * 0.03 * progress)
                
                # Create transformation matrix
                new_width = int(width * current_scale)
                new_height = int(height * current_scale)
                
                # Resize image
                resized = cv2.resize(img, (new_width, new_height))
                
                # Calculate crop area
                crop_x = max(0, (new_width - width) // 2 + pan_x)
                crop_y = max(0, (new_height - height) // 2 + pan_y)
                
                # Ensure crop doesn't exceed image boundaries
                crop_x = min(crop_x, new_width - width)
                crop_y = min(crop_y, new_height - height)
                
                # Crop to original size
                frame = resized[crop_y:crop_y + height, crop_x:crop_x + width]
                
                # Write frame
                out.write(frame)
            
            out.release()
            logger.info(f"Ken Burns effect applied: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying Ken Burns effect: {e}")
            return False
    
    async def create_video(self, paragraphs: List[str], links: List[str], 
                          output_name: str, resolution: str = "1920x1080",
                          transition_duration: float = 2.0) -> bool:
        """Create enhanced video with multiple improvements"""
        try:
            update_progress("working", "Initializing video creation...", 5, "Setup")
            
            # Create temp directory
            temp_dir = tempfile.mkdtemp(prefix="gleamvideo_")
            logger.info(f"Working in temp directory: {temp_dir}")
            
            # Parse resolution
            width, height = map(int, resolution.split('x'))
            
            # Generate audio for each paragraph
            audio_files = []
            video_clips = []
            
            update_progress("working", "Generating speech audio...", 15, "TTS Generation")
            
            for i, paragraph in enumerate(paragraphs):
                audio_file = os.path.join(temp_dir, f"audio_{i}.wav")
                if self.tts_manager.generate_speech(paragraph, audio_file):
                    audio_files.append(audio_file)
                else:
                    logger.warning(f"Failed to generate audio for paragraph {i}")
            
            # Process images and create video clips
            update_progress("working", "Processing images and creating clips...", 30, "Image Processing")
            
            for i, (paragraph, link) in enumerate(zip(paragraphs, links + [''] * len(paragraphs))):
                clip_path = os.path.join(temp_dir, f"clip_{i}.mp4")
                
                if link and link.strip():
                    # Try to capture screenshot
                    screenshot_path = os.path.join(temp_dir, f"screenshot_{i}.png")
                    if self.screenshot_manager.capture_advanced_screenshot(link, screenshot_path):
                        # Apply Ken Burns effect
                        ken_burns_path = os.path.join(temp_dir, f"kenburns_{i}.mp4")
                        if self.apply_ken_burns_effect(screenshot_path, ken_burns_path, 3.0):
                            video_clips.append(ken_burns_path)
                        else:
                            # Fallback to static image
                            self.create_static_clip(screenshot_path, clip_path, 3.0, width, height)
                            video_clips.append(clip_path)
                    else:
                        # Create text-based clip
                        self.create_text_clip(paragraph[:100], clip_path, 3.0, width, height)
                        video_clips.append(clip_path)
                else:
                    # Create text-based clip
                    self.create_text_clip(paragraph[:100], clip_path, 3.0, width, height)
                    video_clips.append(clip_path)
            
            # Combine video clips
            update_progress("working", "Combining video clips...", 60, "Video Assembly")
            
            final_video_path = await self.combine_clips_with_audio(
                video_clips, audio_files, temp_dir, output_name, transition_duration
            )
            
            # Move final video to videos directory
            os.makedirs("videos", exist_ok=True)
            final_output = os.path.join("videos", output_name)
            
            if os.path.exists(final_video_path):
                shutil.move(final_video_path, final_output)
                logger.info(f"Video created successfully: {final_output}")
                update_progress("done", f"Video created: {output_name}", 100, "Complete")
                return True
            else:
                logger.error("Final video file not found")
                update_progress("error", "Video creation failed", 0, "Error")
                return False
            
        except Exception as e:
            logger.error(f"Error creating video: {e}")
            update_progress("error", f"Video creation failed: {str(e)}", 0, "Error")
            return False
        finally:
            # Cleanup
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.screenshot_manager.cleanup()
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def create_text_clip(self, text: str, output_path: str, duration: float, width: int, height: int):
        """Create a video clip with animated text"""
        try:
            # Create image with text
            img = Image.new('RGB', (width, height), color='#1a1a2e')
            draw = ImageDraw.Draw(img)
            
            # Try to use a nice font
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Draw text with outline
            for dx in [-2, -1, 0, 1, 2]:
                for dy in [-2, -1, 0, 1, 2]:
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill='black')
            
            draw.text((x, y), text, font=font, fill='white')
            
            # Save image
            temp_img_path = output_path.replace('.mp4', '.png')
            img.save(temp_img_path)
            
            # Convert to video
            fps = 30
            total_frames = int(duration * fps)
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # Load image with OpenCV
            cv_img = cv2.imread(temp_img_path)
            
            for _ in range(total_frames):
                out.write(cv_img)
            
            out.release()
            os.remove(temp_img_path)
            
        except Exception as e:
            logger.error(f"Error creating text clip: {e}")
    
    def create_static_clip(self, image_path: str, output_path: str, duration: float, width: int, height: int):
        """Create a static video clip from an image"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return
            
            # Resize image to target resolution
            img = cv2.resize(img, (width, height))
            
            fps = 30
            total_frames = int(duration * fps)
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            for _ in range(total_frames):
                out.write(img)
            
            out.release()
            
        except Exception as e:
            logger.error(f"Error creating static clip: {e}")
    
    async def combine_clips_with_audio(self, video_clips: List[str], audio_files: List[str], 
                                     temp_dir: str, output_name: str, transition_duration: float) -> str:
        """Combine video clips with audio using FFmpeg"""
        try:
            # Create file list for FFmpeg
            file_list_path = os.path.join(temp_dir, "file_list.txt")
            with open(file_list_path, 'w') as f:
                for clip in video_clips:
                    if os.path.exists(clip):
                        f.write(f"file '{clip}'\n")
            
            # Combine video clips
            combined_video = os.path.join(temp_dir, "combined_video.mp4")
            cmd_video = [
                'ffmpeg', '-f', 'concat', '-safe', '0', '-i', file_list_path,
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
                '-y', combined_video
            ]
            
            result = subprocess.run(cmd_video, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg video combine error: {result.stderr}")
                return ""
            
            # Combine audio files if any
            if audio_files:
                audio_list_path = os.path.join(temp_dir, "audio_list.txt")
                with open(audio_list_path, 'w') as f:
                    for audio in audio_files:
                        if os.path.exists(audio):
                            f.write(f"file '{audio}'\n")
                
                combined_audio = os.path.join(temp_dir, "combined_audio.wav")
                cmd_audio = [
                    'ffmpeg', '-f', 'concat', '-safe', '0', '-i', audio_list_path,
                    '-y', combined_audio
                ]
                
                subprocess.run(cmd_audio, capture_output=True, text=True)
                
                # Combine video with audio
                final_output = os.path.join(temp_dir, output_name)
                cmd_final = [
                    'ffmpeg', '-i', combined_video, '-i', combined_audio,
                    '-c:v', 'copy', '-c:a', 'aac', '-shortest',
                    '-y', final_output
                ]
                
                result = subprocess.run(cmd_final, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(f"FFmpeg final combine error: {result.stderr}")
                    return combined_video
                
                return final_output
            else:
                # No audio, just return video
                final_output = os.path.join(temp_dir, output_name)
                shutil.copy(combined_video, final_output)
                return final_output
            
        except Exception as e:
            logger.error(f"Error combining clips: {e}")
            return ""

# ---------------------------------------------------------------------------
# FastAPI Application Setup
# ---------------------------------------------------------------------------
app = FastAPI(title="GleamVideo Enhanced", version="3.0.0")

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Global instances
auto_mode_manager = AutoModeManager()
video_generator = EnhancedVideoGenerator()

# Pydantic models
class AutoModeConfig(BaseModel):
    enabled: bool
    interval_hours: int = 1
    rss_feeds: List[str] = []

class APIKeyConfig(BaseModel):
    openrouter_api_key: str

# ---------------------------------------------------------------------------
# Enhanced UI Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the enhanced modern UI"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Error: index.html not found</h1>", status_code=404)

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/config/api-key")
async def set_api_key(config: APIKeyConfig):
    """Set the OpenRouter API key"""
    try:
        app_config.openrouter_api_key = config.openrouter_api_key
        logger.info("OpenRouter API key updated")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error setting API key: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/auto-mode/start")
async def start_auto_mode_api(config: AutoModeConfig):
    """Start auto mode"""
    try:
        if not app_config.openrouter_api_key:
            return {"success": False, "error": "OpenRouter API key not set"}
        
        app_config.auto_mode_enabled = True
        app_config.auto_mode_interval = config.interval_hours * 3600
        
        if config.rss_feeds:
            app_config.reddit_rss_feeds = config.rss_feeds
        
        success = await auto_mode_manager.start_auto_mode()
        
        if success:
            return {"success": True}
        else:
            return {"success": False, "error": "Failed to start auto mode"}
            
    except Exception as e:
        logger.error(f"Error starting auto mode: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/auto-mode/stop")
async def stop_auto_mode_api():
    """Stop auto mode"""
    try:
        auto_mode_manager.stop_auto_mode()
        app_config.auto_mode_enabled = False
        return {"success": True}
    except Exception as e:
        logger.error(f"Error stopping auto mode: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/auto-mode/run-now")
async def run_auto_now_api():
    """Trigger immediate auto generation"""
    try:
        if not app_config.openrouter_api_key:
            return {"success": False, "error": "OpenRouter API key not set"}
        
        # Run auto generation in background
        asyncio.create_task(auto_mode_manager.run_auto_generation())
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error running auto now: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/auto-mode/status")
async def get_auto_mode_status():
    """Get auto mode status"""
    return {
        "running": auto_mode_manager.is_running,
        "enabled": app_config.auto_mode_enabled,
        "last_run": auto_mode_manager.last_run_time.isoformat() if auto_mode_manager.last_run_time else None,
        "interval_hours": app_config.auto_mode_interval // 3600
    }

@app.get("/api/videos/list")
async def list_videos():
    """List generated videos"""
    try:
        videos_dir = Path("videos")
        if not videos_dir.exists():
            return {"videos": []}
        
        videos = []
        for video_file in videos_dir.glob("*.mp4"):
            stat = video_file.stat()
            videos.append({
                "name": video_file.name,
                "size": f"{stat.st_size / (1024*1024):.1f} MB",
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        
        # Sort by creation time, newest first
        videos.sort(key=lambda x: x["created"], reverse=True)
        return {"videos": videos}
        
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        return {"videos": [], "error": str(e)}

@app.get("/videos/download/{filename}")
async def download_video(filename: str):
    """Download a generated video"""
    try:
        video_path = Path("videos") / filename
        if video_path.exists() and video_path.suffix == ".mp4":
            return FileResponse(
                path=str(video_path),
                filename=filename,
                media_type="video/mp4"
            )
        else:
            raise HTTPException(status_code=404, detail="Video not found")
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate_video")
async def generate_video(
    paragraphs: List[str] = Form(...),
    links: List[str] = Form(default=[]),
    output_name: str = Form(default="generated-video.mp4"),
    resolution: str = Form(default="1920x1080"),
    transition_duration: float = Form(default=2.0)
):
    """Generate video from form data"""
    try:
        # Validate input
        if not paragraphs or all(not p.strip() for p in paragraphs):
            return {"success": False, "error": "No paragraphs provided"}
        
        # Filter out empty paragraphs and links
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        links = [l.strip() for l in links if l.strip()]
        
        # Ensure output name has .mp4 extension
        if not output_name.endswith('.mp4'):
            output_name += '.mp4'
        
        # Start video generation in background
        asyncio.create_task(video_generator.create_video(
            paragraphs=paragraphs,
            links=links,
            output_name=output_name,
            resolution=resolution,
            transition_duration=transition_duration
        ))
        
        return {"success": True, "message": "Video generation started"}
        
    except Exception as e:
        logger.error(f"Error starting video generation: {e}")
        return {"success": False, "error": str(e)}

@app.get("/progress")
async def get_progress():
    """Get current progress"""
    return {
        "status": progress_data["status"],
        "message": progress_data["message"],
        "progress": progress_data["pct"],
        "current_task": progress_data["current_task"],
        "auto_mode": auto_mode_manager.is_running
    }

# ---------------------------------------------------------------------------
# Application Lifecycle
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        # Create necessary directories
        os.makedirs("videos", exist_ok=True)
        
        # Initialize components
        logger.info("GleamVideo Enhanced started successfully")
        update_progress("idle", "Ready to generate videos", 0, "Ready")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        # Stop auto mode
        auto_mode_manager.stop_auto_mode()
        
        # Cleanup screenshot manager
        video_generator.screenshot_manager.cleanup()
        
        logger.info("GleamVideo Enhanced shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        logger.info("Starting GleamVideo Enhanced Server...")
        uvicorn.run(
            "gleamvideo:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {e}")