# DO Button Physical Automation System Guide

This guide explains how to use the real physical automation system for the DO button functionality. The system allows the execution of plans with actual mouse movements and keyboard typing on your screen.

## Overview

The DO button physical automation system consists of:

1. **WebSocket Server**: Receives plans and DO button click events
2. **Input Controller**: Performs actual mouse movements and keyboard typing
3. **Plan Executor**: Executes plans step-by-step with real automation
4. **Test Interface**: HTML page to test the system functionality

## Key Components

### Real Agent DO Button Executor (`real_agent_do_button_executor.py`)

This is the main WebSocket server that handles plan execution with real physical automation. It:

- Listens for WebSocket connections on port 8765
- Processes plans sent from the client
- Executes plans using the InputController for real mouse and keyboard actions
- Sends progress updates and execution results back to the client

### Input Controller (`agent_workflow/input_controller.py`)

This module provides the actual physical automation capabilities:

- Mouse movement with human-like motion
- Mouse clicking (left, right, double, etc.)
- Keyboard typing with configurable delays
- Hotkey combinations
- Scrolling and dragging
- Safety features to prevent unintended automation

### Test Interface (`test_real_do_button.html`)

A simple HTML interface to test the DO button functionality:

- Connect to the WebSocket server
- Send test plans for browser search, clicking, and typing
- Execute plans with the DO button
- View real-time progress and results

## Running the System

You can run the DO button physical automation system in two ways:

### 1. Using the Dedicated Test Script

```bash
./RUN_REAL_DO_BUTTON_TEST.sh
```

This script:
- Starts the real agent DO button executor
- Launches a local HTTP server for the test interface
- Opens the test page in your browser
- Shows real-time logs

### 2. Using the Complete Enhanced System

```bash
./START_ENHANCED_SYSTEM.sh
```

This script starts the entire enhanced system, including:
- The real DO button executor
- The enhanced enterprise backend
- Process and screen sensors
- Memory system
- And more

## Testing the DO Button

1. Start the system using one of the scripts above
2. Open the test interface in your browser (http://localhost:8080/test_real_do_button.html)
3. Click "Connect to WebSocket" to connect to the server
4. Choose a test plan (Browser Search, Simple Click, or Text Input)
5. Click the "DO!" button to execute the plan with real automation
6. Watch as your mouse moves and keyboard types automatically!

## Safety Considerations

The physical automation system includes several safety features:

- **PyAutoGUI Failsafe**: Move your mouse to any screen corner to abort automation
- **Configurable Safety Level**: Controls the speed and delay between actions
- **Limited Scope**: Actions are confined to the visible screen
- **Emergency Stop**: Press Ctrl+C in the terminal to stop the system

## Troubleshooting

If you encounter issues with the DO button execution:

1. **Connection Problems**:
   - Check that the WebSocket server is running on port 8765
   - Verify there are no port conflicts

2. **Automation Not Working**:
   - Ensure PyAutoGUI and Pynput are installed
   - Check that your system allows programmatic input control
   - Look for permission issues (especially on macOS)

3. **Unresponsive DO Button**:
   - Restart the WebSocket server
   - Check the logs for errors
   - Make sure the plan has valid steps

## Logs and Debugging

Logs are stored in:
- `logs/executors/real_agent_do_button_executor.log` - For the standalone test
- `logs/websocket/real_do_button_executor.log` - For the enhanced system

Run with debug logging for more detailed information:
```bash
python3 real_agent_do_button_executor.py --debug
```

## Stopping the System

To stop the system:
- If running the test script, press Ctrl+C in the terminal
- If running the enhanced system, use `./STOP_ENHANCED_SYSTEM.sh`

## Additional Notes

- The system maps UI element names to screen coordinates for automation
- For production use, integrate with a more sophisticated UI element detection system
- Adjust the automation speed and behavior in the InputController class
- Create custom plans for specific automation scenarios

---

This guide should help you understand and use the DO button physical automation system effectively. If you encounter any issues or have questions, check the logs for detailed information or contact support.