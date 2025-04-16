#!/usr/bin/env python3
"""
Local AI Assistant - Main Entry Point
This script initializes and starts all components of the local AI assistant.
"""
import os
import sys
import time
import yaml
import logging
import logging.config
from threading import Thread
import requests
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
from dotenv import load_dotenv
from typing import Dict, Any
import asyncio

# Import all components
from sensors.screen_sensor import ScreenSensor
from sensors.file_sensor import FileSensor
from sensors.process_sensor import ProcessSensor
from sensors.browser_sensor import BrowserSensor
from llm.model import LocalLLM
from memory.memory import ConversationMemory
from agent.data_filter import DataFilter
from agent.task_agent import TaskAgent
from agent.context_analyzer import ContextAnalyzer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/main.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app with correct static and template paths
static_folder = os.path.join(os.path.dirname(__file__), 'ui', 'static')
template_folder = os.path.join(os.path.dirname(__file__), 'ui', 'templates')

app = Flask(__name__,
    static_folder=static_folder,
    static_url_path='/static',
    template_folder=template_folder
)
CORS(app)

# Global instances
agent = None
memory = None
sensors = {}
server_start_time = time.time()

def load_config():
    """Load configuration from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Config file not found at {config_path}. Using default settings.")
        return {
            'sensors': {
                'screen': {'interval_sec': 5},
                'file': {'paths': [os.path.expanduser('~/Documents')]},
                'process': {'interval_sec': 5},
                'browser': {'enabled': False, 'polling_interval_sec': 5}
            },
            'llm': {
                'model_name': 'mistral',
                'host': 'localhost',
                'port': 11434
            },
            'memory': {
                'max_conversation_length': 50
            }
        }

def initialize_components(config):
    """Initialize all components of the system."""
    global agent, memory, sensors
    
    # Initialize sensors
    sensors = {
        'screen': ScreenSensor(int(config['sensors']['screen']['interval_sec'])),
        'file': FileSensor(config['sensors']['file']['paths']),
        'process': ProcessSensor(int(config['sensors']['process']['interval_sec'])),
        'browser': BrowserSensor(int(config['sensors']['browser']['polling_interval_sec'])) if config['sensors']['browser']['enabled'] else None
    }
    
    # Initialize LLM
    llm = LocalLLM(
        model_name=config['llm']['model_name'],
        host=config['llm']['host'],
        port=config['llm']['port']
    )
    
    # Initialize memory
    memory = ConversationMemory(
        max_length=config['memory']['max_conversation_length']
    )
    
    # Initialize data filter
    data_filter = DataFilter()
    
    # Initialize context analyzer with LLM as a dictionary
    context_analyzer = ContextAnalyzer({'main': llm}, sensors)
    
    # Initialize task agent
    agent = TaskAgent(sensors, llm, memory, data_filter, context_analyzer)
    
    # Start sensors
    for name, sensor in sensors.items():
        if sensor and hasattr(sensor, 'start'):
            sensor.start()
            logger.info(f"Started {name} sensor")
    
    return agent, memory, sensors

@app.route('/', methods=['GET'])
def index():
    """Render the main chat interface."""
    try:
        logging.info("Rendering index page")
        all_messages = memory.get_all() if memory else []
        version_info = {
            'assistant': 'Local AI Assistant v0.1.0',
            'model': agent.llm.model_name if agent and agent.llm else 'Unknown model',
            'status': 'ready' if agent and agent.llm else 'not ready'
        }
        return render_template('chat.html', 
                             conversation=all_messages,
                             version=version_info)
    except Exception as e:
        logging.error(f"Error rendering index: {str(e)}", exc_info=True)
        return "Error loading chat interface", 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        return jsonify({
            'status': 'ok',
            'version': '0.1.0',
            'components': {
                'agent': bool(agent),
                'memory': bool(memory),
                'sensors': {name: bool(sensor) for name, sensor in sensors.items()}
            }
        })
    except Exception as e:
        logging.error(f"Health check failed: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    """Handle chat queries."""
    try:
        # Get query from either JSON or form data
        query = None
        if request.is_json:
            data = request.get_json()
            query = data.get('query', '').strip()
        elif request.content_type and 'multipart/form-data' in request.content_type:
            query = request.form.get('query', '').strip()
        elif request.form:
            query = request.form.get('query', '').strip()
        
        if not query:
            return jsonify({
                'error': True,
                'reply': 'Please enter a query'
            })
        
        if not agent or not agent.llm:
            return jsonify({
                'error': True,
                'reply': 'Error: Agent or LLM not initialized'
            })
        
        # Create a new event loop for this request
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Use the agent's LLM to generate response
            response = loop.run_until_complete(agent.handle_query(query))
            
            if not response:
                return jsonify({
                    'error': True,
                    'reply': 'Error: No response from LLM'
                })
            
            return jsonify({
                'error': False,
                'reply': response
            })
        finally:
            loop.close()
        
    except Exception as e:
        logging.error(f"Error in /ask route: {e}", exc_info=True)
        return jsonify({
            'error': True,
            'reply': f'Error: Could not process request - {str(e)}'
        })

@app.route('/events')
def server_sent_events():
    """Server-Sent Events endpoint for real-time updates."""
    def event_stream():
        last_message_count = len(memory.get_all()) if memory else 0
        
        while True:
            try:
                # Check for new messages
                current_count = len(memory.get_all()) if memory else 0
                if current_count > last_message_count:
                    last_message_count = current_count
                    yield f"data: {{'event': 'new_message', 'count': {current_count}}}\n\n"
                
                # Check sensor updates
                for name, sensor in sensors.items():
                    if hasattr(sensor, 'has_updates') and sensor.has_updates():
                        yield f"data: {{'event': 'context_update', 'source': '{name}'}}\n\n"
                
                time.sleep(2)  # Poll every 2 seconds
            except Exception as e:
                logging.error(f"Error in event stream: {str(e)}")
                time.sleep(5)  # Wait longer on error
    
    return Response(event_stream(), mimetype="text/event-stream")

def cleanup():
    """Cleanup resources before shutdown."""
    try:
        if agent:
            agent.stop()
        for sensor in sensors.values():
            if sensor and hasattr(sensor, 'stop'):
                sensor.stop()
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Load configuration
    config = load_config()
    
    try:
        # Initialize components
        logger.info("Initializing components...")
        agent, memory, sensors = initialize_components(config)
        
        # Start sensors
        logger.info("Starting sensors...")
        for name, sensor in sensors.items():
            if sensor:
                sensor.start()
        
        # Start the server
        logger.info("Starting Local AI Assistant server...")
        try:
            app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
        except Exception as e:
            logger.error(f"Error starting server: {e}", exc_info=True)
            raise
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        cleanup()
        sys.exit(1)