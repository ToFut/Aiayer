"""Ultra-fast screen sensor with intelligent sampling and optimization."""

import asyncio
import logging
import mss
import numpy as np
from PIL import Image
from datetime import datetime
from typing import Dict, Any, Optional
import cv2
import threading
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)

class ScreenSensor:
    """High-performance screen capture with intelligent sampling."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the screen sensor."""
        self.config = config or self._default_config()
        self.mss = mss.mss()
        self.last_capture_time = 0
        self.last_image_hash = None
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self.capture_lock = threading.Lock()
        
        # Initialize capture parameters
        self.min_interval = self.config.get('min_interval', 0.2)  # Reduced from 0.5
        self.max_width = self.config.get('max_width', 800)  # Reduced from 1024
        self.jpeg_quality = self.config.get('jpeg_quality', 60)  # Reduced from 75
        self.sampling_rate = self.config.get('sampling_rate', 0.5)  # Sample every other pixel
        
        logger.info("Screen sensor initialized with high-performance settings")
        
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            'min_interval': 0.2,  # Minimum seconds between captures
            'optimization_level': 2,  # 0=None, 1=Basic, 2=Full
            'max_width': 800,  # Maximum width for optimization
            'jpeg_quality': 60,  # JPEG quality for optimization
            'sampling_rate': 0.5,  # Sample every other pixel
            'resize_method': Image.Resampling.LANCZOS,
            'grayscale': True,  # Convert to grayscale by default
            'use_cv2': True  # Use OpenCV for faster processing
        }
        
    async def capture(self) -> Dict[str, Any]:
        """Capture and optimize a screenshot with intelligent sampling."""
        try:
            # Check capture interval
            current_time = time.time()
            time_since_last = current_time - self.last_capture_time
            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)
            
            # Capture screen (use primary monitor)
            with self.capture_lock:
                monitor = self.mss.monitors[0]
                screen = self.mss.grab(monitor)
                
                # Convert to numpy array for faster processing
                frame = np.array(screen)
                
                # Apply intelligent sampling
                if self.config.get('use_cv2', True):
                    # Use OpenCV for faster processing
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    
                    # Resize if needed
                    if frame.shape[1] > self.max_width:
                        ratio = self.max_width / frame.shape[1]
                        new_size = (self.max_width, int(frame.shape[0] * ratio))
                        frame = cv2.resize(frame, new_size, interpolation=cv2.INTER_LANCZOS4)
                    
                    # Convert to grayscale if configured
                    if self.config.get('grayscale', True):
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # Apply sampling
                    if self.sampling_rate < 1.0:
                        frame = frame[::int(1/self.sampling_rate), ::int(1/self.sampling_rate)]
                    
                    # Convert to bytes
                    success, image_bytes = cv2.imencode('.jpg', frame, 
                        [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
                    if not success:
                        raise Exception("Failed to encode image")
                    image_bytes = image_bytes.tobytes()
                else:
                    # Use PIL for processing
                    image = Image.frombytes(
                        'RGB',
                        (screen.width, screen.height),
                        screen.rgb,
                    )
                    
                    # Optimize image
                    image = self._optimize_image(image)
                    
                    # Convert to bytes
                    image_bytes = self._image_to_bytes(image)
                
                # Update last capture time
                self.last_capture_time = time.time()
                
                # Return capture data
                return {
                    'image': image_bytes,
                    'timestamp': datetime.now().isoformat(),
                    'screen_size': {'width': frame.shape[1], 'height': frame.shape[0]}
                }
            
        except Exception as e:
            logger.error(f"Error capturing screen: {str(e)}")
            raise
            
    def _optimize_image(self, image: Image.Image) -> Image.Image:
        """Optimize the image based on configuration."""
        try:
            # Convert to grayscale if configured
            if self.config.get('grayscale', True):
                image = image.convert('L')
            
            # Resize if needed
            if self.config.get('optimization_level', 2) >= 2:
                max_width = self.config.get('max_width', 800)
                if image.width > max_width:
                    ratio = max_width / image.width
                    new_size = (max_width, int(image.height * ratio))
                    image = image.resize(new_size, self.config.get('resize_method', Image.Resampling.LANCZOS))
            
            return image
            
        except Exception as e:
            logger.error(f"Error optimizing image: {str(e)}")
            return image
            
    def _image_to_bytes(self, image: Image.Image) -> bytes:
        """Convert PIL Image to bytes with optimization."""
        try:
            # Save to bytes buffer with optimization
            from io import BytesIO
            buffer = BytesIO()
            
            # Use JPEG format with quality setting
            image.save(
                buffer,
                format='JPEG',
                quality=self.config.get('jpeg_quality', 60),
                optimize=True
            )
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error converting image to bytes: {str(e)}")
            raise
            
    def close(self):
        """Clean up resources."""
        try:
            self.mss.close()
            self.thread_pool.shutdown()
        except Exception as e:
            logger.error(f"Error closing screen sensor: {str(e)}")