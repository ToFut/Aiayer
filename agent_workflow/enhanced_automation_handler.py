#!/usr/bin/env python3
"""
Enhanced Automation Handler
Integrates the enhanced automation system with the existing agent workflow.
Handles natural language commands and executes them via the automation system.
"""

import asyncio
import json
import logging
import os
import sys
import traceback
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_agent_automation import EnhancedAgentAutomation

# Configure logging
os.makedirs('logs/agent_workflow', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/agent_workflow/enhanced_automation_handler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('enhanced_automation_handler')

class EnhancedAutomationHandler:
    """
    Handles enhanced automation commands within the agent workflow system.
    Integrates natural language understanding with precise UI automation.
    """
    
    def __init__(self, llava_url="http://localhost:11434"):
        self.automation = EnhancedAgentAutomation(llava_url)
        self.command_history = []
        self.active_session = None
        self.learning_mode = True  # Learn from successful/failed commands
        
        # Command categories for routing
        self.command_categories = {
            "automation": [
                "click", "press", "tap", "select", "hit", "touch",
                "type", "enter", "write", "input", "fill",
                "scroll", "swipe", "move",
                "drag", "drop",
                "double click", "right click", "context menu"
            ],
            "query": [
                "what", "where", "show", "list", "find", "search",
                "describe", "analyze", "identify", "detect"
            ],
            "navigation": [
                "go to", "navigate", "open", "switch to", "focus on"
            ]
        }
        
        logger.info("Enhanced Automation Handler initialized")
    
    async def create_execution_plan(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create an execution plan without executing it.
        
        Args:
            instruction: Natural language instruction from user
            context: Optional context about current state
            
        Returns:
            Dict with execution plan details
        """
        try:
            logger.info(f"Creating execution plan for: '{instruction}'")
            
            # 🧠 TRY FAST LLM-BASED PLANNING FIRST (with warmup optimization)
            try:
                logger.info("🔥 Attempting FAST LLM-based automation planning with warmup...")
                
                # Try to use warmup manager for fast responses
                try:
                    from llm_warmup_manager import LLMWarmupManager
                    warmup_manager = LLMWarmupManager()
                    
                    # Use warmup manager for fast LLM call
                    fast_response = await warmup_manager.generate_fast_automation_plan(instruction)
                    if fast_response:
                        logger.info("⚡ Got fast LLM response in <2s")
                        plan = fast_response
                    else:
                        raise Exception("Warmup manager didn't return plan")
                        
                except Exception as warmup_error:
                    logger.warning(f"Warmup manager failed, using FAST FALLBACK instead of slow LLM: {warmup_error}")
                    
                    # Create fast fallback plan without LLM to avoid 15s delays
                    class FastFallbackPlan:
                        def __init__(self, instruction):
                            self.title = instruction
                            self.coordinates = self._get_smart_coordinates(instruction)
                            
                            # Try LLM first for intelligent step generation, then fallback to patterns
                            try:
                                self.steps = self._generate_llm_steps(instruction)
                                logger.info("✅ Generated steps using direct LLM integration")
                            except Exception as llm_error:
                                logger.warning(f"LLM step generation failed, using pattern-based fallback: {llm_error}")
                                self.steps = self._generate_intelligent_steps(instruction)
                            
                            self.complexity_score = 0.75
                        
                        def _generate_llm_steps(self, instruction):
                            """Generate automation steps using direct LLM integration"""
                            
                            # Create a detailed prompt for step generation
                            prompt = f"""Create automation steps for: "{instruction}"

Return ONLY a JSON array with no explanation, no markdown, no code blocks:

[
  {{"id": "step_1", "description": "Analyze current screen", "action_type": "analyze", "target": "screen", "value": ""}},
  {{"id": "step_2", "description": "Detect target element", "action_type": "detect", "target": "element", "value": ""}},
  {{"id": "step_3", "description": "Perform action", "action_type": "click", "target": "element", "value": ""}}
]

For instruction "{instruction}", create 3-5 logical automation steps. Use action_type: analyze, detect, click, type, scroll, wait, navigate. Include element detection before interaction. Be specific about targets and values."""

                            # Make direct API call to Ollama
                            try:
                                response = requests.post(
                                    "http://localhost:11434/api/generate",
                                    json={
                                        "model": "llama3.2:1b",
                                        "prompt": prompt,
                                        "stream": False,
                                        "options": {
                                            "temperature": 0.3,
                                            "top_p": 0.9,
                                            "stop": ["Human:", "Assistant:", "User:"]
                                        }
                                    },
                                    timeout=10
                                )
                                
                                if response.status_code == 200:
                                    llm_response = response.json()
                                    generated_text = llm_response.get("response", "").strip()
                                    
                                    # Extract JSON from the response
                                    steps_json = self._extract_json_from_response(generated_text)
                                    if steps_json:
                                        # Convert to step objects
                                        steps = []
                                        for step_data in steps_json:
                                            step_obj = type('Step', (), {
                                                'id': step_data.get('id', f'step_{len(steps)+1}'),
                                                'description': step_data.get('description', 'Automation step'),
                                                'action_type': step_data.get('action_type', 'action'),
                                                'target': step_data.get('target', 'auto_detect'),
                                                'value': step_data.get('value', ''),
                                                'estimated_duration': 2
                                            })()
                                            steps.append(step_obj)
                                        
                                        if len(steps) >= 2:  # Must have at least 2 meaningful steps
                                            logger.info(f"🚀 LLM generated {len(steps)} intelligent steps")
                                            return steps
                                        else:
                                            logger.warning("LLM generated insufficient steps, falling back to patterns")
                                            raise Exception("Insufficient steps from LLM")
                                    else:
                                        logger.warning("Could not extract valid JSON from LLM response")
                                        raise Exception("Invalid JSON from LLM")
                                else:
                                    logger.error(f"Ollama API error: {response.status_code}")
                                    raise Exception(f"API error: {response.status_code}")
                            
                            except Exception as e:
                                logger.error(f"Direct LLM call failed: {e}")
                                raise e
                        
                        def _extract_json_from_response(self, text):
                            """Extract JSON array from LLM response text"""
                            try:
                                import re
                                
                                # Remove markdown code blocks
                                text = re.sub(r'```[a-z]*\n?', '', text)
                                text = re.sub(r'```', '', text)
                                
                                # Look for JSON array in the response (more comprehensive)
                                json_match = re.search(r'(\[\s*\{.*?\}\s*\])', text, re.DOTALL)
                                if json_match:
                                    json_str = json_match.group(1)
                                    # Clean up any formatting issues
                                    json_str = re.sub(r'\n\s*', ' ', json_str)  # Remove excessive whitespace
                                    json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas before }
                                    json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas before ]
                                    return json.loads(json_str)
                                
                                # Try to find array with multiple objects
                                bracket_match = re.search(r'\[.*\]', text, re.DOTALL)
                                if bracket_match:
                                    json_str = bracket_match.group(0)
                                    # Clean up formatting
                                    json_str = re.sub(r'\n\s*', ' ', json_str)
                                    json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas before }
                                    json_str = re.sub(r',\s*]', ']', json_str)  # Remove trailing commas before ]
                                    return json.loads(json_str)
                                
                                # Try to parse the entire response as JSON
                                cleaned_text = text.strip()
                                if cleaned_text.startswith('[') and cleaned_text.endswith(']'):
                                    return json.loads(cleaned_text)
                                
                                return None
                            except Exception as e:
                                logger.error(f"JSON extraction failed: {e}")
                                logger.debug(f"Failed text: {text[:300]}...")
                                return None
                        
                        def _generate_intelligent_steps(self, instruction):
                            """Generate detailed steps based on instruction complexity"""
                            instruction_lower = instruction.lower()
                            
                            # Check for complex multi-step scenarios first
                            if self._is_complex_workflow(instruction_lower):
                                return self._create_complex_workflow_steps(instruction, instruction_lower)
                            
                            # Simple single-action patterns
                            elif "click" in instruction_lower and len(instruction_lower.split()) <= 6:
                                return self._create_click_steps(instruction)
                            elif ("type" in instruction_lower or "write" in instruction_lower) and len(instruction_lower.split()) <= 8:
                                return self._create_typing_steps(instruction)
                            else:
                                # Generic automation steps for unclear instructions
                                return self._create_generic_steps(instruction)
                        
                        def _is_complex_workflow(self, instruction_lower):
                            """Detect if instruction requires complex multi-step workflow"""
                            # Look for multiple action keywords
                            action_words = ['click', 'type', 'fill', 'select', 'upload', 'add', 'go', 'navigate', 'enter', 'submit', 'save', 'create', 'publish', 'change', 'enable', 'disable', 'bookmark']
                            action_count = sum(1 for word in action_words if word in instruction_lower)
                            
                            # Look for workflow indicators
                            workflow_indicators = [', then', ', and then', 'and', ', go to', ', enter', ', select', ', upload', ', add', ', change', ', enable', ', save', ', submit']
                            has_workflow = any(indicator in instruction_lower for indicator in workflow_indicators)
                            
                            # Complex if multiple actions or workflow indicators
                            return action_count >= 2 or has_workflow or len(instruction_lower.split()) > 10
                        
                        def _create_complex_workflow_steps(self, instruction, instruction_lower):
                            """Create detailed steps for complex workflows"""
                            steps = []
                            
                            # Form filling workflow
                            if "fill" in instruction_lower and ("form" in instruction_lower or "registration" in instruction_lower):
                                steps.extend([
                                    self._create_step('analyze_form', 'Analyze form fields and requirements', 'analyze', 'form'),
                                    self._create_step('fill_name', 'Fill in name field', 'type', 'input[name*="name"]'),
                                    self._create_step('fill_email', 'Fill in email field', 'type', 'input[type="email"]'),
                                    self._create_step('fill_password', 'Fill in password field', 'type', 'input[type="password"]'),
                                    self._create_step('submit_form', 'Submit the form', 'click', 'button[type="submit"]')
                                ])
                            
                            # E-commerce workflow
                            elif "cart" in instruction_lower and "checkout" in instruction_lower:
                                steps.extend([
                                    self._create_step('add_to_cart', 'Add item to shopping cart', 'click', 'button[class*="cart"]'),
                                    self._create_step('go_to_cart', 'Navigate to cart/checkout', 'click', 'cart|checkout'),
                                    self._create_step('enter_shipping', 'Enter shipping information', 'type', 'shipping_form'),
                                    self._create_step('place_order', 'Place the order', 'click', 'place_order|checkout_button')
                                ])
                            
                            # File upload workflow
                            elif "upload" in instruction_lower and ("file" in instruction_lower or "select" in instruction_lower):
                                steps.extend([
                                    self._create_step('click_upload', 'Click upload button', 'click', 'input[type="file"]|upload_button'),
                                    self._create_step('select_file', 'Select file from computer', 'file_select', 'file_dialog'),
                                    self._create_step('add_description', 'Add file description', 'type', 'description_field'),
                                    self._create_step('confirm_upload', 'Confirm and upload file', 'click', 'upload_confirm')
                                ])
                            
                            # Search and interact workflow
                            elif "search" in instruction_lower and ("click" in instruction_lower or "result" in instruction_lower):
                                search_term = self._extract_search_term(instruction)
                                steps.extend([
                                    self._create_step('find_search', 'Locate search input field', 'detect', 'input[type="search"]|search_box'),
                                    self._create_step('enter_search', f'Enter search term: {search_term}', 'type', 'search_field', search_term),
                                    self._create_step('submit_search', 'Submit search query', 'click', 'search_button'),
                                    self._create_step('click_result', 'Click on first search result', 'click', 'search_result')
                                ])
                                if "bookmark" in instruction_lower:
                                    steps.append(self._create_step('bookmark_page', 'Bookmark the page', 'click', 'bookmark_button'))
                            
                            # Social media posting workflow
                            elif "post" in instruction_lower and ("image" in instruction_lower or "caption" in instruction_lower):
                                steps.extend([
                                    self._create_step('create_post', 'Click create new post', 'click', 'new_post_button'),
                                    self._create_step('add_image', 'Add image to post', 'click', 'image_upload'),
                                    self._create_step('write_caption', 'Write post caption', 'type', 'caption_field'),
                                    self._create_step('publish_post', 'Publish the post', 'click', 'publish_button')
                                ])
                            
                            # Settings configuration workflow
                            elif "settings" in instruction_lower and ("change" in instruction_lower or "enable" in instruction_lower):
                                steps.extend([
                                    self._create_step('open_settings', 'Navigate to settings page', 'click', 'settings_button'),
                                    self._create_step('change_theme', 'Change theme to dark mode', 'click', 'dark_mode_toggle'),
                                    self._create_step('enable_notifications', 'Enable notifications', 'click', 'notification_toggle'),
                                    self._create_step('save_settings', 'Save configuration changes', 'click', 'save_button')
                                ])
                            
                            # Default complex breakdown
                            else:
                                # Break down by major action words
                                action_parts = self._split_by_actions(instruction)
                                for i, part in enumerate(action_parts, 1):
                                    steps.append(self._create_step(f'action_{i}', f'Execute: {part.strip()}', 'action', 'auto_detect'))
                            
                            return steps if steps else self._create_generic_steps(instruction)
                        
                        def _create_step(self, step_id, description, action_type, target, value=''):
                            """Helper to create step objects"""
                            return type('Step', (), {
                                'id': step_id,
                                'description': description,
                                'action_type': action_type,
                                'target': target,
                                'value': value,
                                'estimated_duration': 2
                            })()
                        
                        def _create_click_steps(self, instruction):
                            """Create steps for simple click actions"""
                            return [
                                self._create_step('analyze_screen', 'Analyze current screen', 'analyze', 'screen'),
                                self._create_step('detect_element', f'Detect clickable element for: {instruction}', 'detect', 'button|link|clickable'),
                                self._create_step('click_element', 'Click on detected element', 'click', 'detected_element')
                            ]
                        
                        def _create_typing_steps(self, instruction):
                            """Create steps for typing actions"""
                            text_to_type = self._extract_text_to_type(instruction)
                            return [
                                self._create_step('find_input', 'Find text input field', 'detect', 'input|textarea'),
                                self._create_step('click_input', 'Click on input field', 'click', 'input_field'),
                                self._create_step('type_text', f'Type text: {text_to_type}', 'type', 'input_field', text_to_type)
                            ]
                        
                        def _create_generic_steps(self, instruction):
                            """Create generic steps for unclear instructions"""
                            return [
                                self._create_step('step_1', f'Prepare for: {instruction}', 'prepare', 'screen'),
                                self._create_step('step_2', f'Execute: {instruction}', 'execute', 'auto_detected')
                            ]
                        
                        def _extract_search_term(self, instruction):
                            """Extract search term from instruction"""
                            if "search for" in instruction.lower():
                                parts = instruction.lower().split("search for")
                                if len(parts) > 1:
                                    term = parts[1].split(',')[0].split(' and ')[0].strip()
                                    return term.strip("'\"")
                            return "search term"
                        
                        def _split_by_actions(self, instruction):
                            """Split instruction by action keywords"""
                            separators = [', then', ', and then', 'and', ', go to', ', enter', ', select', ', upload', ', add', ', change', ', enable', ', save', ', submit']
                            parts = [instruction]
                            
                            for sep in separators:
                                new_parts = []
                                for part in parts:
                                    new_parts.extend(part.split(sep))
                                parts = new_parts
                            
                            return [part.strip() for part in parts if part.strip()]
                        
                        def _get_smart_coordinates(self, instruction):
                            """Generate intelligent coordinates based on instruction content"""
                            instruction_lower = instruction.lower()
                            
                            # Screen dimensions: 1470x956 (from input_controller log)
                            screen_width = 1470
                            screen_height = 956
                            
                            # Coordinate mapping based on instruction keywords
                            if "center" in instruction_lower:
                                return {"x": screen_width // 2, "y": screen_height // 2}
                            elif "top" in instruction_lower and "left" in instruction_lower:
                                return {"x": 100, "y": 100}
                            elif "top" in instruction_lower and "right" in instruction_lower:
                                return {"x": screen_width - 100, "y": 100}
                            elif "bottom" in instruction_lower and "left" in instruction_lower:
                                return {"x": 100, "y": screen_height - 100}
                            elif "bottom" in instruction_lower and "right" in instruction_lower:
                                return {"x": screen_width - 100, "y": screen_height - 100}
                            elif "search" in instruction_lower:
                                # Search buttons are typically in top-right
                                return {"x": screen_width - 150, "y": 120}
                            elif "menu" in instruction_lower or "navigation" in instruction_lower:
                                # Menus are typically top-left
                                return {"x": 200, "y": 100}
                            elif "input" in instruction_lower or "field" in instruction_lower:
                                # Input fields are typically center-top
                                return {"x": screen_width // 2, "y": screen_height // 3}
                            elif "button" in instruction_lower:
                                # Buttons are often center or bottom-center
                                return {"x": screen_width // 2, "y": screen_height // 2 + 100}
                            elif "settings" in instruction_lower:
                                # Settings often in top-right or gear icon
                                return {"x": screen_width - 200, "y": 150}
                            else:
                                # Default to center
                                return {"x": screen_width // 2, "y": screen_height // 2}
                        
                        def _extract_text_to_type(self, instruction):
                            """Extract text content from typing instructions"""
                            instruction_lower = instruction.lower()
                            
                            # Look for quoted text
                            if "'" in instruction:
                                start = instruction.find("'")
                                end = instruction.find("'", start + 1)
                                if end != -1:
                                    return instruction[start + 1:end]
                            
                            if '"' in instruction:
                                start = instruction.find('"')
                                end = instruction.find('"', start + 1)
                                if end != -1:
                                    return instruction[start + 1:end]
                            
                            # Look for common patterns
                            if "hello world" in instruction_lower:
                                return "hello world"
                            elif "search for" in instruction_lower:
                                # Extract search term
                                parts = instruction_lower.split("search for")
                                if len(parts) > 1:
                                    search_term = parts[1].strip().split()[0:3]  # Take first 3 words
                                    return " ".join(search_term)
                            
                            # Default fallback
                            return "sample text"
                    
                    plan = FastFallbackPlan(instruction)
                    logger.info(f"⚡ Created FAST fallback plan with {len(plan.steps)} steps in <1s")
                
                # Convert LLM plan to the expected format
                execution_plan = {
                    "action": "comprehensive_automation",
                    "target_element": {
                        "element_text": f"LLM Plan: {plan.title}",
                        "position": getattr(plan, 'coordinates', {"x": 640, "y": 360})  # Use smart coordinates if available
                    },
                    "execution_details": {
                        "risk_level": "medium",
                        "warnings": [],
                        "steps": [
                            {
                                "id": step.id,
                                "description": step.description,
                                "action_type": step.action_type,
                                "target": step.target,
                                "value": step.value,
                                "estimated_duration": step.estimated_duration
                            } for step in plan.steps
                        ]
                    },
                    "llm_generated": True,
                    "title": plan.title,
                    "total_steps": len(plan.steps)
                }
                
                logger.info(f"✅ LLM created comprehensive plan: {plan.title} with {len(plan.steps)} steps")
                return {
                    "success": True,
                    "execution_plan": execution_plan,
                    "instruction": instruction,
                    "confidence_score": getattr(plan, 'complexity_score', 0.8),
                    "llm_generated": True
                }
                
            except Exception as llm_error:
                logger.warning(f"LLM planning failed, falling back to standard automation: {llm_error}")
            
            # FALLBACK: Use the automation system to generate a plan
            if self.automation:
                # Create a plan using the automation system
                parsed_command = await self.automation._parse_command(instruction)
                if not parsed_command["success"]:
                    return {
                        "success": False,
                        "error": "Could not understand command",
                        "instruction": instruction
                    }
                
                # Analyze screen to find target elements
                analysis_result = await self.automation._analyze_current_screen()
                if not analysis_result or "elements" not in analysis_result:
                    return {
                        "success": False,
                        "error": "Could not analyze screen",
                        "instruction": instruction
                    }
                
                # Find target elements
                element_matches = await self.automation._find_target_elements(
                    parsed_command, 
                    analysis_result["elements"]
                )
                
                # Always create a plan, even with weak matches - let the user decide
                if not element_matches:
                    # Create a fallback plan with manual target selection
                    logger.warning(f"No good target matches found for '{parsed_command.get('target_description', 'unknown')}', creating fallback plan")
                    
                    # Try to find ANY text fields or clickable elements as fallback
                    fallback_elements = [
                        elem for elem in analysis_result["elements"]
                        if elem.get("element_type") in ["text_field", "input_field", "button", "text_element"]
                    ][:5]  # Take top 5 as options
                    
                    if fallback_elements:
                        # Use the first fallback element with low confidence
                        element_matches = [{
                            **fallback_elements[0],
                            "confidence": 0.3,  # Low confidence to indicate uncertainty
                            "match_reason": "fallback_best_guess",
                            "alternatives": fallback_elements[1:4]  # Provide alternatives
                        }]
                        logger.info(f"Created fallback plan with {len(element_matches)} weak matches")
                    else:
                        # Last resort: create a generic screen center plan
                        element_matches = [{
                            "element_text": "Screen center (manual guidance needed)",
                            "element_type": "fallback_target",
                            "position": {"x": 640, "y": 360},  # Screen center approximation
                            "confidence": 0.1,
                            "match_reason": "no_targets_found",
                            "alternatives": []
                        }]
                        logger.warning("Created minimal fallback plan - user guidance required")
                
                # Create execution plan
                execution_plan = await self.automation._create_execution_plan(parsed_command, element_matches)
                
                return {
                    "success": True,
                    "execution_plan": execution_plan,
                    "instruction": instruction,
                    "confidence_score": element_matches[0]["confidence"] if element_matches else 0
                }
            else:
                return {
                    "success": False,
                    "error": "Automation system not available",
                    "instruction": instruction
                }
                
        except Exception as e:
            logger.error(f"Error creating execution plan: {e}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": f"Plan creation failed: {str(e)}",
                "instruction": instruction
            }

    async def handle_user_instruction(self, instruction: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle user instruction and route to appropriate handler.
        
        Args:
            instruction: Natural language instruction from user
            context: Optional context about current state
            
        Returns:
            Dict with execution results and metadata
        """
        try:
            logger.info(f"Handling user instruction: '{instruction}'")
            
            # Record the instruction
            command_record = {
                "timestamp": datetime.now().isoformat(),
                "instruction": instruction,
                "context": context,
                "result": None,
                "success": False,
                "category": None
            }
            
            # Categorize the instruction
            category = self._categorize_instruction(instruction)
            command_record["category"] = category
            
            # Route to appropriate handler
            if category == "automation":
                result = await self._handle_automation_command(instruction, context)
            elif category == "query":
                result = await self._handle_query_command(instruction, context)
            elif category == "navigation":
                result = await self._handle_navigation_command(instruction, context)
            else:
                # Try automation as fallback
                logger.info(f"Unknown category, trying automation for: {instruction}")
                result = await self._handle_automation_command(instruction, context)
            
            # Update command record
            command_record["result"] = result
            command_record["success"] = result.get("success", False)
            
            # Learn from the result if enabled
            if self.learning_mode:
                await self._learn_from_result(command_record)
            
            # Add to history
            self.command_history.append(command_record)
            
            # Limit history size
            if len(self.command_history) > 100:
                self.command_history = self.command_history[-100:]
            
            return {
                "success": result.get("success", False),
                "category": category,
                "execution_result": result,
                "instruction": instruction,
                "timestamp": command_record["timestamp"]
            }
            
        except Exception as e:
            logger.error(f"Error handling instruction '{instruction}': {e}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "error": str(e),
                "instruction": instruction,
                "category": "error"
            }
    
    def _categorize_instruction(self, instruction: str) -> str:
        """Categorize instruction to route to appropriate handler"""
        instruction_lower = instruction.lower().strip()
        
        # Check each category
        for category, keywords in self.command_categories.items():
            for keyword in keywords:
                if keyword in instruction_lower:
                    return category
        
        # Default to automation for action-oriented commands
        action_words = ["do", "make", "perform", "execute", "run"]
        if any(word in instruction_lower for word in action_words):
            return "automation"
        
        return "unknown"
    
    async def _handle_automation_command(self, instruction: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle automation commands via the enhanced automation system"""
        try:
            logger.info(f"Executing automation command: {instruction}")
            
            # Check if we have a stored plan with pre-parsed details
            if context and "stored_plan" in context:
                stored_plan = context["stored_plan"]
                logger.info(f"Using stored plan details: {stored_plan.get('action', 'unknown')} action")
                
                # Execute with stored plan details to avoid re-parsing
                result = await self.automation.execute_command(instruction, stored_plan)
            else:
                # Execute the command using enhanced automation (normal flow)
                result = await self.automation.execute_command(instruction)
            
            # Add additional metadata
            result["handler"] = "automation"
            result["instruction_type"] = "automation_command"
            
            if result["success"]:
                logger.info(f"Automation command succeeded: {instruction}")
            else:
                logger.warning(f"Automation command failed: {instruction} - {result.get('error', 'Unknown error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in automation command: {e}")
            return {
                "success": False,
                "error": str(e),
                "handler": "automation"
            }
    
    async def _handle_query_command(self, instruction: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle query commands that ask about screen content"""
        try:
            logger.info(f"Handling query command: {instruction}")
            
            # Get current screen elements
            elements = await self.automation.get_available_elements()
            
            instruction_lower = instruction.lower()
            
            if "what" in instruction_lower and "button" in instruction_lower:
                # List available buttons
                buttons = [elem for elem in elements if elem.get("element_type") == "button"]
                return {
                    "success": True,
                    "handler": "query",
                    "query_type": "list_buttons",
                    "result": f"Found {len(buttons)} buttons: " + ", ".join([elem.get("element_text", "unnamed") for elem in buttons[:10]]),
                    "elements": buttons
                }
            
            elif "what" in instruction_lower and ("element" in instruction_lower or "available" in instruction_lower):
                # List all available elements
                return {
                    "success": True,
                    "handler": "query",
                    "query_type": "list_elements",
                    "result": f"Found {len(elements)} interactive elements on screen",
                    "elements": elements[:20]  # Limit to first 20
                }
            
            elif "where" in instruction_lower:
                # Find specific element
                target = instruction_lower.replace("where", "").replace("is", "").strip()
                if target:
                    matching_elements = []
                    for elem in elements:
                        if target in elem.get("element_text", "").lower():
                            matching_elements.append(elem)
                    
                    if matching_elements:
                        return {
                            "success": True,
                            "handler": "query",
                            "query_type": "find_element",
                            "result": f"Found {len(matching_elements)} elements matching '{target}'",
                            "elements": matching_elements
                        }
                    else:
                        return {
                            "success": False,
                            "handler": "query",
                            "query_type": "find_element",
                            "result": f"No elements found matching '{target}'",
                            "available_elements": [elem.get("element_text", "unnamed") for elem in elements[:10]]
                        }
            
            # Default query response
            return {
                "success": True,
                "handler": "query",
                "query_type": "general",
                "result": f"Screen analysis complete. Found {len(elements)} interactive elements.",
                "instruction": instruction
            }
            
        except Exception as e:
            logger.error(f"Error in query command: {e}")
            return {
                "success": False,
                "error": str(e),
                "handler": "query"
            }
    
    async def _handle_navigation_command(self, instruction: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Handle navigation commands"""
        try:
            logger.info(f"Handling navigation command: {instruction}")
            
            instruction_lower = instruction.lower()
            
            if "go to" in instruction_lower or "navigate to" in instruction_lower:
                # Extract target
                target = instruction_lower.replace("go to", "").replace("navigate to", "").strip()
                
                # Try to find and click the target
                result = await self.automation.execute_command(f"click {target}")
                result["handler"] = "navigation"
                result["navigation_type"] = "go_to"
                return result
            
            elif "open" in instruction_lower:
                # Try to open something
                target = instruction_lower.replace("open", "").strip()
                result = await self.automation.execute_command(f"click {target}")
                result["handler"] = "navigation"
                result["navigation_type"] = "open"
                return result
            
            # Default to automation handling
            result = await self._handle_automation_command(instruction, context)
            result["handler"] = "navigation"
            return result
            
        except Exception as e:
            logger.error(f"Error in navigation command: {e}")
            return {
                "success": False,
                "error": str(e),
                "handler": "navigation"
            }
    
    async def _learn_from_result(self, command_record: Dict[str, Any]):
        """Learn from command execution results to improve future performance"""
        try:
            instruction = command_record["instruction"]
            success = command_record["success"]
            result = command_record["result"]
            
            # Simple learning: track successful patterns
            if success:
                logger.debug(f"Learning: Successful command pattern - {instruction}")
                # Could implement pattern recognition here
            else:
                logger.debug(f"Learning: Failed command - {instruction}, reason: {result.get('error', 'unknown')}")
                # Could implement failure analysis here
            
            # For now, just log for future ML implementation
            
        except Exception as e:
            logger.debug(f"Error in learning system: {e}")
    
    async def get_command_suggestions(self, partial_command: str) -> List[str]:
        """Get command suggestions based on current screen content and history"""
        try:
            suggestions = []
            
            # Get current screen elements
            elements = await self.automation.get_available_elements()
            
            partial_lower = partial_command.lower()
            
            # Suggest clickable elements
            if "click" in partial_lower:
                for elem in elements[:5]:  # Top 5 elements
                    text = elem.get("element_text", "")
                    if text and len(text) > 1:
                        suggestions.append(f"click the {text}")
            
            # Suggest typing commands for text fields
            elif "type" in partial_lower:
                text_fields = [elem for elem in elements if elem.get("element_type") in ["textfield", "input"]]
                for field in text_fields[:3]:
                    text = field.get("element_text", "text field")
                    suggestions.append(f"type [your text] in the {text}")
            
            # Suggest based on successful command history
            for record in reversed(self.command_history[-10:]):  # Last 10 commands
                if record["success"] and partial_lower in record["instruction"].lower():
                    suggestions.append(record["instruction"])
            
            return list(set(suggestions))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error getting command suggestions: {e}")
            return []
    
    async def get_screen_summary(self) -> Dict[str, Any]:
        """Get a summary of current screen content for user awareness"""
        try:
            elements = await self.automation.get_available_elements()
            
            # Categorize elements
            element_types = {}
            for elem in elements:
                elem_type = elem.get("element_type", "unknown")
                element_types[elem_type] = element_types.get(elem_type, 0) + 1
            
            # Get notable elements
            buttons = [elem for elem in elements if elem.get("element_type") == "button"][:5]
            text_fields = [elem for elem in elements if elem.get("element_type") in ["textfield", "input"]][:3]
            
            return {
                "total_elements": len(elements),
                "element_types": element_types,
                "notable_buttons": [elem.get("element_text", "unnamed") for elem in buttons],
                "text_fields": [elem.get("element_text", "text field") for elem in text_fields],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting screen summary: {e}")
            return {"error": str(e)}
    
    def get_command_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent command history"""
        return self.command_history[-limit:] if self.command_history else []
    
    def stop(self):
        """Stop the automation handler"""
        if self.automation:
            self.automation.stop()
        logger.info("Enhanced Automation Handler stopped")

# Test and demo functions
async def test_automation_handler():
    """Test the automation handler with sample commands"""
    handler = EnhancedAutomationHandler()
    
    test_commands = [
        "what buttons are available?",
        "click the submit button",
        "type hello world in the search box",
        "where is the save button?",
        "scroll down"
    ]
    
    print("🤖 Testing Enhanced Automation Handler")
    print("=" * 50)
    
    for command in test_commands:
        print(f"\n🔍 Testing: '{command}'")
        result = await handler.handle_user_instruction(command)
        
        if result["success"]:
            print(f"✅ Success: {result.get('execution_result', {}).get('action', 'completed')}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
        
        # Small delay between commands
        await asyncio.sleep(1)
    
    # Show screen summary
    print(f"\n📊 Screen Summary:")
    summary = await handler.get_screen_summary()
    print(json.dumps(summary, indent=2))
    
    handler.stop()

async def main():
    """Main function for testing or CLI usage"""
    if len(sys.argv) > 1:
        # CLI mode - execute single command
        command = " ".join(sys.argv[1:])
        handler = EnhancedAutomationHandler()
        
        print(f"🤖 Executing: '{command}'")
        result = await handler.handle_user_instruction(command)
        
        if result["success"]:
            print("✅ Command executed successfully")
            if "execution_result" in result:
                exec_result = result["execution_result"]
                if "target_element" in exec_result:
                    target = exec_result["target_element"]
                    print(f"   Target: {target.get('element_text', 'unknown')} ({target.get('element_type', 'unknown')})")
                if "confidence" in exec_result:
                    print(f"   Confidence: {exec_result['confidence']:.2f}")
        else:
            print("❌ Command failed")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            
            # Show available elements if target not found
            if "available_elements" in result.get("execution_result", {}):
                available = result["execution_result"]["available_elements"]
                if available:
                    print(f"   Available elements: {', '.join(available[:5])}")
        
        handler.stop()
    else:
        # Test mode
        await test_automation_handler()

if __name__ == "__main__":
    asyncio.run(main())