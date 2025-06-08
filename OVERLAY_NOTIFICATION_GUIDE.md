# Overlay Notification System Guide

This guide explains how to send notifications to the overlay system. We have implemented two approaches:

1. **WebSocket Direct Notification**: Send messages directly to the overlay via WebSocket
2. **Emergency DOM Notification**: Inject notifications directly into the DOM when WebSocket fails

## Quick Start

Use our simplified script to send notifications:

```bash
# Send a basic notification
python3 send_overlay_notification.py --message "Your important message here"

# Use custom importance level (high, medium, low)
python3 send_overlay_notification.py --importance medium --message "Medium priority alert"

# Send without sound
python3 send_overlay_notification.py --no-sound --message "Silent notification"

# Use custom buttons
python3 send_overlay_notification.py --custom-buttons --message "Custom button notification"

# Try all available ports to see which ones work
python3 send_overlay_notification.py --port 0 --message "Testing all ports"
```

## WebSocket Communication Details

The overlay system has multiple WebSocket endpoints:

| Port | Path | Status | Format | Notes |
|------|------|--------|--------|-------|
| 8765 | / | ✓ | Error on unknown message types | Responds to messages but rejects all formats we tried |
| 8766 | / | ✅ | `suggestion` type | This is the most reliable port for notifications |
| 8767 | /ws | ✓ | Requires registration | Backend server, accepts registration but rejects message formats |

### Working Message Format (Port 8766)

The following format works reliably on port 8766:

```json
{
  "type": "suggestion",
  "response": "Your notification message here",
  "buttons": [
    {"text": "Button 1", "value": "btn1", "style": "success"},
    {"text": "Button 2", "value": "btn2", "style": "danger"}
  ],
  "importance": "high",
  "play_sound": true,
  "plan_id": "unique_id_here",
  "timestamp": "ISO timestamp here"
}
```

## Emergency DOM Notification

If WebSocket communication fails, we've implemented a fallback system that injects notifications directly into the DOM. 

### Setup

1. We've added `notification.js` to `overlay/dist/` folder
2. We've included this script in `overlay/dist/index.html`

### Usage from Console

You can trigger a notification directly from the browser console:

```javascript
// Basic notification
window.sendEmergencyNotification("Your message here");

// Custom notification with buttons and importance
window.sendEmergencyNotification(
  "Custom notification with buttons", 
  [
    {text: "OK", value: "ok", style: "success"},
    {text: "Cancel", value: "cancel", style: "danger"}
  ],
  "medium" // importance: high, medium, or low
);
```

### Technical Details

The emergency notification system:

1. Attempts to find and use existing WebSocket connections in the Svelte app
2. Falls back to direct DOM manipulation if WebSocket access fails
3. Includes animations, sounds, and automatic cleanup
4. Provides visual differentiation based on importance levels

## Troubleshooting

If notifications aren't appearing:

1. Check browser console for errors
2. Verify that `notification.js` is loaded in the overlay HTML
3. Try different ports to see which ones are currently working
4. Test the emergency notification via browser console
5. Restart the overlay: `cd overlay && npm run tauri dev`

## Example Implementation

```python
import asyncio
import websockets
import json
import uuid
from datetime import datetime

async def send_overlay_notification(message, importance="high", play_sound=True):
    """Send a notification to the overlay"""
    ws_url = "ws://localhost:8766"
    
    async with websockets.connect(ws_url) as ws:
        # Wait for welcome message
        await ws.recv()
        
        # Create notification
        notification = {
            "type": "suggestion",
            "response": message,
            "buttons": [
                {"text": "OK", "value": "ok", "style": "success"},
                {"text": "Dismiss", "value": "dismiss", "style": "danger"}
            ],
            "importance": importance,
            "play_sound": play_sound,
            "plan_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat()
        }
        
        # Send notification
        await ws.send(json.dumps(notification))
        
        # Wait for response
        try:
            response = await asyncio.wait_for(ws.recv(), timeout=2.0)
            return True
        except asyncio.TimeoutError:
            return False
```