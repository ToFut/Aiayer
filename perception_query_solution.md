# Fixing Perception Queries in Agent-Based LLM System

This document explains how to fix the perception query handling issue in the Agent-Based LLM WebSocket server system. The problem occurs when the user asks "what am I seeing?" or similar queries, and the LLM response doesn't include information about what's on the screen.

## Root Cause Analysis

The root cause of the perception query issue was identified:

1. **Missing Memory Connection**: The memory system wasn't properly receiving screen content from sensors
2. **Empty Screen Content**: When perception queries were made, the context retrieved from memory had empty screen content (length: 0)
3. **Initialization Issues**: The memory system and sensor caches weren't properly initialized at startup

## Solution Components

The following components were enhanced to fix the issue:

### 1. Enhanced `run_agent_based_llm.sh` Script

The startup script now:
- Creates all necessary directories for memory and sensors
- Initializes detailed sensor cache files with proper content
- Pre-populates the memory system with screen content
- Establishes proper connections between sensors and memory
- Includes automated cleanup for logs and cache to prevent excessive storage usage
- Includes auto-verification to ensure screen content is available
- Creates a monitoring system to maintain system health

### 2. Updated Memory Initialization

The memory system now receives direct initialization with:
- Default screen content in `memory_state.json`
- Pre-populated context in `last_context.json`
- Proper directory structure for all memory components

### 3. Enhanced Sensor-to-Memory Connection

The `connect_sensors.py` script was enhanced to:
- Run immediately during startup to update memory with sensor data
- Continuously update the memory system with sensor data
- Include verification to ensure screen content is properly stored
- Format sensor data correctly for the memory system

### 4. Improved Perception Query Detection

The agent's perception query detection was improved:
- Added more patterns for identifying perception queries
- Enhanced semantic search to prioritize screen content for perception queries
- Added context verification to ensure screen content is available

## How to Test the Solution

1. Run the enhanced startup script:
   ```bash
   ./run_agent_based_llm.sh
   ```

2. Test perception queries with the testing script:
   ```bash
   python3 test_perception_query.py
   ```

3. Monitor logs for verification:
   ```bash
   tail -f logs/agent_based_llm_ws.log
   ```

4. Look for entries that confirm:
   - "Screen content length: [non-zero number]"
   - "Memory verification results: ✅"
   - "Perception query handled correctly"

## Troubleshooting

If perception queries still don't work:

1. Check if screen cache is populated:
   ```bash
   cat cache/screen_sensor/last_screen.json
   ```

2. Verify memory state contains screen content:
   ```bash
   cat memory/memory_state.json
   ```

3. Run the sensor connector manually to update memory:
   ```bash
   python3 connect_sensors.py --verify
   ```

4. Restart the system with the enhanced script:
   ```bash
   ./stop_agent_system.sh
   ./run_agent_based_llm.sh
   ```

The most important aspect of fixing perception queries is ensuring that the memory system has access to screen content data when the LLM generates a response.