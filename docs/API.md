# API Documentation

## Core Components

### TaskAgent

The main agent class that orchestrates all components.

```python
class TaskAgent:
    def __init__(self, sensors: Dict, llm: LocalLLM, memory: ConversationMemory, 
                 data_filter: DataFilter, context_analyzer: ContextAnalyzer)
```

#### Methods

- `async handle_query(query: str) -> str`
  - Process a user query with context awareness
  - Returns formatted response

- `async get_current_context() -> Optional[ContextInsight]`
  - Get the current context analysis
  - Returns ContextInsight object or None

- `async get_context_age() -> float`
  - Get age of current context in seconds
  - Returns float (infinity if no context)

### ContextAnalyzer

Analyzes system context using multiple sensors.

```python
class ContextAnalyzer:
    def __init__(self, models: Dict[str, Any], sensors: Dict, model_profiles: Optional[Dict] = None)
```

#### Methods

- `async analyze_context() -> ContextInsight`
  - Analyze current system context
  - Returns ContextInsight object

- `get_last_analysis() -> Optional[ContextInsight]`
  - Get most recent context analysis
  - Returns ContextInsight or None

- `get_analysis_age() -> Optional[float]`
  - Get age of last analysis in seconds
  - Returns float or None

### LocalLLM

Local language model interface.

```python
class LocalLLM:
    def __init__(self, model_name: str, host: str = "localhost", port: int = 11434)
```

#### Methods

- `async generate_response(messages: List[Dict[str, str]]) -> str`
  - Generate response from messages
  - Returns generated text

- `async stop() -> bool`
  - Stop the LLM
  - Returns success status

### ConversationMemory

Manages conversation history.

```python
class ConversationMemory:
    def __init__(self, max_length: int = 10)
```

#### Methods

- `add_message(message: Dict[str, str]) -> bool`
  - Add message to memory
  - Returns success status

- `get_recent() -> List[Dict[str, str]]`
  - Get recent messages
  - Returns list of messages

- `clear() -> None`
  - Clear all messages

## Data Structures

### ContextInsight

```python
@dataclass
class ContextInsight:
    current_activity: str
    context_summary: str
    potential_needs: List[str]
    attention_level: str
    confidence_score: float
    source_model: str
    timestamp: datetime = field(default_factory=datetime.now)
    raw_response: Dict = field(default_factory=dict)
    semantic_understanding: Dict = field(default_factory=dict)
```

## Sensor Interfaces

### ScreenSensor

```python
class ScreenSensor:
    def get_data() -> Dict[str, Any]
    def has_updates() -> bool
```

### FileSensor

```python
class FileSensor:
    def get_data() -> Dict[str, Any]
    def has_updates() -> bool
```

### ProcessSensor

```python
class ProcessSensor:
    def get_data() -> Dict[str, Any]
    def has_updates() -> bool
```

### BrowserSensor

```python
class BrowserSensor:
    def get_data() -> Dict[str, Any]
    def has_updates() -> bool
```

## Error Handling

All components raise appropriate exceptions:

- `ValueError`: Invalid input parameters
- `RuntimeError`: Component initialization/operation errors
- `ConnectionError`: Network/connection issues
- `TimeoutError`: Operation timeout

## Configuration

Components are configured through `config/config.yaml`:

```yaml
sensors:
  screen:
    interval_sec: 5
  file:
    paths: ["~/Documents", "~/Desktop"]
  process:
    interval_sec: 2
  browser:
    enabled: true
    polling_interval_sec: 1

llm:
  model_name: "mistral"
  host: "localhost"
  port: 11434

memory:
  max_conversation_length: 10
``` 