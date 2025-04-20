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
    """Handle incoming chat requests with improved error recovery and logging."""
    # Generate transaction ID for tracking this request through the system
    transaction_id = f"web_{int(time.time())}"
    logging.info(f"[TRANSACTION:{transaction_id}] Received chat request")
    
    try:
        # Log request details
        data = request.get_json()
        logging.info(f"[TRANSACTION:{transaction_id}] Request data: {data}")
        
        query = data.get('query', '')
        
        if not query:
            logging.warning(f"[TRANSACTION:{transaction_id}] Empty query received")
            return jsonify({
                'error': True,
                'transaction_id': transaction_id,
                'reply': 'Please enter a query',
                'status': 'error'
            })
        
        # Send immediate response to prevent timeout
        def generate():
            yield json.dumps({
                'error': False,
                'transaction_id': transaction_id,
                'status': 'processing',
                'reply': "Processing your request..."
            })
            
        # Log that we're starting to process
        logging.info(f"[TRANSACTION:{transaction_id}] Processing query: {query}")
        
        # Process query through task agent with timeout protection
        try:
            # Use a timeout to prevent hanging
            response = await asyncio.wait_for(
                app.agent.handle_query(query), 
                timeout=30.0  # 30 second timeout for overall processing
            )
            
            logging.info(f"[TRANSACTION:{transaction_id}] Got response: {response[:100]}...")
            
            return jsonify({
                'error': False,
                'transaction_id': transaction_id,
                'status': 'complete',
                'reply': response
            })
            
        except asyncio.TimeoutError:
            # Handle timeout by returning a specific message
            logging.error(f"[TRANSACTION:{transaction_id}] Request timed out")
            return jsonify({
                'error': True,
                'transaction_id': transaction_id,
                'status': 'timeout',
                'reply': "The request timed out. Please try again with a simpler question."
            })
        
    except json.JSONDecodeError:
        # Handle malformed JSON
        logging.error(f"[TRANSACTION:{transaction_id}] Malformed JSON in request")
        return jsonify({
            'error': True,
            'transaction_id': transaction_id,
            'status': 'error',
            'reply': "Invalid JSON format in request."
        })
        
    except Exception as e:
        # Log the full exception for debugging
        logging.error(f"[TRANSACTION:{transaction_id}] Error processing query: {str(e)}", exc_info=True)
        
        # Return a helpful error message
        return jsonify({
            'error': True,
            'transaction_id': transaction_id,
            'status': 'error',
            'reply': f"Error processing your request. Please try again or check the logs for details. (Error: {str(e)})"
        })

