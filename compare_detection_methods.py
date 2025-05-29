#!/usr/bin/env python3
"""
Compare Detection Methods Demo
Shows the difference between basic and enhanced UI detection
"""

import asyncio
import cv2
import numpy as np
import time
import logging
from PIL import Image, ImageGrab
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def capture_test_screenshot():
    """Capture current screen for testing"""
    logger.info("📸 Capturing screen for detection comparison...")
    screenshot = ImageGrab.grab()
    screenshot_np = np.array(screenshot)
    screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
    return screenshot_cv

async def test_basic_detection(screenshot):
    """Test basic detection methods"""
    logger.info("🔍 Testing basic detection methods...")
    
    from teamviewer_ui_automation_system import TeamViewerUIAutomationSystem
    system = TeamViewerUIAutomationSystem()
    
    start_time = time.time()
    
    # Use basic detection methods
    elements = []
    try:
        button_elements = await system.detect_buttons(screenshot)
        elements.extend(button_elements)
        
        input_elements = await system.detect_input_fields(screenshot)
        elements.extend(input_elements)
        
        interactive_elements = await system.detect_interactive_elements(screenshot)
        elements.extend(interactive_elements)
    except Exception as e:
        logger.error(f"Basic detection error: {e}")
    
    detection_time = time.time() - start_time
    
    logger.info(f"🔧 Basic Detection Results:")
    logger.info(f"   📊 Found: {len(elements)} elements")
    logger.info(f"   ⏱️ Time: {detection_time:.2f}s")
    
    # Show breakdown by method
    method_counts = {}
    for element in elements:
        method = element.detection_method
        method_counts[method] = method_counts.get(method, 0) + 1
    
    for method, count in method_counts.items():
        logger.info(f"   📈 {method}: {count} elements")
    
    return elements, detection_time

async def test_enhanced_detection(screenshot):
    """Test enhanced detection methods"""
    logger.info("🔬 Testing enhanced detection methods...")
    
    try:
        from enhanced_ui_detection_engine import EnhancedUIDetectionEngine
        engine = EnhancedUIDetectionEngine()
        engine.debug_mode = False  # Disable debug for clean comparison
        
        start_time = time.time()
        elements = await engine.detect_ui_elements(screenshot)
        detection_time = time.time() - start_time
        
        logger.info(f"🚀 Enhanced Detection Results:")
        logger.info(f"   📊 Found: {len(elements)} elements")
        logger.info(f"   ⏱️ Time: {detection_time:.2f}s")
        
        # Show breakdown by method
        method_counts = {}
        confidence_sum = 0
        for element in elements:
            method = element.detection_method
            method_counts[method] = method_counts.get(method, 0) + 1
            confidence_sum += element.confidence
        
        avg_confidence = confidence_sum / len(elements) if elements else 0
        logger.info(f"   🎯 Average Confidence: {avg_confidence:.2f}")
        
        for method, count in method_counts.items():
            logger.info(f"   📈 {method}: {count} elements")
        
        # Show top elements
        sorted_elements = sorted(elements, key=lambda e: e.confidence, reverse=True)
        logger.info("   🏆 Top Elements:")
        for i, element in enumerate(sorted_elements[:5]):
            logger.info(f"      {i+1}. {element.element_type}: '{element.text[:30]}...' (confidence: {element.confidence:.2f})")
        
        return elements, detection_time
        
    except ImportError:
        logger.error("❌ Enhanced detection engine not available")
        return [], 0

