"""
Screen Sensor Module
Captures screenshots and extracts text via OCR.
"""
import mss
import mss.tools
import threading
import time
import logging
import os
import numpy as np
from datetime import datetime
import psutil
from PIL import Image, ImageEnhance, ImageFilter, ImageGrab
import pytesseract

# Optional imports with fallbacks
try:
    import cv2
except ImportError:
    cv2 = None
    
try:
    import pytesseract
except ImportError:
    pytesseract = None

class ScreenSensor:
    """
    Captures screenshots and performs OCR to extract text.
    Runs in a background thread at specified intervals.
    """
    
    def __init__(self, interval_sec=5, ocr_quality="balanced", downsampling_factor=1.0,
                 region_detection=False, cache_static_regions=False, privacy_filter=False):
        """
        Initialize the screen sensor.
        
        Args:
            interval_sec (int): Seconds between screenshots
            ocr_quality (str): OCR quality setting ("high", "balanced", "fast")
            downsampling_factor (float): Factor to downsample images (1.0 = no downsampling)
            region_detection (bool): Whether to use intelligent region detection
            cache_static_regions (bool): Whether to cache static regions of the screen
            privacy_filter (bool): Whether to filter potentially sensitive content
        """
        self.interval = interval_sec
        self.ocr_quality = ocr_quality
        self.downsampling_factor = downsampling_factor
        self.region_detection = region_detection
        self.cache_static_regions = cache_static_regions
        self.privacy_filter = privacy_filter
        
        self.latest_text = ""
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(__name__)
        self.has_images = False
        self.has_videos = False
        self._stop_event = threading.Event()
        self.sensor_type = "screen"
        self._last_update = time.time()
        
        # For region detection and caching
        self.static_regions_cache = {}
        self.last_screen_hash = None
        
        # Create results directory if it doesn't exist
        self.results_dir = "resultsOCRtest"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Set up OCR-specific logger
        self.ocr_logger = logging.getLogger('ocr_logger')
        self.ocr_logger.setLevel(logging.INFO)
        
        # Create OCR log file handler
        ocr_handler = logging.FileHandler(os.path.join(self.results_dir, 'ocr_results.log'))
        ocr_handler.setLevel(logging.INFO)
        
        # Create formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - OCR Results:\n%(message)s\n')
        ocr_handler.setFormatter(formatter)
        
        # Add the handler to the logger
        self.ocr_logger.addHandler(ocr_handler)
        
        # Configure pytesseract path if needed
        # Uncomment and set this for Windows if tesseract is not in PATH
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    def _preprocess_image(self, image):
        """
        Preprocess image for better OCR results.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to grayscale
        image = image.convert('L')
        
        # Apply different preprocessing based on quality setting
        if self.ocr_quality == "high":
            # High quality: More aggressive preprocessing
            image = image.point(lambda x: 0 if x < 128 else 255, '1')  # Binarize
            image = image.filter(ImageFilter.SHARPEN)  # Sharpen edges
            image = image.filter(ImageFilter.EDGE_ENHANCE)  # Enhance edges
        elif self.ocr_quality == "balanced":
            # Balanced: Moderate preprocessing
            image = image.point(lambda x: 0 if x < 150 else 255, '1')  # Binarize with higher threshold
            image = image.filter(ImageFilter.SHARPEN)  # Sharpen edges
        else:  # "fast"
            # Fast: Minimal preprocessing
            image = image.point(lambda x: 0 if x < 180 else 255, '1')  # Simple binarization
            
        return image
    
    def capture_screen_text(self):
        """
        Capture screenshot and extract text using OCR.
        
        Returns:
            str: Extracted text
        """
        try:
            # Capture screenshot
            screenshot = ImageGrab.grab()
            
            # Convert to grayscale and preprocess
            img = screenshot.convert('L')
            img = self._preprocess_image(img)
            
            # Configure Tesseract based on quality setting
            if self.ocr_quality == "high":
                config = '--oem 1 --psm 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,!?@#$%&*()[]{}<>:;-_+=|\\/"\''
            elif self.ocr_quality == "balanced":
                config = '--oem 1 --psm 3'
            else:  # "fast"
                config = '--oem 1 --psm 6'  # Assume uniform block of text
                
            # Perform OCR
            text = pytesseract.image_to_string(img, config=config)
            
            # Log the results
            self.ocr_logger.info(f"OCR Results:\n{text}")
            
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Error in capture_screen_text: {str(e)}")
            return ""
    
    def write_ocr_results(self, text, timestamp):
        """
        Write OCR results to a file and log.
        
        Args:
            text (str): Extracted text from OCR
            timestamp (datetime): Timestamp of the capture
        """
        filename = os.path.join(self.results_dir, f"ocr_results_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"OCR Results - {timestamp}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Total characters: {len(text)}\n")
                f.write(f"Total words: {len(text.split())}\n")
                f.write(f"Total lines: {len(text.splitlines())}\n\n")
                f.write("Extracted Text:\n")
                f.write("=" * 50 + "\n")
                f.write(text)
            
            # Log OCR results
            log_message = f"""
