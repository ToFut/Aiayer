#!/bin/bash

# SensAI Lightweight System Startup
# OPTIMIZED FOR MINIMAL RESOURCE USAGE

echo "🚀 Starting Lightweight SensAI System..."
echo "⚡ OPTIMIZED FOR MINIMAL RESOURCE USAGE"
echo ""
echo "🔧 Lightweight Components:"
echo "   • Enhanced Backend (minimal features)"
echo "   • Basic Screen Sensor (30s intervals)"
echo "   • Basic Process Sensor (15s intervals)"
echo "   • LLM Service (llama3.2:1b)"
echo "   • Memory System (50MB limit)"
echo "   • DO Button Server (essential only)"
echo ""
echo "❌ Disabled for Performance:"
echo "   • Proactive Suggestion Monitor"
echo "   • Memory Feeder"
echo "   • Performance Monitor"
echo "   • Screen Sharing"
echo "   • Heavy UI Analysis"
echo "   • Continuous Memory Feeding"
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

# Set Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Create necessary directories
echo "📁 Creating required directories..."
mkdir -p logs/sensors
mkdir -p logs/backend
mkdir -p logs/llm
mkdir -p pids
mkdir -p cache/screen_sensor
mkdir -p cache/process_sensor
mkdir -p memory
mkdir -p config

# Create lightweight configuration
echo "⚙️ Creating lightweight configuration..."
python3 lightweight_system_config.py

# Initialize variables
BACKEND_OK=false
DO_BUTTON_OK=false
LLM_OK=false
SENSORS_OK=false

# Stop any existing processes
echo "🛑 Stopping any existing processes..."
pkill -f enhanced_enterprise_backend 2>/dev/null || true
pkill -f direct_coordinate_automation 2>/dev/null || true
pkill -f enhanced_fixed_process_sensor 2>/dev/null || true
pkill -f total_screen_analyzer 2>/dev/null || true
pkill -f llm_service 2>/dev/null || true

# Clean up ports
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
lsof -ti:8767 | xargs kill -9 2>/dev/null || true
lsof -ti:8768 | xargs kill -9 2>/dev/null || true

sleep 2

# Start LLM Service (essential)
echo "🧠 Starting LLM Service..."
if command -v ollama &> /dev/null; then
    # Check if llama3.2:1b is available
    if ollama list | grep -q "llama3.2:1b"; then
        echo "✅ llama3.2:1b model available"
        LLM_OK=true
    else
        echo "📥 Pulling llama3.2:1b model..."
        ollama pull llama3.2:1b
        if [ $? -eq 0 ]; then
            echo "✅ llama3.2:1b model pulled successfully"
            LLM_OK=true
        else
            echo "❌ Failed to pull llama3.2:1b model"
            echo "   Using default model if available"
            LLM_OK=true
        fi
    fi
else
    echo "❌ Ollama not found. Please install Ollama first."
    echo "   Visit: https://ollama.ai"
    exit 1
fi

# Start DO Button Server (essential)
echo "🔘 Starting DO Button Server..."
python3 direct_coordinate_automation.py > logs/backend/do_button_server.log 2>&1 &
DO_BUTTON_PID=$!
echo $DO_BUTTON_PID > pids/do_button_server.pid

# Wait for DO Button Server
sleep 3
if ps -p $DO_BUTTON_PID > /dev/null; then
    echo "✅ DO Button Server started (PID: $DO_BUTTON_PID)"
    DO_BUTTON_OK=true
else
    echo "❌ DO Button Server failed to start"
    cat logs/backend/do_button_server.log
    exit 1
fi

# Start Lightweight Backend
if [ "$DO_BUTTON_OK" = true ]; then
    echo "🖥️ Starting Lightweight Backend..."
    
    # Create lightweight backend configuration
    cat > lightweight_backend_config.py << 'EOF'
#!/usr/bin/env python3
"""
Lightweight Backend Configuration
"""
import os
import json

# Lightweight settings
LIGHTWEIGHT_CONFIG = {
    "max_concurrent_requests": 2,
    "request_timeout": 10,
    "max_memory_mb": 200,
    "enable_throttling": True,
    "screen_capture_interval": 30,
    "process_monitor_interval": 15,
    "disable_heavy_features": True,
    "use_caching": True,
    "cache_duration": 300
}

# Save config
with open('config/lightweight_backend_config.json', 'w') as f:
    json.dump(LIGHTWEIGHT_CONFIG, f, indent=2)

print("✅ Lightweight backend configuration created")
EOF

    python3 lightweight_backend_config.py
    
    # Start the lightweight backend
    python3 lightweight_backend.py > logs/backend/lightweight_backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > pids/lightweight_backend.pid
    
    # Wait for backend to start
    echo "⏳ Waiting for backend to initialize..."
    sleep 5
    
    # Check if backend is running
    if ps -p $BACKEND_PID > /dev/null; then
        echo "✅ Lightweight Backend started (PID: $BACKEND_PID)"
        BACKEND_OK=true
    else
        echo "❌ Lightweight Backend failed to start"
        cat logs/backend/lightweight_backend.log
        exit 1
    fi
fi

