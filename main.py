#!/usr/bin/env python3
"""
Aiayer - Local AI Assistant
Main entry point for the application
"""

import asyncio
import logging
import sys
import signal
import os
from pathlib import Path
from typing import Optional
import yaml
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from enhanced_enterprise_backend import EnhancedEnterpriseBackend
from utils.logging_setup import setup_logging
from security.auth_system import AuthenticationSystem as AuthSystem

class AiayerApplication:
    """Main application class for Aiayer"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/config.yaml"
        self.config = {}
        self.backend: Optional[EnhancedEnterpriseBackend] = None
        self.auth_system: Optional[AuthSystem] = None
        self.logger = logging.getLogger(__name__)
        self.running = False
        
    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            from utils.config_validator import ConfigValidator
            
            validator = ConfigValidator(self.config_path)
            
            # Try to validate existing config
            if not validator.validate():
                self.logger.warning("Configuration validation failed, creating default config")
                if not validator.create_default_config():
                    self.logger.error("Failed to create default configuration")
                    return False
            
            # Load the validated config
            self.config = validator.get_config()
            self.logger.info("Configuration loaded and validated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return False
    
    async def initialize(self) -> bool:
        """Initialize the application"""
        try:
            # Setup logging
            log_level = self.config.get('logging', {}).get('level', 'INFO')
            setup_logging(log_level)
            
            # Initialize auth system
            self.auth_system = AuthSystem()
            await self.auth_system.initialize()
            
            # Initialize backend
            self.backend = EnhancedEnterpriseBackend(self.config)
            await self.backend.initialize()
            
            self.logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False
    
    async def start(self) -> bool:
        """Start the application"""
        try:
            if not self.backend:
                self.logger.error("Backend not initialized")
                self.running = False  # Ensure running is False on failure
                return False
                
            self.running = True
            await self.backend.start()
            self.logger.info("Application started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start application: {e}")
            self.running = False  # Ensure running is False on failure
            return False
    
    async def stop(self) -> bool:
        """Stop the application"""
        try:
            self.running = False
            
            if self.backend:
                await self.backend.stop()
                
            if self.auth_system:
                await self.auth_system.cleanup()
                
            self.logger.info("Application stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop application: {e}")
            return False
    
    async def run(self) -> None:
        """Main application loop"""
        exit_code = 0
        try:
            if not await self.initialize():
                exit_code = 1
            elif not await self.start():
                exit_code = 1
            else:
                # Keep running until interrupted
                while self.running:
                    await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            exit_code = 1
        finally:
            await self.stop()
            if exit_code != 0:
                sys.exit(exit_code)

def signal_handler(signum, frame):
    """Handle system signals"""
    logging.info(f"Received signal {signum}")
    sys.exit(0)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Aiayer - Local AI Assistant")
    parser.add_argument(
        "--config", 
        default="config/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="Enable debug mode"
    )
    
    args = parser.parse_args()
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run application
    app = AiayerApplication(args.config)
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    
    try:
        asyncio.run(app.run())
    except Exception as e:
        logging.error(f"Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 