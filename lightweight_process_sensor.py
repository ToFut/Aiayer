#!/usr/bin/env python3
"""
Lightweight Process Sensor
Monitors only top 5 processes every 15 seconds
"""
import asyncio
import json
import psutil
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightweightProcessSensor:
    def __init__(self):
        self.interval = 15  # 15 seconds
        self.max_processes = 5
        self.running = False
        
    async def start(self):
        self.running = True
        logger.info("🚀 Lightweight Process Sensor started")
        
        while self.running:
            try:
                # Get top processes by CPU
                processes = []
                for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                    try:
                        proc_info = proc.info
                        if proc_info['cpu_percent'] > 0:
                            processes.append(proc_info)
                    except:
                        continue
                
                # Sort by CPU and take top 5
                processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
                top_processes = processes[:self.max_processes]
                
                # Save to cache
                cache_data = {
                    "timestamp": datetime.now().isoformat(),
                    "processes": top_processes
                }
                
                with open("cache/process_sensor/lightweight_process_cache.json", "w") as f:
                    json.dump(cache_data, f)
                
                logger.info(f"📊 Monitored {len(top_processes)} processes")
                
                await asyncio.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Process sensor error: {e}")
                await asyncio.sleep(self.interval)
    
    def stop(self):
        self.running = False

if __name__ == "__main__":
    sensor = LightweightProcessSensor()
    asyncio.run(sensor.start())
