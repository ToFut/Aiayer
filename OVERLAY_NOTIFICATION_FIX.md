# Overlay Notification System Fix

## Problem

The notification system was not displaying messages in the chat overlay UI despite successful server-side processing. The investigation revealed several issues:

1. **WebSocket Handler Signature**: The WebSocket handler in `simple_do_button_fix.py` had an incorrect signature, missing the required `path` parameter.
2. **Message Format Incompatibility**: The notification format sent by various scripts didn't match what the `NextGenAppleChatWidget.svelte` component expected.
3. **Connection Issues**: Multiple services attempting to use the same port (8766) created connection conflicts.
4. **Port Routing Issues**: The system uses multiple WebSocket servers on different ports:
   - DO Button Server (port 8765)
   - Neural UI Detector Server (port 8768)
   - Backend Server (port 8767)
   - The overlay connects to port 8766, but notifications weren't properly handled

## Root Cause

The core issues identified through our investigation:

1. **Handler Signature Mismatch**: In `simple_do_button_fix.py`, the handler was defined as:
   ```python
   async def handle_websocket(websocket)  # Missing path parameter
   ```
   But the websockets library (version 15.0.1) requires:
   ```python
   async def handle_websocket(websocket, path)
   ```

2. **Message Format Requirements**: The overlay component (`NextGenAppleChatWidget.svelte`) expects notification messages to have specific properties:
   - Either `data.type === 'suggestion'` OR `data.mode === 'SUGGEST' && data.notification === true`
   - Content must be in `data.response`
   - Buttons must be in `data.buttons`
   - Must include `importance` and `timestamp` fields

## Solution Implemented

We created a robust set of tools to fix the notification system:

1. **Fixed DO Button Proxy**: Created `fixed_do_button_proxy.py` with:
   - Correct WebSocket handler signature: `async def handle_websocket(websocket, path=None)`
   - Special handling for suggestion/notification messages
   - Proper message formatting for the NextGenAppleChatWidget component
   - Robust error handling and connection management

2. **Fixed Notification Test**: Created `fixed_notification_test.py` that:
   - Tries multiple ports (8766, 8767, 8768, 8765) to find the right connection
   - Uses the exact message format expected by the NextGenAppleChatWidget component
   - Provides clear feedback about notification delivery status
   - Supports various notification options (importance, sound)

3. **Easy-to-Use Shell Script**: Created `send_overlay_notification.sh` for easy notification sending with:
   - Simple command-line interface
   - Support for different importance levels
   - Option to enable notification sounds

## Message Format

The correct notification format that works with the overlay:

```json
{
    "type": "suggestion",
    "response": "Your notification message here",
    "mode": "SUGGEST",
    "buttons": [
        {"text": "✅ Show me", "value": "show", "style": "success"},
        {"text": "❓ More info", "value": "info", "style": "primary"},
        {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
    ],
    "importance": "high",
    "play_sound": true,
    "notification": true,
    "timestamp": "2025-06-04T18:58:37.371099"
}
```

## Usage Instructions

### Starting the Notification Proxy

```bash
# Kill any existing instances
pkill -f fixed_do_button_proxy.py

# Start the fixed proxy
python3 fixed_do_button_proxy.py
```

### Sending Notifications

#### Using the Shell Script (Recommended)

```bash
# Basic notification
./send_overlay_notification.sh "Your notification message"

# With importance level (high, medium, low)
./send_overlay_notification.sh "Important notification" high

# With sound
./send_overlay_notification.sh "Notification with sound" high with-sound
```

#### Using the Python Script Directly

```bash
# Basic notification
python3 fixed_notification_test.py "Your notification message"

# With importance level and sound
python3 fixed_notification_test.py "Important notification" --importance high --sound
```

## Verification

The fix has been verified by successfully sending various notifications directly to the overlay UI using different formats, importance levels, and sound options. The notifications appear correctly in the NextGenAppleChatWidget component and include interactive buttons.

## Troubleshooting

If notifications aren't appearing:

1. Check if the fixed_do_button_proxy.py is running on port 8766 using `lsof -i :8766`
2. Verify the overlay UI is running and connected to WebSockets
3. Check the logs in `logs/do_button_fix/fixed_proxy.log` for errors
4. Try restarting both the proxy and the overlay UI
5. Test with different importance levels and message formats

## Architecture Diagram

```
┌─────────────────────────┐      ┌─────────────────────────┐
│                         │      │                         │
│  NextGenAppleChatWidget │      │  Other Notification     │
│  (Overlay UI)           │      │  Senders                │
│                         │      │                         │
└───────────┬─────────────┘      └────────────┬────────────┘
            │                                 │
            │                                 │
            ▼                                 ▼
┌───────────────────────────────────────────────────────┐
│                                                       │
│            Fixed DO Button Proxy (8766)               │
│                                                       │
└───────────┬───────────────────────────────┬───────────┘
            │                               │
            ▼                               ▼
┌───────────────────────┐      ┌───────────────────────┐
│                       │      │                       │
│  DO Button Server     │      │  Ultimate DO Button   │
│  (Port 8765)          │      │  Server (Port 8768)   │
│                       │      │                       │
└───────────────────────┘      └───────────────────────┘
```