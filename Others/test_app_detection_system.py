#!/usr/bin/env python3
"""
Test Application Detection System

This script demonstrates the unified application detection system with improved UI analysis.
It captures the current screen and performs comprehensive application detection.
"""
import os
import sys
import time
import asyncio
import argparse
import json
from datetime import datetime
from PIL import Image

# Add script directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import detection modules
try:
    from unified_app_detection import UnifiedAppDetectionSystem, ApplicationContext
    from ui_element_detector import UIElementDetector
    from app_aware_memory_integrator import AppAwareMemoryIntegrator
except ImportError as e:
    print(f"Error importing detection modules: {e}")
    print("Make sure all required files are available in the same directory")
    sys.exit(1)

async def test_single_screenshot(args):
    """Test application detection with a single screenshot"""
    print("\n----- Testing Single Screenshot Detection -----")
    
    if args.screenshot:
        # Use provided screenshot
        screenshot_path = args.screenshot
        if not os.path.exists(screenshot_path):
            print(f"Error: Screenshot file '{screenshot_path}' not found")
            return
    else:
        # Capture a screenshot
        try:
            import mss
            import mss.tools
            
            print("Capturing screenshot...")
            with mss.mss() as sct:
                primary = sct.monitors[1]  # Primary monitor
                screenshot = sct.grab(primary)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"results/app_detection/screenshot_{timestamp}.png"
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                
                # Save to file
                mss.tools.to_png(screenshot.rgb, screenshot.size, output=screenshot_path)
                print(f"Screenshot saved to: {screenshot_path}")
        except Exception as e:
            print(f"Error capturing screenshot: {e}")
            return
    
    # Initialize detectors
    app_detector = UnifiedAppDetectionSystem(llava_url=args.llava_url)
    ui_detector = UIElementDetector(llava_url=args.llava_url)
    
    # Run application detection
    print("\nDetecting application...")
    start_time = time.time()
    app_result = await app_detector.manual_detection(screenshot_path)
    app_detection_time = time.time() - start_time
    
    # Show application detection results
    print("\n===== APPLICATION DETECTION RESULTS =====")
    print(f"Application: {app_result.app_name}")
    print(f"Confidence: {app_result.confidence:.2f}")
    print(f"Category: {app_result.app_category}")
    print(f"View: {app_result.view_name}")
    print(f"Workflow: {app_result.workflow}")
    print(f"Detection time: {app_detection_time:.2f} seconds")
    
    # Run UI element detection if requested
    if args.ui:
        print("\nAnalyzing UI elements...")
        app_context = {
            "app_name": app_result.app_name,
            "view_name": app_result.view_name
        }
        
        start_time = time.time()
        ui_result = await ui_detector.detect_ui_elements(screenshot_path, app_context)
        ui_detection_time = time.time() - start_time
        
        # Show UI detection results
        print("\n===== UI ELEMENT DETECTION RESULTS =====")
        print(f"Element count: {len(ui_result.elements)}")
        
        # Display top 5 elements
        if ui_result.elements:
            print("\nTop 5 UI Elements:")
            for i, element in enumerate(ui_result.elements[:5]):
                print(f"{i+1}. {element.element_type}: {element.element_text}")
                if element.state:
                    print(f"   State: {element.state}")
                if element.parent_component:
                    print(f"   Parent: {element.parent_component}")
                if element.interaction_hints:
                    print(f"   Interaction: {', '.join(element.interaction_hints)}")
        
        # Show application patterns
        if ui_result.app_specific_patterns:
            print("\nApplication Patterns:")
            if "raw_text" in ui_result.app_specific_patterns:
                pattern_text = ui_result.app_specific_patterns["raw_text"]
                # Limit display to first 200 chars
                print(f"  {pattern_text[:200]}" + ('...' if len(pattern_text) > 200 else ''))
            else:
                print("  No application-specific patterns detected")
        
        print(f"\nUI Analysis time: {ui_detection_time:.2f} seconds")
    
    # Save results
    result_path = f"results/app_detection/detection_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    result = {
        "timestamp": time.time(),
        "screenshot": screenshot_path,
        "application": {
            "name": app_result.app_name,
            "confidence": app_result.confidence,
            "category": app_result.app_category,
            "view": app_result.view_name,
            "workflow": app_result.workflow
        },
        "detection_time": app_detection_time
    }
    
    if args.ui and 'ui_result' in locals():
        result["ui_elements"] = {
            "count": len(ui_result.elements),
            "top_elements": [
                {
                    "type": elem.element_type,
                    "text": elem.element_text,
                    "state": elem.state
                } for elem in ui_result.elements[:5]
            ],
            "detection_time": ui_detection_time
        }
    
    # Save to file
    os.makedirs(os.path.dirname(result_path), exist_ok=True)
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nDetection results saved to: {result_path}")

