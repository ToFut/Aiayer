# Neural UI Detector System

The Neural UI Detector is a state-of-the-art system for detecting and interacting with UI elements on the screen. This document provides comprehensive information about the system, its components, usage instructions, and troubleshooting tips.

## Table of Contents
- [Overview](#overview)
- [Key Components](#key-components)
- [Installation](#installation)
- [Usage](#usage)
- [Testing Framework](#testing-framework)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)
- [Architecture](#architecture)

## Overview

The Neural UI Detector uses multiple AI-based techniques to identify UI elements such as buttons, text fields, checkboxes, and other interactive components on the screen. It provides a WebSocket server interface for clients to request detection and interaction with these elements.

**Key Features:**
- Multiple detection methods: YOLO object detection, OCR, template matching, edge detection
- WebSocket API for real-time detection and interaction
- Port conflict resolution to avoid collisions with other services
- Performance monitoring and optimization
- Comprehensive testing framework

## Key Components

The system consists of the following key components:

1. **Neural UI Detector Core (`neural_ui_detector.py`)**:
   - Core detection and interaction functionality
   - Multiple detection methods
   - Interaction with UI elements (click, type, etc.)

2. **Neural UI Detector Server (`fixed_neural_ui_detector_server.py`)**:
   - WebSocket server providing API access to the detector
   - Port conflict resolution
   - Performance monitoring
   - Error handling and recovery

3. **DO Button Integration (`neural_ui_do_button_handler.py`)**:
   - Bridges Neural UI Detector with DO Button system
   - Plan management and persistence
   - Connection management with multiple services

4. **Testing Framework (`do_button_testing_framework.py`)**:
   - Comprehensive test suite for the Neural UI Detector
   - Port conflict testing
   - Detection reliability testing
   - Performance testing
   - Integration testing

5. **Test UI (`test_neural_ui_detector_fixed.html`)**:
   - HTML page with test UI elements
   - WebSocket client for interacting with the server
   - Visual feedback of detection results

6. **Launcher Script (`RUN_NEURAL_UI_DETECTOR.sh`)**:
   - Easy startup of the server in various modes
   - Test mode with automatic browser launch
   - Debug mode with enhanced logging

## Installation

### Prerequisites

- Python 3.7 or higher
- Required Python packages:
  - websockets
  - numpy
  - Pillow (PIL)
  - opencv-python (for some detection methods)
  - pyautogui (for interaction)

### Setup

1. Install required Python packages:
   ```bash
   pip install websockets numpy pillow opencv-python pyautogui
   ```

2. Optional: Install additional packages for enhanced detection:
   ```bash
   pip install ultralytics transformers easyocr
   ```

3. Make the launcher script executable:
   ```bash
   chmod +x RUN_NEURAL_UI_DETECTOR.sh
   ```

## Usage

### Starting the Server

Use the launcher script to start the Neural UI Detector server:

```bash
./RUN_NEURAL_UI_DETECTOR.sh
```

This will start the fixed version of the server on port 8768.

### Command Line Options

The launcher script supports various command line options:

- `--debug`, `-d`: Enable debug logging
- `--port PORT`, `-p PORT`: Use specific port (default: 8768)
- `--test`, `-t`: Run in test mode with test page
- `--no-browser`, `-n`: Don't open browser automatically
- `--original`, `-o`: Run original version instead of fixed version
- `--test-framework`, `-f`: Run the testing framework
- `--help`, `-h`: Show help message

Examples:
```bash
# Run fixed version in test mode with debug logging
./RUN_NEURAL_UI_DETECTOR.sh --debug --test

# Run original version
./RUN_NEURAL_UI_DETECTOR.sh --original

# Run on a specific port
./RUN_NEURAL_UI_DETECTOR.sh --port 8780

# Run the testing framework
./RUN_NEURAL_UI_DETECTOR.sh --test-framework
```

### WebSocket API

The Neural UI Detector server provides a WebSocket API with the following endpoints:

1. **Detect UI Elements**:
   ```json
   {
     "action": "detect"
   }
   ```

2. **Find Element**:
   ```json
   {
     "action": "find",
     "description": "Submit button",
     "element_type": "button"
   }
   ```

3. **Click Element**:
   ```json
   {
     "action": "click",
     "description": "Submit button",
     "element_type": "button"
   }
   ```

4. **Type Text**:
   ```json
   {
     "action": "type",
     "description": "Username field",
     "text": "user@example.com",
     "element_type": "text_field"
   }
   ```

5. **Press Key**:
   ```json
   {
     "action": "key",
     "key": "enter"
   }
   ```

6. **Execute Sequence**:
   ```json
   {
     "action": "execute",
     "steps": [
       { "action": "detect" },
       { "action": "find", "description": "Username", "element_type": "text_field" },
       { "action": "click", "description": "Username" },
       { "action": "type", "description": "Username", "text": "user@example.com" },
       { "action": "key", "key": "tab" },
       { "action": "type", "description": "Password", "text": "password123" },
       { "action": "click", "description": "Login button" }
     ],
     "abort_on_failure": true
   }
   ```

7. **Get Performance Statistics**:
   ```json
   {
     "action": "stats"
   }
   ```

## Testing Framework

The Neural UI Detector includes a comprehensive testing framework that verifies various aspects of its functionality:

1. **Port Conflict Resolution Test**:
   - Verifies that the server can handle port conflicts correctly
   - Tries to start multiple servers on the same port
   - Checks if alternative ports are selected automatically

2. **Detection Reliability Test**:
   - Runs multiple detection tests
   - Measures success rate and average execution time
   - Verifies consistent detection results

3. **Integration Test**:
   - Tests integration with the DO Button system
   - Verifies plan execution functionality
   - Checks message flow between components

4. **Performance Test**:
   - Measures detection performance under various conditions
   - Tracks execution times for different operations
   - Identifies potential bottlenecks

### Running the Testing Framework

To run the testing framework:

```bash
./RUN_NEURAL_UI_DETECTOR.sh --test-framework
```

The framework will generate a comprehensive test report that identifies any issues and measures the system's performance.

## Troubleshooting

### Common Issues

1. **Server fails to start**:
   - Check if another process is using the specified port
   - Look for error messages in the logs
   - Try starting with a different port: `./RUN_NEURAL_UI_DETECTOR.sh --port 8770`

2. **Detection hangs or times out**:
   - Check system resources (CPU, memory)
   - Try running with debugging enabled: `./RUN_NEURAL_UI_DETECTOR.sh --debug`
   - Look for error messages in the logs

3. **Poor detection accuracy**:
   - Ensure good lighting conditions
   - Use the testing framework to identify specific issues
   - Consider training or fine-tuning the detection models

4. **Port conflicts with other services**:
   - Use a different port: `./RUN_NEURAL_UI_DETECTOR.sh --port 8790`
   - Check if DO Button or other services are running on conflicting ports
   - Configure services to use non-conflicting ports

### Logs

Log files are stored in the `logs/neural_ui_detector` directory:

- `fixed_server.log`: Main server log
- `neural_detector.log`: Detection engine log
- `test_framework.log`: Testing framework log

Enable debug logging for more detailed information:

```bash
./RUN_NEURAL_UI_DETECTOR.sh --debug
```

## Advanced Configuration

### Port Configuration

The Neural UI Detector system uses the following default ports:

- Neural UI Detector Server: 8768
- DO Button Server: 8765
- DO Button Connection Bridge: 8766
- Backend Server: 8767

To avoid port conflicts, the system will automatically select alternative ports if the default ones are already in use.

### Detection Configuration

The detection system uses multiple methods with different characteristics:

1. **YOLO Object Detection**:
   - Fastest and most accurate for standard UI elements
   - Requires GPU for optimal performance
   - Can be disabled if resources are limited

2. **OCR (Optical Character Recognition)**:
   - Good for detecting text elements
   - Relatively slow but accurate
   - Resource-intensive

3. **Template Matching**:
   - Fast and reliable for known UI patterns
   - Works well with consistent UI elements
   - Less effective with dynamic content

4. **Edge Detection**:
   - Lightweight fallback method
   - Works reasonably well for basic UI elements
   - Less accurate than other methods

You can adjust which methods are used in the `neural_ui_detector.py` file.

## Architecture

The Neural UI Detector system uses a modular architecture with the following components:

1. **Detection Engine**:
   - Multiple detection methods working together
   - Element classification and filtering
   - Detection result management

2. **WebSocket Server**:
   - Client connection management
   - Command processing
   - Response handling

3. **Integration Layer**:
   - DO Button integration
   - Backend server integration
   - Plan management

4. **Testing Framework**:
   - Automated testing
   - Performance measurement
   - Reporting

The system is designed to be extensible, allowing new detection methods and integrations to be added easily.

---

For additional information or support, check the log files or contact the development team.