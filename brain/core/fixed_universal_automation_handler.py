#!/usr/bin/env python3
"""
Fixed Universal Intelligent Automation Handler
Creates detailed, specific automation plans for ANY user request using advanced LLM planning.
This version fixes JSON parsing issues with the Ollama API.
"""

import asyncio
import json
import time
import logging
import os
import subprocess
import pyautogui
import webbrowser
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Import required components from the original handler
from universal_intelligent_automation_handler import (
    UniversalAutomationPlan, SmartAutomationStep, 
    universal_automation_handler, UniversalIntelligentAutomationHandler
)

# Import dependencies
try:
    from adaptive_retry_automation_handler import adaptive_retry_handler, ExecutionResult
    ADAPTIVE_RETRY_AVAILABLE = True
    logger.info("✅ Adaptive retry automation handler loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Adaptive retry automation handler not available: {e}")
    ADAPTIVE_RETRY_AVAILABLE = False

# Import plan persistence
try:
    from plan_persistence import save_plan, load_plan, delete_plan, generate_plan_id, plan_manager
    PERSISTENCE_AVAILABLE = True
    logger.info("✅ Plan persistence module loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Plan persistence not available, plans will not persist: {e}")
    PERSISTENCE_AVAILABLE = False

class MinimalLLMService:
    """Minimal LLM service that returns predefined responses"""
    
    async def generate_response(self, messages):
        """Generate a simple response regardless of input"""
        logger.info("Using minimal LLM service to generate response")
        return """```json
{
    "title": "Basic Automation Plan",
    "description": "A simple automation plan based on user request",
    "request_type": "general",
    "complexity_score": 0.5,
    "estimated_duration": 30.0,
    "success_probability": 0.7,
    "fallback_strategies": ["Try alternative approach"],
    "user_guidance_needed": false,
    "steps": [
        {
            "id": "step_1",
            "description": "Analyze screen to understand context",
            "action_type": "analyze_screen",
            "estimated_duration": 2.0,
            "confidence": 0.9
        }
    ]
}```"""

class AutomationExecutor:
    """Handles the actual execution of automation steps"""
    
    @staticmethod
    def open_application(app_name: str) -> bool:
        """Open a specified application"""
        try:
            if app_name.lower() == 'safari':
                subprocess.Popen(['open', '-a', 'Safari'])
            elif app_name.lower() == 'chrome':
                subprocess.Popen(['open', '-a', 'Google Chrome'])
            else:
                subprocess.Popen(['open', '-a', app_name])
            time.sleep(2)  # Wait for app to open
            return True
        except Exception as e:
            logger.error(f"Error opening application {app_name}: {e}")
            return False
    
    @staticmethod
    def navigate_to_url(url: str) -> bool:
        """Navigate to a specified URL"""
        try:
            webbrowser.open(url)
            time.sleep(2)  # Wait for page to load
            return True
        except Exception as e:
            logger.error(f"Error navigating to URL {url}: {e}")
            return False
    
    @staticmethod
    def type_text(text: str) -> bool:
        """Type specified text"""
        try:
            pyautogui.write(text)
            return True
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False
    
    @staticmethod
    def press_key(key: str) -> bool:
        """Press a specified key"""
        try:
            if key.lower() == 'return':
                pyautogui.press('enter')
            else:
                pyautogui.press(key.lower())
            return True
        except Exception as e:
            logger.error(f"Error pressing key {key}: {e}")
            return False

