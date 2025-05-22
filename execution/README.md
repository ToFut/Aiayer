# SensAI Execution System

## 🚀 Enterprise-Grade Agent Execution Framework

The SensAI Execution System is a comprehensive, scalable, and professional agent execution framework inspired by Google Project Mariner and Claude Code. It provides intelligent automation, contextual awareness, and enterprise-grade reliability.

## 📁 Architecture Overview

```
execution/
├── core/                    # Core execution components
│   ├── agent_base.py       # Enterprise-grade base class for all agents
│   ├── execution_engine.py # Main execution coordination
│   └── task_orchestrator.py # Multi-agent task coordination
├── agents/                  # Specialized agent implementations
│   ├── suggestion_agent.py  # Integrates with backend SuggestionDetector
│   ├── automation_agent.py  # Enhanced mouse/keyboard control  
│   └── context_agent.py     # Context-aware analysis
├── memory/                  # Advanced memory management
│   ├── agent_memory.py      # Comprehensive task & context memory
│   └── task_tracker.py      # Task completion tracking
├── services/                # External service integrations
│   ├── workflow_integration.py # Legacy agent_workflow integration
│   └── llm_integration.py   # LLM service connections
├── interfaces/              # Communication protocols
├── config/                  # Configuration management
│   └── config_manager.py    # Enterprise-grade config system
├── utils/                   # Utility functions
├── tests/                   # Comprehensive test suite
└── logs/                    # Structured logging
```

## 🎯 Key Features

### ✅ Completed Components

#### 1. **Enterprise Agent Base** (`core/agent_base.py`)
- **State Management**: IDLE, RUNNING, PAUSED, ERROR, STOPPED
- **Task Execution**: Concurrent task processing with timeout/retry
- **Health Monitoring**: Automatic health checks and recovery
- **Metrics Collection**: Performance tracking and analytics
- **Event System**: Extensible event handlers
- **Safety Features**: Rate limiting, emergency stops

#### 2. **Enhanced SuggestionAgent** (`agents/suggestion_agent.py`)
- **Backend Integration**: Direct connection to existing `SuggestionDetector`
- **Chat Mode Support**: Agent/Ask/Suggest/General modes
- **WebSocket Communication**: Real-time backend coordination
- **Context Awareness**: Memory integration for learning
- **Proactive Suggestions**: Intelligent suggestion generation
- **User Feedback**: Learning from user interactions

#### 3. **Advanced AutomationAgent** (`agents/automation_agent.py`)
- **Enhanced InputController**: Improved mouse/keyboard control
- **Human-like Movements**: Natural interaction patterns
- **Safety Levels**: MAXIMUM, HIGH, MEDIUM, LOW safety modes
- **Action Sequences**: Complex multi-step automation
- **Emergency Stops**: Hardware-level Ctrl+1 shutdown
- **Performance Optimization**: Learning from user patterns
- **Screen Analysis**: Element detection and interaction

#### 4. **Task Orchestrator** (`core/task_orchestrator.py`)
- **Multi-Agent Coordination**: Intelligent agent routing
- **Dependency Management**: Complex task step dependencies
- **Priority Scheduling**: Critical/High/Normal/Low priorities
- **Parallel Execution**: Optimized concurrent processing
- **Retry Logic**: Intelligent failure recovery
- **Real-time Monitoring**: Complete task visibility

#### 5. **Agent Memory System** (`memory/agent_memory.py`)
- **Task Tracking**: Complete execution history
- **Context Snapshots**: Screen/system state capture
- **Pattern Recognition**: Learning from successful executions
- **Performance Analytics**: Success rates and optimization
- **SQLite Storage**: Persistent memory with caching
- **Smart Retrieval**: Context-aware memory search

#### 6. **Workflow Integration** (`services/workflow_integration.py`)
- **Legacy Compatibility**: Seamless existing `agent_workflow` integration
- **Message Bridging**: WebSocket message translation
- **Enhanced Capabilities**: Combining old and new systems
- **Backward Compatibility**: No breaking changes
- **Unified Task Coordination**: Single orchestration point

#### 7. **Configuration Management** (`config/config_manager.py`)
- **Multi-Format Support**: YAML, JSON, environment variables
- **Hot Reloading**: Dynamic configuration updates
- **Environment Overrides**: Development/Staging/Production
- **Validation**: Schema enforcement and error checking
- **Security**: Encrypted credential management
- **Thread Safety**: Concurrent access protection

