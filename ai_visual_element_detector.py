#!/usr/bin/env python3
"""
AI Visual Element Detector - Uses LLaVA to analyze screenshots and identify UI elements with precise coordinates
"""

import pyautogui
import subprocess
import time
import json
import logging
import base64
import io
import requests
from typing import Tuple, Dict, Optional, List
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class UIElement:
    """Represents a detected UI element"""
    element_type: str  # 'text_input', 'button', 'search_box', 'text_area'
    coordinates: Tuple[int, int]
    confidence: float
    description: str
    bounds: Tuple[int, int, int, int]  # x1, y1, x2, y2

class AIVisualElementDetector:
    """Uses AI vision to detect and locate UI elements on screen"""
    
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()
        self.ollama_url = "http://localhost:11434/api/generate"
        logger.info(f"AI Visual Element Detector initialized for {self.screen_width}x{self.screen_height}")
    
    def take_screenshot(self) -> Image.Image:
        """Take a screenshot for analysis"""
        return pyautogui.screenshot()
    
    def encode_image_for_llava(self, image: Image.Image) -> str:
        """Encode image for LLaVA analysis"""
        # Resize image for faster processing while maintaining aspect ratio
        max_size = 1024
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def analyze_ui_elements_with_llava(self, image: Image.Image, target_description: str) -> List[UIElement]:
        """Use LLaVA to analyze UI elements and their locations"""
        
        image_b64 = self.encode_image_for_llava(image)
        
        # Craft prompt for precise UI element detection
        prompt = f"""Analyze this screenshot and identify UI elements that match: "{target_description}"

Look for:
1. Text input fields/search boxes
2. Text areas for typing
3. Buttons
4. Any clickable elements related to the task

For each relevant element, provide:
- Element type (text_input, search_box, text_area, button)
- Approximate pixel coordinates (x, y) from the top-left corner
- Confidence level (0.0-1.0)
- Brief description

Respond in JSON format:
{{
  "elements": [
    {{
      "type": "search_box",
      "x": 735,
      "y": 250,
      "confidence": 0.9,
      "description": "Google search input field"
    }}
  ]
}}

Focus on elements that are actually visible and clickable for the task: "{target_description}"
"""

        try:
            response = requests.post(self.ollama_url, json={
                "model": "llava",
                "prompt": prompt,
                "images": [image_b64],
                "stream": False
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')
                
                # Parse JSON response
                try:
                    # Extract JSON from response
                    json_start = response_text.find('{')
                    json_end = response_text.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = response_text[json_start:json_end]
                        data = json.loads(json_str)
                        
                        elements = []
                        for elem in data.get('elements', []):
                            ui_element = UIElement(
                                element_type=elem.get('type', 'unknown'),
                                coordinates=(elem.get('x', 0), elem.get('y', 0)),
                                confidence=elem.get('confidence', 0.5),
                                description=elem.get('description', ''),
                                bounds=(elem.get('x', 0) - 50, elem.get('y', 0) - 25,
                                       elem.get('x', 0) + 50, elem.get('y', 0) + 25)
                            )
                            elements.append(ui_element)
                        
                        logger.info(f"🔍 LLaVA detected {len(elements)} UI elements for '{target_description}'")
                        return elements
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLaVA JSON response: {e}")
                    logger.debug(f"Raw response: {response_text}")
            
        except Exception as e:
            logger.error(f"LLaVA analysis failed: {e}")
        
        return []
    
    def get_smart_coordinates_for_action(self, action_description: str, step_type: str = "unknown") -> Tuple[int, int]:
        """Get smart coordinates using AI visual analysis"""
        
        logger.info(f"🔍 Analyzing screen for action: '{action_description}'")
        
        # Take screenshot
        screenshot = self.take_screenshot()
        
        # Analyze with LLaVA
        elements = self.analyze_ui_elements_with_llava(screenshot, action_description)
        
        if elements:
            # Use the highest confidence element
            best_element = max(elements, key=lambda e: e.confidence)
            logger.info(f"🎯 Selected element: {best_element.description} at {best_element.coordinates} (confidence: {best_element.confidence:.2f})")
            
            # Create visual verification
            self.create_visual_verification(screenshot, best_element, action_description)
            
            return best_element.coordinates
        else:
            # Fallback to context-aware detection
            logger.warning("🤖 No elements detected by AI, falling back to context-aware detection")
            try:
                from context_aware_coordinate_detector import context_aware_detector
                return context_aware_detector.get_smart_coordinates_for_action(action_description, step_type)
            except Exception as e:
                logger.error(f"Fallback detection failed: {e}")
                # Ultimate fallback
                return (self.screen_width // 2, self.screen_height // 2)
    
    def create_visual_verification(self, screenshot: Image.Image, element: UIElement, action_description: str) -> str:
        """Create visual verification showing detected element"""
        
        draw = ImageDraw.Draw(screenshot)
        x, y = element.coordinates
        
        # Draw crosshairs with different colors based on confidence
        color = 'green' if element.confidence > 0.7 else 'orange' if element.confidence > 0.5 else 'red'
        crosshair_size = 30
        line_width = 5
        
        # White outline for visibility
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            draw.line([
                (x - crosshair_size + offset[0], y + offset[1]),
                (x + crosshair_size + offset[0], y + offset[1])
            ], fill='white', width=line_width + 2)
            
            draw.line([
                (x + offset[0], y - crosshair_size + offset[1]),
                (x + offset[0], y + crosshair_size + offset[1])
            ], fill='white', width=line_width + 2)
        
        # Main colored crosshairs
        draw.line([
            (x - crosshair_size, y),
            (x + crosshair_size, y)
        ], fill=color, width=line_width)
        
        draw.line([
            (x, y - crosshair_size),
            (x, y + crosshair_size)
        ], fill=color, width=line_width)
        
        # Add element info
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        info_text = f"AI Detection: {element.description}\nType: {element.element_type}\nCoords: {element.coordinates}\nConfidence: {element.confidence:.2f}\nAction: {action_description[:25]}..."
        
        # Position text to avoid overlap
        text_x = max(10, min(x - 150, screenshot.width - 300))
        text_y = max(10, y - 100) if y > 120 else y + 50
        
        # Background for text
        text_lines = info_text.split('\n')
        max_width = max(draw.textlength(line, font=font) for line in text_lines)
        text_height = len(text_lines) * 18
        
        draw.rectangle([
            (text_x - 5, text_y - 5),
            (text_x + max_width + 10, text_y + text_height + 10)
        ], fill='white', outline='black', width=2)
        
        for i, line in enumerate(text_lines):
            draw.text((text_x, text_y + i * 18), line, fill='black', font=font)
        
        # Save verification
        filename = f"ai_visual_detection_{int(time.time())}.png"
        screenshot.save(filename)
        logger.info(f"📸 AI visual verification saved: {filename}")
        
        return filename
    
    def test_detection(self, test_description: str) -> Dict:
        """Test the AI detection system"""
        
        logger.info(f"🧪 Testing AI detection for: '{test_description}'")
        
        screenshot = self.take_screenshot()
        elements = self.analyze_ui_elements_with_llava(screenshot, test_description)
        
        result = {
            "test_description": test_description,
            "elements_found": len(elements),
            "elements": [
                {
                    "type": elem.element_type,
                    "coordinates": elem.coordinates,
                    "confidence": elem.confidence,
                    "description": elem.description
                }
                for elem in elements
            ]
        }
        
        if elements:
            best_element = max(elements, key=lambda e: e.confidence)
            verification_file = self.create_visual_verification(screenshot, best_element, test_description)
            result["verification_image"] = verification_file
        
        return result

# Create singleton instance
ai_visual_detector = AIVisualElementDetector()

if __name__ == "__main__":
    detector = AIVisualElementDetector()
    
    # Test cases
    test_cases = [
        "text input field to type in",
        "search box on Google",
        "text area for writing",
        "button to click"
    ]
    
    print("=== AI Visual Element Detection Tests ===")
    
    for test_desc in test_cases:
        result = detector.test_detection(test_desc)
        print(f"\n🧪 Test: {test_desc}")
        print(f"   Elements found: {result['elements_found']}")
        
        for elem in result['elements']:
            print(f"   - {elem['type']} at {elem['coordinates']} (confidence: {elem['confidence']:.2f})")
            print(f"     Description: {elem['description']}")
        
        if 'verification_image' in result:
            print(f"   📸 Verification: {result['verification_image']}")