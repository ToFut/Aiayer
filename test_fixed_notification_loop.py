#!/usr/bin/env python3
import asyncio
import sys
import os
import logging
import time
import random
from datetime import datetime
from fixed_nextgen_notification import send_chat_notification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_notification_loop.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_notification_loop')

# Sample notifications
SAMPLE_NOTIFICATIONS = [
    "I noticed you've been working on coding for a while. Would you like to take a short break?",
    "There's a new email in your inbox from an important contact.",
    "Your CPU usage has been high for the last 10 minutes. Consider closing unused applications.",
    "I found a more efficient way to handle that task you've been working on.",
    "You have a meeting scheduled in 15 minutes.",
    "Based on your browser history, you might be interested in this related article.",
    "I noticed a pattern in your workflow. Would you like me to automate this repetitive task?",
    "There's an update available for your development environment.",
    "Your current task seems complex. Would you like me to break it down into smaller steps?",
    "You've been context-switching frequently. Would you like to enable focus mode?"
]

# Sample modes
MODES = ["Ask", "Suggest", "Agent", "Creative"]

async def run_notification_loop():
    """Run a loop that sends test notifications periodically"""
    logger.info("🔄 Starting notification test loop")
    
    # Ensure directory exists
    os.makedirs('logs', exist_ok=True)
    
    interval = 10  # seconds between notifications
    counter = 0
    
    try:
        while True:
            counter += 1
            
            # Select a random notification and mode
            message = random.choice(SAMPLE_NOTIFICATIONS)
            mode = random.choice(MODES)
            
            # Choose a random port to test with
            port = random.choice([8765, 8766, 8767, 8768])
            
            # Send notification directly
            logger.info(f"📣 Sending test notification #{counter} to port {port} with mode {mode}")
            
            try:
                result = await send_chat_notification(message, port, mode)
                if result:
                    logger.info(f"✅ Successfully sent notification to port {port}")
                else:
                    logger.warning(f"⚠️ Failed to send notification to port {port}")
            except Exception as e:
                logger.error(f"🔴 Error sending notification: {e}")
                
            # Wait for the next interval
            logger.info(f"⏱️ Waiting {interval} seconds until the next notification...")
            await asyncio.sleep(interval)
            
    except KeyboardInterrupt:
        logger.info("👋 Notification test loop stopped by user")
    except Exception as e:
        logger.error(f"🔴 Error in notification test loop: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(run_notification_loop())
    except KeyboardInterrupt:
        logger.info("👋 Test stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"🔴 Error running test: {e}")
        sys.exit(1)