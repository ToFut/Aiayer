#!/usr/bin/env python3
"""
Unified Application Detection System
Comprehensive solution for detecting any application type for SensAI.
Integrates with the memory system to provide application context.
"""
import os
import sys
import time
import json
import asyncio
import logging
import hashlib
import mss
import mss.tools
import base64
import re
from dataclasses import dataclass, asdict, field
from typing import Dict, Any, List, Optional, Union, Tuple
from PIL import Image
from io import BytesIO
import aiohttp
import threading

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/unified_app_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("unified_app_detection")

# Path constants
CACHE_DIR = "cache/app_detection"
RESULTS_DIR = "results/app_detection"

# Ensure directories exist
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

@dataclass
class ApplicationContext:
    """Structured data for application context"""
    app_name: str
    app_category: str = ""
    view_name: str = ""
    workflow: str = ""
    current_document: str = ""
    timestamp: float = field(default_factory=time.time)
    confidence: float = 0.0
    ui_elements: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationContext':
        """Create from dictionary"""
        return cls(**data)

class UnifiedAppDetectionSystem:
    """
    Unified application detection system that works with all application types.
    Integrates with the memory system and provides real-time application context.
    """
    
    def __init__(self, llava_url="http://localhost:11434"):
        self.llava_url = llava_url
        self.llava_endpoint = f"{llava_url}/api/chat"
        self.llava_model = "llava"
        self.llava_timeout = 60
        
        # Detection settings
        self.detection_interval = 5.0  # Seconds between detection runs
        self.min_confidence_threshold = 0.6  # Minimum confidence to accept detection
        self.change_threshold = 0.3  # Required confidence difference to register app change
        
        # Thread management
        self.running = False
        self.detection_thread = None
        self._stop_event = threading.Event()
        
        # State tracking
        self.current_context = None
        self.last_detection_time = 0
        self.detection_history = []
        self.max_history = 20
        
        # Capture settings
        try:
            self.sct = mss.mss()
            logger.info("Screen capture initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize screen capture: {e}")
            self.sct = None
        
        # Cache settings
        self.cache_file = f"{CACHE_DIR}/last_detection.json"
        self.load_cache()
        
        # Test LLaVA connection
        self._test_llava_connection()
        
        # Load enhanced app detector (assuming it's in the same directory)
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        try:
            from enhanced_app_detection import EnhancedAppDetector
            self.app_detector = EnhancedAppDetector(llava_url=llava_url)
            logger.info("Enhanced app detector loaded successfully")
        except ImportError:
            logger.error("Could not import EnhancedAppDetector, falling back to basic detection")
            self.app_detector = None
    
    def _test_llava_connection(self) -> bool:
        """Test connection to LLaVA service"""
        try:
            import requests
            response = requests.get(f"{self.llava_url}/api/version", timeout=2)
            if response.status_code == 200:
                logger.info(f"Successfully connected to Ollama API at {self.llava_url}")
                return True
            else:
                logger.warning(f"Failed to connect to Ollama API at {self.llava_url}: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Error connecting to LLaVA service: {e}")
            return False
    
    def load_cache(self):
        """Load previous detection results from cache"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    
                    # Convert to ApplicationContext
                    if data:
                        self.current_context = ApplicationContext.from_dict(data)
                        logger.info(f"Loaded previous detection from cache: {self.current_context.app_name}")
        except Exception as e:
            logger.warning(f"Failed to load detection cache: {e}")
    
    def save_cache(self):
        """Save current detection results to cache"""
        try:
            if self.current_context:
                with open(self.cache_file, 'w') as f:
                    json.dump(self.current_context.to_dict(), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save detection cache: {e}")
    
    def get_current_application_context(self) -> Optional[ApplicationContext]:
        """Get the current application context for external use"""
        return self.current_context
    
    def start(self):
        """Start the continuous application detection system"""
        if self.running:
            logger.warning("Application detection system is already running")
            return
            
        self.running = True
        self._stop_event.clear()
        
        logger.info("Starting unified application detection system")
        self.detection_thread = threading.Thread(target=self._detection_loop)
        self.detection_thread.daemon = True
        self.detection_thread.start()
        
        logger.info("Application detection system started")
    
    def stop(self):
        """Stop the continuous application detection system"""
        if not self.running:
            logger.warning("Application detection system is not running")
            return
            
        logger.info("Stopping application detection system")
        self._stop_event.set()
        self.running = False
        
        if self.detection_thread:
            self.detection_thread.join(timeout=10)
            if self.detection_thread.is_alive():
                logger.warning("Detection thread did not terminate cleanly")
                
        # Save final state to cache
        self.save_cache()
        
        # Clean up resources
        if self.sct:
            try:
                self.sct.close()
            except:
                pass
            
        logger.info("Application detection system stopped")
    
    def _detection_loop(self):
        """Main detection loop running in a background thread"""
        while not self._stop_event.is_set():
            try:
                # Check if it's time for a new detection
                current_time = time.time()
                if current_time - self.last_detection_time >= self.detection_interval:
                    # Capture screenshot
                    screenshot = self._capture_screenshot()
                    if screenshot:
                        # Call async detection in a separate thread
                        asyncio.run(self._process_screenshot(screenshot))
                        
                        # Update timing
                        self.last_detection_time = current_time
                    else:
                        logger.warning("Failed to capture screenshot")
                        
            except Exception as e:
                logger.error(f"Error in detection loop: {e}")
                
            # Sleep to avoid excessive CPU usage
            time.sleep(0.1)
    
    def _capture_screenshot(self) -> Optional[Image.Image]:
        """Capture the current screen"""
        try:
            if not self.sct:
                self.sct = mss.mss()
                
            # Get primary monitor
            primary_monitor = self.sct.monitors[1]  # Usually index 1 is the primary display
            
            # Capture screen
            screenshot = self.sct.grab(primary_monitor)
            
            # Convert to PIL Image
            image = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Track capture success
            logger.debug(f"Captured screenshot: {image.width}x{image.height}")
            return image
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
    
    async def _process_screenshot(self, screenshot: Image.Image):
        """Process the screenshot to detect application"""
        try:
            logger.info("Processing screenshot for application detection")
            
            # Save screenshot to temp file for detection
            temp_path = f"{CACHE_DIR}/temp_screenshot.jpg"
            screenshot.save(temp_path, format="JPEG", quality=85)
            
            # Use the EnhancedAppDetector if available
            detection_result = None
            
            if self.app_detector:
                try:
                    # Use the enhanced detector
                    detection_result = await self.app_detector.detect_application(temp_path)
                    
                    # Convert to ApplicationContext
                    context = ApplicationContext(
                        app_name=detection_result.application,
                        app_category=detection_result.category,
                        view_name=detection_result.view,
                        workflow=detection_result.workflow,
                        timestamp=time.time(),
                        confidence=detection_result.confidence,
                        ui_elements=[{"element": e.get("element", "")} for e in detection_result.ui_elements]
                    )
                except Exception as e:
                    logger.error(f"Error using enhanced detector: {e}")
                    detection_result = None
            
            # Fallback to basic detection if enhanced detection failed
            if not detection_result:
                try:
                    # Convert image to base64
                    img_byte_array = BytesIO()
                    screenshot.save(img_byte_array, format='JPEG', quality=85)
                    img_bytes = img_byte_array.getvalue()
                    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                    
                    # Use basic LLaVA analysis
                    llava_result = await self._analyze_with_llava(img_base64)
                    
                    # Extract basic info
                    app_info = self._parse_basic_llava_response(llava_result)
                    
                    # Create ApplicationContext
                    context = ApplicationContext(
                        app_name=app_info.get("application", "Unknown"),
                        app_category=app_info.get("category", ""),
                        view_name=app_info.get("view", ""),
                        workflow=app_info.get("workflow", ""),
                        timestamp=time.time(),
                        confidence=float(app_info.get("confidence", 0.3)),
                        ui_elements=[{"element": e.get("element", "")} for e in app_info.get("ui_elements", [])]
                    )
                except Exception as e:
                    logger.error(f"Error in basic detection fallback: {e}")
                    # If we have a previous context, keep using it
                    if self.current_context:
                        # Reduce confidence to reflect potential staleness
                        self.current_context.confidence *= 0.8
                        logger.info("Using previous context with reduced confidence")
                        return
                    else:
                        # Create unknown context if we have nothing else
                        context = ApplicationContext(
                            app_name="Unknown",
                            timestamp=time.time(),
                            confidence=0.1
                        )
            
            # Update context if significant change or higher confidence
            if self._should_update_context(context):
                logger.info(f"Application detected: {context.app_name} (confidence: {context.confidence:.2f})")
                if self.current_context:
                    logger.info(f"Previous application: {self.current_context.app_name}")
                
                # Record the change
                self._record_context_change(context)
                
                # Update current context
                self.current_context = context
                
                # Save to cache
                self.save_cache()
                
                # Save detection history
                self._update_detection_history(context)
                
                # Log detailed info
                logger.info(f"View: {context.view_name}")
                logger.info(f"Workflow: {context.workflow}")
                logger.info(f"UI Elements: {len(context.ui_elements)} detected")
            
        except Exception as e:
            logger.error(f"Error processing screenshot: {e}")
    
    def _should_update_context(self, new_context: ApplicationContext) -> bool:
        """Determine if the context should be updated based on confidence and changes"""
        # Always update if we don't have a current context
        if not self.current_context:
            return True
            
        # Check if confidence meets minimum threshold
        if new_context.confidence < self.min_confidence_threshold:
            logger.debug(f"New detection below confidence threshold: {new_context.confidence:.2f}")
            return False
            
        # If new detection is same app but higher confidence, update
        if (new_context.app_name == self.current_context.app_name and 
            new_context.confidence > self.current_context.confidence):
            return True
            
        # If different app, check if confidence difference is significant
        if new_context.app_name != self.current_context.app_name:
            confidence_diff = new_context.confidence - self.current_context.confidence
            if confidence_diff > self.change_threshold:
                return True
                
        # If same app but view changed significantly, update
        if (new_context.app_name == self.current_context.app_name and
            new_context.view_name != self.current_context.view_name and
            new_context.confidence > 0.7):
            return True
            
        # If same app but workflow changed significantly, update
        if (new_context.app_name == self.current_context.app_name and
            new_context.workflow != self.current_context.workflow and
            new_context.confidence > 0.7):
            return True
            
        return False
    
    def _record_context_change(self, new_context: ApplicationContext):
        """Record application context change for analysis"""
        if not self.current_context:
            return
            
        # Save the transition information
        transition = {
            "timestamp": time.time(),
            "from_app": self.current_context.app_name,
            "to_app": new_context.app_name,
            "from_view": self.current_context.view_name,
            "to_view": new_context.view_name,
            "from_confidence": self.current_context.confidence,
            "to_confidence": new_context.confidence
        }
        
        # Save to transitions file
        try:
            transitions_file = f"{RESULTS_DIR}/app_transitions.jsonl"
            with open(transitions_file, 'a') as f:
                f.write(json.dumps(transition) + '\n')
        except Exception as e:
            logger.warning(f"Failed to save transition record: {e}")
    
    def _update_detection_history(self, context: ApplicationContext):
        """Update detection history with new context"""
        # Add to history
        self.detection_history.append(context.to_dict())
        
        # Trim history if needed
        if len(self.detection_history) > self.max_history:
            self.detection_history = self.detection_history[-self.max_history:]
            
        # Save history to file
        try:
            history_file = f"{RESULTS_DIR}/detection_history.json"
            with open(history_file, 'w') as f:
                json.dump(self.detection_history, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save detection history: {e}")
    
    async def _analyze_with_llava(self, img_base64: str) -> str:
        """Analyze the image with LLaVA using the enhanced app detection prompt"""
        # Prepare the message for LLaVA with enhanced application detection prompt
        messages = [
            {
                "role": "system",
                "content": """You are an expert screen content analyzer specializing in application detection for ALL types of applications. Your primary goal is to accurately identify any application the user is using with as much detail as possible.

