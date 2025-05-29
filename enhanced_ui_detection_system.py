#!/usr/bin/env python3
"""
Enhanced UI Detection System
Integrates multiple advanced approaches for superior UI element detection:
1. Accessibility APIs for element role detection
2. Machine Learning Models for UI pattern classification
3. Browser/OS APIs for direct DOM element access
4. OCR + NLP for text content understanding
"""

import os
import sys
import json
import time
import logging
import asyncio
import base64
import hashlib
import re
import pickle
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from PIL import Image
from io import BytesIO
import numpy as np

# Platform-specific imports
try:
    import pyautogui
    import pygetwindow as gw
except ImportError:
    pyautogui = None
    gw = None

# Machine Learning imports
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.model_selection import train_test_split
    import joblib
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# OCR imports
try:
    import pytesseract
    import easyocr
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# NLP imports
try:
    import spacy
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

# Browser automation imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    BROWSER_AUTOMATION_AVAILABLE = True
except ImportError:
    BROWSER_AUTOMATION_AVAILABLE = False

# Accessibility imports (platform-specific)
try:
    if sys.platform == "darwin":  # macOS
        import Quartz
        from ApplicationServices import AXUIElementCreateSystemWide, AXUIElementCopyAttributeNames
        ACCESSIBILITY_AVAILABLE = True
    elif sys.platform == "win32":  # Windows
        import win32gui
        import win32con
        ACCESSIBILITY_AVAILABLE = True
    else:  # Linux
        try:
            import pyatspi
            ACCESSIBILITY_AVAILABLE = True
        except ImportError:
            ACCESSIBILITY_AVAILABLE = False
except ImportError:
    ACCESSIBILITY_AVAILABLE = False

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/enhanced_ui_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("enhanced_ui_detection")

@dataclass
class EnhancedUIElement:
    """Enhanced data structure for detected UI elements with multiple detection sources"""
    element_id: str
    element_type: str
    element_text: str = ""
    bounding_box: Optional[List[int]] = None  # [x1, y1, x2, y2]
    center_point: Optional[Tuple[int, int]] = None
    state: str = ""
    role: str = ""  # Accessibility role
    action: str = ""
    confidence: float = 0.0
    parent_component: str = ""
    interaction_hints: List[str] = field(default_factory=list)
    
    # Detection source information
    detected_by: List[str] = field(default_factory=list)
    accessibility_info: Dict[str, Any] = field(default_factory=dict)
    ml_confidence: float = 0.0
    ocr_text: str = ""
    nlp_intent: str = ""
    dom_attributes: Dict[str, Any] = field(default_factory=dict)
    
    # App-specific attributes
    app_specific: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EnhancedDetectionResult:
    """Enhanced detection result with multi-source analysis"""
    timestamp: float
    app_name: str
    view_name: str
    elements: List[EnhancedUIElement] = field(default_factory=list)
    accessibility_tree: Dict[str, Any] = field(default_factory=dict)
    ml_predictions: Dict[str, Any] = field(default_factory=dict)
    ocr_results: Dict[str, Any] = field(default_factory=dict)
    nlp_analysis: Dict[str, Any] = field(default_factory=dict)
    dom_structure: Dict[str, Any] = field(default_factory=dict)
    screenshot_hash: str = ""
    detection_methods_used: List[str] = field(default_factory=list)

