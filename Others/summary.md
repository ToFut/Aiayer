# Sensor Data Processing and Memory System

## Sensor Data Flow

1. **Data Collection**: Three main sensors collect data:
   - `ScreenSensor`: Captures screenshots and window information
   - `ProcessSensor`: Monitors active processes/applications
   - `FileSensor`: Tracks file system changes

2. **Initial Processing**:
   - Sensors apply basic filtering (removing duplicates, standardizing formats)
   - `DataFilter` class removes sensitive content and normalizes data

3. **Data Buffering**:
   - `ConsciousMemory` maintains buffers for each sensor type (screen, process, file)
   - Buffer size limited to 10 entries per sensor type (see `max_buffer_size` variable)
   - Data marked with timestamps for tracking

4. **Processing Pipeline**:
   - Raw sensor data → `ConsciousMemory.add_sensor_data()` → Processing → Memory System
   - Processing includes normalization, significance detection, and enrichment
   - `ConsciousMemory._process_sensor_data()` transforms raw data into structured format

5. **Memory Storage**:
   - Processed data is sent to multiple memory stores:
     - Short-term memory (recent data, limited to ~100 entries)
     - Context memory (current environment state)
     - Long-term memory (only for "significant" data)

## Data Retention Policies

1. **Buffer Management**:
   - `ConsciousMemory` buffers limited to 10 entries per sensor type
   - Buffers cleared after periodic processing (~30 second interval)

2. **Memory Limits**:
   - Short-term memory: Limited to ~100 entries
   - Context memory: Limited to 50 entries 
   - Long-term memory: Limited to 1000 entries but more selective

3. **Cleanup Processes**:
   - Automatic cleanup triggered by:
     - Time-based: Every hour (`cleanup_interval = 3600`)
     - Memory usage: When approaching `MAX_MEMORY_SIZE_MB` (100MB)
   - Old data (>24 hours) automatically pruned

4. **Data Compression**:
   - Memory is compressed when total usage exceeds `COMPRESSION_THRESHOLD_MB` (50MB)
   - Uses zlib compression for efficient storage

## LLM Integration

1. **Periodic Analysis**:
   - Every 30 seconds, buffered data is analyzed by LLM
   - Analysis generates insights about current user activity
   - Insights stored in both long-term and context memory

2. **Context Management**:
   - Current context maintained for relevance detection
   - `_prepare_context()` combines recent sensor data for LLM prompt generation
   - Context used to determine significance of new sensor data

## Search and Retrieval

1. **Text-based Search**:
   - Memory system uses text matching for search (not vector embeddings)
   - Simple relevance scoring based on term frequency
   - Results deduplicated to provide diverse results

2. **Smart Batching**:
   - `_should_process_sensor_data()` uses adaptive batching based on:
     - System load (reduces frequency when CPU usage is high)
     - Data significance (processes important changes sooner)
     - Sensor type (different processing intervals for each sensor)