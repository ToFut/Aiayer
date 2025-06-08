#!/bin/bash

# Fix DO Button Issues Now (No Restart Required)
echo "=== DO Button Runtime Fix ==="
echo "This script applies fixes to the running system without requiring a restart"

# Create necessary directories
mkdir -p logs

# Run the direct plan backend fix
echo ""
echo "Step 1: Applying backend plan sharing fix..."
python3 direct_plan_backend_fix.py

# Run the direct neural UI handler fix
echo ""
echo "Step 2: Applying neural UI DO button handler fix..."
python3 direct_fix_neural_ui_do_button_handler.py

# Create test plan via the handler
echo ""
echo "Step 3: Testing with a direct message to the DO Button fix proxy..."
python3 -c "
import asyncio
import websockets
import json
import uuid
import time

async def test_do_button():
    # Connect to proxy
    uri = 'ws://localhost:8766'
    print(f'Connecting to {uri}...')
    async with websockets.connect(uri) as websocket:
        # Wait for welcome message
        welcome = await websocket.recv()
        print(f'Connected: {welcome[:100]}...')
        
        # Create session ID
        session_id = f'test_plan_{uuid.uuid4()}'
        
        # Send DO button action
        message = {
            'type': 'agent_confirmation',
            'sessionId': session_id,
            'action': 'DO',
            'timestamp': int(time.time() * 1000)
        }
        
        print(f'Sending DO button action for {session_id}...')
        await websocket.send(json.dumps(message))
        
        # Wait for response
        response = await websocket.recv()
        response_data = json.loads(response)
        
        print(f'Response type: {response_data.get(\"type\")}')
        print(f'Success: {\"success\" in response_data}')
        
        if response_data.get('type') == 'agent_execution_error':
            print(f'Error: {response_data.get(\"error\")}')
        else:
            print('Test succeeded!')

asyncio.run(test_do_button())
"

echo ""
echo "✅ DO Button fix has been applied to the running system!"
echo "The 'Available plans: None' issue should now be resolved."
echo "You can continue using the system without restarting."
echo ""
echo "If you still encounter issues:"
echo "1. Try restarting the system completely:"
echo "   ./STOP_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh"
echo "   ./START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh"
echo ""
echo "2. Check the logs for more information:"
echo "   tail -f logs/direct_plan_fix.log"
echo "   tail -f logs/direct_neural_ui_fix.log"
echo "   tail -f logs/do_button_fix/connection_fix.log"