# Integrated Memory System

This document explains how to use the integrated memory system that connects sensors to memory and ensures proper data flow for contextual awareness.

## System Components

The integrated memory system consists of several key components:

1. **Process Sensor:** Monitors active processes and applications
2. **Screen Sensor:** Captures screen text and visual information 
3. **Bridge Server:** Central communication hub for data routing
4. **Direct Sensor-to-Memory Integration:** Ensures data flows from sensors to memory
5. **Memory System:** Stores and manages contextual information
6. **WebSocket Servers:** Handle communication between components

## Running the System

To run the complete integrated memory system:

```
./run_integrated_memory_system.sh
```

This script:
1. Stops any existing processes
2. Fixes port configurations to ensure proper connectivity
3. Initializes necessary files with correct structure
4. Starts all required services in the correct order
5. Verifies data flow from sensors to memory
6. Monitors system health

## Checking System Status

To check the status of the context integration:

```
./check_context_integration.sh
```

This script provides a comprehensive status report including:
- Running services
- Port bindings
- Memory file health
- Data flow from sensors to memory

## Troubleshooting

If the system isn't working properly:

1. **Check Port Configuration:**
   - Bridge server should be on port 8766
   - WebSocket server should be on port 8765
   - Backend server should be on port 8767

2. **Check Sensor Data:**
   - Review `cache/process_sensor/process_cache.json` for process data
   - Review `cache/screen_sensor/last_screen.json` for screen data

3. **Check Memory Files:**
   - Check `memory/memory_state.json` for memory content
   - Check `memory/last_context.json` for context information

4. **Check Logs:**
   - `logs/memory/direct_integration.log` for memory integration issues
   - `logs/bridge/bridge_server.log` for communication issues
   - `logs/sensors/*.log` for sensor-specific issues

## Understanding Context Integration

The system ensures that sensor data flows properly from the environment to the memory system through:

1. **Direct File Monitoring:** Continuous monitoring of sensor cache files for updates
2. **Data Processing:** Extracting contextual information from raw sensor data
3. **Memory Update:** Structured updates to memory state and context files
4. **Continuous Verification:** Active monitoring to ensure data flow

## Architecture

```
Sensors (Process/Screen) → Cache Files → Direct Integration → Memory Files
                               ↓                                  ↑
                         Bridge Server --------------------------+
                               ↓
                            Memory
                               ↓
                        Context-aware LLM
```

## Key Files

- `direct_sensor_to_memory.py`: Ensures sensor data flows to memory
- `fixed_bridge_server_enhanced.py`: Routes data between components
- `enhanced_fixed_process_sensor.py`: Captures process and application data
- `enhanced_fixed_screen_sensor.py`: Captures screen text and visual data
- `monitor_context_integration.py`: Monitors system health
- `memory/memory_state.json`: Primary memory storage
- `memory/last_context.json`: Current context for LLM