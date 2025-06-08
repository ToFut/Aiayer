#!/usr/bin/env python3
"""
Test script for Neural UI Detector

This script demonstrates how to use the Neural UI Detector
to detect and interact with UI elements on the screen.
"""

import asyncio
import argparse
import os
import sys
import time
from neural_ui_detector import ui_detector

async def test_detection():
    """Test basic UI element detection"""
    print("\n=== Testing UI Element Detection ===\n")
    
    # Detect UI elements
    print("Taking screenshot and detecting UI elements...")
    result = await ui_detector.detect_elements()
    
    # Print detection stats
    print(f"\nDetected {len(result.elements)} UI elements in {result.execution_time:.2f}s")
    print(f"Detection methods used: {', '.join(result.detection_methods)}")
    
    # Print top 10 elements
    print("\nTop 10 detected elements:")
    for i, element in enumerate(result.elements[:10]):
        print(f"  {i+1}. {element.element_type}: '{element.text or '[No text]'}' at {element.center} " +
              f"(confidence: {element.confidence:.2f})")
    
    # Save visualization
    print("\nCreating visualization...")
    vis_path = ui_detector.visualize_detection(result)
    
    if vis_path:
        print(f"Visualization saved to: {vis_path}")
        # Try to open the image
        try:
            if sys.platform == "darwin":
                os.system(f"open {vis_path}")
            elif sys.platform == "win32":
                os.startfile(vis_path)
            else:
                os.system(f"xdg-open {vis_path}")
        except Exception as e:
            print(f"Could not open visualization: {e}")

async def test_interaction(target_description=None, target_type=None):
    """Test UI element interaction"""
    print("\n=== Testing UI Element Interaction ===\n")
    
    if not target_description:
        target_description = input("Enter text description of element to find (e.g., 'Submit button'): ")
    
    if not target_type and input("Specify element type? (y/n): ").lower() == 'y':
        target_type = input("Enter element type (e.g., button, text_field): ")
    
    # Find element
    print(f"\nFinding element: '{target_description}'" + 
          (f" of type '{target_type}'" if target_type else ""))
    
    element = await ui_detector.find_element(target_description, target_type)
    
    if not element:
        print(f"❌ Element '{target_description}' not found")
        return
    
    print(f"✅ Found element: {element.element_type} '{element.text or '[No text]'}' at {element.center}")
    
    # Ask for interaction
    action = input("\nChoose action (click/type/none): ").lower()
    
    if action == 'click':
        # Add confirmation for safety
        if input(f"Confirm click on '{target_description}' at {element.center}? (y/n): ").lower() != 'y':
            print("Click cancelled")
            return
        
        print(f"Clicking on element...")
        success = await ui_detector.click_element(target_description, target_type)
        
        if success:
            print(f"✅ Successfully clicked on element")
        else:
            print(f"❌ Failed to click on element")
    
    elif action == 'type':
        text = input("Enter text to type: ")
        
        # Add confirmation for safety
        if input(f"Confirm typing '{text}' into '{target_description}'? (y/n): ").lower() != 'y':
            print("Typing cancelled")
            return
        
        print(f"Typing text...")
        success = await ui_detector.type_text(target_description, text, target_type)
        
        if success:
            print(f"✅ Successfully typed text into element")
        else:
            print(f"❌ Failed to type text into element")

async def automate_sequence(actions=None):
    """Run a sequence of automation actions"""
    print("\n=== Running Automation Sequence ===\n")
    
    if not actions:
        print("No actions provided. Running example sequence.")
        # Example action sequence
        actions = [
            {"action": "detect", "description": "Detect all UI elements"},
            {"action": "find", "description": "Find a specific element", "target": "input", "type": "text_field"},
            {"action": "click", "description": "Click on the element", "target": "input", "type": "text_field"},
            {"action": "type", "description": "Type text into the element", "target": "input", "type": "text_field", "text": "Hello, world!"},
            {"action": "key", "description": "Press Enter key", "key": "enter"},
        ]
    
    # Run each action
    for i, action in enumerate(actions):
        print(f"\n⏩ Action {i+1}/{len(actions)}: {action['description']}")
        
        if action["action"] == "detect":
            result = await ui_detector.detect_elements()
            print(f"Detected {len(result.elements)} UI elements")
            
            # Create visualization
            vis_path = ui_detector.visualize_detection(result)
            if vis_path:
                print(f"Visualization saved to: {vis_path}")
        
        elif action["action"] == "find":
            element = await ui_detector.find_element(
                action["target"], 
                action.get("type")
            )
            
            if element:
                print(f"✅ Found element: {element.element_type} '{element.text or '[No text]'}' at {element.center}")
            else:
                print(f"❌ Element '{action['target']}' not found")
        
        elif action["action"] == "click":
            success = await ui_detector.click_element(
                action["target"], 
                action.get("type")
            )
            
            if success:
                print(f"✅ Clicked on element '{action['target']}'")
            else:
                print(f"❌ Failed to click on element '{action['target']}'")
        
        elif action["action"] == "type":
            success = await ui_detector.type_text(
                action["target"], 
                action["text"], 
                action.get("type")
            )
            
            if success:
                print(f"✅ Typed '{action['text']}' into element '{action['target']}'")
            else:
                print(f"❌ Failed to type text into element '{action['target']}'")
        
        elif action["action"] == "key":
            success = await ui_detector.press_key(action["key"])
            
            if success:
                print(f"✅ Pressed key '{action['key']}'")
            else:
                print(f"❌ Failed to press key '{action['key']}'")
        
        elif action["action"] == "hotkey":
            success = await ui_detector.press_hotkey(*action["keys"])
            
            if success:
                print(f"✅ Pressed hotkey '{'+'.join(action['keys'])}'")
            else:
                print(f"❌ Failed to press hotkey '{'+'.join(action['keys'])}'")
        
        elif action["action"] == "wait":
            duration = action.get("duration", 1.0)
            print(f"Waiting for {duration} seconds...")
            await asyncio.sleep(duration)
        
        else:
            print(f"❌ Unknown action: {action['action']}")
        
        # Add small delay between actions
        await asyncio.sleep(0.5)

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test Neural UI Detector")
    parser.add_argument("--detect", action="store_true", help="Test detection only")
    parser.add_argument("--interact", action="store_true", help="Test interaction")
    parser.add_argument("--automate", action="store_true", help="Run automation sequence")
    parser.add_argument("--target", type=str, help="Target element description")
    parser.add_argument("--type", type=str, help="Target element type")
    
    args = parser.parse_args()
    
    # Default to detection if no arguments provided
    if not (args.detect or args.interact or args.automate):
        args.detect = True
    
    # Run requested tests
    if args.detect:
        await test_detection()
    
    if args.interact:
        await test_interaction(args.target, args.type)
    
    if args.automate:
        await automate_sequence()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(0)