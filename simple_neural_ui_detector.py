#!/usr/bin/env python3
"""
Simple Neural UI Detector - Lightweight version for testing

This module provides a simplified version of the Neural UI Detector that focuses
on basic screenshot-based UI detection without heavy neural network models.
"""

import os
import sys
import time
import json
import logging
import asyncio
import tempfile
import websockets
import base64
from PIL import Image, ImageDraw, ImageFont
import pyautogui
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Union

# Configure logging
os.makedirs('logs/neural_ui_detector', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/neural_ui_detector/simple_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("simple_neural_ui_detector")

@dataclass
class UIElement:
    """Represents a detected UI element"""
    id: str
    element_type: str
    bounding_box: List[int]  # [x1, y1, x2, y2]
    center: List[int]  # [x, y]
    confidence: float = 0.0
    text: str = ""
    detection_method: str = "simple"
    can_click: bool = True
    can_type: bool = False
    
    def __post_init__(self):
        """Validate and set defaults"""
        if not self.center and self.bounding_box:
            # Calculate center from bounding box
            x1, y1, x2, y2 = self.bounding_box
            self.center = [x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2]

@dataclass
class DetectionResult:
    """Result of UI element detection"""
    timestamp: float
    execution_time: float
    elements: List[UIElement] = field(default_factory=list)
    detection_methods: List[str] = field(default_factory=list)
    visualization_path: str = ""

class SimpleUIDetector:
    """Simple UI element detector using basic image processing"""
    
    def __init__(self):
        """Initialize the detector"""
        logger.info("Initializing Simple UI Detector")
        self.last_screenshot = None
        self.last_screenshot_time = 0
    
    async def take_screenshot(self) -> Image.Image:
        """Take a screenshot of the screen"""
        # Check if we have a recent screenshot (less than 1 second old)
        if self.last_screenshot and time.time() - self.last_screenshot_time < 1:
            logger.info("Using recent screenshot")
            return self.last_screenshot
        
        logger.info("Taking new screenshot")
        # Take a new screenshot
        screenshot = pyautogui.screenshot()
        self.last_screenshot = screenshot
        self.last_screenshot_time = time.time()
        return screenshot
    
    async def detect_elements(self) -> DetectionResult:
        """Detect UI elements on the screen using simple methods"""
        start_time = time.time()
        
        # Take a screenshot
        screenshot = await self.take_screenshot()
        
        # For simplicity, we'll create some mock elements
        # In a real implementation, you'd perform actual detection here
        elements = []
        
        # Simulate a few common UI elements
        # Button in top right
        elements.append(UIElement(
            id="button_1",
            element_type="button",
            bounding_box=[screenshot.width - 150, 50, screenshot.width - 50, 100],
            center=[screenshot.width - 100, 75],
            confidence=0.95,
            text="Submit",
            detection_method="simple"
        ))
        
        # Text input in middle
        elements.append(UIElement(
            id="text_input_1",
            element_type="text_input",
            bounding_box=[100, screenshot.height // 2 - 25, 400, screenshot.height // 2 + 25],
            center=[250, screenshot.height // 2],
            confidence=0.92,
            text="",
            detection_method="simple",
            can_type=True
        ))
        
        # Checkbox
        elements.append(UIElement(
            id="checkbox_1",
            element_type="checkbox",
            bounding_box=[50, screenshot.height - 150, 70, screenshot.height - 130],
            center=[60, screenshot.height - 140],
            confidence=0.88,
            text="Remember me",
            detection_method="simple"
        ))
        
        # Create result
        result = DetectionResult(
            timestamp=time.time(),
            execution_time=time.time() - start_time,
            elements=elements,
            detection_methods=["simple"]
        )
        
        return result
    
    def visualize_detection(self, result: DetectionResult) -> str:
        """Create a visualization of the detection result"""
        # Take a new screenshot or use the last one
        if self.last_screenshot:
            screenshot = self.last_screenshot.copy()
        else:
            screenshot = pyautogui.screenshot()
        
        # Draw bounding boxes and labels
        draw = ImageDraw.Draw(screenshot)
        try:
            font = ImageFont.truetype("Arial.ttf", 14)
        except IOError:
            font = ImageFont.load_default()
        
        # Draw each element
        for elem in result.elements:
            # Get bounding box
            x1, y1, x2, y2 = elem.bounding_box
            
            # Choose color based on element type
            color_map = {
                "button": (255, 0, 0),    # Red
                "text_input": (0, 255, 0), # Green
                "checkbox": (0, 0, 255),   # Blue
                "default": (255, 255, 0)    # Yellow
            }
            color = color_map.get(elem.element_type, color_map["default"])
            
            # Draw rectangle
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            
            # Draw label
            label = f"{elem.element_type}: {elem.text}" if elem.text else elem.element_type
            draw.text((x1, y1 - 15), label, fill=color, font=font)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            screenshot.save(tmp.name)
            result.visualization_path = tmp.name
            return tmp.name

# Create global detector instance
ui_detector = SimpleUIDetector()

# Connected clients
connected_clients = set()

# Latest detection result cache
latest_detection = None
last_detection_time = 0

async def handle_client(websocket, path=None):
    """Handle WebSocket client connection"""
    client_id = id(websocket)
    logger.info(f"Client {client_id} connected")
    connected_clients.add(websocket)
    
    # Send welcome message
    welcome_msg = {
        "type": "welcome",
        "message": "Connected to Simple Neural UI Detector",
        "version": "1.0.0",
        "capabilities": ["detect", "visualize"]
    }
    await websocket.send(json.dumps(welcome_msg))
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                action = data.get("action", "")
                logger.info(f"Received message from client {client_id}: {action}")
                
                # Process command
                response = await process_command(data)
                
                # Send response
                await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}: {message}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": "Invalid JSON"
                }))
                
            except Exception as e:
                logger.error(f"Error processing message from client {client_id}: {str(e)}")
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": str(e)
                }))
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    
    finally:
        connected_clients.remove(websocket)

