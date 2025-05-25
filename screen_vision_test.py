#!/usr/bin/env python3
"""
Screen Vision Test - Check what the system can actually "see" and understand from UI
"""

import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
    import pyautogui
    pyautogui.FAILSAFE = False
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

def capture_screen_and_analyze():
    """Capture current screen and analyze what we can see"""
    
    if not VISION_AVAILABLE:
        print("❌ Vision libraries not available. Install with:")
        print("pip install pytesseract pillow pyautogui")
        return None
    
    try:
        # Capture screen
        screenshot_path = "/tmp/current_screen_analysis.png"
        result = subprocess.run(['screencapture', '-x', screenshot_path], capture_output=True)
        
        if result.returncode != 0:
            print("❌ Failed to capture screen")
            return None
        
        # Analyze screenshot
        image = Image.open(screenshot_path)
        
        # Get basic image info
        width, height = image.size
        print(f"📸 Screen captured: {width}x{height} pixels")
        
        # Extract text using OCR
        print("🔍 Extracting text from screen...")
        extracted_text = pytesseract.image_to_string(image)
        
        # Get detailed OCR data with positions
        print("📍 Getting text with positions...")
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # Analyze what we can detect
        analysis = {
            "screen_info": {
                "dimensions": f"{width}x{height}",
                "capture_time": datetime.now().isoformat()
            },
            "text_content": {
                "raw_text": extracted_text,
                "text_blocks": [],
                "word_count": len(extracted_text.split()) if extracted_text else 0
            },
            "ui_elements_detected": {
                "buttons": [],
                "inputs": [],
                "menus": [],
                "links": [],
                "forms": []
            },
            "application_context": {
                "detected_app": "unknown",
                "ui_type": "unknown",
                "confidence": 0
            }
        }
        
        # Process OCR data to find UI elements
        words = []
        confidences = []
        
        for i, word in enumerate(ocr_data['text']):
            if word.strip():
                conf = int(ocr_data['conf'][i])
                if conf > 30:  # Only include confident detections
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    
                    word_data = {
                        "text": word.strip(),
                        "position": {"x": x, "y": y, "width": w, "height": h},
                        "confidence": conf
                    }
                    words.append(word_data)
                    confidences.append(conf)
        
        analysis["text_content"]["text_blocks"] = words
        
        # Detect UI elements based on text patterns
        all_text = extracted_text.lower()
        
        # Button detection
        button_keywords = ["button", "click", "submit", "save", "cancel", "send", "apply", "ok", "yes", "no"]
        for keyword in button_keywords:
            if keyword in all_text:
                analysis["ui_elements_detected"]["buttons"].append(keyword)
        
        # Input field detection
        input_keywords = ["name", "email", "password", "search", "enter", "input", "field"]
        for keyword in input_keywords:
            if keyword in all_text:
                analysis["ui_elements_detected"]["inputs"].append(keyword)
        
        # Menu detection
        menu_keywords = ["menu", "file", "edit", "view", "help", "tools", "options", "settings"]
        for keyword in menu_keywords:
            if keyword in all_text:
                analysis["ui_elements_detected"]["menus"].append(keyword)
        
        # Application detection
        app_signatures = {
            "cursor": ["cursor", "claude", "ai", "copilot", "code"],
            "vscode": ["visual studio", "vscode", "extensions", "terminal"],
            "chrome": ["chrome", "google", "bookmark", "tab"],
            "slack": ["slack", "channel", "message", "workspace"],
            "notion": ["notion", "page", "database", "block"],
            "figma": ["figma", "frame", "component", "design"],
            "github": ["github", "repository", "commit", "pull request"]
        }
        
        for app, keywords in app_signatures.items():
            matches = sum(1 for keyword in keywords if keyword in all_text)
            if matches > 0:
                confidence = min(matches / len(keywords), 1.0)
                if confidence > analysis["application_context"]["confidence"]:
                    analysis["application_context"]["detected_app"] = app
                    analysis["application_context"]["confidence"] = confidence
        
        # UI type detection
        ui_types = {
            "code_editor": ["class", "function", "import", "def", "var", "const", "if", "else"],
            "web_browser": ["http", "www", "search", "bookmark", "tab", "url"],
            "chat_app": ["message", "chat", "send", "reply", "thread"],
            "design_tool": ["frame", "layer", "color", "font", "style"],
            "productivity": ["document", "sheet", "slide", "note", "task"]
        }
        
        for ui_type, keywords in ui_types.items():
            matches = sum(1 for keyword in keywords if keyword in all_text)
            if matches > 2:  # Need multiple matches for UI type
                analysis["application_context"]["ui_type"] = ui_type
                break
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error analyzing screen: {e}")
        return None