When given a screen capture:

1. IDENTIFY THE EXACT APPLICATION: Determine the specific application name (not just the category). Be specific - for example, say "Microsoft Word" not just "word processor" or "Visual Studio Code" not just "code editor".

2. Categorize the application type (productivity, communication, development, media, web browser, design, system, office, social media, utility)

3. Detect the specific view or mode within the application (e.g., inbox view in Gmail, editing mode in Word, repository view in GitHub)

4. Identify major UI components visible on screen

5. Determine what the user is doing - their current task or workflow stage

Respond with this exact format:
- APPLICATION: [Full application name]
- CATEGORY: [Application category]
- VIEW: [Current view/mode]
- WORKFLOW: [What the user is doing]
- UI ELEMENTS: [List key interface elements]"""
            },
            {
                "role": "user",
                "content": "What application am I using in this screenshot? Identify the exact application name, the current view, and what I appear to be doing."
            }
        ]
        
        # Prepare the payload
        payload = {
            "model": self.llava_model,
            "messages": messages,
            "images": [img_base64],
            "temperature": 0.2,
            "stream": True
        }
        
        logger.info("Sending request to LLaVA API for basic application detection...")
        
        try:
            # Send request to LLaVA
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.llava_endpoint,
                    json=payload,
                    timeout=self.llava_timeout
                ) as response:
                    logger.info(f"Received response status: {response.status}")
                    
                    if response.status != 200:
                        logger.error(f"LLaVA request failed with status {response.status}")
                        return f"Error: LLaVA request failed with status {response.status}"
                    
                    # Handle streaming response
                    full_response = ""
                    
                    # Process the streaming NDJSON response
                    logger.info("Processing streaming response...")
                    async for line in response.content:
                        try:
                            line_str = line.decode('utf-8').strip()
                            if not line_str:
                                continue
                                
                            # Parse the JSON
                            try:
                                chunk = json.loads(line_str)
                                if 'message' in chunk and 'content' in chunk['message']:
                                    content = chunk['message']['content']
                                    full_response += content
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse JSON: {line_str[:50]}...")
                        except Exception as e:
                            logger.warning(f"Error processing response line: {e}")
                            
                    return full_response
                    
        except asyncio.TimeoutError:
            logger.error(f"LLaVA request timed out after {self.llava_timeout}s")
            return "Error: LLaVA request timed out"
        except Exception as e:
            logger.error(f"Error in LLaVA analysis: {e}")
            return f"Error: {str(e)}"
    
    def _parse_basic_llava_response(self, response_text: str) -> Dict[str, Any]:
        """Parse the basic LLaVA response for application detection"""
        result = {
            "application": "Unknown",
            "confidence": 0.3,  # Default confidence level
            "category": "",
            "view": "",
            "workflow": "",
            "ui_elements": []
        }
        
        # Process the response with basic patterns
        try:
            # Extract application name
            app_match = re.search(r"APPLICATION:\s*([^\n]+)", response_text, re.IGNORECASE)
            if app_match:
                app_name = app_match.group(1).strip()
                if app_name and app_name.lower() not in ["unknown", "unclear", "not clear", "not visible"]:
                    result["application"] = app_name
                    result["confidence"] = 0.7  # Higher confidence for structured format
            
            # Extract category
            category_match = re.search(r"CATEGORY:\s*([^\n]+)", response_text, re.IGNORECASE)
            if category_match:
                category = category_match.group(1).strip()
                if category and category.lower() not in ["unknown", "unclear", "not clear", "not visible"]:
                    result["category"] = category
            
            # Extract view
            view_match = re.search(r"VIEW:\s*([^\n]+)", response_text, re.IGNORECASE)
            if view_match:
                view = view_match.group(1).strip()
                if view and view.lower() not in ["unknown", "unclear", "not clear", "not visible"]:
                    result["view"] = view
            
            # Extract workflow
            workflow_match = re.search(r"WORKFLOW:\s*([^\n]+)", response_text, re.IGNORECASE)
            if workflow_match:
                workflow = workflow_match.group(1).strip()
                if workflow and workflow.lower() not in ["unknown", "unclear", "not clear", "not visible"]:
                    result["workflow"] = workflow
            
            # Extract UI elements
            ui_elements = []
            ui_section_match = re.search(r"UI ELEMENTS:?\s*(.+?)(?:\n\n|\n[A-Z-]+:|\Z)", response_text, re.DOTALL | re.IGNORECASE)
            
            if ui_section_match:
                ui_text = ui_section_match.group(1).strip()
                
                # Split by list items (bullets, dashes, or numbers)
                if "-" in ui_text or "•" in ui_text or "*" in ui_text or re.search(r"\d+\.", ui_text):
                    element_lines = re.split(r"\n+", ui_text)
                    for line in element_lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        # Clean up bullet points and numbers
                        element = re.sub(r"^[\s•\-\*]+\s*", "", line)
                        element = re.sub(r"^\d+\.\s*", "", element)
                        
                        if element:
                            ui_elements.append({"element": element})
                else:
                    # If no bullet points, try comma-separated list
                    elements = [e.strip() for e in ui_text.split(",")]
                    for element in elements:
                        if element:
                            ui_elements.append({"element": element})
            
            result["ui_elements"] = ui_elements
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing LLaVA response: {e}")
            return result
    
    def get_application_history(self) -> List[Dict[str, Any]]:
        """Get the application detection history for analysis"""
        return self.detection_history
    
    async def manual_detection(self, image_path: str) -> ApplicationContext:
        """Run a manual detection on a specific image file"""
        try:
            logger.info(f"Running manual detection on image: {image_path}")
            
            # Use the EnhancedAppDetector if available
            if self.app_detector:
                try:
                    # Use the enhanced detector
                    detection_result = await self.app_detector.detect_application(image_path)
                    
                    # Convert to ApplicationContext
                    context = ApplicationContext(
                        app_name=detection_result.application,
                        app_category=detection_result.category,
                        view_name=detection_result.view,
                        workflow=detection_result.workflow,
                        timestamp=time.time(),
                        confidence=detection_result.confidence,
                        ui_elements=[{"element": e.get("element", "")} for e in detection_result.ui_elements]
                    )
                    
                    return context
                except Exception as e:
                    logger.error(f"Error using enhanced detector: {e}")
            
            # Fallback to basic detection
            # Load image
            image = Image.open(image_path)
            
            # Convert to base64
            img_byte_array = BytesIO()
            image.save(img_byte_array, format='JPEG', quality=85)
            img_bytes = img_byte_array.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            
            # Use basic LLaVA analysis
            llava_result = await self._analyze_with_llava(img_base64)
            
            # Extract basic info
            app_info = self._parse_basic_llava_response(llava_result)
            
            # Create ApplicationContext
            context = ApplicationContext(
                app_name=app_info.get("application", "Unknown"),
                app_category=app_info.get("category", ""),
                view_name=app_info.get("view", ""),
                workflow=app_info.get("workflow", ""),
                timestamp=time.time(),
                confidence=float(app_info.get("confidence", 0.3)),
                ui_elements=[{"element": e.get("element", "")} for e in app_info.get("ui_elements", [])]
            )
            
            return context
            
        except Exception as e:
            logger.error(f"Error in manual detection: {e}")
            return ApplicationContext(
                app_name="Error",
                timestamp=time.time(),
                confidence=0.0
            )

async def main():
    """Main function for running standalone detection"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unified Application Detection System")
    parser.add_argument("--image", help="Path to screenshot image for manual detection")
    parser.add_argument("--run", action="store_true", help="Run continuous detection service")
    parser.add_argument("--time", type=int, default=60, help="Run time in seconds for continuous detection (default: 60)")
    parser.add_argument("--interval", type=float, default=5.0, help="Detection interval in seconds (default: 5.0)")
    parser.add_argument("--llava-url", default="http://localhost:11434", help="URL for Ollama API (default: http://localhost:11434)")
    
    args = parser.parse_args()
    
    # Create detection system
    detector = UnifiedAppDetectionSystem(llava_url=args.llava_url)
    
    # If image path provided, run manual detection
    if args.image:
        print(f"Running manual detection on image: {args.image}")
        if not os.path.exists(args.image):
            print(f"Error: Image file '{args.image}' not found")
            return 1
            
        result = await detector.manual_detection(args.image)
        
        # Print formatted results
        print("\n===== DETECTION RESULTS =====")
        print(f"Application: {result.app_name}")
        print(f"Confidence:  {result.confidence:.2f}")
        print(f"Category:    {result.app_category}")
        print(f"View:        {result.view_name}")
        print(f"Workflow:    {result.workflow}")
        print("-----------------------------")
        print("UI Elements:")
        for ui in result.ui_elements:
            print(f"  - {ui['element']}")
        print("=============================")
        
    # If run flag provided, start continuous detection
    elif args.run:
        print(f"Starting continuous detection for {args.time} seconds")
        print(f"Detection interval: {args.interval} seconds")
        
        # Configure detection interval
        detector.detection_interval = args.interval
        
        # Start detection
        detector.start()
        
        # Run for specified time
        try:
            for i in range(args.time):
                await asyncio.sleep(1)
                if i % 5 == 0:  # Print status every 5 seconds
                    context = detector.get_current_application_context()
                    if context:
                        print(f"Current app: {context.app_name} (view: {context.view_name})")
        except KeyboardInterrupt:
            print("\nStopping detection due to user interrupt")
        finally:
            # Stop detection
            detector.stop()
            
        # Print detection summary
        history = detector.get_application_history()
        print("\n===== DETECTION SUMMARY =====")
        print(f"Total detections: {len(history)}")
        if history:
            apps = {}
            for entry in history:
                app = entry.get("app_name", "Unknown")
                apps[app] = apps.get(app, 0) + 1
                
            print("\nDetected applications:")
            for app, count in sorted(apps.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {app}: {count} times")
        print("=============================")
        
    else:
        parser.print_help()
    
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