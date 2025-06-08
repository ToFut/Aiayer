# Overlay Notification System

This document provides a comprehensive guide to the overlay notification system, including how it works, how to use it, and how the issues were fixed.

## Overview

The overlay notification system allows sending real-time notifications to the overlay UI. These notifications appear as pop-up messages in the NextGenAppleChatWidget component and can include buttons for user interaction.

## Components

The system consists of the following components:

1. **Primary WebSocket Server** (`fixed_ws_server_8765.py`): Runs on port 8765, which the overlay UI's doButton connection uses.
2. **Proxy Server** (`fixed_minimal_do_button_proxy.py`): Runs on port 8766 and handles WebSocket connections, forwarding to the ultimate backend.
3. **Notification Utility Module** (`utils/notification_formatter.py`): Standardizes notification format across all system components.
4. **Direct Notification Scripts**:
   - `send_notification_to_port_8765.py`: Sends notifications directly to port 8765
   - `send_notification_to_port_8766.py`: Sends notifications directly to port 8766
   - `fixed_notification_test.py`: Multi-port notification tester that tries ports 8765-8768
5. **Shell Scripts**:
   - `send_notification_8765.sh`: Sends notifications directly to port 8765
   - `send_notification_8766.sh`: Sends notifications directly to port 8766
   - `send_overlay_notification.sh`: Legacy script for sending notifications through port 8766
6. **Management Scripts**:
   - `START_COMPLETE_NOTIFICATION_SYSTEM.sh`: Starts both WebSocket servers
   - `STOP_COMPLETE_NOTIFICATION_SYSTEM.sh`: Stops both WebSocket servers
   - Individual start/stop scripts for each server:
     - `start_fixed_do_button_proxy.sh` / `stop_fixed_do_button_proxy.sh`
     - `start_guaranteed_ws_8765.sh` / `stop_guaranteed_ws_8765.sh`

## How It Works

1. The system runs two WebSocket servers:
   - Port 8765: Used by the overlay UI for doButton connections (configured in overlay/src/config.js)
   - Port 8766: Used for the proxy server handling notifications and forwarding to the backend

2. When a notification message is received on either port:
   - It is formatted correctly for the NextGenAppleChatWidget component using the standard formatter
   - The formatted message is sent directly to the connected client

3. Both servers use identical message formatting to ensure consistency across all notification channels.

## Message Format

All notifications use a standardized format defined in `utils/notification_formatter.py`:

```json
{
  "type": "suggestion",
  "response": "Your notification message",
  "mode": "SUGGEST",
  "buttons": [
    {"text": "✅ Got it", "value": "understood", "style": "success"},
    {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
  ],
  "importance": "high",
  "play_sound": true,
  "notification": true,
  "timestamp": "2025-06-04T12:34:56.789Z"
}
```

## How to Use

### Complete System Management

To start the complete notification system:
```bash
./START_COMPLETE_NOTIFICATION_SYSTEM.sh
```

To stop the complete notification system:
```bash
./STOP_COMPLETE_NOTIFICATION_SYSTEM.sh
```

### Sending Notifications

#### To Port 8765 (Primary Method - Direct to Overlay)

```bash
./send_notification_8765.sh "Your notification message" [high|medium|low] [true|false]
```

Examples:
```bash
# High importance notification with sound
./send_notification_8765.sh "Critical system alert!" high true

# Medium importance notification without sound
./send_notification_8765.sh "Task completed successfully" medium false

# Default importance (high) with sound
./send_notification_8765.sh "New message received"
```

#### To Port 8766 (Alternative Method - Via Proxy)

```bash
./send_notification_8766.sh "Your notification message" [high|medium|low] [true|false]
```

Examples:
```bash
# High importance notification with sound
./send_notification_8766.sh "Critical system alert!" high true

# Low importance notification without sound
./send_notification_8766.sh "Background process completed" low false
```

#### Multi-Port Attempt (Most Reliable for Testing)

