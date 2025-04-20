#!/usr/bin/env python3
"""
Local AI Assistant - Main Entry Point
Enhanced version with proper component management
"""
import os
import logging
import asyncio
import signal
import sys
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from sensors.overlay_sensor import OverlaySensor
from sensors.screen_sensor import ScreenSensor
from sensors.process_sensor import ProcessSensor
from agent.context_analyzer import ContextAnalyzer
from agent.task_agent import TaskAgent
from sensors.llm_analyzer import LocalLLMAnalyzer
from screen_controller import ScreenController
from memory import Memory
from llm import LocalLLM
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/main.log')
    ]
)
logger = logging.getLogger(__name__)

class LocalAssistant:
    """Main class managing the local assistant components."""
    
    def __init__(self):
        self.components: Dict[str, Any] = {}
        self.running = False
        
    async def initialize(self) -> bool:
        """Initialize all components."""
        try:
            logger.info("Initializing system components...")
            
            # Initialize sensors
            self.components['overlay'] = OverlaySensor()
            self.components['screen'] = ScreenSensor()
            self.components['process'] = ProcessSensor()
            
            # Initialize context analyzer with sensors
            self.components['context_analyzer'] = ContextAnalyzer(
                sensors={
                    'screen': self.components['screen'],
                    'process': self.components['process']
                }
            )
            
            # Initialize shared components
            self.components['llm'] = LocalLLM()
            self.components['memory'] = Memory()
            self.components['llm_analyzer'] = LocalLLMAnalyzer(self.components['llm'])
            
            # Initialize screen controller with shared components
            self.components['screen_controller'] = ScreenController(
                screen_sensor=self.components['screen'],
                llm_analyzer=self.components['llm_analyzer']
            )
            
            # Initialize task agent with shared components
            self.components['task_agent'] = TaskAgent(
                llm=self.components['llm'],
                memory=self.components['memory'],
                screen_controller=self.components['screen_controller'],
                llm_analyzer=self.components['llm_analyzer']
            )
            
            # Start screen controller
            await self.components['screen_controller'].start()
            
            logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            await self.cleanup()
            return False
    
    async def cleanup(self):
        """Clean up all components."""
        logger.info("Cleaning up system components...")
        for name, component in self.components.items():
            if component:
                try:
                    if hasattr(component, 'stop'):
                        component.stop()
                    if hasattr(component, 'cleanup'):
                        await component.cleanup()
                    logger.info(f"Cleaned up {name} component")
                except Exception as e:
                    logger.error(f"Error cleaning up {name} component: {e}")
        self.components.clear()
        logger.info("All components cleaned up")

    async def run(self):
        """Main run loop."""
        self.running = True
        try:
            while self.running:
                # Main loop logic here
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("Run loop cancelled")
        finally:
            self.running = False
            await self.cleanup()
    
    def stop(self):
        """Stop the assistant."""
        self.running = False

# Initialize Flask app 
app = Flask(__name__,
    static_folder=os.path.join(os.path.dirname(__file__), 'ui', 'static'),
    static_url_path='/static',
    template_folder=os.path.join(os.path.dirname(__file__), 'ui', 'templates')
)
CORS(app)

@app.route('/')
def index():
    """Render the main page."""
    return "Welcome to Local AI Assistant!"

@app.route('/chat')
def chat():
    """Render the chat interface."""
    try:
        logger.info("Rendering chat page")
        return render_template('chat.html', 
                             conversation=[],
                             version={"assistant": "Local AI Assistant v0.1.0"})
    except Exception as e:
        logger.error(f"Error rendering chat: {str(e)}")
        return "Error loading chat interface", 500

@app.route('/health')
def health():
    """Health check endpoint."""
    status = {
        'status': 'ok',
        'version': '0.1.0',
        'components': {}
    }
    
    # Check each component's status
    for name, component in self.components.items():
        if component:
            try:
                if hasattr(component, 'get_status'):
                    status['components'][name] = component.get_status()
                else:
                    status['components'][name] = 'running'
            except Exception as e:
                status['components'][name] = f'error: {str(e)}'
        else:
            status['components'][name] = 'not_initialized'
    
    return jsonify(status)

@app.route('/test')
def test():
    return "Test route is working!"

async def main():
    """Initialize and run the local assistant."""
    assistant = LocalAssistant()
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        assistant.stop()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if await assistant.initialize():
            await assistant.run()
        else:
            logger.error("Failed to initialize assistant")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        await assistant.cleanup()
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise