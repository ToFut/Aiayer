#!/usr/bin/env python3
"""
Centralized Logging Setup
Provides a unified logging configuration for all components.
"""
import os
import logging
import logging.config
from pathlib import Path

def setup_logging(config_path: str = 'config/logging.conf'):
    """Setup logging configuration for the entire application."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create component-specific log directories
    log_dirs = [
        'logs/sensors',
        'logs/llm',
        'logs/agent',
        'logs/ui',
        'logs/memory',
        'logs/websocket',
        'logs/bridge',
        'logs/neural_ui',
        'logs/do_button',
        'logs/overlay',
        'logs/backend',
        'logs/ui_detection'
    ]
    for log_dir in log_dirs:
        os.makedirs(log_dir, exist_ok=True)
    
    # Load logging configuration
    if os.path.exists(config_path):
        logging.config.fileConfig(config_path)
    else:
        # Fallback to basic configuration if config file not found
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('logs/fallback.log')
            ]
        )
        logging.warning(f"Logging config file not found: {config_path}, using fallback configuration")

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)

# Initialize logging when module is imported
setup_logging() 