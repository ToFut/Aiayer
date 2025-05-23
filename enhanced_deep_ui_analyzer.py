#!/usr/bin/env python3
"""
Enhanced Deep UI Analyzer
Captures in-depth UI understanding and user activities, not just application titles
"""

import sys
import os
import json
import time
import base64
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import subprocess
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import screen capture libraries
try:
    import pytesseract
    from PIL import Image, ImageGrab
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("OCR libraries not available - install with: pip install pytesseract pillow")

try:
    import pyautogui
    pyautogui.FAILSAFE = False  # Disable failsafe
    SCREENSHOT_AVAILABLE = True
except ImportError:
    SCREENSHOT_AVAILABLE = False
    print("Screenshot library not available - install with: pip install pyautogui")

class DeepUIAnalyzer:
    """Deep UI analysis to understand actual user activities"""
    
    def __init__(self):
        self.cache_dir = "cache/deep_ui_analysis"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Activity patterns for deep understanding
        self.activity_patterns = {
            "coding": {
                "keywords": ["function", "class", "import", "def", "var", "const", "if", "else", "for", "while", "return"],
                "file_extensions": [".py", ".js", ".ts", ".html", ".css", ".java", ".cpp", ".go", ".rs"],
                "ui_indicators": ["line numbers", "syntax highlighting", "code editor", "terminal"]
            },
            "debugging": {
                "keywords": ["error", "exception", "stack trace", "breakpoint", "console", "debug", "warning"],
                "ui_indicators": ["debug console", "error messages", "stack trace", "breakpoints"]
            },
            "reading_documentation": {
                "keywords": ["documentation", "tutorial", "guide", "readme", "api", "reference", "help"],
                "ui_indicators": ["documentation site", "help panel", "reference guide"]
            },
            "writing_text": {
                "keywords": ["document", "article", "email", "message", "note", "report"],
                "ui_indicators": ["text editor", "word processor", "email composer", "chat input"]
            },
            "data_analysis": {
                "keywords": ["chart", "graph", "data", "analysis", "visualization", "statistics", "metrics"],
                "ui_indicators": ["spreadsheet", "charts", "graphs", "data tables"]
            },
            "design_work": {
                "keywords": ["design", "wireframe", "prototype", "mockup", "layout", "ui", "ux"],
                "ui_indicators": ["design canvas", "color picker", "layers panel", "design tools"]
            },
            "research": {
                "keywords": ["search", "research", "study", "investigation", "analysis", "findings"],
                "ui_indicators": ["search results", "multiple tabs", "bookmarks", "research tools"]
            },
            "communication": {
                "keywords": ["message", "chat", "email", "call", "meeting", "discussion"],
                "ui_indicators": ["chat interface", "video call", "email client", "messaging app"]
            }
        }
        
        self.ui_element_patterns = {
            "buttons": ["button", "btn", "click", "submit", "cancel", "ok", "save"],
            "input_fields": ["input", "textbox", "field", "enter", "type"],
            "menus": ["menu", "dropdown", "select", "options", "settings"],
            "tabs": ["tab", "sheet", "page", "section"],
            "panels": ["panel", "sidebar", "pane", "window"],
            "lists": ["list", "items", "entries", "rows"]
        }
    
    def capture_screen_content(self) -> Dict[str, Any]:
        """Capture and analyze screen content for deep understanding"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "screen_text": "",
            "detected_activities": [],
            "ui_elements": {},
            "content_analysis": {},
            "user_focus": {},
            "application_context": {},
            "workflow_stage": "unknown"
        }
        
        try:
            if SCREENSHOT_AVAILABLE:
                # Capture screenshot
                screenshot = pyautogui.screenshot()
                screenshot_path = f"{self.cache_dir}/current_screen.png"
                screenshot.save(screenshot_path)
                analysis["screenshot_path"] = screenshot_path
                
                # Extract text from screenshot if OCR available
                if OCR_AVAILABLE:
                    extracted_text = pytesseract.image_to_string(screenshot)
                    analysis["screen_text"] = extracted_text
                    
                    # Analyze extracted text for activities
                    analysis["detected_activities"] = self._analyze_activities(extracted_text)
                    analysis["ui_elements"] = self._detect_ui_elements(extracted_text)
                    analysis["content_analysis"] = self._analyze_content_depth(extracted_text)
                    analysis["user_focus"] = self._analyze_user_focus(extracted_text)
                    
            # Get application context
            analysis["application_context"] = self._get_detailed_app_context()
            
            # Determine workflow stage
            analysis["workflow_stage"] = self._determine_workflow_stage(analysis)
            
        except Exception as e:
            analysis["error"] = str(e)
            print(f"Error in screen capture: {e}")
        
        return analysis
    
    def _analyze_activities(self, text: str) -> List[Dict[str, Any]]:
        """Analyze text to detect specific user activities"""
        detected_activities = []
        text_lower = text.lower()
        
        for activity, patterns in self.activity_patterns.items():
            confidence = 0.0
            matched_keywords = []
            
            # Check for keywords
            for keyword in patterns["keywords"]:
                if keyword in text_lower:
                    confidence += 0.1
                    matched_keywords.append(keyword)
            
            # Check for UI indicators
            ui_matches = []
            for indicator in patterns.get("ui_indicators", []):
                if indicator in text_lower:
                    confidence += 0.2
                    ui_matches.append(indicator)
            
            # Check for file extensions if coding
            if activity == "coding":
                for ext in patterns.get("file_extensions", []):
                    if ext in text_lower:
                        confidence += 0.3
                        matched_keywords.append(f"file{ext}")
            
            if confidence > 0.2:  # Threshold for activity detection
                detected_activities.append({
                    "activity": activity,
                    "confidence": min(confidence, 1.0),
                    "evidence": {
                        "keywords": matched_keywords,
                        "ui_indicators": ui_matches
                    },
                    "intensity": self._calculate_activity_intensity(activity, text_lower)
                })
        
        # Sort by confidence
        detected_activities.sort(key=lambda x: x["confidence"], reverse=True)
        return detected_activities
    
    def _detect_ui_elements(self, text: str) -> Dict[str, List[str]]:
        """Detect specific UI elements in the text"""
        ui_elements = {}
        text_lower = text.lower()
        
        for element_type, patterns in self.ui_element_patterns.items():
            detected = []
            for pattern in patterns:
                # Find context around UI element mentions
                matches = re.finditer(rf'\\b{pattern}\\b', text_lower)
                for match in matches:
                    start = max(0, match.start() - 20)
                    end = min(len(text_lower), match.end() + 20)
                    context = text_lower[start:end].strip()
                    detected.append(context)
            
            if detected:
                ui_elements[element_type] = detected[:5]  # Limit to 5 examples
        
        return ui_elements
    
    def _analyze_content_depth(self, text: str) -> Dict[str, Any]:
        """Analyze the depth and complexity of content"""
        words = text.split()
        lines = text.split('\\n')
        
        # Technical indicators
        technical_terms = ["function", "variable", "method", "class", "object", "array", "database", "api", "algorithm"]
        technical_count = sum(1 for word in words if word.lower() in technical_terms)
        
        # Code indicators
        code_indicators = ["{", "}", "(", ")", "=", "==", "!=", "->", "=>", "//", "/*", "*/"]
        code_count = sum(1 for indicator in code_indicators if indicator in text)
        
        # Documentation indicators
        doc_indicators = ["example", "usage", "parameter", "return", "description", "note", "warning"]
        doc_count = sum(1 for word in words if word.lower() in doc_indicators)
        
        return {
            "word_count": len(words),
            "line_count": len(lines),
            "technical_density": technical_count / max(len(words), 1),
            "code_density": code_count / max(len(text), 1),
            "documentation_density": doc_count / max(len(words), 1),
            "complexity_score": (technical_count + code_count + doc_count) / max(len(words), 1),
            "content_type": self._classify_content_type(text)
        }
    
    def _analyze_user_focus(self, text: str) -> Dict[str, Any]:
        """Analyze what the user is focusing on"""
        focus_analysis = {
            "primary_focus": "unknown",
            "focus_indicators": [],
            "attention_level": 0.0,
            "multitasking": False
        }
        
        # Detect focused editing areas
        if "cursor" in text.lower() or "typing" in text.lower():
            focus_analysis["primary_focus"] = "active_editing"
            focus_analysis["attention_level"] = 0.9
        
        # Detect reading patterns
        if len(text.split()) > 100:  # Long text suggests reading
            focus_analysis["primary_focus"] = "reading"
            focus_analysis["attention_level"] = 0.7
        
        # Detect multitasking
        tab_indicators = ["tab", "window", "switch", "alt+tab"]
        if any(indicator in text.lower() for indicator in tab_indicators):
            focus_analysis["multitasking"] = True
            focus_analysis["attention_level"] *= 0.8  # Reduce attention for multitasking
        
        return focus_analysis
    
    def _get_detailed_app_context(self) -> Dict[str, Any]:
        """Get detailed context about current applications"""
        context = {
            "active_window": self._get_active_window(),
            "window_title": "",
            "process_details": {},
            "file_context": {}
        }
        
        try:
            # Get active window title (macOS)
            if sys.platform == "darwin":
                result = subprocess.run([
                    "osascript", "-e",
                    'tell application "System Events" to get name of first application process whose frontmost is true'
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    context["active_window"] = result.stdout.strip()
                
                # Get window title
                title_result = subprocess.run([
                    "osascript", "-e",
                    'tell application "System Events" to get title of front window of first application process whose frontmost is true'
                ], capture_output=True, text=True)
                if title_result.returncode == 0:
                    context["window_title"] = title_result.stdout.strip()
            
            # Analyze file context from window title
            context["file_context"] = self._analyze_file_context(context.get("window_title", ""))
            
        except Exception as e:
            context["error"] = str(e)
        
        return context
    
    def _analyze_file_context(self, window_title: str) -> Dict[str, Any]:
        """Analyze file context from window title"""
        file_context = {
            "file_name": "",
            "file_extension": "",
            "file_type": "unknown",
            "project_context": "",
            "editing_state": "unknown"
        }
        
        # Extract file name and extension
        file_patterns = [
            r'([^/\\]+\\.(py|js|ts|html|css|java|cpp|go|rs|md|txt|json|yaml|yml))',
            r'([^/\\]+\\.\\w{2,4})'
        ]
        
        for pattern in file_patterns:
            match = re.search(pattern, window_title, re.IGNORECASE)
            if match:
                file_context["file_name"] = match.group(1)
                file_context["file_extension"] = match.group(2) if match.lastindex > 1 else ""
                break
        
        # Determine file type
        if file_context["file_extension"]:
            file_context["file_type"] = self._classify_file_type(file_context["file_extension"])
        
        # Detect editing state
        if "•" in window_title or "*" in window_title:
            file_context["editing_state"] = "unsaved_changes"
        elif file_context["file_name"]:
            file_context["editing_state"] = "editing"
        
        return file_context
    
    def _classify_file_type(self, extension: str) -> str:
        """Classify file type based on extension"""
        type_mapping = {
            "py": "python_code",
            "js": "javascript_code", 
            "ts": "typescript_code",
            "html": "web_markup",
            "css": "stylesheet",
            "java": "java_code",
            "cpp": "cpp_code",
            "go": "go_code",
            "rs": "rust_code",
            "md": "markdown_doc",
            "txt": "text_file",
            "json": "data_file",
            "yaml": "config_file",
            "yml": "config_file"
        }
        return type_mapping.get(extension.lower(), "unknown")
    
    def _classify_content_type(self, text: str) -> str:
        """Classify the type of content being viewed/edited"""
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ["function", "class", "import", "def"]):
            return "source_code"
        elif any(keyword in text_lower for keyword in ["error", "exception", "stack"]):
            return "error_messages"
        elif any(keyword in text_lower for keyword in ["documentation", "readme", "guide"]):
            return "documentation"
        elif any(keyword in text_lower for keyword in ["email", "message", "subject"]):
            return "communication"
        elif any(keyword in text_lower for keyword in ["chart", "graph", "data"]):
            return "data_visualization"
        else:
            return "general_text"
    
    def _calculate_activity_intensity(self, activity: str, text: str) -> float:
        """Calculate how intensely the user is engaged in an activity"""
        # Base intensity on text complexity and activity-specific indicators
        complexity_indicators = {
            "coding": ["function", "class", "method", "variable"],
            "debugging": ["error", "exception", "trace", "breakpoint"],
            "research": ["search", "compare", "analyze", "investigate"]
        }
        
        indicators = complexity_indicators.get(activity, [])
        matches = sum(1 for indicator in indicators if indicator in text)
        
        # Normalize to 0-1 scale
        return min(matches / 10.0, 1.0)
    
    def _determine_workflow_stage(self, analysis: Dict[str, Any]) -> str:
        """Determine what stage of workflow the user is in"""
        activities = analysis.get("detected_activities", [])
        
        if not activities:
            return "idle"
        
        primary_activity = activities[0]["activity"]
        confidence = activities[0]["confidence"]
        
        if confidence > 0.8:
            return f"active_{primary_activity}"
        elif confidence > 0.5:
            return f"light_{primary_activity}"
        else:
            return "transitioning"
    
    def _get_active_window(self) -> str:
        """Get the currently active window name"""
        try:
            if sys.platform == "darwin":  # macOS
                result = subprocess.run([
                    "osascript", "-e",
                    'tell application "System Events" to get name of first application process whose frontmost is true'
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    return result.stdout.strip()
        except Exception:
            pass
        return "unknown"

def test_deep_ui_analyzer():
    """Test the deep UI analyzer"""
    print("🔍 Testing Deep UI Analyzer...")
    
    analyzer = DeepUIAnalyzer()
    analysis = analyzer.capture_screen_content()
    
    print(f"\n📊 Analysis Results:")
    print(f"Timestamp: {analysis['timestamp']}")
    print(f"Active Window: {analysis['application_context'].get('active_window', 'Unknown')}")
    print(f"Window Title: {analysis['application_context'].get('window_title', 'Unknown')}")
    print(f"Workflow Stage: {analysis['workflow_stage']}")
    
    print(f"\n🎯 Detected Activities ({len(analysis['detected_activities'])}):")
    for activity in analysis['detected_activities'][:3]:
        print(f"  • {activity['activity']}: {activity['confidence']:.2f} confidence")
        print(f"    Evidence: {', '.join(activity['evidence']['keywords'][:3])}")
    
    print(f"\n🖥️ UI Elements:")
    for element_type, elements in analysis['ui_elements'].items():
        print(f"  • {element_type}: {len(elements)} detected")
    
    print(f"\n📝 Content Analysis:")
    content = analysis['content_analysis']
    print(f"  • Words: {content.get('word_count', 0)}")
    print(f"  • Content Type: {content.get('content_type', 'unknown')}")
    print(f"  • Complexity Score: {content.get('complexity_score', 0):.2f}")
    
    print(f"\n🎯 User Focus:")
    focus = analysis['user_focus']
    print(f"  • Primary Focus: {focus.get('primary_focus', 'unknown')}")
    print(f"  • Attention Level: {focus.get('attention_level', 0):.2f}")
    print(f"  • Multitasking: {focus.get('multitasking', False)}")
    
    if analysis.get('screen_text'):
        print(f"\n📄 Screen Text Sample:")
        print(f"  {analysis['screen_text'][:200]}...")
    
    return analysis

if __name__ == "__main__":
    test_deep_ui_analyzer()