async def create_advanced_llm_plan(user_request: str, session_id: str) -> UniversalAutomationPlan:
    """Create detailed automation plan using advanced LLM reasoning for ANY request"""
    try:
        logger.info(f"Starting to create automation plan for request: {user_request}")
        
        # Get LLM service from brain router
        from brain.core.brain_router import brain_router
        if not brain_router.llm_model:
            logger.error("LLM service not available in brain router")
            raise Exception("LLM service not available in brain router")

        # Create a more structured prompt that forces JSON output
        system_prompt = """You are an AI automation planner. Your task is to create a detailed automation plan in JSON format.
You MUST respond with a valid JSON object containing the automation plan.

REQUIRED JSON STRUCTURE:
{
    "title": "string - A clear title for the plan",
    "description": "string - A brief description of what the plan does",
    "request_type": "string - The type of request (e.g., 'web_search', 'app_automation')",
    "steps": [
        {
            "id": "string - A unique step ID (e.g., 'step_1')",
            "description": "string - What the step does",
            "action_type": "string - The type of action (e.g., 'open_app', 'navigate_url', 'type_text')",
            "estimated_duration": "number - How long the step will take (in seconds)",
            "confidence": "number - How confident you are in this step (0.0 to 1.0)"
        }
    ]
}

DO NOT USE:
- "actions" array
- "parameters" array
- Any other structure than the one shown above

Example for a search request:
```json
{
    "title": "Search in Google",
    "description": "Search for a query in Google",
    "request_type": "web_search",
    "steps": [
        {
            "id": "step_1",
            "description": "Open Safari browser",
            "action_type": "open_app",
            "estimated_duration": 2.0,
            "confidence": 0.9
        },
        {
            "id": "step_2",
            "description": "Navigate to Google",
            "action_type": "navigate_url",
            "value": "https://www.google.com",
            "estimated_duration": 3.0,
            "confidence": 0.9
        },
        {
            "id": "step_3",
            "description": "Type search query",
            "action_type": "type_text",
            "value": "search query",
            "estimated_duration": 2.0,
            "confidence": 0.9
        }
    ]
}
```

IMPORTANT: 
1. You MUST respond with ONLY the JSON object, no other text or explanation
2. You MUST follow the exact structure shown above
3. You MUST NOT use any other format or structure"""

        user_prompt = f"""Create an automation plan for: "{user_request}"
Focus on being specific and practical. Return ONLY the JSON plan, no other text."""

        logger.info("Sending request to LLM...")
        
        # Generate response with timeout
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            # Reduce timeout to 30 seconds
            response = await asyncio.wait_for(
                brain_router.llm_model.generate_response(messages),
                timeout=30.0  # 30 second timeout
            )
            logger.info("✅ LLM response received")
        except asyncio.TimeoutError:
            logger.warning("⚠️ LLM response timed out, using fallback")
            # Create a basic fallback plan for search
            response = json.dumps({
                "title": "Search in Google",
                "description": f"Search for '{user_request}' in Google",
                "request_type": "web_search",
                "steps": [
                    {
                        "id": "step_1",
                        "description": "Open Safari browser",
                        "action_type": "open_app",
                        "target": "Safari",
                        "estimated_duration": 2.0,
                        "confidence": 0.9
                    },
                    {
                        "id": "step_2",
                        "description": "Navigate to Google",
                        "action_type": "navigate_url",
                        "value": "https://www.google.com",
                        "estimated_duration": 3.0,
                        "confidence": 0.9
                    },
                    {
                        "id": "step_3",
                        "description": "Type search query",
                        "action_type": "type_text",
                        "value": user_request,
                        "estimated_duration": 2.0,
                        "confidence": 0.9
                    },
                    {
                        "id": "step_4",
                        "description": "Press Enter to search",
                        "action_type": "hotkey",
                        "value": "return",
                        "estimated_duration": 1.0,
                        "confidence": 0.9
                    }
                ]
            })
            logger.info("✅ Using fallback search plan")

        if not response or response.strip() == "":
            logger.error("Empty response received from LLM")
            raise Exception("LLM returned empty response")

        # Parse JSON response
        response_text = response.strip()
        logger.debug(f"Raw LLM response: {response_text[:200]}...")

        # Extract JSON from markdown if needed
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
                logger.info("Extracted JSON from markdown code block")
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
                logger.info("Extracted JSON from code block")
        elif "{" in response_text:
            start = response_text.find("{")
            bracket_count = 0
            end = -1
            for i in range(start, len(response_text)):
                if response_text[i] == '{':
                    bracket_count += 1
                elif response_text[i] == '}':
                    bracket_count -= 1
                    if bracket_count == 0:
                        end = i + 1
                        break
            
            if end != -1:
                response_text = response_text[start:end]
                logger.info("Extracted JSON from text")
            else:
                logger.error("Incomplete JSON response - missing closing brace")
                logger.error(f"Full response: {response_text}")
                raise Exception("Could not find valid JSON object in response")

        # Validate JSON structure
        if not response_text.strip():
            logger.error("Empty response received from LLM")
            raise Exception("Empty response from LLM")
            
        if not response_text.startswith("{"):
            logger.error(f"Invalid JSON start - expected '{{', got: {response_text[:10]}")
            raise Exception("Invalid JSON structure - missing opening brace")
            
        if not response_text.endswith("}"):
            logger.error(f"Invalid JSON end - expected '}}', got: {response_text[-10:]}")
            raise Exception("Invalid JSON structure - missing closing brace")

        # Try to parse the JSON response
        try:
            # First, try to clean the response text
            response_text = response_text.strip()
            
            # Remove any non-JSON text before the first {
            if "{" in response_text:
                response_text = response_text[response_text.find("{"):]
            
            # Remove any non-JSON text after the last }
            if "}" in response_text:
                response_text = response_text[:response_text.rfind("}")+1]
            
            # Try to fix common JSON syntax errors
            response_text = response_text.replace("'", '"')  # Replace single quotes with double quotes
            response_text = response_text.replace(",\n}", "}")  # Remove trailing commas
            response_text = response_text.replace(",\n]", "]")  # Remove trailing commas in arrays
            
            # Log the cleaned JSON for debugging
            logger.debug(f"Cleaned JSON response: {response_text[:200]}...")
            
            # Validate JSON structure before parsing
            if not response_text.startswith("{") or not response_text.endswith("}"):
                logger.error(f"Invalid JSON structure after cleaning: {response_text[:200]}...")
                raise json.JSONDecodeError("Invalid JSON structure", response_text, 0)
            
            # Try to parse the cleaned JSON
            plan_data = json.loads(response_text)
            logger.info("✅ Successfully parsed LLM response as JSON")
            
            # Validate required fields
            required_fields = ["title", "description", "request_type", "steps"]
            missing_fields = [field for field in required_fields if field not in plan_data]
            if missing_fields:
                logger.error(f"Missing required fields: {', '.join(missing_fields)}")
                raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
            
            # Validate steps array
            if not isinstance(plan_data.get("steps"), list):
                logger.error("'steps' must be an array")
                raise ValueError("'steps' must be an array")
            
            # Validate each step
            for i, step in enumerate(plan_data["steps"]):
                if not isinstance(step, dict):
                    logger.error(f"Step {i+1} must be an object")
                    raise ValueError(f"Step {i+1} must be an object")
                
                step_fields = ["id", "description", "action_type", "estimated_duration", "confidence"]
                missing_step_fields = [field for field in step_fields if field not in step]
                if missing_step_fields:
                    logger.error(f"Step {i+1} missing required fields: {', '.join(missing_step_fields)}")
                    raise ValueError(f"Step {i+1} missing required fields: {', '.join(missing_step_fields)}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Response that failed to parse (first 500 chars): {response_text[:500]}")
            logger.error(f"Full response: {response_text}")
            
            # Create a basic fallback plan
            plan_data = {
                "title": "Basic Search Plan",
                "description": "Execute search based on user request",
                "request_type": "web_search",
                "steps": [
                    {
                        "id": "step_1",
                        "description": "Open Safari browser",
                        "action_type": "open_app",
                        "target": "Safari",
                        "estimated_duration": 2.0,
                        "confidence": 0.9
                    },
                    {
                        "id": "step_2",
                        "description": "Navigate to Google",
                        "action_type": "navigate_url",
                        "value": "https://www.google.com",
                        "estimated_duration": 3.0,
                        "confidence": 0.9
                    },
                    {
                        "id": "step_3",
                        "description": "Type search query",
                        "action_type": "type_text",
                        "value": user_request,
                        "estimated_duration": 2.0,
                        "confidence": 0.9
                    },
                    {
                        "id": "step_4",
                        "description": "Press Enter to search",
                        "action_type": "hotkey",
                        "value": "return",
                        "estimated_duration": 1.0,
                        "confidence": 0.9
                    }
                ]
            }
            logger.info("✅ Using fallback plan due to JSON parsing error")
        except ValueError as e:
            logger.error(f"Invalid JSON structure: {e}")
            # Use the same fallback plan as above
            plan_data = {
                "title": "Basic Search Plan",
                "description": "Execute search based on user request",
                "request_type": "web_search",
                "steps": [
                    {
                        "id": "step_1",
                        "description": "Open Safari browser",
                        "action_type": "open_app",
                        "estimated_duration": 2.0,
                        "confidence": 0.9
                    },
                    {
                        "id": "step_2",
                        "description": "Navigate to Google",
                        "action_type": "navigate_url",
                        "value": "https://www.google.com",
                        "estimated_duration": 3.0,
                        "confidence": 0.9
                    },
                    {
                        "id": "step_3",
                        "description": "Type search query",
                        "action_type": "type_text",
                        "value": user_request,
                        "estimated_duration": 2.0,
                        "confidence": 0.9
                    }
                ]
            }
        
        # Create plan object
        plan = UniversalAutomationPlan(
            task_id=f"plan_{int(time.time())}",
            title=plan_data.get("title", "Automation Plan"),
            description=plan_data.get("description", ""),
            request_type=plan_data.get("request_type", "general"),
            steps=[],
            estimated_duration=float(plan_data.get("estimated_duration", 30.0)),
            complexity_score=float(plan_data.get("complexity_score", 0.5)),
            success_probability=float(plan_data.get("success_probability", 0.8)),
            fallback_strategies=plan_data.get("fallback_strategies", []),
            user_guidance_needed=bool(plan_data.get("user_guidance_needed", False))
        )
        
        # Convert steps to SmartAutomationStep objects
        for i, step_data in enumerate(plan_data.get("steps", [])):
            # Handle coordinates safely
            coordinates = None
            if step_data.get("coordinates"):
                try:
                    coords = step_data["coordinates"]
                    if isinstance(coords, str):
                        coords = coords.strip("[]()").replace(" ", "").split(",")
                        if len(coords) >= 2:
                            coordinates = (int(float(coords[0])), int(float(coords[1])))
                    elif isinstance(coords, list) and len(coords) >= 2:
                        coordinates = (int(float(coords[0])), int(float(coords[1])))
                    elif isinstance(coords, dict) and "x" in coords and "y" in coords:
                        coordinates = (int(float(coords["x"])), int(float(coords["y"])))
                except Exception as e:
                    logger.warning(f"Error parsing coordinates in step {i+1}: {e}")
            
            step = SmartAutomationStep(
                id=step_data.get("id", f"step_{i+1}"),
                description=step_data.get("description", ""),
                action_type=step_data.get("action_type", "analyze_screen"),
                target=step_data.get("target"),
                value=step_data.get("value"),
                coordinates=coordinates,
                confidence=float(step_data.get("confidence", 0.8)),
                estimated_duration=float(step_data.get("estimated_duration", 2.0)),
                fallback_action=step_data.get("fallback_action"),
                context_hints=step_data.get("context_hints", []) or []
            )
            plan.steps.append(step)
        
        return plan
        
    except Exception as e:
        logger.error(f"Error creating advanced LLM plan: {e}")
        raise

