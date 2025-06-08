#!/usr/bin/env python3
"""
Automatic Suggestion System - Monitors system activity and sends suggestions to overlay
Bypasses the LLM timeout and plan persistence issues by sending notifications directly
"""

import os
import json
import asyncio
import logging
import websockets
import uuid
import time
import random
from datetime import datetime

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/auto_suggestion_system.log')
    ]
)
logger = logging.getLogger('auto_suggestion_system')

# WebSocket ports
UI_PORT = 8766  # Overlay UI port
BACKEND_PORT = 8767  # Backend server port

# Suggestion configuration
SUGGESTION_INTERVAL = 60  # seconds between suggestion checks
MAX_SUGGESTIONS_PER_HOUR = 3  # maximum number of suggestions per hour
NOTIFICATION_SOUND = True  # whether to play sound with notifications

# Track suggestions to avoid flooding
last_suggestions = []
suggestion_count = 0
start_time = time.time()

async def send_suggestion(message, port=8766, buttons=None, importance="high", play_sound=True):
    """Send a suggestion to the overlay via WebSocket"""
    ws_url = f"ws://localhost:{port}"
    if port == 8767:
        ws_url += "/ws"  # Backend requires /ws path
    
    notification_id = f"suggestion_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"
    
    if buttons is None:
        buttons = [
            {"text": "✅ Got it", "value": "understood", "style": "success"},
            {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
        ]
    
    try:
        logger.info(f"Connecting to {ws_url}...")
        async with websockets.connect(ws_url) as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            logger.info(f"Connected to {ws_url}! Welcome message received.")
            
            # Register with backend if needed
            if port == 8767:
                register_msg = {
                    "type": "register",
                    "client_type": "auto_suggestion_system",
                    "client_id": f"auto_suggestion_{uuid.uuid4()}"
                }
                await ws.send(json.dumps(register_msg))
                response = await ws.recv()
                logger.info(f"Registration response received.")
            
            # Create notification based on port type
            if port == 8766:  # UI Overlay port
                notification = {
                    "type": "suggestion",
                    "response": message,
                    "buttons": buttons,
                    "importance": importance,
                    "play_sound": play_sound,
                    "notification": True,
                    "plan_id": notification_id,
                    "timestamp": datetime.now().isoformat()
                }
            else:  # Backend port
                notification = {
                    "type": "message",
                    "message": message,
                    "mode": "SUGGEST",
                    "buttons": buttons,
                    "importance": importance,
                    "play_sound": play_sound, 
                    "notification": True,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Send notification
            logger.info(f"Sending suggestion: {message}")
            await ws.send(json.dumps(notification))
            
            # Try to send legacy format as well for better compatibility
            if port == 8766:
                legacy_notification = {
                    "success": True,
                    "response": message,
                    "mode": "SUGGEST",
                    "notification": True,
                    "play_sound": play_sound,
                    "importance": importance,
                    "buttons": buttons,
                    "interactive": True,
                    "timestamp": datetime.now().isoformat()
                }
                await asyncio.sleep(0.5)  # Small delay between messages
                await ws.send(json.dumps(legacy_notification))
                logger.info("Legacy format also sent for compatibility")
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                logger.info("Response received from overlay")
                return True
            except asyncio.TimeoutError:
                logger.warning("No response received within timeout")
                return True  # Continue even without response
    
    except Exception as e:
        logger.error(f"Error sending suggestion: {e}")
        
        # If the overlay connection fails, try backend
        if port == 8766:
            logger.info("Trying backend port as fallback...")
            return await send_suggestion(message, port=8767, buttons=buttons, importance=importance, play_sound=play_sound)
        return False

async def check_memory_and_suggest():
    """Check memory and current context to generate suggestions"""
    global suggestion_count, start_time
    
    # Reset suggestion count every hour
    current_time = time.time()
    if current_time - start_time > 3600:
        suggestion_count = 0
        start_time = current_time
    
    # Don't exceed max suggestions per hour
    if suggestion_count >= MAX_SUGGESTIONS_PER_HOUR:
        logger.info(f"Maximum suggestions per hour ({MAX_SUGGESTIONS_PER_HOUR}) reached. Waiting...")
        return
    
    # Generate a suggestion based on system activity
    # In a real implementation, this would analyze memory, screen, and process data
    suggestion = generate_sample_suggestion()
    
    if suggestion:
        # Record suggestion was sent
        last_suggestions.append({
            "time": datetime.now().isoformat(),
            "content": suggestion["message"]
        })
        suggestion_count += 1
        
        # Send the suggestion
        success = await send_suggestion(
            message=suggestion["message"],
            buttons=suggestion["buttons"],
            importance=suggestion["importance"],
            play_sound=NOTIFICATION_SOUND
        )
        
        if success:
            logger.info(f"Suggestion #{suggestion_count} sent successfully")
        else:
            logger.warning("Failed to send suggestion")

def generate_sample_suggestion():
    """Generate a sample suggestion based on basic patterns"""
    # In a real implementation, this would analyze memory and current context
    # For demo purposes, we'll just use some canned suggestions
    suggestions = [
        {
            "message": "🔍 ACTION SUGGESTION: I notice you're working on the SensAI project. Would you like help with the notification system?",
            "importance": "high",
            "buttons": [
                {"text": "✅ Yes, help me", "value": "help", "style": "success"},
                {"text": "❌ Not now", "value": "dismiss", "style": "danger"}
            ]
        },
        {
            "message": "💡 UI SUGGESTION: Based on the current screen, consider testing the WebSocket connection to ensure notifications are working properly.",
            "importance": "medium",
            "buttons": [
                {"text": "📋 Show me how", "value": "how", "style": "success"},
                {"text": "✅ Got it", "value": "understood", "style": "primary"},
                {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
            ]
        },
        {
            "message": "🔔 SYSTEM ALERT: The LLM service is experiencing timeouts. Consider restarting the service or using a smaller model.",
            "importance": "high",
            "buttons": [
                {"text": "🔄 Restart service", "value": "restart", "style": "warning"},
                {"text": "⚙️ Configuration", "value": "config", "style": "primary"},
                {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
            ]
        },
        {
            "message": "🧩 AUTOMATION SUGGESTION: I can help you fix the plan persistence system to handle AutomationPlan objects correctly.",
            "importance": "medium",
            "buttons": [
                {"text": "👍 Show solution", "value": "solution", "style": "success"},
                {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
            ]
        },
        {
            "message": "📊 PERFORMANCE TIP: The system is currently using fallback screen capture mode. Enabling direct screen access could improve response time.",
            "importance": "medium",
            "buttons": [
                {"text": "⚡ Optimize now", "value": "optimize", "style": "success"},
                {"text": "❓ Tell me more", "value": "more", "style": "primary"},
                {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
            ]
        }
    ]
    
    # Pick a random suggestion that hasn't been used recently
    available = [s for s in suggestions if s["message"] not in [ls["content"] for ls in last_suggestions[-3:]]]
    if not available:
        available = suggestions  # If we've used all suggestions, reset
    
    return random.choice(available)

async def suggestion_monitor():
    """Main monitoring loop that periodically checks and sends suggestions"""
    logger.info("Starting automatic suggestion system...")
    
    while True:
        try:
            await check_memory_and_suggest()
        except Exception as e:
            logger.error(f"Error in suggestion check: {e}")
        
        # Wait for next check interval
        await asyncio.sleep(SUGGESTION_INTERVAL)

async def main():
    """Main function"""
    print("\n=== AUTOMATIC SUGGESTION SYSTEM ===\n")
    print("This system monitors activity and sends relevant suggestions to the overlay chat.")
    print(f"Checking for suggestion opportunities every {SUGGESTION_INTERVAL} seconds.")
    print(f"Maximum {MAX_SUGGESTIONS_PER_HOUR} suggestions per hour.")
    print("\nPress Ctrl+C to stop the service.\n")
    
    # Initial suggestion to verify system is working
    initial_msg = "✅ ACTION SUGGESTION: The automatic suggestion system is now active. You'll receive contextual notifications based on your activity."
    await send_suggestion(initial_msg, importance="high")
    
    # Start the monitoring loop
    await suggestion_monitor()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nAutomatic suggestion system stopped.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\nError: {e}")