#!/bin/bash
# Restart the enhanced backend with fixes applied

echo "🛑 Stopping current processes..."
pkill -f enhanced_enterprise_backend_with_context.py || true

echo "🔧 Applying fixes..."
python3 fix_agent_mode_llm_and_execution_fixed.py

echo "🚀 Starting enhanced backend with fixes..."
nohup python3 enhanced_enterprise_backend_with_context.py > logs/backend/enhanced_enterprise_fixed.log 2>&1 &

echo "✅ Backend restarted with fixes! Logs at logs/backend/enhanced_enterprise_fixed.log"
