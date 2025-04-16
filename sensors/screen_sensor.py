"""
Screen Sensor Module
Captures screenshots and extracts text via OCR.
"""
import mss
import mss.tools
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import threading
import time
import logging
import cv2
import numpy as np
import os
from datetime import datetime
import psutil

class ScreenSensor:
    """
    Captures screenshots and performs OCR to extract text.
    Runs in a background thread at specified intervals.
    """
    
    def __init__(self, interval_sec=5):
        """
        Initialize the screen sensor.
        
        Args:
            interval_sec (int): Seconds between screenshots
        """
        self.interval = interval_sec
        self.latest_text = ""
        self.running = False
        self.thread = None
        self.logger = logging.getLogger(__name__)
        self.has_images = False
        self.has_videos = False
        self._stop_event = threading.Event()
        self.sensor_type = "screen"
        self._last_update = time.time()
        
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
    
    def preprocess_image(self, img):
        """
        Preprocess image to improve OCR quality.
        
        Args:
            img (PIL.Image): Input image
            
        Returns:
            PIL.Image: Preprocessed image
        """
        # Convert to grayscale
        img = img.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(3.0)  # Increased contrast
        
        # Convert to numpy array for OpenCV operations
        img_np = np.array(img)
        
        # Apply adaptive thresholding with larger block size
        img_np = cv2.adaptiveThreshold(
            img_np, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 21, 5  # Increased block size and constant
        )
        
        # Apply slight blur to reduce noise
        img_np = cv2.GaussianBlur(img_np, (5, 5), 0)
        
        # Convert back to PIL Image
        img = Image.fromarray(img_np)
        
        # Apply additional sharpening
        img = img.filter(ImageFilter.SHARPEN)
        
        return img
    
    def capture_screen_text(self):
        """
        Capture screenshot and extract text via OCR.
        
        Returns:
            str: Extracted text from screen
        """
        try:
            timestamp = datetime.now()
            with mss.mss() as sct:
                # Capture primary monitor
                monitor = sct.monitors[1]  # Primary monitor is usually 1
                
                # Define a region of interest (ROI) for the chat area
                # Adjust these values based on your screen resolution and chat window position
                roi = {
                    'left': monitor['left'] + int(monitor['width'] * 0.2),  # 20% from left
                    'top': monitor['top'] + int(monitor['height'] * 0.2),   # 20% from top
                    'width': int(monitor['width'] * 0.6),                   # 60% width
                    'height': int(monitor['height'] * 0.6)                  # 60% height
                }
                
                screenshot = sct.grab(roi)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)
                
                # Preprocess image
                img = self.preprocess_image(img)
                
                # OCR: extract text from image with custom configuration
                custom_config = r'--oem 3 --psm 6 -l eng --dpi 300 --tessdata-dir /opt/homebrew/share/tessdata'  # Added tessdata path
                text = pytesseract.image_to_string(img, config=custom_config)
                
                # Clean up the text
                text = text.replace('§', '')  # Remove special characters
                text = text.replace('®', '')
                text = text.replace('™', '')
                text = text.replace('~', '')
                text = text.replace('©', '')
                
                # Write results to file and log
                self.write_ocr_results(text, timestamp)
                
                self.latest_text = text.strip()
                
                # Check for images and videos
                self.has_images = self._detect_images(img)
                self.has_videos = self._detect_videos()
                
                return text
        except Exception as e:
            self.logger.error(f"Error capturing screen: {str(e)}", exc_info=True)
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