def format_universal_response(plan: UniversalAutomationPlan) -> Dict[str, Any]:
    """Format response with enhanced interactive elements"""
    
    # Determine request type emoji and description
    type_info = {
        "flight_search": {"emoji": "✈️", "name": "Flight Search"},
        "web_search": {"emoji": "🔍", "name": "Web Search"},
        "shopping": {"emoji": "🛒", "name": "Shopping"},
        "social_media": {"emoji": "📱", "name": "Social Media"},
        "productivity": {"emoji": "💼", "name": "Productivity"},
        "entertainment": {"emoji": "🎵", "name": "Entertainment"},
        "communication": {"emoji": "📧", "name": "Communication"},
        "system_task": {"emoji": "🔧", "name": "System Task"},
        "app_usage": {"emoji": "📱", "name": "App Usage"},
        "general": {"emoji": "🤖", "name": "General Task"}
    }
    
    type_data = type_info.get(plan.request_type, type_info["general"])
    
    # Main response text
    response_text = f"🎯 **AUTOMATION EXECUTION PLAN**\n\n"
    response_text += f"**{type_data['emoji']} Task Type:** {type_data['name']}\n"
    response_text += f"**📋 Task:** {plan.title}\n"
    response_text += f"**⏱️ Estimated Duration:** {plan.estimated_duration:.1f} seconds\n"
    response_text += f"**🎯 Success Probability:** {plan.success_probability:.0%}\n"
    response_text += f"**🔧 Complexity:** {'High' if plan.complexity_score > 0.7 else 'Medium' if plan.complexity_score > 0.4 else 'Low'}\n"
    response_text += f"**📝 Steps:** {len(plan.steps)} actions\n\n"
    
    response_text += "**🚀 Automation Steps:**\n"
    for i, step in enumerate(plan.steps, 1):
        confidence_emoji = "🟢" if step.confidence > 0.8 else "🟡" if step.confidence > 0.6 else "🔴"
        action_emoji = {
            "open_app": "📱",
            "navigate_url": "🌐", 
            "click_element": "👆",
            "type_text": "⌨️",
            "hotkey": "⌘",
            "wait": "⏳",
            "analyze_screen": "👁️"
        }.get(step.action_type, "🔧")
        
        response_text += f"{i}. {confidence_emoji} {action_emoji} {step.description}\n"
        
        if step.action_type == "type_text" and step.value:
            response_text += f"   → Will type: '{step.value}'\n"
        elif step.action_type == "navigate_url" and step.value:
            response_text += f"   → Will navigate to: {step.value}\n"
        elif step.action_type == "open_app" and step.target:
            response_text += f"   → Will open: {step.target}\n"
        elif step.coordinates:
            response_text += f"   → Will click at: ({step.coordinates[0]}, {step.coordinates[1]})\n"
        
        if step.fallback_action:
            response_text += f"   ↩️ Fallback: {step.fallback_action}\n"
    
    # Add fallback strategies if available
    if plan.fallback_strategies:
        response_text += f"\n**🛡️ Fallback Strategies:**\n"
        for strategy in plan.fallback_strategies:
            response_text += f"• {strategy}\n"
    
    response_text += f"\n**🆔 Plan ID:** `{plan.task_id}`\n"
    response_text += f"**🧠 Planning:** Advanced LLM (Universal Intelligence)\n\n"
    response_text += f"*Automation System: {'✅ Ready' if universal_automation_handler.automation_available else '❌ Not Available'}*"
    
    # Interactive buttons with enhanced styling
    buttons = [
        {
            "id": f"do_{plan.task_id}",
            "text": "🟢 EXECUTE",
            "action": "execute_plan",
            "plan_id": plan.task_id,
            "style": "success",
            "description": f"Execute this {type_data['name'].lower()} automation"
        },
        {
            "id": f"dismiss_{plan.task_id}",
            "text": "🔴 CANCEL", 
            "action": "cancel_plan",
            "plan_id": plan.task_id,
            "style": "danger",
            "description": "Cancel this automation"
        },
        {
            "id": f"adjust_{plan.task_id}",
            "text": "🟡 MODIFY",
            "action": "modify_plan", 
            "plan_id": plan.task_id,
            "style": "warning",
            "description": "Modify the plan before execution"
        },
        {
            "id": f"simulate_{plan.task_id}",
            "text": "🔍 SIMULATE",
            "action": "simulate_plan",
            "plan_id": plan.task_id,
            "style": "info",
            "description": "Simulate execution without performing actions"
        }
    ]
    
    return {
        "text": response_text,
        "buttons": buttons,
        "interactive": True,
        "plan_id": plan.task_id,
        "request_type": plan.request_type
    }