@app.route('/events')
def server_sent_events():
    """Server-Sent Events endpoint for real-time updates with enhanced context sharing."""
    def event_stream():
        last_message_count = len(app.memory.get_all()) if app.memory else 0
        last_context_update = time.time()
        last_sensor_check = {}
        context_check_interval = 5  # Check for context updates every 5 seconds
        
        while True:
            try:
                # Check for new messages
                current_count = len(app.memory.get_all()) if app.memory else 0
                if current_count > last_message_count:
                    last_message_count = current_count
                    # Send new message event with more details
                    last_message = app.memory.get_recent(count=1)[0] if app.memory else None
                    if last_message:
                        yield f"data: {{\"event\": \"new_message\", \"count\": {current_count}, \"role\": \"{last_message.get('role', 'unknown')}\", \"timestamp\": {time.time()}}}\n\n"
                    else:
                        yield f"data: {{\"event\": \"new_message\", \"count\": {current_count}, \"timestamp\": {time.time()}}}\n\n"
                
                # Check for context updates periodically
                current_time = time.time()
                if current_time - last_context_update > context_check_interval:
                    last_context_update = current_time
                    
                    # Get context from agent if available
                    if app.agent and hasattr(app.agent, 'get_current_context'):
                        try:
                            # Use asyncio.run to handle coroutine if needed
                            import asyncio
                            context = asyncio.run(app.agent.get_current_context())
                            
                            if context:
                                # Send rich context update with actual content
                                context_data = {
                                    "event": "context_update",
                                    "timestamp": time.time(),
                                    "activity": context.current_activity[:100] if hasattr(context, 'current_activity') else "Unknown",
                                    "summary": context.context_summary[:150] if hasattr(context, 'context_summary') else "",
                                    "needs": context.potential_needs[:3] if hasattr(context, 'potential_needs') else [],
                                    "attention": context.attention_level if hasattr(context, 'attention_level') else "medium"
                                }
                                
                                # Add semantic understanding if available
                                if hasattr(context, 'semantic_understanding') and context.semantic_understanding:
                                    semantic = context.semantic_understanding
                                    context_data["semantic"] = {
                                        "purpose": semantic.get('purpose', '')[:100],
                                        "workflow": semantic.get('workflow', '')[:100],
                                        "emotional_state": semantic.get('emotional_state', '')
                                    }
                                
                                # Convert to JSON and emit
                                import json
                                yield f"data: {json.dumps(context_data)}\n\n"
                        except Exception as context_err:
                            logging.error(f"Error getting context: {context_err}")
                
                # Check sensor updates with individual tracking
                for name, sensor in app.sensors.items():
                    # Initialize if not seen before
                    if name not in last_sensor_check:
                        last_sensor_check[name] = 0
                    
                    # Check if this sensor has updates (respecting individual sensor rates)
                    if hasattr(sensor, 'has_updates') and sensor.has_updates():
                        # Only send update if sufficient time has passed for this sensor
                        if current_time - last_sensor_check[name] > 3:  # At most every 3 seconds per sensor
                            last_sensor_check[name] = current_time
                            
                            # Get sensor data if available
                            sensor_data = None
                            if hasattr(sensor, 'get_data'):
                                try:
                                    sensor_data = sensor.get_data()
                                except:
                                    pass
                            
                            # Create event with sensor data if available
                            if sensor_data and isinstance(sensor_data, dict):
                                # Include summary of sensor data in event
                                import json
                                event_data = {
                                    "event": "sensor_update", 
                                    "source": name,
                                    "timestamp": time.time(),
                                    "summary": self._summarize_sensor_data(sensor_data, name)
                                }
                                yield f"data: {json.dumps(event_data)}\n\n"
                            else:
                                # Simple event without data
                                yield f"data: {{\"event\": \"sensor_update\", \"source\": \"{name}\", \"timestamp\": {time.time()}}}\n\n"
                
                time.sleep(1)  # Poll more frequently (1 second)
            except Exception as e:
                logging.error(f"Error in event stream: {str(e)}")
                time.sleep(5)  # Wait longer on error
    
    def _summarize_sensor_data(self, data, sensor_name):
        """Generate a brief summary of sensor data for the event stream."""
        summary = {}
        
        try:
            # Extract relevant fields based on sensor type
            if sensor_name == "screen":
                if "data" in data and isinstance(data["data"], dict):
                    screen_data = data["data"]
                    summary["has_images"] = screen_data.get("has_images", False)
                    summary["has_videos"] = screen_data.get("has_videos", False)
                    # Include limited text preview if available
                    if "text" in screen_data and isinstance(screen_data["text"], str):
                        text = screen_data["text"]
                        if len(text) > 100:
                            summary["text_preview"] = text[:100] + "..."
                        else:
                            summary["text_preview"] = text
            
            elif sensor_name == "process":
                if "active_app" in data:
                    summary["active_app"] = data["active_app"]
                if "window_title" in data:
                    summary["window_title"] = data["window_title"]
            
            elif sensor_name == "browser":
                if "current_url" in data:
                    summary["current_url"] = data["current_url"]
                if "current_title" in data:
                    summary["current_title"] = data["current_title"]
                if "tab_count" in data:
                    summary["tab_count"] = data["tab_count"]
            
            # Add timestamp if available
            if "timestamp" in data:
                summary["timestamp"] = data["timestamp"]
        
        except Exception as e:
            logging.error(f"Error summarizing sensor data: {e}")
            return {"error": "Failed to summarize sensor data"}
        
        return summary
    
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