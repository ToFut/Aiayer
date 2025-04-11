#!/usr/bin/env python3
"""
Local AI Assistant - Main Entry Point
This script initializes and starts all components of the local AI assistant.
"""
import os
import sys
import signal
import asyncio
import logging
from logging.handlers import RotatingFileHandler
import yaml

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm.model_main import LocalLLM
from sensors.file_sensor import FileSensor
from sensors.process_sensor import ProcessSensor
from sensors.ai_sensor import AISensor

def load_config():
    """Load configuration from YAML file."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {}

def setup_logging():
    """Configure logging for the main application."""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'main.log')
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

class SystemComponents:
    def __init__(self):
        self.config = load_config()
        self.llm = None
        self.file_sensor = None
        self.process_sensor = None
        self.ai_sensor = None
        self.running = False
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """Start all system components."""
        try:
            # Initialize components with config
            self.llm = LocalLLM(**self.config.get('llm', {}))
            self.file_sensor = FileSensor()
            self.process_sensor = ProcessSensor()
            self.ai_sensor = AISensor()
            
            # Start components in sequence
            components = [
                ('llm', self.llm),
                ('file_sensor', self.file_sensor),
                ('process_sensor', self.process_sensor),
                ('ai_sensor', self.ai_sensor)
            ]
            
            for name, component in components:
                try:
                    if hasattr(component, 'start'):
                        result = component.start()
                        if asyncio.iscoroutine(result):
                            result = await result
                        if not result:
                            raise RuntimeError(f"Failed to start {name}")
                    self.logger.info(f"{name} started successfully")
                except Exception as e:
                    self.logger.error(f"Error starting {name}: {e}")
                    await self.stop()
                    return False
            
            self.running = True
            self.logger.info("All components started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting components: {e}")
            await self.stop()
            return False

    async def stop(self):
        """Stop all system components in reverse order."""
        components = [
            ('ai_sensor', self.ai_sensor),
            ('process_sensor', self.process_sensor),
            ('file_sensor', self.file_sensor),
            ('llm', self.llm)
        ]
        
        for name, component in components:
            if component:
                try:
                    if hasattr(component, 'stop'):
                        result = component.stop()
                        if asyncio.iscoroutine(result):
                            result = await result
                    self.logger.info(f"{name} stopped successfully")
                except Exception as e:
                    self.logger.error(f"Error stopping {name}: {e}")
        
        self.running = False
        self.logger.info("All components stopped")

async def main():
    """Main entry point."""
    logger = setup_logging()
    components = SystemComponents()
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        if components.running:
            asyncio.create_task(components.stop())
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start components
        if not await components.start():
            logger.error("Failed to start system")
            return False
        
        # Keep the main thread alive
        while components.running:
            await asyncio.sleep(1)
            
        return True
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        await components.stop()
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)