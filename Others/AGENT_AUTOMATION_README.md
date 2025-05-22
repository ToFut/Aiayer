# 🤖 Enhanced Agent Automation System

## Overview

The Enhanced Agent Automation System allows you to control your computer using natural language commands. Simply say things like "click the submit button" or "type hello in the search box" and the agent will understand and execute the actions.

## ✨ Key Features

- **Natural Language Understanding**: Commands like "click the button", "type text", "scroll down"
- **Smart Element Recognition**: Uses AI vision (LLaVA) and computer vision to find UI elements
- **Multiple Detection Methods**: Combines OCR, visual detection, and semantic understanding
- **Safety Features**: Built-in safety mechanisms and emergency shutdown (Ctrl+1)
- **Learning Capability**: Improves from successful/failed command patterns

## 🚀 Quick Start

### 1. Test the System
```bash
# Run comprehensive test
python test_complete_automation.py

# Test a single command
python agent_workflow/enhanced_automation_handler.py "click the submit button"
```

### 2. Basic Usage Examples
```python
from agent_workflow.enhanced_automation_handler import EnhancedAutomationHandler

# Initialize the handler
handler = EnhancedAutomationHandler()

# Execute commands
await handler.handle_user_instruction("click the submit button")
await handler.handle_user_instruction("type hello world in the search box")
await handler.handle_user_instruction("scroll down")
await handler.handle_user_instruction("what buttons are available?")
```

## 📋 Supported Commands

### Click Actions
- `"click the submit button"`
- `"press the save button"`
- `"tap the menu icon"`
- `"select the checkbox"`
- `"double click the file"`
- `"right click the menu"`

### Text Input
- `"type hello world in the search box"`
- `"enter my email in the field"`
- `"fill the form with data"`

### Navigation
- `"scroll down"`
- `"scroll up"`
- `"scroll to the bottom"`
- `"go to the settings"`

### Queries
- `"what buttons are available?"`
- `"where is the save button?"`
- `"what elements are on screen?"`
- `"show me the clickable items"`

## 🔧 System Architecture

```
User Command ("click the button")
    ↓
Enhanced Automation Handler
    ↓
Command Parser (understands intent)
    ↓
Screen Analyzer (finds elements)
    ├── LLaVA Visual AI
    ├── UI Element Detector  
    ├── OCR Text Recognition
    └── Computer Vision
    ↓
Element Matcher (finds target)
    ↓
Input Controller (executes action)
    ↓
Result & Feedback
```

## 🛠️ Setup Requirements

### Dependencies
- Python 3.8+
- LLaVA/Ollama (for AI vision)
- PyAutoGUI (for input control)
- OpenCV (for computer vision)
- Tesseract (for OCR)
- PIL/Pillow (for image processing)

### Install Requirements
```bash
pip install -r requirements.txt

# Install Tesseract OCR
# macOS: brew install tesseract
# Ubuntu: sudo apt-get install tesseract-ocr
# Windows: Download from GitHub
```

### LLaVA Setup
1. Install Ollama: https://ollama.ai/
2. Pull LLaVA model: `ollama pull llava`
3. Start Ollama service: `ollama serve`

## 🎯 Usage Examples

### Interactive Python Session
```python
import asyncio
from agent_workflow.enhanced_automation_handler import EnhancedAutomationHandler

async def demo():
    handler = EnhancedAutomationHandler()
    
    # Get screen summary
    summary = await handler.get_screen_summary()
    print(f"Found {summary['total_elements']} elements")
    
    # Execute commands
    result = await handler.handle_user_instruction("click the submit button")
    if result['success']:
        print("✅ Button clicked successfully!")
    else:
        print(f"❌ Failed: {result['error']}")
        
    handler.stop()

# Run the demo
asyncio.run(demo())
```

### Command Line Usage
```bash
# Single command
python enhanced_agent_automation.py "click the submit button"

# Via handler
python agent_workflow/enhanced_automation_handler.py "type hello in search box"

# Run tests
python test_complete_automation.py
```

## 🔍 How Element Detection Works

