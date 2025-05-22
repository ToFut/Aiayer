# Enhanced Context Memory System

This implementation significantly enhances the Context Memory system by integrating LLaVA visual analysis with process classification to provide meaningful contextual awareness of user activities.

## Features

1. **Rich Visual Understanding with LLaVA**
   - Analyzes screen content using LLaVA multimodal models
   - Identifies applications, UI elements, and specific views/modes
   - Detects user workflow stage and tasks being performed
   - Extracts text content and interactive elements

2. **Foreground/Background Process Classification**
   - Distinguishes between foreground applications the user is interacting with
   - Identifies supporting processes related to the current application
   - Separates background system processes from user-facing applications
   - Tracks active window and application focus

3. **Meaningful Contextual Relationships**
   - Creates connections between screen content and running processes
   - Builds activity timeline with importance scores
   - Tracks application context across sessions
   - Organizes memory by timestamp for temporal understanding

4. **User Activity Inference**
   - Automatically determines what the user is doing
   - Identifies specific workflows like "composing email", "code editing", etc.
   - Rates importance of different activities for better memory prioritization
   - Creates comprehensive activity summaries

## Components

1. **LLaVAVisualProcessor**
   - Processes screen captures for detailed visual understanding
   - Connects to Ollama API to use LLaVA models
   - Handles retries, fallbacks, and error recovery
   - Implements caching to improve performance

2. **EnhancedContextMemory**
   - Manages relationships between memory items
   - Maintains application context history
   - Infers user activities from sensor data
   - Calculates importance scores for memory prioritization

3. **MemoryContextIntegration**
   - Integrates enhanced context with existing memory system
   - Processes sensor data in parallel queues
   - Provides clean API for memory system interaction
   - Handles startup/shutdown and error recovery

## Usage

### Starting the System

```bash
./start_enhanced_context_memory.sh
```

This starts the enhanced context memory system, which will:
- Initialize LLaVA analysis via Ollama
- Connect to screen and process sensors
- Begin monitoring and analyzing user activity
- Store context snapshots periodically in the results directory

### Stopping the System

```bash
./stop_enhanced_context_memory.sh
```

This gracefully shuts down the enhanced context memory system.

## System Requirements

- Python 3.8+
- Ollama with LLaVA model installed (http://localhost:11434)
- PIL, aiohttp, and other dependencies listed in requirements.txt

## Implementation Details

### LLaVA Configuration

The system is configured to use the LLaVA model through Ollama. It will fall back to other available models if LLaVA is not available.

### Process Classification

Process classification uses a combination of techniques:
1. Window title and focus state detection
2. Pattern matching for known system processes
3. Relationship analysis between processes

### Context Memory Structure

The context memory maintains:
- Recent screen and process data
- Timeline of user activities
- Application-specific context
- Relationship mappings between memory items

### Performance Considerations

- Image data is not stored in memory after analysis
- Caching is used to avoid redundant LLaVA calls
- Rate limiting prevents excessive API usage
- Background processing queues ensure responsiveness