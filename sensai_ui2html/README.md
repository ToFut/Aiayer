# SensAI.UI2HTMLMemory

A next-generation UI memory system that replaces traditional screen sensors with semantic UI tree extraction and vector-based memory storage.

## Overview

SensAI.UI2HTMLMemory is a revolutionary approach to UI understanding that:

1. **Extracts semantic UI trees** from native applications on Windows/macOS
2. **Maps UI elements to HTML** for better understanding by LLMs
3. **Stores snapshots in vector memory** (ChromaDB) for semantic querying
4. **Enables natural language queries** of UI state and history

## Key Features

- **Cross-platform support**: Windows (uiautomation) and macOS (atomacos)
- **Semantic HTML mapping**: Converts UI trees to meaningful HTML
- **Vector memory storage**: ChromaDB-based storage with semantic search
- **Natural language queries**: Find UI elements by description
- **Memory persistence**: Snapshots stored permanently for analysis
- **Real-time capture**: Live UI state monitoring

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UI Scraper    │───▶│  HTML Mapper    │───▶│  Memory Store   │
│                 │    │                 │    │                 │
│ • Windows       │    │ • UI→HTML       │    │ • ChromaDB      │
│ • macOS         │    │ • Semantic      │    │ • Vector Search │
│ • Fallback      │    │ • Accessible    │    │ • Persistence   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Installation

```bash
# Install dependencies
pip install uiautomation chromadb openai

# For macOS (optional, for better accessibility support)
pip install atomacos
```

## Quick Start

```python
from sensai_ui2html.ui2html_sensor import UI2HTMLSensor

# Create sensor
sensor = UI2HTMLSensor()

# Start capturing
sensor.start()

# Capture a snapshot
snapshot = sensor.capture_snapshot({
    "app": "Chrome",
    "action": "opened_settings"
})

# Query memory
results = sensor.query_memory("settings button", n_results=5)

# Stop sensor
sensor.stop()
```

## API Reference

### UI2HTMLSensor

The main sensor class that handles UI capture and memory operations.

#### Methods

- `start()`: Start the sensor
- `stop()`: Stop the sensor  
- `capture_snapshot(metadata)`: Capture and store UI snapshot
- `query_memory(query_text, n_results)`: Query stored snapshots
- `get_last_snapshot()`: Get the most recent snapshot
- `list_recent_snapshots(limit)`: List recent snapshots
- `get_sensor_info()`: Get sensor status and statistics

### Utility Functions

- `capture_ui_snapshot(metadata)`: One-shot snapshot capture
- `query_ui_memory(query_text, n_results)`: Direct memory query

## Usage Examples

### Basic UI Capture

```python
from sensai_ui2html.ui2html_sensor import capture_ui_snapshot

# Capture current UI state
snapshot = capture_ui_snapshot({
    "timestamp": "2024-01-15T10:30:00",
    "application": "Visual Studio Code",
    "context": "editing_python_file"
})

print(f"Captured {snapshot['element_count']} UI elements")
print(f"Generated HTML: {len(snapshot['html_content'])} characters")
```

### Semantic Memory Query

```python
from sensai_ui2html.ui2html_sensor import query_ui_memory

# Find UI elements by description
results = query_ui_memory("login form", n_results=3)

for result in results:
    print(f"Found: {result['id']}")
    print(f"Elements: {result['metadata']['element_count']}")
    print(f"Timestamp: {result['metadata']['timestamp']}")
```

### Continuous Monitoring

```python
from sensai_ui2html.ui2html_sensor import UI2HTMLSensor
import time

sensor = UI2HTMLSensor()
sensor.start()

try:
    while True:
        # Capture snapshot every 5 seconds
        snapshot = sensor.capture_snapshot({
            "monitoring": True,
            "interval": "5s"
        })
        
        print(f"Captured snapshot: {snapshot['snapshot_id']}")
        time.sleep(5)
        
except KeyboardInterrupt:
    sensor.stop()
    print("Monitoring stopped")
```

## HTML Mapping

The system maps UI elements to semantic HTML:

| UI Element | HTML Tag | Example |
|------------|----------|---------|
| Button | `<button>` | `<button class="ui-button">Save</button>` |
| Text Field | `<input type="text">` | `<input type="text" class="ui-edit" data-value="username">` |
| Checkbox | `<input type="checkbox">` | `<input type="checkbox" class="ui-checkbox">` |
| Menu | `<nav>` | `<nav class="ui-menu" role="menu">` |
| Window | `<section>` | `<section class="ui-window" role="dialog">` |

## Memory Storage

Snapshots are stored in ChromaDB with:

- **Vector embeddings** for semantic search
- **Metadata** including UI tree, HTML, timestamps
- **Text extraction** for querying
- **Element counting** for analysis

## Configuration

```python
config = {
    "chroma_path": "./chroma_db",
    "collection_name": "ui_snapshots",
    "embedding_model": "all-MiniLM-L6-v2",
    "max_elements": 1000,
    "capture_interval": 1.0
}

sensor = UI2HTMLSensor(config)
```

## Integration with Existing Systems

The UI2HTML sensor can replace existing screen sensors:

```python
# Old screen sensor
from sensors.screen_sensor import ScreenSensor
sensor = ScreenSensor()

# New UI2HTML sensor
from sensai_ui2html.ui2html_sensor import UI2HTMLSensor
sensor = UI2HTMLSensor()

# Same interface, better capabilities
snapshot = sensor.capture_snapshot()
```

## Performance

- **Capture time**: ~100-500ms per snapshot
- **Memory usage**: ~1-5MB per snapshot
- **Query speed**: ~10-100ms for semantic search
- **Storage**: Efficient vector compression

## Troubleshooting

### Common Issues

1. **Import errors**: Install required dependencies
2. **Permission denied**: Grant accessibility permissions (macOS)
3. **No UI detected**: Check if applications are accessible
4. **Memory errors**: Ensure sufficient disk space for ChromaDB

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

sensor = UI2HTMLSensor()
# Detailed logs will be shown
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Roadmap

- [ ] Linux support
- [ ] Mobile UI extraction
- [ ] Advanced HTML templates
- [ ] Real-time UI change detection
- [ ] Integration with LLM agents
- [ ] Web UI dashboard
- [ ] API server mode 