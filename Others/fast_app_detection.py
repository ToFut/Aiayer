#!/usr/bin/env python3
"""
Fast Application Detection System
A lightweight, efficient alternative to LLaVA for screen understanding.
"""
import os
import sys
import time
import json
import logging
import hashlib
import mss
import mss.tools
import base64
import re
import asyncio
import threading
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict, field
from PIL import Image
import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import tensorflow as tf
import requests
from concurrent.futures import ThreadPoolExecutor

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/fast_app_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fast_app_detection")

# Path constants
CACHE_DIR = "cache/fast_app_detection"
MODELS_DIR = "models/app_detection"

# Ensure directories exist
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)

@dataclass
class WindowInfo:
    """Information about a window/application"""
    title: str = ""
    app_name: str = ""
    process_name: str = ""
    pid: int = 0
    bundle_id: str = ""  # macOS specific
    window_id: str = ""  # Platform specific identifier
    foreground: bool = False

@dataclass
class AppSignature:
    """Application signature data for pattern matching"""
    name: str
    category: str = ""
    icon_hash: str = ""
    window_patterns: List[str] = field(default_factory=list)
    ui_patterns: Dict[str, List[str]] = field(default_factory=dict)
    color_profile: Optional[Dict[str, Any]] = None

@dataclass
class UIElement:
    """UI element data extracted from screen"""
    element_type: str  # button, text_field, menu, etc.
    text: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    confidence: float = 0.0

@dataclass
class DetectionResult:
    """Result of application detection"""
    app_name: str
    view_name: str = ""
    category: str = ""
    window_title: str = ""
    confidence: float = 0.0
    process_name: str = ""
    ui_elements: List[UIElement] = field(default_factory=list)
    raw_text: str = ""
    timestamp: float = field(default_factory=time.time)