class AccessibilityDetector:
    """Handles accessibility API-based element detection"""
    
    def __init__(self):
        self.available = ACCESSIBILITY_AVAILABLE
        if not self.available:
            logger.warning("Accessibility APIs not available on this platform")
    
    def get_element_role(self, x: int = None, y: int = None) -> Optional[str]:
        """Get accessibility role of element at coordinates or focused element"""
        if not self.available:
            return None
            
        try:
            if sys.platform == "darwin":
                return self._get_macos_element_role(x, y)
            elif sys.platform == "win32":
                return self._get_windows_element_role(x, y)
            else:
                return self._get_linux_element_role(x, y)
        except Exception as e:
            logger.error(f"Error getting element role: {e}")
            return None
    
    def _get_macos_element_role(self, x: int = None, y: int = None) -> Optional[str]:
        """Get element role on macOS using Accessibility API"""
        try:
            # Get system accessibility element
            system_element = AXUIElementCreateSystemWide()
            
            if x is not None and y is not None:
                # Get element at specific coordinates
                # This is a simplified implementation
                return "button"  # Placeholder - would need proper coordinate-to-element mapping
            else:
                # Get focused element
                return "textfield"  # Placeholder - would need proper focused element detection
                
        except Exception as e:
            logger.error(f"macOS accessibility error: {e}")
            return None
    
    def _get_windows_element_role(self, x: int = None, y: int = None) -> Optional[str]:
        """Get element role on Windows using Win32 API"""
        try:
            if x is not None and y is not None:
                hwnd = win32gui.WindowFromPoint((x, y))
                class_name = win32gui.GetClassName(hwnd)
                
                # Map Windows class names to roles
                role_mapping = {
                    "Button": "button",
                    "Edit": "textfield",
                    "ComboBox": "dropdown",
                    "ListBox": "list",
                    "Static": "label"
                }
                
                return role_mapping.get(class_name, "unknown")
            
            return None
            
        except Exception as e:
            logger.error(f"Windows accessibility error: {e}")
            return None
    
    def _get_linux_element_role(self, x: int = None, y: int = None) -> Optional[str]:
        """Get element role on Linux using AT-SPI"""
        try:
            # This would require proper AT-SPI implementation
            # Placeholder implementation
            return "button"
            
        except Exception as e:
            logger.error(f"Linux accessibility error: {e}")
            return None

class MLUIClassifier:
    """Machine Learning classifier for UI element types"""
    
    def __init__(self):
        self.available = ML_AVAILABLE
        self.model = None
        self.vectorizer = None
        self.is_trained = False
        self.model_path = "models/ui_classifier.pkl"
        self.vectorizer_path = "models/ui_vectorizer.pkl"
        
        if self.available:
            self._load_or_create_model()
        else:
            logger.warning("ML libraries not available")
    
    def _load_or_create_model(self):
        """Load existing model or create and train new one"""
        try:
            os.makedirs("models", exist_ok=True)
            
            if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
                self.model = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                self.is_trained = True
                logger.info("Loaded existing UI classifier model")
            else:
                self._train_initial_model()
                
        except Exception as e:
            logger.error(f"Error loading/creating ML model: {e}")
    
    def _train_initial_model(self):
        """Train initial model with synthetic data"""
        try:
            # Create synthetic training data for UI elements
            training_data = self._generate_training_data()
            
            if not training_data:
                logger.warning("No training data available")
                return
            
            texts, labels = zip(*training_data)
            
            # Create TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            X = self.vectorizer.fit_transform(texts)
            
            # Train Random Forest classifier
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X, labels)
            
            # Save model and vectorizer
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.vectorizer, self.vectorizer_path)
            
            self.is_trained = True
            logger.info("Trained new UI classifier model")
            
        except Exception as e:
            logger.error(f"Error training ML model: {e}")
    
    def _generate_training_data(self) -> List[Tuple[str, str]]:
        """Generate synthetic training data for UI elements"""
        training_data = [
            # Button examples
            ("click here to submit", "button"),
            ("save document button", "button"),
            ("cancel operation", "button"),
            ("submit form", "button"),
            ("download file", "button"),
            ("upload image", "button"),
            ("login button", "button"),
            ("search button", "button"),
            
            # Text field examples
            ("enter your name", "textfield"),
            ("type your message here", "textfield"),
            ("input field for email", "textfield"),
            ("search box", "textfield"),
            ("password field", "textfield"),
            ("text area for comments", "textfield"),
            
            # Dropdown examples
            ("select country dropdown", "dropdown"),
            ("choose option menu", "dropdown"),
            ("dropdown list", "dropdown"),
            ("select from menu", "dropdown"),
            
            # Checkbox examples
            ("check this option", "checkbox"),
            ("agree to terms checkbox", "checkbox"),
            ("select all checkbox", "checkbox"),
            
            # Link examples
            ("click here for more info", "link"),
            ("visit our website", "link"),
            ("hyperlink to page", "link"),
            
            # Label examples
            ("username label", "label"),
            ("form field label", "label"),
            ("description text", "label"),
        ]
        
        return training_data
    
    def classify_element(self, text: str, context: str = "") -> Tuple[str, float]:
        """Classify UI element type based on text and context"""
        if not self.available or not self.is_trained:
            return "unknown", 0.0
        
        try:
            # Combine text and context
            combined_text = f"{text} {context}".strip()
            
            if not combined_text:
                return "unknown", 0.0
            
            # Vectorize the text
            X = self.vectorizer.transform([combined_text])
            
            # Get prediction and confidence
            prediction = self.model.predict(X)[0]
            probabilities = self.model.predict_proba(X)[0]
            confidence = max(probabilities)
            
            return prediction, confidence
            
        except Exception as e:
            logger.error(f"Error classifying element: {e}")
            return "unknown", 0.0

