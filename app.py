"""
Flask application for Local Assistant Dashboard
"""
from flask import Flask, render_template, jsonify, request
import psutil
import os
import subprocess
import json
from datetime import datetime
import threading
import logging
import time
import signal
import atexit
import yaml
import argparse
from llm.model import LocalLLM
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from YAML file."""
    try:
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load config file: {e}")
        return {}

class FlaskApp:
    def __init__(self):
        self.app = Flask(__name__, static_folder='static', static_url_path='/static')
        self.config = load_config()
        self.system_state = {
            'running': False,
            'components': {
                'ai-sensor': {'running': False, 'health': 'unknown'},
                'file-sensor': {'running': False, 'health': 'unknown'},
                'process-sensor': {'running': False, 'health': 'unknown'},
                'llm-model': {'running': False, 'health': 'unknown'}
            },
            'start_time': datetime.now(),
            'last_error': None
        }
        self.monitor_thread = None
        self.should_run = True
        
        # Initialize LLM
        try:
            self.llm = LocalLLM(
                model_name=self.config.get('llm', {}).get('model_name', 'mistral'),
                host=self.config.get('llm', {}).get('host', 'localhost'),
                port=self.config.get('llm', {}).get('port', 11434)
            )
            if self.llm.start():
                logger.info("LLM initialized successfully")
                self.system_state['components']['llm-model']['running'] = True
                self.system_state['components']['llm-model']['health'] = 'healthy'
            else:
                logger.error("Failed to initialize LLM")
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
        
        # Register routes
        self.register_routes()
        
        # Register cleanup
        atexit.register(self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        signal.signal(signal.SIGINT, self.cleanup)
        
        logger.info("Flask application initialized")
        
    def register_routes(self):
        @self.app.route('/')
        def index():
            """Render the dashboard."""
            return render_template('index.html')
            
        @self.app.route('/static/<path:filename>')
        def serve_static(filename):
            """Serve static files."""
            return self.app.send_static_file(filename)
            
        @self.app.route('/api/system/status')
        def system_status():
            """Get current system status."""
            try:
                stats = self.get_system_stats()
                return jsonify({
                    'status': 'running' if self.system_state['running'] else 'stopped',
                    'uptime': (datetime.now() - self.system_state['start_time']).total_seconds(),
                    'last_error': self.system_state['last_error'],
                    'components': self.system_state['components'],
                    **stats
                })
            except Exception as e:
                logger.error(f"Error getting system status: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
                
        @self.app.route('/api/system-health')
        def system_health():
            """Get system health metrics."""
            try:
                stats = self.get_system_stats()
                return jsonify({
                    'cpu': stats['cpu_percent'],
                    'memory': stats['memory_percent'],
                    'disk': stats['disk_percent'],
                    'health': 'GOOD' if self.system_state['running'] else 'ERROR'
                })
            except Exception as e:
                logger.error(f"Error getting system health: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
                
        @self.app.route('/api/system/start', methods=['POST'])
        def start_system():
            """Start all components."""
            try:
                if not self.system_state['running']:
                    for component in self.system_state['components']:
                        self.start_component(component)
                    self.system_state['running'] = True
                    self.system_state['start_time'] = datetime.now()
                return jsonify({'status': 'success'})
            except Exception as e:
                logger.error(f"Error starting system: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
                
        @self.app.route('/api/system/stop', methods=['POST'])
        def stop_system():
            """Stop all components."""
            try:
                if self.system_state['running']:
                    for component in self.system_state['components']:
                        self.stop_component(component)
                    self.system_state['running'] = False
                return jsonify({'status': 'success'})
            except Exception as e:
                logger.error(f"Error stopping system: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
                
        @self.app.route('/api/component/<component>/logs')
        def component_logs(component):
            """Get logs for a specific component."""
            try:
                log_file = f"logs/{component}.log"
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        return jsonify({'logs': f.read()})
                return jsonify({'logs': 'No logs available'})
            except Exception as e:
                logger.error(f"Error getting component logs: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
                
        @self.app.route('/api/ai-sensor/stats')
        def ai_sensor_stats():
            """Get AI sensor statistics."""
            try:
                return jsonify({
                    'events': 0,  # TODO: Implement actual event counting
                    'predictions': 0,  # TODO: Implement actual prediction counting
                    'insights': 0  # TODO: Implement actual insight counting
                })
            except Exception as e:
                logger.error(f"Error getting AI sensor stats: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
                
        @self.app.route('/api/recent-events')
        def recent_events():
            """Get recent system events."""
            try:
                return jsonify({
                    'events': []  # TODO: Implement actual event tracking
                })
            except Exception as e:
                logger.error(f"Error getting recent events: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
                
        @self.app.route('/api/resource-predictions')
        def resource_predictions():
            """Get resource usage predictions."""
            try:
                stats = self.get_system_stats()
                return jsonify({
                    'cpu': stats['cpu_percent'],
                    'memory': stats['memory_percent']
                })
            except Exception as e:
                logger.error(f"Error getting resource predictions: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
                
        @self.app.route('/api/system-insights')
        def system_insights():
            """Get system insights."""
            try:
                return jsonify({
                    'insights': []  # TODO: Implement actual insight generation
                })
            except Exception as e:
                logger.error(f"Error getting system insights: {e}")
                return jsonify({'status': 'error', 'message': str(e)}), 500
                
        @self.app.route('/api/chat', methods=['POST'])
        def chat():
            """Handle chat messages with the LLM."""
            try:
                data = request.get_json()
                if not data or 'message' not in data:
                    return jsonify({'error': 'No message provided'}), 400
                    
                message = data['message']
                logger.info(f"Received chat message: {message}")
                
                # Direct Ollama API call for more reliable communication
                try:
                    response = requests.post(
                        f"http://localhost:11434/api/generate",
                        json={
                            "model": "mistral",
                            "prompt": message,
                            "stream": False
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "response" in result:
                            logger.info(f"Generated response: {result['response'][:100]}...")
                            return jsonify({'response': result['response']})
                    
                    logger.error(f"Error from Ollama API: {response.text}")
                    return jsonify({'error': 'Failed to generate response'}), 500
                    
                except requests.exceptions.Timeout:
                    logger.error("Request to Ollama timed out")
                    return jsonify({'error': 'Request timed out'}), 504
                except requests.exceptions.ConnectionError:
                    logger.error("Could not connect to Ollama")
                    return jsonify({'error': 'Could not connect to LLM service'}), 503
                    
            except Exception as e:
                logger.error(f"Error in chat endpoint: {e}")
                return jsonify({'error': str(e)}), 500
                
    def get_system_stats(self):
        """Get current system statistics."""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'process_count': len(psutil.pids())
            }
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {}
            
    def monitor_components(self):
        """Monitor component health in a separate thread."""
        while self.should_run:
            try:
                for component in self.system_state['components']:
                    self.check_component_health(component)
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error in monitor thread: {e}")
                time.sleep(30)  # Wait longer on error
                
    def check_component_health(self, component):
        """Check health of a specific component."""
        try:
            # Check if component process is running
            process_name = f"python -m {component.replace('-', '_')}"
            running = False
            for proc in psutil.process_iter(['cmdline']):
                if proc.info['cmdline'] and process_name in ' '.join(proc.info['cmdline']):
                    running = True
                    break
                    
            self.system_state['components'][component]['running'] = running
            self.system_state['components'][component]['health'] = 'healthy' if running else 'stopped'
        except Exception as e:
            logger.error(f"Error checking component health: {e}")
            self.system_state['components'][component]['health'] = 'error'
            
    def cleanup(self, *args):
        """Cleanup resources on shutdown."""
        self.should_run = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        if hasattr(self, 'llm'):
            self.llm.stop()
        logger.info("Application shutdown complete")
        
    def run(self, host='0.0.0.0', port=None, debug=False):
        """Run the Flask application."""
        # Start monitor thread
        self.monitor_thread = threading.Thread(target=self.monitor_components)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Run Flask app
        self.app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the Local Assistant Dashboard')
    parser.add_argument('--port', type=int, default=5001, help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    args = parser.parse_args()
    
    # Create and run application
    app_instance = FlaskApp()
    app_instance.run(host=args.host, port=args.port, debug=args.debug) 