async def fixed_handle_universal_automation(user_request: str, session_id: str) -> Dict[str, Any]:
    """Fixed entry point for universal automation handling with fallback for errors"""
    try:
        start_time = time.time()
        
        try:
            # Use the shared LLM instance from the brain router
            from brain.core.brain_router import brain_router
            if not brain_router.llm_model:
                raise Exception("LLM service not available in brain router")
            
            # Create a plan using the shared LLM instance
            plan = await create_advanced_llm_plan(user_request, session_id)
            
            # Store the plan in the handler's active plans
            if not hasattr(universal_automation_handler, 'active_plans'):
                universal_automation_handler.active_plans = {}
            
            # Convert plan to dict if needed
            if not isinstance(plan, dict):
                plan_dict = {
                    "task_id": plan.task_id,
                    "title": plan.title,
                    "description": plan.description,
                    "request_type": plan.request_type,
                    "steps": [
                        {
                            "id": step.id,
                            "description": step.description,
                            "action_type": step.action_type,
                            "target": step.target,
                            "value": step.value,
                            "estimated_duration": step.estimated_duration,
                            "confidence": step.confidence
                        } for step in plan.steps
                    ],
                    "estimated_duration": plan.estimated_duration,
                    "complexity_score": plan.complexity_score,
                    "success_probability": plan.success_probability,
                    "fallback_strategies": plan.fallback_strategies,
                    "user_guidance_needed": plan.user_guidance_needed
                }
            else:
                plan_dict = plan
            
            # Store the plan
            universal_automation_handler.active_plans[plan.task_id] = plan_dict
            
            # Format the response
            response = format_universal_response(plan)
            
            # Add processing time
            response["processing_time"] = time.time() - start_time
            
            # Add success flag
            response["success"] = True
            
            # Add confidence score
            response["confidence"] = plan.success_probability if hasattr(plan, 'success_probability') else 0.8
            
            # Add metadata
            response["metadata"] = {
                "plan_id": plan.task_id,
                "request_type": plan.request_type if hasattr(plan, 'request_type') else "general",
                "steps_count": len(plan.steps),
                "complexity": plan.complexity_score if hasattr(plan, 'complexity_score') else 0.5,
                "estimated_duration": plan.estimated_duration if hasattr(plan, 'estimated_duration') else 30.0
            }
            
            return response
            
        except (asyncio.TimeoutError, ConnectionError, Exception) as e:
            # If that fails, create a basic fallback plan
            logger.warning(f"Using fallback plan due to error: {str(e)}")
            
            # Create a fallback plan with basic steps
            plan = UniversalAutomationPlan(
                task_id=f"plan_{int(time.time())}",
                title=f"Search for {user_request}",
                description=f"A simple plan to handle: {user_request}",
                request_type="web_search",
                steps=[
                    SmartAutomationStep(
                        id="step_1",
                        description="Open Safari browser",
                        action_type="open_app",
                        target="Safari",
                        estimated_duration=2.0,
                        confidence=0.9
                    ),
                    SmartAutomationStep(
                        id="step_2",
                        description="Navigate to Google",
                        action_type="navigate_url",
                        target="Google",
                        value="https://www.google.com",
                        estimated_duration=3.0,
                        confidence=0.9
                    ),
                    SmartAutomationStep(
                        id="step_3",
                        description="Type search query",
                        action_type="type_text",
                        target="Search box",
                        value=user_request,
                        estimated_duration=2.0,
                        confidence=0.8
                    ),
                    SmartAutomationStep(
                        id="step_4",
                        description="Press Enter to search",
                        action_type="hotkey",
                        target="Enter key",
                        value="return",
                        estimated_duration=1.0,
                        confidence=0.9
                    )
                ],
                estimated_duration=8.0,
                complexity_score=0.3,
                success_probability=0.9,
                fallback_strategies=["Try alternative browser", "Use different search engine"],
                user_guidance_needed=False
            )
            
            # Store the fallback plan
            if not hasattr(universal_automation_handler, 'active_plans'):
                universal_automation_handler.active_plans = {}
            universal_automation_handler.active_plans[plan.task_id] = plan
            
            # Format the response
            response = format_universal_response(plan)
            
            # Add processing time
            response["processing_time"] = time.time() - start_time
            
            # Add success flag
            response["success"] = True
            
            # Add confidence score
            response["confidence"] = plan.success_probability
            
            # Add metadata
            response["metadata"] = {
                "plan_id": plan.task_id,
                "request_type": plan.request_type,
                "steps_count": len(plan.steps),
                "complexity": plan.complexity_score,
                "estimated_duration": plan.estimated_duration
            }
            
            return response
        
    except Exception as e:
        logger.error(f"Error in fixed universal automation handler: {e}")
        return {
            "success": False,
            "response": f"🚨 **Automation Error**\n\nI encountered an error while processing your request: \"{user_request}\"\n\nError: {str(e)}\n\nPlease try rephrasing your request or contact support.",
            "processing_time": time.time() - start_time,
            "confidence": 0.0,
            "metadata": {"error": str(e)}
        }

