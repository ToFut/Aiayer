"""
Chat Server Module
Provides a Flask web interface for interacting with the AI assistant.
"""
import os
import sys
import time
import logging
import threading
from flask import Flask, request, jsonify, render_template, send_from_directory, Response

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Placeholders for global instances that will be set on startup
agent = None
memory = None
sensors = {}
server_start_time = time.time()

# Initialize Flask app with correct static and template paths
static_folder = os.path.join(os.path.dirname(__file__), 'static')
template_folder = os.path.join(os.path.dirname(__file__), 'templates')

app = Flask(__name__,
    static_folder=static_folder,
    static_url_path='/static',
    template_folder=template_folder
)

# Add request logging
@app.before_request
def log_request_info():
    logging.debug('Headers: %s', request.headers)
    logging.debug('Body: %s', request.get_data())

@app.after_request
def log_response_info(response):
    # Skip logging for static files
    if request.path.startswith('/static/'):
        return response
        
    try:
        logging.debug('Response: %s', response.get_data())
    except Exception as e:
        logging.debug('Could not log response data: %s', str(e))
    return response

@app.route('/', methods=['GET'])
def index():
    """Render the main chat interface."""
    try:
        logging.info("Rendering index page")
        all_messages = memory.get_all() if memory else []
        version_info = {
            'assistant': 'Local AI Assistant v0.1.0',
            'model': agent.llm.model_name if agent and agent.llm else 'Unknown model'
        }
        return render_template('chat.html', 
                             conversation=all_messages,
                             version=version_info)
    except Exception as e:
        logging.error(f"Error rendering index: {str(e)}", exc_info=True)
        return "Error loading chat interface", 500

@app.route('/ask', methods=['POST'])
def ask():
    """Handle chat queries."""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'response': '*(Please enter a query)*',
                'error': True
            })
        
        if not agent:
            return jsonify({
                'response': '*(Error: Agent not initialized)*',
                'error': True
            })
        
        try:
            # Set a timeout for the agent response
            response = agent.process_query(query, timeout=30)
            
            # Check if response is an error message
            if response.startswith('*(') and response.endswith(')*'):
                return jsonify({
                    'response': response,
                    'error': True
                })
            
            return jsonify({
                'response': response,
                'error': False
            })
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return jsonify({
                'response': '*(Error processing query. Please try again.)*',
                'error': True
            })
            
    except Exception as e:
        logger.error(f"Error in /ask route: {e}")
        return jsonify({
            'response': '*(Error: Could not process request)*',
            'error': True
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

def _get_system_status():
    """Generate a human-readable status report."""
    try:
        runtime = time.time() - server_start_time
        hours, remainder = divmod(runtime, 3600)
        minutes, seconds = divmod(remainder, 60)
        runtime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        
        status_lines = [
            "# System Status",
            f"- **Uptime**: {runtime_str}",
            f"- **Model**: {agent.llm.model_name if agent and agent.llm else 'Unknown'}",
            "- **Active Sensors**:"
        ]
        
        for name in sensors:
            status_lines.append(f"  - {name}")
        
        if memory:
            mem_stats = memory.get_summary()
            status_lines.append(f"- **Memory Usage**: {mem_stats.get('count', 0)} messages " +
                               f"({mem_stats.get('usage_percent', 0):.1f}% of capacity)")
        
        return "\n".join(status_lines)
    except Exception as e:
        logging.error(f"Error generating status: {str(e)}")
        return "Error generating status report"

def start_server(task_agent, mem=None, sensor_dict=None, host='127.0.0.1', port=5001, debug=False):
    """
    Start the Flask server with the provided components.
    """
    global agent, memory, sensors, server_start_time
    
    agent = task_agent
    memory = mem if mem else task_agent.memory
    sensors = sensor_dict if sensor_dict else task_agent.sensors
    server_start_time = time.time()
    
    # Configure logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Try different ports if the default is in use
    max_attempts = 5
    current_port = port
    
    for attempt in range(max_attempts):
        try:
            # Log server startup
            logging.info(f"Starting chat server on {host}:{current_port}")
            logging.info(f"Open http://{host}:{current_port} in your browser to interact with the assistant")
            
            # Run Flask app
            app.run(host=host, port=current_port, debug=debug, use_reloader=False)
            break
        except OSError as e:
            if "Address already in use" in str(e):
                logging.warning(f"Port {current_port} is in use, trying port {current_port + 1}")
                current_port += 1
                if attempt == max_attempts - 1:
                    logging.error("Could not find an available port. Please check your running processes.")
                    raise
            else:
                raise

# Direct execution - only for development/testing
if __name__ == '__main__':
    print("This module should be imported and started via main.py")
    print("For testing, we'll start with mock components...")
    
    # Mock components for testing
    from memory.memory import ConversationMemory
    
    class MockAgent:
        def __init__(self):
            self.llm = type('obj', (object,), {'model_name': 'mock-model'})
        
        def handle_query(self, query):
            return f"Mock response to: {query}"
    
    class MockSensor:
        def __init__(self, name):
            self.name = name
            self.active_app = "MockApp"
            self.active_window_title = "Mock Window"
    
    # Create instances
    mock_memory = ConversationMemory()
    mock_agent = MockAgent()
    mock_sensors = {
        "screen": MockSensor("screen"),
        "process": MockSensor("process")
    }
    
    # Start server
    start_server(mock_agent, mock_memory, mock_sensors, debug=True)