#!/usr/bin/env python3
"""
Notification System Demo

This script demonstrates the complete functionality of the overlay notification system,
including different notification types, importance levels, button configurations, and
delivery methods.

Usage:
  python3 notification_system_demo.py [--interactive]
"""

import asyncio
import argparse
import json
import logging
import os
import sys
import time
import random
import websockets
from datetime import datetime

# Add parent directory to path for importing utility modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import standardized notification formatter
from utils.notification_formatter import format_notification, to_json

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/notification_demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("notification_demo")

# Sample notification messages for demo
SAMPLE_NOTIFICATIONS = [
    "⚠️ System update available. Would you like to install now?",
    "🔍 Scan completed: No issues found",
    "📊 Weekly report generated and ready to view",
    "🔔 Meeting reminder: Team check-in in 15 minutes",
    "📁 New file downloaded: presentation.pptx",
    "💬 New message from Alice: 'Can we talk about the project?'",
    "📱 Your mobile device is now connected",
    "🛑 Error detected in background process",
    "✅ Task completed successfully",
    "🚀 Application performance optimization complete"
]

# Sample button configurations
BUTTON_CONFIGS = {
    "standard": [
        {"text": "✅ Got it", "value": "understood", "style": "success"},
        {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
    ],
    "yes_no": [
        {"text": "✅ Yes", "value": "yes", "style": "success"},
        {"text": "❌ No", "value": "no", "style": "danger"}
    ],
    "actions": [
        {"text": "👁️ View", "value": "view", "style": "primary"},
        {"text": "⬇️ Download", "value": "download", "style": "success"},
        {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
    ],
    "rich": [
        {"text": "👍 Approve", "value": "approve", "style": "success"},
        {"text": "✏️ Edit", "value": "edit", "style": "primary"},
        {"text": "⏱️ Remind Later", "value": "remind", "style": "warning"},
        {"text": "❌ Decline", "value": "decline", "style": "danger"}
    ],
    "confirmation": [
        {"text": "✅ Confirm", "value": "confirm", "style": "success"}
    ]
}

async def test_connection(port):
    """Test if a websocket server is running on the given port"""
    try:
        async with websockets.connect(f"ws://localhost:{port}", ping_interval=None, close_timeout=1.0) as ws:
            await asyncio.wait_for(ws.recv(), timeout=1.0)
            logger.info(f"✅ Connection to port {port} successful")
            return True
    except Exception as e:
        logger.warning(f"❌ Connection to port {port} failed: {e}")
        return False

async def send_notification_to_port(port, notification):
    """Send a notification to a specific port"""
    try:
        async with websockets.connect(f"ws://localhost:{port}", ping_interval=None) as ws:
            # Wait for welcome message
            welcome = await asyncio.wait_for(ws.recv(), timeout=2.0)
            logger.info(f"Connected to port {port}. Welcome: {welcome}")
            
            # Send notification
            logger.info(f"Sending notification to port {port}: {notification['response']}")
            await ws.send(to_json(notification))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                logger.info(f"Response from port {port}: {response}")
                return True
            except asyncio.TimeoutError:
                logger.warning(f"No response received from port {port}")
                return False
    except Exception as e:
        logger.error(f"Error sending to port {port}: {e}")
        return False

async def demo_basic_notifications():
    """Demonstrate basic notifications with different importance levels"""
    logger.info("=== Demonstrating Basic Notifications ===")
    
    # Test all importance levels
    importance_levels = ["high", "medium", "low"]
    for importance in importance_levels:
        message = f"This is a {importance} importance notification"
        notification = format_notification(
            message=message,
            importance=importance,
            play_sound=(importance == "high")  # Only play sound for high importance
        )
        
        # Try port 8765 first (more direct to overlay)
        success = await send_notification_to_port(8765, notification)
        if not success:
            # Fall back to port 8766
            await send_notification_to_port(8766, notification)
        
        # Wait between notifications
        await asyncio.sleep(3)

async def demo_buttons():
    """Demonstrate different button configurations"""
    logger.info("=== Demonstrating Button Configurations ===")
    
    for config_name, buttons in BUTTON_CONFIGS.items():
        message = f"Button demo: {config_name} configuration"
        notification = format_notification(
            message=message,
            buttons=buttons,
            importance="medium"
        )
        
        # Try port 8765 first (more direct to overlay)
        success = await send_notification_to_port(8765, notification)
        if not success:
            # Fall back to port 8766
            await send_notification_to_port(8766, notification)
        
        # Wait between notifications
        await asyncio.sleep(3)

async def demo_random_notifications(count=5):
    """Demonstrate random notifications with various configurations"""
    logger.info(f"=== Demonstrating {count} Random Notifications ===")
    
    for i in range(count):
        # Select random message and configuration
        message = random.choice(SAMPLE_NOTIFICATIONS)
        importance = random.choice(["high", "medium", "low"])
        play_sound = random.choice([True, False])
        buttons = random.choice(list(BUTTON_CONFIGS.values()))
        
        notification = format_notification(
            message=message,
            buttons=buttons,
            importance=importance,
            play_sound=play_sound
        )
        
        # Randomly choose port
        port = random.choice([8765, 8766])
        logger.info(f"Sending random notification {i+1}/{count} to port {port}")
        
        success = await send_notification_to_port(port, notification)
        if not success:
            # Try the other port
            other_port = 8766 if port == 8765 else 8765
            await send_notification_to_port(other_port, notification)
        
        # Wait between notifications
        await asyncio.sleep(3)

async def interactive_demo():
    """Interactive demo where user can create custom notifications"""
    print("\n=== Interactive Notification Demo ===\n")
    
    while True:
        print("\n----- Create a Custom Notification -----")
        
        # Get message
        message = input("Enter notification message (or 'exit' to quit): ")
        if message.lower() == 'exit':
            break
        
        # Get importance
        importance_options = ["high", "medium", "low"]
        for i, option in enumerate(importance_options):
            print(f"{i+1}. {option}")
        importance_choice = input(f"Select importance (1-{len(importance_options)}, default=1): ")
        
        try:
            importance_idx = int(importance_choice) - 1
            importance = importance_options[importance_idx]
        except (ValueError, IndexError):
            importance = "high"  # Default
        
        # Get sound preference
        play_sound = input("Play sound? (y/n, default=y): ").lower() != 'n'
        
        # Get button configuration
        print("\nButton configurations:")
        for i, (name, _) in enumerate(BUTTON_CONFIGS.items()):
            print(f"{i+1}. {name}")
        
        button_choice = input(f"Select button configuration (1-{len(BUTTON_CONFIGS)}, default=1): ")
        
        try:
            button_idx = int(button_choice) - 1
            button_config = list(BUTTON_CONFIGS.values())[button_idx]
        except (ValueError, IndexError):
            button_config = BUTTON_CONFIGS["standard"]  # Default
        
        # Get port
        port_choice = input("Send to port (8765/8766/both, default=both): ")
        
        if port_choice == "8765":
            ports = [8765]
        elif port_choice == "8766":
            ports = [8766]
        else:
            ports = [8765, 8766]  # Default to both
        
        # Create and send notification
        notification = format_notification(
            message=message,
            buttons=button_config,
            importance=importance,
            play_sound=play_sound
        )
        
        for port in ports:
            success = await send_notification_to_port(port, notification)
            if success:
                print(f"✅ Notification sent successfully to port {port}!")
            else:
                print(f"❌ Failed to send notification to port {port}")

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Demonstrate the overlay notification system')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    args = parser.parse_args()
    
    print("\n========================================")
    print("   OVERLAY NOTIFICATION SYSTEM DEMO")
    print("========================================\n")
    
    # Check connections first
    print("Checking WebSocket server connections...")
    port_8765_available = await test_connection(8765)
    port_8766_available = await test_connection(8766)
    
    if not (port_8765_available or port_8766_available):
        print("\n❌ ERROR: No WebSocket servers are available!")
        print("Please start the notification system first:")
        print("  ./START_COMPLETE_NOTIFICATION_SYSTEM.sh")
        return
    
    print("\n✅ Connection check complete. Available servers:")
    if port_8765_available:
        print("  - Port 8765 (Primary / Direct)")
    if port_8766_available:
        print("  - Port 8766 (Proxy / Alternative)")
    
    if args.interactive:
        await interactive_demo()
    else:
        print("\nRunning automated demonstration...")
        print("(Use --interactive for manual control)\n")
        
        # Introduction notification
        intro_notification = format_notification(
            message="🎮 Notification System Demo Starting!",
            buttons=[
                {"text": "✅ Continue", "value": "continue", "style": "success"},
                {"text": "❓ Help", "value": "help", "style": "primary"}
            ],
            importance="high",
            play_sound=True
        )
        
        # Send to the first available port
        if port_8765_available:
            await send_notification_to_port(8765, intro_notification)
        elif port_8766_available:
            await send_notification_to_port(8766, intro_notification)
        
        # Wait for user to see the first notification
        await asyncio.sleep(5)
        
        # Run demos
        await demo_basic_notifications()
        await demo_buttons()
        await demo_random_notifications(3)
        
        # Completion notification
        completion_notification = format_notification(
            message="✨ Notification System Demo Complete!",
            buttons=[
                {"text": "👍 Great!", "value": "great", "style": "success"}
            ],
            importance="medium",
            play_sound=True
        )
        
        # Send to the first available port
        if port_8765_available:
            await send_notification_to_port(8765, completion_notification)
        elif port_8766_available:
            await send_notification_to_port(8766, completion_notification)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        logger.error(f"Error in demo: {e}")
        print(f"\n\nError: {e}")
    finally:
        print("\nNotification System Demo complete.")
        print("For more information, see OVERLAY_NOTIFICATION_SYSTEM_README.md")