```bash
python3 fixed_notification_test.py "Your notification message" --importance [high|medium|low] [--sound]
```

Examples:
```bash
# High importance notification with sound
python3 fixed_notification_test.py "Critical alert!" --importance high --sound

# Medium importance notification without sound
python3 fixed_notification_test.py "Process completed" --importance medium

# Interactive mode (will prompt for message)
python3 fixed_notification_test.py
```

### Sending Notifications from Python

#### Method 1: Using the Standardized Formatter

```python
from utils.notification_formatter import format_notification, to_json
import asyncio
import websockets

async def send_notification(message, importance="high", play_sound=True):
    # Create notification with standardized format
    notification = format_notification(
        message=message,
        buttons=[
            {"text": "✅ Show me", "value": "show", "style": "success"},
            {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
        ],
        importance=importance,
        play_sound=play_sound
    )
    
    # Try port 8765 first (more reliable for overlay)
    try:
        async with websockets.connect("ws://localhost:8765", ping_interval=None) as ws:
            await ws.recv()  # Get welcome message
            await ws.send(to_json(notification))
            await ws.recv()  # Wait for confirmation
            return True
    except Exception as e:
        print(f"Error on port 8765: {e}")
        
        # Fall back to port 8766
        try:
            async with websockets.connect("ws://localhost:8766", ping_interval=None) as ws:
                await ws.recv()  # Get welcome message
                await ws.send(to_json(notification))
                await ws.recv()  # Wait for confirmation
                return True
        except Exception as e:
            print(f"Error on port 8766: {e}")
            return False

# Usage
asyncio.run(send_notification("Your notification message", "high", True))
```

#### Method 2: Direct Import of Utility Scripts

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the direct notification script
from send_notification_to_port_8765 import send_notification

# Usage
import asyncio
asyncio.run(send_notification("Your notification message", "medium", True))
```

## Troubleshooting

### Common Issues

#### 1. Notifications not appearing in the UI

**Symptoms:**
- The script reports success but nothing appears in the overlay UI
- No error messages are displayed

**Possible Causes and Solutions:**

a) **WebSocket servers not running**:
   - Check if both WebSocket servers are running:
     ```bash
     lsof -i :8765
     lsof -i :8766
     ```
   - If not running, start the notification system:
     ```bash
     ./START_COMPLETE_NOTIFICATION_SYSTEM.sh
     ```

b) **Overlay UI not running or connected**:
   - Verify that the overlay UI is running
   - Check the overlay logs for connection errors:
     ```bash
     cat overlay/logs/frontend.log
     ```

c) **WebSocket connection issues**:
   - Check network connectivity between components:
     ```bash
     curl -v http://localhost:8765
     curl -v http://localhost:8766
     ```
   - Restart both servers and try again:
     ```bash
     ./STOP_COMPLETE_NOTIFICATION_SYSTEM.sh
     ./START_COMPLETE_NOTIFICATION_SYSTEM.sh
     ```

d) **Message format issues**:
   - Use the standardized notification utility:
     ```python
     from utils.notification_formatter import format_notification
     ```

#### 2. Connection errors or timeouts

**Symptoms:**
- "Error connecting to ws://localhost:XXXX" messages
- Timeout waiting for welcome message

**Possible Causes and Solutions:**

a) **Server not running**:
   - Check if the server is running:
     ```bash
     ps aux | grep ws_server
     ```
   - Look for process ID in PID files:
     ```bash
     cat pids/ws_server_8765.pid
     cat pids/do_button_proxy.pid
     ```

b) **Port conflicts**:
   - Check if another process is using the port:
     ```bash
     lsof -i :8765
     lsof -i :8766
     ```
   - Kill conflicting processes:
     ```bash
     kill -9 $(lsof -t -i:8765)
     kill -9 $(lsof -t -i:8766)
     ```

c) **Network interface issues**:
   - Try specifying a different interface:
     ```bash
     # Edit fixed_ws_server_8765.py to use 0.0.0.0 instead of localhost
     # host = "0.0.0.0"  # Allow connections from any interface
     ```

#### 3. Wrong notification format

**Symptoms:**
- Notification not displaying correctly
- Strange rendering or missing elements in the UI

**Possible Causes and Solutions:**

a) **Inconsistent format**:
   - Always use the standardized formatter:
     ```python
     from utils.notification_formatter import format_notification
     notification = format_notification(message="Your message")
     ```
   - Check the JSON being sent:
     ```python
     print(json.dumps(notification, indent=2))
     ```

b) **Missing required fields**:
   - Ensure all required fields are present:
     - type: "suggestion" 
     - response: message text
     - mode: "SUGGEST"
     - notification: true

### Diagnostic Commands

Check if servers are running:
```bash
ps aux | grep fixed_ws_server_8765.py
ps aux | grep fixed_minimal_do_button_proxy.py
```

Check ports in use:
```bash
lsof -i :8765
lsof -i :8766
lsof -i :8767
lsof -i :8768
```

Check logs:
```bash
tail -f logs/ws_server_8765.log
tail -f logs/do_button_fix/fixed_proxy.log
tail -f logs/fixed_notification_test.log
```

Test connectivity:
```bash
# Try to connect to the websocket servers
python3 -c "import asyncio, websockets; asyncio.run(asyncio.wait_for(websockets.connect('ws://localhost:8765'), 2))"
python3 -c "import asyncio, websockets; asyncio.run(asyncio.wait_for(websockets.connect('ws://localhost:8766'), 2))"
```

## Advanced Usage Examples

### Custom Buttons

```bash
# Using the Python script directly
python3 - <<EOF
import asyncio
import sys
sys.path.append("$(pwd)")
from utils.notification_formatter import format_notification, to_json
import websockets