async def test_continuous_detection(args):
    """Test continuous application detection"""
    print("\n----- Starting Continuous Application Detection -----")
    print(f"Running for {args.duration} seconds, interval: {args.interval} seconds")
    
    # Initialize memory integration
    integrator = AppAwareMemoryIntegrator(llava_url=args.llava_url)
    
    # Configure detection interval
    integrator.app_detector.detection_interval = args.interval
    
    # Start detection
    integrator.start()
    print("Application detection system started")
    
    try:
        for i in range(args.duration):
            # Update progress every 5 seconds
            if i % 5 == 0 or i == args.duration - 1:
                context = integrator.get_current_context()
                if context:
                    print(f"[{i+1}/{args.duration}s] Current app: {context.app_name}")
                    print(f"  View: {context.view_name}")
                    print(f"  Workflow: {context.workflow}")
                    print(f"  Session duration: {context.session_duration:.1f}s")
                    print(f"  Confidence: {context.confidence:.2f}")
                    print()
            
            # Sleep for 1 second
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        print("\nDetection interrupted by user")
    finally:
        # Stop detection
        integrator.stop()
        print("Application detection system stopped")
    
    # Show detection summary
    print("\n===== DETECTION SUMMARY =====")
    history = integrator.get_context_history()
    print(f"Total context changes: {len(history)}")
    
    # Show detected applications
    app_counts = {}
    view_counts = {}
    for context in history:
        app_counts[context.app_name] = app_counts.get(context.app_name, 0) + 1
        if context.view_name:
            key = f"{context.app_name} - {context.view_name}"
            view_counts[key] = view_counts.get(key, 0) + 1
    
    print("\nDetected Applications:")
    for app, count in sorted(app_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {app}: {count} times")
    
    if view_counts:
        print("\nTop Application Views:")
        for view, count in sorted(view_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {view}: {count} times")
    
    # Show statistics
    stats = integrator.get_app_usage_statistics()
    
    print("\nApplication Usage Statistics:")
    for app_name, app_stats in sorted(stats["apps"].items(), 
                                     key=lambda x: x[1]["total_time"], 
                                     reverse=True):
        total_time_secs = app_stats["total_time"]
        print(f"  {app_name}:")
        print(f"    Total time: {total_time_secs:.1f} seconds")
        print(f"    Session count: {app_stats['session_count']}")
        
        # Show top views if available
        if app_stats["top_views"]:
            top_views = app_stats["top_views"]
            print(f"    Top views: " + ", ".join([f"{v[0]} ({v[1]})" for v in top_views[:3]]))
    
    # Save final statistics
    stats_path = f"results/app_detection/usage_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(stats_path), exist_ok=True)
    
    with open(stats_path, 'w') as f:
        json.dump({
            "timestamp": time.time(),
            "duration": args.duration,
            "interval": args.interval,
            "app_counts": app_counts,
            "view_counts": view_counts,
            "app_stats": stats["apps"]
        }, f, indent=2)
    
    print(f"\nUsage statistics saved to: {stats_path}")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test Application Detection System")
    parser.add_argument("--screenshot", help="Path to screenshot file (if not provided, will capture current screen)")
    parser.add_argument("--ui", action="store_true", help="Perform detailed UI analysis")
    parser.add_argument("--continuous", action="store_true", help="Run continuous detection")
    parser.add_argument("--duration", type=int, default=60, help="Duration for continuous detection in seconds (default: 60)")
    parser.add_argument("--interval", type=float, default=5.0, help="Detection interval in seconds (default: 5.0)")
    parser.add_argument("--llava-url", default="http://localhost:11434", help="URL for Ollama API (default: http://localhost:11434)")
    
    args = parser.parse_args()
    
    print("Application Detection System Test")
    print(f"LLaVA URL: {args.llava_url}")
    
    # Check which test to run
    if args.continuous:
        await test_continuous_detection(args)
    else:
        await test_single_screenshot(args)
    
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