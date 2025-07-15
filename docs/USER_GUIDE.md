# SensAI User Guide

## 🎯 What is SensAI?

SensAI is an intelligent AI assistant that can understand, automate, and enhance your computer interactions. Think of it as having a smart assistant who can see your screen, understand what you're doing, and help you be more productive.

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone https://github.com/your-repo/sensai.git
cd sensai

# Install dependencies
pip install -r requirements.txt

# Start the system
./START_MASTER_SYSTEM.sh
```

### First Use
1. **Start the system** using the startup script
2. **Open the overlay** - press the hotkey to bring up the chat interface
3. **Choose your mode**:
   - **Ask**: "What's on my screen right now?"
   - **Agent**: "Open Spotify and play my favorite music"
   - **Suggest**: Let the AI suggest helpful actions
   - **General**: Have a conversation

## 🤖 Understanding the Modes

### Agent Mode - Physical Automation
**What it does**: Actually performs actions on your computer

**Examples**:
- "Open Chrome and go to Gmail"
- "Save this document as 'Project_Report.pdf'"
- "Click the 'Submit' button"

**How it works**:
1. AI analyzes your request
2. Creates a step-by-step plan
3. Shows you the plan for approval
4. Executes each step with visual feedback
5. Confirms completion

### Ask Mode - Context-Aware Answers
**What it does**: Provides intelligent answers using your screen context

**Examples**:
- "What's in this email?"
- "Summarize this document"
- "What applications are currently running?"

**How it works**:
1. Analyzes your current screen
2. Searches through your memory
3. Provides detailed, contextual responses

### Suggest Mode - Proactive Assistance
**What it does**: Automatically suggests helpful actions

**Examples**:
- Notices you're working on a document → "Would you like me to save this?"
- Sees you're browsing → "Should I bookmark this page?"
- Detects repetitive tasks → "I can automate this for you"

### General Mode - Conversational AI
**What it does**: Natural conversation with memory

**Examples**:
- "What did we work on yesterday?"
- "Remind me about that project from last week"
- "What's my typical morning routine?"

## 🎨 Using the Interface

### Chat Overlay
- **Hotkey**: Press the configured hotkey to open/close
- **Modes**: Switch between Ask, Agent, Suggest, General
- **History**: View past conversations and actions
- **Settings**: Configure preferences and behavior

### Web Dashboard
- **URL**: http://localhost:8082
- **Memory**: View what the AI has learned about you
- **Documents**: See analyzed documents and insights
- **Analytics**: Track your productivity patterns

## 🔧 Configuration

### Basic Settings
```yaml
# config/user_config.yaml
interface:
  hotkey: "Cmd+Shift+A"  # macOS
  theme: "dark"
  sound_enabled: true

automation:
  safety_level: "high"  # high, medium, low
  confirmation_required: true
  max_execution_time: 300  # seconds

memory:
  retention_days: 30
  auto_cleanup: true
  privacy_mode: false
```

### Advanced Settings
```yaml
# config/advanced_config.yaml
llm:
  model: "llama3.2:latest"
  temperature: 0.7
  max_tokens: 2048

automation:
  mouse_speed: "medium"
  keyboard_delay: 0.1
  retry_attempts: 3

security:
  enable_encryption: true
  audit_logging: true
  ip_restrictions: []
```

## 🛡️ Safety Features

### Confirmation System
- **Action Preview**: See exactly what will happen before execution
- **Step-by-Step**: Execute complex tasks one step at a time
- **Emergency Stop**: Press Ctrl+1 to immediately stop all automation
- **Undo Capability**: Reverse recent actions when possible

### Privacy Controls
- **Local Processing**: All AI processing happens on your computer
- **Data Retention**: Control how long your data is kept
- **Privacy Mode**: Disable memory features for sensitive work
- **Data Export**: Export and delete your data anytime

## 🎯 Best Practices

### Getting the Best Results
1. **Be Specific**: "Open Chrome and go to Gmail" vs "Open email"
2. **Use Natural Language**: Talk to it like a human assistant
3. **Provide Context**: "In the document I'm editing, find all mentions of 'budget'"
4. **Confirm Actions**: Review plans before execution
5. **Give Feedback**: Tell it when it does something well or wrong

### Common Use Cases
- **Document Work**: "Organize my downloads folder"
- **Web Automation**: "Book a flight from NYC to Miami"
- **File Management**: "Find all PDFs from last month"
- **Information Retrieval**: "What was that project from last week?"
- **Routine Automation**: "Set up my morning workspace"

## 🔍 Troubleshooting

### Common Issues

**System won't start**
```bash
# Check dependencies
pip install -r requirements.txt

# Check ports
lsof -i :8765,8767,8768

# View logs
tail -f logs/startup.log
```

**Automation not working**
- Check screen recording permissions
- Verify mouse/keyboard access
- Ensure target application is visible
- Try running in compatibility mode

**AI responses are slow**
- Check Ollama is running: `ollama list`
- Restart the LLM service
- Reduce model complexity in settings

**Memory not working**
- Check disk space
- Verify database permissions
- Restart memory service

### Getting Help
- **Logs**: Check `logs/` directory for detailed error information
- **Status**: Use `./manage_enterprise_system.sh status` to check system health
- **Support**: Create an issue on GitHub with logs and steps to reproduce

## 🔄 Updates and Maintenance

### Updating the System
```bash
# Backup your configuration
cp config/user_config.yaml config/user_config.yaml.backup

# Update the system
git pull origin main
pip install -r requirements.txt

# Restart the system
./STOP_MASTER_SYSTEM.sh
./START_MASTER_SYSTEM.sh
```

### Regular Maintenance
- **Weekly**: Check for updates
- **Monthly**: Review and clean up memory
- **Quarterly**: Backup your configuration and data

## 📞 Support

### Getting Help
- **Documentation**: Check this guide and other docs in the `docs/` folder
- **Issues**: Report bugs on GitHub
- **Community**: Join our Discord for help and discussions

### System Requirements
- **OS**: macOS 10.15+, Windows 10+, Ubuntu 18.04+
- **Python**: 3.8 or higher
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 2GB free space
- **Network**: Internet connection for model downloads

---

**Version**: 1.0.0  
**Last Updated**: June 2025  
**Support**: GitHub Issues or Discord Community 