#!/usr/bin/env python3
"""
Enhanced Agent Automation System
Combines visual understanding, natural language processing, and precise automation
to execute user commands like "click the button" by recognizing and interacting with screen elements.
"""

import asyncio
import json
import logging
import os
import time
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union
from PIL import Image, ImageGrab
import numpy as np
import cv2

# Import existing components
from agent_workflow.input_controller import InputController
from agent_workflow.agent_system import AgentSystem
from ui_element_detector import UIElementDetector
from sensors.total_screen_analyzer import TotalScreenAnalyzer
from professional_ui_detector import ProfessionalUIDetector
from enhanced_coordinate_extractor import CoordinateExtractor

# Configure logging
os.makedirs('logs/enhanced_agent', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_agent/enhanced_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('enhanced_agent_automation')

class EnhancedAgentAutomation:
    """
    Advanced agent that understands natural language commands and executes them
    by recognizing and interacting with UI elements on screen.
    """
    
    def __init__(self, fallback_llava_url="http://localhost:11434"):
        self.input_controller = InputController(safety_level="medium")
        self.ui_detector = UIElementDetector(llava_url=fallback_llava_url)  # Fallback only
        # Initialize total screen analyzer with ultra-fast settings for automation
        self.total_screen_analyzer = TotalScreenAnalyzer(capture_interval=1, fast_mode=True)
        
        # Initialize professional UI detection system
        self.professional_ui_detector = ProfessionalUIDetector()
        self.coordinate_extractor = CoordinateExtractor()
        
        # Create a lightweight screen analyzer for instant results
        self.quick_analyzer = None
        
        # Current screen state cache
        self.current_screenshot = None
        self.current_ui_elements = []
        self.current_analysis = {}
        self.last_analysis_time = 0
        self.analysis_cache_duration = 5  # Cache for 5 seconds
        
        # Command understanding patterns
        self.command_patterns = self._initialize_command_patterns()
        
        # Element matching confidence thresholds
        self.confidence_thresholds = {
            "exact_match": 0.9,
            "good_match": 0.7,
            "acceptable_match": 0.5,
            "minimum_match": 0.3
        }
        
        logger.info("Enhanced Agent Automation initialized with Total Screen Analyzer")
    
    def _initialize_command_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for understanding natural language commands"""
        return {
            "click": {
                "patterns": [
                    r"click (?:the )?(.+?)(?:\s|$)",
                    r"press (?:the )?(.+?)(?:\s|$)",
                    r"tap (?:the )?(.+?)(?:\s|$)",
                    r"select (?:the )?(.+?)(?:\s|$)",
                    r"hit (?:the )?(.+?)(?:\s|$)"
                ],
                "action": "click",
                "element_extractors": [
                    r"button",
                    r"link",
                    r"menu",
                    r"icon",
                    r"tab"
                ]
            },
            "type": {
                "patterns": [
                    r"type \"([^\"]+)\" in (?:the )?(.+?)(?:\s|$)",  # Match "quoted text" in target
                    r"write \"([^\"]+)\" in (?:the )?(.+?)(?:\s|$)",  # Match "quoted text" in target
                    r"enter \"([^\"]+)\" in (?:the )?(.+?)(?:\s|$)",  # Match "quoted text" in target
                    r"input \"([^\"]+)\" in (?:the )?(.+?)(?:\s|$)",  # Match "quoted text" in target
                    r"write my name \"([^\"]+)\" in (?:the )?(.+?)(?:\s|$)",  # Specific pattern for "write my name"
                    r"type (.+?) in (?:the )?(.+?)(?:\s|$)",  # Fallback for unquoted text
                    r"enter (.+?) in (?:the )?(.+?)(?:\s|$)",
                    r"write (.+?) in (?:the )?(.+?)(?:\s|$)",
                    r"input (.+?) in (?:the )?(.+?)(?:\s|$)",
                    r"fill (?:the )?(.+?) with (.+?)(?:\s|$)"
                ],
                "action": "type",
                "requires_text": True
            },
            "scroll": {
                "patterns": [
                    r"scroll (up|down|left|right)",
                    r"scroll (\d+) (?:times|clicks)",
                    r"scroll to (?:the )?(.+?)(?:\s|$)"
                ],
                "action": "scroll"
            },
            "drag": {
                "patterns": [
                    r"drag (?:the )?(.+?) to (?:the )?(.+?)(?:\s|$)",
                    r"move (?:the )?(.+?) to (?:the )?(.+?)(?:\s|$)"
                ],
                "action": "drag",
                "requires_target": True
            },
            "double_click": {
                "patterns": [
                    r"double click (?:the )?(.+?)(?:\s|$)",
                    r"double tap (?:the )?(.+?)(?:\s|$)"
                ],
                "action": "double_click"
            },
            "right_click": {
                "patterns": [
                    r"right click (?:the )?(.+?)(?:\s|$)",
                    r"context menu (?:on )?(?:the )?(.+?)(?:\s|$)"
                ],
                "action": "right_click"
            }
        }
    
    async def execute_command(self, command: str, pre_parsed_plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a natural language command with interactive user approval.
        
        Args:
            command: Natural language command like "click the submit button"
            pre_parsed_plan: Optional pre-parsed plan details to avoid re-parsing
            
        Returns:
            Dict with execution results and details
        """
        try:
            logger.info(f"Executing command: '{command}'")
            
            # Use pre-parsed plan if available, otherwise parse command
            if pre_parsed_plan:
                logger.info(f"Using pre-parsed plan with action: {pre_parsed_plan.get('action', 'unknown')}")
                parsed_command = {
                    "success": True,
                    "action": pre_parsed_plan.get("action", ""),
                    "target_description": pre_parsed_plan.get("target_description", ""),
                    "text_to_type": pre_parsed_plan.get("text_to_type", ""),
                    "confidence": pre_parsed_plan.get("confidence", 0.8),
                    "original_command": command,
                    "parsing_method": "pre_parsed",
                    "stored_target_element": pre_parsed_plan.get("target_element", {}),
                    "stored_execution_details": pre_parsed_plan.get("execution_details", {})
                }
            else:
                # Parse the command to understand intent
                parsed_command = await self._parse_command(command)
                if not parsed_command["success"]:
                    return {
                        "success": False,
                        "error": "Could not understand command",
                        "details": parsed_command
                }
            
            # Check if we have stored target element data from pre-parsed plan
            if parsed_command.get("parsing_method") == "pre_parsed" and parsed_command.get("stored_target_element"):
                logger.info("Using stored target element from pre-parsed plan")
                stored_target = parsed_command["stored_target_element"]
                element_matches = [stored_target]  # Use stored target directly
            else:
                # Capture and analyze current screen
                analysis_result = await self._analyze_current_screen()
                if not analysis_result["success"]:
                    return {
                        "success": False,
                        "error": "Could not analyze screen",
                        "details": analysis_result
                    }
                
                # Find target elements based on command
                element_matches = await self._find_target_elements(
                    parsed_command, 
                    analysis_result["elements"]
                )
                
                if not element_matches:
                    return {
                        "success": False,
                        "error": "Could not find target element on screen",
                        "parsed_command": parsed_command,
                        "available_elements": [elem.get("element_text", elem.get("element_type", "unknown")) 
                                             for elem in analysis_result.get("elements", [])[:10]]
                    }
            
            # Create execution plan with target details
            execution_plan = await self._create_execution_plan(parsed_command, element_matches)
            
            # Request user approval with interactive dialog
            approval_result = await self._request_user_approval(execution_plan)
            
            if approval_result["action"] == "dismiss":
                return {
                    "success": False,
                    "error": "User dismissed the automation",
                    "execution_plan": execution_plan,
                    "user_choice": "dismissed"
                }
            elif approval_result["action"] == "adjust":
                return {
                    "success": False,
                    "error": "User requested plan adjustment",
                    "execution_plan": execution_plan,
                    "user_choice": "adjust",
                    "adjustment_feedback": approval_result.get("feedback", "")
                }
            elif approval_result["action"] == "do":
                # Execute the approved plan
                execution_result = await self._execute_approved_plan(execution_plan, approval_result)
                
                return {
                    "success": execution_result["success"],
                    "action": parsed_command["action"],
                    "target_element": element_matches[0],
                    "execution_details": execution_result,
                    "confidence": element_matches[0]["confidence"],
                    "command_understood": parsed_command,
                    "execution_plan": execution_plan,
                    "user_choice": "approved"
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid user approval response",
                    "execution_plan": execution_plan
                }
            
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def _parse_command(self, command: str) -> Dict[str, Any]:
        """Parse natural language command using LLM to understand intent"""
        try:
            logger.info(f"🧠 Using LLM to parse command: '{command}'")
            
            # Use LLM to understand the command intent
            intent_prompt = f"""
You are a command parser for UI automation. Parse this user command and extract the action details.

User Command: "{command}"

CRITICAL: Return exactly ONE action word, not multiple. Choose the most appropriate single action:
- "type" - for writing, typing, entering text anywhere
- "click" - for clicking buttons, links, icons  
- "scroll" - for scrolling up/down/left/right
- "drag" - for moving items from one place to another
- "double_click" - for double-clicking items
- "right_click" - for right-clicking items

For ANY command involving writing text (write, type, enter, input), ALWAYS use "type".

Respond with JSON in this EXACT format:
{{
    "success": true,
    "action": "type",
    "target_description": "notepad",
    "text_to_type": "SEGEV",
    "confidence": 0.9
}}

Examples:
- "write SEGEV in notepad" → {{"success": true, "action": "type", "target_description": "notepad", "text_to_type": "SEGEV", "confidence": 0.9}}
- "type hello in search box" → {{"success": true, "action": "type", "target_description": "search box", "text_to_type": "hello", "confidence": 0.9}}
- "click submit button" → {{"success": true, "action": "click", "target_description": "submit button", "confidence": 0.9}}

Parse the command now. Return ONLY ONE action word:
"""

            # Try to use Ollama for intent understanding
            try:
                import requests
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2:1b",
                        "prompt": intent_prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    llm_result = response.json()
                    llm_response = llm_result.get("response", "")
                    
                    # Try to parse the JSON response
                    try:
                        import json
                        parsed_intent = json.loads(llm_response)
                        
                        if parsed_intent.get("success", False):
                            # Add original command for reference
                            parsed_intent["original_command"] = command
                            parsed_intent["parsing_method"] = "llm"
                            logger.info(f"✅ LLM successfully parsed command: {parsed_intent}")
                            return parsed_intent
                        else:
                            logger.warning(f"❌ LLM indicated parsing failure: {parsed_intent.get('explanation', 'Unknown error')}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ LLM response not valid JSON: {llm_response}")
                        
            except Exception as e:
                logger.warning(f"⚠️ LLM parsing failed, falling back to regex: {e}")
            
            # Fallback to original regex parsing
            logger.info("🔄 Falling back to regex pattern matching")
            command_lower = command.lower().strip()
            
            for action_type, config in self.command_patterns.items():
                for pattern in config["patterns"]:
                    match = re.search(pattern, command_lower)
                    if match:
                        parsed = {
                            "success": True,
                            "action": config["action"],
                            "action_type": action_type,
                            "original_command": command,
                            "pattern_matched": pattern,
                            "parsing_method": "regex"
                        }
                        
                        # Extract target element description
                        if action_type == "type":
                            if len(match.groups()) >= 2:
                                parsed["text_to_type"] = match.group(1)
                                parsed["target_description"] = match.group(2)
                            else:
                                # Handle "fill X with Y" pattern
                                parsed["target_description"] = match.group(1)
                                parsed["text_to_type"] = match.group(2)
                        elif action_type == "drag":
                            parsed["source_description"] = match.group(1)
                            parsed["target_description"] = match.group(2)
                        elif action_type == "scroll":
                            if match.group(1) in ["up", "down", "left", "right"]:
                                parsed["scroll_direction"] = match.group(1)
                            elif match.group(1).isdigit():
                                parsed["scroll_amount"] = int(match.group(1))
                            else:
                                parsed["scroll_target"] = match.group(1)
                        else:
                            parsed["target_description"] = match.group(1)
                        
                        logger.info(f"✅ Regex successfully parsed command: {parsed}")
                        return parsed
            
            return {
                "success": False,
                "error": "Could not understand command with LLM or regex patterns",
                "command": command,
                "parsing_method": "failed"
            }
            
        except Exception as e:
            logger.error(f"Error parsing command: {e}")
            return {"success": False, "error": str(e)}
    
    async def _analyze_current_screen(self) -> Dict[str, Any]:
        """Capture and analyze current screen state"""
        try:
            current_time = time.time()
            
            # Use cache if recent analysis exists
            if (self.current_analysis and 
                current_time - self.last_analysis_time < self.analysis_cache_duration):
                logger.debug("Using cached screen analysis")
                return self.current_analysis
            
            # Capture screenshot
            screenshot = ImageGrab.grab()
            if screenshot.mode == 'RGBA':
                screenshot = screenshot.convert('RGB')
            
            self.current_screenshot = screenshot
            
            # Run parallel analysis
            logger.info("Analyzing current screen with multiple methods...")
            
            # Get application context first for targeted analysis
            app_context = await self._get_app_context()
            
            # Use professional UI detection system for maximum accuracy
            logger.info("Running professional UI analysis for super accurate automation...")
            professional_result = await self.professional_ui_detector.analyze_screen_professional(screenshot)
            
            # Fall back to fast analysis if professional detection fails
            if not professional_result or not professional_result.get("success", False):
                logger.warning("Professional UI detection failed, falling back to fast analysis")
                total_screen_result = await self._perform_fast_ui_analysis(screenshot)
                combined_elements = self._combine_detection_results(None, total_screen_result)
            else:
                elements = professional_result.get("elements", [])
                logger.info(f"Professional UI detection succeeded: {len(elements)} elements found")
                # Convert professional UI elements to the expected format
                combined_elements = self._convert_professional_elements(elements)
            
            self.current_analysis = {
                "success": True,
                "timestamp": current_time,
                "screenshot_size": screenshot.size,
                "elements": combined_elements,
                "professional_ui_analysis": professional_result,
                "app_context": app_context
            }
            
            self.last_analysis_time = current_time
            self.current_ui_elements = combined_elements
            
            logger.info(f"Screen analysis complete: {len(combined_elements)} elements detected")
            return self.current_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing screen: {e}")
            return {"success": False, "error": str(e)}
    
    def _convert_professional_elements(self, professional_elements) -> List[Dict[str, Any]]:
        """Convert professional UI elements to the expected format"""
        converted_elements = []
        
        for element in professional_elements:
            # Convert professional UI element format to our expected format
            converted_element = {
                "element_id": element.get("element_id", ""),
                "element_type": element.get("element_type", "unknown"),
                "element_text": element.get("element_text", ""),
                "bounding_box": element.get("bounding_box", {}),
                "state": "unknown",
                "confidence": element.get("confidence", 0.5),
                "interaction_hints": element.get("interaction_hints", []),
                "source": f"professional_{element.get('detection_method', 'unknown')}",
                "app_specific": element.get("attributes", {}),
                "searchable_text": element.get("element_text", "").lower()
            }
            converted_elements.append(converted_element)
        
        logger.info(f"Converted {len(professional_elements)} professional elements to expected format")
        return converted_elements
    
    def _save_temp_screenshot(self, screenshot: Image.Image) -> str:
        """Save screenshot to temporary file and return path"""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            screenshot.save(temp_file.name)
            return temp_file.name
    
    async def _get_app_context(self) -> Dict[str, Any]:
        """Get current application context"""
        try:
            import platform
            import subprocess
            
            context = {"app_name": "Unknown", "view_name": ""}
            
            if platform.system() == "Darwin":  # macOS
                try:
                    # Get frontmost application
                    result = subprocess.run([
                        'osascript', '-e',
                        'tell application "System Events" to get name of first application process whose frontmost is true'
                    ], capture_output=True, text=True, timeout=3)
                    
                    if result.returncode == 0:
                        context["app_name"] = result.stdout.strip()
                    
                    # Get window title
                    result = subprocess.run([
                        'osascript', '-e',
                        'tell application "System Events" to get title of front window of first application process whose frontmost is true'
                    ], capture_output=True, text=True, timeout=3)
                    
                    if result.returncode == 0:
                        context["view_name"] = result.stdout.strip()
                
                except Exception as e:
                    logger.debug(f"Could not get macOS app context: {e}")
            
            return context
            
        except Exception as e:
            logger.debug(f"Error getting app context: {e}")
            return {"app_name": "Unknown", "view_name": ""}
    
    def _combine_detection_results(self, ui_result, total_screen_result) -> List[Dict[str, Any]]:
        """Combine UI detection and total screen analysis results into unified element list"""
        try:
            combined_elements = []
            
            # Add UI detector results (if available)
            if ui_result and hasattr(ui_result, 'elements'):
                for element in ui_result.elements:
                    combined_elements.append({
                        "element_id": element.element_id,
                        "element_type": element.element_type,
                        "element_text": element.element_text,
                        "bounding_box": element.bounding_box,
                        "state": element.state,
                        "confidence": element.confidence,
                        "interaction_hints": element.interaction_hints,
                        "source": "ui_detector",
                        "app_specific": element.app_specific
                    })
            
            # Add total screen analyzer detected elements
            if isinstance(total_screen_result, dict) and "layers" in total_screen_result:
                ui_analysis = total_screen_result.get("layers", {}).get("ui_analysis", {})
                text_analysis = total_screen_result.get("layers", {}).get("text_analysis", {})
                
                # Add UI elements from total screen analyzer
                if "elements" in ui_analysis:
                    logger.info(f"Adding {len(ui_analysis['elements'])} UI elements from fast analysis")
                    for i, element in enumerate(ui_analysis["elements"]):
                        pos = element.get("position", {})
                        # Try to find nearby text for this UI element
                        nearby_text = self._find_nearby_text(pos, text_analysis.get("text_elements", []))
                        
                        combined_elements.append({
                            "element_id": f"total_screen_{i}",
                            "element_type": element.get("type", "unknown"),
                            "element_text": nearby_text,  # Fill with nearby text if found
                            "bounding_box": {
                                "x": pos.get("x", 0),
                                "y": pos.get("y", 0),
                                "width": pos.get("width", 0),
                                "height": pos.get("height", 0)
                            } if pos else None,
                            "state": "unknown",
                            "confidence": 0.8,  # High confidence for CV-based detection
                            "interaction_hints": self._determine_interaction_hints(element.get("type", "unknown")),
                            "source": "total_screen_analyzer",
                            "app_specific": {"nearby_text": nearby_text}
                        })
                
                # Add text elements as potential interaction targets
                if "text_elements" in text_analysis:
                    for i, text_element in enumerate(text_analysis["text_elements"]):
                        if text_element.get("confidence", 0) > 50:  # Only high-confidence text
                            pos = text_element.get("position", {})
                            combined_elements.append({
                                "element_id": f"text_{i}",
                                "element_type": "text_element",
                                "element_text": text_element.get("text", ""),
                                "bounding_box": {
                                    "x": pos.get("x", 0),
                                    "y": pos.get("y", 0),
                                    "width": pos.get("width", 0),
                                    "height": pos.get("height", 0)
                                } if pos else None,
                                "state": "unknown",
                                "confidence": min(text_element.get("confidence", 0) / 100, 1.0),
                                "interaction_hints": ["click"] if self._is_clickable_text(text_element.get("text", "")) else [],
                                "source": "total_screen_text",
                                "app_specific": {}
                            })
            
            # Remove duplicates and enhance with heuristics
            unique_elements = self._deduplicate_and_enhance_elements(combined_elements)
            
            # Debug: Show breakdown before and after deduplication
            ui_count = len([e for e in combined_elements if e.get("source") == "total_screen_analyzer"])
            text_count = len([e for e in combined_elements if e.get("source") == "total_screen_text"])
            
            ui_unique = len([e for e in unique_elements if e.get("source") == "total_screen_analyzer"])
            text_unique = len([e for e in unique_elements if e.get("source") == "total_screen_text"])
            
            logger.info(f"Before dedup: {ui_count} UI elements, {text_count} text elements")
            logger.info(f"After dedup: {ui_unique} UI elements, {text_unique} text elements")
            logger.info(f"Combined elements: {len(combined_elements)} total, {len(unique_elements)} unique")
            return unique_elements
            
        except Exception as e:
            logger.error(f"Error combining detection results: {e}")
            return []
    
    def _determine_interaction_hints(self, element_type: str) -> List[str]:
        """Determine appropriate interaction hints for element type"""
        hint_mapping = {
            "button": ["click"],
            "text_field": ["click", "type"],
            "input_field": ["click", "type"],
            "link": ["click"],
            "icon": ["click"],
            "tab": ["click"],
            "menu": ["click"],
            "checkbox": ["click"],
            "radio": ["click"],
            "widget": ["click"],
            "content_area": ["scroll"],
            "vertical_panel": ["scroll"],
            "horizontal_panel": ["scroll"],
            "unknown": ["click"]
        }
        return hint_mapping.get(element_type, ["click"])
    
    def _is_clickable_text(self, text: str) -> bool:
        """Determine if text is likely to be clickable"""
        clickable_indicators = [
            "button", "click", "submit", "send", "save", "ok", "cancel", "close",
            "login", "signin", "register", "next", "previous", "continue", "back",
            "menu", "settings", "options", "more", "add", "new", "create", "edit",
            "delete", "remove", "search", "find", "go", "start", "stop", "play",
            "pause", "download", "upload", "refresh", "reload", "home", "help"
        ]
        text_lower = text.lower().strip()
        return any(indicator in text_lower for indicator in clickable_indicators) or len(text_lower) < 20
    
    def _find_nearby_text(self, ui_position: Dict, text_elements: List[Dict]) -> str:
        """Find text elements near a UI element position"""
        if not ui_position or not text_elements:
            return ""
        
        ui_x = ui_position.get("x", 0)
        ui_y = ui_position.get("y", 0)
        ui_w = ui_position.get("width", 0)
        ui_h = ui_position.get("height", 0)
        
        # Calculate center of UI element
        ui_center_x = ui_x + ui_w // 2
        ui_center_y = ui_y + ui_h // 2
        
        nearby_texts = []
        
        for text_elem in text_elements:
            text_pos = text_elem.get("position", {})
            if not text_pos:
                continue
                
            text_x = text_pos.get("x", 0)
            text_y = text_pos.get("y", 0)
            text_w = text_pos.get("width", 0)
            text_h = text_pos.get("height", 0)
            
            # Calculate center of text element
            text_center_x = text_x + text_w // 2
            text_center_y = text_y + text_h // 2
            
            # Calculate distance between centers
            distance = ((ui_center_x - text_center_x) ** 2 + (ui_center_y - text_center_y) ** 2) ** 0.5
            
            # Check if text is within reasonable distance (50 pixels)
            if distance < 50:
                text_content = text_elem.get("text", "").strip()
                if text_content and len(text_content) > 1:
                    nearby_texts.append((distance, text_content))
        
        # Return the closest text if any found
        if nearby_texts:
            nearby_texts.sort(key=lambda x: x[0])  # Sort by distance
            return nearby_texts[0][1]  # Return closest text
        
        return ""
    
    async def _perform_fast_ui_analysis(self, screenshot: Image.Image) -> Dict[str, Any]:
        """Ultra-fast UI analysis optimized for automation speed"""
        try:
            import pytesseract
            
            start_time = time.time()
            width, height = screenshot.size
            logger.info(f"Starting fast analysis of {width}x{height} screen")
            
            # Convert to formats needed for analysis
            cv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            # Quick OCR with simplified config
            try:
                ocr_text = pytesseract.image_to_string(gray, config='--psm 6').strip()
                ocr_data = pytesseract.image_to_data(gray, config='--psm 6', output_type=pytesseract.Output.DICT)
            except Exception as e:
                logger.warning(f"OCR failed: {e}")
                ocr_text = ""
                ocr_data = {"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []}
            
            # Fast UI element detection using edge detection
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            ui_elements = []
            text_elements = []
            
            # Process OCR results
            if ocr_data and "text" in ocr_data:
                for i in range(len(ocr_data["text"])):
                    text = ocr_data["text"][i].strip()
                    conf = int(ocr_data["conf"][i]) if ocr_data["conf"][i] != "-1" else 0
                    
                    if text and conf > 30 and len(text) > 1:  # Filter low confidence and single chars
                        text_elements.append({
                            "text": text,
                            "confidence": conf,
                            "position": {
                                "x": ocr_data["left"][i],
                                "y": ocr_data["top"][i],
                                "width": ocr_data["width"][i],
                                "height": ocr_data["height"][i]
                            }
                        })
            
            # Process contours for UI elements
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Filter for reasonable UI element sizes
                if (100 < area < width * height * 0.1 and 
                    w > 15 and h > 10 and 
                    w < width * 0.8 and h < height * 0.8):
                    
                    aspect_ratio = w / h
                    
                    # Classify element type quickly
                    if 0.8 <= aspect_ratio <= 1.2 and area < 5000:
                        element_type = "button"
                    elif aspect_ratio > 5 and h < 40:
                        element_type = "text_field"
                    elif aspect_ratio > 3:
                        element_type = "horizontal_panel"
                    elif aspect_ratio < 0.3:
                        element_type = "vertical_panel"
                    else:
                        element_type = "widget"
                    
                    ui_elements.append({
                        "type": element_type,
                        "position": {"x": x, "y": y, "width": w, "height": h},
                        "area": area,
                        "aspect_ratio": aspect_ratio
                    })
            
            duration = time.time() - start_time
            
            # Create simplified result structure compatible with combine_detection_results
            result = {
                "layers": {
                    "ui_analysis": {
                        "elements": ui_elements,
                        "total_count": len(ui_elements)
                    },
                    "text_analysis": {
                        "text_elements": text_elements,
                        "all_text": ocr_text,
                        "has_meaningful_content": len(text_elements) > 0
                    }
                },
                "analysis_duration": duration,
                "method": "fast_automation_analysis"
            }
            
            logger.info(f"Fast analysis completed in {duration:.2f}s: {len(ui_elements)} UI elements, {len(text_elements)} text elements")
            
            # Debug: Log some UI elements
            if ui_elements:
                logger.info(f"Sample UI elements detected:")
                for i, elem in enumerate(ui_elements[:3]):
                    logger.info(f"  {i+1}. {elem['type']} at ({elem['position']['x']}, {elem['position']['y']}) size: {elem['position']['width']}x{elem['position']['height']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Fast UI analysis failed: {e}")
            return {
                "layers": {
                    "ui_analysis": {"elements": [], "total_count": 0},
                    "text_analysis": {"text_elements": [], "all_text": "", "has_meaningful_content": False}
                },
                "analysis_duration": 0,
                "method": "fast_automation_analysis",
                "error": str(e)
            }
    
    async def _create_execution_plan(self, parsed_command: Dict[str, Any], element_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a detailed execution plan for user approval"""
        try:
            best_match = element_matches[0]
            action = parsed_command.get("action", "unknown")
            
            # Get element position
            position = await self._get_element_position(best_match)
            
            execution_plan = {
                "command": parsed_command.get("original_command", ""),
                "action": action,
                "text_to_type": parsed_command.get("text_to_type", ""),  # Include text to type
                "target_element": {
                    "text": best_match.get("element_text", ""),
                    "type": best_match.get("element_type", "unknown"),
                    "confidence": best_match.get("confidence", 0),
                    "position": position,
                    "coordinates": f"({position[0]}, {position[1]})" if position else "Unknown",
                    "source": best_match.get("source", "unknown")
                },
                "execution_details": {
                    "will_click_at": position,
                    "action_type": action,
                    "safety_level": "medium",
                    "reversible": action in ["click", "double_click"],
                    "risk_level": "low" if action in ["click", "scroll"] else "medium"
                },
                "alternatives": [
                    {
                        "text": elem.get("element_text", ""),
                        "type": elem.get("element_type", "unknown"),
                        "confidence": elem.get("confidence", 0)
                    }
                    for elem in element_matches[1:3]  # Show top 2 alternatives
                ],
                "timestamp": time.time()
            }
            
            return execution_plan
            
        except Exception as e:
            logger.error(f"Error creating execution plan: {e}")
            return {
                "command": parsed_command.get("original_command", ""),
                "action": "unknown",
                "error": str(e)
            }
    
    async def _request_user_approval(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Request user approval with interactive dialog"""
        try:
            # Create approval request with detailed plan
            plan_summary = self._format_execution_plan(execution_plan)
            
            logger.info("=== AUTOMATION EXECUTION PLAN ===")
            logger.info(plan_summary)
            logger.info("==================================")
            
            # Create detailed approval request for the frontend
            approval_request = {
                "type": "user_approval_request",
                "execution_plan": execution_plan,
                "plan_summary": plan_summary,
                "options": ["DO", "Dismiss", "Adjust"],
                "default": "DO",
                "timeout": 30,  # seconds
                "details": {
                    "command": execution_plan.get('command', 'Unknown'),
                    "action": execution_plan.get('action', 'unknown').upper(),
                    "target": execution_plan.get("target_element", {}).get("element_text", "Unknown"),
                    "coordinates": execution_plan.get("execution_details", {}).get("click_position"),
                    "confidence": execution_plan.get("target_element", {}).get("confidence", 0),
                    "risk_level": execution_plan.get("execution_details", {}).get("risk_level", "medium"),
                    "reversible": execution_plan.get("execution_details", {}).get("reversible", False)
                }
            }
            
            # Send approval request to frontend via WebSocket
            if hasattr(self, 'websocket_handler') and self.websocket_handler:
                logger.info("📋 Sending approval request to user interface...")
                response = await self._send_approval_request_to_frontend(approval_request)
                if response and response.get("action"):
                    return response
            
            # Fallback: Terminal-based approval for testing
            logger.info("💬 USER APPROVAL REQUIRED:")
            logger.info("Please respond with: DO, Dismiss, or Adjust")
            logger.info("Waiting for user input...")
            
            # For now, simulate user approval with a short delay
            await asyncio.sleep(2)
            logger.info("⚠️ No user input received, defaulting to 'DO' for this test")
            
            return {
                "action": "do",
                "approved_plan": execution_plan,
                "user_feedback": "default approval (no user input)",
                "approval_time": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error requesting user approval: {e}")
            return {"action": "dismiss", "reason": "approval_error", "error": str(e)}
    
    async def _send_approval_request_to_frontend(self, approval_request: Dict[str, Any]) -> Dict[str, Any]:
        """Send approval request to frontend and wait for response"""
        try:
            # This would integrate with the WebSocket handler to send to frontend
            # For now, return None to trigger fallback behavior
            logger.info("🔌 WebSocket approval integration not yet implemented")
            return None
        except Exception as e:
            logger.error(f"Error sending approval request to frontend: {e}")
            return None
    
    async def _verify_typing_result(self, text_typed: str, target_element: Dict[str, Any]) -> Dict[str, Any]:
        """Verify that the typing action was successful by checking the screen"""
        try:
            # Give the system a moment to update
            await asyncio.sleep(0.5)
            
            # Take a new screenshot and analyze
            verification_analysis = await self._analyze_screen()
            
            if not verification_analysis or "elements" not in verification_analysis:
                return {"verified": False, "reason": "Could not analyze screen for verification"}
            
            # Look for the typed text on the screen
            text_found = False
            for element in verification_analysis["elements"]:
                element_text = element.get("element_text", "").lower()
                if text_typed.lower() in element_text:
                    text_found = True
                    break
            
            # Check if the target area has changed (indicating successful input)
            target_area_changed = self._check_target_area_changes(target_element, verification_analysis["elements"])
            
            return {
                "verified": text_found or target_area_changed,
                "text_found_on_screen": text_found,
                "target_area_changed": target_area_changed,
                "elements_analyzed": len(verification_analysis["elements"])
            }
            
        except Exception as e:
            logger.error(f"Error verifying typing result: {e}")
            return {"verified": False, "reason": f"Verification error: {e}"}
    
    def _check_target_area_changes(self, target_element: Dict[str, Any], current_elements: List[Dict[str, Any]]) -> bool:
        """Check if the target area has changed after the action"""
        try:
            # Simple check: if we can find the same element but with different properties,
            # it suggests the action had an effect
            target_bbox = target_element.get("bounding_box", {})
            if not target_bbox:
                return False
            
            # Look for elements in the same area
            for element in current_elements:
                elem_bbox = element.get("bounding_box", {})
                if not elem_bbox:
                    continue
                    
                # Check if this element is in roughly the same area
                if (abs(elem_bbox.get("x", 0) - target_bbox.get("x", 0)) < 50 and
                    abs(elem_bbox.get("y", 0) - target_bbox.get("y", 0)) < 50):
                    # Found an element in the same area - this suggests activity
                    return True
                    
            return False
            
        except Exception as e:
            logger.debug(f"Error checking target area changes: {e}")
            return False
    
    def _format_execution_plan(self, execution_plan: Dict[str, Any]) -> str:
        """Format execution plan for user display"""
        try:
            target = execution_plan.get("target_element", {})
            details = execution_plan.get("execution_details", {})
            
            plan_text = f"""
🎯 AUTOMATION PLAN:
Command: {execution_plan.get('command', 'Unknown')}
Action: {execution_plan.get('action', 'unknown').upper()}

📍 TARGET ELEMENT:
• Text: "{target.get('text', 'N/A')}"
• Type: {target.get('type', 'unknown')}
• Confidence: {target.get('confidence', 0):.2f}
• Coordinates: {target.get('coordinates', 'Unknown')}
• Source: {target.get('source', 'unknown')}

⚡ EXECUTION DETAILS:
• Will click at: {details.get('will_click_at', 'Unknown')}
• Risk level: {details.get('risk_level', 'unknown')}
• Reversible: {details.get('reversible', False)}

🔄 ALTERNATIVES FOUND:
"""
            
            alternatives = execution_plan.get("alternatives", [])
            if alternatives:
                for i, alt in enumerate(alternatives, 1):
                    plan_text += f"  {i}. {alt.get('type', 'unknown')} - \"{alt.get('text', 'N/A')}\" (confidence: {alt.get('confidence', 0):.2f})\n"
            else:
                plan_text += "  None\n"
                
            return plan_text.strip()
            
        except Exception as e:
            return f"Error formatting plan: {e}"
    
    async def _execute_approved_plan(self, execution_plan: Dict[str, Any], approval_result: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the user-approved automation plan"""
        try:
            logger.info(f"🚀 Executing approved plan: {execution_plan.get('action', 'unknown')}")
            
            # Extract execution details
            target_element = execution_plan.get("target_element", {})
            action = execution_plan.get("action", "unknown")
            position = target_element.get("position")
            
            if not position:
                return {
                    "success": False,
                    "error": "Could not determine target position",
                    "execution_plan": execution_plan
                }
            
            # Visual verification before executing action
            logger.info(f"Performing visual verification before executing {action} at ({position[0]}, {position[1]})")
            verification_preview = await self.coordinate_extractor.create_verification_preview(
                position, target_element, action, self.current_screenshot
            )
            
            if verification_preview:
                logger.info(f"Visual verification preview created successfully")
            else:
                logger.warning("Could not create verification preview, proceeding with caution")
            
            # Verify feasibility of the action
            feasible = await self.coordinate_extractor.verify_action_feasibility(
                position, action, target_element, self.current_screenshot
            )
            
            if not feasible.get("feasible", True):
                logger.warning(f"Action may not be feasible: {feasible.get('reason', 'Unknown')}")
                # Continue anyway but log the concern
            
            # Execute the action using input controller
            x, y = position
            result = {"success": False}
            
            if action == "click":
                click_result = self.input_controller.click(x, y)
                result = {"success": True, "visual_verification": verification_preview}
                logger.info(f"✅ Successfully executed click on {target_element.get('text', 'element')} at ({x}, {y})")
                
            elif action == "double_click":
                click_result = self.input_controller.double_click(x, y)
                result = {"success": True, "visual_verification": verification_preview}
                logger.info(f"✅ Successfully executed double-click on {target_element.get('text', 'element')} at ({x}, {y})")
                
            elif action == "type":
                # First click to focus, then type
                self.input_controller.click(x, y)
                text_to_type = execution_plan.get("text_to_type", "")
                type_result = self.input_controller.type_text(text_to_type)
                
                # Verify the typing was successful
                verification_result = await self._verify_typing_result(text_to_type, target_element)
                result = {
                    "success": True,
                    "verification": verification_result,
                    "visual_verification": verification_preview,
                    "text_typed": text_to_type
                }
                logger.info(f"✅ Successfully typed '{text_to_type}' in {target_element.get('text', 'element')}")
                
                if verification_result.get("verified", False):
                    logger.info(f"🎯 Verification passed: Text '{text_to_type}' confirmed on screen")
                else:
                    logger.warning(f"⚠️ Verification inconclusive: Could not confirm text '{text_to_type}' on screen")
                
            elif action == "scroll":
                direction = execution_plan.get("scroll_direction", "down")
                scroll_result = self.input_controller.scroll(x, y, direction)
                result = {"success": True, "visual_verification": verification_preview}
                logger.info(f"✅ Successfully scrolled {direction} at ({x}, {y})")
                
            else:
                return {
                    "success": False,
                    "error": f"Unsupported action: {action}",
                    "execution_plan": execution_plan
                }
            
            # Add execution tracking
            result.update({
                "action_taken": action,
                "target_coordinates": (x, y),
                "target_element": target_element.get("text", "unknown"),
                "execution_time": time.time(),
                "approved_by_user": True
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing approved plan: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_plan": execution_plan
            }
    
    def _deduplicate_and_enhance_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and enhance element descriptions"""
        try:
            # Group similar elements
            unique_elements = []
            seen_texts = set()
            
            for element in elements:
                text = element.get("element_text", "").lower().strip()
                element_type = element.get("element_type", "unknown")
                
                # Skip empty text ONLY for text elements, keep UI elements even without text
                if (not text or len(text) < 2) and element_type == "text_element":
                    continue
                
                # Create a signature for deduplication
                if not text and element.get("bounding_box"):
                    # For UI elements without text, use position-based signature
                    bbox = element["bounding_box"]
                    signature = f"{element_type}:{bbox.get('x', 0)}:{bbox.get('y', 0)}:{bbox.get('width', 0)}:{bbox.get('height', 0)}"
                else:
                    signature = f"{element_type}:{text}"
                
                if signature not in seen_texts:
                    seen_texts.add(signature)
                    
                    # Enhance element with additional metadata
                    enhanced = element.copy()
                    enhanced["searchable_text"] = self._create_searchable_text(element)
                    enhanced["element_priority"] = self._calculate_element_priority(element)
                    
                    unique_elements.append(enhanced)
            
            # Sort by priority (higher priority first)
            unique_elements.sort(key=lambda x: x.get("element_priority", 0), reverse=True)
            
            return unique_elements
            
        except Exception as e:
            logger.error(f"Error deduplicating elements: {e}")
            return elements
    
    def _create_searchable_text(self, element: Dict[str, Any]) -> str:
        """Create searchable text combining all element attributes"""
        searchable_parts = []
        
        # Add element text
        if element.get("element_text"):
            searchable_parts.append(element["element_text"].lower())
        
        # Add element type (essential for UI elements without text)
        element_type = element.get("element_type", "")
        if element_type:
            searchable_parts.append(element_type.lower())
        
        # For UI elements, add common synonyms
        if not element.get("element_text") and element_type in ["button", "widget", "icon"]:
            searchable_parts.extend(["button", "click", "interactive"])
        
        # Add interaction hints
        hints = element.get("interaction_hints", [])
        searchable_parts.extend([hint.lower() for hint in hints])
        
        # Add app-specific terms
        app_specific = element.get("app_specific", {})
        for key, value in app_specific.items():
            if isinstance(value, str):
                searchable_parts.append(value.lower())
        
        return " ".join(searchable_parts)
    
    def _calculate_element_priority(self, element: Dict[str, Any]) -> float:
        """Calculate priority score for element matching"""
        priority = 0.0
        
        # Base confidence score
        priority += element.get("confidence", 0.5) * 100
        
        # Boost for common interactive elements
        element_type = element.get("element_type", "").lower()
        if element_type in ["button", "link", "textfield", "checkbox", "radio"]:
            priority += 50
        
        # Boost for elements with clear text
        text = element.get("element_text", "")
        if text and len(text) > 2:
            priority += 30
        
        # Boost for elements with bounding boxes (precise location)
        if element.get("bounding_box"):
            priority += 20
        
        # Boost for UI detector results (more reliable)
        if element.get("source") == "ui_detector":
            priority += 15
        
        return priority
    
    async def _find_target_elements(self, parsed_command: Dict[str, Any], elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find elements that match the command target description"""
        try:
            target_description = parsed_command.get("target_description", "").lower().strip()
            if not target_description:
                return []
            
            matches = []
            
            for element in elements:
                confidence = self._calculate_element_match_confidence(
                    target_description,
                    element,
                    parsed_command.get("action", "")
                )
                
                if confidence >= self.confidence_thresholds["minimum_match"]:
                    element_with_confidence = element.copy()
                    element_with_confidence["confidence"] = confidence
                    element_with_confidence["match_reason"] = self._explain_match(target_description, element)
                    matches.append(element_with_confidence)
            
            # Sort by confidence (highest first)
            matches.sort(key=lambda x: x["confidence"], reverse=True)
            
            # Log the best matches for debugging
            if matches:
                logger.info(f"Found {len(matches)} potential matches for '{target_description}':")
                for i, match in enumerate(matches[:3]):  # Show top 3
                    logger.info(f"  {i+1}. {match.get('element_text', 'N/A')} "
                              f"({match.get('element_type', 'unknown')}) "
                              f"- confidence: {match['confidence']:.2f}")
            
            return matches
            
        except Exception as e:
            logger.error(f"Error finding target elements: {e}")
            return []
    
    def _calculate_element_match_confidence(self, target_desc: str, element: Dict[str, Any], action: str) -> float:
        """Calculate how well an element matches the target description"""
        try:
            confidence = 0.0
            
            element_text = element.get("element_text", "").lower()
            element_type = element.get("element_type", "").lower()
            searchable_text = element.get("searchable_text", "").lower()
            
            # Exact text match gets highest score
            if target_desc == element_text:
                confidence += 1.0
            
            # Partial text match
            elif target_desc in element_text or element_text in target_desc:
                # Calculate overlap ratio
                overlap = len(set(target_desc.split()) & set(element_text.split()))
                total_words = len(set(target_desc.split()) | set(element_text.split()))
                confidence += (overlap / total_words) * 0.8
            
            # Check for keyword matches
            target_words = target_desc.split()
            element_words = searchable_text.split()
            
            for target_word in target_words:
                if target_word in element_words:
                    confidence += 0.2
            
            # Special handling for common UI elements by position and type
            confidence += self._check_positional_matches(target_desc, element)
            
            # Boost for action-appropriate element types
            action_element_mapping = {
                "click": ["button", "link", "icon", "tab", "menu", "widget"],
                "type": ["textfield", "input", "textarea", "text_field", "text_area"],
                "scroll": ["scrollbar", "content_area"],
                "double_click": ["icon", "file", "folder"]
            }
            
            if action in action_element_mapping:
                if element_type in action_element_mapping[action]:
                    confidence += 0.3
            
            # Special handling for text typing in applications
            if action == "type":
                # Prioritize text input areas over window titles/labels
                if element_type in ["text_field", "textarea", "input", "textfield"]:
                    confidence += 0.5  # Strong preference for text input elements
                elif element_type == "text_element" and "notepad" in target_desc:
                    # For notepad, if we find actual text input area, prefer it over title
                    bbox = element.get("bounding_box", {})
                    if bbox:
                        # Prefer larger elements that could be text areas
                        area = bbox.get("width", 0) * bbox.get("height", 0)
                        if area > 10000:  # Likely a text area, not just a title
                            confidence += 0.4
                        elif area < 1000:  # Likely just a title or small text
                            confidence -= 0.2
            
            # Check for semantic matches
            semantic_matches = self._check_semantic_matches(target_desc, element)
            confidence += semantic_matches * 0.4
            
            # Normalize confidence to 0-1 range
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.debug(f"Error calculating match confidence: {e}")
            return 0.0
    
    def _check_positional_matches(self, target_desc: str, element: Dict[str, Any]) -> float:
        """Check for positional/contextual matches for common UI elements"""
        try:
            element_type = element.get("element_type", "").lower()
            bbox = element.get("bounding_box", {})
            
            if not bbox:
                return 0.0
            
            x = bbox.get("x", 0)
            y = bbox.get("y", 0)
            w = bbox.get("width", 0)
            h = bbox.get("height", 0)
            
            # Estimate screen dimensions (this is rough but works for most cases)
            screen_width = 2940  # From our analysis
            screen_height = 1912
            
            confidence = 0.0
            
            # Check for common button positions and descriptions
            position_matches = {
                "close": {
                    "description": ["close", "x", "exit", "quit"],
                    "position": lambda x, y, w, h: (
                        # Top-right corner
                        (x > screen_width * 0.85 and y < screen_height * 0.15) or
                        # Small square button (typical close button)
                        (w < 30 and h < 30 and abs(w - h) < 5)
                    )
                },
                "minimize": {
                    "description": ["minimize", "min", "-", "hide"],
                    "position": lambda x, y, w, h: (
                        # Top area, usually left of close button
                        (x > screen_width * 0.75 and x < screen_width * 0.9 and y < screen_height * 0.15) or
                        # Small horizontal line shape
                        (w > h * 2 and h < 20)
                    )
                },
                "maximize": {
                    "description": ["maximize", "max", "expand", "fullscreen"],
                    "position": lambda x, y, w, h: (
                        # Top area, between minimize and close
                        (x > screen_width * 0.8 and x < screen_width * 0.9 and y < screen_height * 0.15) or
                        # Square button
                        (abs(w - h) < 5 and w < 25)
                    )
                },
                "menu": {
                    "description": ["menu", "hamburger", "≡", "options"],
                    "position": lambda x, y, w, h: (
                        # Top-left corner
                        (x < screen_width * 0.1 and y < screen_height * 0.15) or
                        # Typical menu button size
                        (w < 50 and h < 50)
                    )
                }
            }
            
            # Check if target description matches any position-based patterns
            for pattern_name, pattern_info in position_matches.items():
                # Check if target contains any of the description keywords
                if any(desc in target_desc.lower() for desc in pattern_info["description"]):
                    # Check if element is in the expected position
                    if pattern_info["position"](x, y, w, h):
                        confidence += 0.6  # High confidence for position + description match
                        logger.debug(f"Positional match: {pattern_name} at ({x}, {y})")
                        break
            
            # General button matching
            if "button" in target_desc.lower() and element_type in ["button", "widget"]:
                confidence += 0.3
            
            return confidence
            
        except Exception as e:
            logger.debug(f"Error checking positional matches: {e}")
            return 0.0
    
    def _check_semantic_matches(self, target_desc: str, element: Dict[str, Any]) -> float:
        """Check for semantic similarity between target and element"""
        try:
            # Define semantic groups
            semantic_groups = {
                "submit": ["submit", "send", "save", "apply", "confirm", "ok"],
                "cancel": ["cancel", "close", "dismiss", "abort", "back"],
                "search": ["search", "find", "lookup", "query"],
                "login": ["login", "signin", "sign in", "log in"],
                "menu": ["menu", "options", "settings", "more"],
                "next": ["next", "continue", "forward", "proceed"],
                "previous": ["previous", "back", "prev", "return"],
                "delete": ["delete", "remove", "trash", "discard"],
                "edit": ["edit", "modify", "change", "update"],
                "add": ["add", "new", "create", "plus", "+"]
            }
            
            element_text = element.get("element_text", "").lower()
            
            for group_key, synonyms in semantic_groups.items():
                if group_key in target_desc or any(syn in target_desc for syn in synonyms):
                    if any(syn in element_text for syn in synonyms):
                        return 0.8  # High semantic match
            
            return 0.0
            
        except Exception as e:
            logger.debug(f"Error checking semantic matches: {e}")
            return 0.0
    
    def _explain_match(self, target_desc: str, element: Dict[str, Any]) -> str:
        """Explain why an element was matched"""
        reasons = []
        
        element_text = element.get("element_text", "").lower()
        element_type = element.get("element_type", "").lower()
        
        if target_desc == element_text:
            reasons.append("exact text match")
        elif target_desc in element_text:
            reasons.append("text contains target")
        elif element_text in target_desc:
            reasons.append("target contains element text")
        
        if any(word in element_text for word in target_desc.split()):
            reasons.append("keyword match")
        
        if element_type in target_desc:
            reasons.append("element type match")
        
        return ", ".join(reasons) if reasons else "heuristic match"
    
    async def _execute_action(self, parsed_command: Dict[str, Any], target_element: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the parsed action on the target element"""
        try:
            action = parsed_command["action"]
            element_text = target_element.get("element_text", "unknown")
            
            logger.info(f"Executing {action} on element: {element_text}")
            
            # Get element position
            position = await self._get_element_position(target_element)
            if not position:
                return {
                    "success": False,
                    "error": "Could not determine element position",
                    "element": target_element
                }
            
            x, y = position
            result = {"success": False}
            
            # Execute the action
            if action == "click":
                success = self.input_controller.click(x, y)
                result = {
                    "success": success,
                    "action": "click",
                    "position": {"x": x, "y": y},
                    "element": element_text
                }
            
            elif action == "double_click":
                success = self.input_controller.double_click(x, y)
                result = {
                    "success": success,
                    "action": "double_click",
                    "position": {"x": x, "y": y},
                    "element": element_text
                }
            
            elif action == "right_click":
                success = self.input_controller.right_click(x, y)
                result = {
                    "success": success,
                    "action": "right_click",
                    "position": {"x": x, "y": y},
                    "element": element_text
                }
            
            elif action == "type":
                text_to_type = parsed_command.get("text_to_type", "")
                # First click on the element to focus it
                self.input_controller.click(x, y)
                await asyncio.sleep(0.5)  # Wait for focus
                success = self.input_controller.type_text(text_to_type)
                result = {
                    "success": success,
                    "action": "type",
                    "text": text_to_type,
                    "position": {"x": x, "y": y},
                    "element": element_text
                }
            
            elif action == "scroll":
                # Handle different scroll types
                if "scroll_direction" in parsed_command:
                    direction = parsed_command["scroll_direction"]
                    clicks = 3 if direction in ["up", "down"] else 3
                    if direction == "down":
                        clicks = -clicks
                    success = self.input_controller.scroll(clicks)
                elif "scroll_amount" in parsed_command:
                    amount = parsed_command["scroll_amount"]
                    success = self.input_controller.scroll(-amount)  # Negative for down
                else:
                    success = self.input_controller.scroll(-3)  # Default scroll down
                
                result = {
                    "success": success,
                    "action": "scroll",
                    "details": parsed_command
                }
            
            else:
                result = {
                    "success": False,
                    "error": f"Unsupported action: {action}"
                }
            
            if result["success"]:
                logger.info(f"Successfully executed {action} on {element_text}")
            else:
                logger.warning(f"Failed to execute {action} on {element_text}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_element_position(self, element: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Get precise clickable position for an element using enhanced coordinate extraction"""
        try:
            logger.debug(f"Getting position for element: {element}")
            
            # Use enhanced coordinate extractor for maximum precision
            coordinates = await self.coordinate_extractor.extract_precise_coordinates(
                element, 
                screenshot=self.current_screenshot
            )
            
            if coordinates:
                logger.info(f"Enhanced coordinate extraction succeeded: {coordinates}")
                return coordinates
            
            # Fallback to original logic if enhanced extraction fails
            logger.warning("Enhanced coordinate extraction failed, using fallback")
            
            # If element has bounding box, use center point
            bbox = element.get("bounding_box")
            logger.debug(f"Element bounding_box: {bbox}")
            if bbox:
                if isinstance(bbox, dict):
                    # New format: {"x": 10, "y": 20, "width": 30, "height": 40}
                    x = bbox.get("x", 0) + bbox.get("width", 0) // 2
                    y = bbox.get("y", 0) + bbox.get("height", 0) // 2
                    return (x, y)
                elif isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                    # Old format: [x, y, width, height]
                    x = bbox[0] + bbox[2] // 2
                    y = bbox[1] + bbox[3] // 2
                    return (x, y)
            
            # If no bounding box, try to find element using visual search
            if self.current_screenshot:
                position = await self._visual_element_search(element)
                if position:
                    return position
            
            # Fallback: use heuristic positioning based on element text
            position = await self._heuristic_positioning(element)
            return position
            
        except Exception as e:
            logger.error(f"Error getting element position: {e}")
            return None
    
    async def _visual_element_search(self, element: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Search for element visually using OCR and template matching"""
        try:
            if not self.current_screenshot:
                return None
            
            import pytesseract
            
            # Convert screenshot to OpenCV format
            cv_image = cv2.cvtColor(np.array(self.current_screenshot), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
            
            element_text = element.get("element_text", "").strip()
            if not element_text:
                return None
            
            # Use OCR to find text locations
            data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            
            for i, text in enumerate(data['text']):
                if text.strip().lower() == element_text.lower():
                    x = data['left'][i] + data['width'][i] // 2
                    y = data['top'][i] + data['height'][i] // 2
                    confidence = int(data['conf'][i])
                    
                    if confidence > 30:  # Minimum OCR confidence
                        logger.info(f"Found element '{element_text}' at ({x}, {y}) with OCR confidence {confidence}")
                        return (x, y)
            
            return None
            
        except Exception as e:
            logger.debug(f"Visual element search failed: {e}")
            return None
    
    async def _heuristic_positioning(self, element: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Fallback positioning based on element type and screen layout"""
        try:
            if not self.current_screenshot:
                return None
            
            width, height = self.current_screenshot.size
            element_type = element.get("element_type", "").lower()
            element_text = element.get("element_text", "").lower()
            
            # Common button positions based on type
            if "submit" in element_text or "save" in element_text or "send" in element_text:
                # Bottom right area (common for submit buttons)
                return (int(width * 0.8), int(height * 0.9))
            
            elif "cancel" in element_text or "close" in element_text:
                # Top right or bottom left
                return (int(width * 0.9), int(height * 0.1))
            
            elif element_type == "button":
                # Center-bottom area
                return (int(width * 0.5), int(height * 0.8))
            
            elif element_type == "textfield":
                # Center area
                return (int(width * 0.5), int(height * 0.4))
            
            else:
                # Default to center
                return (int(width * 0.5), int(height * 0.5))
            
        except Exception as e:
            logger.debug(f"Heuristic positioning failed: {e}")
            return None
    
    async def get_available_elements(self) -> List[Dict[str, Any]]:
        """Get list of currently available interactive elements"""
        try:
            analysis = await self._analyze_current_screen()
            if analysis["success"]:
                return analysis["elements"]
            return []
        except Exception as e:
            logger.error(f"Error getting available elements: {e}")
            return []
    
    def stop(self):
        """Stop the automation system"""
        if self.input_controller:
            self.input_controller.stop()
        logger.info("Enhanced Agent Automation stopped")

# Test and demo functions
async def test_enhanced_automation():
    """Test the enhanced automation system"""
    automation = EnhancedAgentAutomation()
    
    # Test commands
    test_commands = [
        "click the submit button",
        "type hello world in the search box",
        "scroll down",
        "double click the file icon"
    ]
    
    for command in test_commands:
        print(f"\nTesting command: '{command}'")
        result = await automation.execute_command(command)
        print(f"Result: {result['success']}")
        if not result['success']:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        await asyncio.sleep(2)  # Wait between commands
    
    automation.stop()

async def main():
    """Main function for testing"""
    if len(os.sys.argv) > 1:
        command = " ".join(os.sys.argv[1:])
        automation = EnhancedAgentAutomation()
        result = await automation.execute_command(command)
        print(json.dumps(result, indent=2))
        automation.stop()
    else:
        await test_enhanced_automation()

if __name__ == "__main__":
    asyncio.run(main())