"""
Main entry point for the LLM Model
"""
import os
import sys
import time
import yaml
import logging
from logging.handlers import RotatingFileHandler

# Add parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.model import LocalLLM

def setup_logging():
    """Configure logging for the LLM model."""
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, 'llm_model.log')
    
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

def load_config():
    """Load configuration from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            llm_config = config.get('llm', {})
            if not llm_config:
                logger.warning("No LLM configuration found in config file")
                llm_config = {
                    'model_name': 'mistral',
                    'host': 'localhost',
                    'port': 11434
                }
            # Extract only the necessary parameters
            return {
                'model_name': llm_config.get('model_name', 'mistral'),
                'host': llm_config.get('host', 'localhost'),
                'port': llm_config.get('port', 11434)
            }
    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}. Using default settings.")
        return {
            'model_name': 'mistral',
            'host': 'localhost',
            'port': 11434
        }
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {
            'model_name': 'mistral',
            'host': 'localhost',
            'port': 11434
        }

def main():
    """Main function to run the LLM model."""
    logger = setup_logging()
    model = None
    
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Load configuration
        llm_config = load_config()
        logger.info(f"Loaded LLM configuration: {llm_config}")
        
        # Initialize model
        try:
            model = LocalLLM(**llm_config)
            logger.info("LLM Model initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LLM model: {e}")
            return False
        
        # Start the model
        if not model.start():
            logger.error("Failed to start LLM Model")
            return False
            
        logger.info("LLM Model started successfully")
        
        # Main loop
        while True:
            try:
                # Check model health
                if not model.is_healthy():
                    logger.warning("LLM Model health check failed")
                    if not model._ensure_model_available():
                        logger.error("Failed to recover model health")
                        return False
                
                # Sleep briefly
                time.sleep(5)
                
            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)  # Wait before retrying
                
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return False
    finally:
        if model:
            model.stop()
        logger.info("LLM Model shutdown complete")
        
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nShutting down LLM model...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 