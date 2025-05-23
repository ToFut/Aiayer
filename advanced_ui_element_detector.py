#!/usr/bin/env python3
"""
Advanced UI Element Detector
Identifies and understands complex UI elements including buttons, graphs, SaaS interfaces
"""

import sys
import os
import json
import re
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import subprocess

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import pytesseract
    from PIL import Image, ImageGrab, ImageDraw, ImageFilter
    import cv2
    import numpy as np
    ADVANCED_VISION_AVAILABLE = True
except ImportError:
    ADVANCED_VISION_AVAILABLE = False
    print("Advanced vision libraries not available - install with: pip install pytesseract pillow opencv-python")

try:
    import pyautogui
    pyautogui.FAILSAFE = False
    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False

class AdvancedUIElementDetector:
    """Advanced UI element detection and understanding"""
    
    def __init__(self):
        self.cache_dir = "cache/ui_element_detection"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # UI Element patterns for different types
        self.ui_patterns = {
            "buttons": {
                "keywords": ["button", "btn", "click", "submit", "cancel", "ok", "save", "delete", "edit", "add", "create", "login", "signup", "download", "upload"],
                "visual_indicators": ["rounded_rectangle", "solid_background", "centered_text"],
                "contexts": ["form", "toolbar", "dialog", "navigation"]
            },
            "input_fields": {
                "keywords": ["input", "field", "textbox", "textarea", "email", "password", "search", "enter", "type"],
                "visual_indicators": ["rectangular_border", "cursor_visible", "placeholder_text"],
                "contexts": ["form", "search", "login", "settings"]
            },
            "dropdowns": {
                "keywords": ["dropdown", "select", "choose", "option", "menu", "picker"],
                "visual_indicators": ["arrow_down", "expandable", "list_items"],
                "contexts": ["form", "filter", "navigation"]
            },
            "checkboxes_radios": {
                "keywords": ["checkbox", "radio", "select", "check", "tick", "option"],
                "visual_indicators": ["square_box", "circle", "checkmark"],
                "contexts": ["form", "settings", "preferences"]
            },
            "navigation": {
                "keywords": ["nav", "menu", "tab", "breadcrumb", "link", "home", "back", "next", "previous"],
                "visual_indicators": ["horizontal_list", "vertical_list", "tabs"],
                "contexts": ["header", "sidebar", "footer"]
            },
            "data_tables": {
                "keywords": ["table", "grid", "row", "column", "sort", "filter", "data", "list", "entries"],
                "visual_indicators": ["grid_lines", "columns", "headers"],
                "contexts": ["dashboard", "admin", "reports"]
            },
            "charts_graphs": {
                "keywords": ["chart", "graph", "plot", "visualization", "analytics", "metrics", "data", "statistics"],
                "visual_indicators": ["axis", "bars", "lines", "pie", "legend"],
                "contexts": ["dashboard", "analytics", "reports"]
            },
            "modals_dialogs": {
                "keywords": ["modal", "dialog", "popup", "alert", "confirm", "warning", "error", "success"],
                "visual_indicators": ["overlay", "centered", "shadow"],
                "contexts": ["confirmation", "notification", "form"]
            },
            "cards_panels": {
                "keywords": ["card", "panel", "widget", "tile", "block", "section"],
                "visual_indicators": ["bordered_rectangle", "grouped_content"],
                "contexts": ["dashboard", "gallery", "feed"]
            },
            "progress_indicators": {
                "keywords": ["progress", "loading", "spinner", "bar", "percent", "%", "complete"],
                "visual_indicators": ["horizontal_bar", "circular", "animated"],
                "contexts": ["upload", "processing", "installation"]
            }
        }
        
        # SaaS platform specific patterns
        self.saas_patterns = {
            "salesforce": {
                "indicators": ["salesforce", "lightning", "opportunity", "lead", "account", "contact", "case"],
                "ui_elements": ["record_form", "related_lists", "activity_timeline", "kanban_board"]
            },
            "slack": {
                "indicators": ["slack", "channel", "message", "thread", "dm", "workspace"],
                "ui_elements": ["message_input", "channel_list", "thread_view", "file_upload"]
            },
            "jira": {
                "indicators": ["jira", "issue", "epic", "story", "bug", "task", "sprint"],
                "ui_elements": ["issue_form", "board_view", "backlog", "filters"]
            },
            "github": {
                "indicators": ["github", "repository", "pull request", "issue", "commit", "branch"],
                "ui_elements": ["code_editor", "diff_view", "pr_form", "issue_tracker"]
            },
            "figma": {
                "indicators": ["figma", "design", "frame", "component", "layer", "prototype"],
                "ui_elements": ["design_canvas", "layers_panel", "properties_panel", "toolbar"]
            },
            "notion": {
                "indicators": ["notion", "page", "block", "database", "template", "workspace"],
                "ui_elements": ["block_editor", "database_view", "page_tree", "properties"]
            },
            "google_workspace": {
                "indicators": ["google", "drive", "docs", "sheets", "slides", "gmail"],
                "ui_elements": ["document_editor", "spreadsheet_grid", "email_composer", "file_browser"]
            },
            "microsoft_365": {
                "indicators": ["microsoft", "office", "word", "excel", "powerpoint", "teams"],
                "ui_elements": ["ribbon_toolbar", "document_view", "chat_interface", "file_explorer"]
            }
        }
        
        # Chart and graph specific patterns
        self.chart_patterns = {
            "bar_chart": ["bar", "column", "histogram", "vertical", "horizontal"],
            "line_chart": ["line", "trend", "time series", "continuous", "curve"],
            "pie_chart": ["pie", "donut", "circular", "percentage", "proportion"],
            "scatter_plot": ["scatter", "plot", "correlation", "xy", "bubble"],
            "area_chart": ["area", "filled", "stacked", "cumulative"],
            "heatmap": ["heatmap", "heat", "density", "color coded", "matrix"],
            "gantt_chart": ["gantt", "timeline", "schedule", "project", "duration"],
            "funnel_chart": ["funnel", "conversion", "stages", "pipeline"],
            "dashboard": ["dashboard", "kpi", "metrics", "overview", "summary"]
        }
        
        # Interactive element patterns
        self.interactive_patterns = {
            "clickable": ["click", "tap", "select", "choose", "activate"],
            "editable": ["edit", "modify", "change", "update", "input"],
            "draggable": ["drag", "move", "reorder", "sort", "drop"],
            "expandable": ["expand", "collapse", "toggle", "show", "hide"],
            "filterable": ["filter", "search", "sort", "find", "query"],
            "downloadable": ["download", "export", "save", "pdf", "csv"],
            "uploadable": ["upload", "import", "attach", "browse", "select file"]
        }
    
    def analyze_ui_elements(self, screenshot_path: str = None) -> Dict[str, Any]:
        """Analyze UI elements in the current screen or provided screenshot"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "ui_elements": {},
            "saas_platform": None,
            "charts_detected": [],
            "interactive_elements": {},
            "ui_layout": {},
            "complexity_score": 0.0,
            "accessibility_indicators": {},
            "user_focus_elements": []
        }
        
        try:
            # Capture screenshot if not provided
            if not screenshot_path and SCREENSHOT_AVAILABLE:
                screenshot = pyautogui.screenshot()
                screenshot_path = f"{self.cache_dir}/current_ui_analysis.png"
                screenshot.save(screenshot_path)
                analysis["screenshot_path"] = screenshot_path
            
            if screenshot_path and os.path.exists(screenshot_path):
                # Extract text from screenshot
                extracted_text = self._extract_text_from_image(screenshot_path)
                analysis["extracted_text"] = extracted_text
                
                # Analyze UI elements
                analysis["ui_elements"] = self._detect_ui_elements(extracted_text)
                
                # Detect SaaS platform
                analysis["saas_platform"] = self._detect_saas_platform(extracted_text)
                
                # Detect charts and graphs
                analysis["charts_detected"] = self._detect_charts_graphs(extracted_text, screenshot_path)
                
                # Detect interactive elements
                analysis["interactive_elements"] = self._detect_interactive_elements(extracted_text)
                
                # Analyze UI layout
                analysis["ui_layout"] = self._analyze_ui_layout(extracted_text)
                
                # Calculate complexity score
                analysis["complexity_score"] = self._calculate_ui_complexity(analysis)
                
                # Detect accessibility indicators
                analysis["accessibility_indicators"] = self._detect_accessibility_features(extracted_text)
                
                # Identify user focus elements
                analysis["user_focus_elements"] = self._identify_focus_elements(extracted_text)
                
                # Visual analysis if computer vision is available
                if ADVANCED_VISION_AVAILABLE:
                    visual_analysis = self._perform_visual_analysis(screenshot_path)
                    analysis["visual_elements"] = visual_analysis
        
        except Exception as e:
            analysis["error"] = str(e)
            print(f"Error in UI analysis: {e}")
        
        return analysis
    
    def _extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            if ADVANCED_VISION_AVAILABLE:
                image = Image.open(image_path)
                # Enhance image for better OCR
                enhanced_image = self._enhance_image_for_ocr(image)
                text = pytesseract.image_to_string(enhanced_image)
                return text
        except Exception as e:
            print(f"OCR extraction error: {e}")
        return ""
    
    def _enhance_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for better OCR results"""
        # Convert to grayscale
        gray = image.convert('L')
        
        # Increase contrast
        enhanced = gray.point(lambda x: 0 if x < 128 else 255, '1')
        
        # Scale up for better OCR
        width, height = enhanced.size
        enhanced = enhanced.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
        
        return enhanced
    
    def _detect_ui_elements(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Detect various UI elements from extracted text"""
        detected_elements = {}
        text_lower = text.lower()
        lines = text.split('\n')
        
        for element_type, patterns in self.ui_patterns.items():
            elements = []
            keywords = patterns["keywords"]
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                if not line_lower:
                    continue
                
                # Check for element keywords
                for keyword in keywords:
                    if keyword in line_lower:
                        element_info = {
                            "text": line.strip(),
                            "line_number": i,
                            "confidence": self._calculate_element_confidence(line_lower, patterns),
                            "context": self._determine_element_context(line_lower, lines, i),
                            "functionality": self._infer_element_functionality(line_lower, element_type)
                        }
                        elements.append(element_info)
                        break
            
            if elements:
                detected_elements[element_type] = elements
        
        return detected_elements
    
    def _detect_saas_platform(self, text: str) -> Optional[Dict[str, Any]]:
        """Detect which SaaS platform is being used"""
        text_lower = text.lower()
        
        for platform, patterns in self.saas_patterns.items():
            matches = 0
            matched_indicators = []
            
            for indicator in patterns["indicators"]:
                if indicator in text_lower:
                    matches += 1
                    matched_indicators.append(indicator)
            
            if matches >= 2:  # Require at least 2 indicators
                return {
                    "platform": platform,
                    "confidence": min(matches / len(patterns["indicators"]), 1.0),
                    "matched_indicators": matched_indicators,
                    "ui_elements": self._detect_saas_ui_elements(text_lower, patterns["ui_elements"])
                }
        
        return None
    
    def _detect_charts_graphs(self, text: str, screenshot_path: str) -> List[Dict[str, Any]]:
        """Detect charts and graphs in the UI"""
        detected_charts = []
        text_lower = text.lower()
        
        for chart_type, keywords in self.chart_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    chart_info = {
                        "type": chart_type,
                        "keyword_match": keyword,
                        "confidence": self._calculate_chart_confidence(text_lower, chart_type),
                        "data_indicators": self._extract_chart_data_indicators(text_lower),
                        "interactivity": self._detect_chart_interactivity(text_lower)
                    }
                    
                    # Visual analysis for charts if available
                    if ADVANCED_VISION_AVAILABLE:
                        visual_chart_info = self._analyze_chart_visually(screenshot_path, chart_type)
                        chart_info.update(visual_chart_info)
                    
                    detected_charts.append(chart_info)
                    break
        
        return detected_charts
    
    def _detect_interactive_elements(self, text: str) -> Dict[str, List[str]]:
        """Detect interactive elements and their capabilities"""
        interactive_elements = {}
        text_lower = text.lower()
        
        for interaction_type, keywords in self.interactive_patterns.items():
            found_elements = []
            for keyword in keywords:
                if keyword in text_lower:
                    # Find context around the keyword
                    context = self._extract_context_around_keyword(text_lower, keyword)
                    found_elements.append(context)
            
            if found_elements:
                interactive_elements[interaction_type] = found_elements
        
        return interactive_elements
    
    def _analyze_ui_layout(self, text: str) -> Dict[str, Any]:
        """Analyze the overall UI layout and structure"""
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        layout_analysis = {
            "total_elements": len(non_empty_lines),
            "layout_type": self._determine_layout_type(text),
            "navigation_structure": self._analyze_navigation_structure(text),
            "content_areas": self._identify_content_areas(text),
            "density": len(non_empty_lines) / max(len(lines), 1),
            "organization": self._assess_organization_quality(text)
        }
        
        return layout_analysis
    
    def _calculate_ui_complexity(self, analysis: Dict[str, Any]) -> float:
        """Calculate UI complexity score"""
        complexity = 0.0
        
        # Element count factor
        total_elements = sum(len(elements) for elements in analysis["ui_elements"].values())
        complexity += min(total_elements / 20.0, 1.0) * 0.3
        
        # Chart complexity
        charts_count = len(analysis["charts_detected"])
        complexity += min(charts_count / 5.0, 1.0) * 0.2
        
        # Interactive elements
        interactive_count = sum(len(elements) for elements in analysis["interactive_elements"].values())
        complexity += min(interactive_count / 10.0, 1.0) * 0.2
        
        # SaaS platform complexity
        if analysis["saas_platform"]:
            complexity += 0.3
        
        return min(complexity, 1.0)
    
    def _detect_accessibility_features(self, text: str) -> Dict[str, Any]:
        """Detect accessibility features in the UI"""
        accessibility_keywords = ["alt", "aria", "label", "title", "tooltip", "help", "description"]
        text_lower = text.lower()
        
        features = {
            "alt_text_present": "alt" in text_lower,
            "labels_detected": any(keyword in text_lower for keyword in ["label", "aria-label"]),
            "help_text": any(keyword in text_lower for keyword in ["help", "tooltip", "description"]),
            "keyboard_navigation": any(keyword in text_lower for keyword in ["tab", "enter", "space", "arrow"]),
            "accessibility_score": 0.0
        }
        
        # Calculate accessibility score
        features["accessibility_score"] = sum(features[key] for key in features if isinstance(features[key], bool)) / 4.0
        
        return features
    
    def _identify_focus_elements(self, text: str) -> List[Dict[str, Any]]:
        """Identify elements that likely have user focus"""
        focus_indicators = ["focused", "selected", "active", "current", "highlighted", "cursor"]
        focus_elements = []
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            for indicator in focus_indicators:
                if indicator in line_lower:
                    focus_elements.append({
                        "text": line.strip(),
                        "line_number": i,
                        "focus_type": indicator,
                        "confidence": 0.8 if indicator in ["focused", "selected"] else 0.6
                    })
                    break
        
        return focus_elements
    
    def _perform_visual_analysis(self, image_path: str) -> Dict[str, Any]:
        """Perform computer vision analysis on the screenshot"""
        visual_analysis = {
            "color_scheme": {},
            "layout_regions": [],
            "visual_hierarchy": {},
            "ui_patterns": []
        }
        
        try:
            if ADVANCED_VISION_AVAILABLE:
                # Load image with OpenCV
                image = cv2.imread(image_path)
                
                # Analyze color scheme
                visual_analysis["color_scheme"] = self._analyze_color_scheme(image)
                
                # Detect layout regions
                visual_analysis["layout_regions"] = self._detect_layout_regions(image)
                
                # Analyze visual hierarchy
                visual_analysis["visual_hierarchy"] = self._analyze_visual_hierarchy(image)
                
        except Exception as e:
            visual_analysis["error"] = str(e)
        
        return visual_analysis
    
    # Helper methods
    def _calculate_element_confidence(self, text: str, patterns: Dict) -> float:
        """Calculate confidence score for element detection"""
        confidence = 0.0
        
        # Keyword match
        keyword_matches = sum(1 for keyword in patterns["keywords"] if keyword in text)
        confidence += keyword_matches / len(patterns["keywords"]) * 0.7
        
        # Context match
        context_matches = sum(1 for context in patterns["contexts"] if context in text)
        confidence += context_matches / len(patterns["contexts"]) * 0.3
        
        return min(confidence, 1.0)
    
    def _determine_element_context(self, line: str, all_lines: List[str], line_index: int) -> str:
        """Determine the context of a UI element"""
        # Look at surrounding lines for context
        start_idx = max(0, line_index - 2)
        end_idx = min(len(all_lines), line_index + 3)
        context_lines = all_lines[start_idx:end_idx]
        context_text = ' '.join(context_lines).lower()
        
        contexts = ["form", "navigation", "header", "footer", "sidebar", "content", "dialog", "menu"]
        for context in contexts:
            if context in context_text:
                return context
        
        return "general"
    
    def _infer_element_functionality(self, text: str, element_type: str) -> str:
        """Infer the functionality of a UI element"""
        functionality_map = {
            "buttons": {
                "submit": "form_submission",
                "save": "data_persistence", 
                "delete": "data_removal",
                "edit": "content_modification",
                "cancel": "action_cancellation",
                "login": "authentication",
                "download": "file_retrieval"
            },
            "input_fields": {
                "email": "email_input",
                "password": "credential_input",
                "search": "query_input",
                "name": "identity_input"
            }
        }
        
        if element_type in functionality_map:
            for keyword, functionality in functionality_map[element_type].items():
                if keyword in text:
                    return functionality
        
        return f"general_{element_type}"
    
    def _detect_saas_ui_elements(self, text: str, ui_elements: List[str]) -> List[str]:
        """Detect specific SaaS UI elements"""
        detected = []
        for element in ui_elements:
            if element.replace('_', ' ') in text or element.replace('_', '') in text:
                detected.append(element)
        return detected
    
    def _calculate_chart_confidence(self, text: str, chart_type: str) -> float:
        """Calculate confidence for chart detection"""
        chart_keywords = self.chart_patterns[chart_type]
        matches = sum(1 for keyword in chart_keywords if keyword in text)
        return min(matches / len(chart_keywords), 1.0)
    
    def _extract_chart_data_indicators(self, text: str) -> List[str]:
        """Extract indicators of chart data"""
        data_indicators = ["x-axis", "y-axis", "legend", "series", "data points", "values", "labels"]
        found_indicators = [indicator for indicator in data_indicators if indicator in text]
        return found_indicators
    
    def _detect_chart_interactivity(self, text: str) -> Dict[str, bool]:
        """Detect interactive features of charts"""
        interactive_features = {
            "zoomable": any(keyword in text for keyword in ["zoom", "scale", "magnify"]),
            "filterable": any(keyword in text for keyword in ["filter", "select", "hide"]),
            "clickable": any(keyword in text for keyword in ["click", "select", "drill"]),
            "hoverable": any(keyword in text for keyword in ["hover", "tooltip", "popup"])
        }
        return interactive_features
    
    def _extract_context_around_keyword(self, text: str, keyword: str) -> str:
        """Extract context around a keyword"""
        keyword_index = text.find(keyword)
        if keyword_index != -1:
            start = max(0, keyword_index - 30)
            end = min(len(text), keyword_index + 30)
            return text[start:end].strip()
        return keyword
    
    def _determine_layout_type(self, text: str) -> str:
        """Determine the type of UI layout"""
        layout_indicators = {
            "dashboard": ["dashboard", "overview", "metrics", "kpi"],
            "form": ["form", "input", "field", "submit"],
            "list": ["list", "table", "grid", "rows"],
            "navigation": ["menu", "nav", "breadcrumb", "tabs"]
        }
        
        text_lower = text.lower()
        for layout_type, indicators in layout_indicators.items():
            if any(indicator in text_lower for indicator in indicators):
                return layout_type
        
        return "general"
    
    def _analyze_navigation_structure(self, text: str) -> Dict[str, Any]:
        """Analyze navigation structure"""
        nav_elements = ["home", "back", "next", "menu", "tab", "breadcrumb"]
        text_lower = text.lower()
        
        detected_nav = [element for element in nav_elements if element in text_lower]
        
        return {
            "navigation_elements": detected_nav,
            "navigation_complexity": len(detected_nav),
            "has_breadcrumbs": "breadcrumb" in detected_nav,
            "has_tabs": "tab" in detected_nav
        }
    
    def _identify_content_areas(self, text: str) -> List[str]:
        """Identify different content areas in the UI"""
        content_areas = ["header", "sidebar", "main", "content", "footer", "navigation"]
        text_lower = text.lower()
        
        identified_areas = [area for area in content_areas if area in text_lower]
        return identified_areas
    
    def _assess_organization_quality(self, text: str) -> float:
        """Assess how well organized the UI appears to be"""
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Basic organization metrics
        avg_line_length = sum(len(line) for line in non_empty_lines) / max(len(non_empty_lines), 1)
        
        # Consistent formatting indicators
        consistent_formatting = 0.0
        if len(non_empty_lines) > 5:
            # Check for consistent indentation or structure
            indented_lines = sum(1 for line in non_empty_lines if line.startswith(' '))
            consistent_formatting = indented_lines / len(non_empty_lines)
        
        # Organization score (0-1)
        organization_score = min((avg_line_length / 50.0) * 0.5 + consistent_formatting * 0.5, 1.0)
        
        return organization_score
    
    def _analyze_color_scheme(self, image) -> Dict[str, Any]:
        """Analyze the color scheme of the UI"""
        # Extract dominant colors
        data = image.reshape((-1, 3))
        data = np.float32(data)
        
        # Use k-means to find dominant colors
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        k = 5
        _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
        
        # Convert to hex colors
        colors = []
        for center in centers:
            color_hex = '#{:02x}{:02x}{:02x}'.format(int(center[2]), int(center[1]), int(center[0]))
            colors.append(color_hex)
        
        return {
            "dominant_colors": colors,
            "color_count": len(colors),
            "scheme_type": self._classify_color_scheme(colors)
        }
    
    def _classify_color_scheme(self, colors: List[str]) -> str:
        """Classify the type of color scheme"""
        # Simple classification based on color analysis
        if len(colors) <= 2:
            return "monochromatic"
        elif len(colors) <= 4:
            return "minimal"
        else:
            return "colorful"
    
    def _detect_layout_regions(self, image) -> List[Dict[str, Any]]:
        """Detect layout regions using computer vision"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Find contours to identify regions
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        regions = []
        for contour in contours[:10]:  # Limit to top 10 largest regions
            area = cv2.contourArea(contour)
            if area > 1000:  # Filter small areas
                x, y, w, h = cv2.boundingRect(contour)
                regions.append({
                    "x": int(x), "y": int(y), 
                    "width": int(w), "height": int(h),
                    "area": int(area)
                })
        
        return regions
    
    def _analyze_visual_hierarchy(self, image) -> Dict[str, Any]:
        """Analyze visual hierarchy in the UI"""
        # Basic visual hierarchy analysis
        height, width = image.shape[:2]
        
        return {
            "image_dimensions": {"width": width, "height": height},
            "aspect_ratio": width / height,
            "layout_orientation": "landscape" if width > height else "portrait"
        }

def test_advanced_ui_detector():
    """Test the advanced UI element detector"""
    print("🔍 Testing Advanced UI Element Detector...")
    
    detector = AdvancedUIElementDetector()
    analysis = detector.analyze_ui_elements()
    
    print(f"\n📊 UI Analysis Results:")
    print(f"Timestamp: {analysis['timestamp']}")
    print(f"Complexity Score: {analysis['complexity_score']:.2f}")
    
    # Show detected UI elements
    print(f"\n🎛️ Detected UI Elements:")
    for element_type, elements in analysis['ui_elements'].items():
        print(f"  • {element_type}: {len(elements)} detected")
        for element in elements[:2]:  # Show first 2 examples
            print(f"    - {element['text'][:50]}... (confidence: {element['confidence']:.2f})")
    
    # Show SaaS platform detection
    if analysis['saas_platform']:
        platform = analysis['saas_platform']
        print(f"\n🏢 SaaS Platform Detected:")
        print(f"  • Platform: {platform['platform']}")
        print(f"  • Confidence: {platform['confidence']:.2f}")
        print(f"  • Indicators: {', '.join(platform['matched_indicators'])}")
    
    # Show charts detected
    if analysis['charts_detected']:
        print(f"\n📊 Charts/Graphs Detected:")
        for chart in analysis['charts_detected']:
            print(f"  • {chart['type']}: {chart['confidence']:.2f} confidence")
    
    # Show interactive elements
    print(f"\n🖱️ Interactive Elements:")
    for interaction_type, elements in analysis['interactive_elements'].items():
        if elements:
            print(f"  • {interaction_type}: {len(elements)} detected")
    
    # Show layout analysis
    layout = analysis['ui_layout']
    print(f"\n📐 Layout Analysis:")
    print(f"  • Layout Type: {layout['layout_type']}")
    print(f"  • Total Elements: {layout['total_elements']}")
    print(f"  • Density: {layout['density']:.2f}")
    print(f"  • Organization Quality: {layout['organization']:.2f}")
    
    # Show accessibility
    accessibility = analysis['accessibility_indicators']
    print(f"\n♿ Accessibility Features:")
    print(f"  • Accessibility Score: {accessibility['accessibility_score']:.2f}")
    print(f"  • Labels Present: {accessibility['labels_detected']}")
    print(f"  • Help Text: {accessibility['help_text']}")
    
    return analysis

if __name__ == "__main__":
    test_advanced_ui_detector()