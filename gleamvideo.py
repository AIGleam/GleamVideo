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
import logging
import shutil
from urllib.parse import urlparse, unquote
import re
from concurrent.futures import ThreadPoolExecutor
import feedparser
import platform

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
    from indextts.infer import IndexTTS
    INDEX_TTS_AVAILABLE = True
except ImportError:
    INDEX_TTS_AVAILABLE = False
    print("Warning: Index-TTS not available. Install with: pip install git+https://github.com/index-tts/index-tts.git")

# Audio processing
import soundfile as sf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cross-platform utility functions
# ---------------------------------------------------------------------------

def get_system_font_path():
    """Get system font path based on platform"""
    system = platform.system()
    
    if system == "Windows":
        return "C:/Windows/Fonts/arial.ttf"
    elif system == "Darwin":  # macOS
        return "/System/Library/Fonts/Arial.ttf"
    else:  # Linux
        return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def ensure_cross_platform_path(path_str: str) -> str:
    """Ensure path works across platforms"""
    return str(Path(path_str).resolve())

# ---------------------------------------------------------------------------
# Enhanced TTS Text Formatting
# ---------------------------------------------------------------------------
class TTSTextFormatter:
    """Enhanced text formatter for TTS-friendly output"""
    
    @staticmethod
    def format_for_tts(text: str) -> str:
        """Format text to be more TTS-friendly"""
        # Replace common contractions that sound weird
        text = re.sub(r"\bI'm\b", "I am", text)
        text = re.sub(r"\byou're\b", "you are", text)
        text = re.sub(r"\bwe're\b", "we are", text)
        text = re.sub(r"\bthey're\b", "they are", text)
        text = re.sub(r"\bcan't\b", "cannot", text)
        text = re.sub(r"\bwon't\b", "will not", text)
        text = re.sub(r"\bdon't\b", "do not", text)
        text = re.sub(r"\bdidn't\b", "did not", text)
        text = re.sub(r"\bhasn't\b", "has not", text)
        text = re.sub(r"\bhaven't\b", "have not", text)
        text = re.sub(r"\bisn't\b", "is not", text)
        text = re.sub(r"\baren't\b", "are not", text)
        text = re.sub(r"\bwasn't\b", "was not", text)
        text = re.sub(r"\bweren't\b", "were not", text)
        text = re.sub(r"\bshouldn't\b", "should not", text)
        text = re.sub(r"\bwouldn't\b", "would not", text)
        text = re.sub(r"\bcouldn't\b", "could not", text)
        
        # Handle common abbreviations
        text = re.sub(r"\bvs\.\b", "versus", text)
        text = re.sub(r"\betc\.\b", "etcetera", text)
        text = re.sub(r"\bi\.e\.\b", "that is", text)
        text = re.sub(r"\be\.g\.\b", "for example", text)
        text = re.sub(r"\bMr\.\b", "Mister", text)
        text = re.sub(r"\bMrs\.\b", "Missus", text)
        text = re.sub(r"\bDr\.\b", "Doctor", text)
        
        # Handle URLs and subreddits
        text = re.sub(r"r/([a-zA-Z0-9_]+)", r"r slash \1", text)
        text = re.sub(r"u/([a-zA-Z0-9_]+)", r"u slash \1", text)
        text = re.sub(r"https?://[^\s]+", "link", text)
        
        # Handle numbers and units
        text = re.sub(r"\b(\d+)k\b", r"\1 thousand", text)
        text = re.sub(r"\b(\d+)m\b", r"\1 million", text)
        text = re.sub(r"\b(\d+)b\b", r"\1 billion", text)
        text = re.sub(r"\b(\d+)%", r"\1 percent", text)
        
        # Add pauses for better flow
        text = re.sub(r"[.!?]\s+", ". ", text)
        text = re.sub(r",\s+", ", ", text)
        
        return text.strip()

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
        self.auto_mode_voice = "female"  # Default voice for auto mode
        self.target_subreddit = "technology"  # User-specified subreddit
        self.video_length_target = 180  # Target video length in seconds (3 minutes)
        self.commentary_style = "funny_vulgar"  # Commentary style
        self.specific_reddit_posts = []  # List of specific Reddit post URLs
        self.reaction_personality = "sarcastic_reviewer"  # AI personality for reactions

app_config = AppConfig()

