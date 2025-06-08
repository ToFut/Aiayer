# Direct Coordinate Automation System

This document explains the Direct Coordinate Automation system, a reliable approach to physical automation that bypasses complex UI detection in favor of direct coordinate specifications.

## Overview

The Direct Coordinate Automation system provides a WebSocket-based interface for executing physical mouse and keyboard actions using explicit coordinate specifications. This approach prioritizes reliability over automatic element detection, making it ideal for scenarios where precise control is needed.

## Key Features

1. **Direct Coordinate Specification**: Uses explicit x,y coordinates for clicking and other mouse actions
2. **Real Physical Automation**: Controls the actual mouse and keyboard for reliable interactions
3. **Simplified Execution Flow**: Removes complex UI detection to focus on reliable execution
4. **Progress Tracking**: Provides real-time feedback on execution progress
5. **Error Recovery**: Includes retry mechanisms for failed steps
6. **Execution Plans**: Supports structured execution plans with multiple steps
7. **Direct Actions**: Offers direct action commands (click, type) for immediate execution

## How It Works

1. The system runs as a WebSocket server on port 8765
2. It accepts plans and commands from clients (like the overlay interface)
3. When execution is requested, it processes each step using the InputController
4. Each step gets direct access to the InputController for physical actions
5. Results and progress are sent back to the client in real-time

## Key Components

- **WebSocket Server**: Handles client connections and commands (port 8765)
- **InputController**: Controls physical mouse and keyboard via PyAutoGUI
- **Plan Executor**: Processes execution plans with multiple steps
- **Direct Actions**: Handles direct click and typing requests
- **Error Handling**: Includes retry mechanisms and error reporting

## Direct Coordinate vs. UI Detection

UI detection approaches try to analyze the screen to find elements based on their visual properties. While powerful, this approach can be unreliable due to:

1. Visual changes in UI elements
2. Different screen resolutions and scaling
3. Overlapping elements
4. Complex detection algorithms that can fail

Direct coordinate automation bypasses these issues by using explicit coordinates, providing a simpler and more reliable approach. While it requires more manual specification, it guarantees consistent execution.

## Usage

### Starting the System

1. Run `./RUN_DIRECT_COORDINATE_AUTOMATION.sh` to start the server
2. Open `http://localhost:8080/test_direct_coordinate_automation.html` to test functionality
3. For production use, the server is automatically started by `START_ENHANCED_SYSTEM.sh`

### Creating Plans

Plans consist of steps with actions and parameters:

```json
{
  "title": "Example Plan",
  "steps": [
    {
      "type": "click",
      "x": 500,
      "y": 300,
      "description": "Click at position (500, 300)"
    },
    {
      "type": "type_text",
      "text": "Hello, world!",
      "description": "Type some text"
    }
  ]
}
```

### Direct Actions

The system supports immediate direct actions:

1. **Direct Click**: Provide x,y coordinates for immediate clicking
2. **Direct Type**: Provide text to type immediately
3. **Hotkeys**: Execute keyboard shortcuts
4. **App Launch**: Open applications with Spotlight

## Message Types

The server accepts several message types:

1. `plan_created`: Stores a plan for execution
2. `agent_confirmation`: Executes the stored plan (DO button)
3. `direct_click`: Performs immediate click at coordinates
4. `direct_type`: Types text immediately
5. `get_screen_size`: Returns the screen dimensions

## Example Use Cases

1. **Precise Form Filling**: Click on specific form fields and input data
2. **Application Control**: Launch and interact with desktop applications
3. **Game Automation**: Control games with precise mouse positioning
4. **UI Testing**: Verify application behavior with consistent inputs
5. **Workflow Automation**: Automate repetitive tasks with keyboard shortcuts

## Testing and Debugging

Use the provided test interface (`test_direct_coordinate_automation.html`) to:

1. Visualize coordinates
2. Test direct click actions
3. Test text input
4. Create and execute simple test plans
5. View execution logs in real-time

## Troubleshooting

1. **Port Already in Use**: The script will attempt to free port 8765 automatically
2. **Missing Dependencies**: The script checks for required packages and installs them if needed
3. **Permission Issues**: May require accessibility permissions on macOS
4. **Execution Failures**: Check logs for detailed error messages
5. **Screen Scaling**: Be aware of high-DPI displays that may affect coordinate mapping

## Integration with Enhanced System

The Direct Coordinate Automation system is integrated with the Enhanced System:

1. `START_ENHANCED_SYSTEM.sh` automatically starts the direct automation server
2. All components communicate through WebSockets for real-time interaction
3. DO button functionality in the overlay uses this system for reliable execution

## Safety Features

1. **Emergency Stop**: Move mouse to any screen corner to abort (PyAutoGUI failsafe)
2. **Timeouts**: Steps have maximum execution times
3. **Step Delays**: Small delays between actions prevent system overload
4. **Controlled Execution**: One step at a time with progress tracking