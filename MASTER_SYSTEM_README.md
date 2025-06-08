# SensAI MASTER SYSTEM

## Overview

The SensAI MASTER SYSTEM is a comprehensive intelligent AI system that combines multiple advanced components:

- **Neural UI Detection**: AI-powered UI element detection on screen
- **DO Button Automation**: Physical automation for mouse and keyboard control
- **Contextual Memory**: Smart memory system with semantic search capabilities
- **Multi-Mode AI**: Supports multiple interaction modes (Agent, Ask, Suggest, General)
- **TeamViewer-style Remote Control**: Automated UI interaction with verification

## System Architecture

The system consists of the following key components:

1. **Enhanced Enterprise Backend** (Port 8767)
   - Core WebSocket server handling all modes and user interactions
   - Integrates with memory and execution systems
   - Handles contextual responses and agent mode planning

2. **Neural UI Detector** (Port 8768)
   - AI-powered UI element detection using multiple neural networks
   - Provides coordinates and metadata for UI elements
   - Enables intelligent automation with context awareness

3. **DO Button Server** (Port 8765)
   - Handles physical automation (mouse/keyboard)
   - Executes agent plans safely with user confirmation
   - Manages action queues and step-by-step execution

4. **Memory System**
   - Process Sensor: Monitors running applications
   - Total Screen Analyzer: Analyzes screen content
   - Smart Memory Feeder: Updates memory with relevant information
   - Semantic Search: Retrieves contextual information

## Usage

### Starting the System

Run the MASTER system startup script:

```bash
./START_MASTER_SYSTEM.sh
```

This will:
1. Initialize all required directories
2. Start all components with proper logging
3. Establish connections between components
4. Show a status summary when complete

### Interacting with the System

The system supports multiple interaction modes:

1. **General Mode**: Regular conversational AI
2. **Ask Mode**: Context-aware answers using memory
3. **Suggest Mode**: Proactive suggestions based on context
4. **Agent Mode**: TeamViewer-style UI automation with verification

### Stopping the System

To stop all components cleanly:

```bash
./STOP_MASTER_SYSTEM.sh
```

## Features

- **Beautiful Terminal Output**: Clear, colorful status information
- **Fallback Mechanisms**: Graceful degradation when components fail
- **Compatibility Mode**: Simplified implementations for neural components
- **Automated Dependency Management**: Installs required packages
- **Clear Status Reporting**: Shows which components are active and in what mode

## Advanced Configuration

The system uses several Python modules that can be configured:

- Neural UI detection sensitivity in `neural_ui_detector_server.py`
- Memory retention settings in `smart_memory_feeder.py`
- Automation safety settings in `direct_coordinate_automation.py`

## Troubleshooting

If you encounter issues, check the logs:

```bash
# Backend logs
tail -f logs/backend/enhanced_enterprise_8767.log

# Neural UI detector logs
tail -f logs/neural_ui_detector/neural_ui_detector.log

# DO Button server logs
tail -f logs/do_button/do_button_server.log

# Memory system logs
tail -f logs/memory/smart_feeder.log
```

For a comprehensive test plan, see `MASTER_SYSTEM_TEST_PLAN.md`.

## System Requirements

- Python 3.8+
- OpenCV
- YOLOv8 (for full Neural UI detection)
- PyAutoGUI (for automation)
- WebSockets support
- Available ports: 8765, 8767, 8768