"""
Screen Sensor Module
Captures screenshots for LLaVA processing.
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
from typing import Dict, Any, Optional
import hashlib
import json
from dataclasses import dataclass, asdict
from PIL import Image
import numpy as np
import pytesseract
from pytesseract import Output
import cv2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/screen_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ScreenData:
    """Data class for screen capture results."""
    timestamp: float
    image: Optional[bytes] = None
    image_hash: Optional[str] = None
    text: Optional[str] = None
    text_content: Optional[str] = None
    active_window: Optional[str] = None
    active_apps: Optional[list] = None
    error: Optional[str] = None

class ScreenSensor:
    """
    Captures screenshots for LLaVA processing.
    Runs in a background thread at specified intervals.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.interval = config.get('interval_sec', 2.0)
        self.sct = None
        self.last_data: Optional[ScreenData] = None
        self.cache_dir = "cache/screen_sensor"
        self.cache_file = f"{self.cache_dir}/last_screen.json"
        self.unchanged_count = 0
        self.max_unchanged = 5  # Skip processing after 5 unchanged frames
        
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
    
    def _extract_text(self, image: Image.Image) -> str:
        """Extract text from image using OCR"""
        try:
            # Convert image to grayscale for better OCR
            gray_image = image.convert('L')
            
            # Use pytesseract to extract text
            data = pytesseract.image_to_data(gray_image, output_type=Output.DICT)
            
            # Combine all text blocks
            text_blocks = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 60:  # Only include text with confidence > 60%
                    text_blocks.append(data['text'][i])
            
            return ' '.join(text_blocks)
        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
    
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
        try:
            # Create a memory-optimized version of the screen data without the image
            cache_data = asdict(data)
            
            # Remove large binary data before saving to cache
            if 'image' in cache_data:
                # Keep a small thumbnail or just remove the image completely
                cache_data['image'] = None
                
            # Save only essential data to cache
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f)
                
            logger.debug("Saved memory-optimized screen data to cache")
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
        """Capture and process screen content with optimizations"""
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
                    self.last_data.is_unchanged = True
                    return self.last_data
            
            # Extract text from image
            text_content = self._extract_text(image)
            
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Get active window info
            window_info = self._get_window_info()
            
            # Create screen data
            screen_data = ScreenData(
                timestamp=current_time,
                image=img_byte_arr,
                image_hash=image_hash,
                text=text_content,
                text_content=text_content,
                active_window=window_info.get('active_window'),
                active_apps=window_info.get('active_apps', [])
            )
            
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
    
    async def get_data(self) -> Dict[str, Any]:
        """Get current screen data"""
        try:
            screen_data = await self.capture_screen()
            
            return {
                'timestamp': screen_data.timestamp,
                'image': base64.b64encode(screen_data.image).decode('utf-8'),
                'image_hash': screen_data.image_hash,
                'text': screen_data.text,
                'has_images': self.has_images,
                'has_videos': self.has_videos
            }
        except Exception as e:
            logger.error(f"Error getting screen data: {e}")
            return {
                'timestamp': time.time(),
                'error': str(e)
            }

    async def cleanup(self):
        """Cleanup resources"""
        try:
            if self.sct:
                self.sct.close()
        except Exception as e:
            logger.error(f"Error in screen sensor cleanup: {str(e)}")

    def get_latest_image(self) -> Image.Image:
        """Get the latest captured image."""
        return self.latest_image
    
    def get_latest_image_base64(self) -> str:
        """Get the latest captured image as base64 string."""
        if self.latest_image is None:
            return ""
            
        buffered = io.BytesIO()
        self.latest_image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def _run_capture_loop(self):
        """Background thread function for periodic screenshot capture."""
        self.running = True
        while self.running:
            try:
                # Ensure initialization before capturing
                if not self.sct:
                    self.logger.info("Screen capture not initialized in loop, initializing now...")
                    asyncio.run(self.initialize())
                # Only capture if initialized
                if self.sct:
                    data = asyncio.run(self.capture_screen())
                    # Update latest_image if capture was successful
                    if data and data.image:
                        try:
                            from PIL import Image
                            import io
                            self.latest_image = Image.open(io.BytesIO(data.image))
                        except Exception as img_e:
                            self.logger.error(f"Failed to update latest_image: {img_e}")
                else:
                    self.logger.warning("Screen capture still not initialized, will retry...")
            except Exception as e:
                self.logger.error(f"Error in screen capture loop: {str(e)}", exc_info=True)
            # Sleep for the specified interval
            time.sleep(self.interval)
    
    def start(self):
        """Start the screen monitoring thread."""
        if self.thread is None:
            self._stop_event.clear()
            self.thread = threading.Thread(target=self._run_capture_loop, daemon=True)
            self.thread.start()
            self.logger.info("Screen sensor started")
    
    def stop(self):
        """Stop the screen monitoring thread."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self._stop_event.set()
            self.thread.join(timeout=2.0)
            self.thread = None
            self.logger.info("Screen sensor stopped")
    
    def _detect_images(self, screenshot: Image.Image) -> bool:
        """Detect if there are images on the screen."""
        try:
            # Convert to grayscale
            gray = screenshot.convert('L')
            
            # Calculate standard deviation of pixel values
            std_dev = np.std(np.array(gray))
            
            # If standard deviation is high, likely contains images
            return std_dev > 30
        except Exception as e:
            self.logger.error(f"Error detecting images: {e}")
            return False
            
    def _detect_videos(self) -> bool:
        """Detect if there are videos playing on the screen."""
        try:
            # Check for video-related processes
            video_processes = ['vlc', 'quicktime', 'mpv', 'mplayer', 'ffplay']
            for proc in psutil.process_iter(['name']):
                if proc.info['name'].lower() in video_processes:
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Error detecting videos: {e}")
            return False

    def has_updates(self):
        """Check if there are new updates since last check."""
        current_time = time.time()
        if current_time - self._last_update >= self.interval:
            self._last_update = current_time
            return True
        return False

    def get_data(self):
        """Get the current sensor data."""
        return {
            "timestamp": datetime.now().isoformat(),
            "type": "screen_capture",
            "data": {
                "image": self.get_latest_image_base64(),
                "has_images": self.has_images,
                "has_videos": self.has_videos
            }
        }

    def capture(self):
        """Capture the current screen state."""
        return asyncio.run(self.capture_screen())

    def _get_window_info(self) -> Dict[str, Any]:
        """Get information about active window and applications."""
        try:
            self.logger.info("Getting window information...")
            
            # Get active window
            active_window = os.popen('osascript -e \'tell application "System Events" to get name of first window of first process whose frontmost is true\'').read().strip()
            self.logger.debug(f"Active window: {active_window}")
            
            # Get active applications
            active_apps = []
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    if proc.info['name'] not in active_apps:
                        active_apps.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.logger.debug(f"Active applications: {active_apps}")
            
            return {
                'active_window': active_window,
                'active_apps': active_apps
            }
            
        except Exception as e:
            self.logger.error(f"Error getting window info: {e}")
            return {
                'active_window': 'Unknown',
                'active_apps': []
            }

# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sensor = ScreenSensor({"interval_sec": 3})
    sensor.start()
    
    try:
        # Test for 15 seconds
        time.sleep(15)
        print("Latest captured image:", sensor.get_latest_image_base64())
    finally:
        sensor.stop()