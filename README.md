# Aiayer - Local AI Assistant

A comprehensive local AI assistant system that provides intelligent automation, document processing, and contextual awareness through advanced UI detection and machine learning capabilities.

## 🚀 Features

- **Intelligent UI Detection**: Advanced computer vision and OCR for screen content analysis
- **Document Intelligence**: Automated document processing and information extraction
- **Contextual Memory**: Short-term and long-term memory management for conversations
- **Real-time Automation**: Browser and desktop automation capabilities
- **Secure Local Processing**: All processing happens locally for privacy
- **Multi-modal Input**: Support for text, image, and document inputs
- **Extensible Architecture**: Plugin-based system for custom functionality

## 📋 Prerequisites

- Python 3.8 or higher
- macOS, Linux, or Windows
- 8GB+ RAM recommended
- GPU acceleration (optional, for enhanced ML performance)

### System Dependencies

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install tesseract
brew install python@3.11
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev
```

#### Windows
```bash
# Install Chocolatey if not already installed
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install system dependencies
choco install python311
choco install tesseract
```

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sensai/aiayer.git
   cd aiayer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements_enhanced_ui_detection.txt
   ```

4. **Install spaCy language model**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Setup configuration**
   ```bash
   cp config/config.example.yaml config/config.yaml
   # Edit config/config.yaml with your preferences
   ```

6. **Install Ollama (for local LLM)**
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ollama pull mistral  # or your preferred model
   ```

## 🚀 Quick Start

### Development Mode
```bash
# Start the application
python main.py

# Or with debug mode
python main.py --debug
```

### Production Mode
```bash
# Using Docker
docker-compose up -d

# Or using systemd (Linux)
sudo cp systemd/aiayer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable aiayer
sudo systemctl start aiayer
```

## 📖 Usage

### Basic Usage

1. **Start the application**
   ```bash
   python main.py
   ```

2. **Access the web interface**
   - Open your browser to `http://localhost:5001`
   - The overlay interface will be available at `http://localhost:8765`

3. **Configure sensors**
   - Edit `config/config.yaml` to enable/disable sensors
   - Adjust paths for file monitoring
   - Configure LLM settings

### Advanced Configuration

#### Sensor Configuration
```yaml
sensors:
  screen:
    enabled: true
    interval_sec: 10
    capture_active_window_only: true
    ocr_language: "eng"
  
  file:
    enabled: true
    paths:
      - "/path/to/monitor"
    ignore_patterns:
      - "*.tmp"
      - ".git/*"
  
  process:
    enabled: true
    interval_sec: 5
    track_all_processes: false
```

#### LLM Configuration
```yaml
llm:
  model_name: "mistral:latest"
  host: "localhost"
  port: 11434
  temperature: 0.7
  max_tokens: 1000
```

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_main.py
```

### Test Coverage
```bash
# Generate coverage report
pytest --cov=. --cov-report=html --cov-report=term
```

## 🐳 Docker Deployment

### Build and Run
```bash
# Build the image
docker build -t aiayer .

# Run the container
docker run -d \
  --name aiayer \
  -p 5000:5000 \
  -p 5001:5001 \
  -p 8765:8765 \
  -v /path/to/config:/app/config \
  aiayer
```

### Using Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔧 Development

### Project Structure
```
aiayer/
├── main.py                 # Main application entry point
├── enhanced_enterprise_backend.py  # Core backend system
├── neural_ui_detector.py   # UI detection engine
├── config/                 # Configuration files
├── tests/                  # Test suite
├── docs/                   # Documentation
├── security/               # Authentication and security
├── sensors/                # Sensor implementations
├── memory/                 # Memory management
├── utils/                  # Utility functions
└── web/                    # Web interface
```

### Adding New Features

1. **Create a new module**
   ```python
   # sensors/new_sensor.py
   class NewSensor:
       async def initialize(self):
           pass
       
       async def start(self):
           pass
   ```

2. **Add tests**
   ```python
   # tests/test_new_sensor.py
   def test_new_sensor():
       sensor = NewSensor()
       # Add test cases
   ```

3. **Update configuration**
   ```yaml
   sensors:
     new_sensor:
       enabled: true
       # Add configuration options
   ```

### Code Style
- Follow PEP 8 for Python code
- Use type hints
- Add docstrings for all functions and classes
- Write unit tests for new features

## 📚 API Documentation

### REST API Endpoints

- `GET /health` - Health check
- `POST /api/process` - Process input
- `GET /api/memory` - Get memory contents
- `POST /api/memory` - Add to memory

### WebSocket Events

- `connect` - Client connection
- `disconnect` - Client disconnection
- `message` - Send/receive messages
- `sensor_data` - Real-time sensor data

## 🔒 Security

- All processing happens locally
- No data is sent to external servers
- Configurable access controls
- Encrypted storage for sensitive data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks
pre-commit install

# Run linting
flake8 .
black .
isort .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/sensai/aiayer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sensai/aiayer/discussions)

## 🗺️ Roadmap

- [ ] Enhanced UI detection with deep learning
- [ ] Multi-language support
- [ ] Mobile app companion
- [ ] Cloud synchronization (optional)
- [ ] Plugin marketplace
- [ ] Advanced automation workflows

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM support
- [Ultralytics](https://ultralytics.com/) for YOLO object detection
- [spaCy](https://spacy.io/) for NLP capabilities
- [OpenCV](https://opencv.org/) for computer vision 