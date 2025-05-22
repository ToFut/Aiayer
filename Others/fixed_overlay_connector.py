import asyncio
import websockets
import json
import logging
import os
import time
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/overlay_connector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('overlay_connector')

# Save PID
with open('pids/overlay_connector.pid', 'w') as f:
    f.write(str(os.getpid()))

async def connect_to_server():
    """Connect to the WebSocket server and handle messages"""
    url = "ws://localhost:8767"
    logger.info(f"Attempting to connect to {url}")
    
    try:
        async with websockets.connect(url) as websocket:
            logger.info(f"Connected to {url}")
            
            # Handle welcome message
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"Received from server: {data.get('type', 'unknown')} - {data.get('message', 'No message')}")
            
            # Send initialization message
            init_msg = {
                "type": "overlay_init",
                "message": "Overlay initialized and connected",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(init_msg))
            logger.info(f"Sent initialization message: {init_msg}")
            
            # Periodic test messages
            test_counter = 1
            while True:
                # Send test message
                test_msg = {
                    "type": "overlay_update",
                    "message": f"Periodic test message #{test_counter}",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send(json.dumps(test_msg))
                logger.info(f"Sent test message #{test_counter}")
                
                # Receive response
                response = await websocket.recv()
                data = json.loads(response)
                logger.info(f"Received response: {data}")
                
                test_counter += 1
                await asyncio.sleep(10)  # Wait 10 seconds between messages
                
    except websockets.exceptions.ConnectionClosed as e:
        logger.error(f"Connection closed: {e}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

async def main():
    """Main function with retry logic"""
    retries = 0
    max_retries = 10
    retry_delay = 5
    
    while retries < max_retries:
        success = await connect_to_server()
        if success:
            break
            
        retries += 1
        logger.warning(f"Connection attempt {retries}/{max_retries} failed. Retrying in {retry_delay} seconds...")
        await asyncio.sleep(retry_delay)
    
    if retries >= max_retries:
        logger.error("Maximum retry attempts reached. Giving up.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Overlay connector stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
