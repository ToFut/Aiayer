# Proactive Suggestion System

This system monitors memory for actionable suggestions, pushes them to the NextGen overlay with sound notifications, and handles execution of automation plans.

## Overview

The proactive suggestion system consists of:

1. **Memory Monitoring**: Continuously scans memory for suggestion opportunities
2. **Suggestion Detection**: Identifies actions that would benefit the user
3. **Proactive Notifications**: Pushes suggestions to the overlay with sound alerts
4. **Mode Transition**: Switches to Agent mode when suggestions are accepted
5. **Plan Execution**: Executes automation plans with real UI control

## Key Components

### 1. Memory-Aware Suggestion Monitor (`memory_aware_suggestion_monitor.py`)

The core component that monitors memory for suggestion patterns:
- Scans the conscious memory file for patterns and opportunities
- Extracts suggestions with confidence scores
- Sends properly formatted notifications to the overlay
- Handles mode transitions when suggestions are accepted
- Manages execution flow when plans are approved

### 2. DO Button Server Integration

Works with any of these servers on port 8765:
- `fixed_do_button_server.py` (original implementation)
- `intelligent_do_button_server.py` (enhanced version)
- `real_do_button_executor_with_real_input.py` (current version in startup script)

The server handles:
- Real automation with mouse and keyboard control
- Step-by-step execution with progress updates
- Result reporting and error handling

### 3. Testing Scripts

Multiple scripts to test different aspects of the system:
- `test_proactive_suggestion_complete.py`: Comprehensive test suite
- `test_suggestion_with_fixed_do_button.py`: Tests DO button integration
- `send_test_suggestion.py`: Simple utility to send test suggestions

## How It Works

### Memory Monitoring

The system identifies suggestions in memory through:

1. **Explicit Patterns**: Looking for "SUGGESTION: [title] | [message] | [confidence]" format
2. **Behavioral Analysis**: Detecting repeated tasks, inefficient workflows, etc.
3. **Confidence Scoring**: Rating suggestions from 0.0 to 1.0

### Notification Flow

1. Suggestions are formatted with:
   - Sound notification flags
   - Visual highlighting
   - Interactive buttons

2. The notification appears in the NextGen overlay with:
   - Title and message
   - "Yes, help me" and "No thanks" buttons
   - Sound alert

### Mode Transition

When a user accepts a suggestion:
1. The system transitions from Suggest to Agent mode
2. A plan with detailed steps is created
3. The plan is displayed with execution options

### Plan Execution

When the user confirms execution:
1. The DO button server receives the execution request
2. The plan is executed step by step with real UI control
3. Progress updates are shown in the overlay
4. Completion status is reported

## Setup and Usage

### Starting the System

The proactive suggestion system is integrated into the main system startup script:

```bash
./START_ENHANCED_SYSTEM.sh
```

This automatically:
- Starts the memory-aware suggestion monitor
- Configures the DO button server
- Sets up all the necessary components

### Manual Testing

You can test the system manually with:

```bash
# Send a test suggestion
python3 send_test_suggestion.py "Browser Tab Organizer" "You have many tabs open. Would you like me to organize them?"

# Run comprehensive tests in manual mode
python3 test_proactive_suggestion_complete.py --manual

# Test with fixed DO button server
python3 test_suggestion_with_fixed_do_button.py
```

## WebSocket Communication

The system uses WebSocket communication for real-time interaction:
- Memory monitor connects to port 8765
- Notifications are sent as JSON payloads
- Button actions are received as JSON messages
- Progress updates are streamed during execution

## Troubleshooting

If you encounter issues:

1. **Connection Problems**: 
   - Check if the WebSocket server is running on port 8765
   - Verify that the server starts correctly in `START_ENHANCED_SYSTEM.sh`
   - Look for errors in `logs/websocket/` and `logs/memory/suggestion_monitor.log`

2. **Suggestion Detection Issues**:
   - Ensure conscious memory file exists and is properly formatted
   - Check memory monitor logs for errors in pattern recognition
   - Try sending manual suggestions for testing

3. **Execution Problems**:
   - Verify DO button server is running correctly
   - Check logs for automation errors
   - Try simpler automation plans to isolate issues

## Known Limitations

- The system requires a running WebSocket server on port 8765
- Memory monitoring relies on specific formatting patterns
- Automation execution requires proper UI element detection

## Future Enhancements

Potential improvements include:
- More sophisticated pattern recognition in memory
- Enhanced confidence scoring for suggestions
- Broader range of automation capabilities
- Improved error handling and recovery
- More natural language interaction

## Components Ready for Use

All components have been implemented and are ready for use:
- ✅ Memory-aware suggestion monitor
- ✅ DO button server integration
- ✅ WebSocket communication
- ✅ Mode transition logic
- ✅ Plan execution flow
- ✅ Comprehensive testing

The system is fully integrated with START_ENHANCED_SYSTEM.sh and will automatically start with the rest of the system.