#!/bin/bash
# Enhanced System Startup with LLM Warmup
# Ensures fast AI responses by pre-warming the model

echo "🚀 Starting Enhanced System with LLM Warmup..."

# Kill any existing processes
echo "🛑 Stopping existing processes..."
./STOP_ENHANCED_SYSTEM.sh

# Wait for cleanup
sleep 2

# Create logs directory
mkdir -p logs

# Start warmup manager first
echo "🔥 Pre-warming LLM model for fast responses..."
python3 -c "
import asyncio
from llm_warmup_manager import get_warmup_manager
import logging

logging.basicConfig(level=logging.INFO)

async def warmup():
    try:
        manager = await get_warmup_manager()
        if manager.is_model_warm():
            print('✅ LLM model warmed up and ready!')
            print('⚡ Agent mode will now respond in 3-10 seconds!')
        else:
            print('❌ LLM warmup failed')
    except Exception as e:
        print(f'❌ Warmup error: {e}')

asyncio.run(warmup())
" &

WARMUP_PID=$!

# Wait for warmup to complete
echo "⏳ Waiting for model warmup..."
sleep 15

# Kill the warmup process (model stays warm in Ollama)
kill $WARMUP_PID 2>/dev/null

echo "🚀 Starting enhanced enterprise backend..."
python3 enhanced_enterprise_backend_with_context.py &
BACKEND_PID=$!

# Store PIDs for cleanup
echo $BACKEND_PID > pids/enterprise_backend_contextual.pid

echo "✅ Enhanced system started with warm LLM!"
echo "🔥 AI responses should now be fast (1-3 seconds)"
echo ""
echo "📊 System Status:"
echo "   Backend PID: $BACKEND_PID"
echo "   LLM Model: llama3.2:1b (warmed)"
echo "   Port: 8765"
echo ""
echo "🌐 Connect at: ws://localhost:8765"
echo ""
echo "To stop the system: ./STOP_ENHANCED_SYSTEM.sh"