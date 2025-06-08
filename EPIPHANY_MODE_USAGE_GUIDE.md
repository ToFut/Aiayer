# Epiphany Mode Usage Guide

The Epiphany mode is now fully operational. This guide explains how to use and test it.

## What is Epiphany Mode?

Epiphany mode is a proactive suggestion system that monitors your activities and automatically offers helpful suggestions when opportunities for automation or improvement are detected. It works by:

1. Monitoring your activity through the memory system
2. Analyzing patterns to identify automation opportunities
3. Sending contextual suggestions to the overlay interface
4. Executing approved suggestions when you click the action buttons

## Testing Epiphany Mode

You can test the Epiphany mode using the following scripts:

### 1. Basic Test

```bash
python3 send_test_epiphany.py
```

This sends a simple test suggestion with basic formatting.

### 2. Enhanced Suggestion Test

```bash
python3 fixed_nextgen_suggestion_handler.py "Title" "Your suggestion message"
```

Example:
```bash
python3 fixed_nextgen_suggestion_handler.py "Productivity Tip" "I noticed you're working on a development project. Would you like me to help optimize your workflow?"
```

### 3. Custom Detailed Suggestion

```bash
python3 send_custom_epiphany.py "Title" "Your detailed suggestion message"
```

Example:
```bash
python3 send_custom_epiphany.py "Workflow Optimization" "I noticed you're using multiple terminal windows. Would you like me to set up a tmux session for better productivity?"
```

This sends a detailed suggestion with multiple buttons and a complete action plan.

## Adding Custom Suggestions to Memory

To have the system automatically generate suggestions based on your memory:

1. Edit the `/Users/segevbin/Desktop/SensAI/Aiayer/memory/conscious.json` file
2. Add a new insight with the format:

```json
{
  "timestamp": "2025-06-08T12:50:00.000000",
  "memory_type": "suggestion_insight",
  "content": "SUGGESTION: Your Title | Your suggestion message | 0.9",
  "memory_id": "suggestion_1234567890"
}
```

The system will detect this pattern and automatically generate a suggestion.

## System Components

The Epiphany mode consists of the following components:

1. **WebSocket Server** (Port 8765): Handles suggestion communication
2. **Suggestion Monitor**: Scans memory for suggestion patterns
3. **Frontend Display**: Shows suggestions in the overlay interface
4. **Action Executor**: Executes approved suggestions

## Troubleshooting

If suggestions aren't appearing:

1. Check if the WebSocket server is running: `lsof -i :8765`
2. Verify the suggestion monitor is running: `ps aux | grep suggestion_monitor`
3. Restart components if needed:
   ```bash
   python3 direct_coordinate_automation.py > logs/websocket/direct_coordinate_automation.log 2>&1 &
   python3 memory_aware_suggestion_monitor.py > logs/memory/suggestion_monitor.log 2>&1 &
   ```

## Logs

Check these logs for debugging:

- WebSocket server: `logs/websocket/direct_coordinate_automation.log`
- Suggestion monitor: `logs/memory/suggestion_monitor.log`