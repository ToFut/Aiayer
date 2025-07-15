# Migration Guide: Replacing Screen Sensors with UI2HTML

This guide shows how to migrate from existing screen sensors to the new SensAI.UI2HTMLMemory system.

## Quick Migration

### 1. Install Dependencies

```bash
pip install uiautomation chromadb openai
```

### 2. Replace Import Statements

**Before:**
```python
from sensors.screen_sensor import ScreenSensor
# or
from sensors.basic_screen_sensor import BasicScreenSensor
```

**After:**
```python
from sensai_ui2html.integration import ScreenSensorReplacement
# or for direct functions
from sensai_ui2html.integration import capture_screen
```

### 3. Update Sensor Creation

**Before:**
```python
sensor = ScreenSensor()
# or
sensor = BasicScreenSensor(config)
```

**After:**
```python
sensor = ScreenSensorReplacement()
# or
sensor = ScreenSensorReplacement(config)
```

### 4. Update Method Calls

The interface is compatible, so most method calls work the same:

```python
# Start sensor
sensor.start()

# Capture screen
screen_data = sensor.capture_screen(metadata)

# Stop sensor
sensor.stop()

# Get sensor info
info = sensor.get_sensor_info()
```

## Enhanced Capabilities

### New Features Available

1. **Semantic Memory Query**
```python
# Find UI elements by description
results = sensor.query_ui_memory("login button", n_results=5)
for result in results:
    print(f"Found: {result['id']}")
    print(f"HTML: {result['metadata']['html_content']}")
```

2. **HTML Generation**
```python
screen_data = sensor.capture_screen()
html_content = screen_data['html_content']
print(f"Generated HTML: {html_content}")
```

3. **Memory Persistence**
```python
# Snapshots are automatically stored in ChromaDB
# Query historical UI states
results = sensor.query_ui_memory("settings dialog", n_results=10)
```

## Advanced Integration

### Using the Main UI2HTML Sensor

For advanced features, use the main sensor directly:

```python
from sensai_ui2html.ui2html_sensor import UI2HTMLSensor

sensor = UI2HTMLSensor()
sensor.start()

# Capture with metadata
snapshot = sensor.capture_snapshot({
    "app": "Chrome",
    "action": "opened_settings",
    "user": "john_doe"
})

# Query memory
results = sensor.query_memory("settings button", n_results=3)

# List recent snapshots
recent = sensor.list_recent_snapshots(limit=10)

sensor.stop()
```

### Direct Functions

For simple one-shot operations:

```python
from sensai_ui2html.ui2html_sensor import capture_ui_snapshot, query_ui_memory

# Capture snapshot
snapshot = capture_ui_snapshot({"context": "testing"})

# Query memory
results = query_ui_memory("button", n_results=5)
```

## Configuration

### Basic Configuration

```python
config = {
    "chroma_path": "./chroma_db",
    "collection_name": "ui_snapshots",
    "max_elements": 1000,
    "capture_interval": 1.0
}

sensor = ScreenSensorReplacement(config)
```

### Advanced Configuration

```python
config = {
    "chroma_path": "./chroma_db",
    "collection_name": "ui_snapshots",
    "embedding_model": "all-MiniLM-L6-v2",
    "max_elements": 1000,
    "capture_interval": 1.0,
    "html_generation": True,
    "memory_persistence": True,
    "semantic_search": True
}

sensor = UI2HTMLSensor(config)
```

## Data Format Changes

### Screen Data Structure

**Before:**
```python
{
    "timestamp": "2024-01-15T10:30:00",
    "sensor_type": "screen_sensor",
    "image_data": "...",
    "resolution": [1920, 1080]
}
```

**After:**
```python
{
    "timestamp": "2024-01-15T10:30:00",
    "sensor_type": "ui2html_screen_sensor",
    "ui_tree": {...},
    "html_content": "<div>...</div>",
    "element_count": 25,
    "snapshot_id": "snapshot_1234567890",
    "metadata": {...}
}
```

## Testing Migration

### Run Integration Tests

```bash
cd sensai_ui2html
python test_integration.py
```

### Run Demo

```bash
cd sensai_ui2html/examples
python demo.py
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install uiautomation chromadb openai
   ```

2. **Permission Issues (macOS)**
   - Grant accessibility permissions to Terminal/IDE
   - Install atomacos for better support: `pip install atomacos`

3. **ChromaDB Issues**
   - Ensure sufficient disk space
   - Check write permissions to `./chroma_db` directory

4. **No UI Detected**
   - Check if applications are accessible
   - Verify platform-specific dependencies

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

sensor = ScreenSensorReplacement()
# Detailed logs will be shown
```

## Performance Comparison

| Feature | Old Screen Sensor | UI2HTML Sensor |
|---------|------------------|----------------|
| Capture Speed | ~50-200ms | ~100-500ms |
| Memory Usage | ~1-10MB | ~1-5MB |
| Storage | Image files | Vector database |
| Query Capability | None | Semantic search |
| HTML Generation | None | Automatic |
| Memory Persistence | None | ChromaDB |

## Benefits of Migration

1. **Semantic Understanding**: UI elements are mapped to HTML for better LLM comprehension
2. **Memory Persistence**: Snapshots stored in vector database for historical analysis
3. **Natural Language Queries**: Find UI elements by description
4. **Better Integration**: HTML output works seamlessly with web-based systems
5. **Scalability**: Vector storage scales better than image files
6. **Searchability**: Find specific UI states across time

## Rollback Plan

If you need to rollback:

1. Keep the old sensor code as backup
2. Use feature flags to switch between systems
3. The new system is non-destructive to existing data

```python
# Feature flag example
USE_UI2HTML = True

if USE_UI2HTML:
    from sensai_ui2html.integration import ScreenSensorReplacement
    sensor = ScreenSensorReplacement()
else:
    from sensors.screen_sensor import ScreenSensor
    sensor = ScreenSensor()
```

## Support

For issues or questions:
1. Check the README.md for detailed documentation
2. Run the demo and integration tests
3. Review the troubleshooting section
4. Check ChromaDB and platform-specific documentation 