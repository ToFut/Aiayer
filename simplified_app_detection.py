#!/usr/bin/env python3
"""
Simplified Application Detection
Direct integration with LLaVA for application detection.
"""
import os
import sys
import time
import json
import asyncio
import logging
import aiohttp
import base64
from PIL import Image
from io import BytesIO

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("app_detection")

class SimpleAppDetector:
    """Simplified application detector using LLaVA directly."""
    
    def __init__(self, llava_url="http://localhost:11434"):
        self.llava_url = llava_url
        self.llava_endpoint = f"{llava_url}/api/chat"
        self.llava_model = "llava"
        self.llava_timeout = 60
        self.running = False
        
    async def detect_application(self, image_path):
        """Detect application from an image file."""
        try:
            # Load the image
            logger.info(f"Loading image from {image_path}")
            image = Image.open(image_path)
            
            # Convert image to base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            # Prepare the message for LLaVA with application detection prompt
            messages = [
                {
                    "role": "system",
                    "content": """You are an expert screen content analyzer specializing in application-specific interface detection. When given a screen capture:

1. IMPORTANT: Identify which application the user is using (e.g., Gmail, Google Docs, Visual Studio Code, Slack, or a specific SaaS platform)
2. Detect specific views or modes within the application (e.g., inbox view, compose email, settings page, editing mode)
3. Identify UI components with their EXACT labels and functions (buttons, forms, navigation elements, dialogs)
4. Extract important text content visible on screen, especially from main content areas
5. Determine the USER'S EXACT task or workflow stage (e.g., "composing new email to sales@example.com", "editing document title", "reviewing code in function calculateTotal")"""
                },
                {
                    "role": "user",
                    "content": "What application am I using right now? Please identify it and describe what I'm doing in detail."
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
            
            logger.info("Sending request to LLaVA API...")
            start_time = time.time()
            
            # Send request to LLaVA
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.llava_endpoint,
                    json=payload,
                    timeout=self.llava_timeout
                ) as response:
                    logger.info(f"Received response status: {response.status}")
                    
                    # Handle streaming response
                    full_response = ""
                    try:
                        # Process the streaming NDJSON response
                        logger.info("Processing streaming response...")
                        async for line in response.content:
                            line_str = line.decode('utf-8').strip()
                            if not line_str:
                                continue
                                
                            # Log raw chunks for debugging
                            logger.debug(f"Raw chunk: {line_str[:50]}...")
                                
                            # Parse the JSON
                            try:
                                chunk = json.loads(line_str)
                                if 'message' in chunk and 'content' in chunk['message']:
                                    content = chunk['message']['content']
                                    full_response += content
                                    # Print partial responses for interactivity
                                    print(content, end="", flush=True)
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse JSON: {line_str[:50]}...")
                                
                        print("\n")  # New line after streaming completes
                        
                        elapsed_time = time.time() - start_time
                        logger.info(f"Full analysis completed in {elapsed_time:.2f} seconds")
                        
                        # Extract application data from response
                        app_name = self._extract_app_name(full_response)
                        app_view = self._extract_app_view(full_response)
                        workflow = self._extract_workflow(full_response)
                        
                        # Create structured result
                        result = {
                            "application": app_name,
                            "view": app_view,
                            "workflow": workflow,
                            "full_analysis": full_response,
                            "analysis_time": elapsed_time
                        }
                        
                        # Save the result
                        with open('logs/latest_detection.json', 'w') as f:
                            json.dump(result, f, indent=2)
                            
                        logger.info(f"Application detected: {app_name}")
                        logger.info(f"View: {app_view}")
                        logger.info(f"Workflow: {workflow}")
                        
                        return result
                        
                    except Exception as e:
                        logger.error(f"Error processing response: {e}")
                        return {"error": str(e)}
                        
        except Exception as e:
            logger.error(f"Error in detect_application: {e}")
            return {"error": str(e)}
            
    def _extract_app_name(self, text):
        """Extract application name from the LLaVA response."""
        app_name = "Unknown"
        
        # Look for common patterns indicating application name
        patterns = [
            r"Application:\s*([^\n\.]+)",
            r"The application (?:being used|shown|visible|displayed) is\s*([^\n\.]+)",
            r"You are using\s*([^\n\.]+)",
            r"This is\s*([^\n\.]+?)(?:\s+interface|application|app|website|\.|$)",
            r"I can see\s*(?:that\s*)?(?:you're using|you are using)?\s*([^\n\.]+)"
        ]
        
        for pattern in patterns:
            import re
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                app_name = match.group(1).strip()
                if app_name:
                    return app_name
        
        # If no patterns match, look for common application names
        common_apps = ["Gmail", "Google Docs", "Microsoft Word", "Visual Studio Code", "Slack", 
                      "Outlook", "Chrome", "Firefox", "Safari", "Excel", "PowerPoint", 
                      "Teams", "Zoom", "Terminal", "Command Prompt", "File Explorer"]
        
        for app in common_apps:
            if app.lower() in text.lower():
                return app
                
        return app_name
    
    def _extract_app_view(self, text):
        """Extract application view from the LLaVA response."""
        view = "Unknown view"
        
        # Look for common patterns indicating view
        patterns = [
            r"View:\s*([^\n\.]+)",
            r"Mode:\s*([^\n\.]+)",
            r"Page:\s*([^\n\.]+)",
            r"You are (?:in|on|viewing|at) the\s*([^\n\.]+?)(?:\s+view|mode|page|section|\.|$)",
            r"The (?:user|person) is (?:in|on|viewing|at) the\s*([^\n\.]+?)(?:\s+view|mode|page|section|\.|$)"
        ]
        
        for pattern in patterns:
            import re
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                view = match.group(1).strip()
                if view:
                    return view
        
        return view
    
    def _extract_workflow(self, text):
        """Extract workflow or user task from the LLaVA response."""
        workflow = "Unknown workflow"
        
        # Look for common patterns indicating workflow
        patterns = [
            r"Workflow:\s*([^\n\.]+)",
            r"Task:\s*([^\n\.]+)",
            r"The user is\s*([^\n\.]+?(?:ing|ing a|ing the)[^\n\.]+)",
            r"You are\s*([^\n\.]+?(?:ing|ing a|ing the)[^\n\.]+)",
            r"User task:\s*([^\n\.]+)"
        ]
        
        for pattern in patterns:
            import re
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                workflow = match.group(1).strip()
                if workflow:
                    return workflow
        
        return workflow

async def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python simplified_app_detection.py <screenshot_path>")
        print("Example: python simplified_app_detection.py screenshot.png")
        return
        
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: Image file '{image_path}' not found")
        return
    
    detector = SimpleAppDetector()
    print(f"Analyzing screenshot: {image_path}")
    print("Please wait while LLaVA processes the image...\n")
    
    result = await detector.detect_application(image_path)
    
    print("\n===== DETECTION RESULTS =====")
    print(f"Application: {result.get('application', 'Unknown')}")
    print(f"View: {result.get('view', 'Unknown')}")
    print(f"Workflow: {result.get('workflow', 'Unknown')}")
    print(f"Analysis time: {result.get('analysis_time', 0):.2f} seconds")
    print("=============================")
    print(f"\nDetailed results saved to logs/latest_detection.json")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript terminated by user")
    except Exception as e:
        print(f"Error: {e}")