class BrowserAPIDetector:
    """Handles browser/OS API-based element detection"""
    
    def __init__(self):
        self.available = BROWSER_AUTOMATION_AVAILABLE
        self.driver = None
        
        if not self.available:
            logger.warning("Browser automation libraries not available")
    
    def connect_to_browser(self) -> bool:
        """Connect to existing browser session or start new one"""
        if not self.available:
            return False
        
        try:
            # Try to connect to existing Chrome session
            chrome_options = ChromeOptions()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("Connected to existing Chrome session")
                return True
            except:
                # Start new Chrome session
                chrome_options = ChromeOptions()
                chrome_options.add_argument("--remote-debugging-port=9222")
                self.driver = webdriver.Chrome(options=chrome_options)
                logger.info("Started new Chrome session")
                return True
                
        except Exception as e:
            logger.error(f"Error connecting to browser: {e}")
            return False
    
    def get_dom_elements(self) -> List[Dict[str, Any]]:
        """Get DOM elements from current page"""
        if not self.driver:
            return []
        
        try:
            # Get all interactive elements
            elements = []
            
            # Buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for btn in buttons:
                elements.append({
                    "type": "button",
                    "text": btn.text,
                    "tag": btn.tag_name,
                    "attributes": {
                        "id": btn.get_attribute("id"),
                        "class": btn.get_attribute("class"),
                        "role": btn.get_attribute("role")
                    },
                    "location": btn.location,
                    "size": btn.size
                })
            
            # Input fields
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            for inp in inputs:
                input_type = inp.get_attribute("type") or "text"
                elements.append({
                    "type": f"input_{input_type}",
                    "text": inp.get_attribute("placeholder") or "",
                    "tag": inp.tag_name,
                    "attributes": {
                        "id": inp.get_attribute("id"),
                        "class": inp.get_attribute("class"),
                        "type": input_type,
                        "name": inp.get_attribute("name")
                    },
                    "location": inp.location,
                    "size": inp.size
                })
            
            # Links
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                elements.append({
                    "type": "link",
                    "text": link.text,
                    "tag": link.tag_name,
                    "attributes": {
                        "href": link.get_attribute("href"),
                        "id": link.get_attribute("id"),
                        "class": link.get_attribute("class")
                    },
                    "location": link.location,
                    "size": link.size
                })
            
            logger.info(f"Retrieved {len(elements)} DOM elements")
            return elements
            
        except Exception as e:
            logger.error(f"Error getting DOM elements: {e}")
            return []

