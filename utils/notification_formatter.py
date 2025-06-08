#!/usr/bin/env python3
"""
Notification Formatter Utility

This module provides a standardized way to format overlay notifications
to ensure consistency across all components of the notification system.
"""

import json
from datetime import datetime
import logging
import os

# Create utils directory if it doesn't exist
os.makedirs('utils', exist_ok=True)

# Configure logger
logger = logging.getLogger("notification_formatter")

def format_notification(
    message, 
    buttons=None, 
    importance="high", 
    play_sound=True, 
    mode="SUGGEST",
    timestamp=None
):
    """
    Create a properly formatted notification message for the overlay UI.
    
    Args:
        message (str): The notification message to display
        buttons (list, optional): List of button objects. Defaults to standard buttons.
        importance (str, optional): Importance level ("high", "medium", "low"). Defaults to "high".
        play_sound (bool, optional): Whether to play a sound. Defaults to True.
        mode (str, optional): The mode for the notification. Defaults to "SUGGEST".
        timestamp (str/float, optional): Custom timestamp. Defaults to current time.
        
    Returns:
        dict: Properly formatted notification object
    """
    if buttons is None:
        buttons = [
            {"text": "✅ Got it", "value": "understood", "style": "success"},
            {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
        ]
        
    if timestamp is None:
        timestamp = datetime.now().isoformat()
        
    # Format the notification according to NextGenAppleChatWidget expectations
    notification = {
        "type": "suggestion",
        "response": message,
        "mode": mode,
        "buttons": buttons,
        "importance": importance,
        "play_sound": play_sound,
        "notification": True,
        "timestamp": timestamp
    }
    
    return notification

def to_json(notification):
    """Convert notification to JSON string"""
    return json.dumps(notification)
    
def log_notification(notification):
    """Log notification details"""
    logger.info(f"Notification: {notification.get('response')} (Importance: {notification.get('importance')})")
    return notification