def detailed_ui_elements_analysis():
    """Perform detailed analysis of specific UI elements"""
    
    if not VISION_AVAILABLE:
        return None
    
    try:
        # Get mouse position for context
        mouse_x, mouse_y = pyautogui.position()
        
        # Get screen regions analysis
        screen_width, screen_height = pyautogui.size()
        
        regions = {
            "top_bar": (0, 0, screen_width, 100),
            "sidebar": (0, 100, 300, screen_height-100),
            "main_content": (300, 100, screen_width-300, screen_height-200),
            "bottom_bar": (0, screen_height-100, screen_width, 100)
        }
        
        detailed_analysis = {
            "mouse_position": {"x": mouse_x, "y": mouse_y},
            "screen_dimensions": {"width": screen_width, "height": screen_height},
            "regions_analysis": {}
        }
        
        # Analyze each region
        for region_name, (x, y, w, h) in regions.items():
            try:
                # Capture region
                region_screenshot = pyautogui.screenshot(region=(x, y, w, h))
                region_text = pytesseract.image_to_string(region_screenshot)
                
                detailed_analysis["regions_analysis"][region_name] = {
                    "bounds": {"x": x, "y": y, "width": w, "height": h},
                    "text_content": region_text.strip()[:200] if region_text else "",  # First 200 chars
                    "has_content": bool(region_text.strip())
                }
            except Exception as e:
                detailed_analysis["regions_analysis"][region_name] = {
                    "bounds": {"x": x, "y": y, "width": w, "height": h},
                    "error": str(e)
                }
        
        return detailed_analysis
        
    except Exception as e:
        print(f"❌ Error in detailed analysis: {e}")
        return None

def main():
    """Run comprehensive screen vision test"""
    
    print("🔍 SCREEN VISION TEST - What can the system actually SEE?")
    print("=" * 60)
    
    # Basic screen capture and analysis
    print("\n1. BASIC SCREEN ANALYSIS:")
    analysis = capture_screen_and_analyze()
    
    if analysis:
        print(f"   ✅ Screen captured: {analysis['screen_info']['dimensions']}")
        print(f"   📝 Words detected: {analysis['text_content']['word_count']}")
        print(f"   🎯 App detected: {analysis['application_context']['detected_app']} ({analysis['application_context']['confidence']:.2f})")
        print(f"   🎨 UI type: {analysis['application_context']['ui_type']}")
        
        # Show detected UI elements
        ui_elements = analysis['ui_elements_detected']
        print(f"   🔘 Buttons found: {len(ui_elements['buttons'])}")
        print(f"   📝 Inputs found: {len(ui_elements['inputs'])}")
        print(f"   📋 Menus found: {len(ui_elements['menus'])}")
        
        # Show sample text
        if analysis['text_content']['raw_text']:
            sample_text = analysis['text_content']['raw_text'][:200]
            print(f"   📄 Sample text: {repr(sample_text)}...")
    
    # Detailed regional analysis
    print("\n2. DETAILED SCREEN REGIONS:")
    detailed = detailed_ui_elements_analysis()
    
    if detailed:
        print(f"   🖱️  Mouse at: ({detailed['mouse_position']['x']}, {detailed['mouse_position']['y']})")
        print(f"   📺 Screen: {detailed['screen_dimensions']['width']}x{detailed['screen_dimensions']['height']}")
        
        for region_name, region_data in detailed['regions_analysis'].items():
            if 'error' not in region_data:
                has_content = "✅" if region_data['has_content'] else "❌"
                print(f"   {has_content} {region_name}: {len(region_data['text_content'])} chars")
                if region_data['text_content']:
                    print(f"      Preview: {repr(region_data['text_content'][:50])}...")
    
    # Summary of capabilities
    print("\n3. SYSTEM VISION CAPABILITIES:")
    if VISION_AVAILABLE:
        print("   ✅ OCR Text Extraction: Available")
        print("   ✅ UI Element Detection: Basic patterns")
        print("   ✅ Application Recognition: Pattern-based")
        print("   ✅ Regional Analysis: Available")
        print("   ✅ Mouse Position: Available")
        print("   ❌ Deep UI Understanding: Limited to text")
        print("   ❌ Interactive Elements: Detection only")
        print("   ❌ Visual Layout: No spatial analysis")
        print("   ❌ Complex Components: No recognition")
    else:
        print("   ❌ Vision libraries not installed")
    
    # Save analysis
    if analysis:
        output_file = "/Users/segevbin/Desktop/SensAI/Aiayer/screen_vision_analysis.json"
        with open(output_file, 'w') as f:
            json.dump({
                "basic_analysis": analysis,
                "detailed_analysis": detailed,
                "test_timestamp": datetime.now().isoformat()
            }, f, indent=2)
        print(f"\n💾 Analysis saved to: {output_file}")

if __name__ == "__main__":
    main()