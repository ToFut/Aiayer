#!/usr/bin/env python3
"""
LLaVA Visual Processor Module
Processes screen captures with LLaVA for rich visual understanding.
Provides detailed analysis of application context, UI elements, and user activities.
"""
import os
import logging
import json
import base64
import asyncio
import aiohttp
import traceback
import time
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from io import BytesIO
from PIL import Image

# Configure logging
os.makedirs('logs/llm', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/llm/llava_processor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('llava_processor')

class LLaVAVisualProcessor:
    """
    Processes screen captures with LLaVA for rich visual understanding.
    
    Features:
    - Detailed application context detection
    - UI element identification
    - User workflow and task analysis
    - Foreground vs background process classification
    """
    
    def __init__(self, ollama_url="http://localhost:11434"):
        self.ollama_url = ollama_url
        self.llava_endpoint = f"{ollama_url}/api/chat"
        self.llava_model = "llava:latest"  # Default model name
        self.fallback_model = "llava"  # Fallback model name
        self.max_retries = 3
        self.timeout = 60  # Default timeout in seconds
        self.last_request_time = 0
        self.request_rate_limit = 1.0  # Minimum seconds between requests
        self.cache_dir = "cache/llava_processor"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # System process patterns to identify background processes
        self.system_process_patterns = [
            "helper", "agent", "daemon", "service", "system", "update", "background",
            "launcher", "monitor", "manager", "assistant", "worker", "controller",
            "sync", "extension", "cache", "finder", "plugin"
        ]
        
        # Initialize the service connection
        self.initialized = False
        self.version_check()
        
    def version_check(self):
        """Check if LLaVA is available and get API version"""
        try:
            import requests
            response = requests.get(f"{self.ollama_url}/api/version", timeout=2)
            if response.status_code == 200:
                version_info = response.json()
                logger.info(f"Connected to Ollama API v{version_info.get('version', 'unknown')}")
                self.initialized = True
            else:
                logger.warning(f"Failed to connect to Ollama API: {response.status_code}")
                self.initialized = False
        except Exception as e:
            logger.warning(f"Error checking LLaVA availability: {e}")
            self.initialized = False
        return self.initialized
            
    async def analyze_screen(self, image: Union[Image.Image, bytes, str], 
                             context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze screen content with LLaVA to get detailed visual understanding.
        
        Args:
            image: PIL Image, bytes, or base64 string of the screen capture
            context: Optional context about processes, etc.
            
        Returns:
            Dict with analysis results including application, UI elements, and user activity
        """
        if not self.initialized and not self.version_check():
            logger.error("LLaVA service not available")
            return self._create_error_response("LLaVA service not available")
            
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_rate_limit:
            await asyncio.sleep(self.request_rate_limit - time_since_last)
        
        # Normalize image to base64 string
        try:
            image_base64 = self._normalize_image(image)
            if not image_base64:
                return self._create_error_response("Failed to process image")
        except Exception as e:
            logger.error(f"Error normalizing image: {e}")
            return self._create_error_response(f"Error processing image: {str(e)}")
            
        # Create image hash for caching
        image_hash = self._hash_image(image_base64)
        
        # Check cache for recent result
        cached_result = self._check_cache(image_hash)
        if cached_result:
            logger.info(f"Using cached LLaVA analysis for image {image_hash[:8]}")
            return cached_result
            
        # Prepare prompt with application-specific context
        prompt = self._create_analysis_prompt(context)
        
        # Send request to LLaVA
        logger.info(f"Sending image for LLaVA analysis (hash: {image_hash[:8]})")
        analysis = await self._request_llava_analysis(image_base64, prompt)
        
        # Add timestamp and image hash
        analysis["timestamp"] = datetime.now().isoformat()
        analysis["image_hash"] = image_hash
        
        # Update context with process classification if available
        if context and "processes" in context:
            process_classification = self.classify_processes(context["processes"])
            analysis["process_classification"] = process_classification
            
            # Enhance context understanding with process info
            if "foreground" in process_classification and process_classification["foreground"]:
                foreground_app = process_classification["foreground"][0] if process_classification["foreground"] else "Unknown"
                if "application" in analysis and isinstance(analysis["application"], dict):
                    # Update application name if LLaVA didn't detect it
                    if not analysis["application"].get("name") or analysis["application"].get("name") == "unknown":
                        analysis["application"]["name"] = foreground_app
                        
        # Cache the result
        self._cache_result(image_hash, analysis)
        
        # Update rate limit tracking
        self.last_request_time = time.time()
        
        logger.info(f"Completed LLaVA analysis: {len(json.dumps(analysis))} bytes")
        return analysis
            
    def _normalize_image(self, image: Union[Image.Image, bytes, str]) -> Optional[str]:
        """Convert various image formats to base64 string"""
        try:
            if isinstance(image, Image.Image):
                # Convert PIL Image to base64
                buffer = BytesIO()
                image.save(buffer, format="JPEG", quality=85)
                image_bytes = buffer.getvalue()
                return base64.b64encode(image_bytes).decode("utf-8")
                
            elif isinstance(image, bytes):
                # Convert bytes to base64
                return base64.b64encode(image).decode("utf-8")
                
            elif isinstance(image, str):
                # Check if already base64
                try:
                    # Try to decode to validate it's base64
                    base64.b64decode(image)
                    # If no exception, assume it's already a valid base64 string
                    return image
                except:
                    # Not a valid base64 string, might be a file path
                    if os.path.exists(image):
                        with open(image, "rb") as f:
                            image_bytes = f.read()
                            return base64.b64encode(image_bytes).decode("utf-8")
            
            logger.error(f"Unsupported image type: {type(image)}")
            return None
        except Exception as e:
            logger.error(f"Error normalizing image: {e}")
            return None
            
    def _hash_image(self, image_base64: str) -> str:
        """Create a hash of the image for caching"""
        import hashlib
        return hashlib.md5(image_base64.encode()).hexdigest()
        
    def _check_cache(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Check if we have a cached analysis for this image hash"""
        cache_file = os.path.join(self.cache_dir, f"{image_hash}.json")
        
        if os.path.exists(cache_file):
            # Check if cache is recent (less than 5 minutes old)
            if time.time() - os.path.getmtime(cache_file) < 300:
                try:
                    with open(cache_file, "r") as f:
                        return json.load(f)
                except Exception as e:
                    logger.warning(f"Error reading cache file: {e}")
        
        return None
        
    def _cache_result(self, image_hash: str, result: Dict[str, Any]) -> None:
        """Cache the analysis result"""
        cache_file = os.path.join(self.cache_dir, f"{image_hash}.json")
        try:
            with open(cache_file, "w") as f:
                json.dump(result, f)
            logger.debug(f"Cached LLaVA analysis for {image_hash[:8]}")
        except Exception as e:
            logger.warning(f"Error caching result: {e}")
        
    def _create_analysis_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Create a detailed prompt for LLaVA based on context"""
        prompt = """You are an expert screen content analyzer specializing in application-specific interface detection. 
Be extremely detailed and specific about what you see.

Follow these steps when analyzing this screen capture:

1. Identify the application: What specific application is the user using? (e.g., Gmail, Visual Studio Code, Slack)

2. Identify the application view/mode: What specific view or mode is shown? (e.g., compose email, code editor, settings page)

3. Identify the user's workflow stage: What EXACT task is the user currently performing? Be specific about content.

4. Identify UI elements: List important interactive elements visible on screen with their exact labels.

5. Extract key text content: Note important text visible on screen, especially from main content areas.

For known application types, provide these additional details:
- Email client: Sender/recipient information, subject lines, email content
- Code editor: File names, code language, function or class being edited
- Document editor: Document title, document type, content being edited
- Browser: Website URL, page title, primary content
- Chat/messaging: Conversation participants, message content

Important: Be extremely precise and detailed. Avoid generic descriptions. Extract specific names, content, and details that identify exactly what the user is doing and seeing.
"""
        
        # Add process context if available
        if context and "processes" in context:
            process_info = self.classify_processes(context["processes"])
            if process_info and "foreground" in process_info and process_info["foreground"]:
                prompt += f"\n\nThe following application appears to be in the foreground: {process_info['foreground'][0]}"
        
        return prompt
    
    async def _request_llava_analysis(self, image_base64: str, prompt: str) -> Dict[str, Any]:
        """Send request to LLaVA with error handling and retries"""
        retry_count = 0
        base_delay = 1.0
        
        while retry_count <= self.max_retries:
            try:
                # Prepare message for LLaVA
                messages = [
                    {
                        "role": "system",
                        "content": """You are an expert screen content analyzer that identifies applications, 
UI elements, and user activities with extreme precision and detail."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
                
                # Prepare request payload
                payload = {
                    "model": self.llava_model,
                    "messages": messages,
                    "images": [image_base64],
                    "temperature": 0.2,  # Low temperature for more factual analysis
                    "max_tokens": 1024
                }
                
                # Log the request
                logger.info(f"Sending LLaVA request (attempt {retry_count + 1}/{self.max_retries + 1})")
                
                # Make request with timeout
                timeout = min(self.timeout * (retry_count + 1), 120)  # Increase timeout with retries, max 120s
                
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.post(
                            self.llava_endpoint,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=timeout, connect=10, sock_read=30)
                        ) as response:
                            if response.status != 200:
                                error_text = await response.text()
                                logger.warning(f"LLaVA request failed with status {response.status}: {error_text}")
                                
                                # Try fallback model if the main one fails
                                if self.llava_model != self.fallback_model:
                                    logger.info(f"Trying fallback model: {self.fallback_model}")
                                    self.llava_model = self.fallback_model
                                    continue
                                
                                # Increment retry counter and apply exponential backoff
                                retry_count += 1
                                if retry_count <= self.max_retries:
                                    delay = base_delay * (2 ** (retry_count - 1))  # Exponential backoff
                                    logger.info(f"Retrying in {delay} seconds...")
                                    await asyncio.sleep(delay)
                                    continue
                                
                                # All retries failed
                                return self._create_error_response(f"LLaVA request failed after {self.max_retries} retries: {response.status}")
                            
                            # Parse the response
                            full_response = ""
                            try:
                                # Handle streaming NDJSON response
                                async for line in response.content:
                                    if not line.strip():
                                        continue
                                    
                                    # Parse the line as JSON
                                    try:
                                        chunk = json.loads(line)
                                        if isinstance(chunk, dict):
                                            if 'message' in chunk and 'content' in chunk['message']:
                                                full_response += chunk['message']['content']
                                            elif 'response' in chunk:
                                                full_response += chunk['response']
                                            elif 'content' in chunk:
                                                full_response += chunk['content']
                                    except json.JSONDecodeError:
                                        pass
                                
                                # Check if we received a response
                                if not full_response:
                                    logger.warning("Empty response from LLaVA")
                                    retry_count += 1
                                    if retry_count <= self.max_retries:
                                        delay = base_delay * (2 ** (retry_count - 1))
                                        logger.info(f"Retrying in {delay} seconds...")
                                        await asyncio.sleep(delay)
                                        continue
                                    
                                    return self._create_error_response("Empty response from LLaVA")
                                
                                # Parse the LLaVA response
                                analysis = self._parse_llava_response(full_response)
                                logger.info(f"Successfully parsed LLaVA response: {len(analysis.keys())} fields")
                                return analysis
                                
                            except asyncio.TimeoutError:
                                logger.warning(f"Timeout while reading LLaVA response")
                                if full_response:
                                    # Use partial response if available
                                    logger.info(f"Using partial response: {len(full_response)} chars")
                                    analysis = self._parse_llava_response(full_response)
                                    return analysis
                                    
                                retry_count += 1
                                if retry_count <= self.max_retries:
                                    delay = base_delay * (2 ** (retry_count - 1))
                                    logger.info(f"Retrying in {delay} seconds...")
                                    await asyncio.sleep(delay)
                                    continue
                                
                                return self._create_error_response("Timeout reading LLaVA response")
                                
                    except asyncio.TimeoutError:
                        logger.warning(f"Request timeout")
                        retry_count += 1
                        if retry_count <= self.max_retries:
                            delay = base_delay * (2 ** (retry_count - 1))
                            logger.info(f"Retrying in {delay} seconds...")
                            await asyncio.sleep(delay)
                            continue
                        
                        return self._create_error_response("Request timeout")
                        
                    except Exception as e:
                        logger.error(f"Error in LLaVA request: {e}")
                        logger.error(traceback.format_exc())
                        retry_count += 1
                        if retry_count <= self.max_retries:
                            delay = base_delay * (2 ** (retry_count - 1))
                            logger.info(f"Retrying in {delay} seconds...")
                            await asyncio.sleep(delay)
                            continue
                        
                        return self._create_error_response(f"Error in LLaVA request: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error in LLaVA analysis: {e}")
                logger.error(traceback.format_exc())
                retry_count += 1
                if retry_count <= self.max_retries:
                    delay = base_delay * (2 ** (retry_count - 1))
                    logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    continue
                
                return self._create_error_response(f"Error in LLaVA analysis: {str(e)}")
        
        # All retries failed
        return self._create_error_response(f"LLaVA analysis failed after {self.max_retries + 1} attempts")
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create a response for error conditions"""
        logger.error(error_message)
        return {
            "error": error_message,
            "llava_description": "",
            "screen_elements": [],
            "visual_context": "",
            "application": {
                "name": "unknown",
                "view": "",
                "workflow_stage": ""
            },
            "timestamp": datetime.now().isoformat()
        }
        
    def _parse_llava_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLaVA's response into structured data with application-specific understanding
        """
        try:
            # Initial response container
            parsed_data = {
                "llava_description": response,
                "screen_elements": [],
                "visual_context": "",
                "application": {
                    "name": "unknown",
                    "state": "",
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
                "text_content": []
            }
            
            # Process response for cleaner structure
            lines = response.split('\n')
            
            # Extract information using patterns
            current_section = None
            ui_elements = []
            application_info = {"name": "unknown", "state": "", "workflow_stage": ""}
            visual_context_parts = []
            user_activity = {"current_task": "", "workflow_stage": "", "interaction_points": []}
            visual_content = {"main_content": "", "text_content": [], "images": []}
            text_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                line_lower = line.lower()
                
                # Check for application information
                if "application:" in line_lower or "app:" in line_lower:
                    parts = line.split(":", 1)
                    if len(parts) > 1 and parts[1].strip():
                        application_info["name"] = parts[1].strip()
                
                # Check for view/mode/state information
                elif any(mode in line_lower for mode in ["view:", "mode:", "page:", "state:"]):
                    for prefix in ["view:", "mode:", "page:", "state:"]:
                        if prefix in line_lower:
                            parts = line.split(":", 1)
                            if len(parts) > 1 and parts[1].strip():
                                application_info["state"] = parts[1].strip()
                                break
                
                # Check for workflow/task information
                elif any(task in line_lower for task in ["workflow:", "task:", "user is", "user's task"]):
                    # This is very important info about what the user is doing
                    for prefix in ["workflow:", "task:", "user is", "user's task:"]:
                        if prefix in line_lower:
                            idx = line_lower.find(prefix)
                            end_prefix = idx + len(prefix)
                            workflow = line[end_prefix:].strip()
                            if workflow:
                                application_info["workflow_stage"] = workflow
                                user_activity["current_task"] = workflow
                                user_activity["workflow_stage"] = workflow
                                break
                
                # Check for UI elements
                elif "ui element" in line_lower or "interface element" in line_lower:
                    current_section = "ui_elements"
                    continue
                elif current_section == "ui_elements" and (line.startswith("-") or line.startswith("*") or (line[0].isdigit() and line[1:].startswith("."))):
                    # Parse UI element
                    element_text = line[1:].strip() if line.startswith("-") or line.startswith("*") else line[line.find(".")+1:].strip()
                    
                    # Try to determine element type
                    element_type = "unknown"
                    if "button" in element_text.lower():
                        element_type = "button"
                    elif any(input_type in element_text.lower() for input_type in ["input", "field", "text box", "textbox"]):
                        element_type = "input_field"
                    elif "menu" in element_text.lower() or "dropdown" in element_text.lower():
                        element_type = "menu"
                    elif "link" in element_text.lower():
                        element_type = "link"
                    elif "checkbox" in element_text.lower():
                        element_type = "checkbox"
                    elif "tab" in element_text.lower():
                        element_type = "tab"
                    
                    ui_element = {
                        "element": element_text,
                        "type": element_type,
                        "name": element_text
                    }
                    ui_elements.append(ui_element)
                    user_activity["interaction_points"].append(ui_element)
                
                # Check for text content
                elif any(text_indicator in line_lower for text_indicator in ["text:", "content:", "message:"]):
                    text_content.append(line)
                    visual_content["text_content"].append(line)
                
                # Check for main content
                elif "main content" in line_lower or "primary content" in line_lower:
                    parts = line.split(":", 1)
                    if len(parts) > 1 and parts[1].strip():
                        visual_content["main_content"] = parts[1].strip()
                
                # Add to visual context if not processed otherwise
                visual_context_parts.append(line)
            
            # Update parsed data with structured format
            parsed_data = {
                "application": application_info,
                "ui_elements": ui_elements,
                "user_activity": user_activity,
                "visual_content": visual_content,
                "text_content": text_content,
                "visual_context": "\n".join(visual_context_parts),
                "llava_description": response,
                "screen_elements": ui_elements,  # Use UI elements as screen elements
                "timestamp": datetime.now().isoformat()
            }
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing LLaVA response: {e}")
            logger.error(traceback.format_exc())
            return {
                "application": {
                    "name": "unknown",
                    "state": "",
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
                "visual_context": "",
                "llava_description": response,
                "screen_elements": [],
                "timestamp": datetime.now().isoformat(),
                "parse_error": str(e)
            }
    
    def classify_processes(self, processes_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Classify processes into foreground, supporting, and background categories.
        
        Args:
            processes_data: List of process dictionaries with name, pid, etc.
            
        Returns:
            Dict with foreground, supporting, and background processes
        """
        active_window = None
        active_app = None
        all_processes = []
        
        # Normalize processes data
        for proc in processes_data:
            if isinstance(proc, dict):
                proc_name = proc.get("name", "")
                pid = proc.get("pid", 0)
                if proc_name:
                    all_processes.append(proc_name)
                    
                    # Look for indicators this is the active window
                    if proc.get("is_active", False) or proc.get("active", False) or proc.get("foreground", False):
                        active_app = proc_name
                        active_window = proc.get("window_title", "")
        
        # If no active app was explicitly marked, use heuristics
        if not active_app and all_processes:
            # Exclude likely background processes
            foreground_candidates = [
                proc for proc in all_processes 
                if not any(pattern in proc.lower() for pattern in self.system_process_patterns)
            ]
            if foreground_candidates:
                active_app = foreground_candidates[0]  # Just use the first non-system process
        
        # Categorize processes
        foreground = []
        supporting = []
        background = []
        
        # Add active app to foreground
        if active_app:
            foreground.append(active_app)
            
        # Classify remaining processes
        for proc_name in all_processes:
            # Skip if already added to foreground
            if proc_name == active_app:
                continue
                
            # Check if this is a supporting process for the active app
            if active_app and (
                active_app.lower() in proc_name.lower() or 
                proc_name.lower() in active_app.lower() or
                any(helper in proc_name.lower() for helper in ["helper", "renderer", "gpu", "plugin"])
            ):
                supporting.append(proc_name)
            # Check if this is a system process
            elif any(pattern in proc_name.lower() for pattern in self.system_process_patterns):
                background.append(proc_name)
            # Otherwise add to background apps
            else:
                background.append(proc_name)
        
        return {
            "foreground": foreground,
            "supporting": supporting,
            "background": background,
            "active_window": active_window,
            "active_app": active_app
        }

# Main function for testing
async def main():
    """Test function for LLaVA processor"""
    processor = LLaVAVisualProcessor()
    
    # Test with a sample image
    sample_image_path = "sample.png"
    if os.path.exists(sample_image_path):
        print(f"Processing image: {sample_image_path}")
        result = await processor.analyze_screen(sample_image_path)
        print(json.dumps(result, indent=2))
    else:
        print(f"Sample image not found: {sample_image_path}")
        
        # Test with dummy processes
        dummy_processes = [
            {"name": "Chrome", "pid": 1234, "is_active": True},
            {"name": "Chrome Helper", "pid": 1235},
            {"name": "Chrome GPU Helper", "pid": 1236},
            {"name": "Finder", "pid": 100},
            {"name": "SystemUIServer", "pid": 101}
        ]
        
        process_classification = processor.classify_processes(dummy_processes)
        print("Process classification:")
        print(json.dumps(process_classification, indent=2))

if __name__ == "__main__":
    asyncio.run(main())