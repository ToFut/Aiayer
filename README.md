# Aiayer - Local AI Assistant

Aiayer is an intelligent local AI assistant that provides context-aware assistance using local AI models. It monitors your system activities and provides intelligent responses based on your current context.

## Features

- **Context-Aware Assistance**: Understands your current activities and provides relevant help
- **Local Processing**: All processing happens on your machine, ensuring privacy
- **Multiple Sensors**: Monitors screen, files, processes, and browser activities
- **Conversation Memory**: Maintains context across conversations
- **Real-time Analysis**: Continuously analyzes your context for better assistance

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ToFut/Aiayer.git
cd Aiayer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install test dependencies (optional):
```bash
pip install -r tests/requirements-test.txt
```

## Configuration

1. Copy the example configuration:
```bash
cp config/config.example.yaml config/config.yaml
```

2. Edit `config/config.yaml` to customize:
- Sensor intervals
- Memory settings
- LLM model configuration
- Browser monitoring settings

## Usage

### Starting the Assistant

1. Start the main application:
```bash
python main.py
```

2. Or use the simple runner script:
```bash
./run_simple.sh
```

### Interacting with the Assistant

1. The assistant will automatically start monitoring your system
2. Use the chat interface to interact with the assistant
3. The assistant will respond based on your current context

### Available Commands

- `help`: Show available commands
- `status`: Show current system status
- `context`: Show current context analysis
- `memory`: Show conversation history
- `sensors`: Show sensor status
- `exit`: Stop the assistant

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Structure

- `agent/`: Core AI agent functionality
- `memory/`: Conversation and context memory
- `llm/`: Local language model integration
- `sensors/`: System monitoring sensors
- `tests/`: Test suite
- `ui/`: User interface components

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.