# Start Lightweight Sensors
if [ "$BACKEND_OK" = true ]; then
    echo "📡 Starting Lightweight Sensors..."
    
    # Start Lightweight Process Sensor
    echo "  📊 Starting Lightweight Process Sensor..."
    cat > lightweight_process_sensor.py << 'EOF'
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
EOF

    python3 lightweight_process_sensor.py > logs/sensors/lightweight_process.log 2>&1 &
    PROCESS_PID=$!
    echo $PROCESS_PID > pids/lightweight_process_sensor.pid
    
    # Start Lightweight Screen Sensor
    echo "  📸 Starting Lightweight Screen Sensor..."
    cat > lightweight_screen_sensor.py << 'EOF'
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
EOF

    python3 lightweight_screen_sensor.py > logs/sensors/lightweight_screen.log 2>&1 &
    SCREEN_PID=$!
    echo $SCREEN_PID > pids/lightweight_screen_sensor.pid
    
    # Wait for sensors to start
    sleep 3
    
    # Check sensor status
    SENSORS_RUNNING=0
    if ps -p $PROCESS_PID > /dev/null; then
        echo "✅ Lightweight Process Sensor running (PID: $PROCESS_PID)"
        SENSORS_RUNNING=$((SENSORS_RUNNING + 1))
    fi
    
    if ps -p $SCREEN_PID > /dev/null; then
        echo "✅ Lightweight Screen Sensor running (PID: $SCREEN_PID)"
        SENSORS_RUNNING=$((SENSORS_RUNNING + 1))
    fi
    
    if [ $SENSORS_RUNNING -eq 2 ]; then
        SENSORS_OK=true
    fi
fi

# System Status
echo ""
echo "🚀 LIGHTWEIGHT SENSAI SYSTEM READY!"
echo "================================================================="
echo "⚡ Lightweight Backend: ws://localhost:8767"
echo "🔘 DO Button Server: ws://localhost:8765"
echo "🧠 LLM Service: llama3.2:1b (fast model)"
echo "📡 Sensors Running: $SENSORS_RUNNING/2"
echo ""
echo "📊 Performance Optimizations:"
echo "  • Screen capture: 30s intervals (vs 10s)"
echo "  • Process monitoring: 15s intervals (vs 5s)"
echo "  • Memory limit: 200MB (vs unlimited)"
echo "  • Concurrent requests: 2 (vs unlimited)"
echo "  • Request timeout: 10s (vs 60s)"
echo "  • Compression: 50% quality (vs 85%)"
echo "  • Resolution: 1280x720 (vs full resolution)"
echo ""
echo "❌ Disabled Features (for performance):"
echo "  • Proactive suggestions"
echo "  • Continuous memory feeding"
echo "  • Performance monitoring"
echo "  • Screen sharing"
echo "  • Heavy UI analysis"
echo "  • OCR processing"
echo ""
echo "🎯 Expected Resource Usage:"
echo "  • CPU: < 30% (vs 80%+ in full mode)"
echo "  • Memory: < 200MB (vs 500MB+ in full mode)"
echo "  • Startup time: ~10s (vs 30s+ in full mode)"
echo "  • Response time: 2-5s (vs 5-15s in full mode)"
echo ""
echo "📁 Log Files:"
echo "  • Backend: logs/backend/lightweight_backend.log"
echo "  • DO Button: logs/backend/do_button_server.log"
echo "  • Process Sensor: logs/sensors/lightweight_process.log"
echo "  • Screen Sensor: logs/sensors/lightweight_screen.log"
echo ""
echo "🛑 Stop System: ./STOP_LIGHTWEIGHT_SYSTEM.sh"
echo ""
echo "Press Ctrl+C to stop showing logs (system will keep running)"
echo "----------------------------------------"

# Create stop script
cat > STOP_LIGHTWEIGHT_SYSTEM.sh << 'STOP_EOF'
#!/bin/bash
echo "🛑 Stopping Lightweight SensAI System..."

# Read PIDs and stop processes
for pidfile in pids/*.pid; do
    if [ -f "$pidfile" ]; then
        PID=$(cat "$pidfile")
        COMPONENT=$(basename "$pidfile" .pid)
        if ps -p $PID > /dev/null; then
            echo "Stopping $COMPONENT (PID: $PID)"
            kill -TERM $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        fi
        rm -f "$pidfile"
    fi
done

# Cleanup any remaining processes
pkill -f lightweight_backend 2>/dev/null || true
pkill -f lightweight_process_sensor 2>/dev/null || true
pkill -f lightweight_screen_sensor 2>/dev/null || true
pkill -f direct_coordinate_automation 2>/dev/null || true

# Clean up ports
lsof -ti:8765 | xargs kill -9 2>/dev/null || true
lsof -ti:8767 | xargs kill -9 2>/dev/null || true

echo "✅ Lightweight SensAI System stopped"
STOP_EOF
chmod +x STOP_LIGHTWEIGHT_SYSTEM.sh

# Show live logs
echo "📋 Showing live logs (Lightweight System)..."
tail -f logs/backend/lightweight_backend.log 2>/dev/null | sed 's/^/[LIGHTWEIGHT] /' || {
    echo "System running in background..."
    echo "Use 'tail -f logs/backend/lightweight_backend.log' to see backend logs"
} 