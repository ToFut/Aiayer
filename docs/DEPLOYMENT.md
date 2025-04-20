# Deployment Guide

## Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)
- Required system permissions:
  - Screen recording access
  - File system access
  - Process monitoring access
  - Browser monitoring access (optional)

## Installation Steps

1. **System Dependencies**

   ```bash
   # macOS
   brew install tesseract  # For OCR
   
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install tesseract-ocr
   ```

2. **Python Environment Setup**

   ```bash
   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configuration**

   ```bash
   # Copy and edit configuration
   cp config/config.example.yaml config/config.yaml
   nano config/config.yaml  # Edit with your preferences
   ```

4. **LLM Setup**

   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull the model
   ollama pull mistral  # or your preferred model
   ```

## Running the Application

1. **Development Mode**

   ```bash
   # Start the application
   python main.py
   
   # Or use the simple runner
   ./run_simple.sh
   ```

2. **Production Mode**

   ```bash
   # Use systemd service (Linux)
   sudo cp systemd/aiayer.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable aiayer
   sudo systemctl start aiayer
   ```

3. **Docker Deployment**

   ```bash
   # Build the image
   docker build -t aiayer .
   
   # Run the container
   docker run -d \
     --name aiayer \
     -p 5000:5000 \
     -v /path/to/config:/app/config \
     aiayer
   ```

## Monitoring

1. **Logs**

   ```bash
   # View application logs
   tail -f logs/aiayer.log
   
   # Systemd logs
   journalctl -u aiayer -f
   ```

2. **Metrics**

   - CPU usage
   - Memory consumption
   - Response times
   - Error rates

## Scaling

1. **Vertical Scaling**
   - Increase system resources
   - Adjust configuration parameters

2. **Horizontal Scaling**
   - Deploy multiple instances
   - Use load balancer
   - Configure shared memory

## Backup and Recovery

1. **Data Backup**

   ```bash
   # Backup configuration
   tar -czf config_backup.tar.gz config/
   
   # Backup logs
   tar -czf logs_backup.tar.gz logs/
   ```

2. **Recovery**

   ```bash
   # Restore configuration
   tar -xzf config_backup.tar.gz
   
   # Restore logs
   tar -xzf logs_backup.tar.gz
   ```

## Security Considerations

1. **Permissions**
   - Run with minimal required privileges
   - Use dedicated user account
   - Restrict file system access

2. **Network**
   - Use HTTPS in production
   - Configure firewall rules
   - Enable rate limiting

3. **Data**
   - Encrypt sensitive data
   - Regular security audits
   - Update dependencies

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

## Maintenance

1. **Updates**

   ```bash
   # Update dependencies
   pip install -r requirements.txt --upgrade
   
   # Update configuration
   git pull
   cp config/config.example.yaml config/config.yaml.new
   # Merge changes manually
   ```

2. **Cleanup**

   ```bash
   # Clear old logs
   find logs/ -type f -mtime +30 -delete
   
   # Clear temporary files
   rm -rf tmp/*
   ``` 