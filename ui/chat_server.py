"""
Chat Server Module
Provides a Flask web interface for interacting with the AI assistant.
"""
import os
import sys
import time
import logging
import threading
import asyncio
from flask import Flask, request, jsonify, render_template, send_from_directory, Response
from flask_cors import CORS

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Initialize Flask app with correct static and template paths
static_folder = os.path.join(os.path.dirname(__file__), 'static')
template_folder = os.path.join(os.path.dirname(__file__), 'templates')

app = Flask(__name__,
    static_folder=static_folder,
    static_url_path='/static',
    template_folder=template_folder
)

# Enable CORS
CORS(app)

# Placeholders for global instances that will be set on startup
app.agent = None
app.memory = None
app.sensors = {}
server_start_time = time.time()

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
        all_messages = app.memory.get_all() if app.memory else []
        version_info = {
            'assistant': 'Local AI Assistant v0.1.0',
            'model': app.agent.llm.model_name if app.agent and app.agent.llm else 'Unknown model',
            'status': 'ready' if app.agent and app.agent.llm else 'not ready'
        }
        return render_template('chat.html', 
                             conversation=all_messages,
                             version=version_info)
    except Exception as e:
        logging.error(f"Error rendering index: {str(e)}", exc_info=True)
        return "Error loading chat interface", 500

@app.route('/ask', methods=['POST'])
async def ask():
    """Handle incoming chat requests."""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({
                'error': True,
                'reply': 'Please enter a query'
            })
        
        # Process query through task agent
        response = await app.agent.handle_query(query)
        
        return jsonify({
            'error': False,
            'reply': response
        })
        
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}", exc_info=True)
        return jsonify({
            'error': True,
            'reply': f"Error processing query: {str(e)}"
        })

@app.route('/events')
def server_sent_events():
    """Server-Sent Events endpoint for real-time updates."""
    def event_stream():
        last_message_count = len(app.memory.get_all()) if app.memory else 0
        
        while True:
            try:
                # Check for new messages
                current_count = len(app.memory.get_all()) if app.memory else 0
                if current_count > last_message_count:
                    last_message_count = current_count
                    yield f"data: {{'event': 'new_message', 'count': {current_count}}}\n\n"
                
                # Check sensor updates
                for name, sensor in app.sensors.items():
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
            f"- **Model**: {app.agent.llm.model_name if app.agent and app.agent.llm else 'Unknown'}",
            "- **Active Sensors**:"
        ]
        
        for name in app.sensors:
            status_lines.append(f"  - {name}")
        
        if app.memory:
            mem_stats = app.memory.get_summary()
            status_lines.append(f"- **Memory Usage**: {mem_stats.get('count', 0)} messages " +
                               f"({mem_stats.get('usage_percent', 0):.1f}% of capacity)")
        
        return "\n".join(status_lines)
    except Exception as e:
        logging.error(f"Error generating status: {str(e)}")
        return "Error generating status report"

def start_server(agent_instance, memory_instance, sensors_instance, port=5002):
    """Start the chat server."""
    app.agent = agent_instance
    app.memory = memory_instance
    app.sensors = sensors_instance
    
    app.run(host='127.0.0.1', port=port, debug=True)

# Direct execution - only for development/testing
if __name__ == '__main__':
    print("This module should be imported and started via main.py")
    print("For testing, we'll start with mock components...")
    
    # Mock components for testing
    from memory.memory import ConversationMemory
    
    class MockAgent:
        def __init__(self):
            self.llm = type('obj', (object,), {'model_name': 'mock-model'})
            self.context_analyzer = MockContextAnalyzer()
        
        async def handle_query(self, query):
            # Simulate context analysis
            context_analysis = await self.context_analyzer.analyze_context()
            
            # Format response with context
            response = f"""
Context Analysis:
- Current Activity: {context_analysis.current_activity}
- Context Summary: {context_analysis.context_summary}
- Potential Needs: {', '.join(context_analysis.potential_needs)}
- Attention Level: {context_analysis.attention_level}

Response:
This is a mock response to: {query}
"""
            return response

    class MockContextAnalyzer:
        async def analyze_context(self):
            return type('obj', (object,), {
                'current_activity': 'Testing the chat interface',
                'context_summary': 'User is interacting with the mock chat interface',
                'potential_needs': ['Testing', 'Debugging', 'Development'],
                'attention_level': 'high',
                'confidence_score': 0.95,
                'semantic_understanding': {
                    'task_purpose': 'Testing the chat interface',
                    'workflow': 'User interaction testing',
                    'challenges': ['Async handling', 'Mock responses'],
                    'related_concepts': ['Testing', 'Development'],
                    'implicit_goals': ['Verify functionality']
                }
            })

    class MockSensor:
        def __init__(self, name):
            self.name = name
            self.active_app = "MockApp"
            self.active_window_title = "Mock Window"
            self.has_updates = lambda: True

    # Create instances
    mock_memory = ConversationMemory()
    mock_agent = MockAgent()
    mock_sensors = {
        "screen": MockSensor("screen"),
        "process": MockSensor("process"),
        "file": MockSensor("file")
    }
    
    # Start server
    start_server(mock_agent, mock_memory, mock_sensors, port=5002)