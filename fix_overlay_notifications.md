# Fixing Overlay Notifications

We've identified and fixed issues with the notification system. Here are the troubleshooting steps and solutions:

## The Problem
The chat overlay was not showing notifications because messages were being sent with incorrect type formats.

## Solutions Implemented

1. **Fixed Notification Script (`send_fixed_notification.py`)**
   - Now sends messages with the correct `type: "suggestion"` format
   - Tests multiple ports (8765, 8766, 8767, 8768) to find working connections
   - Example usage: `python3 send_fixed_notification.py --message "Your notification here"`

2. **Fixed Memory Trigger Connector (`connect_memory_trigger.py`)**
   - Updated to send notifications in the compatible format
   - Now properly connects to the overlay's WebSocket server
   - Handles reconnection robustly

3. **Emergency DOM Notification System**
   - Already exists in the overlay's `notification.js`
   - Provides a direct injection method when WebSockets fail
   - Test with: `python3 test_emergency_notification.py --message "Test message"`

## How to Test

1. **Direct WebSocket Notification:**
   ```
   python3 send_fixed_notification.py --message "Testing WebSocket notification" --port 8766
   ```

2. **Comprehensive Testing (all formats, all ports):**
   ```
   python3 emergency_notification.py
   ```

3. **DOM Injection (when all else fails):**
   ```
   python3 test_emergency_notification.py
   ```

## Troubleshooting Steps

If notifications still don't appear:

1. Verify the overlay is running with:
   ```
   lsof -i :8765 -i :8766 -i :8767 -i :8768 | grep LISTEN
   ```

2. Restart the overlay components:
   ```
   cd overlay
   npm run tauri dev
   ```

3. Check Chrome DevTools console (Option+Command+J) for errors

4. Try DOM injection by manually pasting this in Chrome console:
   ```javascript
   window.sendEmergencyNotification('Manual test notification');
   ```

5. Review `/Users/segevbin/Desktop/SensAI/Aiayer/overlay/logs/ws_server_8765.log` for errors
