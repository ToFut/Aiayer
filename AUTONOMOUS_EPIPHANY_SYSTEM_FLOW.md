# Autonomous Epiphany System Flow

This document outlines the enhanced autonomous epiphany system flow, designed to provide proactive, contextually-aware suggestions based on screen analysis and user activity patterns.

## System Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Screen Sensor  │──────│ Contextual      │──────│  LLM-based      │──────│  Suggestion     │
│  Analysis       │      │ Memory System   │      │  Analysis       │      │  Generator      │
└─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘
                                                                                   │
                                                                                   ▼
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Action         │◀─────│  User           │◀─────│  Notification   │◀─────│  SUGGESTION     │
│  Executor       │      │  Confirmation   │      │  System         │      │  MEMORY         │
└─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────────┘
         │                                                                        ▲
         └──────────────────────────────────────────────────────────────────────┐│
                                                                                 ││
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌────┘└────────┐
│  Execution      │──────│  User Feedback  │──────│  Feedback       │──────│  Learning    │
│  Results        │      │  Processing     │      │  Analysis       │      │  System      │
└─────────────────┘      └─────────────────┘      └─────────────────┘      └─────────────┘
```

## Core Components

### 1. Enhanced Screen Analysis
- Real-time screen content analysis
- UI element detection with neural model
- Application context extraction
- Active window and content analysis

### 2. Contextual Memory System
- Short-term and long-term memory integration
- User activity pattern recognition
- Application usage history
- Recent interaction tracking

### 3. LLM-based Analysis 
- Process screen content with context-aware LLM
- Extract potential automation opportunities
- Generate actionable suggestions
- Assign confidence scores to suggestions

### 4. SUGGESTION_MEMORY
- Global parameter storing actionable items
- Structured format for suggestions:
  ```json
  {
    "id": "sugg_12345",
    "title": "Create calendar event",
    "description": "I noticed you're reading an email about a meeting on Thursday",
    "confidence": 0.85,
    "action_items": [
      {"type": "open_app", "target": "Calendar"},
      {"type": "input_text", "target": "event_title", "value": "Team Meeting"},
      {"type": "input_text", "target": "date", "value": "Thursday 3pm"}
    ],
    "context": {
      "source": "email",
      "app": "Mail",
      "timestamp": "2025-06-06T15:30:00Z"
    }
  }
  ```

### 5. Notification System
- Timely, non-intrusive UI notifications
- Clear presentation of suggested actions
- User confirmation options
- Adaptive timing based on user focus

### 6. User Confirmation Flow
- Two-stage confirmation process:
  1. Initial suggestion approval ("Yes, help me" / "No thanks")
  2. Detailed action plan confirmation
- Option to modify suggested actions
- Remember user preferences

### 7. Action Execution
- Universal intelligent automation
- Neural UI detection for robust element targeting
- Adaptive retry with error handling
- Visual verification of execution success

### 8. Feedback Learning System
- Records user responses to suggestions
- Analyzes patterns in acceptance/rejection
- Enhances suggestion quality over time
- Adapts to user preferences
- Provides system insights and improvement recommendations

## Workflow Process

1. **Continuous Monitoring**
   - Screen sensor captures content and UI state
   - Process sensor tracks active applications
   - Memory system maintains contextual awareness

2. **Contextual Analysis**
   - LLM processes screen content with memory context
   - Prompt specifically asks for potential automation opportunities
   - System extracts actionable items and confidence scores

3. **Suggestion Generation**
   - High-confidence suggestions are stored in SUGGESTION_MEMORY
   - Suggestions include specific action items for execution
   - Metadata includes context source and confidence level
   - Feedback learning enhances suggestion quality

4. **Notification Delivery**
   - System selects optimal timing for notification
   - Non-intrusive UI presents suggestion with clear intent
   - User is prompted for initial confirmation

5. **Confirmation Process**
   - If approved, detailed action plan is presented
   - User can review and modify specific steps
   - Final confirmation triggers execution

6. **Execution & Feedback**
   - System executes action plan with real-time feedback
   - Visual verification confirms successful completion
   - User reaction is recorded to improve future suggestions

7. **Feedback Learning Loop**
   - User feedback (acceptance/rejection) is analyzed
   - System learns from execution successes and failures
   - Future suggestions are adjusted based on learned patterns
   - Time and context patterns are identified and leveraged

## LLM Prompt Template

```
You are an automation assistant analyzing screen content.

CURRENT SCREEN CONTENT:
{screen_content}

ACTIVE APPLICATION:
{active_app}

RECENT USER ACTIVITY:
{recent_activity}

Based on this information, identify if there's a valuable automation opportunity. 
If yes, provide:
1. A brief title for the suggestion
2. A clear description of what can be automated
3. A confidence score (0.0-1.0)
4. Specific action items required to complete this automation
5. Any contextual information to remember

Format your response as follows if you find an opportunity:
SUGGESTION: [title] | [description] | [confidence]
ACTION_ITEMS:
- [action_type]: [details]
- [action_type]: [details]
...

If no clear automation opportunity exists, respond with "NO_SUGGESTION".
```

## Feedback Learning Components

### 1. Suggestion Feedback Learner
- Extracts features from suggestions (app, action type, time, etc.)
- Tracks success/failure patterns for different features
- Calculates quality scores for new suggestions
- Provides improvement recommendations

### 2. Feature Analysis
- Identifies high-performing suggestion features
- Tracks time-of-day and day-of-week patterns
- Analyzes app-specific preferences
- Categorizes suggestions by type and complexity

### 3. Quality Scoring System
- Enhances confidence scores with learned patterns
- Adjusts thresholds based on user acceptance rates
- Prioritizes suggestions with high success likelihood
- Demotes suggestion types with low acceptance

### 4. Feedback Integration
- Connects user feedback with suggestion memory
- Updates feature success rates in real-time
- Applies learned patterns to enhance new suggestions
- Provides system-wide insights and metrics

## Improvements Over Current System

1. **Action Item Extraction**
   - Explicit extraction of executable actions from LLM
   - Structured format for reliable automation

2. **Global SUGGESTION_MEMORY**
   - Central repository for active suggestions
   - Accessible across system components

3. **Confidence-Based Filtering**
   - Only high-confidence suggestions reach users
   - Reduces notification fatigue

4. **Two-Stage Confirmation**
   - Less disruptive initial notification
   - Detailed confirmation only after user interest

5. **Feedback Learning Loop**
   - Record user responses to suggestions
   - Improve suggestion quality over time
   - Adapt to user preferences and patterns
   - Self-improve without explicit programming

6. **Neural UI Integration**
   - Robust element targeting for reliable execution
   - Fallback mechanisms when needed
   - Visual verification of actions

## Implementation Status

1. ✅ Create action item extraction from LLM analysis
2. ✅ Implement SUGGESTION_MEMORY global parameter
3. ✅ Enhance notification system for two-stage confirmation
4. ✅ Integrate with neural UI detection for better execution
5. ✅ Add feedback loop for continuous improvement

## Testing Framework

An end-to-end testing framework verifies:
- Accuracy of suggestion generation
- Appropriateness of suggestions in different contexts
- Reliability of action execution
- User experience and confirmation flow
- System performance and resource usage
- Feedback learning effectiveness
- Quality score accuracy

## Metrics for Success

- Suggestion acceptance rate
- Execution success rate
- Time saved through automation
- User satisfaction scores
- System resource efficiency
- Learning rate and adaptation speed
- Quality score correlation with user acceptance