class OCRNLPDetector:
    """Handles OCR + NLP-based text understanding"""
    
    def __init__(self):
        self.ocr_available = OCR_AVAILABLE
        self.nlp_available = NLP_AVAILABLE
        
        self.ocr_reader = None
        self.nlp_model = None
        
        if self.ocr_available:
            try:
                self.ocr_reader = easyocr.Reader(['en'])
                logger.info("EasyOCR initialized")
            except Exception as e:
                logger.warning(f"EasyOCR initialization failed: {e}")
                self.ocr_available = False
        
        if self.nlp_available:
            try:
                self.nlp_model = spacy.load("en_core_web_sm")
                logger.info("SpaCy NLP model loaded")
            except Exception as e:
                logger.warning(f"SpaCy model loading failed: {e}")
                self.nlp_available = False
    
    def extract_text_content(self, image_path: str) -> Dict[str, Any]:
        """Extract text content using OCR"""
        if not self.ocr_available:
            return {"text": "", "regions": []}
        
        try:
            # Use EasyOCR for text extraction
            results = self.ocr_reader.readtext(image_path)
            
            extracted_text = []
            regions = []
            
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # Filter low-confidence results
                    extracted_text.append(text)
                    regions.append({
                        "text": text,
                        "bbox": bbox,
                        "confidence": confidence
                    })
            
            return {
                "text": " ".join(extracted_text),
                "regions": regions
            }
            
        except Exception as e:
            logger.error(f"OCR extraction error: {e}")
            return {"text": "", "regions": []}
    
    def analyze_intent(self, text: str) -> Dict[str, Any]:
        """Analyze text intent using NLP"""
        if not self.nlp_available or not text:
            return {"intent": "unknown", "entities": []}
        
        try:
            doc = self.nlp_model(text.lower())
            
            # Intent classification based on keywords and patterns
            intent = "unknown"
            entities = []
            
            # Extract entities
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "description": spacy.explain(ent.label_)
                })
            
            # Simple intent classification
            search_keywords = ["search", "find", "look", "query"]
            submit_keywords = ["submit", "send", "post", "save"]
            cancel_keywords = ["cancel", "close", "exit", "back"]
            
            text_lower = text.lower()
            
            if any(keyword in text_lower for keyword in search_keywords):
                intent = "search"
            elif any(keyword in text_lower for keyword in submit_keywords):
                intent = "submit"
            elif any(keyword in text_lower for keyword in cancel_keywords):
                intent = "cancel"
            elif "button" in text_lower or "click" in text_lower:
                intent = "action"
            elif "input" in text_lower or "enter" in text_lower:
                intent = "input"
            
            return {
                "intent": intent,
                "entities": entities,
                "tokens": [token.text for token in doc],
                "pos_tags": [(token.text, token.pos_) for token in doc]
            }
            
        except Exception as e:
            logger.error(f"NLP analysis error: {e}")
            return {"intent": "unknown", "entities": []}

