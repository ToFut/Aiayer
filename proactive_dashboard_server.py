#!/usr/bin/env python3
"""
Proactive Dashboard Server
Automatically identifies and displays potential tasks from UI analysis
"""

import asyncio
import json
import logging
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import threading
import time
from pathlib import Path
import sys

# Add Aiayer to path
sys.path.insert(0, str(Path(__file__).parent))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'proactive_dashboard_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
enhanced_system = None
analysis_thread = None
is_running = False

class ProactiveDashboard:
    """Manages proactive task identification and display"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.current_analysis = {}
        self.proactive_tasks = []
        self.recent_executions = []
        self.system_stats = {}
        
    async def initialize(self):
        """Initialize the proactive dashboard"""
        try:
            from integration.enhanced_complete_system import initialize_enhanced_system
            await initialize_enhanced_system()
            
            from integration.enhanced_complete_system import enhanced_system
            global enhanced_system
            enhanced_system = enhanced_system
            
            self.logger.info("Proactive Dashboard initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize proactive dashboard: {e}")
    
    async def start_continuous_analysis(self):
        """Start continuous UI analysis and task identification"""
        global is_running
        is_running = True
        
        while is_running:
            try:
                # Perform UI analysis and get proactive tasks
                analysis = await enhanced_system.understand_ui_and_suggest_tasks()
                
                # Update current state
                self.current_analysis = analysis
                self.proactive_tasks = analysis.get('proactive_tasks', [])
                self.system_stats = enhanced_system.get_system_stats()
                
                # Get recent executions
                if enhanced_system.memory_manager:
                    self.recent_executions = await enhanced_system.memory_manager.get_recent_executions(limit=5)
                
                # Emit updates to connected clients
                await self._emit_updates()
                
                # Wait before next analysis
                await asyncio.sleep(5)  # Analyze every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in continuous analysis: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _emit_updates(self):
        """Emit updates to connected clients"""
        try:
            dashboard_data = {
                'current_ui': self.current_analysis.get('ui_state', {}),
                'proactive_tasks': self._format_tasks_for_display(),
                'recent_executions': self.recent_executions,
                'system_stats': self.system_stats,
                'last_analysis': self.current_analysis.get('timestamp', 0),
                'timestamp': time.time()
            }
            
            # Emit to all connected clients
            socketio.emit('dashboard_update', dashboard_data)
            
        except Exception as e:
            self.logger.error(f"Error emitting updates: {e}")
    
    def _format_tasks_for_display(self):
        """Format tasks for frontend display"""
        formatted_tasks = []
        
        for task in self.proactive_tasks:
            formatted_task = {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'action_type': task.action_type,
                'confidence': task.confidence,
                'priority': task.priority,
                'estimated_time': task.estimated_time,
                'category': task.category,
                'icon': task.icon,
                'status': 'suggested'
            }
            formatted_tasks.append(formatted_task)
        
        return formatted_tasks
    
    async def execute_task(self, task_id: str):
        """Execute a proactive task"""
        try:
            # Find the task
            task = None
            for t in self.proactive_tasks:
                if t.id == task_id:
                    task = t
                    break
            
            if task:
                # Execute the task
                result = await enhanced_system.execute_proactive_task(task)
                
                # Update task status
                task.status = 'executed'
                
                # Emit execution result
                socketio.emit('task_executed', {
                    'task_id': task_id,
                    'result': result,
                    'timestamp': time.time()
                })
                
                return result
            else:
                return {'success': False, 'error': 'Task not found'}
                
        except Exception as e:
            self.logger.error(f"Error executing task: {e}")
            return {'success': False, 'error': str(e)}

# Global dashboard instance
dashboard = ProactiveDashboard()

@app.route('/')
def index():
    """Serve the proactive dashboard"""
    return render_template('proactive_dashboard.html')

@app.route('/api/analysis')
def get_analysis():
    """Get current analysis data"""
    return jsonify({
        'current_ui': dashboard.current_analysis.get('ui_state', {}),
        'proactive_tasks': dashboard._format_tasks_for_display(),
        'recent_executions': dashboard.recent_executions,
        'system_stats': dashboard.system_stats,
        'last_analysis': dashboard.current_analysis.get('timestamp', 0)
    })

@app.route('/api/execute_task', methods=['POST'])
def execute_task():
    """Execute a proactive task"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        
        if not task_id:
            return jsonify({'success': False, 'error': 'Task ID required'})
        
        # Run task execution in async context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(dashboard.execute_task(task_id))
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/start_analysis')
def start_analysis():
    """Start continuous analysis"""
    global analysis_thread, is_running
    
    if not is_running:
        is_running = True
        analysis_thread = threading.Thread(target=run_continuous_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()
        
        return jsonify({'success': True, 'message': 'Analysis started'})
    else:
        return jsonify({'success': False, 'message': 'Analysis already running'})

@app.route('/api/stop_analysis')
def stop_analysis():
    """Stop continuous analysis"""
    global is_running
    
    is_running = False
    return jsonify({'success': True, 'message': 'Analysis stopped'})

def run_continuous_analysis():
    """Run continuous analysis in background thread"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(dashboard.start_continuous_analysis())
    loop.close()

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {request.sid}")

@socketio.on('request_analysis')
def handle_analysis_request():
    """Handle manual analysis request"""
    try:
        # Trigger immediate analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        analysis = loop.run_until_complete(enhanced_system.understand_ui_and_suggest_tasks())
        loop.close()
        
        emit('analysis_result', analysis)
        
    except Exception as e:
        emit('analysis_error', {'error': str(e)})

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize dashboard
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(dashboard.initialize())
    loop.close()
    
    print("🚀 Proactive Dashboard Server starting...")
    print("📊 Dashboard available at: http://localhost:5003")
    print("🔍 Automatic task identification enabled")
    
    # Start the server
    socketio.run(app, host='0.0.0.0', port=5003, debug=True) 