#!/bin/bash

# Stop the agent-based system
echo "Stopping agent-based LLM system..."

# Kill server
if [ -f "pids/agent_based_llm_ws.pid" ]; then
    kill -9 $(cat pids/agent_based_llm_ws.pid) 2>/dev/null
    rm pids/agent_based_llm_ws.pid
    echo "✅ Server stopped"
fi

# Kill sensor connector
if [ -f "pids/connect_sensors.pid" ]; then
    kill -9 $(cat pids/connect_sensors.pid) 2>/dev/null
    rm pids/connect_sensors.pid
    echo "✅ Sensor connector stopped"
fi

# Kill monitor
if [ -f "pids/system_monitor.pid" ]; then
    kill -9 $(cat pids/system_monitor.pid) 2>/dev/null
    rm pids/system_monitor.pid
    echo "✅ System monitor stopped"
fi

echo "All components stopped successfully."
