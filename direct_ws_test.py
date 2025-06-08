#!/usr/bin/env python3
"""
Direct WebSocket Test - Try different message formats directly
"""
import asyncio
import websockets
import json
import logging
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test message formats to try
FORMATS = [
    {
        "name": "Basic suggestion",
        "data": {
            "type": "suggestion",
            "response": "🔔 BASIC SUGGESTION TEST"
        }
    },
    {
        "name": "Full suggestion",
        "data": {
            "type": "suggestion",
            "response": "🔔 FULL SUGGESTION TEST",
            "buttons": [
                {"text": "I see this!", "value": "seen", "style": "success"},
                {"text": "Not visible", "value": "not_seen", "style": "danger"}
            ],
            "importance": "high",
            "play_sound": True,
            "plan_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat()
        }
    },
    {
        "name": "Bridge format",
        "data": {
            "type": "chat_message",
            "payload": {
                "content": "🔔 BRIDGE FORMAT TEST",
                "mode": "SUGGEST",
                "buttons": [
                    {"text": "I see this!", "value": "seen", "style": "success"},
                    {"text": "Not visible", "value": "not_seen", "style": "danger"}
                ]
            }
        }
    },
    {
        "name": "Enhanced format",
        "data": {
            "type": "message",
            "mode": "SUGGEST",
            "notification": True,
            "message": "🔔 ENHANCED FORMAT TEST",
            "buttons": [
                {"text": "I see this!", "value": "seen", "style": "success"},
                {"text": "Not visible", "value": "not_seen", "style": "danger"}
            ]
        }
    },
    {
        "name": "NextGen format",
        "data": {
            "type": "final_response",
            "mode": "SUGGEST",
            "response": "🔔 NEXTGEN FORMAT TEST",
            "buttons": [
                {"text": "I see this!", "value": "seen", "style": "success"},
                {"text": "Not visible", "value": "not_seen", "style": "danger"}
            ]
        }
    }
]

async def test_format(port, format_data):
    """Test a specific message format"""
    ws_url = f"ws://localhost:{port}"
    if port == 8767:
        ws_url += "/ws"  # Backend requires /ws path
        
    try:
        logger.info(f"Connecting to {ws_url}...")
        
        async with websockets.connect(ws_url) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Welcome message received: {welcome[:100]}...")
            
            # For port 8767 (backend), we need to register first
            if port == 8767:
                register = {
                    "type": "register",
                    "client_type": "direct_test",
                    "client_id": f"direct_test_{uuid.uuid4()}"
                }
                
                await ws.send(json.dumps(register))
                register_response = await ws.recv()
                logger.info(f"Register response: {register_response[:100]}...")
            
            # Send the test format
            logger.info(f"Sending {format_data['name']} to port {port}...")
            await ws.send(json.dumps(format_data['data']))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                logger.info(f"Response received: {response[:100]}...")
                return True, response
            except asyncio.TimeoutError:
                logger.warning("No response within timeout")
                return False, None
                
    except Exception as e:
        logger.error(f"Error connecting to {ws_url}: {e}")
        return False, None

async def main():
    """Main function"""
    logger.info("=== DIRECT WEBSOCKET FORMAT TEST ===")
    
    # Test port 8766 with all formats
    port = 8766
    logger.info(f"\nTesting all formats on port {port}...")
    
    results = []
    for format_data in FORMATS:
        logger.info(f"\nTesting format: {format_data['name']}")
        success, response = await test_format(port, format_data)
        
        results.append({
            "format": format_data['name'],
            "success": success,
            "response": response[:100] if response else None
        })
        
        # Add a small delay between attempts
        await asyncio.sleep(1)
    
    # Print summary
    logger.info("\n=== TEST RESULTS ===")
    for result in results:
        status = "✅" if result['success'] else "❌"
        logger.info(f"{status} {result['format']}: {result['response']}")
    
    logger.info("\nTest complete.")

if __name__ == "__main__":
    asyncio.run(main())