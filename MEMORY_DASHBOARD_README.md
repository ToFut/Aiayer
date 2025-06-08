# Neural Memory Dashboard

## Overview

The Neural Memory Dashboard provides a comprehensive visualization and monitoring interface for the AI memory system. It offers a brain-like visualization of memory connections, detailed metrics, and system health monitoring for all memory types including:

- **Short-Term Memory**: Recent, temporary memory storage
- **Context Memory**: Current operational context
- **Long-Term Memory**: Persistent knowledge and important information
- **Conscious Memory**: Active processing and semantic memory formation

## Features

- **Neural Network Visualization**: Interactive 3D visualization of memory nodes and connections
- **Memory Type Analytics**: Detailed metrics for each memory type
- **System Health Monitoring**: Real-time monitoring of memory utilization, coherence, and performance
- **Memory Optimization**: Automatic optimization recommendations
- **Memory Explorer**: Browse and search memory contents
- **Detailed Reports**: Generate comprehensive memory system reports

## Getting Started

### Starting the Dashboard

To start the memory dashboard server:

```bash
./start_memory_dashboard.sh
```

This will:
1. Start the memory dashboard server on port 8082
2. Open the dashboard in your default browser
3. Begin monitoring the memory system

### Stopping the Dashboard

To stop the memory dashboard server:

```bash
./stop_memory_dashboard.sh
```

## Dashboard Sections

### Overview

The main dashboard page provides a high-level overview of the memory system, including:

- Memory type counts and statistics
- Neural memory network visualization
- Recent memory activity
- System health metrics

### Brain Map

An interactive 3D visualization of the memory network showing:

- Memory nodes by type (color-coded)
- Connections between related memories
- Memory activation patterns
- Node clustering by memory type and relation

### Memory Types

Detailed sections for each memory type:

- **Short-Term Memory**: Recent memories, expiration times, and activity patterns
- **Context Memory**: Active contexts, context types, and update frequencies
- **Long-Term Memory**: Persistent memories, importance levels, and retrieval metrics
- **Conscious Memory**: Sensor data processing, insight generation, and memory formation

### Memory Analytics

Comprehensive analytics for monitoring and optimizing the memory system:

- Memory efficiency metrics
- Memory transition flow
- Retrieval performance
- System health trends
- Optimization recommendations

## Integration with Memory System

The dashboard integrates with the memory system to provide real-time monitoring. It connects to:

- The main memory system for short-term, context, and long-term memory metrics
- Conscious memory for processing metrics and insight generation
- Sensor data buffers for input monitoring

## Technical Details

The dashboard consists of:

- **Backend**: Flask-based server with memory monitoring API endpoints
- **Frontend**: Interactive visualization using D3.js and Force Graph
- **Metrics Collection**: Real-time metrics collection from memory system
- **Analytics Engine**: Memory system health analysis and optimization

## Customizing the Dashboard

You can customize the dashboard by modifying:

- `web/dashboard/templates/memory_dashboard.html`: Frontend layout and design
- `web/dashboard/static/js/memory_dashboard.js`: Visualization logic and interactivity
- `memory/enhanced_memory_dashboard.py`: Backend metrics collection and analysis
- `memory/memory_dashboard_server.py`: API endpoints and server configuration

## Troubleshooting

### Dashboard Not Starting

If the dashboard fails to start:

1. Check the logs at `logs/memory_dashboard_server.log`
2. Ensure Flask and Flask-CORS are installed (`pip install flask flask-cors`)
3. Verify port 8082 is not in use by another application

### Visualization Issues

If the brain visualization doesn't appear:

1. Check your browser console for JavaScript errors
2. Ensure D3.js and Force Graph libraries are loaded correctly
3. Try a different browser (Chrome or Firefox recommended)

### Data Not Updating

If dashboard data is not updating:

1. Check the connection to the memory system
2. Restart the dashboard server
3. Verify the memory system is running and accessible