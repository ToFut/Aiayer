#!/usr/bin/env python3
"""
NextGen Suggestion Fix Script

This script sends a properly formatted suggestion message specifically for the NextGenAppleChatWidget.
"""
import asyncio
import websockets
import json
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("nextgen_suggestion_fix")

# WebSocket connection info
WS_URI = "ws://localhost:8765"

async def send_nextgen_suggestion(title="Suggestion", message="Would you like help with this?"):
    """Send a properly formatted suggestion to the NextGenAppleChatWidget"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}...")
            
            # Create NextGen format suggestion - different from Enterprise format
            suggestion = {
                "type": "chat_response",
                "mode": "SUGGEST",
                "content": f"💡 {title}: {message}",
                "timestamp": datetime.now().isoformat(),
                "session_id": f"nextgen_suggestion_{int(datetime.now().timestamp())}",
                "interactive": True,
                "buttons": [
                    {
                        "id": "accept_suggestion",
                        "text": "Yes, please",
                        "action": "accept",
                        "style": "primary"
                    },
                    {
                        "id": "dismiss_suggestion",
                        "text": "No thanks",
                        "action": "dismiss",
                        "style": "secondary"
                    }
                ],
                "nextgen_format": True,
                "confidence": 0.95
            }
            
            # Send the suggestion directly
            await websocket.send(json.dumps(suggestion))
            logger.info(f"✅ Sent NextGen suggestion format to overlay")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                logger.info(f"Received response: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return True
                
    except Exception as e:
        logger.error(f"Error sending suggestion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def send_simple_format(title="Suggestion", message="Would you like help with this?"):
    """Send a simpler suggestion format that might be compatible with NextGenAppleChatWidget"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}...")
            
            # Create a simpler suggestion format
            suggestion = {
                "type": "message",
                "mode": "SUGGEST",
                "title": title,
                "message": message,
                "showButtons": True
            }
            
            # Send the suggestion
            await websocket.send(json.dumps(suggestion))
            logger.info(f"✅ Sent simple format suggestion to overlay")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                logger.info(f"Received response: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return True
                
    except Exception as e:
        logger.error(f"Error sending suggestion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def try_direct_format(title="Suggestion", message="Would you like help with this?"):
    """Try sending a direct message to the NextGen overlay in raw format"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}...")
            
            # Create a direct raw message with the content we want to display
            raw_message = f"""
            {{
                "type": "direct_nextgen_message",
                "content": "💡 **{title}**\\n\\n{message}",
                "buttons": [
                    {{
                        "id": "accept",
                        "text": "Yes, help me",
                        "action": "accept"
                    }},
                    {{
                        "id": "dismiss",
                        "text": "No thanks",
                        "action": "dismiss"
                    }}
                ]
            }}
            """
            
            # Send the raw message
            await websocket.send(raw_message.strip())
            logger.info(f"✅ Sent raw message format to overlay")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                logger.info(f"Received response: {response[:100]}...")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return True
                
    except Exception as e:
        logger.error(f"Error sending suggestion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def send_all_formats(title="Suggestion", message="Would you like help with this?"):
    """Send all possible suggestion formats to find which one works with NextGen overlay"""
    try:
        logger.info(f"Connecting to WebSocket server at {WS_URI}")
        
        async with websockets.connect(WS_URI, ping_interval=5, ping_timeout=20) as websocket:
            logger.info("Connected to WebSocket server")
            
            # Wait for welcome message
            welcome = await websocket.recv()
            logger.info(f"Received welcome: {welcome[:100]}...")
            
            # List of all formats to try
            formats = [
                # Format 1: standard success/response
                {
                    "success": True,
                    "response": f"💡 {title}: {message}",
                    "mode": "SUGGEST",
                    "processing_time": 0.5,
                    "enterprise_validated": True,
                    "buttons": [
                        {
                            "id": "do_it",
                            "text": "Yes, help me",
                            "action": "accept",
                            "style": "success"
                        },
                        {
                            "id": "dismiss",
                            "text": "No thanks",
                            "action": "dismiss",
                            "style": "danger"
                        }
                    ],
                    "interactive": True
                },
                
                # Format 2: chat_message type
                {
                    "type": "chat_message",
                    "mode": "SUGGEST",
                    "content": f"💡 {title}: {message}",
                    "sender": "assistant",
                    "timestamp": datetime.now().isoformat(),
                    "buttons": [
                        {
                            "id": "accept",
                            "text": "Yes, please",
                            "action": "accept"
                        },
                        {
                            "id": "dismiss",
                            "text": "No thanks",
                            "action": "dismiss"
                        }
                    ]
                },
                
                # Format 3: suggestion type
                {
                    "type": "suggestion",
                    "title": title,
                    "message": message,
                    "session_id": f"suggestion_{int(datetime.now().timestamp())}"
                },
                
                # Format 4: direct mode
                {
                    "mode": "SUGGEST",
                    "text": f"{title}: {message}",
                    "interactive": True,
                    "show_buttons": True
                }
            ]
            
            for i, fmt in enumerate(formats):
                logger.info(f"Trying format {i+1}/{len(formats)}")
                await websocket.send(json.dumps(fmt))
                await asyncio.sleep(1)  # Wait before trying next format
            
            logger.info(f"✅ Sent all suggestion formats to overlay")
            return True
                
    except Exception as e:
        logger.error(f"Error sending suggestion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main function - try multiple suggestion formats"""
    logger.info("🚀 Testing NextGen Suggestion System")
    
    # Get message from command line arguments if provided
    title = "NextGen Suggestion Test"
    message = "This is a test suggestion for the NextGenAppleChatWidget"
    
    if len(sys.argv) > 1:
        title = sys.argv[1]
    if len(sys.argv) > 2:
        message = sys.argv[2]
    
    # Try all formats
    logger.info("Trying all formats to find which one works with NextGen overlay")
    await send_all_formats(title, message)
    
    logger.info("✅ Test complete")
    logger.info("Check the overlay to see if any suggestion appears")
    return True

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)