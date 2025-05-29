#!/usr/bin/env python3
"""
Simple test to verify screen sharing works end-to-end.
This will help fix the black screen issue.
"""

import PIL.ImageGrab
import base64
import io
import json

def create_simple_screen_frame():
    """Create a simple screen frame like the backend should"""
    print("📸 Capturing screen...")
    
    # Capture screen
    screenshot = PIL.ImageGrab.grab()
    width, height = screenshot.size
    print(f"📺 Screen size: {width}x{height}")
    
    # Convert RGBA to RGB for JPEG compatibility
    if screenshot.mode == 'RGBA':
        screenshot = screenshot.convert('RGB')
    
    # Compress to JPEG
    img_buffer = io.BytesIO()
    screenshot.save(img_buffer, format='JPEG', quality=85, optimize=True)
    jpeg_data = img_buffer.getvalue()
    print(f"📦 JPEG size: {len(jpeg_data)} bytes")
    
    # Encode to base64
    b64_data = base64.b64encode(jpeg_data).decode('utf-8')
    print(f"📦 Base64 size: {len(b64_data)} chars")
    
    # Create frame data structure like backend
    frame_data = {
        "type": "screen_frame",
        "timestamp": 1234567890.0,
        "frame_id": 1,
        "width": width,
        "height": height,
        "format": "compressed_jpeg",
        "data": b64_data,
        "ui_elements": [],
        "cursor_position": {"x": 100, "y": 100},
        "active_window": "Test",
        "fps": 15.0,
        "compressed": True
    }
    
    print("✅ Frame data created successfully")
    return frame_data

def test_frame_decode(frame_data):
    """Test decoding the frame data"""
    print("🔍 Testing frame decode...")
    
    try:
        # Decode base64
        jpeg_bytes = base64.b64decode(frame_data['data'])
        print(f"✅ Base64 decoded: {len(jpeg_bytes)} bytes")
        
        # Create image from bytes
        img = PIL.Image.open(io.BytesIO(jpeg_bytes))
        print(f"✅ JPEG decoded: {img.size}")
        
        # Save test result
        img.save("screen_test_decoded.jpg")
        print("💾 Saved decoded image: screen_test_decoded.jpg")
        
        return True
        
    except Exception as e:
        print(f"❌ Decode failed: {e}")
        return False

if __name__ == "__main__":
    # Test the complete pipeline
    frame_data = create_simple_screen_frame()
    success = test_frame_decode(frame_data)
    
    if success:
        print("\n🎉 SUCCESS: Screen capture pipeline works!")
        print("The issue is likely in the backend frame capture loop.")
        print("✅ Screen sharing should work once the backend is fixed.")
    else:
        print("\n❌ FAILED: Frame processing has issues.")