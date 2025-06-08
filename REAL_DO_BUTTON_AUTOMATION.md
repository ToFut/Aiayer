# Real DO Button Automation System

This documentation explains how to use the Real DO Button Automation System, which connects the DO button testing framework to actual physical mouse and keyboard automation.

## Overview

The original DO button testing framework successfully generates plans but doesn't physically execute them with real mouse movements and keyboard typing. The Real DO Button Automation System fixes this by:

1. Connecting to the WebSocket server
2. Listening for plans and button actions
3. Translating them into real mouse movements and keyboard typing using PyAutoGUI
4. Providing real-time feedback on execution progress

## Components

The system consists of the following components:

1. **fixed_agent_do_button_exam.py** - The WebSocket server that generates plans
2. **fixed_agent_do_button_exam.html** - The user interface for testing
3. **real_agent_do_button_executor.py** - The executor that performs real automation
4. **run_real_do_button_executor.sh** - A launcher script that starts both components

## Prerequisites

- Python 3.6+
- PyAutoGUI (`pip install pyautogui`)
- Websockets (`pip install websockets`)
- Pynput (`pip install pynput`)

## How to Use

### Option 1: Using the Launcher Script

The easiest way to use the system is with the launcher script:

```bash
./run_real_do_button_executor.sh
```

This will:
1. Start the WebSocket server if needed
2. Open the test interface in your browser
3. Start the real executor that listens for actions
4. Ask for confirmation before enabling physical automation

### Option 2: Manual Setup

If you prefer to set up the components manually:

1. Start the WebSocket server:
   ```bash
   python fixed_agent_do_button_exam.py --port 8767
   ```

2. Open the test interface in your browser:
   ```
   file:///path/to/fixed_agent_do_button_exam.html
   ```

3. Start the real executor:
   ```bash
   python real_agent_do_button_executor.py
   ```

## Testing Workflow

1. Select an exam in the test interface
2. Enter the message shown in the instructions
3. Click "Send to Agent" to generate a plan
4. When the plan appears, click the "DO" button
5. The real executor will now physically move your mouse and type on your keyboard to execute the plan

## Safety Features

The system includes several safety features:

1. **PyAutoGUI Failsafe**: Move your mouse to any screen corner to abort execution
2. **Confirmation Prompt**: The launcher asks for confirmation before enabling automation
3. **Emergency Hotkey**: Press Ctrl+1 to immediately stop all automation
4. **Safety Levels**: The input controller has configurable safety levels

## Customizing UI Element Positions

The real executor uses a mapping of UI element names to screen coordinates. By default, it includes positions for common elements in the test scenarios. You can customize these positions by editing the `ui_elements` dictionary in `real_agent_do_button_executor.py`.

For example:
```python
self.ui_elements = {
    "search_box": (400, 200),
    "search_button": (600, 200),
    # Add your custom positions here
}
```

## Troubleshooting

If you encounter issues:

1. **Automation Not Working**: Check that you have the required permissions for input control. On macOS, you may need to grant Accessibility permissions to Terminal/your IDE.

2. **WebSocket Connection Errors**: Ensure no other services are using port 8767.

3. **Position Mapping Errors**: If the executor can't find UI elements, check the debug logs and update the element positions in the `ui_elements` dictionary.

4. **Automation Safety Stops**: If automation stops unexpectedly, you may have triggered a safety feature. Check the logs for details.

## Advanced Usage

### Adding New Exam Scenarios

To add new exam scenarios:

1. Edit `fixed_agent_do_button_exam.py` to add new exam definitions
2. Update the `ui_elements` dictionary in `real_agent_do_button_executor.py` with positions for new UI elements

### Custom Automation Logic

To implement custom automation logic:

1. Extend the `execute_step` method in `RealAgentExecutor` class
2. Add new action types and their corresponding automation logic

## Logs and Debugging

Logs are stored in:
- `logs/exams/fixed_do_button_exam.log` - Server logs
- `logs/executors/real_do_button_executor.log` - Executor logs

Use the `--debug` flag for more detailed logging:

```bash
python real_agent_do_button_executor.py --debug
```