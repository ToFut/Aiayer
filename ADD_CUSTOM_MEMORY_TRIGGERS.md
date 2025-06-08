# Adding Custom Memory Triggers

This guide explains how to add custom trigger rules to the Memory Trigger System to detect specific patterns in memory and generate tailored suggestions.

## Understanding Trigger Rules

Trigger rules define when and how the Memory Trigger Service should generate suggestions. Each rule consists of:

1. **Rule ID**: Unique identifier for the rule
2. **Name**: Human-readable name
3. **Description**: Purpose of the rule
4. **Trigger Type**: What kind of pattern to detect (see below)
5. **Priority**: Importance of the rule (HIGH, MEDIUM, LOW)
6. **Pattern**: Definition of what to look for in memory
7. **Confidence Threshold**: Minimum confidence level to trigger (0.0-1.0)
8. **Action Template**: Defines what to suggest when triggered

## Trigger Types

The system supports several trigger types:

- `APPLICATION_PATTERN`: Detects patterns in application usage
- `ACTIVITY_SEQUENCE`: Detects sequences of user activities
- `TIME_BASED`: Triggers based on time (time of day, duration)
- `SEMANTIC_PATTERN`: Uses semantic search to find patterns in memory
- `TASK_COMPLETION`: Detects when tasks are completed
- `CONTENT_BASED`: Finds patterns in content (text, keywords)
- `USER_BEHAVIOR`: Detects patterns in user behavior (repetition, context switching)

## Pattern Formats

Patterns can be defined in different ways depending on the trigger type:

### Simple Regex Pattern

```python
pattern = "keyword1|keyword2|keyword3"  # Regular expression
```

### Keyword List Pattern

```python
pattern = {
    "keywords": ["word1", "word2", "word3"],
    "min_matches": 2  # Minimum keywords to match
}
```

### Application List Pattern

```python
pattern = {
    "applications": ["Chrome", "Safari", "Firefox"]
}
```

### Time-Based Pattern

```python
pattern = {
    "time_of_day": [9, 12, 17],  # Hours of day to trigger
    "duration": 60  # Duration in minutes
}
```

### Sequence Pattern

```python
pattern = {
    "sequence": ["step1", "step2", "step3"],
    "min_length": 2  # Minimum steps to match
}
```

## Adding a Custom Rule

### Method 1: Using the API

You can add rules programmatically:

```python
from memory.memory_trigger_service import TriggerRule, TriggerType, TriggerPriority

# Create custom rule
custom_rule = TriggerRule(
    id="my_custom_rule",
    name="My Custom Rule",
    description="Detects a custom pattern in memory",
    trigger_type=TriggerType.CONTENT_BASED,
    priority=TriggerPriority.MEDIUM,
    pattern={
        "keywords": ["custom", "pattern", "keywords"],
        "min_matches": 2
    },
    action_template={
        "type": "custom_action",
        "description": "Custom action for this pattern"
    }
)

# Add to running service
from memory.memory_trigger_service import memory_trigger_service
memory_trigger_service.rule_manager.add_rule(custom_rule)
```

### Method 2: Using the Configuration File

You can add rules to the configuration file:

1. Create a JSON file at `config/trigger_rules.json`:

```json
{
  "version": "1.0",
  "last_updated": 1625097600,
  "rules": [
    {
      "id": "custom_rule_1",
      "name": "Custom Rule 1",
      "description": "Detects pattern in memory",
      "trigger_type": "content_based",
      "priority": "medium",
      "pattern": {
        "keywords": ["custom", "pattern", "keywords"],
        "min_matches": 2
      },
      "confidence_threshold": 0.7,
      "cooldown_seconds": 3600,
      "enabled": true,
      "action_template": {
        "type": "custom_action",
        "description": "Custom action"
      }
    }
  ]
}
```

2. Restart the Memory Trigger Service

## Example Custom Rules

### E-commerce Shopping Detection

```python
shopping_rule = TriggerRule(
    id="ecommerce_detection",
    name="E-commerce Shopping Detection",
    description="Detects when user is shopping on e-commerce sites",
    trigger_type=TriggerType.CONTENT_BASED,
    priority=TriggerPriority.HIGH,
    pattern={
        "keywords": [
            "add to cart", "checkout", "buy now", "price", "product", 
            "shipping", "payment", "order", "discount"
        ],
        "min_matches": 3
    },
    action_template={
        "type": "shopping_assistance",
        "description": "Help with e-commerce shopping"
    }
)
```

### Long Work Session Detection

```python
work_session_rule = TriggerRule(
    id="long_work_session",
    name="Long Work Session Detection",
    description="Detects when user has been working for a long time",
    trigger_type=TriggerType.TIME_BASED,
    priority=TriggerPriority.MEDIUM,
    pattern={
        "duration": 90  # 90 minutes
    },
    action_template={
        "type": "wellness_suggestion",
        "description": "Suggest taking a break"
    }
)
```

### Repetitive Task Detection

```python
repetitive_task_rule = TriggerRule(
    id="repetitive_task",
    name="Repetitive Task Detection",
    description="Detects when user is performing repetitive tasks",
    trigger_type=TriggerType.USER_BEHAVIOR,
    priority=TriggerPriority.HIGH,
    pattern={
        "repetitive_action": True,
        "min_repetitions": 3
    },
    action_template={
        "type": "automation_suggestion",
        "description": "Suggest task automation"
    }
)
```

## Testing Custom Rules

After adding a custom rule, you can test it by:

1. Adding memory items that should trigger the rule
2. Monitoring the logs for pattern detection
3. Checking if the chat overlay displays the expected suggestion

Example for adding test memory:

```python
# Add test memory that should trigger the rule
memory_item = {
    "type": "web_content",
    "url": "https://example.com/products/test",
    "title": "Test Product Page",
    "searchable_text": "Add to Cart Buy Now Price: $59.99 Shipping: Free",
    "timestamp": time.time(),
    "source": "test"
}

# Add to memory system
memory_system.short_term_memory.append(memory_item)
```

## Advanced Configuration

You can configure advanced aspects of trigger rules:

- **cooldown_seconds**: Time before the rule can trigger again (default: 3600s)
- **max_triggers_per_day**: Maximum times a rule can trigger per day (default: 5)
- **contexts**: List of contexts where this rule applies (default: all contexts)

Example with advanced configuration:

```python
advanced_rule = TriggerRule(
    id="advanced_rule",
    name="Advanced Rule Configuration",
    description="Advanced rule with custom configuration",
    trigger_type=TriggerType.CONTENT_BASED,
    priority=TriggerPriority.MEDIUM,
    pattern={"keywords": ["advanced", "config"], "min_matches": 1},
    confidence_threshold=0.8,
    cooldown_seconds=1800,  # 30 minutes cooldown
    max_triggers_per_day=3,
    contexts=["browser", "productivity"],  # Only apply in these contexts
    action_template={"type": "advanced_action"}
)
```

## Best Practices

1. **Unique Rule IDs**: Ensure each rule has a unique ID
2. **Descriptive Names**: Use clear names that explain what the rule does
3. **Appropriate Confidence**: Set confidence thresholds based on pattern specificity
4. **Reasonable Cooldowns**: Avoid overwhelming users with too many suggestions
5. **Test Thoroughly**: Verify rules with different memory patterns
6. **Contextual Actions**: Make action templates specific to the detected pattern
7. **Start Simple**: Begin with simple patterns and gradually add complexity