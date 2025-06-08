#!/usr/bin/env python3
"""
Enhanced suggestion handler with improved debugging and direct relay to WebSocket clients
This ensures that notifications are properly displayed in the overlay
"""

import asyncio
import json
import logging
import os
import sys
import uuid
import websockets
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/nextgen_suggestion_fix.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('nextgen_suggestion_fix')

# WebSocket server port (direct connection)
PROXY_PORT = 8765

async def send_suggestion(response_text, buttons=None, importance="high", play_sound=True):
    """
    Send a suggestion message directly to the overlay
    
    Args:
        response_text (str): The text content of the suggestion
        buttons (list): List of button objects with text and value properties
        importance (str): Importance level (high, medium, low)
        play_sound (bool): Whether to play a sound when the suggestion appears
    
    Returns:
        bool: True if the suggestion was successfully sent, False otherwise
    """
    # Default buttons if none provided
    if buttons is None:
        buttons = [
            {"text": "✅ OK", "value": "ok", "style": "success"},
            {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
        ]
    
    # Create plan ID for tracking
    plan_id = f"suggestion_{uuid.uuid4()}"
    
    # Try both message formats to ensure compatibility
    # Format 1: New "suggestion" type format
    suggestion_type_format = {
        "type": "suggestion",
        "response": response_text,
        "buttons": buttons,
        "importance": importance,
        "play_sound": play_sound,
        "plan_id": plan_id,
        "timestamp": datetime.now().isoformat()
    }
    
    # Format 2: Legacy SUGGEST mode format with notification flag
    suggest_mode_format = {
        "success": True,
        "response": response_text,
        "mode": "SUGGEST",
        "notification": True,
        "play_sound": play_sound,
        "importance": importance,
        "buttons": buttons,
        "interactive": True,
        "timestamp": datetime.now().isoformat()
    }
    
    # Pretty print suggestion for debugging
    logger.info(f"Sending suggestion (new format): {json.dumps(suggestion_type_format, indent=2)}")
    
    success = False
    
    try:
        # Connect to the proxy WebSocket server
        async with websockets.connect(f"ws://localhost:{PROXY_PORT}") as ws:
            logger.info(f"Connected to proxy on port {PROXY_PORT}")
            
            # Wait for welcome message
            welcome = await ws.recv()
            welcome_data = json.loads(welcome)
            logger.info(f"Received welcome: {welcome}")
            
            # Send the suggestion in new format
            await ws.send(json.dumps(suggestion_type_format))
            logger.info("Suggestion sent to proxy (new format)")
            
            # Wait briefly to allow processing
            await asyncio.sleep(1)
            
            # Also try the legacy format for better compatibility
            await ws.send(json.dumps(suggest_mode_format))
            logger.info("Suggestion sent to proxy (legacy format)")
            
            # Wait for any response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                logger.info(f"Received response: {response}")
                success = True
            except asyncio.TimeoutError:
                logger.warning("No immediate response received, but messages were sent")
                success = True
                
    except Exception as e:
        logger.error(f"Error sending suggestion: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    # Also try direct connection to port 8765 as fallback
    if not success:
        try:
            logger.info("Attempting direct connection to WebSocket server on port 8765...")
            async with websockets.connect("ws://localhost:8765") as direct_ws:
                await direct_ws.send(json.dumps(suggestion_type_format))
                logger.info("Suggestion sent directly to port 8765")
                success = True
        except Exception as e:
            logger.error(f"Error sending suggestion directly: {e}")
    
    return success

async def test_suggestions():
    """Test sending different types of suggestions to verify functionality"""
    # Simple notification
    simple_success = await send_suggestion(
        "📣 This is a simple notification",
        [{"text": "OK", "value": "ok", "style": "success"}],
        "medium"
    )
    logger.info(f"Simple notification sent: {simple_success}")
    await asyncio.sleep(2)
    
    # High priority notification with custom buttons
    high_priority = await send_suggestion(
        "🔴 HIGH PRIORITY TEST\n\nThis is a test of the suggestion notification system with high importance.",
        [
            {"text": "✅ It works!", "value": "success", "style": "success"},
            {"text": "❌ Not working", "value": "failure", "style": "danger"}
        ],
        "high"
    )
    logger.info(f"High priority notification sent: {high_priority}")
    await asyncio.sleep(2)
    
    # Technical suggestion with detailed content
    technical = await send_suggestion(
        "💡 OPTIMIZATION SUGGESTION\n\nBased on your recent activities, you might want to consider refactoring the `processData` function to improve performance.\n\nWould you like to see a suggested implementation?",
        [
            {"text": "👍 Show me", "value": "show", "style": "success"},
            {"text": "⏱️ Later", "value": "later", "style": "warning"},
            {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
        ],
        "medium"
    )
    logger.info(f"Technical suggestion sent: {technical}")
    
    return simple_success and high_priority and technical

# Run the test if executed directly
if __name__ == "__main__":
    print("\n=== ENHANCED NEXTGEN SUGGESTION HANDLER ===\n")
    print("This script sends suggestion notifications directly to the overlay.")
    print("It includes enhanced debugging and direct WebSocket connection.\n")
    
    # Check if command line arguments were provided
    if len(sys.argv) > 1:
        # Custom message from command line
        message = " ".join(sys.argv[1:])
        asyncio.run(send_suggestion(message))
    else:
        # Run the test suite
        asyncio.run(test_suggestions())
    
    print("\n=== SUGGESTIONS SENT ===")
    print("Check the overlay to see if the notifications appear correctly.")
    print("If not, check the logs for error details.")