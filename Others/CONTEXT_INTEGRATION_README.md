# Context Integration System

This system ensures reliable integration between sensors, memory, and the LLM, enabling contextual awareness in the entire application.

## Overview

The Context Integration System solves the problem of creating a context-aware LLM by connecting sensor data to memory and LLM systems. It ensures that environmental context is properly captured, stored, and delivered to the language model for more relevant responses.

## Key Components

1. **Direct Sensor to Memory Integration** (`direct_sensor_to_memory.py`)
   - Monitors sensor cache files for changes
   - Processes sensor data and updates memory state
   - Updates context file with relevant information
   - Bypasses potential WebSocket communication issues

2. **Fixed Bridge Context Connector** (`fixed_bridge_context_connector.py`)
   - Enhanced bridge connector for WebSocket communication
   - Provides a parallel path for sensor data to reach memory
   - Formats data correctly for memory consumption
   - Handles periodic updates to ensure context freshness

3. **LLM Context Connector** (`llm_context_connector.py`)
   - Connects memory system to LLM service
   - Reads context data from memory files
   - Formats context for LLM consumption
   - Sends periodic context updates to the LLM service
   - Enriches user messages with contextual information

4. **Context Integration Monitor** (`monitor_context_integration.py`)
   - Continuously monitors system health
   - Verifies data flow from sensors to memory to LLM
   - Alerts on issues with context integration
   - Provides detailed status reporting

5. **Complete System Script** (`run_integrated_memory_system.sh`)
   - Manages all system components in the correct sequence
   - Handles process cleanup, startup, and monitoring
   - Provides verification of system health
   - Ensures proper communication between components

6. **Tauri Integration Script** (`run_tauri_with_context.sh`)
   - Runs the complete system with the Tauri overlay UI
   - Configures all services for the overlay
   - Manages WebSocket connections for context-aware UI
   - Ensures proper communication between UI and backend services

7. **Status Check Tool** (`check_context_integration.sh`)
   - Quick diagnostic of the running system
   - Verifies all components are operational
   - Checks data flow and file health
   - Reports on any issues detected

## How It Works

The system implements a multi-path approach to ensure sensor data reaches memory:

1. **File-Based Integration**:
   - Directly monitors cache files created by sensors
   - Processes updates immediately when detected
   - Updates memory state and context files without requiring intermediate services

2. **WebSocket-Based Integration**:
   - Connects to the bridge server (port 8766)
   - Receives data via WebSocket protocol
   - Processes and forwards to memory system

3. **Monitoring and Verification**:
   - Continuously checks that data is flowing correctly
   - Verifies file updates and content changes
   - Alerts on stalled or broken data flows

## Usage

### Starting the System

```bash
# Run the complete integrated system (backend only)
./fixed_context_integration_system.sh

# Run the complete system with Tauri overlay UI
./run_tauri_with_context.sh
```

### Checking System Status

```bash
# Check the status of the context integration
./check_context_integration.sh

# Check LLM connectivity specifically
./check_context_integration.sh --llm
```

### Monitoring the System

```bash
# Monitor the context integration logs
tail -f logs/monitoring/context_monitor.log

# Monitor LLM context updates
tail -f logs/llm/llm_context.log
```

## Verification

The context integration is working correctly when:

1. The memory state file (`memory/memory_state.json`) contains sensor data and is regularly updated
2. The context file (`memory/last_context.json`) contains current app and window information
3. The monitor shows "System is healthy" messages
4. There is a verifiable flow of data from sensors to memory

## Troubleshooting

### General Issues

If context integration is not working:

1. Check if all services are running with `check_context_integration.sh`
2. Verify sensor cache files are being updated
3. Check logs for specific error messages
4. Restart the system with `fixed_context_integration_system.sh`

### Overlay Issues

If you see "Disconnected from LLM service" in the Tauri overlay:

1. Verify the LLM service is running on port 8765 with `lsof -i :8765`
2. Check that the LLM context connector is running with `ps aux | grep llm_context_connector`
3. Examine the logs for context updates with `grep "Sent periodic context update" logs/llm/llm_context.log`
4. Verify the websocket config in `overlay/src/config.js` is set to the correct ports
5. Restart the overlay with `./run_tauri_with_context.sh`

### WebSocket Connectivity Issues

If WebSocket connections are failing:

1. Check all ports are available and not used by other applications
2. Verify that the correct WebSocket URLs are configured in `overlay/src/config.js`
3. Check for firewall issues that might be blocking WebSocket connections
4. Examine browser console for connection errors if using web-based overlay
5. Try restarting the bridge server with `./restart_bridge_server.sh`

## Architecture

```
Sensors (Process/Screen) → Cache Files ──┬─→ Direct Integration → Memory Files
                              │          │                           │
                              v          │                           v
                        Bridge Server ───┘                   LLM Context Connector
                              │                                      │
                              v                                      v
                    Context Integration Monitor ──────────→ LLM Service (8765)
                              │                                      │
                              v                                      v
                      WebSocket Server (8767) ◄──────────► Tauri Overlay UI
                                                           (Config-based connections)
```

The system ensures data flows reliably from sensors through memory to the LLM by implementing multiple paths and continuous monitoring. The Tauri overlay connects to all necessary services via WebSocket connections defined in the configuration, enabling a fully context-aware user interface with LLM integration.