# Plan Persistence System

This document explains the implementation of the Plan Persistence system, which solves the issue of automation plans being lost on service restarts and enhances the user experience with intelligent next step suggestions.

## Problem Addressed

Before this implementation, all automation plans were stored only in memory:

```python
self.active_plans: Dict[str, AutomationPlan] = {}
```

This meant that when services restarted, all active plans were lost, leading to:
- Lost state for pending plans
- Inability to recover from service interruptions
- Poor user experience when plans disappear
- No context for follow-up actions after plan completion

## Solution

The Plan Persistence system implements a disk-based persistence layer that:

1. Saves plans to disk when created
2. Allows retrieval of plans from disk when needed
3. Provides cleanup of completed/cancelled plans
4. Maintains metadata for searching and listing plans
5. Generates intelligent next step suggestions after plan completion

## Components

### 1. `plan_persistence.py`

Core persistence module with these key features:
- JSON-based storage of plans with metadata
- Async API for save/load/delete operations
- Auto-save background task
- Automatic ID generation
- Plan cleanup functionality
- Error handling and recovery
- Intelligent next step suggestions generation

### 2. Integration in Automation Handlers

The plan persistence system has been integrated into:
- `real_agent_automation_handler.py`
- `universal_intelligent_automation_handler.py`

Key integration points:
- Plan creation uses persistent IDs
- Plan storage to disk upon creation
- Checks for plans on disk when not found in memory
- Plan cleanup after execution/cancellation
- Generation of contextual next step suggestions

### 3. Brain Router Integration

New 'PLANS' mode in the brain router allows:
- Listing all stored plans
- Deleting specific plans
- Cleaning up old plans

## Enhanced Next Step Suggestions

The system now provides intelligent next step suggestions after plan completion:

### Features

1. **Context-Aware**: Suggestions are based on the plan's context, content, and type
2. **Personalized**: Extracts key terms from the plan to create tailored suggestions
3. **Categorized**: Different suggestion types based on the plan category (web search, shopping, travel, etc.)
4. **Action-Oriented**: Each suggestion includes an actionable command template
5. **Prioritized**: Suggestions are ranked by relevance and importance
6. **Visually Enhanced**: Presented with clear formatting and helpful emojis

### Implementation

The suggestion system:
1. Analyzes completed plans to determine their type and extract key terms
2. Generates 3 contextually relevant next step suggestions
3. Provides actionable command templates for each suggestion
4. Presents them in a non-intrusive, visually organized format
5. Preserves plan context to enable these suggestions

Example suggestion types:
- For web searches: Save results, refine search, explore related topics
- For shopping: Compare prices, read reviews, find alternatives
- For travel: Compare prices, check accommodations, explore activities
- For entertainment: Find similar content, save to playlist, share content
- For productivity: Share document, create backup, set reminder

## Usage Examples

### Accessing Plans

```
# List all stored plans
plans list

# Delete a specific plan
plans delete plan_1718395938_1234

# Clean up old plans
plans clean 7 days
```

### Command Line Utility

The `list_stored_plans.py` script provides a CLI for plan management:
```
python list_stored_plans.py
```

## Implementation Details

### Storage Format

Plans are stored as JSON files in the `cache/plans/` directory:
- Each plan has a separate JSON file named by its ID
- A central `plan_metadata.json` file maintains metadata for all plans
- Each plan's metadata includes creation time, status, and other key info

### Recovery Process

When a plan is requested but not found in memory:
1. The system checks for the plan in the persistent storage
2. If found, the plan is loaded into memory
3. The plan can then be executed or managed as usual

### Next Step Suggestion Process

1. When a plan completes execution, the system:
   - Extracts key terms from the plan content
   - Determines the plan type (web search, shopping, travel, etc.)
   - Generates context-aware next step suggestions
   - Presents these suggestions to the user
   - Stores the suggestions with the plan metadata

2. Suggestions are prioritized based on:
   - Relevance to the plan type
   - Success rate of the executed plan
   - Extracted key terms
   - Common follow-up actions for the plan type

## Best Practices

1. Always use the `await save_plan()` method after creating or modifying plans
2. Use `await delete_plan()` after plan execution/cancellation
3. Periodically clean up old plans to prevent storage bloat
4. Use the `generate_plan_id()` function to create robust plan IDs
5. Pass context to `generate_next_steps()` for better suggestion quality

## Limitations

1. Complex object serialization relies on custom JSON encoding
2. No database-level transactions (file system based)
3. No distributed storage support (local file system only)
4. Basic term extraction without full NLP capabilities

## Future Improvements

1. Add database support for more robust storage
2. Implement plan versioning and history
3. Add plan templates for common automation tasks
4. Support plan recovery with partial execution history
5. Enhance term extraction with more advanced NLP techniques
6. Add machine learning to improve suggestion relevance
7. Implement user feedback loop for suggestion quality