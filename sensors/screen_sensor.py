"""
Screen Sensor Module
Captures screenshots and extracts text via OCR.
"""
import mss
import mss.tools
import pytesseract
from PIL import Image
import threading
import time
import logging

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
        
        # Configure pytesseract path if needed
        # Uncomment and set this for Windows if tesseract is not in PATH
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    def capture_screen_text(self):
        """
        Capture screenshot and extract text via OCR.
        
        Returns:
            str: Extracted text from screen
        """
        try:
            with mss.mss() as sct:
                # Capture primary monitor
                monitor = sct.monitors[1]  # Primary monitor is usually 1
                screenshot = sct.grab(monitor)
                
                # Convert to PIL Image
                img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.rgb)
                
                # Optional: Save for debugging
                # img.save("debug_screenshot.png")
                
                # OCR: extract text from image
                text = pytesseract.image_to_string(img)
                self.latest_text = text.strip()
                self.logger.debug(f"Screen text captured: {len(text)} characters")
                return text
        except Exception as e:
            self.logger.error(f"Error capturing screen: {e}")
            return ""
    
    def _run_capture_loop(self):
        """Background thread function for periodic screenshot capture."""
        self.logger.info("Screen sensor started")
        self.running = True
        
        while self.running:
            try:
                self.capture_screen_text()
            except Exception as e:
                self.logger.error(f"Error in screen capture loop: {e}")
            
            # Sleep for the specified interval
            time.sleep(self.interval)
    
    def start(self):
        """Start periodic capture in a background thread."""
        if self.thread is not None and self.thread.is_alive():
            self.logger.warning("Screen sensor already running")
            return
        
        self.thread = threading.Thread(target=self._run_capture_loop, daemon=True)
        self.thread.start()
        self.logger.info(f"Screen sensor thread started with {self.interval}s interval")
    
    def stop(self):
        """Stop the background thread."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            self.logger.info("Screen sensor stopped")

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