class FastAppDetector:
    """
    Fast Application Detection System using a combination of techniques:
    1. Native window API queries
    2. OCR-based text extraction
    3. UI element recognition with lightweight ML
    4. Color profile and layout signature matching
    5. Application icon recognition
    """
    
    def __init__(self):
        self.loaded_models = False
        self.use_ocr = True
        self.use_ui_detection = True
        self.use_window_api = True
        self.use_color_profiles = True
        self.detection_interval = 2.0  # seconds
        
        # State tracking
        self.current_detection = None
        self.detection_history = []
        self.max_history = 20
        self.signature_db = self._load_app_signatures()
        
        # Initialize screen capture
        try:
            self.sct = mss.mss()
            logger.info("Screen capture initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize screen capture: {e}")
            self.sct = None
        
        # Thread management
        self.running = False
        self.detection_thread = None
        self._stop_event = threading.Event()
        
        # Load ML models if available
        self._load_models()
        
        # Initialize OCR settings
        if self.use_ocr:
            self._initialize_ocr()
    
    def _load_app_signatures(self) -> Dict[str, AppSignature]:
        """Load application signatures database"""
        signatures = {}
        
        # Load from file if exists
        signatures_file = f"{MODELS_DIR}/app_signatures.json"
        if os.path.exists(signatures_file):
            try:
                with open(signatures_file, 'r') as f:
                    data = json.load(f)
                
                # Convert to AppSignature objects
                for app_id, app_data in data.items():
                    signatures[app_id] = AppSignature(
                        name=app_data.get("name", ""),
                        category=app_data.get("category", ""),
                        icon_hash=app_data.get("icon_hash", ""),
                        window_patterns=app_data.get("window_patterns", []),
                        ui_patterns=app_data.get("ui_patterns", {}),
                        color_profile=app_data.get("color_profile")
                    )
                
                logger.info(f"Loaded {len(signatures)} application signatures")
                return signatures
            except Exception as e:
                logger.warning(f"Failed to load application signatures: {e}")
        
        # Define common application signatures
        signatures["finder"] = AppSignature(
            name="Finder",
            category="File Management",
            window_patterns=["Finder", "macOS Finder"],
            ui_patterns={
                "sidebar": ["Favorites", "Locations", "Tags"],
                "toolbar": ["Back", "Forward", "View", "Action", "Arrange"]
            },
            color_profile={"dominant": "#e8e8e8"}
        )
        
        signatures["chrome"] = AppSignature(
            name="Google Chrome",
            category="Web Browser",
            window_patterns=["Google Chrome", "Chrome"],
            ui_patterns={
                "omnibox": ["Search or enter website name", "http", "https"],
                "tabs": ["New Tab", "Tabs"],
                "menu": ["Bookmarks", "History", "Downloads"]
            },
            color_profile={"dominant": "#ffffff"}
        )
        
        signatures["safari"] = AppSignature(
            name="Safari",
            category="Web Browser",
            window_patterns=["Safari"],
            ui_patterns={
                "toolbar": ["Back", "Forward", "Share", "New Tab"],
                "searchbox": ["Search or enter website name"]
            },
            color_profile={"dominant": "#ffffff"}
        )
        
        signatures["vscode"] = AppSignature(
            name="Visual Studio Code",
            category="Development",
            window_patterns=["Visual Studio Code", "VS Code"],
            ui_patterns={
                "sidebar": ["EXPLORER", "SEARCH", "SOURCE CONTROL", "RUN"],
                "editor": ["Editor"]
            },
            color_profile={"dominant": "#1e1e1e"}
        )
        
        signatures["terminal"] = AppSignature(
            name="Terminal",
            category="Development",
            window_patterns=["Terminal", "Command Prompt", "Shell"],
            ui_patterns={
                "prompt": ["$", ">", "~", "bash", "zsh"]
            },
            color_profile={"dominant": "#000000"}
        )
        
        signatures["slack"] = AppSignature(
            name="Slack",
            category="Communication",
            window_patterns=["Slack"],
            ui_patterns={
                "sidebar": ["Channels", "Direct Messages", "Apps"],
                "header": ["Thread"]
            },
            color_profile={"dominant": "#3F0E40"}
        )
        
        signatures["gmail"] = AppSignature(
            name="Gmail",
            category="Communication",
            window_patterns=["Gmail", "Google Mail"],
            ui_patterns={
                "sidebar": ["Inbox", "Sent", "Drafts"],
                "toolbar": ["Compose", "More", "Labels"]
            },
            color_profile={"dominant": "#ffffff"}
        )
        
        # Add more signatures for common applications
        # ...
        
        return signatures
    
    def _load_models(self):
        """Load ML models for UI element detection if available"""
        try:
            # Check if TensorFlow models exist
            ui_model_path = f"{MODELS_DIR}/ui_element_detector.h5"
            if os.path.exists(ui_model_path) and self.use_ui_detection:
                # Load model using TensorFlow
                self.ui_element_model = tf.keras.models.load_model(ui_model_path)
                logger.info("Loaded UI element detection model")
            else:
                self.ui_element_model = None
                logger.info("UI element detection model not found, using rule-based detection")
            
            # Check if application icon recognition model exists
            icon_model_path = f"{MODELS_DIR}/app_icon_detector.h5"
            if os.path.exists(icon_model_path):
                # Load model using TensorFlow
                self.icon_model = tf.keras.models.load_model(icon_model_path)
                logger.info("Loaded application icon recognition model")
            else:
                self.icon_model = None
                logger.info("Application icon recognition model not found, using signature-based detection")
            
            self.loaded_models = True
            
        except Exception as e:
            logger.warning(f"Failed to load ML models: {e}")
            self.loaded_models = False
            self.ui_element_model = None
            self.icon_model = None
    
    def _initialize_ocr(self):
        """Initialize OCR settings"""
        try:
            # Test pytesseract availability
            pytesseract.get_tesseract_version()
            self.ocr_config = {
                'lang': 'eng',
                'config': '--psm 11 --oem 3'  # Page segmentation mode 11 (sparse text) and LSTM OCR engine
            }
            logger.info("OCR initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize OCR: {e}")
            self.use_ocr = False
    
    def start(self):
        """Start continuous detection"""
        if self.running:
            logger.warning("Detection already running")
            return
        
        self.running = True
        self._stop_event.clear()
        
        logger.info("Starting fast application detection")
        self.detection_thread = threading.Thread(target=self._detection_loop)
        self.detection_thread.daemon = True
        self.detection_thread.start()
        
        logger.info("Application detection started")
    
    def stop(self):
        """Stop continuous detection"""
        if not self.running:
            logger.warning("Detection not running")
            return
        
        logger.info("Stopping application detection")
        self._stop_event.set()
        self.running = False
        
        if self.detection_thread:
            self.detection_thread.join(timeout=5)
        
        # Clean up resources
        if self.sct:
            try:
                self.sct.close()
            except:
                pass
        
        logger.info("Application detection stopped")
    
    def _detection_loop(self):
        """Main detection loop"""
        while not self._stop_event.is_set():
            try:
                # Capture current screenshot
                screenshot = self._capture_screenshot()
                if screenshot:
                    # Perform detection
                    result = self.detect_application(screenshot)
                    
                    # Update current detection
                    self.current_detection = result
                    
                    # Add to history
                    self._update_history(result)
                    
                    # Log detection
                    logger.info(f"Detected application: {result.app_name} (confidence: {result.confidence:.2f})")
                
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
            
            # Sleep for detection interval
            time.sleep(self.detection_interval)
    
    def _capture_screenshot(self) -> Optional[Image.Image]:
        """Capture current screen"""
        try:
            if not self.sct:
                self.sct = mss.mss()
            
            # Get primary monitor
            primary_monitor = self.sct.monitors[1]  # Index 1 is usually the primary display
            
            # Capture screen
            screenshot = self.sct.grab(primary_monitor)
            
            # Convert to PIL Image
            image = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            return image
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
    
    def detect_application(self, screenshot: Image.Image) -> DetectionResult:
        """
        Detect application from screenshot using fast methods.
        
        This uses a multi-pronged approach:
        1. Query native window system APIs (fastest)
        2. Extract and analyze text using OCR (medium speed)
        3. Detect UI elements with rule-based patterns (medium speed)
        4. Use color and layout analysis (fast)
        5. Only use ML models as a last resort (slowest)
        """
        start_time = time.time()
        
        # Create empty result with default values
        result = DetectionResult(
            app_name="Unknown",
            timestamp=start_time
        )
        
        # Execute detection methods in parallel for speed
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Start all tasks
            window_api_future = executor.submit(self._get_active_window_info) if self.use_window_api else None
            ocr_future = executor.submit(self._extract_text, screenshot) if self.use_ocr else None
            color_future = executor.submit(self._analyze_color_profile, screenshot) if self.use_color_profiles else None
            
            # Get results as they complete
            window_info = window_api_future.result() if window_api_future else None
            extracted_text = ocr_future.result() if ocr_future else ""
            color_profile = color_future.result() if color_future else None
        
        # Store raw text in result
        result.raw_text = extracted_text
        
        # Detect UI elements (run after OCR since it may use OCR results)
        ui_elements = self._detect_ui_elements(screenshot, extracted_text)
        result.ui_elements = ui_elements
        
        # Process in order of speed (fastest first)
        
        # 1. Window API-based detection (fastest and most reliable)
        if window_info and window_info.app_name:
            result.app_name = window_info.app_name
            result.window_title = window_info.title
            result.process_name = window_info.process_name
            result.confidence = 0.9  # High confidence for API-based detection
            
            # Try to determine category from signature DB
            app_sig = self._find_app_by_name(window_info.app_name)
            if app_sig:
                result.category = app_sig.category
            
            # Try to determine view from window title and UI elements
            view_name = self._determine_view(window_info, extracted_text, ui_elements)
            if view_name:
                result.view_name = view_name
                
            # Log API-based detection
            logger.debug(f"API-based detection: {result.app_name}")
        
        # If we didn't get a result from the window API, try other methods
        else:
            # 2. OCR-based detection
            if extracted_text:
                app_match = self._match_app_from_text(extracted_text)
                if app_match and app_match[1] > result.confidence:
                    result.app_name = app_match[0]
                    result.confidence = app_match[1]
                    
                    # Try to determine category and view
                    app_sig = self._find_app_by_name(result.app_name)
                    if app_sig:
                        result.category = app_sig.category
                        
                        # Determine view from text and UI elements
                        view_name = self._determine_view_from_text(app_sig, extracted_text, ui_elements)
                        if view_name:
                            result.view_name = view_name
                    
                    # Log OCR-based detection
                    logger.debug(f"OCR-based detection: {result.app_name}")
            
            # 3. UI element-based detection
            if ui_elements and result.confidence < 0.7:
                app_match = self._match_app_from_ui_elements(ui_elements)
                if app_match and app_match[1] > result.confidence:
                    result.app_name = app_match[0]
                    result.confidence = app_match[1]
                    
                    # Try to determine category and view
                    app_sig = self._find_app_by_name(result.app_name)
                    if app_sig:
                        result.category = app_sig.category
                        
                        # Determine view from UI elements
                        view_name = self._determine_view_from_ui(app_sig, ui_elements)
                        if view_name:
                            result.view_name = view_name
                    
                    # Log UI-based detection
                    logger.debug(f"UI-based detection: {result.app_name}")
            
            # 4. Color profile-based detection
            if color_profile and result.confidence < 0.6:
                app_match = self._match_app_from_color_profile(color_profile)
                if app_match and app_match[1] > result.confidence:
                    result.app_name = app_match[0]
                    result.confidence = app_match[1]
                    
                    # Try to determine category
                    app_sig = self._find_app_by_name(result.app_name)
                    if app_sig:
                        result.category = app_sig.category
                    
                    # Log color-based detection
                    logger.debug(f"Color-based detection: {result.app_name}")
        
        # Calculate detection time
        detection_time = time.time() - start_time
        logger.debug(f"Detection completed in {detection_time:.3f} seconds")
        
        return result
    
    def _get_active_window_info(self) -> Optional[WindowInfo]:
        """Get information about the active window using native APIs"""
        window_info = WindowInfo(foreground=True)
        
        try:
            # macOS specific implementation
            if sys.platform == "darwin":
                # Use AppleScript to get window information
                script = '''
                tell application "System Events"
                    set frontApp to name of first application process whose frontmost is true
                    set frontAppId to bundle identifier of first application process whose frontmost is true
                    
                    set windowTitle to ""
                    set windowId to ""
                    
                    try
                        set windowTitle to name of front window of first application process whose frontmost is true
                        set windowId to id of front window of first application process whose frontmost is true
                    end try
                    
                    return {frontApp, windowTitle, frontAppId, windowId}
                end tell
                '''
                
                result = os.popen(f'osascript -e \'{script}\'').read().strip()
                if result:
                    parts = result.split(", ")
                    if len(parts) >= 2:
                        window_info.app_name = parts[0]
                        window_info.title = parts[1] if len(parts) > 1 else ""
                        window_info.bundle_id = parts[2] if len(parts) > 2 else ""
                        window_info.window_id = parts[3] if len(parts) > 3 else ""
                        window_info.process_name = window_info.app_name
                        
                        # Try to get process ID
                        pid_cmd = f'pgrep "{window_info.app_name}"'
                        pid_result = os.popen(pid_cmd).read().strip()
                        if pid_result:
                            try:
                                window_info.pid = int(pid_result.split("\n")[0])
                            except ValueError:
                                pass
            
            # Windows specific implementation
            elif sys.platform == "win32":
                try:
                    # For Windows, we need to import the win32 modules
                    import win32gui
                    import win32process
                    import win32api
                    
                    # Get foreground window handle
                    hwnd = win32gui.GetForegroundWindow()
                    
                    # Get window title
                    window_info.title = win32gui.GetWindowText(hwnd)
                    
                    # Get process ID
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    window_info.pid = pid
                    
                    # Get process name
                    try:
                        handle = win32api.OpenProcess(0x0400 | 0x0010, False, pid)
                        window_info.process_name = win32process.GetModuleFileNameEx(handle, 0)
                        
                        # Extract application name from process path
                        window_info.app_name = os.path.basename(window_info.process_name)
                        if window_info.app_name.lower().endswith('.exe'):
                            window_info.app_name = window_info.app_name[:-4]
                    except:
                        pass
                    
                    # Store window handle as window_id
                    window_info.window_id = str(hwnd)
                    
                except ImportError:
                    logger.warning("win32 modules not available, cannot get window info")
                    return None
            
            # Linux specific implementation
            elif sys.platform.startswith("linux"):
                try:
                    # For Linux, try using xprop or other X11 utilities
                    # Get active window ID
                    window_id_cmd = "xprop -root 32x '\t$0' _NET_ACTIVE_WINDOW | cut -f 2"
                    window_id = os.popen(window_id_cmd).read().strip()
                    window_info.window_id = window_id
                    
                    if window_id and window_id != "0x0":
                        # Get window title
                        title_cmd = f"xprop -id {window_id} _NET_WM_NAME | sed -e 's/_NET_WM_NAME(UTF8_STRING) = //'"
                        window_info.title = os.popen(title_cmd).read().strip().strip('"')
                        
                        # Get window class (application name)
                        class_cmd = f"xprop -id {window_id} WM_CLASS | cut -d '\"' -f 4"
                        window_info.app_name = os.popen(class_cmd).read().strip()
                        
                        # Get PID
                        pid_cmd = f"xprop -id {window_id} _NET_WM_PID | cut -d ' ' -f 3"
                        pid_result = os.popen(pid_cmd).read().strip()
                        if pid_result:
                            try:
                                window_info.pid = int(pid_result)
                                
                                # Get process name from PID
                                if window_info.pid > 0:
                                    cmd_cmd = f"ps -p {window_info.pid} -o comm="
                                    window_info.process_name = os.popen(cmd_cmd).read().strip()
                            except ValueError:
                                pass
                except Exception as e:
                    logger.warning(f"Error getting Linux window info: {e}")
                    return None
            
            # If we got valid info, return it
            if window_info.app_name:
                return window_info
            else:
                return None
                
        except Exception as e:
            logger.warning(f"Error getting active window info: {e}")
            return None
    
    def _extract_text(self, image: Image.Image) -> str:
        """Extract text from image using OCR"""
        if not self.use_ocr:
            return ""
        
        try:
            # Convert to grayscale
            gray_image = image.convert('L')
            
            # Resize if too large (improves OCR performance)
            width, height = gray_image.size
            if width > 1920:
                ratio = 1920 / width
                new_size = (int(width * ratio), int(height * ratio))
                gray_image = gray_image.resize(new_size, Image.LANCZOS)
            
            # Convert to numpy array for OpenCV processing
            img_np = np.array(gray_image)
            
            # Apply adaptive thresholding for better text extraction
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
            data = pytesseract.image_to_data(enhanced_image, output_type=Output.DICT, **self.ocr_config)
            
            # Combine all text blocks with confidence filtering
            text_blocks = []
            for i in range(len(data['text'])):
                # Higher confidence threshold of 60%
                if int(data['conf'][i]) > 60 and data['text'][i].strip():
                    text_blocks.append(data['text'][i])
            
            result = ' '.join(text_blocks)
            logger.debug(f"OCR extracted {len(text_blocks)} text blocks, total length: {len(result)}")
            return result
        
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            return ""
    
    def _detect_ui_elements(self, image: Image.Image, text: str = "") -> List[UIElement]:
        """
        Detect UI elements in the image using rule-based approach or ML model.
        Returns a list of UIElement objects.
        """
        if not self.use_ui_detection:
            return []
        
        ui_elements = []
        
        try:
            # Convert image to numpy array
            img_np = np.array(image)
            
            # Use OpenCV to detect potential UI elements
            # Convert to grayscale
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            
            # Detect edges
            edges = cv2.Canny(gray, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Process contours to find potential UI elements
            for contour in contours:
                # Filter out tiny or huge contours
                area = cv2.contourArea(contour)
                if area < 100 or area > 100000:
                    continue
                
                # Get bounding box
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check aspect ratio (filter out extremely wide or tall elements)
                aspect_ratio = w / h
                if aspect_ratio > 10 or aspect_ratio < 0.1:
                    continue
                
                # Extract the region
                roi = img_np[y:y+h, x:x+w]
                
                # Determine element type based on appearance
                element_type = self._classify_ui_element(roi, text, x, y, w, h)
                
                # If we identified an element type, add it to the list
                if element_type:
                    # Extract text from this region if not already done
                    element_text = ""
                    try:
                        if self.use_ocr:
                            roi_pil = Image.fromarray(roi)
                            element_text = pytesseract.image_to_string(roi_pil, config='--psm 7').strip()
                    except:
                        pass
                    
                    # Create UI element
                    ui_element = UIElement(
                        element_type=element_type,
                        text=element_text,
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        confidence=0.7  # Default confidence for rule-based detection
                    )
                    
                    ui_elements.append(ui_element)
            
            logger.debug(f"Detected {len(ui_elements)} UI elements")
            return ui_elements
            
        except Exception as e:
            logger.error(f"Error detecting UI elements: {e}")
            return []
    
    def _classify_ui_element(self, roi: np.ndarray, text: str, x: int, y: int, w: int, h: int) -> str:
        """
        Classify UI element type based on appearance and position.
        Returns element type (button, text_field, etc.) or empty string if can't classify.
        """
        try:
            # Simple rule-based classification
            
            # Check aspect ratio
            aspect_ratio = w / h
            
            # Check colors
            try:
                mean_color = cv2.mean(roi)[:3]  # RGB mean
                std_dev = np.std(roi, axis=(0, 1))[:3]  # RGB standard deviation
                
                # Check for solid background (low std_dev)
                is_solid = all(std < 30 for std in std_dev)
                
                # Check for light vs dark background
                is_light = sum(mean_color) / 3 > 128
                
                # Button: often has solid background, rounded corners, border
                if is_solid and 0.5 < aspect_ratio < 5:
                    # Convert to grayscale
                    gray_roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
                    
                    # Check for border or edge
                    edges = cv2.Canny(gray_roi, 50, 150)
                    edge_ratio = np.sum(edges > 0) / (w * h)
                    
                    if 0.05 < edge_ratio < 0.5:
                        return "button"
                
                # Text field: often has white or light background, border, rectangular
                if is_light and 2 < aspect_ratio < 10:
                    # Check border
                    gray_roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
                    edges = cv2.Canny(gray_roi, 50, 150)
                    edge_points = np.sum(edges > 0)
                    perimeter = 2 * (w + h)
                    edge_perimeter_ratio = edge_points / perimeter
                    
                    if 0.3 < edge_perimeter_ratio < 3:
                        return "text_field"
                
                # Checkbox: small, square
                if 0.8 < aspect_ratio < 1.2 and w < 50 and h < 50:
                    return "checkbox"
                
                # Dropdown: medium width, short height, often with arrow
                if 3 < aspect_ratio < 10 and h < 50:
                    # Look for dropdown arrow
                    # (this is a simple approach - a more robust method would use
                    # image matching or neural networks)
                    return "dropdown"
                
                # Menu item: wide, short
                if aspect_ratio > 5 and h < 40:
                    return "menu_item"
                
                # Icon: small, square-ish
                if 0.75 < aspect_ratio < 1.5 and w < 64 and h < 64:
                    return "icon"
                
                # Tab: medium width, short height, often at top
                if 2 < aspect_ratio < 8 and h < 40 and y < 100:
                    return "tab"
                
                # Scrollbar: very narrow or very short
                if aspect_ratio > 20 or aspect_ratio < 0.05:
                    return "scrollbar"
                
                # Fallback
                return "unknown"
                
            except Exception as e:
                logger.debug(f"Error analyzing UI element colors: {e}")
                return "unknown"
                
        except Exception as e:
            logger.debug(f"Error classifying UI element: {e}")
            return ""
    
    def _analyze_color_profile(self, image: Image.Image) -> Dict[str, Any]:
        """
        Analyze color profile of the image to help identify applications.
        Returns a dictionary with color analysis information.
        """
        try:
            # Resize image for faster processing
            resized = image.resize((100, 100), Image.LANCZOS)
            
            # Convert to numpy array
            img_np = np.array(resized)
            
            # Calculate color histogram
            hist = {}
            for channel, color in enumerate(['red', 'green', 'blue']):
                hist[color] = np.histogram(img_np[:,:,channel], bins=8, range=(0, 256))[0].tolist()
            
            # Find dominant colors
            pixels = img_np.reshape(-1, 3)
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=5, random_state=0, n_init=10).fit(pixels)
            dominant_colors = kmeans.cluster_centers_.astype(int).tolist()
            
            # Calculate percent of each dominant color
            labels = kmeans.labels_
            counts = np.bincount(labels)
            percent_colors = (counts / counts.sum() * 100).tolist()
            
            # Calculate overall brightness
            brightness = np.mean(img_np) / 255.0
            
            # Calculate contrast
            contrast = np.std(img_np) / 255.0
            
            # Create color profile
            profile = {
                'histogram': hist,
                'dominant_colors': dominant_colors,
                'percent_colors': percent_colors,
                'brightness': brightness,
                'contrast': contrast
            }
            
            return profile
            
        except Exception as e:
            logger.error(f"Error analyzing color profile: {e}")
            return {
                'histogram': {},
                'dominant_colors': [],
                'percent_colors': [],
                'brightness': 0,
                'contrast': 0
            }
    
    def _match_app_from_text(self, text: str) -> Tuple[str, float]:
        """
        Match application based on extracted text.
        Returns (app_name, confidence) tuple.
        """
        best_match = None
        best_confidence = 0.0
        
        # Convert text to lowercase for matching
        lower_text = text.lower()
        
        # Check each signature for window pattern matches
        for app_id, signature in self.signature_db.items():
            match_count = 0
            
            # Check each window pattern
            for pattern in signature.window_patterns:
                if pattern.lower() in lower_text:
                    match_count += 1
            
            # Calculate confidence based on matches
            if match_count > 0:
                # More matching patterns = higher confidence
                confidence = min(0.7, 0.5 + (match_count / len(signature.window_patterns)) * 0.2)
                
                if confidence > best_confidence:
                    best_match = signature.name
                    best_confidence = confidence
            
            # Check UI patterns as well
            ui_match_count = 0
            total_ui_patterns = 0
            
            for section, patterns in signature.ui_patterns.items():
                total_ui_patterns += len(patterns)
                for pattern in patterns:
                    if pattern.lower() in lower_text:
                        ui_match_count += 1
            
            # Calculate UI pattern confidence
            if ui_match_count > 0 and total_ui_patterns > 0:
                ui_confidence = min(0.65, 0.4 + (ui_match_count / total_ui_patterns) * 0.25)
                
                if ui_confidence > best_confidence:
                    best_match = signature.name
                    best_confidence = ui_confidence
        
        # If we found a match, return it
        if best_match:
            return (best_match, best_confidence)
        
        # If no structured match, try common app name detection
        # This is less reliable but provides a fallback
        common_apps = [
            "Chrome", "Firefox", "Safari", "Edge", "Opera",  # Browsers
            "Word", "Excel", "PowerPoint", "Outlook", "OneNote",  # Microsoft Office
            "Gmail", "Docs", "Sheets", "Slides", "Drive",  # Google productivity
            "Photoshop", "Illustrator", "InDesign", "Lightroom", "Premiere",  # Adobe Creative Cloud
            "Visual Studio", "VS Code", "Sublime", "PyCharm", "IntelliJ",  # Code editors
            "Terminal", "Command Prompt", "PowerShell", "iTerm", "Hyper",  # Terminals
            "Slack", "Teams", "Zoom", "Discord", "Skype",  # Communication
            "Spotify", "iTunes", "Music", "VLC", "YouTube",  # Media
            "Finder", "Explorer", "Files"  # File managers
        ]
        
        for app in common_apps:
            # Check for exact app name
            pattern = r'\b' + re.escape(app) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return (app, 0.6)  # Moderate confidence for direct match
        
        return ("Unknown", 0.0)
    
    def _match_app_from_ui_elements(self, ui_elements: List[UIElement]) -> Tuple[str, float]:
        """
        Match application based on UI elements.
        Returns (app_name, confidence) tuple.
        """
        # Extract text from UI elements
        ui_texts = [element.text for element in ui_elements if element.text]
        combined_text = " ".join(ui_texts)
        
        # Use text matching on UI text
        if combined_text:
            return self._match_app_from_text(combined_text)
        
        # If no text in UI elements, try pattern matching on element types
        best_match = None
        best_confidence = 0.0
        
        # Count element types
        element_counts = {}
        for element in ui_elements:
            element_counts[element.element_type] = element_counts.get(element.element_type, 0) + 1
        
        # Check for specific UI patterns
        
        # VS Code: lots of icons, text fields
        if (element_counts.get("icon", 0) > 10 and 
            element_counts.get("text_field", 0) > 1):
            return ("Visual Studio Code", 0.55)
        
        # Terminal: one big text area, few UI elements
        if (len(ui_elements) < 5 and
            element_counts.get("text_field", 0) == 1 and
            ui_elements[0].width > 500 and
            ui_elements[0].height > 300):
            return ("Terminal", 0.6)
        
        # Browsers: tabs at top, address bar, lots of buttons
        if (element_counts.get("tab", 0) > 1 and
            element_counts.get("text_field", 0) >= 1 and
            element_counts.get("button", 0) > 5):
            return ("Web Browser", 0.5)  # Generic browser, low confidence
        
        return (best_match or "Unknown", best_confidence)
    
    def _match_app_from_color_profile(self, color_profile: Dict[str, Any]) -> Tuple[str, float]:
        """
        Match application based on color profile.
        Returns (app_name, confidence) tuple.
        """
        best_match = None
        best_confidence = 0.0
        
        # Extract dominant colors
        dominant_colors = color_profile.get('dominant_colors', [])
        percent_colors = color_profile.get('percent_colors', [])
        brightness = color_profile.get('brightness', 0)
        contrast = color_profile.get('contrast', 0)
        
        if not dominant_colors or not percent_colors:
            return ("Unknown", 0.0)
        
        # Check each signature for color profile matches
        for app_id, signature in self.signature_db.items():
            # Skip signatures without color profiles
            if not signature.color_profile:
                continue
            
            # Get dominant color from signature
            sig_dominant = signature.color_profile.get('dominant')
            if sig_dominant and sig_dominant.startswith('#'):
                # Convert hex color to RGB
                r = int(sig_dominant[1:3], 16)
                g = int(sig_dominant[3:5], 16)
                b = int(sig_dominant[5:7], 16)
                sig_color = [r, g, b]
                
                # Check if any dominant color matches
                color_match = False
                for i, color in enumerate(dominant_colors):
                    # Calculate color distance
                    distance = sum((c1 - c2) ** 2 for c1, c2 in zip(color, sig_color)) ** 0.5
                    
                    # If close enough and significant percentage
                    if distance < 60 and percent_colors[i] > 10:
                        color_match = True
                        break
                
                if color_match:
                    confidence = 0.4  # Base confidence for color match
                    
                    # Adjust based on brightness and contrast if specified in signature
                    if 'brightness' in signature.color_profile and 'contrast' in signature.color_profile:
                        sig_brightness = signature.color_profile['brightness']
                        sig_contrast = signature.color_profile['contrast']
                        
                        # Calculate difference
                        brightness_diff = abs(brightness - sig_brightness)
                        contrast_diff = abs(contrast - sig_contrast)
                        
                        # Adjust confidence
                        if brightness_diff < 0.2 and contrast_diff < 0.2:
                            confidence += 0.1
                    
                    if confidence > best_confidence:
                        best_match = signature.name
                        best_confidence = confidence
        
        # Some common color-based heuristics
        
        # Very dark with low contrast: likely terminal or code editor
        if brightness < 0.2 and contrast < 0.3 and not best_match:
            return ("Terminal", 0.35)
        
        # Very white with colored elements: likely browser or document
        if brightness > 0.8 and contrast < 0.4 and not best_match:
            return ("Web Browser", 0.3)
        
        return (best_match or "Unknown", best_confidence)
    
    def _find_app_by_name(self, app_name: str) -> Optional[AppSignature]:
        """Find app signature by name or close match"""
        # Look for exact match
        for app_id, signature in self.signature_db.items():
            if signature.name.lower() == app_name.lower():
                return signature
        
        # Look for partial match
        for app_id, signature in self.signature_db.items():
            if app_name.lower() in signature.name.lower() or signature.name.lower() in app_name.lower():
                return signature
        
        return None
    
    def _determine_view(self, window_info: WindowInfo, text: str, ui_elements: List[UIElement]) -> str:
        """Determine view from window info, text, and UI elements"""
        # Try from window title first
        if window_info.title:
            # Remove app name from title
            title = window_info.title
            if window_info.app_name and window_info.app_name in title:
                title = title.replace(window_info.app_name, "").strip(" -–:")
            
            # If meaningful title remains, use it as view
            if title and len(title) > 1:
                return title
        
        # Try from app signature
        app_sig = self._find_app_by_name(window_info.app_name)
        if app_sig:
            # Try to determine view from text and UI elements
            view_name = self._determine_view_from_text(app_sig, text, ui_elements)
            if view_name:
                return view_name
        
        # Fallback to generic view determination from UI layout
        return self._determine_generic_view(ui_elements)
    
    def _determine_view_from_text(self, app_sig: AppSignature, text: str, ui_elements: List[UIElement]) -> str:
        """Determine view from text and UI patterns"""
        # Check UI patterns for this application
        lower_text = text.lower()
        
        for view_name, patterns in app_sig.ui_patterns.items():
            match_count = 0
            for pattern in patterns:
                if pattern.lower() in lower_text:
                    match_count += 1
            
            # If we have enough matches, consider it this view
            if match_count >= max(1, len(patterns) // 3):
                return view_name.replace("_", " ").capitalize()
        
        # Common view keywords
        view_keywords = {
            "settings": ["settings", "preferences", "options", "config"],
            "home": ["home", "main screen", "dashboard", "overview"],
            "details": ["details", "properties", "info", "information"],
            "edit": ["edit", "editing", "modify", "change"],
            "create": ["create", "new", "add", "compose"],
            "list": ["list", "all", "items", "browse"],
            "search": ["search", "find", "query", "results"],
            "profile": ["profile", "account", "user", "personal"]
        }
        
        for view_name, keywords in view_keywords.items():
            for keyword in keywords:
                if keyword in lower_text:
                    return view_name.capitalize()
        
        return ""
    
    def _determine_view_from_ui(self, app_sig: AppSignature, ui_elements: List[UIElement]) -> str:
        """Determine view from UI elements"""
        # Extract text from UI elements
        ui_texts = [element.text for element in ui_elements if element.text]
        combined_text = " ".join(ui_texts)
        
        # Use text-based view determination
        if combined_text:
            return self._determine_view_from_text(app_sig, combined_text, ui_elements)
        
        return ""
    
    def _determine_generic_view(self, ui_elements: List[UIElement]) -> str:
        """Determine generic view from UI layout"""
        # Count element types
        element_counts = {}
        for element in ui_elements:
            element_counts[element.element_type] = element_counts.get(element.element_type, 0) + 1
        
        # Check for common layouts
        
        # Many text fields: likely form or editor
        if element_counts.get("text_field", 0) > 3:
            return "Form"
        
        # Many buttons: likely toolbar or settings
        if element_counts.get("button", 0) > 10:
            return "Tools"
        
        # Tabs: likely tabbed interface
        if element_counts.get("tab", 0) > 1:
            return "Tabbed View"
        
        # Menu items: likely menu
        if element_counts.get("menu_item", 0) > 5:
            return "Menu"
        
        return "Main View"
    
    def _update_history(self, result: DetectionResult):
        """Update detection history"""
        # Add to history
        self.detection_history.append(asdict(result))
        
        # Trim history if needed
        if len(self.detection_history) > self.max_history:
            self.detection_history = self.detection_history[-self.max_history:]
    
    def get_current_detection(self) -> Optional[DetectionResult]:
        """Get the current detection result"""
        return self.current_detection
    
    def get_detection_history(self) -> List[Dict[str, Any]]:
        """Get detection history"""
        return self.detection_history

async def main():
    """Main function for running the detector"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fast Application Detection")
    parser.add_argument("--run", action="store_true", help="Run continuous detection service")
    parser.add_argument("--time", type=int, default=60, help="Run time in seconds for continuous detection (default: 60)")
    parser.add_argument("--interval", type=float, default=2.0, help="Detection interval in seconds (default: 2.0)")
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR for faster performance")
    parser.add_argument("--no-ui", action="store_true", help="Disable UI element detection for faster performance")
    parser.add_argument("--no-color", action="store_true", help="Disable color profile analysis for faster performance")
    
    args = parser.parse_args()
    
    # Create detector
    detector = FastAppDetector()
    
    # Configure detector
    if args.no_ocr:
        detector.use_ocr = False
    if args.no_ui:
        detector.use_ui_detection = False
    if args.no_color:
        detector.use_color_profiles = False
    detector.detection_interval = args.interval
    
    if args.run:
        print(f"Starting fast application detection for {args.time} seconds")
        print(f"Detection interval: {args.interval} seconds")
        print(f"OCR enabled: {detector.use_ocr}")
        print(f"UI detection enabled: {detector.use_ui_detection}")
        print(f"Color profiles enabled: {detector.use_color_profiles}")
        
        # Start detector
        detector.start()
        
        # Run for specified time
        try:
            for i in range(args.time):
                await asyncio.sleep(1)
                if i % 5 == 0:  # Print status every 5 seconds
                    detection = detector.get_current_detection()
                    if detection:
                        print(f"Current app: {detection.app_name} (view: {detection.view_name}, confidence: {detection.confidence:.2f})")
        except KeyboardInterrupt:
            print("\nStopping detection due to user interrupt")
        finally:
            # Stop detector
            detector.stop()
            
        # Print detection summary
        history = detector.get_detection_history()
        print("\n===== DETECTION SUMMARY =====")
        print(f"Total detections: {len(history)}")
        if history:
            apps = {}
            for entry in history:
                app = entry.get("app_name", "Unknown")
                apps[app] = apps.get(app, 0) + 1
                
            print("\nDetected applications:")
            for app, count in sorted(apps.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {app}: {count} times")
                
            # Performance stats
            if len(history) > 1:
                first_time = history[0].get("timestamp", 0)
                last_time = history[-1].get("timestamp", 0)
                if last_time > first_time:
                    total_time = last_time - first_time
                    detections_per_second = len(history) / total_time
                    print(f"\nPerformance: {detections_per_second:.2f} detections/second")
                    
        print("=============================")
    else:
        # Run a single detection on the current screen
        image = detector._capture_screenshot()
        if image:
            print("Analyzing current screen...")
            result = detector.detect_application(image)
            
            print("\n===== DETECTION RESULTS =====")
            print(f"Application: {result.app_name}")
            print(f"Confidence:  {result.confidence:.2f}")
            print(f"Category:    {result.category}")
            print(f"View:        {result.view_name}")
            print(f"Window Title: {result.window_title}")
            print("-----------------------------")
            print(f"UI Elements: {len(result.ui_elements)} detected")
            for i, ui in enumerate(result.ui_elements[:5]):  # Show up to 5 elements
                print(f"  - {ui.element_type}: {ui.text[:30]}{'...' if len(ui.text) > 30 else ''}")
            if len(result.ui_elements) > 5:
                print(f"  ... and {len(result.ui_elements) - 5} more")
            print("=============================")
        else:
            print("Error: Could not capture screenshot")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nScript terminated by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)