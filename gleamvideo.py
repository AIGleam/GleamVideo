import os
import sys
import logging
import tempfile
import subprocess
import aiohttp
import uvicorn
import asyncio
import json
import random
import re
import io
import time
import feedparser
from datetime import datetime, timedelta
from typing import Optional, List, Union, Tuple, Dict, Any
from pathlib import Path

import numpy as np
import cv2
import pytz
from fastapi import FastAPI, Request, UploadFile, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from PIL import Image
import openai

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------------------------
# Enhanced Logging with color
# ---------------------------------------------------------------------------
class ColorFormatter(logging.Formatter):
    grey = "\x1b[38;21m"
    blue = "\x1b[34;21m"
    green = "\x1b[32;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    fmt_str = "%(asctime)s - %(levelname)s - %(message)s"
    FORMATS = {
        logging.DEBUG: grey + fmt_str + reset,
        logging.INFO: blue + fmt_str + reset,
        logging.WARNING: yellow + fmt_str + reset,
        logging.ERROR: red + fmt_str + reset,
        logging.CRITICAL: bold_red + fmt_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.fmt_str)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ColorFormatter())
logger.addHandler(console_handler)

file_handler = logging.FileHandler('app.log')
file_handler.setFormatter(ColorFormatter())
logger.addHandler(file_handler)

