#!/bin/bash

echo "Starting basic system with minimal components..."

# Kill any running services
pkill -f 'python.*sensor' || true
pkill -f 'python.*ws_server' || true
pkill -f 'python.*memory_connector' || true
pkill -f 'python.*main.py' || true
pkill -f 'node.*overlay' || true

# Clean corrupted cache files
echo "Cleaning cache files..."
rm -f memory/memory_state.json 2>/dev/null || true
rm -f memory/last_context.json 2>/dev/null || true
echo "{}" > memory/memory_state.json
echo "{}" > memory/last_context.json

mkdir -p logs
mkdir -p pids

# Start WebSocket server in isolation (basic mode)
echo "Starting WebSocket server..."
python -c "
import asyncio
import websockets
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/simple_ws.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ws_server')

# Store connected clients
connected = set()

async def handler(websocket):
    connected.add(websocket)
    logger.info(f'Client connected. Total clients: {len(connected)}')
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            'type': 'welcome',
            'content': 'Connected to AI system backend'
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                # Echo back with confirmation
                await websocket.send(json.dumps({
                    'type': 'response',
                    'content': f'Received: {data.get(\"content\", \"No content\")}',
                    'timestamp': asyncio.get_event_loop().time()
                }))
                logger.info(f'Message handled: {message[:50]}...')
            except json.JSONDecodeError:
                logger.error(f'Invalid JSON: {message[:50]}...')
                await websocket.send(json.dumps({
                    'type': 'error',
                    'content': 'Invalid JSON message'
                }))
    except websockets.exceptions.ConnectionClosed:
        logger.info('Connection closed')
    finally:
        connected.remove(websocket)

async def main():
    logger.info('Starting WebSocket server on port 8767')
    async with websockets.serve(handler, 'localhost', 8767):
        await asyncio.Future()  # Run forever

try:
    asyncio.run(main())
except KeyboardInterrupt:
    logger.info('Server stopped by user')
" &

# Save WebSocket server PID
echo $! > pids/ws_server_8767.pid

# Wait for WebSocket server to start
sleep 2

# Check if WebSocket server is running
if ps -p $(cat pids/ws_server_8767.pid 2>/dev/null) > /dev/null; then
    echo "✅ WebSocket server running on port 8767"
else
    echo "❌ WebSocket server failed to start"
    exit 1
fi

# Start minimal overlay to test communication
echo "Starting minimal overlay..."
python -c "
import asyncio
import websockets
import json
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/overlay_client.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('overlay_client')

async def client():
    url = 'ws://localhost:8767'
    try:
        async with websockets.connect(url) as websocket:
            logger.info(f'Connected to {url}')
            
            # Receive welcome message
            welcome = await websocket.recv()
            logger.info(f'Received: {welcome}')
            
            # Send test message
            test_msg = {'type': 'test', 'content': 'Testing overlay connection', 'timestamp': time.time()}
            await websocket.send(json.dumps(test_msg))
            logger.info(f'Sent: {test_msg}')
            
            # Receive response
            response = await websocket.recv()
            logger.info(f'Received response: {response}')
            
            return True
    except Exception as e:
        logger.error(f'Error connecting to WebSocket server: {e}')
        return False

async def main():
    for i in range(3):  # Try 3 times
        success = await client()
        if success:
            logger.info('Connection test successful!')
            break
        else:
            logger.warning(f'Connection attempt {i+1} failed, retrying in 2 seconds...')
            await asyncio.sleep(2)

asyncio.run(main())
"

echo ""
echo "Test complete. Check logs:"
echo "- WebSocket server: logs/simple_ws.log" 
echo "- Overlay client: logs/overlay_client.log"
echo ""
echo "To stop the system: kill \$(cat pids/ws_server_8767.pid)"