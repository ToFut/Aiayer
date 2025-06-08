#!/bin/bash
# Update the START_ENHANCED_SYSTEM.sh script to use the real DO button executor

# Backup the original script
cp START_ENHANCED_SYSTEM.sh START_ENHANCED_SYSTEM.sh.bak

# Replace the server launch section to use our real executor
sed -i'.bak' '/# Start WebSocket server on port 8765/,/echo "Starting WebSocket server on port 8765"/c\
# Start real DO button executor on port 8765\
echo "Starting real DO button executor on port 8765..."\
bash ./start_real_do_button_executor.sh' START_ENHANCED_SYSTEM.sh

echo "✅ START_ENHANCED_SYSTEM.sh updated to use the real DO button executor"
echo "✅ Original backed up to START_ENHANCED_SYSTEM.sh.bak"
echo "✅ The system will now properly execute LLM-generated plans when using the DO button"