# Enhanced progress tracking
progress_data = {
    "status": "idle",
    "message": "Ready to generate videos",
    "pct": 0,
    "current_task": ""
}

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
        """Fetch trending content from RSS feeds or specific posts"""
        try:
            # First, check if user has specified specific Reddit posts
            if app_config.specific_reddit_posts:
                return await self.fetch_specific_reddit_post(app_config.specific_reddit_posts[0])
            
            # Build RSS feed URL for target subreddit
            target_feed_url = f"https://www.reddit.com/r/{app_config.target_subreddit}/.rss"
            feeds_to_check = [target_feed_url] + app_config.reddit_rss_feeds[:2]
            
            for feed_url in feeds_to_check:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(feed_url, headers={'User-Agent': 'GleamVideo Bot 2.0'}) as response:
                            if response.status == 200:
                                feed_data = await response.text()
                                feed = feedparser.parse(feed_data)
                                
                                if feed.entries:
                                    # Get first trending entry
                                    entry = feed.entries[0]
                                    
                                    # Extract more content from the entry
                                    content_text = ""
                                    if hasattr(entry, 'content') and entry.content:
                                        content_text = entry.content[0].value if isinstance(entry.content, list) else str(entry.content)
                                    elif hasattr(entry, 'summary'):
                                        content_text = entry.summary
                                    
                                    # Clean up HTML if present
                                    content_text = re.sub(r'<[^>]+>', '', content_text)
                                    content_text = re.sub(r'&[a-zA-Z0-9#]+;', '', content_text)
                                    
                                    return {
                                        "title": entry.title,
                                        "content": content_text or entry.title,
                                        "summary": entry.summary if hasattr(entry, 'summary') else entry.title,
                                        "link": entry.link,
                                        "source": feed_url,
                                        "subreddit": app_config.target_subreddit
                                    }
                except Exception as e:
                    logger.error(f"Error fetching from {feed_url}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching trending content: {e}")
            return None
    
    async def fetch_specific_reddit_post(self, post_url: str) -> Optional[Dict]:
        """Fetch content from a specific Reddit post URL"""
        try:
            # Convert Reddit URL to RSS format if needed
            if '/comments/' in post_url:
                rss_url = post_url + '.rss'
            else:
                rss_url = post_url
            
            async with aiohttp.ClientSession() as session:
                async with session.get(rss_url, headers={'User-Agent': 'GleamVideo Bot 2.0'}) as response:
                    if response.status == 200:
                        feed_data = await response.text()
                        feed = feedparser.parse(feed_data)
                        
                        if feed.entries:
                            entry = feed.entries[0]
                            
                            # Extract content
                            content_text = ""
                            if hasattr(entry, 'content') and entry.content:
                                content_text = entry.content[0].value if isinstance(entry.content, list) else str(entry.content)
                            elif hasattr(entry, 'summary'):
                                content_text = entry.summary
                            
                            # Clean up HTML
                            content_text = re.sub(r'<[^>]+>', '', content_text)
                            content_text = re.sub(r'&[a-zA-Z0-9#]+;', '', content_text)
                            
                            # Extract subreddit from URL
                            subreddit_match = re.search(r'/r/([^/]+)/', post_url)
                            subreddit = subreddit_match.group(1) if subreddit_match else app_config.target_subreddit
                            
                            return {
                                "title": entry.title,
                                "content": content_text or entry.title,
                                "summary": entry.summary if hasattr(entry, 'summary') else entry.title,
                                "link": entry.link,
                                "source": post_url,
                                "subreddit": subreddit
                            }
            
            return None
        except Exception as e:
            logger.error(f"Error fetching specific Reddit post: {e}")
            return None
    
    async def generate_auto_video(self, content: Dict):
        """Generate video from trending content with reactions"""
        try:
            # Initialize AI client
            ai_client = GeminiClient(app_config.openrouter_api_key)
            
            # Generate reaction script using the enhanced method
            script = await ai_client.generate_reddit_reaction(content, app_config.video_length_target)
            
            # Break script into time-appropriate segments
            segments = await ai_client.generate_timed_content(script, app_config.video_length_target)
            
            # Create video with generated content
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            subreddit = content.get('subreddit', app_config.target_subreddit)
            output_name = f"reaction_{subreddit}_{timestamp}.mp4"
            
            # Use the segments as paragraphs
            links = [content.get('link', '')] if content.get('link') else []
            
            video_generator = EnhancedVideoGenerator()
            success = await video_generator.create_video(
                paragraphs=segments,
                links=links,
                output_name=output_name,
                resolution="1920x1080",
                transition_duration=2.0,
                voice=getattr(app_config, 'auto_mode_voice', 'female'),
                target_duration=app_config.video_length_target
            )
            
            if success:
                logger.info(f"Auto reaction video generated successfully: {output_name}")
            else:
                logger.error("Auto video generation failed")
                
        except Exception as e:
            logger.error(f"Error generating auto video: {e}")