async def process_command(data):
    """Process command from client"""
    global latest_detection, last_detection_time
    
    action = data.get("action", "")
    
    try:
        if action == "detect":
            # Check if we have a recent detection (less than 5 seconds old)
            if latest_detection and time.time() - last_detection_time < 5:
                logger.info("Using recent detection result")
                result = latest_detection
            else:
                # Perform new detection
                logger.info("Performing new detection")
                result = await ui_detector.detect_elements()
                latest_detection = result
                last_detection_time = time.time()
            
            # Create visualization
            vis_path = ui_detector.visualize_detection(result)
            
            # Convert elements to serializable format
            elements = []
            for elem in result.elements:
                elem_data = {
                    "id": elem.id,
                    "element_type": elem.element_type,
                    "confidence": elem.confidence,
                    "bounding_box": elem.bounding_box,
                    "center": elem.center,
                    "text": elem.text,
                    "detection_method": elem.detection_method
                }
                elements.append(elem_data)
            
            # Read visualization image if available
            vis_image = None
            if vis_path and os.path.exists(vis_path):
                try:
                    with open(vis_path, "rb") as f:
                        vis_data = f.read()
                        vis_image = base64.b64encode(vis_data).decode('utf-8')
                except Exception as e:
                    logger.error(f"Error reading visualization image: {e}")
            
            return {
                "type": "detection_result",
                "timestamp": result.timestamp,
                "count": len(result.elements),
                "methods": result.detection_methods,
                "execution_time": result.execution_time,
                "elements": elements,
                "visualization": vis_image
            }
        
        else:
            return {
                "type": "error",
                "error": f"Unknown action: {action}"
            }
    
    except Exception as e:
        logger.error(f"Error processing action '{action}': {str(e)}")
        return {
            "type": "error",
            "error": str(e)
        }

async def start_server(port=8768):
    """Start WebSocket server"""
    logger.info(f"Starting Simple Neural UI Detector WebSocket Server on port {port}")
    
    server = await websockets.serve(handle_client, "localhost", port)
    
    # Print status with prominent visual separator
    print("\n" + "=" * 70)
    print(f"🚀 Simple Neural UI Detector WebSocket Server running on ws://localhost:{port}")
    print("=" * 70 + "\n")
    
    # Write port to file for discovery
    with open('neural_ui_detector_port.txt', 'w') as f:
        f.write(str(port))
    
    await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        # Get port from command line
        port = int(sys.argv[1]) if len(sys.argv) > 1 else 8768
        
        # Start server
        asyncio.run(start_server(port))
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        print(f"\nError: {str(e)}")