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
from llava_visual_processor import LLaVAVisualProcessor

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
    
    def __init__(self, llava_url="http://localhost:11434"):
        self.input_controller = InputController(safety_level="medium")
        self.ui_detector = UIElementDetector(llava_url=llava_url)
        self.llava_processor = LLaVAVisualProcessor(llava_url)
        
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
        
        logger.info("Enhanced Agent Automation initialized")
    
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
                    r"type (.+?) in (?:the )?(.+?)(?:\s|$)",
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
    
    async def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute a natural language command by understanding intent and finding target elements.
        
        Args:
            command: Natural language command like "click the submit button"
            
        Returns:
            Dict with execution results and details
        """
        try:
            logger.info(f"Executing command: '{command}'")
            
            # Parse the command to understand intent
            parsed_command = await self._parse_command(command)
            if not parsed_command["success"]:
                return {
                    "success": False,
                    "error": "Could not understand command",
                    "details": parsed_command
                }
            
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
                                         for elem in analysis_result["elements"][:10]]
                }
            
            # Execute the action on the best matching element
            execution_result = await self._execute_action(
                parsed_command,
                element_matches[0]  # Use best match
            )
            
            return {
                "success": execution_result["success"],
                "action": parsed_command["action"],
                "target_element": element_matches[0],
                "execution_details": execution_result,
                "confidence": element_matches[0]["confidence"],
                "command_understood": parsed_command
            }
            
        except Exception as e:
            logger.error(f"Error executing command '{command}': {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def _parse_command(self, command: str) -> Dict[str, Any]:
        """Parse natural language command to extract action and target"""
        try:
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
                            "pattern_matched": pattern
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
                        
                        return parsed
            
            return {
                "success": False,
                "error": "No matching command pattern found",
                "command": command
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
            
            # Run UI detection and LLaVA analysis in parallel
            ui_task = self.ui_detector.detect_ui_elements(
                self._save_temp_screenshot(screenshot),
                app_context
            )
            
            llava_task = self.llava_processor.analyze_screen(screenshot)
            
            ui_result, llava_result = await asyncio.gather(ui_task, llava_task)
            
            # Combine and enhance results
            combined_elements = self._combine_detection_results(ui_result, llava_result)
            
            self.current_analysis = {
                "success": True,
                "timestamp": current_time,
                "screenshot_size": screenshot.size,
                "elements": combined_elements,
                "ui_analysis": ui_result,
                "llava_analysis": llava_result,
                "app_context": app_context
            }
            
            self.last_analysis_time = current_time
            self.current_ui_elements = combined_elements
            
            logger.info(f"Screen analysis complete: {len(combined_elements)} elements detected")
            return self.current_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing screen: {e}")
            return {"success": False, "error": str(e)}
    
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
    
    def _combine_detection_results(self, ui_result, llava_result) -> List[Dict[str, Any]]:
        """Combine UI detection and LLaVA results into unified element list"""
        try:
            combined_elements = []
            
            # Add UI detector results
            if hasattr(ui_result, 'elements'):
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
            
            # Add LLaVA detected elements
            if isinstance(llava_result, dict) and "ui_elements" in llava_result:
                for element in llava_result["ui_elements"]:
                    combined_elements.append({
                        "element_id": f"llava_{len(combined_elements)}",
                        "element_type": element.get("type", "unknown"),
                        "element_text": element.get("name", element.get("element", "")),
                        "bounding_box": None,  # LLaVA doesn't provide exact coordinates
                        "state": "unknown",
                        "confidence": 0.7,  # Default confidence for LLaVA elements
                        "interaction_hints": ["click"],
                        "source": "llava",
                        "app_specific": {}
                    })
            
            # Remove duplicates and enhance with heuristics
            unique_elements = self._deduplicate_and_enhance_elements(combined_elements)
            
            return unique_elements
            
        except Exception as e:
            logger.error(f"Error combining detection results: {e}")
            return []
    
    def _deduplicate_and_enhance_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates and enhance element descriptions"""
        try:
            # Group similar elements
            unique_elements = []
            seen_texts = set()
            
            for element in elements:
                text = element.get("element_text", "").lower().strip()
                element_type = element.get("element_type", "unknown")
                
                # Skip empty or very short texts
                if not text or len(text) < 2:
                    continue
                
                # Create a signature for deduplication
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
        
        # Add element type
        element_type = element.get("element_type", "")
        if element_type:
            searchable_parts.append(element_type.lower())
        
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
            
            # Boost for action-appropriate element types
            action_element_mapping = {
                "click": ["button", "link", "icon", "tab", "menu"],
                "type": ["textfield", "input", "textarea"],
                "scroll": ["scrollbar", "content_area"],
                "double_click": ["icon", "file", "folder"]
            }
            
            if action in action_element_mapping:
                if element_type in action_element_mapping[action]:
                    confidence += 0.3
            
            # Check for semantic matches
            semantic_matches = self._check_semantic_matches(target_desc, element)
            confidence += semantic_matches * 0.4
            
            # Normalize confidence to 0-1 range
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.debug(f"Error calculating match confidence: {e}")
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
        """Get clickable position for an element"""
        try:
            # If element has bounding box, use center point
            bbox = element.get("bounding_box")
            if bbox and len(bbox) >= 4:
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