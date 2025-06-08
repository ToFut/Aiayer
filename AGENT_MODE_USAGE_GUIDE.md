# Agent Mode Usage Guide

This guide explains how to use the newly fixed Agent mode automation capabilities.

## Overview
The Agent mode allows the system to perform real automation tasks on your behalf. With the recent fixes, it can now properly handle web searches, clicking on elements, and executing multi-step tasks.

## When to Use Agent Mode
Use Agent mode when you want the system to:
- Search the web for information
- Navigate to websites
- Interact with UI elements
- Perform a sequence of actions

## Example Queries
Try these example queries to test the Agent mode:

### Web Search
```
search for python programming tutorials on google
```

### Finding Information
```
find the latest news about artificial intelligence
```

### Navigation
```
go to github.com and search for tensorflow
```

### UI Interaction
```
open safari and search for nearby restaurants
```

## Advanced Usage
The Agent mode supports complex multi-step tasks. For example:
```
search for a chocolate chip cookie recipe, find one with good ratings, and save the ingredients list
```

## Interactive Controls
When using Agent mode, you'll see interactive buttons:
- **EXECUTE**: Run the automation plan
- **CANCEL**: Cancel the automation
- **MODIFY**: Adjust the plan before execution
- **SIMULATE**: Show what would happen without performing actions

## Troubleshooting
If you encounter issues:

1. **No automation plan appears**:
   - Check if the system is still processing (it may take 5-15 seconds)
   - Try a simpler query, focusing on web search

2. **Plan appears but execution fails**:
   - Make sure the target application is open
   - Check if the coordinates need adjustment
   - Try a search query with "google" explicitly mentioned

3. **System shows "falling back to normal response"**:
   - Restart the system with `./RESTART_FIXED_SYSTEM.sh`
   - Check logs with `tail -f logs/brain/brain_router.log`

## Best Practices
1. Be specific about what you want the system to do
2. Mention the target application explicitly (e.g., "in Safari" or "using Google")
3. Break complex tasks into simpler steps
4. Start with search queries to test functionality

## Logging and Debugging
To monitor the Agent mode:
```bash
# Watch the brain router log
tail -f logs/brain/brain_router.log

# Watch the universal automation handler
tail -f logs/automation/universal_handler.log

# Watch the backend server
tail -f logs/backend/real_llm_8767.log
```

## How It Works
1. The Agent mode receives your request
2. It uses an LLM to create a detailed automation plan
3. The plan is presented for your approval
4. When approved, the system executes the steps
5. The system provides feedback on completion

## Advanced Configuration
Power users can modify the automation behavior by editing:
- `fixed_universal_automation_handler.py` - For automation planning
- `adaptive_retry_automation_handler.py` - For execution retry logic
- `brain/core/brain_router.py` - For agent mode routing logic