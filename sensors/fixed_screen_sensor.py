#!/usr/bin/env python3
"""
Fixed Screen Sensor Module
Captures screenshots for LLaVA processing with enhanced image and text handling.
"""
import mss
import mss.tools
import threading
import time
import logging
import os
from datetime import datetime
import psutil
import io
import base64
import asyncio
from typing import Dict, Any, Optional, Union, List
import hashlib
import json
from dataclasses import dataclass, asdict, field
from PIL import Image
import numpy as np
import pytesseract
from pytesseract import Output
import cv2
import requests
import aiohttp

# Configure logging
os.makedirs('logs/sensors/screen_sensor', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/screen_sensor/screen_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ScreenData:
    """Data class for screen capture results with enhanced LLaVA integration."""
    timestamp: float
    image: Optional[bytes] = None
    image_hash: Optional[str] = None
    text: Optional[str] = None  # OCR extracted text
    text_content: Optional[str] = None  # Same as text, for backward compatibility
    active_window: Optional[str] = None
    active_apps: Optional[list] = None
    error: Optional[str] = None
    llava_description: Optional[str] = None  # LLaVA's description of the screen
    screen_elements: Optional[List[Dict[str, Any]]] = field(default_factory=list)  # Detected UI elements
    visual_context: Optional[str] = None  # High-level context description from LLaVA

class FixedScreenSensor:
    """
    Captures screenshots for LLaVA processing with enhanced image analysis.
    Runs in a background thread at specified intervals.
    Integrates with LLaVA for detailed screen content analysis.
    """
    
    def __init__(self, llava_url="http://localhost:11434"):
        self.interval = 2.0  # Default interval
        self.sct = None
        self.last_data: Optional[ScreenData] = None
        self.cache_dir = "cache/screen_sensor"
        self.cache_file = f"{self.cache_dir}/last_screen.json"
        self.unchanged_count = 0
        self.max_unchanged = 5  # Skip processing after 5 unchanged frames
        
        # LLaVA integration settings
        self.llava_url = llava_url
        self.llava_endpoint = f"{llava_url}/api/chat"
        self.llava_model = "llava"  # The model name for LLaVA in Ollama
        self.use_llava = True  # Enable/disable LLaVA analysis
        self.llava_timeout = 15  # Timeout for LLaVA requests in seconds
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load last screen data from cache
        self._load_cache()
        
        self.latest_image = None
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(__name__)
        self.has_images = False
        self.has_videos = False
        self._stop_event = threading.Event()
        self.sensor_type = "screen"
        self._last_update = time.time()
        
        # Create results directory if it doesn't exist
        self.results_dir = "results"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize screen capture immediately
        logger.info("Initializing screen capture in constructor...")
        try:
            self.sct = mss.mss()
            if self.sct:
                logger.info("Screen capture initialized successfully in constructor")
                monitors = self.sct.monitors
                logger.info(f"Found {len(monitors)} monitors: {monitors}")
            else:
                logger.error("Failed to initialize screen capture in constructor")
        except Exception as e:
            logger.error(f"Error initializing screen capture in constructor: {e}")
        
        # Initialize OCR settings
        self.ocr_config = {
            'lang': 'eng',
            'config': '--psm 3'  # Assume a single uniform block of text
        }
        
        # Test LLaVA connection
        self._test_llava_connection()
    
    def _test_llava_connection(self):
        """Test connection to LLaVA service"""
        try:
            response = requests.get(f"{self.llava_url}/api/version", timeout=2)
            if response.status_code == 200:
                logger.info(f"Successfully connected to Ollama API at {self.llava_url}")
                self.use_llava = True
            else:
                logger.warning(f"Failed to connect to Ollama API at {self.llava_url}: {response.status_code}")
                self.use_llava = False
        except Exception as e:
            logger.warning(f"Error connecting to LLaVA service: {e}")
            self.use_llava = False
    
    def _extract_text(self, image: Image.Image) -> str:
        """Extract text from image using OCR with enhanced processing"""
        try:
            # Convert image to grayscale for better OCR
            gray_image = image.convert('L')
            
            # Apply some image processing to improve OCR results
            # Resizing can improve OCR quality for some texts
            width, height = gray_image.size
            if width > 1920:  # Resizing very large images can help OCR
                ratio = 1920 / width
                new_size = (int(width * ratio), int(height * ratio))
                gray_image = gray_image.resize(new_size, Image.LANCZOS)
            
            # Convert to numpy array for OpenCV processing
            img_np = np.array(gray_image)
            
            # Apply adaptive thresholding for better text extraction
            # This helps with varying lighting conditions
            try:
                # Use adaptive thresholding to deal with varying background
                thresholded = cv2.adaptiveThreshold(
                    img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 11, 2
                )
                
                # Noise removal
                kernel = np.ones((1, 1), np.uint8)
                opening = cv2.morphologyEx(thresholded, cv2.MORPH_OPEN, kernel)
                
                # Convert back to PIL for pytesseract
                enhanced_image = Image.fromarray(opening)
            except Exception as e:
                logger.warning(f"Error in image enhancement, using original: {e}")
                enhanced_image = gray_image
            
            # Use pytesseract to extract text
            data = pytesseract.image_to_data(enhanced_image, output_type=Output.DICT, 
                                            config='--psm 11 --oem 3')
            
            # Combine all text blocks with better confidence filtering
            text_blocks = []
            for i in range(len(data['text'])):
                # Higher confidence threshold of 70% instead of 60%
                if int(data['conf'][i]) > 70 and data['text'][i].strip():
                    text_blocks.append(data['text'][i])
            
            result = ' '.join(text_blocks)
            logger.info(f"OCR extracted {len(text_blocks)} text blocks, total length: {len(result)}")
            return result
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
            
    async def _analyze_with_llava(self, image: Image.Image) -> Dict[str, Any]:
        """
        Analyze the screen image with LLaVA to get detailed visual understanding
        
        Returns:
            Dict containing visual description, UI elements, and high-level context
        """
        if not self.use_llava:
            logger.warning("LLaVA analysis disabled or unavailable")
            return {
                "llava_description": "",
                "screen_elements": [],
                "visual_context": ""
            }
            
        try:
            # Convert image to base64
            img_byte_array = io.BytesIO()
            # Save as JPEG with reduced quality to minimize size
            image.save(img_byte_array, format='JPEG', quality=85)
            img_bytes = img_byte_array.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Prepare message for LLaVA with structured analysis prompt
            messages = [
                {
                    "role": "system",
                    "content": """You are a professional screen content analyzer. When given a screen capture:
1. First provide a detailed description of what you see in the image
2. Identify all UI elements like buttons, text fields, menus, windows, etc.
3. Extract any important text content visible in the screen
4. Provide a high-level summary of what the user is likely doing"""
                },
                {
                    "role": "user",
                    "content": "Please analyze this screen capture in detail and provide a full breakdown of what you see, including all text content and UI elements."
                }
            ]
            
            # Prepare request payload
            payload = {
                "model": self.llava_model,
                "messages": messages,
                "images": [img_base64],
                "temperature": 0.2,  # Lower temperature for more factual analysis
                "max_tokens": 1024
            }
            
            # Make async request to LLaVA
            logger.info("Sending screen capture to LLaVA for analysis")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.llava_endpoint,
                    json=payload,
                    timeout=self.llava_timeout
                ) as response:
                    if response.status != 200:
                        logger.warning(f"LLaVA request failed with status {response.status}")
                        return {
                            "llava_description": "",
                            "screen_elements": [],
                            "visual_context": ""
                        }
                    
                    result = await response.json()
                    if not result or 'message' not in result:
                        logger.warning("Invalid response from LLaVA")
                        return {
                            "llava_description": "",
                            "screen_elements": [],
                            "visual_context": ""
                        }
                    
                    # Extract full analysis
                    llava_response = result['message']['content']
                    logger.info(f"Received LLaVA analysis: {len(llava_response)} chars")
                    
                    # Process the response to extract structured information
                    analysis = self._parse_llava_response(llava_response)
                    return analysis
                
        except asyncio.TimeoutError:
            logger.warning(f"LLaVA request timed out after {self.llava_timeout}s")
        except Exception as e:
            logger.error(f"Error analyzing image with LLaVA: {e}")
            
        return {
            "llava_description": "",
            "screen_elements": [],
            "visual_context": ""
        }
    
    def _parse_llava_response(self, llava_response: str) -> Dict[str, Any]:
        """Parse the LLaVA response into structured data"""
        try:
            lines = llava_response.split('\n')
            
            # Extract main sections
            description = ""
            ui_elements_text = ""
            context = ""
            
            current_section = "description"
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check for section headers
                lower_line = line.lower()
                if "ui element" in lower_line or "interface" in lower_line:
                    current_section = "ui_elements"
                    continue
                elif "text content" in lower_line:
                    current_section = "text_content"
                    continue
                elif "summary" in lower_line or "user is" in lower_line:
                    current_section = "context"
                    continue
                
                # Add content to appropriate section
                if current_section == "description":
                    description += line + " "
                elif current_section == "ui_elements":
                    ui_elements_text += line + "\n"
                elif current_section == "context":
                    context += line + " "
            
            # Extract UI elements as structured data
            ui_elements = []
            if ui_elements_text:
                # Split by bullet points or numbered items
                element_lines = ui_elements_text.split('\n')
                for line in element_lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Remove bullet points or numbers
                    if line.startswith('- ') or line.startswith('* '):
                        line = line[2:]
                    elif line[0].isdigit() and line[1:].startswith('. '):
                        line = line[line.find('. ')+2:]
                    
                    ui_elements.append({"element": line})
            
            return {
                "llava_description": description.strip(),
                "screen_elements": ui_elements,
                "visual_context": context.strip()
            }
        except Exception as e:
            logger.error(f"Error parsing LLaVA response: {e}")
            return {
                "llava_description": llava_response[:500],  # Use truncated raw response
                "screen_elements": [],
                "visual_context": ""
            }
    
    def _load_cache(self):
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    if data:
                        self.last_data = ScreenData(
                            timestamp=data['timestamp'],
                            image=data.get('image'),
                            image_hash=data.get('image_hash'),
                            text=data.get('text'),
                            text_content=data.get('text_content'),
                            active_window=data.get('active_window'),
                            active_apps=data.get('active_apps', []),
                            error=data.get('error')
                        )
        except Exception as e:
            logger.warning(f"Failed to load screen cache: {e}")

    def _save_cache(self, data: ScreenData):
        """Save screen data to cache with proper handling of binary data and LLaVA results"""
        try:
            # Convert to dict for serialization
            cache_data = asdict(data)
            
            # Handle binary image data: encode as base64 for storage
            if data.image:
                try:
                    cache_data['image'] = base64.b64encode(data.image).decode('utf-8')
                except Exception as e:
                    logger.warning(f"Error encoding image for cache: {e}")
                    cache_data['image'] = None
            
            # Ensure all LLaVA fields are properly serializable
            if not cache_data.get('llava_description'):
                cache_data['llava_description'] = ""
                
            if not cache_data.get('visual_context'):
                cache_data['visual_context'] = ""
                
            if not cache_data.get('screen_elements') or not isinstance(cache_data['screen_elements'], list):
                cache_data['screen_elements'] = []
            
            # Save to file with pretty formatting for readability
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.debug(f"Saved screen cache to {self.cache_file}, size: {os.path.getsize(self.cache_file)} bytes")
        except Exception as e:
            logger.warning(f"Failed to save screen cache: {e}")

    async def initialize(self):
        """Initialize the sensor with proper error handling and retries"""
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Initializing ScreenSensor (attempt {attempt + 1}/{max_retries})")
                
                # Initialize screen capture with explicit monitor selection
                self.sct = mss.mss()
                if not self.sct:
                    raise Exception("Failed to initialize mss")
                
                # Get monitor information
                monitors = self.sct.monitors
                if not monitors:
                    raise Exception("No monitors found")
                
                # Use primary monitor (usually index 1)
                primary_monitor = monitors[1]
                logger.info(f"Using primary monitor: {primary_monitor}")
                
                # Test capture
                test_screenshot = self.sct.grab(primary_monitor)
                if not test_screenshot:
                    raise Exception("Failed to capture test screenshot")
                
                test_image = Image.frombytes('RGB', test_screenshot.size, test_screenshot.rgb)
                if not test_image:
                    raise Exception("Failed to convert screenshot to image")
                
                logger.info("ScreenSensor initialized successfully")
                return True
                
            except Exception as e:
                logger.error(f"ScreenSensor initialization failed (attempt {attempt + 1}): {str(e)}")
                if self.sct:
                    try:
                        self.sct.close()
                    except:
                        pass
                    self.sct = None
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error("ScreenSensor initialization failed after all retries")
                    return False

    def _calculate_image_hash(self, image: Image.Image) -> str:
        """Calculate a hash of the image for change detection"""
        return hashlib.md5(image.tobytes()).hexdigest()

    def _should_process_image(self, current_time: float, image_hash: str) -> bool:
        """Determine if image should be processed based on various factors"""
        if self.last_data and image_hash == self.last_data.image_hash:
            self.unchanged_count += 1
            if self.unchanged_count >= self.max_unchanged:
                return False
        else:
            self.unchanged_count = 0
            
        return True

    async def capture_screen(self) -> ScreenData:
        """Capture and process screen content with optimizations and LLaVA integration"""
        try:
            current_time = time.time()
            
            # Ensure screen capture is initialized
            if not self.sct:
                logger.error("Screen capture not initialized")
                raise Exception("Screen capture not initialized")
            
            # Get primary monitor
            monitors = self.sct.monitors
            if not monitors:
                raise Exception("No monitors found")
            primary_monitor = monitors[1]
            
            # Capture screen
            screenshot = self.sct.grab(primary_monitor)
            if not screenshot:
                raise Exception("Failed to capture screenshot")
                
            image = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            if not image:
                raise Exception("Failed to convert screenshot to image")
            
            # Calculate image hash
            image_hash = self._calculate_image_hash(image)
            
            # Check if we should process this image
            if not self._should_process_image(current_time, image_hash):
                if self.last_data:
                    logger.info("Screen unchanged, reusing previous data")
                    return self.last_data
            
            # Extract text from image using enhanced OCR
            logger.info("Extracting text from screen capture using OCR")
            text = self._extract_text(image)
            
            # Get window info
            window_info = self._get_window_info()
            
            # Create initial screen data without LLaVA analysis
            screen_data = ScreenData(
                timestamp=current_time,
                image=image.tobytes(),
                image_hash=image_hash,
                text=text,
                text_content=text,
                active_window=window_info.get('active_window'),
                active_apps=window_info.get('active_apps', [])
            )
            
            # Perform LLaVA analysis if enabled
            if self.use_llava:
                logger.info("Performing LLaVA analysis for screen capture")
                llava_analysis = await self._analyze_with_llava(image)
                
                # Add LLaVA results to screen data
                screen_data.llava_description = llava_analysis.get("llava_description", "")
                screen_data.screen_elements = llava_analysis.get("screen_elements", [])
                screen_data.visual_context = llava_analysis.get("visual_context", "")
                
                # Log success
                logger.info(f"LLaVA analysis successful: {len(screen_data.llava_description)} chars description, " +
                           f"{len(screen_data.screen_elements)} UI elements identified")
            else:
                logger.info("Skipping LLaVA analysis (disabled or unavailable)")
            
            # Save to cache
            self._save_cache(screen_data)
            self.last_data = screen_data
            
            return screen_data
            
        except Exception as e:
            logger.error(f"Error capturing screen: {e}")
            return ScreenData(
                timestamp=time.time(),
                error=str(e)
            )

    def _get_window_info(self) -> Dict[str, Any]:
        """Get information about the active window and applications"""
        try:
            # Get active window title
            script = 'tell application "System Events" to get name of first window of first process whose frontmost is true'
            active_window = os.popen(f'osascript -e \'{script}\'').read().strip()
            
            # Get list of active applications
            script = 'tell application "System Events" to get name of every process whose visible is true'
            active_apps = os.popen(f'osascript -e \'{script}\'').read().strip().split(', ')
            
            return {
                'active_window': active_window,
                'active_apps': active_apps
            }
        except Exception as e:
            logger.error(f"Error getting window info: {e}")
            return {
                'active_window': '',
                'active_apps': []
            }

    async def get_current_state(self) -> Dict[str, Any]:
        """Get current screen state"""
        try:
            screen_data = await self.capture_screen()
            return {
                'timestamp': screen_data.timestamp,
                'image_hash': screen_data.image_hash,
                'text': screen_data.text,
                'active_window': screen_data.active_window,
                'active_apps': screen_data.active_apps,
                'error': screen_data.error
            }
        except Exception as e:
            logger.error(f"Error getting current state: {e}")
            return {
                'timestamp': time.time(),
                'error': str(e)
            }

    async def cleanup(self):
        """Clean up resources"""
        try:
            logger.info("Cleaning up screen sensor...")
            self.running = False
            if self.sct:
                self.sct.close()
            logger.info("Screen sensor cleaned up successfully")
        except Exception as e:
            logger.error(f"Error cleaning up screen sensor: {e}")

async def main():
    """Main function."""
    sensor = FixedScreenSensor()
    if not await sensor.initialize():
        logger.error("Failed to initialize screen sensor")
        return
    
    logger.info("Screen sensor initialized")
    
    try:
        while True:
            try:
                # Get current state
                state = await sensor.get_current_state()
                
                # Log heartbeat occasionally
                if int(time.time()) % 60 == 0:  # Log every minute
                    logger.info("Screen sensor heartbeat")
                
                # Sleep
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)
    except KeyboardInterrupt:
        logger.info("Stopping screen sensor...")
    finally:
        await sensor.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 