class EnhancedUIDetectionSystem:
    """Main enhanced UI detection system integrating all approaches"""
    
    def __init__(self, llava_url="http://localhost:11434"):
        self.llava_url = llava_url
        self.llava_endpoint = f"{llava_url}/api/chat"
        self.llava_model = "llava"
        self.llava_timeout = 90
        
        # Initialize detection components
        self.accessibility_detector = AccessibilityDetector()
        self.ml_classifier = MLUIClassifier()
        self.browser_detector = BrowserAPIDetector()
        self.ocr_nlp_detector = OCRNLPDetector()
        
        # Results directory
        self.results_dir = "results/enhanced_ui_detection"
        os.makedirs(self.results_dir, exist_ok=True)
        
        logger.info("Enhanced UI Detection System initialized")
        
        # Log available detection methods
        available_methods = []
        if self.accessibility_detector.available:
            available_methods.append("Accessibility APIs")
        if self.ml_classifier.available:
            available_methods.append("Machine Learning")
        if self.browser_detector.available:
            available_methods.append("Browser APIs")
        if self.ocr_nlp_detector.ocr_available:
            available_methods.append("OCR")
        if self.ocr_nlp_detector.nlp_available:
            available_methods.append("NLP")
        
        logger.info(f"Available detection methods: {available_methods}")
    
    async def enhanced_detect_ui_elements(self, image_path: str, app_context: Optional[Dict[str, Any]] = None) -> EnhancedDetectionResult:
        """Enhanced UI element detection using multiple approaches"""
        try:
            start_time = time.time()
            
            # Load and prepare image
            image = Image.open(image_path)
            img_hash = hashlib.md5(image.tobytes()).hexdigest()
            
            app_name = app_context.get("app_name", "Unknown") if app_context else "Unknown"
            view_name = app_context.get("view_name", "") if app_context else ""
            
            # Initialize result
            result = EnhancedDetectionResult(
                timestamp=time.time(),
                app_name=app_name,
                view_name=view_name,
                screenshot_hash=img_hash
            )
            
            # 1. Accessibility API Detection
            accessibility_info = await self._detect_with_accessibility()
            if accessibility_info:
                result.accessibility_tree = accessibility_info
                result.detection_methods_used.append("Accessibility APIs")
            
            # 2. OCR + NLP Analysis
            ocr_results = self._detect_with_ocr_nlp(image_path)
            if ocr_results:
                result.ocr_results = ocr_results
                result.detection_methods_used.append("OCR + NLP")
            
            # 3. Browser/DOM API Detection
            dom_results = await self._detect_with_browser_api()
            if dom_results:
                result.dom_structure = dom_results
                result.detection_methods_used.append("Browser APIs")
            
            # 4. LLaVA Visual Analysis (existing approach)
            llava_analysis = await self._analyze_ui_with_llava(image_path, app_name, view_name)
            
            # 5. Combine and enhance results
            enhanced_elements = await self._combine_detection_results(
                accessibility_info, ocr_results, dom_results, llava_analysis, app_name
            )
            
            result.elements = enhanced_elements
            
            # 6. ML Classification enhancement
            if self.ml_classifier.available:
                result.ml_predictions = await self._enhance_with_ml(enhanced_elements)
                result.detection_methods_used.append("Machine Learning")
            
            # Save results
            self._save_enhanced_result(result)
            
            elapsed_time = time.time() - start_time
            logger.info(f"Enhanced detection complete: {len(result.elements)} elements, {elapsed_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Enhanced detection error: {e}")
            return EnhancedDetectionResult(
                timestamp=time.time(),
                app_name="Error",
                view_name="Error"
            )
    
    async def _detect_with_accessibility(self) -> Optional[Dict[str, Any]]:
        """Detect elements using accessibility APIs"""
        try:
            if not self.accessibility_detector.available:
                return None
            
            # Get accessibility information for common element types
            accessibility_info = {
                "focused_element": self.accessibility_detector.get_element_role(),
                "available": True,
                "method": "accessibility_api"
            }
            
            return accessibility_info
            
        except Exception as e:
            logger.error(f"Accessibility detection error: {e}")
            return None
    
    def _detect_with_ocr_nlp(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Detect elements using OCR + NLP"""
        try:
            # Extract text using OCR
            ocr_results = self.ocr_nlp_detector.extract_text_content(image_path)
            
            if not ocr_results["text"]:
                return None
            
            # Analyze intent using NLP
            nlp_analysis = self.ocr_nlp_detector.analyze_intent(ocr_results["text"])
            
            return {
                "text_content": ocr_results,
                "nlp_analysis": nlp_analysis,
                "method": "ocr_nlp"
            }
            
        except Exception as e:
            logger.error(f"OCR + NLP detection error: {e}")
            return None
    
    async def _detect_with_browser_api(self) -> Optional[Dict[str, Any]]:
        """Detect elements using browser/DOM APIs"""
        try:
            if not self.browser_detector.available:
                return None
            
            # Connect to browser if not already connected
            if not self.browser_detector.driver:
                if not self.browser_detector.connect_to_browser():
                    return None
            
            # Get DOM elements
            dom_elements = self.browser_detector.get_dom_elements()
            
            return {
                "dom_elements": dom_elements,
                "method": "browser_api",
                "element_count": len(dom_elements)
            }
            
        except Exception as e:
            logger.error(f"Browser API detection error: {e}")
            return None
    
    async def _analyze_ui_with_llava(self, image_path: str, app_name: str, view_name: str) -> str:
        """Analyze UI with LLaVA (existing implementation)"""
        try:
            # Convert image to base64
            with open(image_path, "rb") as image_file:
                img_base64 = base64.b64encode(image_file.read()).decode("utf-8")
            
            # Use existing LLaVA analysis logic from ui_element_detector.py
            # This is a simplified version - you can import the full implementation
            return "LLaVA analysis placeholder"
            
        except Exception as e:
            logger.error(f"LLaVA analysis error: {e}")
            return ""
    
    async def _combine_detection_results(self, accessibility_info, ocr_results, dom_results, llava_analysis, app_name) -> List[EnhancedUIElement]:
        """Combine results from all detection methods"""
        elements = []
        element_id_counter = 0
        
        try:
            # Process DOM elements first (most accurate positioning)
            if dom_results and dom_results.get("dom_elements"):
                for dom_elem in dom_results["dom_elements"]:
                    element = EnhancedUIElement(
                        element_id=f"dom_{element_id_counter}",
                        element_type=self._normalize_element_type(dom_elem["type"]),
                        element_text=dom_elem["text"],
                        bounding_box=self._get_bounding_box_from_dom(dom_elem),
                        center_point=self._get_center_from_dom(dom_elem),
                        confidence=0.95,  # High confidence for DOM elements
                        detected_by=["Browser API"],
                        dom_attributes=dom_elem["attributes"]
                    )
                    
                    # Add accessibility info if available
                    if accessibility_info:
                        element.accessibility_info = accessibility_info
                        element.detected_by.append("Accessibility API")
                    
                    elements.append(element)
                    element_id_counter += 1
            
            # Process OCR text regions
            if ocr_results and ocr_results.get("text_content", {}).get("regions"):
                for region in ocr_results["text_content"]["regions"]:
                    # Classify using ML if available
                    element_type, ml_confidence = "unknown", 0.0
                    if self.ml_classifier.available:
                        element_type, ml_confidence = self.ml_classifier.classify_element(region["text"])
                    
                    # Get NLP intent
                    nlp_intent = "unknown"
                    if ocr_results.get("nlp_analysis"):
                        nlp_intent = ocr_results["nlp_analysis"]["intent"]
                    
                    element = EnhancedUIElement(
                        element_id=f"ocr_{element_id_counter}",
                        element_type=element_type,
                        element_text=region["text"],
                        bounding_box=self._get_bounding_box_from_ocr(region["bbox"]),
                        confidence=region["confidence"],
                        detected_by=["OCR", "NLP"],
                        ml_confidence=ml_confidence,
                        ocr_text=region["text"],
                        nlp_intent=nlp_intent
                    )
                    
                    elements.append(element)
                    element_id_counter += 1
            
            # Enhance with accessibility roles
            if accessibility_info:
                for element in elements:
                    if not element.role and accessibility_info.get("focused_element"):
                        element.role = accessibility_info["focused_element"]
            
            return elements
            
        except Exception as e:
            logger.error(f"Error combining detection results: {e}")
            return []
    
    def _get_bounding_box_from_dom(self, dom_elem: Dict[str, Any]) -> List[int]:
        """Convert DOM element location and size to bounding box"""
        try:
            location = dom_elem["location"]
            size = dom_elem["size"]
            
            x1 = location["x"]
            y1 = location["y"]
            x2 = x1 + size["width"]
            y2 = y1 + size["height"]
            
            return [x1, y1, x2, y2]
            
        except Exception:
            return None
    
    def _get_center_from_dom(self, dom_elem: Dict[str, Any]) -> Tuple[int, int]:
        """Get center point from DOM element"""
        try:
            bbox = self._get_bounding_box_from_dom(dom_elem)
            if bbox:
                center_x = (bbox[0] + bbox[2]) // 2
                center_y = (bbox[1] + bbox[3]) // 2
                return (center_x, center_y)
            return None
            
        except Exception:
            return None
    
    def _get_bounding_box_from_ocr(self, bbox) -> List[int]:
        """Convert OCR bbox to standard format"""
        try:
            # OCR bbox is typically [[x1,y1], [x2,y1], [x2,y2], [x1,y2]]
            x_coords = [point[0] for point in bbox]
            y_coords = [point[1] for point in bbox]
            
            x1, x2 = min(x_coords), max(x_coords)
            y1, y2 = min(y_coords), max(y_coords)
            
            return [int(x1), int(y1), int(x2), int(y2)]
            
        except Exception:
            return None
    
    def _normalize_element_type(self, element_type: str) -> str:
        """Normalize element type to standard types"""
        element_type = element_type.lower()
        
        # Map various type names to standard types
        type_mapping = {
            "input_text": "textfield",
            "input_password": "textfield",
            "input_email": "textfield",
            "input_search": "textfield",
            "input_submit": "button",
            "input_button": "button",
            "input_checkbox": "checkbox",
            "input_radio": "radio"
        }
        
        return type_mapping.get(element_type, element_type)
    
    async def _enhance_with_ml(self, elements: List[EnhancedUIElement]) -> Dict[str, Any]:
        """Enhance elements using ML classification"""
        try:
            ml_predictions = {
                "total_elements": len(elements),
                "classified_elements": 0,
                "avg_confidence": 0.0
            }
            
            total_confidence = 0.0
            classified_count = 0
            
            for element in elements:
                if element.element_text and self.ml_classifier.available:
                    predicted_type, confidence = self.ml_classifier.classify_element(
                        element.element_text, 
                        element.parent_component
                    )
                    
                    # Update element if ML prediction has higher confidence
                    if confidence > element.ml_confidence:
                        element.ml_confidence = confidence
                        if confidence > 0.7 and not element.element_type or element.element_type == "unknown":
                            element.element_type = predicted_type
                            element.detected_by.append("Machine Learning")
                    
                    total_confidence += confidence
                    classified_count += 1
            
            if classified_count > 0:
                ml_predictions["classified_elements"] = classified_count
                ml_predictions["avg_confidence"] = total_confidence / classified_count
            
            return ml_predictions
            
        except Exception as e:
            logger.error(f"ML enhancement error: {e}")
            return {}
    
    def _save_enhanced_result(self, result: EnhancedDetectionResult):
        """Save enhanced detection result"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{self.results_dir}/enhanced_detection_{timestamp}.json"
            
            # Convert to serializable format
            result_dict = {
                "timestamp": result.timestamp,
                "app_name": result.app_name,
                "view_name": result.view_name,
                "elements": [asdict(elem) for elem in result.elements],
                "accessibility_tree": result.accessibility_tree,
                "ml_predictions": result.ml_predictions,
                "ocr_results": result.ocr_results,
                "nlp_analysis": result.nlp_analysis,
                "dom_structure": result.dom_structure,
                "screenshot_hash": result.screenshot_hash,
                "detection_methods_used": result.detection_methods_used
            }
            
            with open(filename, 'w') as f:
                json.dump(result_dict, f, indent=2)
            
            # Save as latest
            with open(f"{self.results_dir}/latest.json", 'w') as f:
                json.dump(result_dict, f, indent=2)
            
            logger.info(f"Enhanced result saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving enhanced result: {e}")

async def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced UI Detection System")
    parser.add_argument("image_path", help="Path to screenshot image")
    parser.add_argument("--app", default="", help="Application name")
    parser.add_argument("--view", default="", help="View name")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"Error: Image file '{args.image_path}' not found")
        return 1
    
    detector = EnhancedUIDetectionSystem()
    
    app_context = None
    if args.app:
        app_context = {"app_name": args.app, "view_name": args.view}
    
    result = await detector.enhanced_detect_ui_elements(args.image_path, app_context)
    
    print("\n===== ENHANCED UI DETECTION RESULTS =====")
    print(f"Application: {result.app_name}")
    print(f"Detection methods used: {result.detection_methods_used}")
    print(f"Elements detected: {len(result.elements)}")
    
    for i, element in enumerate(result.elements):
        print(f"\n{i+1}. {element.element_type.upper()}: {element.element_text}")
        print(f"   Detected by: {element.detected_by}")
        print(f"   Confidence: {element.confidence:.2f}")
        if element.ml_confidence > 0:
            print(f"   ML Confidence: {element.ml_confidence:.2f}")
        if element.center_point:
            print(f"   Center: {element.center_point}")
        if element.role:
            print(f"   Accessibility Role: {element.role}")
        if element.nlp_intent != "unknown":
            print(f"   NLP Intent: {element.nlp_intent}")
    
    print("==========================================")
    print(f"Results saved to {detector.results_dir}/latest.json")
    
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