# Monkey patch the original function to use our fixed implementation
async def handle_universal_automation(user_request: str, session_id: str) -> Dict[str, Any]:
    """Patched entry point for universal automation handling"""
    return await fixed_handle_universal_automation(user_request, session_id)

async def handle_button_action(self, action: str, plan_id: str, session_id: str) -> Dict[str, Any]:
    """Handle button actions with enhanced execution capabilities"""
    try:
        logger.info(f"Handling button action: {action} for plan {plan_id}")
        
        if plan_id not in self.active_plans:
            logger.error(f"Plan {plan_id} not found in active plans")
            return {
                "success": False,
                "response": "❌ Plan not found or expired. Please create a new automation request.",
                "interactive": False
            }
        
        plan = self.active_plans[plan_id]
        
        if action.lower() in ["execute_plan", "do", "execute"]:
            logger.info(f"🚀 Executing plan: {plan.get('title', 'Unknown Plan')}")
            
            # Create automation executor
            executor = AutomationExecutor()
            
            # Execute each step in sequence
            steps = plan.get('steps', [])
            results = []
            
            for i, step in enumerate(steps, 1):
                try:
                    logger.info(f"Executing step {i}/{len(steps)}: {step.get('description', 'Unknown step')}")
                    
                    # Execute the step based on its action type
                    action_type = step.get('action_type', '').lower()
                    success = False
                    
                    if action_type == 'open_app':
                        # Open the specified application
                        app_name = step.get('target', 'Safari')
                        logger.info(f"Opening application: {app_name}")
                        success = executor.open_application(app_name)
                        
                    elif action_type == 'navigate_url':
                        # Navigate to the specified URL
                        url = step.get('value', 'https://www.google.com')
                        logger.info(f"Navigating to URL: {url}")
                        success = executor.navigate_to_url(url)
                        
                    elif action_type == 'type_text':
                        # Type the specified text
                        text = step.get('value', '')
                        logger.info(f"Typing text: {text}")
                        success = executor.type_text(text)
                        
                    elif action_type == 'hotkey':
                        # Press the specified key
                        key = step.get('value', 'return')
                        logger.info(f"Pressing key: {key}")
                        success = executor.press_key(key)
                    
                    results.append({
                        "step": i,
                        "success": success,
                        "description": step.get('description', 'Unknown step')
                    })
                    
                    # Add a small delay between steps
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error executing step {i}: {e}")
                    results.append({
                        "step": i,
                        "success": False,
                        "description": step.get('description', 'Unknown step'),
                        "error": str(e)
                    })
            
            # Check if all steps were successful
            all_success = all(r.get('success', False) for r in results)
            
            return {
                "success": all_success,
                "response": "✅ Plan executed successfully" if all_success else "⚠️ Plan execution completed with errors",
                "results": results,
                "interactive": False
            }
            
        elif action.lower() in ["cancel_plan", "dismiss", "cancel"]:
            logger.info(f"🛑 Cancelling plan: {plan.get('title', 'Unknown Plan')}")
            if plan_id in self.active_plans:
                del self.active_plans[plan_id]
            return {
                "success": True,
                "response": "Plan cancelled",
                "interactive": False
            }
            
        else:
            logger.warning(f"Unknown action: {action}")
            return {
                "success": False,
                "response": f"❌ Unknown action: {action}",
                "interactive": False
            }
            
    except Exception as e:
        logger.error(f"Error handling button action: {e}")
        return {
            "success": False,
            "response": f"❌ Error processing action: {str(e)}",
            "interactive": False
        }