async def main():
    custom_buttons = [
        {"text": "👍 Yes", "value": "yes", "style": "success"},
        {"text": "👎 No", "value": "no", "style": "danger"},
        {"text": "🤔 Maybe", "value": "maybe", "style": "primary"}
    ]
    
    notification = format_notification(
        message="Do you want to proceed with the operation?",
        buttons=custom_buttons,
        importance="high",
        play_sound=True
    )
    
    async with websockets.connect("ws://localhost:8765", ping_interval=None) as ws:
        await ws.recv()
        await ws.send(to_json(notification))
        response = await asyncio.wait_for(ws.recv(), 5.0)
        print(f"Response: {response}")

asyncio.run(main())
EOF
```

### Scheduled Notifications

```bash
# Create a scheduled notification job
cat > scheduled_notification.sh << 'EOF'
#!/bin/bash
# Schedule a notification to be sent every hour
while true; do
    ./send_notification_8765.sh "Hourly reminder: $(date)" medium true
    sleep 3600
done
EOF

chmod +x scheduled_notification.sh
./scheduled_notification.sh &
```

### System Integration

```python
# Example: Integrate with system monitoring
import psutil
import asyncio
import time
from utils.notification_formatter import format_notification, to_json
import websockets

async def monitor_system():
    while True:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > 90:
            notification = format_notification(
                message=f"⚠️ High CPU usage detected: {cpu_percent}%",
                importance="high",
                play_sound=True
            )
            
            try:
                async with websockets.connect("ws://localhost:8765", ping_interval=None) as ws:
                    await ws.recv()
                    await ws.send(to_json(notification))
            except Exception as e:
                print(f"Error sending notification: {e}")
                
        elif memory_percent > 85:
            notification = format_notification(
                message=f"⚠️ High memory usage detected: {memory_percent}%",
                importance="medium",
                play_sound=True
            )
            
            try:
                async with websockets.connect("ws://localhost:8765", ping_interval=None) as ws:
                    await ws.recv()
                    await ws.send(to_json(notification))
            except Exception as e:
                print(f"Error sending notification: {e}")
        
        await asyncio.sleep(60)  # Check every minute

