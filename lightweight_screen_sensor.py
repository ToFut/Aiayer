#!/usr/bin/env python3
"""
Lightweight Screen Sensor
Captures screen every 30 seconds with minimal processing
"""
import asyncio
import json
import time
import logging
import hashlib
from datetime import datetime
from PIL import ImageGrab
import io
import base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightweightScreenSensor:
    def __init__(self):
        self.interval = 30  # 30 seconds
        self.last_hash = None
        self.running = False
        self.compression_quality = 50
        
    async def start(self):
        self.running = True
        logger.info("🚀 Lightweight Screen Sensor started")
        
        while self.running:
            try:
                # Capture screen
                screenshot = ImageGrab.grab()
                
                # Resize for performance (1280x720)
                screenshot = screenshot.resize((1280, 720), ImageGrab.Image.LANCZOS)
                
                # Calculate hash
                img_bytes = io.BytesIO()
                screenshot.save(img_bytes, format='JPEG', quality=self.compression_quality)
                img_hash = hashlib.md5(img_bytes.getvalue()).hexdigest()
                
                # Only process if changed
                if img_hash != self.last_hash:
                    # Convert to base64
                    img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                    
                    # Save to cache
                    cache_data = {
                        "timestamp": datetime.now().isoformat(),
                        "image_hash": img_hash,
                        "image_data": img_base64,
                        "resolution": "1280x720",
                        "compression": self.compression_quality
                    }
                    
                    with open("cache/screen_sensor/lightweight_screen_cache.json", "w") as f:
                        json.dump(cache_data, f)
                    
                    self.last_hash = img_hash
                    logger.info(f"📸 Screen captured: {img_hash[:8]}...")
                else:
                    logger.info("📸 Screen unchanged, skipped processing")
                
                await asyncio.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Screen sensor error: {e}")
                await asyncio.sleep(self.interval)
    
    def stop(self):
        self.running = False

if __name__ == "__main__":
    sensor = LightweightScreenSensor()
    asyncio.run(sensor.start())