Total characters: {len(text)}
Total words: {len(text.split())}
Total lines: {len(text.splitlines())}

Extracted Text:
{text[:500]}...  # First 500 characters
"""
            self.ocr_logger.info(log_message)
            
        except Exception as e:
            self.logger.error(f"Error writing OCR results to file: {str(e)}", exc_info=True)
    
    def _run_capture_loop(self):
        """Background thread function for periodic screenshot capture."""
        self.running = True
        
        while self.running:
            try:
                self.capture_screen_text()
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
        """Detect if there are images on the screen using more advanced image analysis."""
        try:
            # Convert to grayscale
            gray = screenshot.convert('L')
            
            # Calculate standard deviation of pixel values
            img_array = np.array(gray)
            std_dev = np.std(img_array)
            
            # Calculate edge density using Canny edge detection
            edges = cv2.Canny(img_array, 100, 200)
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            # Calculate texture using GLCM (Gray-Level Co-occurrence Matrix)
            texture_score = self._calculate_texture_score(img_array)
            
            # Combine indicators - if any of these are high, likely contains images
            has_images = (std_dev > 40) or (edge_density > 0.1) or (texture_score > 0.3)
            
            if has_images:
                self.logger.debug(f"Detected images on screen (std_dev={std_dev:.1f}, edge_density={edge_density:.3f}, texture={texture_score:.3f})")
                
            return has_images
        except Exception as e:
            self.logger.error(f"Error detecting images: {e}")
            return False
            
    def _calculate_texture_score(self, img_array):
        """Calculate a simple texture score based on local variance."""
        try:
            # Calculate local variance in windows
            window_size = 5
            padded = np.pad(img_array, ((window_size//2, window_size//2), (window_size//2, window_size//2)), mode='reflect')
            windows = np.lib.stride_tricks.sliding_window_view(padded, (window_size, window_size))
            local_variance = np.var(windows, axis=(2, 3))
            
            # Normalize and get mean variance
            normalized_variance = np.mean(local_variance) / 255.0
            return normalized_variance
        except Exception as e:
            self.logger.error(f"Error calculating texture: {e}")
            return 0
            
    def _detect_videos(self) -> bool:
        """Detect if there are videos playing on the screen using more reliable techniques."""
        try:
            # First, check for video-related processes
            video_processes = ['vlc', 'quicktime', 'mpv', 'mplayer', 'ffplay', 
                              'chrome', 'firefox', 'safari', 'edge']  # Include browsers
                              
            for proc in psutil.process_iter(['name']):
                proc_name = proc.info['name'].lower()
                if any(vp in proc_name for vp in video_processes):
                    # For browsers, we need to check if they're actually playing video
                    if any(browser in proc_name for browser in ['chrome', 'firefox', 'safari', 'edge']):
                        # Check CPU usage as a proxy for video playback
                        try:
                            cpu_percent = proc.cpu_percent(interval=0.1)
                            if cpu_percent > 15:  # Higher CPU usage suggests video playback
                                return True
                        except:
                            pass
                    else:
                        # For dedicated video players, presence is enough
                        return True
            
            # Check for motion between consecutive frames (if we stored previous frame)
            if hasattr(self, 'previous_frame') and self.previous_frame is not None:
                current_frame = np.array(self.screenshot)
                prev_frame = self.previous_frame
                
                # Ensure dimensions match
                if current_frame.shape == prev_frame.shape:
                    # Calculate difference between frames
                    diff = cv2.absdiff(current_frame, prev_frame)
                    motion = np.mean(diff) / 255.0
                    
                    # If significant motion detected
                    if motion > 0.05:
                        return True
            
            # Store current frame for next comparison
            self.previous_frame = np.array(self.screenshot) if hasattr(self, 'screenshot') else None
            
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
                "text": self.latest_text,
                "has_images": self.has_images,
                "has_videos": self.has_videos
            }
        }

    def capture(self):
        """Capture the current screen state."""
        return self.capture_screen_text()

# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sensor = ScreenSensor(interval_sec=3)
    sensor.start()
    
    try:
        # Test for 15 seconds
        time.sleep(15)
        print("Latest captured text:", sensor.latest_text[:100] + "..." if len(sensor.latest_text) > 100 else sensor.latest_text)
    finally:
        sensor.stop()