1. **Screen Capture**: Takes high-quality screenshot
2. **Multi-Method Analysis**:
   - **LLaVA AI**: Understands context and identifies UI elements semantically
   - **OCR**: Extracts all text with precise positions
   - **Computer Vision**: Detects shapes, buttons, and interactive elements
   - **Template Matching**: Recognizes common UI patterns
3. **Element Fusion**: Combines results from all methods
4. **Smart Matching**: Matches user intent to detected elements
5. **Confidence Scoring**: Ranks matches by likelihood
6. **Position Calculation**: Finds exact click coordinates

## ⚡ Performance Tips

- **LLaVA**: First run may be slow as model loads
- **Caching**: Screen analysis is cached for 5 seconds
- **Element Limits**: Shows top 20 elements to avoid overwhelm
- **Fallbacks**: Multiple detection methods ensure reliability

## 🛡️ Safety Features

- **Emergency Shutdown**: Press Ctrl+1 to immediately stop all automation
- **Safety Levels**: Configurable safety for destructive actions
- **Rate Limiting**: Prevents rapid-fire commands
- **Validation**: Confirms actions before execution
- **Logging**: All actions are logged for debugging

## 🐛 Troubleshooting

### Common Issues

1. **"No elements found"**
   - Check if LLaVA/Ollama is running: `ollama list`
   - Verify screen has interactive elements
   - Try different command phrasing

2. **"Element not found"**
   - Use query commands first: "what buttons are available?"
   - Try more specific descriptions: "submit button" vs "button"
   - Check element actually exists on screen

3. **"Click failed"**
   - Element might be covered or disabled
   - Try scrolling to bring element into view
   - Use "where is the X button?" to locate first

4. **Slow performance**
   - First LLaVA call is slow (model loading)
   - Subsequent calls use caching
   - Consider disabling LLaVA for simple commands

### Debug Commands
```bash
# Check system status
python test_complete_automation.py

# Get detailed element info
python -c "
import asyncio
from enhanced_agent_automation import EnhancedAgentAutomation
async def debug():
    auto = EnhancedAgentAutomation()
    elements = await auto.get_available_elements()
    for i, elem in enumerate(elements[:10]):
        print(f'{i+1}. {elem.get(\"element_text\", \"unnamed\")} ({elem.get(\"element_type\", \"unknown\")})')
    auto.stop()
asyncio.run(debug())
"
```

## 📊 Testing

Run the comprehensive test suite:
```bash
python test_complete_automation.py
```

This will test:
- ✅ Screen analysis and element detection
- ✅ Natural language command parsing
- ✅ Simple automation (scroll, click)
- ✅ Complex automation (specific targets)
- ✅ Error handling and edge cases

## 🎓 Advanced Usage

### Custom Command Patterns
You can extend the command patterns in `enhanced_automation_handler.py`:

```python
# Add new command category
self.command_categories["custom"] = ["my_action", "special_command"]

# Add custom handler
async def _handle_custom_command(self, instruction, context):
    # Your custom logic here
    pass
```

### Integration with Agent System
```python
from agent_workflow.agent_system import AgentSystem
from agent_workflow.enhanced_automation_handler import EnhancedAutomationHandler

# Integrate with existing agent
agent = AgentSystem()
automation = EnhancedAutomationHandler()

# Handle user instructions through automation
async def process_instruction(instruction):
    result = await automation.handle_user_instruction(instruction)
    return result
```

## 🤝 Contributing

The system is designed to be extensible:

1. **Add Detection Methods**: Extend `ui_element_detector.py`
2. **Improve Matching**: Enhance `_calculate_element_match_confidence`
3. **Add Commands**: Extend `command_patterns` in handler
4. **Improve Learning**: Enhance `_learn_from_result` method

## 📝 Logs

Logs are stored in:
- `logs/enhanced_agent/enhanced_automation.log`
- `logs/agent_workflow/enhanced_automation_handler.log`
- `logs/sensors/ui_element_detector.log`

## 🎉 Success Indicators

When working properly, you should see:
- ✅ Screen analysis finds multiple UI elements
- ✅ Commands parse correctly into actions and targets
- ✅ Element matching finds reasonable candidates
- ✅ Actions execute without errors
- ✅ High confidence scores (>0.7) for good matches

The system is working when users can say "click the submit button" and it just works! 🚀