async def create_comparison_visualization(screenshot, basic_elements, enhanced_elements):
    """Create side-by-side comparison image"""
    logger.info("🎨 Creating comparison visualization...")
    
    try:
        height, width = screenshot.shape[:2]
        
        # Create side-by-side comparison
        comparison = np.zeros((height, width * 2, 3), dtype=np.uint8)
        
        # Left side: Basic detection
        basic_vis = screenshot.copy()
        for element in basic_elements:
            bbox = element.bounding_box
            cv2.rectangle(basic_vis, 
                        (bbox['x'], bbox['y']), 
                        (bbox['x'] + bbox['width'], bbox['y'] + bbox['height']), 
                        (0, 0, 255), 2)  # Red for basic
            cv2.circle(basic_vis, element.center, 5, (0, 0, 255), -1)
        
        # Right side: Enhanced detection
        enhanced_vis = screenshot.copy()
        colors = {
            'button': (0, 255, 0),
            'text_field': (255, 0, 0),
            'link': (0, 0, 255),
            'text': (255, 255, 0),
            'interactive': (255, 0, 255),
            'focusable': (0, 255, 255),
            'ml_detected': (128, 128, 128),
            'ocr_text': (0, 255, 0)
        }
        
        for element in enhanced_elements:
            bbox = element.bounding_box
            color = colors.get(element.element_type, (255, 255, 255))
            
            # Thicker border for higher confidence
            thickness = max(1, int(element.confidence * 4))
            
            cv2.rectangle(enhanced_vis, 
                        (bbox['x'], bbox['y']), 
                        (bbox['x'] + bbox['width'], bbox['y'] + bbox['height']), 
                        color, thickness)
            cv2.circle(enhanced_vis, element.center, 5, color, -1)
            
            # Add confidence text
            cv2.putText(enhanced_vis, f"{element.confidence:.2f}", 
                      (bbox['x'], bbox['y'] - 5), 
                      cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        # Combine images
        comparison[:, :width] = basic_vis
        comparison[:, width:] = enhanced_vis
        
        # Add labels
        cv2.putText(comparison, "BASIC DETECTION", (20, 40), 
                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(comparison, "ENHANCED DETECTION", (width + 20, 40), 
                  cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Add statistics
        basic_stats = f"Elements: {len(basic_elements)}"
        enhanced_stats = f"Elements: {len(enhanced_elements)}"
        
        cv2.putText(comparison, basic_stats, (20, 80), 
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(comparison, enhanced_stats, (width + 20, 80), 
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Save comparison
        timestamp = int(time.time())
        comparison_path = f"detection_comparison_{timestamp}.png"
        cv2.imwrite(comparison_path, comparison)
        logger.info(f"💾 Comparison saved: {comparison_path}")
        
        return comparison_path
        
    except Exception as e:
        logger.error(f"Error creating visualization: {e}")
        return None

async def analyze_detection_quality(basic_elements, enhanced_elements):
    """Analyze and compare detection quality"""
    logger.info("📊 Analyzing detection quality...")
    
    # Quality metrics
    basic_high_conf = sum(1 for e in basic_elements if e.confidence > 0.7)
    enhanced_high_conf = sum(1 for e in enhanced_elements if e.confidence > 0.7)
    
    basic_avg_conf = sum(e.confidence for e in basic_elements) / len(basic_elements) if basic_elements else 0
    enhanced_avg_conf = sum(e.confidence for e in enhanced_elements) / len(enhanced_elements) if enhanced_elements else 0
    
    # Element type diversity
    basic_types = set(e.element_type for e in basic_elements)
    enhanced_types = set(e.element_type for e in enhanced_elements)
    
    # Clickable elements
    basic_clickable = sum(1 for e in basic_elements if e.clickable)
    enhanced_clickable = sum(1 for e in enhanced_elements if e.clickable)
    
    # OCR text elements
    enhanced_with_text = sum(1 for e in enhanced_elements if hasattr(e, 'ocr_text') and e.ocr_text)
    
    print("\n" + "="*60)
    print("📊 DETECTION QUALITY ANALYSIS")
    print("="*60)
    
    print(f"\n📈 QUANTITY COMPARISON:")
    print(f"   Basic Detection:    {len(basic_elements)} elements")
    print(f"   Enhanced Detection: {len(enhanced_elements)} elements")
    
    print(f"\n🎯 CONFIDENCE COMPARISON:")
    print(f"   Basic Average:      {basic_avg_conf:.2f}")
    print(f"   Enhanced Average:   {enhanced_avg_conf:.2f}")
    print(f"   Basic High Conf:    {basic_high_conf} elements (>0.7)")
    print(f"   Enhanced High Conf: {enhanced_high_conf} elements (>0.7)")
    
    print(f"\n🎨 TYPE DIVERSITY:")
    print(f"   Basic Types:        {len(basic_types)} types: {', '.join(basic_types)}")
    print(f"   Enhanced Types:     {len(enhanced_types)} types: {', '.join(enhanced_types)}")
    
    print(f"\n🖱️ CLICKABLE ELEMENTS:")
    print(f"   Basic Clickable:    {basic_clickable}")
    print(f"   Enhanced Clickable: {enhanced_clickable}")
    
    print(f"\n📝 TEXT DETECTION:")
    print(f"   Elements with OCR:  {enhanced_with_text}")
    
    # Quality score
    basic_score = (basic_avg_conf * 0.4) + (len(basic_types) * 0.1) + (basic_clickable / max(1, len(basic_elements)) * 0.5)
    enhanced_score = (enhanced_avg_conf * 0.4) + (len(enhanced_types) * 0.1) + (enhanced_clickable / max(1, len(enhanced_elements)) * 0.3) + (enhanced_with_text / max(1, len(enhanced_elements)) * 0.2)
    
    print(f"\n🏆 QUALITY SCORES:")
    print(f"   Basic Score:        {basic_score:.2f}/1.0")
    print(f"   Enhanced Score:     {enhanced_score:.2f}/1.0")
    
    if enhanced_score > basic_score:
        improvement = ((enhanced_score - basic_score) / basic_score * 100) if basic_score > 0 else 100
        print(f"   🎉 Improvement:     +{improvement:.1f}%")
    
    print("="*60)
    
    return {
        'basic_score': basic_score,
        'enhanced_score': enhanced_score,
        'improvement': enhanced_score - basic_score
    }

async def main():
    """Main comparison demo"""
    print("🚀 UI Detection Methods Comparison Demo")
    print("="*50)
    
    # Capture screenshot
    screenshot = await capture_test_screenshot()
    
    # Test both methods
    print("\n🔍 Testing Detection Methods...")
    basic_elements, basic_time = await test_basic_detection(screenshot)
    enhanced_elements, enhanced_time = await test_enhanced_detection(screenshot)
    
    # Create visualization
    comparison_path = await create_comparison_visualization(screenshot, basic_elements, enhanced_elements)
    
    # Analyze quality
    quality_results = await analyze_detection_quality(basic_elements, enhanced_elements)
    
    # Performance comparison
    print(f"\n⏱️ PERFORMANCE COMPARISON:")
    print(f"   Basic Detection:    {basic_time:.2f}s")
    print(f"   Enhanced Detection: {enhanced_time:.2f}s")
    if enhanced_time > 0:
        speed_ratio = basic_time / enhanced_time
        print(f"   Speed Ratio:        {speed_ratio:.2f}x")
    
    # Summary
    print(f"\n📋 SUMMARY:")
    if quality_results['improvement'] > 0:
        print(f"   ✅ Enhanced detection is {quality_results['improvement']:.2f} points better")
        print(f"   🎯 Recommends using Enhanced UI Detection Engine")
    else:
        print(f"   ⚠️ Basic detection performed similarly")
    
    if comparison_path:
        print(f"   🖼️ Visual comparison saved: {comparison_path}")
        print(f"   👁️ Open the image to see the difference!")
    
    print(f"\n💡 To improve detection:")
    print(f"   1. Install: pip install pytesseract scikit-learn")
    print(f"   2. Install Tesseract OCR on your system")
    print(f"   3. Use EnhancedUIDetectionEngine in your code")
    print(f"   4. Enable debug mode to see detailed annotations")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n💥 Demo failed: {e}")
        logger.error(f"Demo error: {e}")