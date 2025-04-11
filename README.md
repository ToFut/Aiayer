# Local AI Assistant

A privacy-focused AI assistant that runs entirely on your local machine, with no data leaving your system. This application uses multiple sensor modules (screen, file system, processes, and more) to understand your context and provide helpful responses using a local language model.

## 🚀 Features

- **Complete Privacy**: All processing happens locally - no data is sent to the cloud
- **Context-Aware**: Understands what you're working on by monitoring:
  - Screen content (via screenshots + OCR)
  - File system changes (files you create/modify)
  - Running applications and active windows
  - (Optional) Browser activity
- **Local LLM**: Uses [Mistral 7B](https://mistral.ai/news/announcing-mistral-7b/) (or other models) via [Ollama](https://ollama.ai/)
- **Security-Focused**: Filters sensitive information to prevent accidental exposure
- **Easy Deployment**: Run with Docker or a Python virtual environment

## 📋 Requirements

- macOS or Linux (Windows support via Docker/WSL2)
- 8GB+ RAM (recommended 16GB for optimal performance)
- Python 3.8+ (if not using Docker)
- [Ollama](https://ollama.ai/) (installed automatically in Docker)

## 🔧 Installation

### Using Docker (Recommended)

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/local-ai-assistant.git
   cd local-ai-assistant
   ```

2. Start with Docker Compose:
   ```
   docker-compose up
   ```

3. Open your browser to http://localhost:5000 to use the assistant.

### Manual Installation (macOS/Linux)

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/local-ai-assistant.git
   cd local-ai-assistant
   ```

2. Install Tesseract OCR:
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`

3. Install Ollama from https://ollama.ai/

4. Create a virtual environment and install dependencies:
   ```
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. Run the assistant:
   ```
   python main.py
   ```

6. Open your browser to http://localhost:5000.

### Windows Installation

For Windows, we recommend using Docker Desktop with WSL2. Alternatively, see the [Windows Installation Guide](docs/windows-install.md) for native setup instructions.

## ⚙️ Configuration

The assistant is configured through the `config/config.yaml` file. You can customize:

- Which folders to monitor
- Screenshot interval
- LLM settings
- UI preferences
- And more

Example configuration:

```yaml
# Edit config/config.yaml
sensors:
  screen:
    interval_sec: 5
  file:
    paths:
      - "~/Documents"
      - "~/Desktop"
      - "~/Downloads"
```

## 🔒 Security & Privacy

- All data stays on your machine
- The assistant can filter sensitive information (passwords, personal data, etc.)
- No telemetry or analytics are collected
- Docker containers are isolated from your network by default

## 🤝 Usage Examples

The assistant can:

- Answer questions about what's on your screen
- Provide context-aware help based on the application you're using
- Remember files you've recently worked on
- Assist with coding, writing, and other tasks based on what it can see

Simply ask in natural language:

- "What's in this document I'm looking at?"
- "What files did I edit today?"
- "Explain the error message on my screen"
- "Summarize what I'm working on"

## 🔍 How It Works

This assistant combines several key components:

1. **Sensor Modules**: Capture your real-time context (screen, files, apps)
2. **Local LLM**: Processes your questions with contextual understanding
3. **Task Agent**: Orchestrates between sensors, memory, and the LLM
4. **Memory**: Maintains conversation history for continuity
5. **UI**: Provides a simple chat interface for interaction

All components run locally and communicate within your device.

## 🧩 Extending the System

The project is designed to be modular and extensible. You can:

- Add new sensor types
- Integrate with other LLMs
- Enhance the UI
- Add additional tools and capabilities

See the [Developer Documentation](docs/developer.md) for details on the architecture.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Limitations

- Requires appropriate permissions (screen recording, accessibility)
- Uses CPU/RAM resources for running the LLM
- Limited to what it can observe through the provided sensors

## 🙏 Acknowledgements

- [Mistral AI](https://mistral.ai/) for their excellent open models
- [Ollama](https://ollama.ai/) for easy local LLM deployment
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text extraction
- All the open-source libraries used in this project