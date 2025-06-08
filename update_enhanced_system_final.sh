#!/bin/bash
# Final update for START_ENHANCED_SYSTEM.sh to use the fixed real DO button executor

# Backup the original script
cp START_ENHANCED_SYSTEM.sh START_ENHANCED_SYSTEM.sh.bak.$(date +%Y%m%d)

# Replace the server launch section to use our fixed executor
sed -i'.bak' '/# Start WebSocket server on port 8765/,/echo "Starting WebSocket server on port 8765"/c\
# Start fixed real DO button executor on port 8765\
echo "Starting fixed real DO button executor on port 8765..."\
bash ./start_fixed_do_button_executor.sh' START_ENHANCED_SYSTEM.sh

echo "✅ START_ENHANCED_SYSTEM.sh updated to use the fixed real DO button executor"
echo "✅ Original backed up to START_ENHANCED_SYSTEM.sh.bak.$(date +%Y%m%d)"
echo "✅ The system will now properly execute LLM-generated plans when using the DO button"
echo ""
echo "To start the updated system, run:"
echo "  ./STOP_ENHANCED_SYSTEM.sh"
echo "  ./START_ENHANCED_SYSTEM.sh"