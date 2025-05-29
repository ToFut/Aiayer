#!/usr/bin/env python3
"""
Debug script to understand why universal screen detector is failing
"""

import pyautogui
import cv2
import numpy as np
import logging
from PIL import Image, ImageDraw
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_detection():
    """Debug the detection algorithms step by step"""
    
    print("🔍 DEBUGGING UNIVERSAL SCREEN DETECTION")
    print("=" * 50)
    
    # Take screenshot
    screenshot = pyautogui.screenshot()
    img_array = np.array(screenshot)
    img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    print(f"📸 Screenshot taken: {img_gray.shape}")
    
    # Method 1: Light area detection
    print("\n🔍 METHOD 1: Light Area Detection")
    light_threshold = 200
    light_mask = cv2.threshold(img_gray, light_threshold, 255, cv2.THRESH_BINARY)[1]
    
    # Save light mask for inspection
    cv2.imwrite("debug_light_mask.png", light_mask)
    print(f"💾 Light mask saved: debug_light_mask.png")
    
    # Find contours
    contours, _ = cv2.findContours(light_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"🔎 Found {len(contours)} light contours")
    
    # Analyze each contour
    potential_inputs = []
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area > 500:  # Only check reasonably sized areas
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            
            print(f"   Contour {i}: area={area}, pos=({x},{y}), size={w}x{h}, ratio={aspect_ratio:.2f}")
            
            # Check if it matches input field criteria
            if 800 < area < 50000 and 2.0 < aspect_ratio < 20.0 and 25 < h < 80:
                center_x = x + w // 2
                center_y = y + h // 2
                potential_inputs.append((center_x, center_y, w, h, area, aspect_ratio))
                print(f"   ✅ POTENTIAL INPUT: center=({center_x}, {center_y})")
    
    print(f"\n🎯 Found {len(potential_inputs)} potential input fields")
    
    # Method 2: Edge detection
    print("\n🔍 METHOD 2: Edge Detection")
    edges = cv2.Canny(img_gray, 50, 150)
    cv2.imwrite("debug_edges.png", edges)
    print(f"💾 Edge map saved: debug_edges.png")
    
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"🔎 Found {len(contours)} edge contours")
    
    edge_inputs = []
    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if 500 < area < 30000:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h
            
            if 2.5 < aspect_ratio < 15.0 and 20 < h < 60:
                center_x = x + w // 2
                center_y = y + h // 2
                edge_inputs.append((center_x, center_y, w, h, area, aspect_ratio))
                print(f"   ✅ EDGE INPUT: center=({center_x}, {center_y}), size={w}x{h}")
    
    print(f"\n🎯 Found {len(edge_inputs)} edge-based input fields")
    
    # Create debug visualization
    debug_img = screenshot.copy()
    draw = ImageDraw.Draw(debug_img)
    
    # Mark all potential inputs
    for i, (cx, cy, w, h, area, ratio) in enumerate(potential_inputs):
        # Green for light detection
        draw.ellipse([cx-10, cy-10, cx+10, cy+10], outline='lime', width=3)
        draw.text((cx+15, cy-10), f"L{i}: {w}x{h}", fill='lime')
    
    for i, (cx, cy, w, h, area, ratio) in enumerate(edge_inputs):
        # Blue for edge detection
        draw.ellipse([cx-8, cy-8, cx+8, cy+8], outline='blue', width=2)
        draw.text((cx+15, cy+15), f"E{i}: {w}x{h}", fill='blue')
    
    # Mark the Google search box manually for comparison
    # Based on the screenshot, it appears to be around (998, 313)
    google_search_x, google_search_y = 998, 313
    draw.ellipse([google_search_x-15, google_search_y-15, google_search_x+15, google_search_y+15], 
                outline='red', width=4)
    draw.text((google_search_x+20, google_search_y-20), "GOOGLE SEARCH", fill='red')
    
    debug_img.save("debug_detection_analysis.png")
    print(f"\n📸 Debug visualization saved: debug_detection_analysis.png")
    
    # Analyze the Google search box area specifically
    print(f"\n🔍 ANALYZING GOOGLE SEARCH BOX AREA")
    
    # Estimate Google search box dimensions (from visual inspection)
    search_x = 725  # Left edge
    search_y = 290  # Top edge  
    search_w = 546  # Width (approximately)
    search_h = 46   # Height (approximately)
    
    print(f"📍 Google search box estimated at: x={search_x}, y={search_y}, w={search_w}, h={search_h}")
    print(f"📍 Center coordinates: ({search_x + search_w//2}, {search_y + search_h//2})")
    
    # Check why this area wasn't detected
    roi = img_gray[search_y:search_y+search_h, search_x:search_x+search_w]
    avg_brightness = np.mean(roi)
    brightness_std = np.std(roi)
    aspect_ratio = search_w / search_h
    area = search_w * search_h
    
    print(f"🔍 Google search box analysis:")
    print(f"   Average brightness: {avg_brightness:.1f}")
    print(f"   Brightness std: {brightness_std:.1f}")
    print(f"   Aspect ratio: {aspect_ratio:.2f}")
    print(f"   Area: {area}")
    print(f"   Height: {search_h}")
    
    # Check if it passes our filters
    print(f"\n📊 Filter analysis:")
    print(f"   Area filter (800 < {area} < 50000): {800 < area < 50000}")
    print(f"   Aspect ratio filter (2.0 < {aspect_ratio:.2f} < 20.0): {2.0 < aspect_ratio < 20.0}")
    print(f"   Height filter (25 < {search_h} < 80): {25 < search_h < 80}")
    print(f"   Brightness filter (>{avg_brightness:.1f} > 200): {avg_brightness > 200}")
    
    print(f"\n✅ DEBUGGING COMPLETE")
    return potential_inputs, edge_inputs

if __name__ == "__main__":
    debug_detection()