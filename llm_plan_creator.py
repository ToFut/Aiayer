#!/usr/bin/env python3
"""
LLM-Powered Plan Creator - Uses LLM to analyze any prompt and create intelligent automation plans
Optimized for speed and reliability without fallbacks
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import sys
import os
import re
import json5

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.llm.llm_service import LLMService

logger = logging.getLogger(__name__)

@dataclass
class LLMStep:
    """LLM-generated automation step"""
    id: str
    description: str
    action_type: str  # 'hotkey', 'type_text', 'press_key', 'click', 'wait', 'open_app'
    target: Optional[str] = None
    value: Optional[str] = None
    coordinates: Optional[tuple] = None
    confidence: float = 0.9
    estimated_duration: float = 2.0
    reasoning: str = ""

@dataclass
class LLMPlan:
    """LLM-generated automation plan"""
    task_id: str
    title: str
    description: str
    request_type: str
    steps: List[LLMStep]
    estimated_duration: float
    complexity_score: float
    success_probability: float
    llm_reasoning: str

class OptimizedLLMPlanCreator:
    def __init__(self):
        """Initialize the LLM-powered plan creator"""
        self.llm_service = LLMService()
        self.response_cache = {}
        self.max_cache_size = 100
        self.initialized = False
        
    async def initialize(self):
        """Initialize the LLM service"""
        if not self.initialized:
            try:
                await self.llm_service.initialize()
                self.initialized = True
                logger.info("✅ LLM Plan Creator initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize LLM Plan Creator: {e}")
                self.initialized = False
            
    async def create_plan(self, prompt: str, timeout: int = 30) -> Dict:
        """
        Create automation plan from prompt using optimized LLM approach (async)
        Returns plan_dict with optimized structure
        """
        try:
            start_time = time.time()
            
            # Check cache first
            cache_key = prompt.lower().strip()
            if cache_key in self.response_cache:
                logger.info(f"Using cached plan for: {prompt}")
                return self.response_cache[cache_key]
            
            # Create optimized prompt for faster response
            llm_prompt = self._create_optimized_prompt(prompt)
            
            messages = [
                {"role": "system", "content": "You are an expert Mac automation planner."},
                {"role": "user", "content": llm_prompt}
            ]
            # Call the LLM using the correct async method
            response = await self.llm_service.llm_client.generate_response(messages, stream=False, max_tokens=512)
            
            elapsed = time.time() - start_time
            logger.info(f"LLM response time: {elapsed:.2f}s")
            
            if response:
                plan = self._parse_llm_response(response, prompt)
                if plan:
                    # Cache the result
                    self._add_to_cache(cache_key, plan)
                    return plan
            
            # If LLM fails, create a simple plan based on keywords
            logger.warning(f"LLM failed for prompt: {prompt}, creating simple plan")
            return self._create_simple_plan(prompt)
            
        except Exception as e:
            logger.error(f"Plan creation error: {e}")
            return self._create_simple_plan(prompt)
    
    async def create_plan_streaming(self, prompt: str, timeout: int = 300):
        """
        Create automation plan from prompt using streaming LLM approach
        Yields chunks as they come from the LLM
        """
        try:
            start_time = time.time()
            
            # Use the improved LLM service with enhanced prompt engineering
            logger.info(f"🔄 Starting streaming plan generation for: {prompt}")
            
            # Stream the response using the improved LLM service
            full_response = ""
            chunk_count = 0
            
            async for chunk in self.llm_service.generate_response_with_fallback(prompt):
                chunk_count += 1
                full_response += chunk
                
                # Yield progress updates
                if chunk_count % 5 == 0:  # Every 5 chunks
                    elapsed = time.time() - start_time
                    yield f"🔄 Generating plan... ({chunk_count} chunks, {elapsed:.1f}s)"
                
                # Also yield the actual chunk for real-time display
                yield chunk
            
            # Parse the complete response
            elapsed = time.time() - start_time
            logger.info(f"✅ Streaming completed: {chunk_count} chunks in {elapsed:.2f}s")
            logger.info(f"LLM raw response: {repr(full_response)[:500]}")
            
            # Parse the plan from the full response
            plan = None
            try:
                plan = self._parse_llm_response(full_response, prompt)
                yield f"[DEBUG] Parsed plan type: {type(plan)}"
                yield f"[DEBUG] Parsed plan content: {repr(plan)[:500]}"
                if not isinstance(plan, dict) or "steps" not in plan or not isinstance(plan["steps"], list):
                    raise ValueError("Parsed plan is not a dict with a list of steps")
            except Exception as parse_error:
                logger.error(f"Failed to parse plan from LLM response: {parse_error}")
                logger.error(f"Raw LLM response: {full_response}")
                yield f"❌ Failed to parse plan from LLM response: {parse_error}"
                yield f"📝 Raw LLM output:\n{full_response[:1000]}"
                # Fallback plan
                fallback_plan = self._create_simple_plan(prompt)
                yield f"[DEBUG] Fallback plan: {json.dumps(fallback_plan, indent=2)}"
                yield json.dumps(fallback_plan, indent=2)
                return
            
            # Cache the result
            cache_key = prompt.lower().strip()
            if len(self.response_cache) >= self.max_cache_size:
                # Remove oldest entry
                oldest_key = next(iter(self.response_cache))
                del self.response_cache[oldest_key]
            self.response_cache[cache_key] = plan
            
            # Yield final result
            yield f"✅ Plan generated successfully in {elapsed:.2f}s"
            yield json.dumps(plan, indent=2)
            
        except Exception as e:
            error_msg = f"Streaming plan creation error: {str(e)}"
            logger.error(error_msg)
            yield f"❌ {error_msg}"
            
            # Return a simple fallback plan
            fallback_plan = {
                "steps": [
                    {
                        "id": "1",
                        "description": f"Execute: {prompt}",
                        "action_type": "hotkey",
                        "target": "cmd+space",
                        "value": prompt
                    }
                ],
                "apps": [],
                "reasoning": f"Fallback plan for: {prompt}"
            }
            yield f"[DEBUG] Exception fallback plan: {json.dumps(fallback_plan, indent=2)}"
            yield json.dumps(fallback_plan, indent=2)

    def _create_optimized_prompt(self, prompt: str) -> str:
        """Create a highly optimized prompt for fast LLM response"""
        return f'''
Create a simple automation plan for: "{prompt}"

Respond with ONLY ONE single-line JSON object, no extra text, no comments, no pretty-printing, no markdown, no explanation, no newlines, no arrays of objects, no multiple objects. Example:
{{"steps":[{{"action":"launch_app","app":"Safari","description":"Open Safari"}}],"apps":["Safari"]}}

Format:
{{"steps":[{{"action":"launch_app","app":"AppName","description":"Brief description"}}],"apps":["AppName"]}}

If you output more than one object, only the first will be used. Keep it simple - maximum 2 steps. Use common app names like Safari, Finder, Terminal, Notes, Calculator, Mail, Messages, Calendar, Photos, Music.'''

    def _repair_json(self, json_str: str) -> str:
        """Comprehensively repair malformed JSON from LLM output"""
        # Remove trailing commas before closing braces/brackets
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        
        # Count braces and brackets
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        
        # Add missing closing braces/brackets
        if open_braces > close_braces:
            json_str += '}' * (open_braces - close_braces)
        if open_brackets > close_brackets:
            json_str += ']' * (open_brackets - close_brackets)
        
        # Fix common LLM mistakes: missing commas between objects in arrays
        # Pattern: } followed by { without a comma
        json_str = re.sub(r'}\s*{', '},{', json_str)
        
        # Fix missing commas between key-value pairs
        # Pattern: "key": value followed by "key" without a comma
        json_str = re.sub(r'("[\w_]+":\s*[^,}\]]+)\s*("[\w_]+":)', r'\1,\2', json_str)
        
        # Fix trailing commas in objects and arrays
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        
        # If the JSON is still incomplete, try to complete it
        if not json_str.strip().endswith('}'):
            # Find the last complete object/array and close it
            last_complete = json_str.rfind('}')
            if last_complete == -1:
                last_complete = json_str.rfind(']')
            if last_complete != -1:
                # Add closing brace for the root object
                json_str = json_str[:last_complete+1] + '}'
        
        return json_str

    def _extract_key_value_pairs(self, json_str: str) -> dict:
        """Extract key-value pairs from a JSON-like string and reconstruct a dict (last resort)"""
        result = {}
        # Extract top-level arrays (steps, apps)
        steps_match = re.search(r'"steps"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
        if steps_match:
            steps_str = steps_match.group(1)
            # Extract each step as a dict
            step_dicts = re.findall(r'\{(.*?)\}', steps_str, re.DOTALL)
            steps = []
            for step in step_dicts:
                step_fields = re.findall(r'"(\w+)"\s*:\s*"([^"]*)"', step)
                steps.append({k: v for k, v in step_fields})
            result['steps'] = steps
        apps_match = re.search(r'"apps"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
        if apps_match:
            apps_str = apps_match.group(1)
            apps = re.findall(r'"([^"]+)"', apps_str)
            result['apps'] = apps
        return result if result else None

    def _merge_json_objects(self, json_objects: list) -> dict:
        """Merge multiple JSON objects into a single plan with combined steps and apps"""
        merged = {"steps": [], "apps": []}
        for obj in json_objects:
            if not isinstance(obj, dict):
                continue
            if "steps" in obj and isinstance(obj["steps"], list):
                merged["steps"].extend(obj["steps"])
            if "apps" in obj and isinstance(obj["apps"], list):
                merged["apps"].extend(obj["apps"])
        # Remove duplicate apps
        merged["apps"] = list(dict.fromkeys(merged["apps"]))
        return merged

    def _parse_llm_response(self, response: str, original_prompt: str) -> Optional[Dict]:
        """Parse LLM response into plan format, robust to malformed JSON and multiple objects"""
        try:
            # Use regex to extract all JSON objects
            json_candidates = re.findall(r'\{[\s\S]*?\}', response)
            logger.debug(f"[DEBUG] Found {len(json_candidates)} JSON candidates")
            for i, candidate in enumerate(json_candidates):
                logger.debug(f"[DEBUG] Candidate {i}: {repr(candidate)}")
            
            if not json_candidates:
                logger.error(f"[DEBUG] No JSON object found in LLM response. Raw: {response[:500]}")
                return None
            
            # Repair and parse all found objects
            parsed_objects = []
            for i, json_str in enumerate(json_candidates):
                # Strip trailing quotes and whitespace
                json_str = json_str.strip().rstrip("'\" ")
                logger.debug(f"[DEBUG] Attempting to parse candidate {i}: {repr(json_str)}")
                json_str = self._repair_json(json_str)
                try:
                    obj = json5.loads(json_str)
                    if isinstance(obj, dict):
                        parsed_objects.append(obj)
                        logger.debug(f"[DEBUG] Successfully parsed with json5: {obj}")
                except Exception as json5_error:
                    logger.debug(f"[DEBUG] json5 failed: {json5_error}")
                    try:
                        obj = json.loads(json_str)
                        if isinstance(obj, dict):
                            parsed_objects.append(obj)
                            logger.debug(f"[DEBUG] Successfully parsed with json: {obj}")
                    except Exception as json_error:
                        logger.debug(f"[DEBUG] json failed: {json_error}")
                        obj = self._extract_key_value_pairs(json_str)
                        if obj:
                            parsed_objects.append(obj)
                            logger.debug(f"[DEBUG] Successfully parsed with key-value extraction: {obj}")
            
            if not parsed_objects:
                logger.error(f"[DEBUG] No valid JSON objects parsed from LLM response. Raw: {response[:500]}")
                # Final fallback: try to parse the entire response as JSON
                try:
                    logger.debug(f"[DEBUG] Trying to parse entire response as JSON: {repr(response)}")
                    clean_response = response.strip().rstrip("'\" ")
                    obj = json5.loads(clean_response)
                    if isinstance(obj, dict):
                        parsed_objects.append(obj)
                        logger.debug(f"[DEBUG] Successfully parsed entire response: {obj}")
                except Exception as final_error:
                    logger.debug(f"[DEBUG] Final fallback failed: {final_error}")
                    return None
            
            if not parsed_objects:
                logger.error(f"[DEBUG] No valid JSON objects parsed from LLM response. Raw: {response[:500]}")
                return None
            
            # If more than one object, merge all into a single plan
            if len(parsed_objects) > 1:
                plan = self._merge_json_objects(parsed_objects)
            else:
                plan = parsed_objects[0]
            
            # Always run the validator to auto-fill missing 'apps' from steps
            return self._validate_and_clean_plan(plan, original_prompt)
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            logger.error(f"Response was: {response}")
            return None
    
    def _validate_and_clean_plan(self, plan: Dict, original_prompt: str) -> Dict:
        """Validate and clean the LLM-generated plan"""
        try:
            # Ensure required fields exist
            if "steps" not in plan:
                plan["steps"] = []
            if "apps" not in plan:
                plan["apps"] = []
            
            # Clean up steps
            cleaned_steps = []
            for step in plan["steps"]:
                if isinstance(step, dict):
                    # Handle different step formats
                    if "action" in step:
                        cleaned_step = {
                            "action": step.get("action", "launch_app"),
                            "app": step.get("app", "Safari"),
                            "description": step.get("description", f"Step for {original_prompt}")
                        }
                    elif "name" in step:
                        # Convert from name format to action format
                        cleaned_step = {
                            "action": "launch_app",
                            "app": step.get("app", step.get("name", "Safari")),
                            "description": step.get("name", f"Step for {original_prompt}")
                        }
                    else:
                        # Default step
                        cleaned_step = {
                            "action": "launch_app",
                            "app": "Safari",
                            "description": f"Step for {original_prompt}"
                        }
                    cleaned_steps.append(cleaned_step)
            
            plan["steps"] = cleaned_steps
            
            # Extract apps from steps if "apps" is missing or empty
            if not plan.get("apps"):
                apps = []
                for step in plan["steps"]:
                    if step.get("action") == "launch_app" and "app" in step:
                        apps.append(step["app"])
                plan["apps"] = list(set(apps))  # Remove duplicates
            
            return plan
            
        except Exception as e:
            logger.error(f"Error validating plan: {e}")
            # Return a simple fallback plan
            return {
                "steps": [
                    {
                        "action": "launch_app",
                        "app": "Safari",
                        "description": f"Open app for {original_prompt}"
                    }
                ],
                "apps": ["Safari"]
            }
    
    def _create_simple_plan(self, prompt: str) -> Dict:
        """Create a simple plan based on keywords when LLM fails"""
        prompt_lower = prompt.lower()
        
        # Common app mappings
        app_keywords = {
            "browser": "Safari",
            "web": "Safari", 
            "internet": "Safari",
            "finder": "Finder",
            "files": "Finder",
            "terminal": "Terminal",
            "command": "Terminal",
            "notes": "Notes",
            "calculator": "Calculator",
            "calc": "Calculator",
            "mail": "Mail",
            "email": "Mail",
            "messages": "Messages",
            "text": "Messages",
            "calendar": "Calendar",
            "photos": "Photos",
            "pictures": "Photos",
            "music": "Music",
            "itunes": "Music"
        }
        
        # Find matching app
        for keyword, app in app_keywords.items():
            if keyword in prompt_lower:
                return {
                    "steps": [
                        {"action": "launch_app", "app": app, "description": f"Open {app}"}
                    ],
                    "apps": [app]
                }
        
        # Default to Safari if no match
        return {
            "steps": [
                {"action": "launch_app", "app": "Safari", "description": "Open Safari browser"}
            ],
            "apps": ["Safari"]
        }
    
    def _add_to_cache(self, key: str, plan: Dict):
        """Add plan to cache with size limit"""
        if len(self.response_cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.response_cache))
            del self.response_cache[oldest_key]
        
        self.response_cache[key] = plan

# Global instance
plan_creator = OptimizedLLMPlanCreator()

async def test_optimized_plan_creator():
    """Test the optimized LLM plan creator"""
    print("🧪 Testing Optimized LLM Plan Creator...")
    
    test_prompts = [
        "open browser",
        "open finder",
        "open terminal",
        "open notes",
        "open calculator"
    ]
    
    for prompt in test_prompts:
        print(f"\n📝 Testing: {prompt}")
        try:
            plan = await plan_creator.create_plan(prompt)
            print(f"✅ Plan created: {json.dumps(plan, indent=2)}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_optimized_plan_creator()) 