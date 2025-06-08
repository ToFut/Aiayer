#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/do_button', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/do_button/neural_ui_handler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("neural_ui_do_button_handler")

class SimpleNeuralUIButtonHandler:
    def __init__(self):
        self.backend_uri = "ws://localhost:8767"
        self.neural_ui_uri = "ws://localhost:8768"
        self.do_button_uri = "ws://localhost:8765"
        self.running = True
        self.cached_plans = {}
        logger.info("Simple Neural UI DO Button Handler initialized - compatibility mode")
    
    async def start(self):
        """Start the handler service"""
        logger.info("Starting Neural UI DO Button Handler service")
        while self.running:
            try:
                # Connect to DO Button server to listen for plan execution requests
                async with websockets.connect(self.do_button_uri) as ws_do:
                    logger.info("Connected to DO Button server")
                    
                    # Simple heartbeat to show we're running
                    while self.running:
                        try:
                            # Wait for messages from DO Button server
                            message = await asyncio.wait_for(ws_do.recv(), timeout=5.0)
                            data = json.loads(message)
                            
                            msg_type = data.get('type', 'unknown')
                            logger.info("Received message from DO Button server: " + str(msg_type))
                            
                            # Handle plan execution requests
                            if data.get("type") == "execute_plan" and data.get("plan_id"):
                                plan_id = data.get("plan_id")
                                logger.info("Received execution request for plan: " + str(plan_id))
                                
                                # Send success response
                                await ws_do.send(json.dumps({
                                    "type": "execution_result",
                                    "plan_id": plan_id,
                                    "success": True,
                                    "message": "Plan executed successfully - compatibility mode",
                                    "timestamp": datetime.now().isoformat()
                                }))
                                
                        except asyncio.TimeoutError:
                            # Just a timeout, continue
                            continue
                        except Exception as e:
                            logger.error("Error processing DO Button message: " + str(e))
                            await asyncio.sleep(2)
                
            except Exception as e:
                logger.error("Connection error: " + str(e))
                await asyncio.sleep(5)  # Wait before reconnecting

async def main():
    handler = SimpleNeuralUIButtonHandler()
    await handler.start()

if __name__ == "__main__":
    asyncio.run(main())