# ---------------------------------------------------------------------------
# Helper Functions for Enhanced Features
# ---------------------------------------------------------------------------
async def generate_specific_reddit_reaction(reddit_url: str, video_length: int, voice: str):
    """Generate a reaction video for a specific Reddit post"""
    try:
        update_progress("working", "Fetching Reddit content...", 10, "Reddit Fetch")
        
        # Fetch the specific Reddit post
        content = await auto_mode_manager.fetch_specific_reddit_post(reddit_url)
        
        if not content:
            update_progress("error", "Failed to fetch Reddit content", 0, "Error")
            return
        
        update_progress("working", "Generating reaction script...", 30, "AI Processing")
        
        # Generate reaction
        ai_client = GeminiClient(app_config.openrouter_api_key)
        script = await ai_client.generate_reddit_reaction(content, video_length)
        segments = await ai_client.generate_timed_content(script, video_length)
        
        update_progress("working", "Creating video...", 60, "Video Generation")
        
        # Create video
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        subreddit = content.get('subreddit', 'reddit')
        output_name = f"reaction_{subreddit}_{timestamp}.mp4"
        
        video_generator = EnhancedVideoGenerator()
        success = await video_generator.create_video(
            paragraphs=segments,
            links=[content.get('link', '')],
            output_name=output_name,
            resolution="1920x1080",
            transition_duration=2.0,
            voice=voice,
            target_duration=video_length
        )
        
        if success:
            update_progress("done", f"Reaction video created: {output_name}", 100, "Complete")
        else:
            update_progress("error", "Video generation failed", 0, "Error")
            
    except Exception as e:
        logger.error(f"Error in specific Reddit reaction generation: {e}")
        update_progress("error", f"Generation failed: {str(e)}", 0, "Error")