## 🔧 Integration with Existing Systems

### Backend SuggestionDetector Integration
```python
# Existing backend component (llm_suggestion_detector.py)
suggestion_detector = SuggestionDetector(confidence_threshold=0.7)

# New SuggestionAgent integrates directly
suggestion_agent = SuggestionAgent(config, memory)
# Automatically connects to ws://localhost:8765
# Processes messages through existing detector
```

### Enhanced Mouse/Keyboard Control
```python
# Enhanced existing InputController
automation_agent = AutomationAgent(config, memory, SafetyLevel.HIGH)

# Supports all existing actions + new capabilities:
await automation_agent.execute_task({
    "action": "execute_sequence",
    "parameters": {
        "sequence": {
            "name": "Form Filling",
            "actions": [
                {"type": "click", "parameters": {"x": 100, "y": 200}},
                {"type": "type_text", "parameters": {"text": "Hello World"}},
                {"type": "key_press", "parameters": {"key": "enter"}}
            ]
        }
    }
})
```

### Legacy Workflow Integration
```python
# Seamless integration with existing agent_workflow
integrator = WorkflowIntegrator(orchestrator, memory)
await integrator.initialize_integration()

# Existing messages automatically routed to new system
# No changes required to existing code
```

## 🚀 Usage Examples

### 1. Initialize Execution System
```python
from execution import TaskOrchestrator, AgentMemory, ConfigManager
from execution.agents import SuggestionAgent, AutomationAgent
from execution.services import WorkflowIntegrator

# Initialize core components
config_manager = ConfigManager("config/execution_config.yaml")
memory = AgentMemory("logs/agent_memory.db")
orchestrator = TaskOrchestrator(max_concurrent_tasks=10)

# Create agents
suggestion_agent = SuggestionAgent(config_manager.get_suggestion_config(), memory)
automation_agent = AutomationAgent(config_manager.get_automation_config(), memory)

# Register with orchestrator
orchestrator.register_agent(suggestion_agent)
orchestrator.register_agent(automation_agent)

# Start system
await orchestrator.start()
```

### 2. Execute Complex Tasks
```python
# Create multi-step task
task_def = TaskDefinition(
    task_id="complex_automation",
    name="Website Form Automation", 
    description="Fill out contact form automatically",
    steps=[
        TaskStep(
            step_id="analyze_screen",
            agent_capability=AgentCapability.SCREEN_ANALYSIS,
            action="take_screenshot",
            parameters={}
        ),
        TaskStep(
            step_id="find_form",
            agent_capability=AgentCapability.SCREEN_ANALYSIS,
            action="find_element",
            parameters={"element": "contact_form", "method": "template"}
        ),
        TaskStep(
            step_id="fill_form",
            agent_capability=AgentCapability.TASK_AUTOMATION,
            action="execute_sequence",
            parameters={
                "sequence": {
                    "name": "Contact Form",
                    "actions": [
                        {"type": "click", "parameters": {"x": 300, "y": 400}},
                        {"type": "type_text", "parameters": {"text": "John Doe"}},
                        {"type": "key_press", "parameters": {"key": "tab"}},
                        {"type": "type_text", "parameters": {"text": "john@example.com"}}
                    ]
                }
            },
            dependencies=["analyze_screen", "find_form"]
        )
    ]
)

# Submit task
task_id = await orchestrator.submit_task(task_def)

# Monitor progress
status = orchestrator.get_task_status(task_id)
print(f"Task progress: {status['progress']}%")
```

### 3. Chat Mode Integration
```python
# Set chat mode for different behaviors
await suggestion_agent.execute_task({
    "action": "set_mode",
    "parameters": {"mode": "Agent"}  # Agent/Ask/Suggest/General
})

# Agent mode: Proactive task execution
# Ask mode: Contextual information
# Suggest mode: Maximum suggestion sensitivity  
# General mode: Minimal context, basic suggestions
```

## 📊 Monitoring and Analytics

### Agent Statistics
```python
# Get comprehensive statistics
agent_stats = suggestion_agent.get_suggestion_statistics()
automation_stats = automation_agent.get_automation_statistics()
orchestrator_stats = orchestrator.get_orchestrator_status()
memory_stats = memory.get_memory_statistics()

print(f"Suggestions accepted: {agent_stats['acceptance_rate']:.1%}")
print(f"Automation success: {automation_stats['success_rate']:.1%}")
print(f"Active tasks: {orchestrator_stats['active_tasks']}")
```

### Memory Analytics
```python
# Analyze task patterns
recent_tasks = memory.get_recent_tasks("form_automation", limit=10)
success_patterns = memory.success_patterns
optimization_hints = memory.get_optimization_suggestions("form_automation", context)
```

## 🔒 Security and Safety

### Safety Levels
- **MAXIMUM**: Requires confirmation for all actions
- **HIGH**: Confirms potentially destructive actions (default)
- **MEDIUM**: Minimal confirmations
- **LOW**: No confirmations (use with caution)

### Emergency Features
- **Hardware Emergency Stop**: Ctrl+1 immediately stops all automation
- **Rate Limiting**: Prevents too-rapid automation
- **Action Validation**: Checks for destructive operations
- **User Confirmation**: Interactive approval for sensitive actions

### Security Features
- **Encrypted Storage**: Secure credential management
- **Audit Logging**: Complete action tracking
- **Session Management**: Timeout and authentication
- **IP Restrictions**: Network access control

## 🎛️ Configuration

### Environment-Specific Settings
```yaml
# config/execution_config.yaml
environment: "production"  # development, staging, production
debug: false

agent:
  max_concurrent_tasks: 10
  task_timeout_seconds: 300
  log_level: "INFO"
  safety_level: "high"

suggestion:
  confidence_threshold: 0.7
  backend_ws_url: "ws://localhost:8765"
  enable_proactive_mode: true

automation:
  safety_level: "high"
  mouse_speed: "medium"
  confirmation_timeout: 30.0

memory:
  memory_path: "logs/agent_memory.db"
  cache_size: 1000
  enable_learning: true

security:
  enable_encryption: true
  enable_audit_logging: true
```

### Environment Variables
```bash
export EXECUTION_ENVIRONMENT=production
export EXECUTION_SAFETY_LEVEL=high
export SUGGESTION_CONFIDENCE_THRESHOLD=0.8
export MEMORY_CACHE_SIZE=2000
```

## 🧪 Testing

```bash
# Run comprehensive tests
python -m pytest execution/tests/ -v

# Test specific components
python -m pytest execution/tests/test_suggestion_agent.py
python -m pytest execution/tests/test_automation_agent.py
python -m pytest execution/tests/test_task_orchestrator.py
```

## 📈 Performance Optimization

### Memory Management
- **Intelligent Caching**: LRU cache for frequently accessed data
- **Automatic Cleanup**: Old entries pruned automatically
- **Context Compression**: Efficient context storage

### Execution Optimization
- **Parallel Processing**: Multiple tasks executed concurrently
- **Smart Routing**: Best agent selection for capabilities
- **Learning System**: Improves performance over time

### Resource Management
- **Connection Pooling**: Efficient WebSocket management
- **Thread Safety**: Concurrent access protection
- **Memory Limits**: Configurable resource constraints

## 🔄 Backward Compatibility

The execution system is designed for **100% backward compatibility** with existing `agent_workflow` components:

- ✅ Existing `ContextAwareAgent` continues to work
- ✅ Existing `InputController` enhanced, not replaced
- ✅ Existing WebSocket messages automatically routed
- ✅ No breaking changes to existing APIs
- ✅ Gradual migration path available

## 🎯 Next Steps

1. **Frontend Integration**: Connect with Tauri overlay chat modes
2. **LLAVA Integration**: Enhanced screen analysis capabilities  
3. **Advanced Learning**: ML-based optimization patterns
4. **Cloud Deployment**: Scalable cloud infrastructure
5. **Plugin System**: Extensible agent capabilities

## 📞 Support

For questions, issues, or contributions:
- 📧 Email: support@sensai-execution.com
- 📚 Documentation: [docs.sensai-execution.com](https://docs.sensai-execution.com)
- 🐛 Issues: [GitHub Issues](https://github.com/SensAI/execution/issues)

---

**Built with ❤️ by the SensAI Team**  
*Enterprise-grade AI automation for the modern world*