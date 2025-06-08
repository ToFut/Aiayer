# Proactive Suggestion System

This document explains the functionality of the newly implemented proactive suggestion system that monitors memory, identifies opportunities for automation, and pushes notifications to the NextGen overlay.

## Overview

The proactive suggestion system is designed to:

1. **Monitor conscious memory** for patterns and potential automation opportunities
2. **Identify actionable suggestions** based on user behavior and context
3. **Push notifications** to the NextGen overlay with sound alerts
4. **Transition between modes** (Suggest → Agent) when suggestions are accepted
5. **Execute automation plans** upon user approval

## Components

### 1. Memory-Aware Suggestion Monitor

The `memory_aware_suggestion_monitor.py` script continuously scans the conscious memory file for patterns that indicate potential automation opportunities. It then creates suggestion payloads and sends them to the overlay via WebSocket.

Key features:
- Analyzes memory data for suggestion patterns
- Extracts suggestions with confidence scores
- Sends properly formatted notifications to the overlay
- Handles mode transitions when suggestions are accepted
- Executes automation plans upon approval

### 2. Enhanced Conscious Memory Prompt

The system adds special prompting to the conscious memory system to explicitly identify suggestion opportunities:

```
When processing conscious memory, identify actionable suggestions based on:
1. User patterns and behaviors
2. Pending tasks or deadlines
3. Productivity opportunities
4. Workflow optimizations

For each potential suggestion:
- Assign a confidence score (0.0-1.0)
- Format as: "SUGGESTION: [title] | [message] | [confidence]"
- Include specific actions the system could perform
```

### 3. NextGen Overlay Integration

The system properly formats notifications to appear with sound alerts in the NextGen overlay:
- Uses the notification sound (`/sounds/notification.mp3`)
- Adds visual highlighting for suggestion messages
- Includes interactive buttons for user approval

### 4. Mode Transition Flow

When a suggestion is approved, the system:
1. Transitions from Suggest mode to Agent mode
2. Creates a structured automation plan
3. Displays the plan with execution options
4. Runs the plan upon confirmation
5. Provides real-time execution progress
6. Reports completion status

## How It Works

1. **Trigger Detection**:
   - Memory is continuously monitored for patterns like repeated tasks
   - The conscious memory system explicitly marks potential suggestions
   - Confidence scores determine which suggestions are pushed

2. **Notification Flow**:
   - Suggestions are formatted with proper notification flags
   - WebSocket sends them to the NextGen overlay
   - Sound alerts and visual highlighting draw user attention
   - Interactive buttons allow for easy acceptance or dismissal

3. **Mode Transition**:
   - When the user clicks "Yes, help me" on a suggestion
   - The system transitions to Agent mode
   - A structured plan is presented with execution options
   - The plan can be executed or canceled

4. **Execution Process**:
   - Upon final confirmation, the plan is executed step by step
   - Real-time progress is displayed in the overlay
   - Completion status is reported when finished

## Example Suggestions

The system can identify and suggest:
- Automation for repetitive manual tasks
- Optimizations for inefficient workflows
- Reminders for pending tasks
- Shortcuts for frequent operations
- Intelligent defaults based on patterns

## Integration with START_ENHANCED_SYSTEM.sh

The proactive suggestion system has been integrated into the main system startup script. When you run `START_ENHANCED_SYSTEM.sh`, it now:
- Starts the memory-aware suggestion monitor
- Updates the conscious memory prompt
- Enables proactive suggestion capabilities

## Testing the System

You can test the system by:
1. Adding test suggestions to conscious memory
2. Watching for notifications in the NextGen overlay
3. Accepting suggestions to see mode transitions
4. Confirming execution to observe automation plans

## Logs and Monitoring

Logs for the suggestion system are available at:
- `logs/memory/suggestion_monitor.log` - Main suggestion monitor logs
- `memory/suggestions/` - Stored suggestion data

## Status and Control

To check if the system is running:
```bash
ps aux | grep memory_aware_suggestion_monitor
```

To manually stop the system:
```bash
./stop_memory_suggestion_system.sh
```