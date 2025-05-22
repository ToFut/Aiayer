# Conscious Memory System

This module provides a comprehensive memory system that integrates data from various sensors (screen, process, file) to create a unified conscious memory representation.

## Overview

The Conscious Memory System collects and processes data from multiple sensors:

1. **Screen Sensor**: Captures screen contents and metadata
2. **Process Sensor**: Monitors running applications and processes
3. **File Sensor**: Tracks file system activities

This data is integrated and processed to generate insights about the user's current context and activity.

## Components

- **update_conscious.py**: Core script that integrates sensor data into conscious memory
- **memory_system.py**: Memory management system that handles different memory types
- **memory.py**: Base memory classes for conversation and context memory
- **conscious_memory.py**: Processes sensor data and generates insights

## How to Use

### Starting the Memory System

To start the memory system, run the provided shell script:

```bash
./start_memory_system.sh
```

Options:
- `-i <seconds>`: Set update interval (default: 30 seconds)
- `-v`: Enable verbose mode

Example:
```bash
./start_memory_system.sh -i 15 -v
```

### Manual Update

To manually update the conscious memory once:

```bash
cd memory
python3 update_conscious.py
```

## Data Structure

The conscious memory is stored in `memory/conscious.json` with the following structure:

```json
{
  "timestamp": "2025-05-20T00:00:00.000Z",
  "sensor_buffers": {
    "screen": [...],
    "process": [...],
    "file": [...]
  },
  "insights": [...],
  "system_state": {
    "last_update": "2025-05-20T00:00:00.000Z",
    "last_insight_generation": "2025-05-20T00:00:00.000Z"
  }
}
```

- **sensor_buffers**: Contains recent data from each sensor type
- **insights**: Generated insights based on sensor data
- **system_state**: Status information about the memory system

## Integration with LLM

The memory system can be integrated with an LLM by using the generated prompt that combines all sensor data. The prompt structure includes:

1. Recent insights from all sensors
2. Current active applications
3. Recent file activity
4. An analysis request for the LLM

## Troubleshooting

- Logs are stored in `logs/memory_update.log` and `logs/memory_runner.log`
- Make sure all sensors are running correctly
- Check that the cache directory contains recent sensor data
- Ensure proper permissions for file operations