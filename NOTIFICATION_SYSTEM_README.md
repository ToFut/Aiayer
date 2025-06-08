# Notification System Documentation

This document explains how the notification system works and how to use it.

## Overview

The notification system enables sending proactive suggestions and notifications to the overlay UI. It consists of several components:

1. **Auto Suggestion System**: Periodically sends notifications based on system activity
2. **Direct Notification Test**: Tests if notifications can be sent to the overlay
3. **Overlay Notification Test**: Comprehensive testing of all notification formats and ports
4. **Send Notification**: Simple command-line tool for sending notifications

## System Architecture

The notification system communicates with the overlay UI through WebSocket connections on ports 8765, 8767, and 8768. Port 8766 appears to be inactive or not properly configured.

- **Port 8765**: Direct Coordinate Automation Server - Accepts notifications and responds reliably
- **Port 8767**: Backend Server - Accepts notifications and forwards them to the overlay
- **Port 8768**: Neural UI Server - Accepts notifications and forwards them to the overlay

Notifications can be sent in various formats, with the "suggestion" format being the most reliable.

## Installation and Setup

All necessary files are already installed. The notification system scripts are:

- `START_NOTIFICATION_SYSTEM.sh`: Starts the automatic suggestion system
- `STOP_NOTIFICATION_SYSTEM.sh`: Stops the automatic suggestion system
- `RESTART_NOTIFICATION_SYSTEM.sh`: Restarts the system and tests it
- `auto_suggestion_system.py`: Core system that sends periodic suggestions
- `direct_notification_test.py`: Tests if notifications work
- `overlay_notification_test.py`: Comprehensive testing tool
- `send_notification.py`: Simple command-line tool for sending notifications

## Usage

### Starting the System

To start the notification system, run:

```bash
./START_NOTIFICATION_SYSTEM.sh
```

This will:
1. Test if notifications are working
2. Start the automatic suggestion system

### Stopping the System

To stop the notification system, run:

```bash
./STOP_NOTIFICATION_SYSTEM.sh
```

### Restarting the System

If you need to restart the system (e.g., if it reached the maximum notifications per hour), run:

```bash
./RESTART_NOTIFICATION_SYSTEM.sh
```

This will:
1. Stop the current notification system
2. Start a fresh instance
3. Test notifications on all working ports

### Sending Manual Notifications

To send a manual notification, use the `send_notification.py` script:

```bash
python send_notification.py "Your message here" --port 8765 --format suggestion --sound
```

Options:
- `--port`: WebSocket port (8765, 8767, or 8768)
- `--format`: Notification format (suggestion, message, or legacy)
- `--importance`: Notification importance (low, medium, or high)
- `--sound`: Play a sound with the notification

### Testing the System

If you want to test if notifications are working, use one of these tools:

1. Simple test:
```bash
python direct_notification_test.py
```

2. Comprehensive test:
```bash
python overlay_notification_test.py
```

3. Test a specific port and format:
```bash
python overlay_notification_test.py 8765 suggestion "Test message"
```

## Troubleshooting

If you're not seeing notifications in the overlay UI:

1. Check if the ports are active:
```bash
lsof -i :8765,8766,8767,8768
```

2. Make sure the overlay UI is running:
```bash
ps aux | grep -E "overlay|tauri"
```

3. Try sending notifications to all ports:
```bash
./RESTART_NOTIFICATION_SYSTEM.sh
```

4. Check the logs:
```bash
tail -f logs/notification_system.log
```

## Limitations

- The system is limited to 3 suggestions per hour to avoid overwhelming the user
- Port 8766 appears to be malfunctioning and should not be used
- Some notification formats may not display properly in all modes

## Technical Details

The notification system bypasses the problematic LLM and plan persistence systems by sending notifications directly to the WebSocket servers. This ensures that notifications always reach the overlay UI, even when other systems are experiencing issues.

### Notification Formats

1. **Suggestion Format**:
```json
{
  "type": "suggestion",
  "response": "Your message here",
  "buttons": [
    {"text": "✅ Got it", "value": "understood", "style": "success"},
    {"text": "❌ Dismiss", "value": "dismiss", "style": "danger"}
  ],
  "importance": "high",
  "play_sound": true,
  "notification": true,
  "plan_id": "unique_id_here",
  "timestamp": "2025-06-04T13:48:00.000Z"
}
```

2. **Message Format**:
```json
{
  "type": "message",
  "message": "Your message here",
  "mode": "SUGGEST",
  "buttons": [...],
  "importance": "high",
  "play_sound": true,
  "notification": true,
  "timestamp": "2025-06-04T13:48:00.000Z"
}
```

3. **Legacy Format**:
```json
{
  "success": true,
  "response": "Your message here",
  "mode": "SUGGEST",
  "notification": true,
  "play_sound": true,
  "importance": "high",
  "buttons": [...],
  "interactive": true,
  "timestamp": "2025-06-04T13:48:00.000Z"
}
```

## Final Notes

The notification system is now fully operational and can be used to send notifications and suggestions to the overlay UI. It bypasses the problematic components that were preventing notifications from being displayed, ensuring reliable delivery.

If you need to modify the system or add new features, the source code is well-documented and modular.