# ---------------------------------------------------------------------------
# Enhanced TTS with Multiple Voices
# ---------------------------------------------------------------------------
class TTSManager:
    def __init__(self):
        self.index_tts_model = None
        self.available_voices = []
        self.initialize_tts()
    
    def initialize_tts(self):
        """Initialize TTS engines"""
        if INDEX_TTS_AVAILABLE:
            try:
                # Initialize Index-TTS
                self.index_tts_model = IndexTTS(
                    model_dir="checkpoints", 
                    cfg_path="checkpoints/config.yaml"
                )
                self.available_voices = self.get_available_voices()
                logger.info(f"Index-TTS initialized successfully with voices: {self.available_voices}")
            except Exception as e:
                logger.error(f"Failed to initialize Index-TTS: {e}")
                self.index_tts_model = None
                self.available_voices = ["female", "male", "neutral"]  # Fallback voices
        else:
            logger.warning("Index-TTS not available")
            self.available_voices = ["female", "male", "neutral"]  # Fallback voices
    
    def get_available_voices(self):
        """Get list of available voices from checkpoints directory"""
        try:
            import os
            from pathlib import Path
            
            checkpoints_dir = Path("checkpoints")
            if not checkpoints_dir.exists():
                return ["female", "male", "neutral"]
            
            # Look for voice files or directories
            voices = []
            for item in checkpoints_dir.iterdir():
                if item.is_dir() and any(keyword in item.name.lower() for keyword in ['voice', 'speaker']):
                    voices.append(item.name)
                elif item.is_file() and item.suffix in ['.pt', '.pth', '.ckpt'] and 'voice' in item.name.lower():
                    voices.append(item.stem)
            
            # If no voices found, return default ones
            if not voices:
                voices = ["female", "male", "neutral"]
            
            return voices
        except Exception as e:
            logger.warning(f"Error getting available voices: {e}")
            return ["female", "male", "neutral"]
    
    def generate_speech(self, text: str, output_file: str, voice: str = "female") -> bool:
        """Generate speech from text with enhanced formatting"""
        try:
            # Format text for better TTS output
            formatted_text = TTSTextFormatter.format_for_tts(text)
            
            if self.index_tts_model and voice in self.available_voices:
                # Use Index-TTS with formatted text
                self.index_tts_model.infer(voice, formatted_text, output_file)
                logger.info(f"Speech generated: {output_file}")
                return True
            else:
                # Fallback to system TTS or silence
                logger.warning("TTS not available, generating silence")
                # Estimate duration based on word count (average 165 WPM)
                word_count = len(formatted_text.split())
                duration = (word_count / 165) * 60  # More accurate duration estimate
                silence = np.zeros(int(24000 * duration))
                sf.write(output_file, silence, 24000)
                return True
        except Exception as e:
            logger.error(f"Error generating speech: {e}")
            return False

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
    
    async def capture_screenshot(self, url: str, index: int) -> str:
        """Capture screenshot and return file path"""
        try:
            screenshot_file = f"screenshots/screenshot_{index}.png"
            Path("screenshots").mkdir(exist_ok=True)
            
            if self.capture_advanced_screenshot(url, screenshot_file):
                return screenshot_file
            return None
            
        except Exception as e:
            logger.error(f"Error in capture_screenshot: {e}")
            return None
    
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
                
                # Apply scale and pan
                center_x, center_y = width // 2, height // 2
                M = cv2.getRotationMatrix2D((center_x + pan_x, center_y + pan_y), 0, current_scale)
                
                # Apply transformation
                transformed = cv2.warpAffine(img, M, (width, height))
                
                out.write(transformed)
            
            out.release()
            return True
            
        except Exception as e:
            logger.error(f"Error applying Ken Burns effect: {e}")
            return False
    
    async def create_video(self, paragraphs: List[str], links: List[str], output_name: str = None, 
                          resolution: str = "1920x1080", transition_duration: float = 2.0, 
                          voice: str = "female", target_duration: int = None) -> bool:
        """Enhanced video creation with Ken Burns effects and better timing"""
        try:
            if not output_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_name = f"enhanced_video_{timestamp}.mp4"
            
            output_path = Path("videos") / output_name
            output_path.parent.mkdir(exist_ok=True)
            
            if not paragraphs:
                logger.error("No content provided for video creation")
                return False
            
            update_progress("working", "Setting up video generation...", 5, "Initialization")
            
            # Calculate video timing
            total_words = sum(len(p.split()) for p in paragraphs)
            words_per_minute = 150  # Average speaking rate
            estimated_audio_duration = (total_words / words_per_minute) * 60
            
            if target_duration:
                # Adjust paragraphs to fit target duration if specified
                target_audio_duration = max(30, min(target_duration - 10, estimated_audio_duration))
                paragraphs = await self.adjust_content_for_duration(paragraphs, target_audio_duration)
            else:
                target_audio_duration = estimated_audio_duration
            
            # Take screenshots
            update_progress("working", "Capturing screenshots...", 15, "Screenshots")
            screenshots = []
            
            for i, link in enumerate(links[:len(paragraphs)]):
                if link.strip():
                    screenshot_path = await self.screenshot_manager.capture_screenshot(link, i)
                    if screenshot_path:
                        screenshots.append(screenshot_path)
                    else:
                        logger.warning(f"Failed to capture screenshot for: {link}")
                
                progress = 15 + (i + 1) * 25 / len(links)
                update_progress("working", f"Screenshot {i+1}/{len(links)}", progress, "Screenshots")
            
            # Generate audio segments
            update_progress("working", "Generating audio...", 45, "TTS Generation")
            audio_segments = []
            segment_durations = []
            
            for i, paragraph in enumerate(paragraphs):
                audio_file = f"temp_audio_{i}.wav"
                
                if self.tts_manager.generate_speech(paragraph, audio_file, voice):
                    # Get actual audio duration
                    try:
                        import soundfile as sf
                        data, samplerate = sf.read(audio_file)
                        duration = len(data) / samplerate
                        segment_durations.append(duration)
                        audio_segments.append(audio_file)
                    except:
                        # Fallback duration estimation
                        word_count = len(paragraph.split())
                        duration = max(3.0, word_count / 2.5)
                        segment_durations.append(duration)
                        audio_segments.append(audio_file)
                else:
                    logger.warning(f"Failed to generate audio for segment {i}")
                    duration = max(3.0, len(paragraph.split()) / 2.5)
                    segment_durations.append(duration)
                    audio_segments.append(None)
                
                progress = 45 + (i + 1) * 25 / len(paragraphs)
                update_progress("working", f"Audio segment {i+1}/{len(paragraphs)}", progress, "TTS Generation")
            
            # Create video segments with Ken Burns effect
            update_progress("working", "Creating video segments...", 70, "Video Processing")
            video_segments = []
            
            for i, (screenshot, duration) in enumerate(zip(screenshots, segment_durations)):
                if screenshot and Path(screenshot).exists():
                    # Create Ken Burns effect for this segment
                    ken_burns_output = f"temp_ken_burns_{i}.mp4"
                    
                    if self.apply_ken_burns_effect(screenshot, ken_burns_output, duration):
                        video_segments.append(ken_burns_output)
                    else:
                        # Fallback: create static video
                        static_output = f"temp_static_{i}.mp4"
                        if self.create_static_video(screenshot, static_output, duration):
                            video_segments.append(static_output)
                        else:
                            video_segments.append(None)
                else:
                    # Create placeholder video
                    placeholder_output = f"temp_placeholder_{i}.mp4"
                    if self.create_placeholder_video(placeholder_output, duration, paragraphs[i][:100]):
                        video_segments.append(placeholder_output)
                    else:
                        video_segments.append(None)
                
                progress = 70 + (i + 1) * 15 / len(screenshots)
                update_progress("working", f"Video segment {i+1}/{len(screenshots)}", progress, "Video Processing")
            
            # Combine video and audio
            update_progress("working", "Combining video and audio...", 85, "Final Assembly")
            
            success = await self.combine_video_audio_segments(
                video_segments, audio_segments, str(output_path), resolution, transition_duration
            )
            
            # Cleanup temporary files
            self.cleanup_temp_files(audio_segments + video_segments)
            
            if success:
                update_progress("done", f"Video created: {output_name}", 100, "Complete")
                logger.info(f"Enhanced video created successfully: {output_path}")
                return True
            else:
                update_progress("error", "Video creation failed", 0, "Error")
                return False
                
        except Exception as e:
            logger.error(f"Error in enhanced video creation: {e}")
            update_progress("error", f"Video creation failed: {str(e)}", 0, "Error")
            return False
    
    async def adjust_content_for_duration(self, paragraphs: List[str], target_duration: int) -> List[str]:
        """Adjust content to fit target duration"""
        try:
            current_words = sum(len(p.split()) for p in paragraphs)
            words_per_minute = 150
            current_duration = (current_words / words_per_minute) * 60
            
            if abs(current_duration - target_duration) < 10:  # Within 10 seconds
                return paragraphs
            
            target_words = int((target_duration * words_per_minute) / 60)
            
            if current_words > target_words:
                # Trim content
                adjusted_paragraphs = []
                words_used = 0
                
                for paragraph in paragraphs:
                    words_in_paragraph = len(paragraph.split())
                    if words_used + words_in_paragraph <= target_words:
                        adjusted_paragraphs.append(paragraph)
                        words_used += words_in_paragraph
                    else:
                        # Trim the last paragraph to fit
                        remaining_words = target_words - words_used
                        if remaining_words > 10:  # Only add if substantial
                            words = paragraph.split()[:remaining_words]
                            adjusted_paragraphs.append(' '.join(words))
                        break
                
                return adjusted_paragraphs
            else:
                # Content is already shorter than target, return as-is
                return paragraphs
                
        except Exception as e:
            logger.error(f"Error adjusting content duration: {e}")
            return paragraphs
    
    def create_static_video(self, image_path: str, output_path: str, duration: float) -> bool:
        """Create a static video from an image"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                return False
            
            height, width = img.shape[:2]
            fps = 30
            total_frames = int(duration * fps)
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            for _ in range(total_frames):
                out.write(img)
            
            out.release()
            return True
            
        except Exception as e:
            logger.error(f"Error creating static video: {e}")
            return False
    
    def create_placeholder_video(self, output_path: str, duration: float, text: str = "") -> bool:
        """Create a placeholder video with text"""
        try:
            width, height = 1920, 1080
            fps = 30
            total_frames = int(duration * fps)
            
            # Create a simple gradient background
            background = np.zeros((height, width, 3), dtype=np.uint8)
            background[:, :] = [40, 40, 60]  # Dark blue-gray
            
            # Add text if provided
            if text:
                from PIL import Image, ImageDraw, ImageFont
                
                # Convert to PIL for text rendering
                pil_image = Image.fromarray(cv2.cvtColor(background, cv2.COLOR_BGR2RGB))
                draw = ImageDraw.Draw(pil_image)
                
                try:
                    font_path = get_system_font_path()
                    font = ImageFont.truetype(font_path, 48)
                except:
                    font = ImageFont.load_default()
                
                # Wrap text
                words = text.split()
                lines = []
                current_line = []
                
                for word in words:
                    current_line.append(word)
                    line_text = ' '.join(current_line)
                    
                    bbox = draw.textbbox((0, 0), line_text, font=font)
                    line_width = bbox[2] - bbox[0]
                    
                    if line_width > width - 200:  # Leave margin
                        if len(current_line) > 1:
                            current_line.pop()
                            lines.append(' '.join(current_line))
                            current_line = [word]
                        else:
                            lines.append(line_text)
                            current_line = []
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                # Draw text lines
                y_offset = height // 2 - (len(lines) * 60) // 2
                for line in lines:
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    x = (width - line_width) // 2
                    
                    draw.text((x, y_offset), line, fill=(255, 255, 255), font=font)
                    y_offset += 60
                
                # Convert back to OpenCV
                background = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            for _ in range(total_frames):
                out.write(background)
            
            out.release()
            return True
            
        except Exception as e:
            logger.error(f"Error creating placeholder video: {e}")
            return False
    
    async def combine_video_audio_segments(self, video_segments: List[str], audio_segments: List[str], 
                                         output_path: str, resolution: str, transition_duration: float) -> bool:
        """Combine video and audio segments using FFmpeg"""
        try:
            import subprocess
            
            # Create input list for FFmpeg
            video_list_path = "temp_video_list.txt"
            audio_list_path = "temp_audio_list.txt"
            
            # Prepare video list
            with open(video_list_path, 'w') as f:
                for video_file in video_segments:
                    if video_file and Path(video_file).exists():
                        f.write(f"file '{video_file}'\n")
            
            # Prepare audio list
            with open(audio_list_path, 'w') as f:
                for audio_file in audio_segments:
                    if audio_file and Path(audio_file).exists():
                        f.write(f"file '{audio_file}'\n")
            
            # Combine videos
            temp_video = "temp_combined_video.mp4"
            video_cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', video_list_path,
                '-c', 'copy', temp_video
            ]
            
            # Combine audio
            temp_audio = "temp_combined_audio.wav"
            audio_cmd = [
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', audio_list_path,
                '-c', 'copy', temp_audio
            ]
            
            # Run commands
            video_result = subprocess.run(video_cmd, capture_output=True, text=True)
            audio_result = subprocess.run(audio_cmd, capture_output=True, text=True)
            
            if video_result.returncode == 0 and audio_result.returncode == 0:
                # Combine video and audio
                final_cmd = [
                    'ffmpeg', '-y', '-i', temp_video, '-i', temp_audio,
                    '-c:v', 'libx264', '-c:a', 'aac', '-strict', 'experimental',
                    '-shortest', output_path
                ]
                
                final_result = subprocess.run(final_cmd, capture_output=True, text=True)
                
                # Cleanup
                for temp_file in [video_list_path, audio_list_path, temp_video, temp_audio]:
                    if Path(temp_file).exists():
                        Path(temp_file).unlink()
                
                return final_result.returncode == 0
            else:
                logger.error(f"FFmpeg error - Video: {video_result.stderr}, Audio: {audio_result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error combining video and audio: {e}")
            return False
    
    def cleanup_temp_files(self, temp_files: List[str]):
        """Clean up temporary files"""
        for temp_file in temp_files:
            if temp_file and Path(temp_file).exists():
                try:
                    Path(temp_file).unlink()
                except Exception as e:
                    logger.warning(f"Could not delete temp file {temp_file}: {e}")

# Application instances
app = FastAPI(
    title="GleamVideo Enhanced",
    description="AI-Powered Video Generation Platform",
    version="2.0.0"
)

# Initialize global instances
auto_mode_manager = AutoModeManager()
video_generator = EnhancedVideoGenerator()

# Configure middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Mount static files
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

def update_progress(status: str, message: str, pct: float, current_task: str = ""):
    """Update global progress state"""
    global progress_data
    progress_data.update({
        "status": status,
        "message": message,
        "pct": max(0, min(100, pct)),
        "current_task": current_task
    })
    logger.info(f"Progress: {pct:.1f}% - {message}")

# ---------------------------------------------------------------------------
# AI Integration with Gemini
# ---------------------------------------------------------------------------
class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.model = "google/gemini-2.5-flash"
    
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
    
    async def generate_reddit_reaction(self, reddit_content: Dict, target_length: int = 180) -> str:
        """Generate a reaction/commentary video script for Reddit content"""
        
        # Enhanced system prompts based on personality
        personality_prompts = {
            "sarcastic_reviewer": """You are a sarcastic, witty content reviewer who reacts to Reddit posts. 
            You're not afraid to be a bit vulgar (but not overly offensive) and use humor to engage viewers.
            You point out absurdities, make clever observations, and aren't afraid to call out bullshit when you see it.
            Keep your reactions authentic and entertaining. Use natural speech patterns that work well with text-to-speech.
            Avoid hard-to-pronounce words and use contractions that sound natural when spoken.""",
            
            "enthusiastic_commentator": """You are an enthusiastic, energetic commentator who gets excited about Reddit content.
            You're funny, a bit edgy, and love to share your genuine reactions. You use casual language and aren't afraid
            to be a bit crude when it fits. Your goal is to entertain while providing actual commentary on the content.""",
            
            "analytical_roaster": """You are someone who deeply analyzes Reddit content but with a humorous, roasting twist.
            You're intelligent but not pretentious, funny but not trying too hard. You call out logical fallacies,
            point out contradictions, and aren't afraid to use colorful language when the situation calls for it."""
        }
        
        system_prompt = personality_prompts.get(app_config.reaction_personality, personality_prompts["sarcastic_reviewer"])
        
        # Calculate target word count (roughly 150-180 words per minute of speech)
        target_words = (target_length // 60) * 165
        
        content_prompt = f"""
        React to this Reddit post from r/{app_config.target_subreddit}:
        
        Title: {reddit_content.get('title', 'No title')}
        Content: {reddit_content.get('content', reddit_content.get('summary', 'No content'))}
        
        Create a {target_length}-second reaction video script (approximately {target_words} words).
        
        Your reaction should:
        1. Actually READ and respond to the specific content (don't just summarize)
        2. Include your genuine thoughts and opinions
        3. Be entertaining and engaging
        4. Use natural speech that sounds good with text-to-speech
        5. Include some humor and personality
        6. Feel like a real person reacting, not a robot reading
        7. Point out interesting details or issues with the content
        8. Be conversational and authentic
        
        Avoid:
        - Just reading the content back
        - Being overly polite or corporate
        - Using complex words that are hard to pronounce
        - Generic reactions that could apply to any post
        
        Write this as a natural monologue, like you're talking to a friend about what you just read.
        """
        
        return await self.generate_content(content_prompt, system_prompt)
    
    async def generate_timed_content(self, content: str, target_duration: int) -> List[str]:
        """Break content into time-appropriate segments"""
        
        # Estimate words per minute for speech (average 150-180 WPM)
        words_per_minute = 165
        target_words = (target_duration // 60) * words_per_minute
        
        # If content is too short, expand it
        if len(content.split()) < target_words * 0.8:
            expansion_prompt = f"""
            Take this content and expand it to approximately {target_words} words while maintaining 
            the same tone and style. Add more details, examples, and natural commentary:
            
            {content}
            
            Make sure the expansion feels natural and doesn't just add filler words.
            """
            content = await self.generate_content(expansion_prompt)
        
        # Break into segments of roughly 30-45 seconds each
        words = content.split()
        segment_size = words_per_minute // 2  # ~30 seconds worth of words
        
        segments = []
        for i in range(0, len(words), segment_size):
            segment = " ".join(words[i:i + segment_size])
            if segment.strip():
                segments.append(segment.strip())
        
        return segments

# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------
class AutoModeConfig(BaseModel):
    interval_hours: int = 1
    rss_feeds: List[str] = []
    voice: str = "female"

class APIKeyConfig(BaseModel):
    openrouter_api_key: str

# ---------------------------------------------------------------------------
# Enhanced UI Routes
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the enhanced video generation interface"""
    try:
        html_content = open("index.html", "r").read()
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error serving index page: {e}")
        return HTMLResponse(content="<h1>Error loading page</h1>", status_code=500)

# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.post("/api/set-api-key")
async def set_api_key(config: APIKeyConfig):
    """Set OpenRouter API key"""
    try:
        app_config.openrouter_api_key = config.openrouter_api_key
        return {"success": True, "message": "API key set successfully"}
    except Exception as e:
        logger.error(f"Error setting API key: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-mode/configure")
async def configure_auto_mode(config: AutoModeConfig):
    """Configure automated video generation"""
    try:
        # Stop current auto mode if running
        if auto_mode_manager.is_running:
            auto_mode_manager.stop_auto_mode()
        
        # Update configuration
        app_config.auto_mode_interval = config.interval_hours * 3600
        
        # Update RSS feeds if provided
        if config.rss_feeds:
            app_config.reddit_rss_feeds = config.rss_feeds
        
        # Update voice if provided
        if config.voice:
            app_config.auto_mode_voice = config.voice
        
        # Mark auto mode as configured
        app_config.auto_mode_enabled = True
        
        return {"success": True, "message": "Auto mode configured successfully"}
        
    except Exception as e:
        logger.error(f"Error configuring auto mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-mode/start")
async def start_auto_mode():
    """Start automated video generation"""
    try:
        if not app_config.openrouter_api_key:
            raise HTTPException(status_code=400, detail="OpenRouter API key required")
        
        if not app_config.auto_mode_enabled:
            raise HTTPException(status_code=400, detail="Auto mode not configured")
        
        success = await auto_mode_manager.start_auto_mode()
        
        if success:
            return {"success": True, "message": "Auto mode started"}
        else:
            raise HTTPException(status_code=500, detail="Failed to start auto mode")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting auto mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auto-mode/stop")
async def stop_auto_mode():
    """Stop automated video generation"""
    try:
        auto_mode_manager.stop_auto_mode()
        app_config.auto_mode_enabled = False
        return {"success": True, "message": "Auto mode stopped"}
        
    except Exception as e:
        logger.error(f"Error stopping auto mode: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auto-mode/status")
async def get_auto_mode_status():
    """Get auto mode status"""
    return {
        "running": auto_mode_manager.is_running,
        "enabled": app_config.auto_mode_enabled,
        "last_run": auto_mode_manager.last_run_time.isoformat() if auto_mode_manager.last_run_time else None,
        "interval_hours": app_config.auto_mode_interval // 3600
    }

@app.get("/api/voices/list")
async def list_voices():
    """Get list of available TTS voices"""
    try:
        if hasattr(video_generator, 'tts_manager') and video_generator.tts_manager:
            voices = video_generator.tts_manager.available_voices
        else:
            voices = ["female", "male", "neutral"]  # Default fallback
        
        return {"voices": voices}
        
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        return {"voices": ["female", "male", "neutral"]}

@app.post("/api/config/reddit")
async def configure_reddit_settings(request: Request):
    """Configure Reddit video generation settings"""
    try:
        config = await request.json()
        
        # Update configuration
        app_config.target_subreddit = config['target_subreddit']
        
        # Update video length target
        app_config.video_length_target = max(30, min(3600, config['video_length_target']))
        
        # Update commentary style
        app_config.commentary_style = config['commentary_style']
        
        # Update reaction personality
        app_config.reaction_personality = config['reaction_personality']
        
        # Update specific Reddit posts
        app_config.specific_reddit_posts = config['specific_reddit_posts']
        
        return {"success": True, "message": "Reddit settings updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating Reddit config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/reddit")
async def get_reddit_settings():
    """Get current Reddit video generation settings"""
    return {
        "target_subreddit": getattr(app_config, 'target_subreddit', 'technology'),
        "video_length_target": getattr(app_config, 'video_length_target', 180),
        "commentary_style": getattr(app_config, 'commentary_style', 'funny_vulgar'),
        "reaction_personality": getattr(app_config, 'reaction_personality', 'sarcastic_reviewer'),
        "specific_reddit_posts": getattr(app_config, 'specific_reddit_posts', [])
    }

@app.get("/api/videos/list")
async def list_videos():
    """List generated videos"""
    try:
        videos_dir = Path("videos")
        videos_dir.mkdir(exist_ok=True)
        
        videos = []
        for video_file in videos_dir.glob("*.mp4"):
            try:
                stat = video_file.stat()
                videos.append({
                    "filename": video_file.name,
                    "size": stat.st_size,
                    "created": stat.st_ctime,
                    "url": f"/videos/{video_file.name}"
                })
            except Exception as e:
                logger.warning(f"Error getting info for {video_file}: {e}")
        
        # Sort by creation time, newest first
        videos.sort(key=lambda x: x["created"], reverse=True)
        
        return {"videos": videos}
        
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        return {"videos": []}

@app.get("/videos/download/{filename}")
async def download_video(filename: str):
    """Download a specific video file"""
    try:
        video_path = Path("videos") / filename
        if not video_path.exists():
            raise HTTPException(status_code=404, detail="Video not found")
        
        return FileResponse(
            path=str(video_path),
            media_type="video/mp4",
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading video {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
async def generate_video(request: Request, background_tasks: BackgroundTasks):
    """Generate video from paragraphs and links"""
    try:
        data = await request.json()
        
        paragraphs = data.get("paragraphs", [])
        links = data.get("links", [])
        resolution = data.get("resolution", "1920x1080")
        voice = data.get("voice", "female")
        
        # Clean and validate inputs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        links = [l.strip() for l in links if l.strip()]
        
        if not paragraphs:
            raise HTTPException(status_code=400, detail="At least one paragraph is required")
        
        # Start video generation in background
        background_tasks.add_task(
            video_generator.create_video,
            paragraphs=paragraphs,
            links=links,
            resolution=resolution,
            voice=voice
        )
        
        return {"success": True, "message": "Video generation started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting video generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-reddit-reaction")
async def generate_reddit_reaction(request: Request, background_tasks: BackgroundTasks):
    """Generate a Reddit reaction video"""
    try:
        data = await request.json()
        
        reddit_url = data.get("reddit_url", "").strip()
        video_length = data.get("video_length", 180)
        voice = data.get("voice", "female")
        
        if not reddit_url:
            raise HTTPException(status_code=400, detail="Reddit URL is required")
        
        if not app_config.openrouter_api_key:
            raise HTTPException(status_code=400, detail="OpenRouter API key is required")
        
        # Start generation in background
        background_tasks.add_task(
            generate_specific_reddit_reaction,
            reddit_url=reddit_url,
            video_length=video_length,
            voice=voice
        )
        
        return {"success": True, "message": "Reddit reaction video generation started"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting Reddit reaction generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/progress")
async def get_progress():
    """Get current video generation progress"""
    return progress_data

# ---------------------------------------------------------------------------
# Main Application Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    
    # Create required directories
    Path("videos").mkdir(exist_ok=True)
    Path("screenshots").mkdir(exist_ok=True)
    Path("temp").mkdir(exist_ok=True)
    
    logger.info("Starting GleamVideo Enhanced Server...")
    logger.info("Access the application at: http://localhost:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )