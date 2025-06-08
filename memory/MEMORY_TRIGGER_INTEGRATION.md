# Memory Trigger Service Integration Guide

This document provides comprehensive guidance on integrating and using the Memory Trigger Service to enhance your AI system with proactive suggestions and automated actions.

## Overview

The Memory Trigger Service is a system that:

1. Monitors memory for patterns and opportunities
2. Generates context-aware suggestions
3. Pushes notifications to the chat interface
4. Executes actions in agent mode upon user approval

This creates a proactive AI assistant that can identify when to offer help and execute tasks based on detected patterns in user behavior and memory content.

## Integration Architecture

The Memory Trigger Service integrates with the following components:

- **Memory System**: For monitoring memory content and patterns
- **Semantic Search**: For retrieving relevant context
- **Brain Router**: For delivering suggestions and executing actions
- **Suggest Mode Handler**: For generating quality suggestions
- **Agent Mode Handler**: For executing approved actions

![Architecture Diagram](docs/architecture/memory_trigger_architecture.png)

## Setup and Installation

### Prerequisites

- Python 3.9+
- Running memory system
- Brain router with suggest and agent modes
- Properly configured semantic search

### Installation Steps

1. Install the Memory Trigger Service:

```bash
# Ensure required directories exist
mkdir -p logs/memory
mkdir -p config

# Copy the implementation files
cp memory_trigger_service.py memory/
cp integrate_memory_trigger.py memory/
```

2. Configure the service:

```bash
# Create default configuration
python -m memory.integrate_memory_trigger --start
```

3. Verify installation:

```bash
# Check status
python -m memory.integrate_memory_trigger --status
```

## Configuration Options

The Memory Trigger Service can be configured via a JSON file at `config/memory_trigger_config.json`:

```json
{
  "check_interval": 60,          // How often to check memory (seconds)
  "max_notifications_per_hour": 5, // Limit notifications to prevent overload
  "enabled": true,               // Master switch to enable/disable
  "min_confidence_threshold": 0.6 // Global minimum confidence for all rules
}
```

## Creating Trigger Rules

Trigger rules define patterns to watch for and actions to suggest. They can be created programmatically or via the integration tool.

### Rule Types

- **Application Pattern**: Triggers based on application usage
- **Content Based**: Triggers based on content keywords
- **Activity Sequence**: Triggers based on sequences of activities
- **Time Based**: Triggers based on time of day or duration
- **Semantic Pattern**: Triggers based on semantic similarity
- **Task Completion**: Triggers when tasks complete
- **User Behavior**: Triggers based on behavior patterns

### Example Rules

Here are some example rules you can implement:

#### Browser Search Detection

```python
rule = {
    "id": "browser_search_detection",
    "name": "Browser Search Detection",
    "description": "Detects when user is searching in a browser",
    "trigger_type": "application_pattern",
    "priority": "medium",
    "pattern": {"applications": ["Chrome", "Safari", "Firefox", "Edge"]},
    "confidence_threshold": 0.7,
    "action_template": {
        "type": "search_assistance",
        "description": "Help with search optimization"
    }
}
```

#### Repetitive Task Detection

```python
rule = {
    "id": "repetitive_task_detection",
    "name": "Repetitive Task Detection",
    "description": "Detects when user is performing repetitive actions",
    "trigger_type": "user_behavior",
    "priority": "high",
    "pattern": {
        "repetitive_action": True,
        "min_repetitions": 3
    },
    "confidence_threshold": 0.8,
    "action_template": {
        "type": "automation_suggestion",
        "description": "Suggest automation for repetitive task"
    }
}
```

#### Long Work Session

```python
rule = {
    "id": "long_work_session",
    "name": "Long Work Session Detection",
    "description": "Suggests a break after working for a long time",
    "trigger_type": "time_based",
    "priority": "medium",
    "pattern": {
        "duration": 60  # 60 minutes
    },
    "confidence_threshold": 0.7,
    "action_template": {
        "type": "wellness_suggestion",
        "description": "Suggest taking a break"
    }
}
```

## Integration with Frontend

The Memory Trigger Service delivers notifications through the brain router to the frontend chat interface. Notifications include action buttons for user interaction.

### Notification Format

```json
{
  "notification_id": "notif_12345",
  "notification_type": "trigger",
  "action_buttons": [
    {
      "id": "do",
      "text": "Do It",
      "action": "execute",
      "style": "primary"
    },
    {
      "id": "dismiss",
      "text": "Dismiss",
      "action": "dismiss",
      "style": "secondary"
    }
  ],
  "rule_id": "browser_search_detection",
  "trigger_context": {
    "application": "Chrome"
  }
}
```

### Frontend Requirements

The frontend must:

1. Display the suggestion text
2. Show action buttons for each notification
3. Send user actions back to the backend
4. Handle different notification priorities appropriately

## User Experience Guidelines

For the best user experience with triggered suggestions:

1. **Relevance**: Ensure suggestions are contextually relevant
2. **Timing**: Avoid interrupting the user's flow
3. **Control**: Always give users the option to dismiss
4. **Value**: Make sure executed actions provide genuine value
5. **Learning**: Track user responses to improve future suggestions

## Monitoring and Maintenance

### Service Status

Check service status with:

```bash
python -m memory.integrate_memory_trigger --status
```

This returns metrics like:

- Running state
- Trigger count
- Active notifications
- Active rules
- Last check time

### Log Monitoring

Logs are stored in `logs/memory/memory_trigger.log` and include:

- Pattern detection events
- Notification creation and delivery
- Action execution
- Error conditions

## Troubleshooting

Common issues and solutions:

### No Notifications Being Generated

- Check service status is running
- Verify memory system is properly connected
- Ensure at least one rule is active
- Check log file for errors in pattern detection

### Actions Not Executing

- Verify brain router is available
- Check agent mode handler is working
- Look for errors in execution logs
- Ensure correct permissions are set

### Performance Issues

- Increase check interval to reduce load
- Limit the number of active rules
- Optimize pattern detection with more specific rules
- Consider implementing rule cooldowns

## Advanced Usage

### Custom Pattern Detectors

You can extend the system with custom pattern detectors by:

1. Subclassing the `MemoryPatternDetector` class
2. Implementing custom detection methods
3. Registering your detector with the service

### Integration with Custom Memory Systems

To integrate with a custom memory system:

1. Implement the memory interface methods:
   - `get_short_term_memory()`
   - `get_memories_by_type()`
2. Provide your system to the service on initialization

### Rule Cooldowns and Scheduling

Control notification frequency with:

- Rule cooldowns (minimum time between triggers)
- Time-of-day scheduling (only trigger during certain hours)
- Maximum triggers per day

## Best Practices

1. **Start Simple**: Begin with a few high-value trigger rules
2. **Test Thoroughly**: Verify triggers and actions before deploying
3. **Monitor User Feedback**: Track acceptance and dismissal rates
4. **Iterate Rules**: Refine patterns based on performance data
5. **Respect Privacy**: Only trigger on appropriate memory contents
6. **Minimize Interruptions**: Balance proactivity with focus

## Version History

- **v1.0.0**: Initial implementation of Memory Trigger Service
- **v1.1.0**: Added advanced pattern detection capabilities
- **v1.2.0**: Improved notification management and action execution

## Support and Resources

For questions or issues:
- Check the logs at `logs/memory/memory_trigger.log`
- Use the interactive mode for testing: `python -m memory.integrate_memory_trigger --interactive`
- Refer to the API documentation in code comments