#!/usr/bin/env python3
import json
import logging
import os
import time
from datetime import datetime

# Configure logging
os.makedirs('logs/memory', exist_ok=True)

# Create a custom filter to prevent duplicate logs
class DuplicateFilter(logging.Filter):
    def __init__(self):
        super().__init__()
        self.last_log = None
        self.last_time = None
        self.min_interval = 5  # Minimum seconds between similar logs

    def filter(self, record):
        current_log = (record.levelno, record.getMessage())
        current_time = time.time()
        
        # Allow if it's a different message
        if current_log != self.last_log:
            self.last_log = current_log
            self.last_time = current_time
            return True
            
        # Allow if enough time has passed since last similar log
        if current_time - self.last_time >= self.min_interval:
            self.last_time = current_time
            return True
            
        return False

# Configure logging with rotation
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/memory/memory.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3
        ),
        RotatingFileHandler(
            'logs/memory/short_term.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3
        ),
        RotatingFileHandler(
            'logs/memory/context.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=3
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('minimal_memory')
logger.addFilter(DuplicateFilter())

# Reduce logging level for all modules
logging.getLogger('asyncio').setLevel(logging.ERROR)

class MinimalMemory:
    def __init__(self, memory_file="memory/memory_state.json"):
        self.memory_file = memory_file
        self.memory_state = self.load_memory()
        
    def load_memory(self):
        """Load memory state from file or create new if it doesn't exist"""
        try:
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Create new memory state
            logger.info("Creating new memory state")
            return {
                "version": "1.0",
                "last_update": datetime.now().isoformat(),
                "context": {},
                "short_term": [],
                "long_term": []
            }
    
    def save_memory(self):
        """Save memory state to file"""
        try:
            # Update timestamp
            self.memory_state["last_update"] = datetime.now().isoformat()
            
            # Save to file
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory_state, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving memory state: {e}")
            return False
    
    def run(self):
        """Main memory system loop"""
        logger.info("Starting minimal memory system")
        
        # Save PID
        os.makedirs("pids", exist_ok=True)
        with open('pids/memory.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        try:
            while True:
                # Update memory periodically
                self.save_memory()
                
                # Log status
                logger.debug(f"Memory state updated - {len(self.memory_state['short_term'])} short term memories, {len(self.memory_state['long_term'])} long term memories")
                
                # Sleep to avoid high CPU usage
                time.sleep(30)
        except KeyboardInterrupt:
            logger.info("Memory system stopped by user")
            self.save_memory()
        except Exception as e:
            logger.error(f"Error in memory system: {e}")
            self.save_memory()

if __name__ == "__main__":
    memory = MinimalMemory()
    memory.run()