# Run the monitoring
asyncio.run(monitor_system())
```

## Technical Details

### Fixed Issues

1. **WebSocket Handler Signature**: The original handler signature was missing the `path` parameter required by the websockets library.

2. **Message Format Compatibility**: Notifications needed to be properly formatted according to the specific structure expected by the NextGenAppleChatWidget component.

3. **Port Configuration**: The overlay UI expects connections on port 8765, but our proxy was running on 8766, causing notifications to be missed.

4. **Special Message Handling**: Added dedicated handlers for notification messages on both servers.

5. **Format Standardization**: Created a utility module to ensure consistent notification format across all scripts.

### Implementation Details

The WebSocket servers handle notifications with this pattern:

```python
# Check for notification messages
if msg_type == "suggestion" or ("notification" in data and data.get("notification") == True):
    logger.info(f"Detected suggestion/notification message. Special handling.")
    
    # Create properly formatted message for NextGenAppleChatWidget
    properly_formatted_message = {
        "type": "suggestion",
        "response": data.get("response") or data.get("message") or "New notification",
        "mode": "SUGGEST",
        "buttons": data.get("buttons", []),
        "importance": data.get("importance", "high"),
        "play_sound": data.get("play_sound", True),
        "notification": True,
        "timestamp": data.get("timestamp", time.time())
    }
    
    # Send directly to client
    await websocket.send(json.dumps(properly_formatted_message))
```

## System Architecture

```
┌─────────────────┐      ┌────────────────┐      ┌───────────────┐
│  Overlay UI     │      │  WS Server     │      │  Backend      │
│  (Tauri App)    │◄────►│  (Port 8765)   │◄────►│  Services     │
└─────────────────┘      └────────────────┘      └───────────────┘
        ▲                        ▲                       ▲
        │                        │                       │
        │                        │                       │
        │                 ┌────────────────┐             │
        └────────────────►│  Proxy Server  │◄────────────┘
                          │  (Port 8766)   │
                          └────────────────┘
                                  ▲
                                  │
                          ┌───────────────┐
                          │  Notification │
                          │  Scripts      │
                          └───────────────┘
                                  ▲
                                  │
                          ┌───────────────┐
                          │ Notification  │
                          │ Formatter     │
                          └───────────────┘
```

## Notification Payload Reference

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `type` | string | Must be "suggestion" for notifications | Yes |
| `response` | string | The notification message text | Yes |
| `mode` | string | Must be "SUGGEST" for notifications | Yes |
| `buttons` | array | Array of button objects | No |
| `importance` | string | "high", "medium", or "low" | No (defaults to "high") |
| `play_sound` | boolean | Whether to play a notification sound | No (defaults to true) |
| `notification` | boolean | Must be true for notifications | Yes |
| `timestamp` | string/number | ISO timestamp or epoch seconds | No (defaults to current time) |

### Button Object Format

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `text` | string | Button label text | Yes |
| `value` | string | Action value sent when clicked | Yes |
| `style` | string | "success", "danger", "primary", etc. | No (defaults to "primary") |

## Future Improvements

1. **Unified Port**: Consider modifying the overlay to consistently use port 8766 for all connections.
2. **Notification Queue**: Implement a queue system for handling multiple notifications.
3. **Persistent Notifications**: Allow some notifications to remain visible until explicitly dismissed.
4. **Notification History**: Keep a history of past notifications for reference.
5. **Custom Sound Options**: Allow specifying different sounds for different notification types.
6. **Message Delivery Guarantees**: Add a system to ensure notifications are delivered even if the client is temporarily disconnected.
7. **Notification Categories**: Support for categorizing notifications to enable filtering.

## Conclusion

The overlay notification system provides a robust way to display notifications to users in real-time. By running WebSocket servers on both port 8765 (for the overlay's doButton connection) and port 8766 (for the proxy server), we ensure reliable notification delivery to the overlay UI regardless of which connection method is used. The standardized notification format ensures consistent appearance and behavior across all notification channels.