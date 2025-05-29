#!/usr/bin/env python3
"""
Total Screen Analyzer

Comprehensive screen analysis system that captures and understands EVERYTHING on screen:
- Complete visual context understanding
- Detailed text extraction and positioning
- UI element detection and classification  
- Application state and workflow detection
- User interaction patterns
- Content semantic analysis
- Visual hierarchy mapping

This provides total awareness of what's happening on screen for rich memory storage.
"""

import os
import json
import time
import asyncio
import logging
import websockets
import tempfile
import hashlib
import base64
import traceback
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from PIL import ImageGrab, Image, ImageEnhance, ImageFilter, ImageDraw
import cv2
import numpy as np
import pytesseract
from io import BytesIO

# Configure logging
os.makedirs('logs/sensors/total_screen', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/total_screen/total_screen_analyzer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('total_screen_analyzer')

class TotalScreenAnalyzer:
    """
    Advanced screen analyzer that captures and understands everything on screen
    for comprehensive memory storage and context awareness.
    """
    
    def __init__(self, bridge_uri="ws://localhost:8767", capture_interval=8, fast_mode=True):
        self.bridge_uri = bridge_uri
        self.capture_interval = capture_interval
        self.running = True
        self.fast_mode = fast_mode  # Skip slow LLaVA analysis in fast mode (default: True)
        self.cache_dir = "cache/total_screen_analyzer"
        self.last_screen_hash = None
        
        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize LLaVA processor
        self.llava_processor = None
        self._initialize_llava()
        
        # Analysis configuration
        self.ocr_configs = [
            '--psm 6',   # Uniform block of text
            '--psm 3',   # Fully automatic page segmentation  
            '--psm 11',  # Sparse text
            '--psm 13'   # Raw line
        ]
        
        # Application detection patterns
        self.app_patterns = {
            'browsers': {
                'indicators': ['http', 'https', 'www.', '.com', '.org', 'browser', 'tab'],
                'ui_elements': ['address bar', 'bookmark', 'reload', 'back', 'forward'],
                'context_extractor': self._extract_browser_context
            },
            'code_editors': {
                'indicators': ['function', 'class', 'import', 'def ', 'var ', 'const ', '#!/usr/bin'],
                'ui_elements': ['line numbers', 'syntax highlighting', 'file tree'],
                'context_extractor': self._extract_code_context
            },
            'text_editors': {
                'indicators': ['document', 'paragraph', 'font', 'bold', 'italic'],
                'ui_elements': ['toolbar', 'ruler', 'formatting'],
                'context_extractor': self._extract_document_context
            },
            'communication': {
                'indicators': ['message', 'chat', 'from:', 'to:', 'subject:', 'reply'],
                'ui_elements': ['send button', 'compose', 'inbox'],
                'context_extractor': self._extract_communication_context
            },
            'terminals': {
                'indicators': ['$', '>', '#', 'command', 'bash', 'zsh', 'terminal'],
                'ui_elements': ['command prompt', 'cursor'],
                'context_extractor': self._extract_terminal_context
            }
        }
        
        logger.info(f"Total Screen Analyzer initialized with {capture_interval}s interval")

    async def analyze_full_screen(self) -> Dict[str, Any]:
        """Public method to perform full screen analysis - compatible with professional agent"""
        return await self._perform_total_screen_analysis() or {}

    def _initialize_llava(self):
        """Initialize LLaVA visual processor"""
        try:
            import sys
            import os
            # Add current directory and sensors directory to path
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            sys.path.append('.')
            from llava_visual_processor import LLaVAVisualProcessor
            self.llava_processor = LLaVAVisualProcessor()
            logger.info("LLaVA visual processor initialized for total screen analysis")
        except Exception as e:
            logger.warning(f"Could not initialize LLaVA processor: {e}")
            logger.warning("TotalScreenAnalyzer will continue without LLaVA (fast mode)")
            self.llava_processor = None

    async def _perform_total_screen_analysis(self) -> Optional[Dict[str, Any]]:
        """
        Perform comprehensive analysis of everything on screen with parallel processing
        """
        try:
            # Capture high-quality screenshot
            screenshot = ImageGrab.grab()
            # Convert RGBA to RGB if needed
            if screenshot.mode == 'RGBA':
                screenshot = screenshot.convert('RGB')
            width, height = screenshot.size
            
            # Calculate change detection hash
            img_hash = hashlib.md5(screenshot.tobytes()).hexdigest()
            is_changed = self.last_screen_hash != img_hash
            
            # Smart caching: skip if very recent analysis
            if hasattr(self, "_last_analysis_time"):
                if time.time() - self._last_analysis_time < 5:  # Skip if analyzed within 5s
                    return self._last_analysis_result if hasattr(self, "_last_analysis_result") else None
            
            # Skip if unchanged (unless forced)
            if not is_changed and self.last_screen_hash:
                logger.debug(f"Screen unchanged (hash: {img_hash[:8]})")
                return None
                
            self.last_screen_hash = img_hash
            start_time = time.time()
            
            logger.info(f"Starting total screen analysis (hash: {img_hash[:8]})")
            
            # Initialize comprehensive analysis result
            total_analysis = {
                "timestamp": datetime.now().isoformat(),
                "image_hash": img_hash,
                "resolution": f"{width}x{height}",
                "analysis_duration": 0,
                "layers": {}
            }

            # Create coroutines for each analysis layer
            async def run_layer1():
                return await self._analyze_window_context()

            async def run_layer2():
                return await self._perform_comprehensive_ocr(screenshot)

            async def run_layer3():
                return await self._analyze_ui_elements(screenshot)

            async def run_layer4():
                return await self._detect_application_context(screenshot, "")

            async def run_layer5():
                return await self._analyze_content_semantics("", {})

            async def run_layer6():
                return await self._analyze_visual_layout(screenshot, {})

            async def run_layer7():
                if self.fast_mode:
                    return await self._analyze_with_lightweight_vision(screenshot)
                return await self._analyze_with_llava(screenshot)

            async def run_layer8():
                return await self._analyze_user_workflow({})

            async def run_layer9():
                return self._synthesize_comprehensive_context({})

            # Run all analysis layers in parallel
            analysis_tasks = [
                run_layer1(),  # Window context
                run_layer2(),  # OCR
                run_layer3(),  # UI elements
                run_layer4(),  # Application context
                run_layer5(),  # Content semantics
                run_layer6(),  # Visual layout
                run_layer7(),  # LLaVA
                run_layer8(),  # Workflow
                run_layer9()   # Synthesis
            ]

            # Execute all tasks in parallel with longer timeout for LLaVA
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            layer_names = [
                "window_context",
                "text_analysis",
                "ui_analysis",
                "application_analysis",
                "content_analysis",
                "layout_analysis",
                "llava_analysis",
                "workflow_analysis",
                "synthesis_analysis"
            ]

            for layer_name, result in zip(layer_names, results):
                if isinstance(result, Exception):
                    logger.error(f"Error in {layer_name}: {str(result)}")
                    total_analysis["layers"][layer_name] = {"error": str(result)}
                else:
                    total_analysis["layers"][layer_name] = result

            # Update dependent layers with results from other layers
            text_analysis = total_analysis["layers"].get("text_analysis", {})
            ui_analysis = total_analysis["layers"].get("ui_analysis", {})
            
            # Update application context with OCR results
            if "text_analysis" in total_analysis["layers"]:
                total_analysis["layers"]["application_analysis"] = await self._detect_application_context(
                    screenshot, 
                    text_analysis.get("all_text", "")
                )

            # Update content semantics with OCR and UI results
            if "text_analysis" in total_analysis["layers"] and "ui_analysis" in total_analysis["layers"]:
                total_analysis["layers"]["content_analysis"] = await self._analyze_content_semantics(
                    text_analysis.get("all_text", ""),
                    ui_analysis
                )

            # Update visual layout with UI results
            if "ui_analysis" in total_analysis["layers"]:
                total_analysis["layers"]["layout_analysis"] = await self._analyze_visual_layout(
                    screenshot,
                    ui_analysis
                )

            # Update workflow analysis with all previous results
            total_analysis["layers"]["workflow_analysis"] = await self._analyze_user_workflow(total_analysis)

            # Final synthesis with all results
            total_analysis["synthesized_context"] = self._synthesize_comprehensive_context(total_analysis)
            
            # Create memory-optimized summary
            total_analysis["memory_summary"] = self._create_memory_summary(total_analysis)
            
            # Calculate analysis duration
            total_analysis["analysis_duration"] = time.time() - start_time
            
            # Cache the analysis
            await self._cache_analysis(total_analysis)
            
            logger.info(f"Completed total screen analysis in {total_analysis['analysis_duration']:.2f}s")
            return total_analysis
            
        except Exception as e:
            logger.error(f"Error in total screen analysis: {e}")
            logger.error(traceback.format_exc())
            return None

    async def _analyze_window_context(self) -> Dict[str, Any]:
        """Get comprehensive window and system context"""
        try:
            import platform
            import subprocess
            
            context = {
                "platform": platform.system(),
                "active_window": "Unknown",
                "application_name": "Unknown",
                "window_state": "unknown"
            }
            
            system = platform.system()
            
            if system == "Darwin":  # macOS
                try:
                    # Enhanced AppleScript for better window detection
                    app_script = '''
                    tell application "System Events"
                        try
                            set frontApp to name of first application process whose frontmost is true
                            return frontApp
                        on error
                            return "Unknown"
                        end try
                    end tell
                    '''
                    
                    window_script = '''
                    tell application "System Events"
                        try
                            set frontWindow to title of front window of first application process whose frontmost is true
                            return frontWindow
                        on error
                            try
                                set frontWindow to name of front window of first application process whose frontmost is true
                                return frontWindow
                            on error
                                return "Main Window"
                            end try
                        end try
                    end tell
                    '''
                    
                    # Get application name with timeout and error handling
                    app_result = subprocess.run(['osascript', '-e', app_script], 
                                              capture_output=True, text=True, timeout=2)
                    if app_result.returncode == 0 and app_result.stdout.strip():
                        app_name = app_result.stdout.strip()
                        # Clean up helper process names
                        if " (" in app_name:
                            app_name = app_name.split(" (")[0]
                        context["application_name"] = app_name
                    
                    # Get window title with timeout and error handling
                    window_result = subprocess.run(['osascript', '-e', window_script], 
                                                 capture_output=True, text=True, timeout=2)
                    if window_result.returncode == 0 and window_result.stdout.strip():
                        window_title = window_result.stdout.strip()
                        context["active_window"] = window_title
                        # Set window state based on title
                        if "untitled" in window_title.lower():
                            context["window_state"] = "new_document"
                        elif any(term in window_title.lower() for term in ["edit", "compose", "new"]):
                            context["window_state"] = "editing"
                        else:
                            context["window_state"] = "viewing"
                    
                    # Fallback: Try to get process information
                    if context["application_name"] == "Unknown":
                        try:
                            import psutil
                            # Find frontmost process by CPU usage and activity
                            processes = []
                            for proc in psutil.process_iter(['name', 'cpu_percent']):
                                try:
                                    if proc.info['name'] not in ['kernel_task', 'WindowServer', 'loginwindow']:
                                        processes.append((proc.info['name'], proc.info['cpu_percent'] or 0))
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    continue
                            
                            if processes:
                                # Sort by CPU and take the most active
                                processes.sort(key=lambda x: x[1], reverse=True)
                                context["application_name"] = processes[0][0]
                                context["active_window"] = f"{processes[0][0]} - Active Window"
                                logger.debug(f"Used psutil fallback: {processes[0][0]}")
                        except Exception as fallback_e:
                            logger.debug(f"Psutil fallback failed: {fallback_e}")
                        
                except Exception as e:
                    logger.debug(f"Could not get macOS window context: {e}")
                    # Final fallback - use system information
                    try:
                        import psutil
                        active_processes = [p.info['name'] for p in psutil.process_iter(['name']) 
                                          if p.info['name'] not in ['kernel_task', 'WindowServer']]
                        if active_processes:
                            context["application_name"] = active_processes[0]
                            context["active_window"] = f"{active_processes[0]} - Window"
                    except:
                        pass
                    
            elif system == "Windows":
                try:
                    import win32gui
                    window = win32gui.GetForegroundWindow()
                    context["active_window"] = win32gui.GetWindowText(window)
                    # Get process name
                    import win32process
                    _, pid = win32process.GetWindowThreadProcessId(window)
                    import psutil
                    process = psutil.Process(pid)
                    context["application_name"] = process.name()
                except Exception as e:
                    logger.debug(f"Could not get Windows window context: {e}")
                    
            elif system == "Linux":
                try:
                    result = subprocess.run(['xdotool', 'getwindowfocus', 'getwindowname'], 
                                          capture_output=True, text=True, timeout=3)
                    if result.returncode == 0:
                        context["active_window"] = result.stdout.strip()
                except Exception as e:
                    logger.debug(f"Could not get Linux window context: {e}")
            
            return context
            
        except Exception as e:
            logger.error(f"Error analyzing window context: {e}")
            return {"platform": "unknown", "active_window": "Unknown", "application_name": "Unknown"}

    async def _perform_comprehensive_ocr(self, screenshot: Image.Image) -> Dict[str, Any]:
        """Perform comprehensive text extraction with multiple techniques"""
        try:
            # Prepare different image versions for OCR
            original = screenshot
            grayscale = screenshot.convert('L')
            
            # Enhanced contrast version
            enhancer = ImageEnhance.Contrast(grayscale)
            enhanced = enhancer.enhance(2.0)
            
            # Preprocessed version (slight blur to reduce noise)
            preprocessed = enhanced.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            # Try OCR with different configurations
            best_results = {"text": "", "confidence": 0, "detailed_data": None}
            
            for config in self.ocr_configs:
                try:
                    # Extract text
                    text = pytesseract.image_to_string(preprocessed, config=config).strip()
                    
                    # Get detailed data with positions
                    detailed_data = pytesseract.image_to_data(
                        preprocessed, config=config, output_type=pytesseract.Output.DICT
                    )
                    
                    # Calculate confidence
                    confidences = [int(conf) for conf in detailed_data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    # Keep best result
                    if avg_confidence > best_results["confidence"] and len(text) > 0:
                        best_results = {
                            "text": text,
                            "confidence": avg_confidence,
                            "detailed_data": detailed_data
                        }
                        
                except Exception as e:
                    logger.debug(f"OCR config {config} failed: {e}")
                    continue
            
            # Process detailed OCR data
            text_elements = []
            text_regions = []
            
            if best_results["detailed_data"]:
                data = best_results["detailed_data"]
                
                for i in range(len(data['text'])):
                    text_item = data['text'][i].strip()
                    confidence = int(data['conf'][i])
                    
                    if text_item and confidence > 30:  # Filter low confidence
                        element = {
                            'text': text_item,
                            'confidence': confidence,
                            'position': {
                                'x': data['left'][i],
                                'y': data['top'][i], 
                                'width': data['width'][i],
                                'height': data['height'][i]
                            },
                            'level': data['level'][i],  # Text hierarchy level
                            'block_num': data['block_num'][i],
                            'par_num': data['par_num'][i],
                            'line_num': data['line_num'][i],
                            'word_num': data['word_num'][i]
                        }
                        text_elements.append(element)
            
            # Group text into logical regions
            text_regions = self._group_text_into_regions(text_elements)
            
            # Extract structured information
            lines = best_results["text"].split('\n')
            meaningful_lines = [line.strip() for line in lines if line.strip() and len(line.strip()) > 2]
            
            # Categorize text content
            text_categories = self._categorize_text_content(best_results["text"])
            
            return {
                "all_text": best_results["text"],
                "confidence": best_results["confidence"],
                "meaningful_lines": meaningful_lines,
                "text_elements": text_elements,
                "text_regions": text_regions,
                "text_categories": text_categories,
                "word_count": len(best_results["text"].split()) if best_results["text"] else 0,
                "character_count": len(best_results["text"]),
                "line_count": len(meaningful_lines),
                "has_meaningful_content": len(meaningful_lines) > 0
            }
            
        except Exception as e:
            logger.error(f"Error in comprehensive OCR: {e}")
            return {
                "all_text": "", "confidence": 0, "meaningful_lines": [],
                "text_elements": [], "text_regions": [], "text_categories": {},
                "word_count": 0, "character_count": 0, "line_count": 0,
                "has_meaningful_content": False, "error": str(e)
            }

    def _group_text_into_regions(self, text_elements: List[Dict]) -> List[Dict]:
        """Group text elements into logical regions based on proximity"""
        if not text_elements:
            return []
        
        regions = []
        used_elements = set()
        
        for i, element in enumerate(text_elements):
            if i in used_elements:
                continue
                
            # Start a new region
            region = {
                "elements": [element],
                "bounding_box": element["position"].copy(),
                "text": element["text"],
                "confidence": element["confidence"]
            }
            used_elements.add(i)
            
            # Find nearby elements
            for j, other in enumerate(text_elements[i+1:], i+1):
                if j in used_elements:
                    continue
                    
                # Check if elements are close enough to group
                if self._are_elements_nearby(element["position"], other["position"]):
                    region["elements"].append(other)
                    region["text"] += " " + other["text"]
                    region["confidence"] = (region["confidence"] + other["confidence"]) / 2
                    
                    # Expand bounding box
                    self._expand_bounding_box(region["bounding_box"], other["position"])
                    used_elements.add(j)
            
            regions.append(region)
        
        return regions

    def _are_elements_nearby(self, pos1: Dict, pos2: Dict, threshold: int = 50) -> bool:
        """Check if two text elements are close enough to be grouped"""
        center1_x = pos1["x"] + pos1["width"] / 2
        center1_y = pos1["y"] + pos1["height"] / 2
        center2_x = pos2["x"] + pos2["width"] / 2
        center2_y = pos2["y"] + pos2["height"] / 2
        
        distance = ((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2) ** 0.5
        return distance < threshold

    def _expand_bounding_box(self, bbox: Dict, new_pos: Dict):
        """Expand bounding box to include new position"""
        min_x = min(bbox["x"], new_pos["x"])
        min_y = min(bbox["y"], new_pos["y"])
        max_x = max(bbox["x"] + bbox["width"], new_pos["x"] + new_pos["width"])
        max_y = max(bbox["y"] + bbox["height"], new_pos["y"] + new_pos["height"])
        
        bbox["x"] = min_x
        bbox["y"] = min_y
        bbox["width"] = max_x - min_x
        bbox["height"] = max_y - min_y

    def _categorize_text_content(self, text: str) -> Dict[str, List[str]]:
        """Categorize text content into different types"""
        categories = {
            "urls": [],
            "emails": [],
            "dates": [],
            "numbers": [],
            "file_paths": [],
            "code_snippets": [],
            "ui_labels": [],
            "headings": [],
            "body_text": []
        }
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # URL detection
            if re.search(r'https?://[^\s]+|www\.[^\s]+', line):
                categories["urls"].append(line)
            
            # Email detection
            elif re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', line):
                categories["emails"].append(line)
            
            # Date detection
            elif re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}', line):
                categories["dates"].append(line)
            
            # File path detection
            elif re.search(r'[/\\][A-Za-z0-9_\-./\\]+|[A-Za-z]:[\\][A-Za-z0-9_\-./\\]+', line):
                categories["file_paths"].append(line)
            
            # Code snippet detection
            elif re.search(r'(function|class|def |import |from |#include|var |const |let )', line):
                categories["code_snippets"].append(line)
            
            # Number-heavy content
            elif re.search(r'\d+', line) and len(re.findall(r'\d+', line)) > 2:
                categories["numbers"].append(line)
            
            # Headings (short, title-case lines)
            elif len(line) < 100 and line.istitle():
                categories["headings"].append(line)
            
            # UI labels (short lines with colons or buttons)
            elif len(line) < 50 and (':' in line or any(ui in line.lower() for ui in ['button', 'click', 'select'])):
                categories["ui_labels"].append(line)
            
            # Everything else is body text
            else:
                categories["body_text"].append(line)
        
        return categories

    async def _analyze_ui_elements(self, screenshot: Image.Image) -> Dict[str, Any]:
        """Comprehensive UI element detection using computer vision"""
        try:
            # Convert to OpenCV format
            cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            height, width = cv_image.shape[:2]
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Multiple edge detection approaches
            elements = []
            
            # 1. Canny edge detection for sharp UI elements
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Filter reasonable UI element sizes
                if 100 < area < width * height * 0.1 and w > 10 and h > 10:
                    aspect_ratio = w / h
                    
                    # Classify element type by shape and size
                    element_type = self._classify_ui_element(w, h, area, aspect_ratio)
                    
                    elements.append({
                        "type": element_type,
                        "position": {"x": x, "y": y, "width": w, "height": h},
                        "area": area,
                        "aspect_ratio": aspect_ratio,
                        "detection_method": "canny_edges"
                    })
            
            # 2. Template matching for common UI elements
            template_elements = await self._detect_template_elements(gray)
            elements.extend(template_elements)
            
            # 3. Color-based detection for buttons and interactive elements
            color_elements = await self._detect_color_based_elements(cv_image)
            elements.extend(color_elements)
            
            # Remove duplicates and sort by confidence
            unique_elements = self._deduplicate_elements(elements)
            
            # Analyze layout structure
            layout_structure = self._analyze_layout_structure(unique_elements, width, height)
            
            return {
                "elements": unique_elements,
                "total_count": len(unique_elements),
                "element_types": self._count_element_types(unique_elements),
                "layout_structure": layout_structure,
                "screen_density": len(unique_elements) / (width * height) * 1000000  # Elements per megapixel
            }
            
        except Exception as e:
            logger.error(f"Error analyzing UI elements: {e}")
            return {"elements": [], "total_count": 0, "error": str(e)}

    def _classify_ui_element(self, w: int, h: int, area: int, aspect_ratio: float) -> str:
        """Classify UI element type based on dimensions"""
        if aspect_ratio > 10:
            return "horizontal_line"
        elif aspect_ratio < 0.1:
            return "vertical_line"
        elif 0.8 <= aspect_ratio <= 1.2:
            if area < 2000:
                return "button"
            elif area < 10000:
                return "icon"
            else:
                return "square_panel"
        elif aspect_ratio > 3:
            if h < 50:
                return "text_field"
            else:
                return "horizontal_panel"
        elif aspect_ratio < 0.33:
            return "vertical_panel"
        elif area > 50000:
            return "content_area"
        else:
            return "widget"

    async def _detect_template_elements(self, gray_image) -> List[Dict]:
        """Detect UI elements using template matching"""
        # This would use pre-defined templates for common UI elements
        # For now, return empty list - can be expanded with actual templates
        return []

    async def _detect_color_based_elements(self, cv_image) -> List[Dict]:
        """Detect interactive elements based on color patterns"""
        elements = []
        
        try:
            # Convert to HSV for better color detection
            hsv = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
            
            # Define color ranges for common UI elements
            # Blue range (common for buttons/links)
            blue_lower = np.array([100, 50, 50])
            blue_upper = np.array([130, 255, 255])
            blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
            
            # Find blue regions
            contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 20 and h > 15 and w * h > 300:  # Reasonable button size
                    elements.append({
                        "type": "interactive_element",
                        "position": {"x": x, "y": y, "width": w, "height": h},
                        "area": w * h,
                        "detection_method": "color_blue",
                        "color_category": "interactive"
                    })
            
        except Exception as e:
            logger.debug(f"Color-based detection failed: {e}")
        
        return elements

    def _deduplicate_elements(self, elements: List[Dict]) -> List[Dict]:
        """Remove duplicate elements based on position overlap"""
        if not elements:
            return []
        
        # Sort by area (larger first) to prefer larger elements
        sorted_elements = sorted(elements, key=lambda x: x.get("area", 0), reverse=True)
        unique_elements = []
        
        for element in sorted_elements:
            is_duplicate = False
            pos = element["position"]
            
            for existing in unique_elements:
                existing_pos = existing["position"]
                
                # Check for significant overlap
                if self._calculate_overlap(pos, existing_pos) > 0.5:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_elements.append(element)
        
        return unique_elements

    def _calculate_overlap(self, pos1: Dict, pos2: Dict) -> float:
        """Calculate overlap ratio between two rectangles"""
        x1_left, y1_top = pos1["x"], pos1["y"]
        x1_right, y1_bottom = x1_left + pos1["width"], y1_top + pos1["height"]
        
        x2_left, y2_top = pos2["x"], pos2["y"]  
        x2_right, y2_bottom = x2_left + pos2["width"], y2_top + pos2["height"]
        
        # Calculate intersection
        inter_left = max(x1_left, x2_left)
        inter_top = max(y1_top, y2_top)
        inter_right = min(x1_right, x2_right)
        inter_bottom = min(y1_bottom, y2_bottom)
        
        if inter_left >= inter_right or inter_top >= inter_bottom:
            return 0.0
        
        inter_area = (inter_right - inter_left) * (inter_bottom - inter_top)
        area1 = pos1["width"] * pos1["height"]
        area2 = pos2["width"] * pos2["height"]
        
        return inter_area / min(area1, area2)

    def _count_element_types(self, elements: List[Dict]) -> Dict[str, int]:
        """Count elements by type"""
        type_counts = {}
        for element in elements:
            element_type = element.get("type", "unknown")
            type_counts[element_type] = type_counts.get(element_type, 0) + 1
        return type_counts

    def _analyze_layout_structure(self, elements: List[Dict], width: int, height: int) -> Dict[str, Any]:
        """Analyze the overall layout structure"""
        if not elements:
            return {"layout_type": "empty"}
        
        # Divide screen into regions
        top_region = [e for e in elements if e["position"]["y"] < height * 0.25]
        middle_region = [e for e in elements if height * 0.25 <= e["position"]["y"] <= height * 0.75]
        bottom_region = [e for e in elements if e["position"]["y"] > height * 0.75]
        
        left_region = [e for e in elements if e["position"]["x"] < width * 0.25]
        center_region = [e for e in elements if width * 0.25 <= e["position"]["x"] <= width * 0.75]
        right_region = [e for e in elements if e["position"]["x"] > width * 0.75]
        
        return {
            "layout_type": "standard" if top_region and middle_region else "custom",
            "region_distribution": {
                "top": len(top_region),
                "middle": len(middle_region), 
                "bottom": len(bottom_region),
                "left": len(left_region),
                "center": len(center_region),
                "right": len(right_region)
            },
            "has_navigation": len(top_region) > 3,
            "has_sidebar": len(left_region) > 5 or len(right_region) > 5,
            "content_focused": len(middle_region) > len(top_region) + len(bottom_region)
        }

    async def _detect_application_context(self, screenshot: Image.Image, text: str) -> Dict[str, Any]:
        """Detect and analyze application context"""
        try:
            detection_results = {
                "detected_app": "unknown",
                "confidence": 0.0,
                "app_category": "unknown",
                "specific_context": {},
                "detection_evidence": []
            }
            
            text_lower = text.lower()
            
            # Test each application pattern
            for app_category, patterns in self.app_patterns.items():
                score = 0
                evidence = []
                
                # Check text indicators
                for indicator in patterns["indicators"]:
                    if indicator in text_lower:
                        score += 1
                        evidence.append(f"text_indicator: {indicator}")
                
                # Check UI element indicators
                for ui_element in patterns["ui_elements"]:
                    if ui_element in text_lower:
                        score += 0.5
                        evidence.append(f"ui_element: {ui_element}")
                
                # Calculate confidence
                confidence = min(score / (len(patterns["indicators"]) + len(patterns["ui_elements"])), 1.0)
                
                if confidence > detection_results["confidence"]:
                    detection_results.update({
                        "detected_app": app_category,
                        "confidence": confidence,
                        "app_category": app_category,
                        "detection_evidence": evidence
                    })
                    
                    # Extract specific context
                    if "context_extractor" in patterns:
                        try:
                            specific_context = await patterns["context_extractor"](text, screenshot)
                            detection_results["specific_context"] = specific_context
                        except Exception as e:
                            logger.debug(f"Context extraction failed for {app_category}: {e}")
            
            return detection_results
            
        except Exception as e:
            logger.error(f"Error detecting application context: {e}")
            return {"detected_app": "unknown", "confidence": 0.0, "error": str(e)}

    async def _extract_browser_context(self, text: str, screenshot: Image.Image) -> Dict[str, Any]:
        """Extract browser-specific context"""
        context = {
            "browser_type": "unknown",
            "current_url": "",
            "page_title": "",
            "tab_count": 0,
            "is_browsing": True
        }
        
        # Extract URL
        url_match = re.search(r'https?://[^\s]+', text)
        if url_match:
            context["current_url"] = url_match.group()
        
        # Extract page title (usually first long line)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # Page title is often the longest line near the top
            context["page_title"] = max(lines[:10], key=len) if len(lines) >= 10 else lines[0]
        
        return context

    async def _extract_code_context(self, text: str, screenshot: Image.Image) -> Dict[str, Any]:
        """Extract code editor context"""
        context = {
            "language": "unknown",
            "file_name": "",
            "function_names": [],
            "class_names": [],
            "is_editing": True
        }
        
        # Detect programming language
        if 'def ' in text or 'import ' in text:
            context["language"] = "python"
        elif 'function ' in text or 'var ' in text or 'const ' in text:
            context["language"] = "javascript"
        elif 'class ' in text and '{' in text:
            context["language"] = "java"
        elif '#include' in text:
            context["language"] = "c/c++"
        
        # Extract function names
        function_matches = re.findall(r'def\s+(\w+)|function\s+(\w+)', text)
        for match in function_matches:
            func_name = match[0] or match[1]
            if func_name:
                context["function_names"].append(func_name)
        
        # Extract class names
        class_matches = re.findall(r'class\s+(\w+)', text)
        context["class_names"] = class_matches
        
        return context

    async def _extract_document_context(self, text: str, screenshot: Image.Image) -> Dict[str, Any]:
        """Extract document editor context"""
        context = {
            "document_type": "text",
            "title": "",
            "word_count": len(text.split()),
            "has_formatting": False,
            "is_editing": True
        }
        
        # Detect document type
        if any(keyword in text.lower() for keyword in ['bold', 'italic', 'font', 'size']):
            context["has_formatting"] = True
            context["document_type"] = "rich_text"
        
        # Extract likely title (first significant line)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            context["title"] = lines[0]
        
        return context

    async def _extract_communication_context(self, text: str, screenshot: Image.Image) -> Dict[str, Any]:
        """Extract communication app context"""
        context = {
            "communication_type": "unknown",
            "participants": [],
            "subject": "",
            "message_count": 0,
            "is_composing": False
        }
        
        # Detect type
        if 'from:' in text.lower() or 'to:' in text.lower():
            context["communication_type"] = "email"
            
            # Extract email fields
            from_match = re.search(r'from:\s*([^\n\r]+)', text, re.IGNORECASE)
            if from_match:
                context["participants"].append(from_match.group(1).strip())
            
            subject_match = re.search(r'subject:\s*([^\n\r]+)', text, re.IGNORECASE)
            if subject_match:
                context["subject"] = subject_match.group(1).strip()
                
        elif 'message' in text.lower() or 'chat' in text.lower():
            context["communication_type"] = "chat"
        
        # Check if composing
        if any(keyword in text.lower() for keyword in ['compose', 'send', 'reply', 'new message']):
            context["is_composing"] = True
        
        return context

    async def _extract_terminal_context(self, text: str, screenshot: Image.Image) -> Dict[str, Any]:
        """Extract terminal/command line context"""
        context = {
            "shell_type": "unknown",
            "current_directory": "",
            "last_command": "",
            "command_history": [],
            "is_running_command": False
        }
        
        lines = text.split('\n')
        
        # Look for prompt patterns
        for line in lines:
            # Look for directory paths
            if '/' in line or '\\' in line:
                path_match = re.search(r'[~/][\w/\\.-]+', line)
                if path_match:
                    context["current_directory"] = path_match.group()
            
            # Look for command prompts
            prompt_match = re.search(r'[\$#>]\s*(\w+.*)', line)
            if prompt_match:
                context["last_command"] = prompt_match.group(1)
        
        return context

    async def _analyze_content_semantics(self, text: str, ui_analysis: Dict) -> Dict[str, Any]:
        """Analyze semantic content and meaning"""
        try:
            analysis = {
                "content_type": "unknown",
                "primary_purpose": "unknown", 
                "user_intent": "unknown",
                "content_categories": [],
                "interaction_level": "passive",
                "complexity_level": "simple"
            }
            
            text_lower = text.lower()
            word_count = len(text.split())
            
            # Determine content type
            if any(kw in text_lower for kw in ['email', 'message', 'from:', 'subject:']):
                analysis["content_type"] = "communication"
                analysis["primary_purpose"] = "messaging"
            elif any(kw in text_lower for kw in ['function', 'class', 'import', 'def']):
                analysis["content_type"] = "code"
                analysis["primary_purpose"] = "development"
            elif any(kw in text_lower for kw in ['document', 'article', 'paragraph']):
                analysis["content_type"] = "document"
                analysis["primary_purpose"] = "writing"
            elif any(kw in text_lower for kw in ['http', 'www', 'website']):
                analysis["content_type"] = "web_browsing"
                analysis["primary_purpose"] = "information_consumption"
            elif word_count > 100:
                analysis["content_type"] = "text_content"
                analysis["primary_purpose"] = "reading"
            else:
                analysis["content_type"] = "interface"
                analysis["primary_purpose"] = "navigation"
            
            # Determine user intent
            if any(kw in text_lower for kw in ['create', 'new', 'compose', 'write']):
                analysis["user_intent"] = "creating"
                analysis["interaction_level"] = "active"
            elif any(kw in text_lower for kw in ['edit', 'modify', 'change', 'update']):
                analysis["user_intent"] = "editing"
                analysis["interaction_level"] = "active"
            elif any(kw in text_lower for kw in ['search', 'find', 'look']):
                analysis["user_intent"] = "searching"
                analysis["interaction_level"] = "active"
            elif any(kw in text_lower for kw in ['read', 'view', 'browse']):
                analysis["user_intent"] = "consuming"
                analysis["interaction_level"] = "passive"
            else:
                analysis["user_intent"] = "navigating"
                analysis["interaction_level"] = "passive"
            
            # Determine complexity
            if word_count > 500 or len(ui_analysis.get("elements", [])) > 20:
                analysis["complexity_level"] = "complex"
            elif word_count > 100 or len(ui_analysis.get("elements", [])) > 10:
                analysis["complexity_level"] = "moderate"
            
            # Add content categories
            if 'error' in text_lower or 'warning' in text_lower:
                analysis["content_categories"].append("error_handling")
            if any(kw in text_lower for kw in ['save', 'submit', 'send']):
                analysis["content_categories"].append("action_oriented")
            if word_count > 200:
                analysis["content_categories"].append("content_heavy")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing content semantics: {e}")
            return {"content_type": "unknown", "error": str(e)}

    async def _analyze_visual_layout(self, screenshot: Image.Image, ui_analysis: Dict) -> Dict[str, Any]:
        """Analyze visual layout and design patterns"""
        try:
            width, height = screenshot.size
            elements = ui_analysis.get("elements", [])
            
            layout = {
                "layout_pattern": "unknown",
                "visual_weight_distribution": {},
                "color_scheme": {},
                "spacing_analysis": {},
                "visual_hierarchy": []
            }
            
            if not elements:
                return layout
            
            # Analyze visual weight distribution
            total_area = width * height
            element_area = sum(e.get("area", 0) for e in elements)
            layout["visual_weight_distribution"] = {
                "ui_elements_ratio": element_area / total_area,
                "whitespace_ratio": 1 - (element_area / total_area),
                "element_density": len(elements) / total_area * 1000000
            }
            
            # Determine layout pattern
            top_elements = [e for e in elements if e["position"]["y"] < height * 0.2]
            left_elements = [e for e in elements if e["position"]["x"] < width * 0.2]
            
            if len(top_elements) > len(elements) * 0.3:
                layout["layout_pattern"] = "top_heavy"
            elif len(left_elements) > len(elements) * 0.3:
                layout["layout_pattern"] = "left_sidebar"
            else:
                layout["layout_pattern"] = "distributed"
            
            # Basic color analysis
            cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            average_color = cv2.mean(cv_image)
            layout["color_scheme"] = {
                "average_brightness": sum(average_color[:3]) / 3,
                "is_dark_theme": sum(average_color[:3]) / 3 < 128
            }
            
            return layout
            
        except Exception as e:
            logger.error(f"Error analyzing visual layout: {e}")
            return {"layout_pattern": "unknown", "error": str(e)}

    async def _analyze_user_workflow(self, total_analysis: Dict) -> Dict[str, Any]:
        """Analyze user workflow and activity patterns"""
        try:
            workflow = {
                "current_activity": "unknown",
                "workflow_stage": "unknown",
                "productivity_context": "unknown",
                "focus_indicators": [],
                "multitasking_level": "low"
            }
            
            # Gather information from all layers
            app_analysis = total_analysis.get("layers", {}).get("application_analysis", {})
            content_analysis = total_analysis.get("layers", {}).get("content_analysis", {})
            text_analysis = total_analysis.get("layers", {}).get("text_analysis", {})
            
            detected_app = app_analysis.get("detected_app", "unknown")
            content_type = content_analysis.get("content_type", "unknown")
            user_intent = content_analysis.get("user_intent", "unknown")
            
            # Determine current activity
            if detected_app == "code_editors":
                workflow["current_activity"] = "software_development"
                workflow["productivity_context"] = "creative_work"
            elif detected_app == "browsers":
                workflow["current_activity"] = "web_browsing"
                workflow["productivity_context"] = "research" if user_intent == "consuming" else "web_work"
            elif detected_app == "communication":
                workflow["current_activity"] = "communication"
                workflow["productivity_context"] = "collaboration"
            elif content_type == "document":
                workflow["current_activity"] = "document_work"
                workflow["productivity_context"] = "content_creation"
            else:
                workflow["current_activity"] = "general_computing"
                workflow["productivity_context"] = "general_usage"
            
            # Determine workflow stage
            if user_intent == "creating":
                workflow["workflow_stage"] = "creation"
            elif user_intent == "editing":
                workflow["workflow_stage"] = "refinement"
            elif user_intent == "searching":
                workflow["workflow_stage"] = "research"
            elif user_intent == "consuming":
                workflow["workflow_stage"] = "learning"
            else:
                workflow["workflow_stage"] = "navigation"
            
            # Analyze focus indicators
            text_content = text_analysis.get("all_text", "")
            if len(text_content) > 500:
                workflow["focus_indicators"].append("content_heavy")
            if content_analysis.get("complexity_level") == "complex":
                workflow["focus_indicators"].append("complex_task")
            if content_analysis.get("interaction_level") == "active":
                workflow["focus_indicators"].append("active_engagement")
            
            return workflow
            
        except Exception as e:
            logger.error(f"Error analyzing user workflow: {e}")
            return {"current_activity": "unknown", "error": str(e)}

    def _synthesize_comprehensive_context(self, total_analysis: Dict) -> Dict[str, Any]:
        """Synthesize all analysis layers into comprehensive context"""
        try:
            layers = total_analysis.get("layers", {})
            
            synthesis = {
                "overall_context": "unknown",
                "confidence": 0.0,
                "key_insights": [],
                "semantic_summary": "",
                "activity_classification": "unknown",
                "memory_priority": "normal"
            }
            
            # Gather key information from layers
            window_context = layers.get("window_context", {})
            app_analysis = layers.get("application_analysis", {})
            content_analysis = layers.get("content_analysis", {})
            workflow_analysis = layers.get("workflow_analysis", {})
            text_analysis = layers.get("text_analysis", {})
            
            # Determine overall context
            app_name = window_context.get("application_name", "Unknown")
            detected_app = app_analysis.get("detected_app", "unknown")
            current_activity = workflow_analysis.get("current_activity", "unknown")
            content_type = content_analysis.get("content_type", "unknown")
            
            if detected_app != "unknown":
                synthesis["overall_context"] = f"{detected_app}_{current_activity}"
                synthesis["confidence"] = app_analysis.get("confidence", 0.5)
            elif app_name != "Unknown":
                synthesis["overall_context"] = f"application_{app_name.lower().replace(' ', '_')}"
                synthesis["confidence"] = 0.7
            else:
                synthesis["overall_context"] = f"general_{content_type}"
                synthesis["confidence"] = 0.3
            
            # Generate key insights
            insights = []
            
            if text_analysis.get("has_meaningful_content"):
                word_count = text_analysis.get("word_count", 0)
                insights.append(f"Content-rich screen with {word_count} words")
            
            if app_analysis.get("confidence", 0) > 0.7:
                insights.append(f"High confidence {detected_app} detection")
            
            productivity_context = workflow_analysis.get("productivity_context", "unknown")
            if productivity_context != "unknown":
                insights.append(f"User engaged in {productivity_context}")
            
            if content_analysis.get("interaction_level") == "active":
                insights.append("Active user interaction detected")
            
            synthesis["key_insights"] = insights
            
            # Create semantic summary
            summary_parts = []
            if app_name != "Unknown":
                summary_parts.append(f"Using {app_name}")
            if current_activity != "unknown":
                summary_parts.append(f"for {current_activity}")
            if workflow_analysis.get("workflow_stage") != "unknown":
                summary_parts.append(f"in {workflow_analysis.get('workflow_stage', 'unknown')} stage")
            
            synthesis["semantic_summary"] = " ".join(summary_parts) if summary_parts else "General computer usage"
            
            # Classify activity
            if current_activity in ["software_development", "document_work"]:
                synthesis["activity_classification"] = "productive_work"
                synthesis["memory_priority"] = "high"
            elif current_activity in ["communication", "web_browsing"]:
                synthesis["activity_classification"] = "interactive_work"
                synthesis["memory_priority"] = "medium"
            else:
                synthesis["activity_classification"] = "general_usage"
                synthesis["memory_priority"] = "normal"
            
            return synthesis
            
        except Exception as e:
            logger.error(f"Error synthesizing comprehensive context: {e}")
            return {"overall_context": "unknown", "error": str(e)}

    def _create_memory_summary(self, total_analysis: Dict) -> Dict[str, Any]:
        """Create optimized summary for memory storage"""
        try:
            synthesis = total_analysis.get("synthesized_context", {})
            layers = total_analysis.get("layers", {})
            
            memory_summary = {
                "timestamp": total_analysis.get("timestamp"),
                "image_hash": total_analysis.get("image_hash"),
                "overall_context": synthesis.get("overall_context", "unknown"),
                "semantic_summary": synthesis.get("semantic_summary", ""),
                "activity_classification": synthesis.get("activity_classification", "unknown"),
                "memory_priority": synthesis.get("memory_priority", "normal"),
                
                # Application context
                "application": {
                    "name": layers.get("window_context", {}).get("application_name", "Unknown"),
                    "detected_type": layers.get("application_analysis", {}).get("detected_app", "unknown"),
                    "confidence": layers.get("application_analysis", {}).get("confidence", 0.0)
                },
                
                # Content summary
                "content": {
                    "type": layers.get("content_analysis", {}).get("content_type", "unknown"),
                    "word_count": layers.get("text_analysis", {}).get("word_count", 0),
                    "has_meaningful_text": layers.get("text_analysis", {}).get("has_meaningful_content", False),
                    "primary_purpose": layers.get("content_analysis", {}).get("primary_purpose", "unknown"),
                    "interaction_level": layers.get("content_analysis", {}).get("interaction_level", "passive")
                },
                
                # User activity
                "user_activity": {
                    "current_activity": layers.get("workflow_analysis", {}).get("current_activity", "unknown"),
                    "workflow_stage": layers.get("workflow_analysis", {}).get("workflow_stage", "unknown"),
                    "user_intent": layers.get("content_analysis", {}).get("user_intent", "unknown"),
                    "productivity_context": layers.get("workflow_analysis", {}).get("productivity_context", "unknown")
                },
                
                # Key insights for memory
                "key_insights": synthesis.get("key_insights", []),
                "analysis_confidence": synthesis.get("confidence", 0.0),
                
                # Truncated text content for context
                "text_sample": layers.get("text_analysis", {}).get("all_text", "")[:500]
            }
            
            # Add LLaVA insights if available
            if "llava_analysis" in layers and "error" not in layers["llava_analysis"]:
                llava = layers["llava_analysis"]
                memory_summary["llava_insights"] = {
                    "visual_context": llava.get("visual_context", "")[:300],
                    "application_detected": llava.get("application", {}).get("name", ""),
                    "workflow_stage": llava.get("application", {}).get("workflow_stage", "")
                }
            
            return memory_summary
            
        except Exception as e:
            logger.error(f"Error creating memory summary: {e}")
            return {"timestamp": total_analysis.get("timestamp"), "error": str(e)}

    async def _cache_analysis(self, analysis: Dict[str, Any]):
        """Cache comprehensive analysis"""
        try:
            cache_file = os.path.join(self.cache_dir, "latest_total_analysis.json")
            
            # Create cache-friendly version (remove large data)
            cache_data = {
                "timestamp": analysis["timestamp"],
                "image_hash": analysis["image_hash"],
                "memory_summary": analysis.get("memory_summary", {}),
                "synthesized_context": analysis.get("synthesized_context", {}),
                "analysis_duration": analysis.get("analysis_duration", 0)
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.debug(f"Cached total analysis: {len(json.dumps(cache_data))} bytes")
            
        except Exception as e:
            logger.warning(f"Error caching analysis: {e}")

    async def connect_to_bridge(self):
        """Connect to the bridge server with proper keepalive settings"""
        while self.running:
            try:
                # Configure WebSocket connection with keepalive
                websocket = await websockets.connect(
                    self.bridge_uri,
                    ping_interval=20,  # Send ping every 20 seconds
                    ping_timeout=10,   # Wait 10 seconds for pong response
                    close_timeout=5,   # Wait 5 seconds for close handshake
                    max_size=None,     # No message size limit
                    max_queue=32,      # Limit message queue
                    compression=None    # Disable compression for better performance
                )
                logger.info(f"Connected to bridge server at {self.bridge_uri}")
                
                # Wait for welcome message first
                welcome = await websocket.recv()
                welcome_data = json.loads(welcome)
                logger.info(f"Received welcome: {welcome_data.get('type')}")
                
                # Register as total screen analyzer
                await websocket.send(json.dumps({
                    "type": "register",
                    "client_type": "total_screen_analyzer",
                    "version": "2.0.0",
                    "capabilities": [
                        "comprehensive_screen_analysis", 
                        "multi_layer_understanding",
                        "semantic_context_extraction",
                        "workflow_detection",
                        "memory_optimized_output"
                    ]
                }))
                
                # Wait for registration confirmation
                response = await websocket.recv()
                data = json.loads(response)
                if data.get('type') == 'registration_confirmed':
                    logger.info(f"Total Screen Analyzer registered as {data.get('payload', {}).get('client_type')}")
                
                # Main analysis loop
                while self.running:
                    try:
                        # Perform total screen analysis
                        analysis = await self._perform_total_screen_analysis()
                        
                        if analysis:
                            # Send memory-optimized summary to bridge
                            payload = {
                                "type": "sensor_data",
                                "sensor_type": "screen",
                                "data": analysis["memory_summary"]
                            }
                            
                            await websocket.send(json.dumps(payload))
                            
                            activity = analysis["memory_summary"]["user_activity"]["current_activity"]
                            app_name = analysis["memory_summary"]["application"]["name"]
                            logger.info(f"Sent total screen analysis: {app_name} - {activity}")
                        
                        await asyncio.sleep(self.capture_interval)
                        
                    except websockets.exceptions.ConnectionClosed as e:
                        logger.error(f"WebSocket connection closed: {e}")
                        break
                    except Exception as e:
                        logger.error(f"Error in analysis loop: {e}")
                        await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting

    async def run(self):
        """Run the total screen analyzer"""
        logger.info("Starting Total Screen Analyzer")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/total_screen_analyzer.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        await self.connect_to_bridge()

    async def _analyze_with_lightweight_vision(self, screenshot: Image.Image) -> Dict[str, Any]:
        """Lightweight visual analysis without LLaVA - fast and reliable"""
        try:
            width, height = screenshot.size
            
            # Enhanced visual analysis using OCR and computer vision
            analysis = {
                "visual_context": "Lightweight visual analysis",
                "application": {
                    "name": "detected_via_cv",
                    "view": "main_interface",
                    "workflow_stage": "ready"
                },
                "ui_elements": [],
                "user_activity": {
                    "current_task": "interface_interaction",
                    "workflow_stage": "ready",
                    "interaction_points": []
                },
                "visual_content": {
                    "main_content": "interface_ready",
                    "text_content": [],
                    "images": []
                },
                "screen_elements": [],
                "confidence": 0.7,
                "analysis_method": "lightweight_cv_ocr",
                "timestamp": datetime.now().isoformat()
            }
            
            # Quick color analysis for UI type detection
            cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            average_color = cv2.mean(cv_image)
            brightness = sum(average_color[:3]) / 3
            
            # Detect common UI patterns based on color and layout
            if brightness > 200:
                analysis["application"]["view"] = "light_interface"
                analysis["visual_content"]["main_content"] = "bright_ui_ready_for_interaction"
            elif brightness < 100:
                analysis["application"]["view"] = "dark_interface"
                analysis["visual_content"]["main_content"] = "dark_ui_ready_for_interaction"
            else:
                analysis["application"]["view"] = "standard_interface"
                analysis["visual_content"]["main_content"] = "standard_ui_ready_for_interaction"
            
            # Quick UI element detection based on common patterns
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Detect rectangular regions (likely buttons/inputs)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            ui_elements_count = 0
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Filter for reasonable UI element sizes
                if 100 < area < width * height * 0.1 and w > 20 and h > 15:
                    ui_elements_count += 1
                    
                    # Estimate element type
                    aspect_ratio = w / h
                    if 0.8 <= aspect_ratio <= 1.2 and area < 5000:
                        element_type = "button"
                    elif aspect_ratio > 3 and h < 50:
                        element_type = "input_field"
                    else:
                        element_type = "ui_element"
                    
                    analysis["ui_elements"].append({
                        "type": element_type,
                        "position": {"x": x, "y": y, "width": w, "height": h},
                        "confidence": 0.6
                    })
                    
                    # Add interaction points for workflow planning
                    center_x = x + w // 2
                    center_y = y + h // 2
                    analysis["user_activity"]["interaction_points"].append({
                        "x": center_x,
                        "y": center_y,
                        "type": element_type,
                        "confidence": 0.6
                    })
            
            analysis["screen_elements"] = [
                {
                    "type": "interactive_elements",
                    "count": ui_elements_count,
                    "confidence": 0.7
                }
            ]
            
            # Update confidence based on detected elements
            if ui_elements_count > 5:
                analysis["confidence"] = 0.8
            elif ui_elements_count > 2:
                analysis["confidence"] = 0.7
            else:
                analysis["confidence"] = 0.6
            
            logger.info(f"Lightweight vision analysis completed: {ui_elements_count} UI elements detected")
            return analysis
            
        except Exception as e:
            logger.error(f"Lightweight vision analysis failed: {e}")
            return {
                "visual_context": "Lightweight analysis failed",
                "application": {"name": "unknown", "view": "", "workflow_stage": ""},
                "ui_elements": [],
                "user_activity": {"current_task": "", "workflow_stage": "", "interaction_points": []},
                "visual_content": {"main_content": "", "text_content": [], "images": []},
                "screen_elements": [],
                "confidence": 0.3,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def _analyze_with_llava(self, screenshot: Image.Image) -> Dict[str, Any]:
        """Run LLaVA analysis in parallel with other layers"""
        try:
            if not self.llava_processor:
                return {"error": "LLaVA processor not initialized"}
            
            if self.fast_mode:
                logger.info("Fast mode enabled - skipping LLaVA analysis")
                return {
                    "visual_context": "Fast mode - LLaVA analysis skipped",
                    "application": {
                        "name": "unknown",
                        "view": "",
                        "workflow_stage": ""
                    },
                    "ui_elements": [],
                    "user_activity": {
                        "current_task": "",
                        "workflow_stage": "",
                        "interaction_points": []
                    },
                    "visual_content": {
                        "main_content": "",
                        "text_content": [],
                        "images": []
                    },
                    "text_content": [],
                    "screen_elements": [],
                    "timestamp": datetime.now().isoformat()
                }

            # Set longer timeout for LLaVA
            self.llava_processor.timeout = 60  # 60 seconds timeout
            return await self.llava_processor.analyze_screen(screenshot)
        except Exception as e:
            logger.error(f"LLaVA analysis failed: {e}")
            return {"error": str(e)}

# Main execution
async def run_total_analyzer():
    analyzer = TotalScreenAnalyzer()
    await analyzer.run()

if __name__ == "__main__":
    try:
        asyncio.run(run_total_analyzer())
    except KeyboardInterrupt:
        logger.info("Total Screen Analyzer stopped by user")
    except Exception as e:
        logger.error(f"Error running total screen analyzer: {e}")
        logger.error(traceback.format_exc())