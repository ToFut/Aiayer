# Memory Trigger System Testing Guide

This guide explains how to test the Memory Trigger system which monitors user activity, detects patterns, and generates proactive suggestions that appear in the chat interface.

## Setup Requirements

The Memory Trigger system consists of several components that need to work together:

1. **WebSocket Server (Port 8765)**: Displays notifications in the overlay
2. **Memory System**: Stores and retrieves memory items
3. **Memory Trigger Service**: Analyzes memory and generates suggestions
4. **Connector**: Bridges the Memory Trigger Service with the WebSocket Server

## Quick Start Testing

The easiest way to test the entire system is to use the automated test script:

```bash
python test_memory_trigger_system.py
```

This script will test each component of the system:
1. Verify the WebSocket server connection
2. Test direct notifications
3. Test DO button message format
4. Test custom memory items

## Starting the Complete System

To start the entire Memory Trigger system at once:

```bash
python start_memory_trigger_system.py
```

This script starts all components in the correct order:
1. WebSocket server on port 8765
2. Memory Trigger Connector (which starts the Memory System and Trigger Service)

To stop the system:

```bash
python stop_memory_trigger_system.py
```

## Testing Individual Components

If you prefer to test components individually, follow these steps:

1. **Start the WebSocket server**:
   ```bash
   python overlay/minimal_ws_server.py
   ```

2. **Test direct notification sending**:
   ```bash
   python fixed_test_direct_chat_message.py
   ```
   
   This should display a test notification in the overlay chat interface.

3. **Run the fixed memory trigger connector**:
   ```bash
   python fixed_connect_memory_trigger.py
   ```
   
   This will start the memory trigger service, load test memories, and generate suggestions based on patterns detected in those memories.

## Detailed Testing Steps

### 1. Verify WebSocket Server (Port 8765)

The WebSocket server is responsible for displaying notifications in the overlay chat interface.

```bash
# Start the minimal WebSocket server
python overlay/minimal_ws_server.py
```

This should start a server on ws://localhost:8765 that will display messages in the chat overlay.

### 2. Test Direct Notification Sending

The `send_direct_suggestion.py` script allows you to send a test notification directly to the WebSocket server:

```bash
python send_direct_suggestion.py
```

You should see a "Shopping Suggestion" appear in the chat overlay with "Yes, help me" and "No thanks" buttons.

### 3. Run the Memory Trigger Connector

The connector brings everything together, starting the memory trigger service and sending detected patterns as notifications:

```bash
python connect_memory_trigger.py
```

The connector will:
- Connect to the WebSocket server
- Initialize the memory system
- Start the memory trigger service
- Add test memory items (shopping and form filling activities)
- Monitor memory for patterns
- Send notifications to the chat interface when patterns are detected

## Troubleshooting

If you encounter issues, check the following:

### Connection Issues

- **WebSocket Connection**: Make sure the WebSocket server is running on port 8765
- **Port Mismatch**: Check if the WS_URI in the connector is set to "ws://localhost:8765"
- **Socket Error**: If you see "address already in use", another process might be using port 8765

### Message Format Issues

- **Notification Not Appearing**: Check the console logs for errors in the notification format
- **WebSocket Messages**: Ensure the WebSocket messages follow the expected format (do_button type)
- **Memory Items**: Verify that test memories are being added correctly

### Missing Dependencies

- **Import Errors**: If you see import errors, make sure all dependencies are installed
- **Missing Files**: Ensure that all required Python modules are in the correct locations

## Understanding the Logs

The connector creates detailed logs in the following locations:

- **Memory Trigger Connector**: `logs/memory/memory_trigger_connector.log`
- **Memory Trigger Service**: `logs/memory/memory_trigger.log`
- **WebSocket Server**: `logs/minimal_ws.log`

These logs can help diagnose issues with the system.

## Advanced Testing

### Adding Custom Memory Items

You can add custom memory items to test specific patterns:

```python
# Add custom memory item
memory_item = {
    "type": "web_content",
    "url": "https://example.com/product",
    "title": "Example Product",
    "searchable_text": "Your custom content here...",
    "timestamp": time.time(),
    "source": "web_browser"
}
connector.memory_system.short_term_memory.append(memory_item)
```

### Testing Custom Rules

You can add custom trigger rules to detect specific patterns:

```python
from memory.memory_trigger_service import TriggerRule, TriggerType, TriggerPriority

# Create custom rule
custom_rule = TriggerRule(
    id="custom_pattern",
    name="Custom Pattern Detection",
    description="Detects a custom pattern in memory",
    trigger_type=TriggerType.CONTENT_BASED,
    priority=TriggerPriority.HIGH,
    pattern={"keywords": ["your", "custom", "keywords"], "min_matches": 2},
    action_template={"type": "custom_action", "description": "Custom action"}
)

# Add rule to service
connector.trigger_service.rule_manager.add_rule(custom_rule)
```

## Component Architecture

The system consists of these key components:

1. **Memory Trigger Service** (`memory/memory_trigger_service.py`):
   - Monitors memory for patterns
   - Applies trigger rules to detect patterns
   - Generates notifications based on detected patterns
   - Handles suggestion generation

2. **Memory System** (`memory/memory_system.py`):
   - Stores and retrieves memory items
   - Provides access to short-term memory
   - Supports filtering memory by type and time

3. **Connector** (`connect_memory_trigger.py`):
   - Bridges memory trigger service and WebSocket server
   - Handles notification delivery
   - Converts notifications to proper WebSocket message format

4. **WebSocket Server** (`overlay/minimal_ws_server.py`):
   - Displays notifications in chat overlay
   - Handles user interaction with notifications

## Next Steps

After basic testing is working, you can:

1. **Integrate with real memory data** instead of test memories
2. **Create more specific trigger rules** for your use cases
3. **Enhance the suggestion generation** to provide more relevant suggestions
4. **Improve notification formatting** in the chat interface
5. **Add support for action execution** when users click the "Do It" button