# ---------------------------------------------------------------------------
# Configuration and Global State
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
    
    async def generate_content(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate content using Gemini 2.5 Flash through OpenRouter"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "GleamVideo AI Generator"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
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
                        return f"Error: API request failed with status {response.status}"
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            return f"Error: {str(e)}"

# ---------------------------------------------------------------------------
# Reddit RSS Feed Parser
# ---------------------------------------------------------------------------
class RedditRSSParser:
    def __init__(self):
        self.feeds = app_config.reddit_rss_feeds
    
    async def fetch_trending_topics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch trending topics from Reddit RSS feeds"""
        topics = []
        
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                subreddit = feed_url.split('/r/')[1].split('/')[0]
                
                for entry in feed.entries[:limit]:
                    topics.append({
                        'title': entry.title,
                        'link': entry.link,
                        'summary': entry.summary if hasattr(entry, 'summary') else '',
                        'published': entry.published if hasattr(entry, 'published') else '',
                        'subreddit': subreddit,
                        'score': random.randint(100, 5000)  # Simulated score
                    })
            except Exception as e:
                logger.error(f"Error fetching RSS feed {feed_url}: {e}")
        
        # Sort by simulated score and return top items
        topics.sort(key=lambda x: x['score'], reverse=True)
        return topics[:limit]
    
    async def select_best_topic(self, topics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select the best topic for video creation using AI"""
        if not topics:
            return None
        
        if not app_config.openrouter_api_key:
            # Fallback to random selection
            return random.choice(topics)
        
        gemini = GeminiClient(app_config.openrouter_api_key)
        
        topics_text = "\n".join([
            f"{i+1}. {topic['title']} (r/{topic['subreddit']}) - Score: {topic['score']}"
            for i, topic in enumerate(topics[:5])
        ])
        
        prompt = f"""
        Select the best topic from these Reddit posts for creating an engaging video:
        
        {topics_text}
        
        Consider:
        - Visual potential (can we find good images/screenshots?)
        - Audience engagement potential
        - Current relevance
        - Educational value
        
        Respond with just the number (1-5) of the best topic.
        """
        
        try:
            response = await gemini.generate_content(prompt, max_tokens=10)
            selection = int(response.strip())
            if 1 <= selection <= len(topics):
                return topics[selection - 1]
        except:
            pass
        
        # Fallback to first topic
        return topics[0]

# ---------------------------------------------------------------------------
# Enhanced Screenshot Capture
# ---------------------------------------------------------------------------
class EnhancedScreenshotCapture:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup headless Firefox driver for background operation"""
        try:
            options = FirefoxOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # Firefox preferences for media and privacy
            options.set_preference('media.navigator.permission.disabled', True)
            options.set_preference('dom.webnotifications.enabled', False)
            options.set_preference('dom.push.enabled', False)
            options.set_preference('geo.enabled', False)
            
            service = FirefoxService()
            self.driver = webdriver.Firefox(service=service, options=options)
            logger.info("Firefox driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firefox driver: {e}")
            # Fallback to Chrome
            self.setup_chrome_driver()
    
    def setup_chrome_driver(self):
        """Fallback Chrome driver setup"""
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            prefs = {
                'profile.default_content_setting_values.notifications': 2,
                'profile.default_content_settings.popups': 0,
                'profile.managed_default_content_settings.images': 1,
                'profile.default_content_setting_values.media_stream': 2,
            }
            options.add_experimental_option('prefs', prefs)
            
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("Chrome driver initialized as fallback")
        except Exception as e:
            logger.error(f"Failed to initialize any webdriver: {e}")
            self.driver = None
    
    async def capture_url_screenshot(self, url: str, filename: str = None) -> str:
        """Capture screenshot of a URL and return the file path"""
        if not self.driver:
            raise Exception("No webdriver available")
        
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            await asyncio.sleep(3)
            
            # Take screenshot
            if not filename:
                filename = f"screenshot_{int(time.time())}.png"
            
            screenshot_path = os.path.join("screenshots", filename)
            os.makedirs("screenshots", exist_ok=True)
            
            self.driver.save_screenshot(screenshot_path)
            logger.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Error capturing screenshot for {url}: {e}")
            raise
    
    async def capture_multiple_angles(self, url: str, count: int = 3) -> List[str]:
        """Capture multiple screenshots with different scroll positions"""
        screenshots = []
        
        if not self.driver:
            return screenshots
        
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page height
            page_height = self.driver.execute_script("return document.body.scrollHeight")
            viewport_height = self.driver.execute_script("return window.innerHeight")
            
            for i in range(count):
                # Calculate scroll position
                scroll_position = (page_height - viewport_height) * (i / (count - 1)) if count > 1 else 0
                
                # Scroll to position
                self.driver.execute_script(f"window.scrollTo(0, {scroll_position})")
                await asyncio.sleep(2)  # Wait for scroll
                
                # Take screenshot
                filename = f"screenshot_{int(time.time())}_{i}.png"
                screenshot_path = os.path.join("screenshots", filename)
                os.makedirs("screenshots", exist_ok=True)
                
                self.driver.save_screenshot(screenshot_path)
                screenshots.append(screenshot_path)
                logger.info(f"Screenshot {i+1}/{count} saved: {screenshot_path}")
                
        except Exception as e:
            logger.error(f"Error capturing multiple screenshots: {e}")
        
        return screenshots
    
    def cleanup(self):
        """Clean up the webdriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Webdriver cleaned up")
            except:
                pass

# ---------------------------------------------------------------------------
# AI Video Content Generator
# ---------------------------------------------------------------------------
class VideoContentGenerator:
    def __init__(self, gemini_client: GeminiClient):
        self.gemini = gemini_client
    
    async def generate_video_idea(self, topic: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a comprehensive video idea from a topic"""
        prompt = f"""
        Create a compelling video concept based on this Reddit post:
        
        Title: {topic['title']}
        Subreddit: r/{topic['subreddit']}
        Summary: {topic.get('summary', 'No summary available')}
        
        Generate a video idea that includes:
        1. A catchy video title (YouTube-optimized)
        2. A hook for the first 10 seconds
        3. Main content structure (3-5 key points)
        4. A strong conclusion/call-to-action
        
        Format your response as JSON:
        {{
            "video_title": "Your catchy title here",
            "hook": "Opening hook that grabs attention",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "conclusion": "Strong ending with call-to-action",
            "estimated_duration": "2-3 minutes"
        }}
        """
        
        try:
            response = await self.gemini.generate_content(prompt, max_tokens=1000)
            
            # Try to parse JSON response
            try:
                content = json.loads(response)
                return content
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "video_title": topic['title'][:60] + "...",
                    "hook": "Here's something interesting from Reddit...",
                    "key_points": ["Main topic discussion", "Key insights", "Why this matters"],
                    "conclusion": "What do you think? Let me know in the comments!",
                    "estimated_duration": "2-3 minutes"
                }
        except Exception as e:
            logger.error(f"Error generating video idea: {e}")
            return None
    
    async def generate_script_with_timing(self, video_idea: Dict[str, Any], topic: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a detailed script with timing and screenshot cues"""
        prompt = f"""
        Create a detailed video script based on this video idea:
        
        Video Title: {video_idea['video_title']}
        Hook: {video_idea['hook']}
        Key Points: {', '.join(video_idea['key_points'])}
        Conclusion: {video_idea['conclusion']}
        
        Original Topic: {topic['title']}
        Source URL: {topic['link']}
        
        Create a script with:
        1. Exact narration text for each segment
        2. Timing for each segment (aim for 2-3 minutes total)
        3. Visual cues for when to show screenshots or specific images
        4. Natural transitions between segments
        
        Format as JSON:
        {{
            "segments": [
                {{
                    "text": "Narration text for this segment",
                    "duration": 15,
                    "visual_cue": "Screenshot of main Reddit post",
                    "screenshot_url": "URL to capture if needed"
                }}
            ],
            "total_duration": 180
        }}
        
        Make the narration conversational and engaging, like a popular YouTuber.
        """
        
        try:
            response = await self.gemini.generate_content(prompt, max_tokens=2000)
            
            try:
                script = json.loads(response)
                
                # Validate and ensure we have screenshot URLs
                for segment in script.get('segments', []):
                    if not segment.get('screenshot_url'):
                        segment['screenshot_url'] = topic['link']  # Default to main URL
                
                return script
            except json.JSONDecodeError:
                # Fallback script
                return {
                    "segments": [
                        {
                            "text": video_idea['hook'],
                            "duration": 10,
                            "visual_cue": "Opening screenshot",
                            "screenshot_url": topic['link']
                        },
                        {
                            "text": f"Let's dive into this interesting topic from r/{topic['subreddit']}.",
                            "duration": 30,
                            "visual_cue": "Main content screenshot",
                            "screenshot_url": topic['link']
                        },
                        {
                            "text": video_idea['conclusion'],
                            "duration": 15,
                            "visual_cue": "Conclusion screenshot",
                            "screenshot_url": topic['link']
                        }
                    ],
                    "total_duration": 55
                }
        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return None

# ---------------------------------------------------------------------------
# Enhanced TTS with Kokoro
# ---------------------------------------------------------------------------
VOICE_COMMAND = "./kokoro-tts"
DEFAULT_VOICE = "am_adam"
DEFAULT_LANGUAGE = "en-us"
DEFAULT_SPEED = 1.2

def generate_tts_kokoro(script_text: str, output_file: str, return_duration: bool = False) -> Union[bool, Tuple[bool, float]]:
    """Generate TTS using Kokoro TTS with enhanced error handling"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tmpf:
            tmpf.write(script_text)
            temp_text_path = tmpf.name

        cmd = [
            VOICE_COMMAND,
            temp_text_path,
            output_file,
            "--speed", str(DEFAULT_SPEED),
            "--lang", DEFAULT_LANGUAGE,
            "--voice", DEFAULT_VOICE
        ]

        logger.info(f"Running TTS command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        # Clean up temp file
        try:
            os.unlink(temp_text_path)
        except:
            pass

        if result.returncode == 0:
            if os.path.exists(output_file):
                logger.info(f"TTS generated successfully: {output_file}")
                
                if return_duration:
                    # Calculate duration from audio file
                    duration = get_audio_duration(output_file)
                    return True, duration
                return True
            else:
                logger.error("TTS command succeeded but output file not found")
                return (False, 0.0) if return_duration else False
        else:
            logger.error(f"TTS command failed: {result.stderr}")
            return (False, 0.0) if return_duration else False

    except subprocess.TimeoutExpired:
        logger.error("TTS command timed out")
        return (False, 0.0) if return_duration else False
    except Exception as e:
        logger.error(f"TTS generation error: {e}")
        return (False, 0.0) if return_duration else False

def get_audio_duration(path: str) -> float:
    """Get audio duration using ffprobe"""
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception as e:
        logger.error(f"Error getting audio duration: {e}")
    return 0.0

# ---------------------------------------------------------------------------
# Enhanced Ken Burns Video Builder
# ---------------------------------------------------------------------------
class EnhancedKenBurnsVideoBuilder:
    def __init__(self, width: int, height: int, fps: int = 60):
        self.width = width
        self.height = height
        self.fps = fps
        self.temp_files = []
        self.screenshot_capture = EnhancedScreenshotCapture()
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
        self.temp_files.clear()
        self.screenshot_capture.cleanup()
    
    async def build_video_from_script(self, script: Dict[str, Any], output_path: str) -> bool:
        """Build video from AI-generated script with screenshots"""
        try:
            segments = script.get('segments', [])
            if not segments:
                logger.error("No segments in script")
                return False
            
            # Create temp directory for this video
            temp_dir = tempfile.mkdtemp(prefix="gleamvideo_")
            video_segments = []
            
            update_progress("working", "Generating audio segments...", 10)
            
            for i, segment in enumerate(segments):
                progress = 10 + (i / len(segments)) * 40
                update_progress("working", f"Processing segment {i+1}/{len(segments)}", progress)
                
                # Generate TTS for this segment
                audio_file = os.path.join(temp_dir, f"segment_{i}_audio.wav")
                success, duration = generate_tts_kokoro(segment['text'], audio_file, return_duration=True)
                
                if not success:
                    logger.error(f"Failed to generate TTS for segment {i}")
                    continue
                
                # Capture screenshot if URL provided
                screenshot_path = None
                if segment.get('screenshot_url'):
                    try:
                        screenshot_path = await self.screenshot_capture.capture_url_screenshot(
                            segment['screenshot_url'],
                            f"segment_{i}_screenshot.png"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to capture screenshot for segment {i}: {e}")
                
                # Create video segment
                video_file = os.path.join(temp_dir, f"segment_{i}_video.mp4")
                if screenshot_path and os.path.exists(screenshot_path):
                    success = await self.create_ken_burns_segment(
                        screenshot_path, audio_file, video_file, duration
                    )
                else:
                    # Create a simple colored background if no screenshot
                    success = await self.create_text_segment(
                        segment['text'][:50] + "...", audio_file, video_file, duration
                    )
                
                if success:
                    video_segments.append(video_file)
                    self.temp_files.extend([audio_file, video_file])
                    if screenshot_path:
                        self.temp_files.append(screenshot_path)
            
            if not video_segments:
                logger.error("No video segments created")
                return False
            
            update_progress("working", "Combining video segments...", 80)
            
            # Combine all segments
            success = await self.combine_video_segments(video_segments, output_path)
            
            if success:
                update_progress("done", f"Video created successfully: {output_path}", 100)
                return True
            else:
                update_progress("error", "Failed to combine video segments", 100)
                return False
                
        except Exception as e:
            logger.error(f"Error building video from script: {e}")
            update_progress("error", f"Video building error: {str(e)}", 100)
            return False
        finally:
            # Cleanup temp directory
            try:
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
    
    async def create_ken_burns_segment(self, image_path: str, audio_path: str, output_path: str, duration: float) -> bool:
        """Create a Ken Burns effect video segment"""
        try:
            # Load and prepare image
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"Could not load image: {image_path}")
                return False
            
            # Resize image to fit video dimensions while maintaining aspect ratio
            img = self.fit_image_to_dimensions(img)
            
            # Create video with Ken Burns effect
            temp_video = tempfile.mktemp(suffix='.mp4')
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_video, fourcc, self.fps, (self.width, self.height))
            
            total_frames = int(duration * self.fps)
            
            for frame_num in range(total_frames):
                progress = frame_num / total_frames
                
                # Apply Ken Burns effect (slow zoom and pan)
                ken_burns_frame = self.apply_ken_burns_effect(img, progress, zoom_in=True)
                out.write(ken_burns_frame)
            
            out.release()
            
            # Combine with audio
            success = await self.combine_video_with_audio(temp_video, audio_path, output_path)
            
            # Cleanup
            try:
                os.unlink(temp_video)
            except:
                pass
            
            return success
            
        except Exception as e:
            logger.error(f"Error creating Ken Burns segment: {e}")
            return False
    
    async def create_text_segment(self, text: str, audio_path: str, output_path: str, duration: float) -> bool:
        """Create a simple text-based video segment as fallback"""
        try:
            # Create a simple colored background with text
            temp_video = tempfile.mktemp(suffix='.mp4')
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_video, fourcc, self.fps, (self.width, self.height))
            
            total_frames = int(duration * self.fps)
            
            # Create background
            background_color = (20, 30, 50)  # Dark blue
            frame = np.full((self.height, self.width, 3), background_color, dtype=np.uint8)
            
            # Add text (simplified - you might want to use PIL for better text rendering)
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 2
            color = (255, 255, 255)
            thickness = 3
            
            # Simple text wrapping
            words = text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                (text_width, text_height), _ = cv2.getTextSize(test_line, font, font_scale, thickness)
                
                if text_width < self.width - 100:  # Leave margin
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
            
            # Add text to frame
            y_start = (self.height - len(lines) * 60) // 2
            for i, line in enumerate(lines):
                (text_width, text_height), _ = cv2.getTextSize(line, font, font_scale, thickness)
                x = (self.width - text_width) // 2
                y = y_start + i * 60
                cv2.putText(frame, line, (x, y), font, font_scale, color, thickness)
            
            # Write all frames
            for _ in range(total_frames):
                out.write(frame)
            
            out.release()
            
            # Combine with audio
            success = await self.combine_video_with_audio(temp_video, audio_path, output_path)
            
            # Cleanup
            try:
                os.unlink(temp_video)
            except:
                pass
            
            return success
            
        except Exception as e:
            logger.error(f"Error creating text segment: {e}")
            return False
    
    def fit_image_to_dimensions(self, img: np.ndarray) -> np.ndarray:
        """Fit image to video dimensions while maintaining aspect ratio"""
        img_height, img_width = img.shape[:2]
        
        # Calculate scaling to fit the image within video dimensions
        scale_x = self.width / img_width
        scale_y = self.height / img_height
        scale = max(scale_x, scale_y)  # Scale to fill the frame
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize image
        img_resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        
        # Center crop to video dimensions
        start_x = (new_width - self.width) // 2
        start_y = (new_height - self.height) // 2
        
        # Ensure we don't go out of bounds
        start_x = max(0, start_x)
        start_y = max(0, start_y)
        end_x = min(new_width, start_x + self.width)
        end_y = min(new_height, start_y + self.height)
        
        cropped = img_resized[start_y:end_y, start_x:end_x]
        
        # If the cropped image is smaller than target, pad it
        if cropped.shape[0] < self.height or cropped.shape[1] < self.width:
            padded = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            y_offset = (self.height - cropped.shape[0]) // 2
            x_offset = (self.width - cropped.shape[1]) // 2
            padded[y_offset:y_offset+cropped.shape[0], x_offset:x_offset+cropped.shape[1]] = cropped
            return padded
        
        return cropped
    
    def apply_ken_burns_effect(self, img: np.ndarray, progress: float, zoom_in: bool = True) -> np.ndarray:
        """Apply Ken Burns effect (zoom and pan) to an image"""
        height, width = img.shape[:2]
        
        # Zoom parameters
        zoom_start = 1.0
        zoom_end = 1.3
        
        if not zoom_in:
            zoom_start, zoom_end = zoom_end, zoom_start
        
        current_zoom = zoom_start + (zoom_end - zoom_start) * progress
        
        # Calculate new dimensions
        new_width = int(width * current_zoom)
        new_height = int(height * current_zoom)
        
        # Resize image
        zoomed = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        
        # Pan parameters (gentle movement)
        pan_x = int((new_width - self.width) * progress * 0.3)  # Move 30% across
        pan_y = int((new_height - self.height) * progress * 0.2)  # Move 20% down
        
        # Ensure we don't go out of bounds
        pan_x = max(0, min(pan_x, new_width - self.width))
        pan_y = max(0, min(pan_y, new_height - self.height))
        
        # Extract the final frame
        result = zoomed[pan_y:pan_y + self.height, pan_x:pan_x + self.width]
        
        # Ensure correct dimensions
        if result.shape[0] != self.height or result.shape[1] != self.width:
            result = cv2.resize(result, (self.width, self.height))
        
        return result
    
    async def combine_video_with_audio(self, video_path: str, audio_path: str, output_path: str) -> bool:
        """Combine video with audio using ffmpeg"""
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-shortest',
                '-preset', 'fast',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully combined video and audio: {output_path}")
                return True
            else:
                logger.error(f"ffmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error combining video and audio: {e}")
            return False
    
    async def combine_video_segments(self, video_paths: List[str], output_path: str) -> bool:
        """Combine multiple video segments into one video"""
        try:
            if len(video_paths) == 1:
                # If only one segment, just copy it
                import shutil
                shutil.copy2(video_paths[0], output_path)
                return True
            
            # Create concat file for ffmpeg
            concat_file = tempfile.mktemp(suffix='.txt')
            with open(concat_file, 'w') as f:
                for video_path in video_paths:
                    f.write(f"file '{os.path.abspath(video_path)}'\n")
            
            self.temp_files.append(concat_file)
            
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Successfully combined video segments: {output_path}")
                return True
            else:
                logger.error(f"ffmpeg concat error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error combining video segments: {e}")
            return False

# ---------------------------------------------------------------------------
# Auto Mode Manager
# ---------------------------------------------------------------------------
class AutoModeManager:
    def __init__(self):
        self.running = False
        self.last_run = None
        self.rss_parser = RedditRSSParser()
        self.content_generator = None
    
    async def start_auto_mode(self):
        """Start auto mode background task"""
        if not app_config.openrouter_api_key:
            logger.error("Cannot start auto mode without OpenRouter API key")
            return False
        
        self.content_generator = VideoContentGenerator(GeminiClient(app_config.openrouter_api_key))
        self.running = True
        progress_data["auto_mode"] = True
        
        logger.info("Auto mode started")
        
        # Run immediately and then schedule periodic runs
        asyncio.create_task(self.auto_mode_loop())
        return True
    
    def stop_auto_mode(self):
        """Stop auto mode"""
        self.running = False
        progress_data["auto_mode"] = False
        logger.info("Auto mode stopped")
    
    async def auto_mode_loop(self):
        """Main auto mode loop"""
        while self.running:
            try:
                await self.run_auto_generation()
                progress_data["last_auto_run"] = datetime.now().isoformat()
                
                # Wait for next interval
                await asyncio.sleep(app_config.auto_mode_interval)
                
            except Exception as e:
                logger.error(f"Error in auto mode loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def run_auto_generation(self):
        """Run one cycle of auto video generation"""
        try:
            update_progress("working", "Auto mode: Fetching trending topics...", 5, "Auto Generation")
            
            # Fetch trending topics
            topics = await self.rss_parser.fetch_trending_topics(10)
            if not topics:
                logger.warning("No topics found from RSS feeds")
                return
            
            # Select best topic
            update_progress("working", "Auto mode: Selecting best topic...", 15, "Auto Generation")
            selected_topic = await self.rss_parser.select_best_topic(topics)
            if not selected_topic:
                logger.warning("No topic selected")
                return
            
            logger.info(f"Selected topic: {selected_topic['title']}")
            
            # Generate video idea
            update_progress("working", "Auto mode: Generating video idea...", 25, "Auto Generation")
            video_idea = await self.content_generator.generate_video_idea(selected_topic)
            if not video_idea:
                logger.warning("Failed to generate video idea")
                return
            
            # Generate script with timing
            update_progress("working", "Auto mode: Creating script...", 35, "Auto Generation")
            script = await self.content_generator.generate_script_with_timing(video_idea, selected_topic)
            if not script:
                logger.warning("Failed to generate script")
                return
            
            # Generate video
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"auto_video_{timestamp}.mp4"
            output_path = os.path.join("videos", output_name)
            os.makedirs("videos", exist_ok=True)
            
            update_progress("working", "Auto mode: Building video...", 45, "Auto Generation")
            
            video_builder = EnhancedKenBurnsVideoBuilder(1920, 1080, 60)
            try:
                success = await video_builder.build_video_from_script(script, output_path)
                
                if success:
                    logger.info(f"Auto video generated successfully: {output_path}")
                    update_progress("done", f"Auto video created: {output_name}", 100, "Auto Generation")
                else:
                    logger.error("Failed to build auto video")
                    update_progress("error", "Auto video generation failed", 100, "Auto Generation")
            finally:
                video_builder.cleanup_temp_files()
                
        except Exception as e:
            logger.error(f"Error in auto generation: {e}")
            update_progress("error", f"Auto generation error: {str(e)}", 100, "Auto Generation")

# Global auto mode manager
auto_mode_manager = AutoModeManager()

# ---------------------------------------------------------------------------
# FastAPI App Setup
# ---------------------------------------------------------------------------
app = FastAPI(title="GleamVideo Enhanced", description="AI-Powered Video Generator with Auto Mode")

# Create necessary directories
os.makedirs("videos", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)
os.makedirs("static", exist_ok=True)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/screenshots", StaticFiles(directory="screenshots"), name="screenshots")

# ---------------------------------------------------------------------------
# API Models
# ---------------------------------------------------------------------------
class VideoGenerationRequest(BaseModel):
    paragraphs: List[str]
    links: List[str] = []
    output_name: str = ""
    resolution: str = "1920x1080"
    transition_duration: float = 2.0
    timestamps: List[float] = []

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
    html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GleamVideo Enhanced - AI Video Generator</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }

        .navbar {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            padding: 1rem 2rem;
            position: fixed;
            width: 100%;
            top: 0;
            z-index: 1000;
            border-bottom: 1px solid rgba(255, 255, 255, 0.2);
        }

        .navbar h1 {
            color: white;
            font-size: 1.8rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 120px 2rem 2rem;
        }

        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #f0f0f0;
        }

        .card-header i {
            font-size: 1.5rem;
            color: #667eea;
        }

        .card-header h2 {
            color: #333;
            font-size: 1.4rem;
        }

        .form-group {
            margin-bottom: 1.5rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #555;
        }

        .form-control {
            width: 100%;
            padding: 0.8rem;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 1rem;
            transition: all 0.3s ease;
            background: white;
        }

        .form-control:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .btn {
            padding: 0.8rem 1.5rem;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            text-decoration: none;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }

        .btn-success {
            background: linear-gradient(135deg, #56ab2f, #a8e6cf);
            color: white;
        }

        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(86, 171, 47, 0.3);
        }

        .btn-danger {
            background: linear-gradient(135deg, #ff416c, #ff4b2b);
            color: white;
        }

        .btn-danger:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(255, 65, 108, 0.3);
        }

        .btn-secondary {
            background: linear-gradient(135deg, #6c757d, #495057);
            color: white;
        }

        .dynamic-fields {
            display: flex;
            gap: 1rem;
            align-items: end;
            margin-bottom: 1rem;
        }

        .dynamic-fields .form-control {
            flex: 1;
        }

        .progress-container {
            margin-top: 2rem;
            padding: 1.5rem;
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            border-radius: 15px;
            border-left: 4px solid #667eea;
        }

        .progress-bar {
            width: 100%;
            height: 10px;
            background: #e0e0e0;
            border-radius: 5px;
            overflow: hidden;
            margin-top: 1rem;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            width: 0%;
            transition: width 0.3s ease;
        }

        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
        }

        .status-idle {
            background: #f8f9fa;
            color: #6c757d;
        }

        .status-working {
            background: #fff3cd;
            color: #856404;
        }

        .status-done {
            background: #d1edff;
            color: #0c5460;
        }

        .status-error {
            background: #f8d7da;
            color: #721c24;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
        }

        .feature-card {
            text-align: center;
            padding: 2rem;
            border-radius: 15px;
            background: white;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }

        .feature-card:hover {
            transform: translateY(-5px);
        }

        .feature-icon {
            font-size: 3rem;
            color: #667eea;
            margin-bottom: 1rem;
        }

        .auto-mode-panel {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 20px;
            padding: 2rem;
            margin-bottom: 2rem;
        }

        .auto-mode-panel .card-header {
            border-bottom-color: rgba(255, 255, 255, 0.2);
        }

        .auto-mode-panel .card-header h2,
        .auto-mode-panel .card-header i {
            color: white;
        }

        .config-section {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
        }

        .video-list {
            max-height: 400px;
            overflow-y: auto;
        }

        .video-item {
            display: flex;
            justify-content: between;
            align-items: center;
            padding: 1rem;
            background: #f8f9fa;
            border-radius: 10px;
            margin-bottom: 0.5rem;
        }

        .video-item a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }

        .video-item a:hover {
            text-decoration: underline;
        }

        .alert {
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 1rem;
        }

        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border-left: 4px solid #bee5eb;
        }

        .alert-warning {
            background: #fff3cd;
            color: #856404;
            border-left: 4px solid #ffeaa7;
        }

        .floating-help {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
            transition: all 0.3s ease;
        }

        .floating-help:hover {
            transform: scale(1.1);
        }

        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        .pulse {
            animation: pulse 2s infinite;
        }

        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .tooltip {
            position: relative;
            display: inline-block;
        }

        .tooltip .tooltiptext {
            visibility: hidden;
            width: 200px;
            background-color: #333;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.8rem;
        }

        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }

        @media (max-width: 768px) {
            .container {
                padding: 100px 1rem 1rem;
            }
            
            .navbar {
                padding: 1rem;
            }
            
            .card {
                padding: 1rem;
            }
            
            .dynamic-fields {
                flex-direction: column;
                align-items: stretch;
            }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1><i class="fas fa-video"></i> GleamVideo Enhanced</h1>
    </nav>

    <div class="container">
        <!-- Auto Mode Panel -->
        <div class="auto-mode-panel animate__animated animate__fadeInDown">
            <div class="card-header">
                <i class="fas fa-robot"></i>
                <h2>Auto Mode</h2>
            </div>
            
            <div class="config-section">
                <div class="form-group">
                    <label for="openrouter-key">OpenRouter API Key (Required for Auto Mode)</label>
                    <input type="password" id="openrouter-key" class="form-control" placeholder="Enter your OpenRouter API key...">
                </div>
                <button onclick="saveApiKey()" class="btn btn-success">
                    <i class="fas fa-save"></i> Save API Key
                </button>
            </div>

            <div class="config-section">
                <div class="form-group">
                    <label>Auto Mode Status</label>
                    <div id="auto-mode-status" class="status-indicator status-idle">
                        <i class="fas fa-circle"></i> Idle
                    </div>
                </div>
                
                <div class="form-group">
                    <label for="auto-interval">Generation Interval (hours)</label>
                    <input type="number" id="auto-interval" class="form-control" value="1" min="1" max="24">
                </div>
                
                <div style="display: flex; gap: 1rem;">
                    <button onclick="startAutoMode()" class="btn btn-success">
                        <i class="fas fa-play"></i> Start Auto Mode
                    </button>
                    <button onclick="stopAutoMode()" class="btn btn-danger">
                        <i class="fas fa-stop"></i> Stop Auto Mode
                    </button>
                    <button onclick="runAutoNow()" class="btn btn-primary">
                        <i class="fas fa-bolt"></i> Generate Now
                    </button>
                </div>
            </div>
        </div>

        <!-- Manual Generation -->
        <div class="card animate__animated animate__fadeInUp">
            <div class="card-header">
                <i class="fas fa-edit"></i>
                <h2>Manual Video Generation</h2>
            </div>

            <form id="video-form">
                <div class="form-group">
                    <label for="output-name">Video Name</label>
                    <input type="text" id="output-name" class="form-control" placeholder="Enter video name (optional)">
                </div>

                <div class="form-group">
                    <label for="resolution">Resolution</label>
                    <select id="resolution" class="form-control">
                        <option value="1920x1080">1920x1080 (Full HD)</option>
                        <option value="1280x720">1280x720 (HD)</option>
                        <option value="3840x2160">3840x2160 (4K)</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Paragraphs & Content</label>
                    <div id="paragraphs-container">
                        <div class="dynamic-fields">
                            <textarea class="form-control paragraph-input" rows="3" placeholder="Enter paragraph text..."></textarea>
                            <button type="button" onclick="addParagraph()" class="btn btn-primary">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label>Images & URLs</label>
                    <div id="links-container">
                        <div class="dynamic-fields">
                            <input type="text" class="form-control link-input" placeholder="Enter image URL or local path...">
                            <button type="button" onclick="addLink()" class="btn btn-primary">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                </div>

                <div class="form-group">
                    <label for="transition-duration">Transition Duration (seconds)</label>
                    <input type="number" id="transition-duration" class="form-control" value="2" min="0.5" max="10" step="0.5">
                </div>

                <button type="submit" class="btn btn-primary btn-lg">
                    <i class="fas fa-video"></i> Generate Video
                </button>
            </form>
        </div>

        <!-- Progress Panel -->
        <div class="card animate__animated animate__fadeInUp">
            <div class="card-header">
                <i class="fas fa-chart-line"></i>
                <h2>Progress</h2>
            </div>
            
            <div class="progress-container">
                <div id="progress-status" class="status-indicator status-idle">
                    <i class="fas fa-circle"></i> Ready
                </div>
                <div id="progress-message">Ready to generate videos</div>
                <div id="current-task"></div>
                <div class="progress-bar">
                    <div id="progress-fill" class="progress-fill"></div>
                </div>
                <div id="progress-percent">0%</div>
            </div>
        </div>

        <!-- Generated Videos -->
        <div class="card animate__animated animate__fadeInUp">
            <div class="card-header">
                <i class="fas fa-folder"></i>
                <h2>Generated Videos</h2>
            </div>
            
            <div id="videos-list" class="video-list">
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i> Generated videos will appear here
                </div>
            </div>
            
            <button onclick="refreshVideosList()" class="btn btn-secondary">
                <i class="fas fa-refresh"></i> Refresh List
            </button>
        </div>

        <!-- Features Overview -->
        <div class="card animate__animated animate__fadeInUp">
            <div class="card-header">
                <i class="fas fa-star"></i>
                <h2>Features</h2>
            </div>
            
            <div class="grid">
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-robot"></i>
                    </div>
                    <h3>Auto Mode</h3>
                    <p>Automatically generates videos from trending Reddit topics using AI</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-brain"></i>
                    </div>
                    <h3>Gemini 2.5 Flash</h3>
                    <p>Powered by Google's latest AI model for content generation</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-camera"></i>
                    </div>
                    <h3>Smart Screenshots</h3>
                    <p>Automatically captures relevant screenshots with multiple angles</p>
                </div>
                
                <div class="feature-card">
                    <div class="feature-icon">
                        <i class="fas fa-magic"></i>
                    </div>
                    <h3>Ken Burns Effect</h3>
                    <p>Professional video transitions with zoom and pan effects</p>
                </div>
            </div>
        </div>
    </div>

    <div class="floating-help tooltip">
        <i class="fas fa-question"></i>
        <span class="tooltiptext">Need help? Check the documentation!</span>
    </div>

    <script>
        let progressInterval;

        // Initialize the application
        document.addEventListener('DOMContentLoaded', function() {
            startProgressUpdates();
            refreshVideosList();
            updateAutoModeStatus();
        });

        // Form submission
        document.getElementById('video-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            await generateVideo();
        });

        // API Key Management
        function saveApiKey() {
            const apiKey = document.getElementById('openrouter-key').value;
            if (!apiKey) {
                alert('Please enter your OpenRouter API key');
                return;
            }

            fetch('/api/config/api-key', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ openrouter_api_key: apiKey })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('API key saved successfully!');
                    document.getElementById('openrouter-key').value = '';
                } else {
                    alert('Error saving API key: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Error saving API key');
            });
        }

        // Auto Mode Functions
        async function startAutoMode() {
            try {
                const interval = document.getElementById('auto-interval').value;
                const response = await fetch('/api/auto-mode/start', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ interval_hours: parseInt(interval) })
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('Auto mode started successfully!');
                    updateAutoModeStatus();
                } else {
                    alert('Error starting auto mode: ' + data.error);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error starting auto mode');
            }
        }

        async function stopAutoMode() {
            try {
                const response = await fetch('/api/auto-mode/stop', {
                    method: 'POST'
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('Auto mode stopped');
                    updateAutoModeStatus();
                } else {
                    alert('Error stopping auto mode: ' + data.error);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error stopping auto mode');
            }
        }

        async function runAutoNow() {
            try {
                const response = await fetch('/api/auto-mode/run-now', {
                    method: 'POST'
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('Auto generation started!');
                } else {
                    alert('Error starting auto generation: ' + data.error);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error starting auto generation');
            }
        }

        async function updateAutoModeStatus() {
            try {
                const response = await fetch('/api/auto-mode/status');
                const data = await response.json();
                
                const statusElement = document.getElementById('auto-mode-status');
                if (data.running) {
                    statusElement.className = 'status-indicator status-working pulse';
                    statusElement.innerHTML = '<i class="fas fa-circle"></i> Running';
                } else {
                    statusElement.className = 'status-indicator status-idle';
                    statusElement.innerHTML = '<i class="fas fa-circle"></i> Stopped';
                }
            } catch (error) {
                console.error('Error updating auto mode status:', error);
            }
        }

        // Dynamic form fields
        function addParagraph() {
            const container = document.getElementById('paragraphs-container');
            const div = document.createElement('div');
            div.className = 'dynamic-fields';
            div.innerHTML = `
                <textarea class="form-control paragraph-input" rows="3" placeholder="Enter paragraph text..."></textarea>
                <button type="button" onclick="removeParagraph(this)" class="btn btn-danger">
                    <i class="fas fa-minus"></i>
                </button>
            `;
            container.appendChild(div);
        }

        function removeParagraph(button) {
            button.parentElement.remove();
        }

        function addLink() {
            const container = document.getElementById('links-container');
            const div = document.createElement('div');
            div.className = 'dynamic-fields';
            div.innerHTML = `
                <input type="text" class="form-control link-input" placeholder="Enter image URL or local path...">
                <button type="button" onclick="removeLink(this)" class="btn btn-danger">
                    <i class="fas fa-minus"></i>
                </button>
            `;
            container.appendChild(div);
        }

        function removeLink(button) {
            button.parentElement.remove();
        }

        // Video generation
        async function generateVideo() {
            const formData = new FormData();
            
            // Collect paragraphs
            const paragraphs = Array.from(document.querySelectorAll('.paragraph-input'))
                .map(input => input.value)
                .filter(text => text.trim());
            
            if (paragraphs.length === 0) {
                alert('Please add at least one paragraph');
                return;
            }

            // Collect links
            const links = Array.from(document.querySelectorAll('.link-input'))
                .map(input => input.value)
                .filter(text => text.trim());

            // Add form data
            paragraphs.forEach(paragraph => formData.append('paragraphs', paragraph));
            links.forEach(link => formData.append('links', link));
            formData.append('output_name', document.getElementById('output-name').value);
            formData.append('resolution', document.getElementById('resolution').value);
            formData.append('transition_duration', document.getElementById('transition-duration').value);

            try {
                const response = await fetch('/generate_video', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    alert('Video generation started! Check the progress panel.');
                    setTimeout(refreshVideosList, 2000);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error submitting form');
            }
        }

        // Progress updates
        function startProgressUpdates() {
            progressInterval = setInterval(updateProgress, 1000);
        }

        async function updateProgress() {
            try {
                const response = await fetch('/progress?task_id=current');
                const data = await response.json();
                
                const statusElement = document.getElementById('progress-status');
                const messageElement = document.getElementById('progress-message');
                const taskElement = document.getElementById('current-task');
                const fillElement = document.getElementById('progress-fill');
                const percentElement = document.getElementById('progress-percent');

                // Update status indicator
                statusElement.className = `status-indicator status-${data.status}`;
                
                const statusIcons = {
                    idle: 'fas fa-circle',
                    working: 'fas fa-spinner fa-spin',
                    done: 'fas fa-check-circle',
                    error: 'fas fa-exclamation-circle'
                };
                
                const statusTexts = {
                    idle: 'Ready',
                    working: 'Working',
                    done: 'Complete',
                    error: 'Error'
                };

                statusElement.innerHTML = `<i class="${statusIcons[data.status]}"></i> ${statusTexts[data.status]}`;
                
                // Update message and progress
                messageElement.textContent = data.message;
                taskElement.textContent = data.current_task ? `Task: ${data.current_task}` : '';
                fillElement.style.width = `${data.pct}%`;
                percentElement.textContent = `${Math.round(data.pct)}%`;

                // Update auto mode indicator
                if (data.auto_mode !== undefined) {
                    updateAutoModeStatus();
                }

            } catch (error) {
                console.error('Error updating progress:', error);
            }
        }

        // Video list management
        async function refreshVideosList() {
            try {
                const response = await fetch('/api/videos/list');
                const data = await response.json();
                
                const listElement = document.getElementById('videos-list');
                
                if (data.videos && data.videos.length > 0) {
                    listElement.innerHTML = data.videos.map(video => `
                        <div class="video-item">
                            <div>
                                <a href="/videos/${video.name}" target="_blank">
                                    <i class="fas fa-play-circle"></i> ${video.name}
                                </a>
                                <small style="display: block; color: #666;">
                                    Created: ${new Date(video.created).toLocaleString()}
                                    | Size: ${video.size}
                                </small>
                            </div>
                        </div>
                    `).join('');
                } else {
                    listElement.innerHTML = `
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle"></i> No videos generated yet
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error refreshing videos list:', error);
            }
        }

        // Periodically refresh status and videos
        setInterval(updateAutoModeStatus, 30000); // Every 30 seconds
        setInterval(refreshVideosList, 60000); // Every minute
    </script>
</body>
</html>
    '''
    return HTMLResponse(content=html_content)

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
        logger.error(f"Error running auto generation: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/auto-mode/status")
async def get_auto_mode_status():
    """Get auto mode status"""
    return {
        "running": auto_mode_manager.running,
        "enabled": app_config.auto_mode_enabled,
        "last_run": progress_data.get("last_auto_run"),
        "interval_hours": app_config.auto_mode_interval / 3600
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
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "size": f"{stat.st_size / 1024 / 1024:.1f} MB"
            })
        
        # Sort by creation time, newest first
        videos.sort(key=lambda x: x["created"], reverse=True)
        return {"videos": videos}
        
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        return {"videos": []}

@app.get("/videos/list")
async def list_videos_no_api():
    """List generated videos (no /api prefix)"""
    return await list_videos()

@app.post("/config/api-key")
async def config_api_key(request: Request):
    """Configure OpenRouter API key"""
    try:
        data = await request.json()
        api_key = data.get("api_key")
        
        if not api_key:
            return {"success": False, "error": "API key is required"}
        
        app_config.openrouter_api_key = api_key
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error setting API key: {e}")
        return {"success": False, "error": str(e)}

@app.post("/auto-mode/start")
async def start_auto_mode_no_api(request: Request):
    """Start auto mode (no /api prefix)"""
    try:
        data = await request.json()
        interval = data.get("interval", 3600)  # Default 1 hour
        subreddit = data.get("subreddit", "technology")
        
        if not app_config.openrouter_api_key:
            return {"success": False, "error": "OpenRouter API key not set"}
        
        auto_mode_manager.start_auto_mode(interval, subreddit)
        app_config.auto_mode_enabled = True
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error starting auto mode: {e}")
        return {"success": False, "error": str(e)}

@app.post("/auto-mode/stop")
async def stop_auto_mode_no_api():
    """Stop auto mode (no /api prefix)"""
    try:
        auto_mode_manager.stop_auto_mode()
        app_config.auto_mode_enabled = False
        return {"success": True}
    except Exception as e:
        logger.error(f"Error stopping auto mode: {e}")
        return {"success": False, "error": str(e)}

@app.post("/auto-mode/run-now")
async def run_auto_now_no_api():
    """Trigger immediate auto generation (no /api prefix)"""
    try:
        if not app_config.openrouter_api_key:
            return {"success": False, "error": "OpenRouter API key not set"}
        
        # Run auto generation in background
        asyncio.create_task(auto_mode_manager.run_auto_generation())
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error running auto generation: {e}")
        return {"success": False, "error": str(e)}

@app.post("/generate_video")
async def generate_video_api(request: Request, background_tasks: BackgroundTasks):
    """Generate video from form data"""
    task_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    update_progress("working", "Starting video generation...", 1)

    try:
        # Parse form data
        form = await request.form()
        
        paragraphs = form.getlist("paragraphs")
        links = form.getlist("links")
        output_name = form.get("output_name") or f"video_{task_id}.mp4"
        resolution = form.get("resolution") or "1920x1080"
        transition_duration = float(form.get("transition_duration") or "2.0")
        
        if not output_name.endswith('.mp4'):
            output_name += '.mp4'
        
        # Parse resolution
        try:
            width, height = map(int, resolution.split('x'))
        except:
            width, height = 1920, 1080
        
        # Create video generation task
        background_tasks.add_task(
            generate_video_background,
            paragraphs, links, output_name, width, height, transition_duration, task_id
        )
        
        return {"task_id": task_id, "message": "Video generation started"}
        
    except Exception as e:
        logger.error(f"Error in generate_video_api: {e}")
        update_progress("error", f"Error starting video generation: {str(e)}", 100)
        return {"error": str(e), "task_id": task_id}

async def generate_video_background(paragraphs: List[str], links: List[str], output_name: str, 
                                   width: int, height: int, transition_duration: float, task_id: str):
    """Background task for video generation"""
    try:
        update_progress("working", "Initializing video builder...", 10, "Manual Generation")
        
        output_path = os.path.join("videos", output_name)
        os.makedirs("videos", exist_ok=True)
        
        video_builder = EnhancedKenBurnsVideoBuilder(width, height, 60)
        
        try:
            # Create a simple script from paragraphs and links
            script = {
                "segments": [],
                "total_duration": 0
            }
            
            total_paragraphs = len(paragraphs)
            segment_duration = 10  # Default duration per segment
            
            for i, paragraph in enumerate(paragraphs):
                segment = {
                    "text": paragraph,
                    "duration": segment_duration,
                    "visual_cue": f"Segment {i+1}",
                    "screenshot_url": links[i] if i < len(links) else None
                }
                script["segments"].append(segment)
                script["total_duration"] += segment_duration
                
                progress = 10 + (i / total_paragraphs) * 30
                update_progress("working", f"Processing segment {i+1}/{total_paragraphs}", progress, "Manual Generation")
            
            # Build video from script
            success = await video_builder.build_video_from_script(script, output_path)
            
            if success:
                update_progress("done", f"Video generated successfully: {output_name}", 100, "Manual Generation")
                logger.info(f"Video generated: {output_path}")
            else:
                update_progress("error", "Video generation failed", 100, "Manual Generation")
                logger.error("Video generation failed")
                
        finally:
            video_builder.cleanup_temp_files()
            
    except Exception as e:
        logger.error(f"Error in video generation background task: {e}")
        update_progress("error", f"Video generation error: {str(e)}", 100, "Manual Generation")

@app.get("/progress")
async def get_progress_api(task_id: str = "current"):
    """Get current progress"""
    return progress_data

# Additional route aliases for the new UI
@app.get("/videos/list")
async def list_videos_alias():
    """List generated videos (alias for new UI)"""
    try:
        videos_dir = Path("videos")
        if not videos_dir.exists():
            return {"videos": []}
        
        videos = []
        for video_file in videos_dir.glob("*.mp4"):
            stat = video_file.stat()
            videos.append({
                "name": video_file.name,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "size": f"{stat.st_size / 1024 / 1024:.1f} MB"
            })
        
        # Sort by creation time, newest first
        videos.sort(key=lambda x: x["created"], reverse=True)
        return {"videos": videos}
        
    except Exception as e:
        logger.error(f"Error listing videos: {e}")
        return {"videos": []}

@app.post("/config/api-key")
async def config_api_key(request: Request):
    """Configure OpenRouter API key"""
    try:
        data = await request.json()
        api_key = data.get("api_key")
        
        if not api_key:
            return {"success": False, "error": "API key is required"}
        
        app_config.openrouter_api_key = api_key
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error setting API key: {e}")
        return {"success": False, "error": str(e)}

@app.post("/auto-mode/start")
async def start_auto_mode_alias(request: Request):
    """Start auto mode (alias for new UI)"""
    return await start_auto_mode_api(request)

@app.post("/auto-mode/stop")
async def stop_auto_mode_alias():
    """Stop auto mode (alias for new UI)"""
    return await stop_auto_mode_api()

@app.post("/auto-mode/run-now")
async def run_auto_now_alias():
    """Trigger immediate auto generation (alias for new UI)"""
    return await run_auto_now_api()

@app.get("/videos/download/{filename}")
async def download_video(filename: str):
    """Download a generated video"""
    try:
        video_path = Path("videos") / filename
        if not video_path.exists():
            return {"error": "Video not found"}
        
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename=filename
        )
    except Exception as e:
        logger.error(f"Error downloading video: {e}")
        return {"error": str(e)}

# ---------------------------------------------------------------------------
# Startup and Cleanup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info("GleamVideo Enhanced starting up...")
    
    # Check for required external tools
    tools_to_check = ["ffmpeg", "ffprobe"]
    for tool in tools_to_check:
        try:
            subprocess.run([tool, "-version"], capture_output=True, check=True)
            logger.info(f"✓ {tool} is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning(f"⚠ {tool} is not available - some features may not work")
    
    # Check for TTS executable
    if os.path.exists(VOICE_COMMAND):
        logger.info("✓ Kokoro TTS is available")
    else:
        logger.warning("⚠ Kokoro TTS not found - TTS features may not work")
    
    logger.info("🚀 GleamVideo Enhanced ready!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down GleamVideo Enhanced...")
    
    # Stop auto mode
    if auto_mode_manager.running:
        auto_mode_manager.stop_auto_mode()
    
    logger.info("👋 GleamVideo Enhanced shut down complete")

# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="GleamVideo Enhanced - AI Video Generator")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    logger.info(f"Starting GleamVideo Enhanced on {args.host}:{args.port}")
    
    uvicorn.run(
        "gleamvideo:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )
