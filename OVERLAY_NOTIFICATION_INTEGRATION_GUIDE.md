# Overlay Notification Integration Guide

This guide explains how the notification system works between the backend components and the overlay UI.

## Problem Summary

The overlay chat application was not displaying notifications from the DO button and other backend components. The issue was due to:

1. Message format mismatches between different components
2. Port conflicts between servers
3. Connection issues between components

## Solution Architecture

The solution involves a WebSocket proxy that:

1. Bridges communication between multiple components
2. Translates message formats to ensure compatibility
3. Ensures consistent session/plan IDs across the system
4. Maintains connections to all necessary components

```
┌─────────────┐      ┌─────────────────┐      ┌─────────────────┐
│             │      │                 │      │                 │
│   Overlay   │◄────►│  WebSocket      │◄────►│  DO Button      │
│   UI        │      │  Proxy (8766)   │      │  Server (8765)  │
│             │      │                 │      │                 │
└─────────────┘      └────────┬────────┘      └─────────────────┘
                              │
                              │
                              ▼
                     ┌─────────────────┐
                     │                 │
                     │  Neural UI      │
                     │  Detector (8768)│
                     │                 │
                     └─────────────────┘
```

## Component Details

### 1. WebSocket Proxy (`fix_do_button_connection.py`)

- **Port**: 8766
- **Purpose**: Connects all components and translates message formats
- **Connections**:
  - Accepts connections from the overlay UI
  - Connects to DO Button Server (port 8765)
  - Connects to Neural UI Detector (port 8768)
  - Optional connection to Backend Server (port 8767)

### 2. Overlay UI (`NextGenAppleChatWidget.svelte`)

- **Connection**: Connects to the proxy at `ws://localhost:8766`
- **Message Format**: Expects notifications with:
  - `type: "suggestion"` or `(data.mode === 'SUGGEST' && data.notification)`
  - Content in `response` or `data.response`
  - Buttons in `buttons` or `data.buttons`

### 3. DO Button Server (`ultimate_do_button_server.py`)

- **Port**: 8765
- **Message Format**: Sends notifications as:
  - `type: "do_button_notification"`
  - Content in `content.message`
  - Buttons in `content.buttons`

### 4. Neural UI Detector (`neural_ui_detector_server.py`)

- **Port**: 8768
- **Purpose**: Provides UI detection and automation capabilities

## Message Format Translation

The proxy translates messages between formats:

```javascript
// Example: Converting DO button notification to overlay suggestion format
if (msg_type == "do_button_notification" || msg_type == "display_notification") {
    converted_data = {
        "type": "suggestion",
        "response": data.content.message,
        "buttons": data.content.buttons,
        "importance": data.importance || "high",
        "play_sound": true,
        "plan_id": data.plan_id
    }
}
```

## Setup Instructions

1. **Start Required Components**:
   ```bash
   # Start DO Button Server
   python3 ultimate_do_button_server.py
   
   # Start Neural UI Detector
   python3 neural_ui_detector_server.py
   
   # Start WebSocket Proxy
   python3 fix_do_button_connection.py
   
   # Start Overlay (should be updated to connect to port 8766)
   # The overlay will connect to the proxy on port 8766
   ```

2. **Verify Configuration**:
   - Ensure the overlay's WebSocket endpoint is set to `ws://localhost:8766`
   - Verify all servers are running and responding
   - Check proxy logs for connection confirmations

## Testing the Notification System

You can test the notification system using the provided test scripts:

```bash
# Test direct notification through proxy
python3 test_notification_to_overlay.py

# Test DO button notification conversion
python3 test_do_button_notification.py
```

## Troubleshooting

### Common Issues:

1. **Notifications not appearing in overlay**:
   - Check if proxy is running on port 8766
   - Verify overlay is connecting to port 8766 (not 8765)
   - Check proxy logs for successful message translation

2. **Connection errors**:
   - Ensure all required servers are running
   - Check for port conflicts
   - Verify proxy can connect to both the DO button server and Neural UI detector

3. **Message format issues**:
   - Check proxy logs for message translation
   - Verify that notifications have the correct format expected by the overlay

## Maintenance

When making changes to the notification system:

1. Update message format translations in the proxy if formats change
2. Ensure consistent plan/session IDs are maintained between components
3. Test with the provided test scripts to verify notifications display correctly

---

By using this proxy architecture, notifications from all backend components will be properly formatted and displayed in the overlay UI.
EOF < /dev/null