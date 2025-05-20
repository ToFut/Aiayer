# SensAI Application Detection System

This document provides an overview of the enhanced application detection system for SensAI, which enables the system to recognize any application the user is interacting with, not just Gmail.

## Components

The application detection system consists of several components that work together:

1. **Enhanced Application Detector** (`enhanced_app_detection.py`):
   - Comprehensive detection of application types using LLaVA
   - Large database of application signatures for specific recognition
   - Pattern-based app classification for high accuracy

2. **UI Element Detector** (`ui_element_detector.py`):
   - Specialized detection of application-specific UI elements
   - Identification of actionable components in interfaces
   - Analysis of interface patterns and workflows

3. **Unified Application Detection System** (`unified_app_detection.py`):
   - Continuous monitoring of application usage
   - Detection of application changes and view changes
   - Tracking of application sessions and statistics

4. **Memory Integration** (`app_aware_memory_integrator.py`):
   - Integration with the memory system for context-aware responses
   - Boosting of application-relevant memories
   - Tracking of application history and usage patterns

## Key Features

- **Universal Application Detection**: Works with all application types, not just Gmail
- **Enhanced LLaVA Integration**: Improved prompts for precise application identification
- **Application Signatures**: Database of 50+ applications with distinctive UI patterns
- **UI Element Analysis**: Specialized detection of interface components by type
- **Memory System Integration**: Boosts relevant memories based on application context
- **Session Tracking**: Records application usage sessions and statistics
- **Context-Aware Responses**: LLM queries can be adapted to current application context

## Using the Application Detection System

### Quick Start

To run a quick test of the application detection system:

```bash
# Test on current screen
python test_app_detection_system.py

# Test with UI element analysis
python test_app_detection_system.py --ui

# Use existing screenshot
python test_app_detection_system.py --screenshot path/to/screenshot.png
```

### Continuous Detection

To run continuous application detection:

```bash
# Run for 1 minute with 5-second intervals
python test_app_detection_system.py --continuous --duration 60 --interval 5
```

### Integrating with Memory System

```python
# Example of using the memory integrator in a project
from app_aware_memory_integrator import AppAwareMemoryIntegrator

# Create integrator
integrator = AppAwareMemoryIntegrator()

# Start continuous detection
integrator.start()

# Boost memories for a query based on current application
boost_factor = integrator.boost_relevant_memories("How do I format this document?")

# Get current application context
context = integrator.get_current_context()
print(f"Current application: {context.app_name}")
print(f"Current view: {context.view_name}")

# Stop when done
integrator.stop()
```

## File Overview

- `enhanced_app_detection.py`: Core application detection with app signatures
- `ui_element_detector.py`: Specialized UI element analysis
- `unified_app_detection.py`: Continuous application monitoring
- `app_aware_memory_integrator.py`: Memory system integration
- `test_app_detection_system.py`: Test script demonstrating all functionality

## Requirements

- Python 3.8+
- Ollama with LLaVA model running locally or remotely
- Required packages: `pillow`, `aiohttp`, `mss`

## Implementation Details

### Application Signatures

The system uses a database of application signatures to improve detection accuracy, with each signature containing:

- Name patterns (e.g., "gmail", "google mail")
- UI elements specific to the application
- Common views and modes
- Application-specific workflows

### Detection Process

1. Capture screenshot
2. Send to LLaVA with enhanced prompt
3. Extract application name, view, and workflow
4. Match against signature database
5. Extract UI elements and patterns
6. Update application context
7. Integrate with memory system

### LLaVA Integration

The system uses a specialized LLaVA prompt that instructs the model to:

1. Identify the specific application (not just the category)
2. Determine the current view or mode
3. Identify UI components and their functions
4. Determine what the user is doing (workflow)
5. Look for application-specific patterns

### Memory Boosting

When the user makes a query, the system:

1. Checks if the query is relevant to the current application
2. Boosts the relevance of memories related to that application
3. Provides more contextually appropriate responses

## Example Applications Supported

- Productivity: Microsoft Office (Word, Excel, PowerPoint), Google Workspace (Docs, Sheets, Slides)
- Communication: Gmail, Outlook, Slack, Teams, Discord, WhatsApp
- Development: VS Code, JetBrains IDEs, Sublime Text
- Browsers: Chrome, Firefox, Safari
- Design: Photoshop, Illustrator, Figma
- And many more (50+ applications with signatures)

## Extending the System

To add support for additional applications:

1. Add new application signatures to `enhanced_app_detection.py`
2. Add UI element patterns to `ui_element_detector.py`
3. Update the LLaVA system prompt if necessary