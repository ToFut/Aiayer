#!/usr/bin/env python3
"""
Comprehensive Overlay-Backend Connection Test
Identifies all connection issues between Tauri overlay and backend services
"""
import asyncio
import json
import logging
import os
import sys
import subprocess
import socket
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import websockets
import threading
import signal
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class ConnectionDiagnostic:
    """Comprehensive connection diagnostic tool."""
    
    def __init__(self):
        self.test_results = {
            'port_availability': {},
            'server_processes': {},
            'websocket_connections': {},
            'message_flow': {},
            'backend_responses': {},
            'errors': []
        }
        self.ports_to_check = [8765, 8766, 8767, 8768, 1421]
        self.servers_to_test = {
            'main_ws_server': 'ws://localhost:8765',
            'bridge_server': 'ws://localhost:8766', 
            'enhanced_bridge': 'ws://localhost:8767',
            'fallback_server': 'ws://localhost:8768'
        }
        self.test_messages = [
            {'type': 'register', 'payload': {'client_type': 'ui', 'capabilities': ['chat']}},
            {'type': 'user_interaction', 'payload': {'type': 'query', 'query': 'Hello, can you help me?'}},
            {'type': 'context_request', 'payload': {'timestamp': int(time.time())}},
            {'type': 'heartbeat', 'payload': {'timestamp': int(time.time())}}
        ]
        self.running_processes = []
        
    def run_full_diagnostic(self):
        """Run complete diagnostic test suite."""
        logger.info("🔍 Starting comprehensive overlay-backend connection diagnostic...")
        logger.info("=" * 80)
        
        # Test 1: Check port availability
        self.test_port_availability()
        
        # Test 2: Check server processes
        self.test_running_processes()
        
        # Test 3: Test WebSocket connections
        asyncio.run(self.test_websocket_connections())
        
        # Test 4: Test message flow
        asyncio.run(self.test_message_flow())
        
        # Test 5: Test backend responses
        asyncio.run(self.test_backend_responses())
        
        # Test 6: Check log files
        self.test_log_files()
        
        # Generate final report
        self.generate_report()
        
        return self.test_results
    
    def test_port_availability(self):
        """Test if required ports are available or in use."""
        logger.info("🔌 Testing port availability...")
        
        for port in self.ports_to_check:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    # Port is in use
                    self.test_results['port_availability'][port] = {
                        'status': 'in_use',
                        'process': self._get_process_using_port(port)
                    }
                    logger.info(f"  ✅ Port {port}: IN USE")
                else:
                    # Port is available
                    self.test_results['port_availability'][port] = {
                        'status': 'available',
                        'process': None
                    }
                    logger.warning(f"  ⚠️  Port {port}: AVAILABLE (no server running)")
                    
            except Exception as e:
                self.test_results['port_availability'][port] = {
                    'status': 'error',
                    'error': str(e)
                }
                logger.error(f"  ❌ Port {port}: ERROR - {e}")
    
    def _get_process_using_port(self, port: int) -> Optional[Dict[str, Any]]:
        """Get process information for a port."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    for conn in proc.connections():
                        if conn.laddr.port == port:
                            return {
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'cmdline': ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                            }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.debug(f"Error getting process for port {port}: {e}")
        return None
    
    def test_running_processes(self):
        """Test which server processes are running."""
        logger.info("🏃 Testing running server processes...")
        
        # Check for Python processes that might be our servers
        server_patterns = [
            'bridge_server',
            'enhanced_backend_server',
            'memory_service',
            'llm_service',
            'ws_server',
            'ollama'
        ]
        
        for pattern in server_patterns:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                    if pattern in cmdline.lower() or pattern in proc.info['name'].lower():
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline,
                            'status': proc.status()
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            self.test_results['server_processes'][pattern] = processes
            if processes:
                logger.info(f"  ✅ {pattern}: {len(processes)} process(es) running")
                for proc in processes:
                    logger.info(f"    PID {proc['pid']}: {proc['name']}")
            else:
                logger.warning(f"  ⚠️  {pattern}: No processes found")
    
    async def test_websocket_connections(self):
        """Test WebSocket connections to all servers."""
        logger.info("🌐 Testing WebSocket connections...")
        
        for server_name, url in self.servers_to_test.items():
            try:
                logger.info(f"  Testing {server_name} at {url}...")
                
                # Try to connect with timeout
                try:
                    async with websockets.connect(url, timeout=5) as websocket:
                        # Connection successful
                        self.test_results['websocket_connections'][server_name] = {
                            'status': 'success',
                            'url': url,
                            'error': None
                        }
                        logger.info(f"    ✅ {server_name}: Connected successfully")
                        
                        # Try to send a simple message
                        await websocket.send(json.dumps({'type': 'test', 'payload': {'test': True}}))
                        
                        # Wait for any response
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=2)
                            logger.info(f"    📨 {server_name}: Received response")
                        except asyncio.TimeoutError:
                            logger.info(f"    ⏰ {server_name}: No immediate response (normal)")
                        
                except asyncio.TimeoutError:
                    self.test_results['websocket_connections'][server_name] = {
                        'status': 'timeout',
                        'url': url,
                        'error': 'Connection timeout'
                    }
                    logger.warning(f"    ⏰ {server_name}: Connection timeout")
                
            except ConnectionRefusedError:
                self.test_results['websocket_connections'][server_name] = {
                    'status': 'refused',
                    'url': url,
                    'error': 'Connection refused - server not running'
                }
                logger.warning(f"    ❌ {server_name}: Connection refused (server not running)")
                
            except Exception as e:
                self.test_results['websocket_connections'][server_name] = {
                    'status': 'error',
                    'url': url,
                    'error': str(e)
                }
                logger.error(f"    ❌ {server_name}: Error - {e}")
    
    async def test_message_flow(self):
        """Test message flow between overlay and backend."""
        logger.info("💬 Testing message flow...")
        
        # Find a working server
        working_server = None
        working_url = None
        
        for server_name, connection_info in self.test_results['websocket_connections'].items():
            if connection_info['status'] == 'success':
                working_server = server_name
                working_url = connection_info['url']
                break
        
        if not working_server:
            logger.error("  ❌ No working WebSocket server found for message flow test")
            return
        
        logger.info(f"  Using {working_server} for message flow test...")
        
        try:
            async with websockets.connect(working_url, timeout=5) as websocket:
                # Test each message type
                for i, test_message in enumerate(self.test_messages):
                    message_type = test_message['type']
                    logger.info(f"    Testing message type: {message_type}")
                    
                    # Send message
                    await websocket.send(json.dumps(test_message))
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3)
                        response_data = json.loads(response)
                        
                        self.test_results['message_flow'][message_type] = {
                            'status': 'success',
                            'sent': test_message,
                            'received': response_data
                        }
                        logger.info(f"      ✅ {message_type}: Response received - {response_data.get('type', 'unknown')}")
                        
                    except asyncio.TimeoutError:
                        self.test_results['message_flow'][message_type] = {
                            'status': 'timeout',
                            'sent': test_message,
                            'received': None
                        }
                        logger.warning(f"      ⏰ {message_type}: No response within timeout")
                    
                    # Small delay between messages
                    await asyncio.sleep(0.5)
                    
        except Exception as e:
            logger.error(f"  ❌ Message flow test failed: {e}")
    
    async def test_backend_responses(self):
        """Test if backend provides meaningful responses."""
        logger.info("🤖 Testing backend AI responses...")
        
        # Find a working server
        working_server = None
        working_url = None
        
        for server_name, connection_info in self.test_results['websocket_connections'].items():
            if connection_info['status'] == 'success':
                working_server = server_name
                working_url = connection_info['url']
                break
        
        if not working_server:
            logger.error("  ❌ No working WebSocket server found for response test")
            return
        
        test_queries = [
            "Hello, can you help me?",
            "What can you do?",
            "Tell me about the current system context",
            "How are you today?"
        ]
        
        try:
            async with websockets.connect(working_url, timeout=5) as websocket:
                # First register as UI client
                registration_msg = {
                    'type': 'register',
                    'payload': {
                        'client_type': 'ui',
                        'version': '1.0.0',
                        'capabilities': ['chat', 'query']
                    }
                }
                await websocket.send(json.dumps(registration_msg))
                
                # Wait for registration confirmation
                try:
                    reg_response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    logger.info(f"    Registration response: {json.loads(reg_response).get('type')}")
                except asyncio.TimeoutError:
                    logger.warning("    No registration confirmation received")
                
                # Test each query
                for query in test_queries:
                    logger.info(f"    Testing query: '{query}'")
                    
                    query_msg = {
                        'type': 'user_interaction',
                        'payload': {
                            'type': 'query',
                            'query': query,
                            'timestamp': int(time.time())
                        }
                    }
                    
                    await websocket.send(json.dumps(query_msg))
                    
                    # Wait for AI response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=10)
                        response_data = json.loads(response)
                        
                        self.test_results['backend_responses'][query] = {
                            'status': 'success',
                            'response_type': response_data.get('type'),
                            'response_data': response_data,
                            'has_content': bool(response_data.get('payload', {}).get('response', '').strip())
                        }
                        
                        if response_data.get('type') == 'query_response':
                            content = response_data.get('payload', {}).get('response', '')
                            if content and len(content.strip()) > 10:
                                logger.info(f"      ✅ Query: Meaningful response received ({len(content)} chars)")
                            else:
                                logger.warning(f"      ⚠️  Query: Response too short or empty")
                        else:
                            logger.info(f"      📨 Query: Received {response_data.get('type')} response")
                        
                    except asyncio.TimeoutError:
                        self.test_results['backend_responses'][query] = {
                            'status': 'timeout',
                            'response_type': None,
                            'response_data': None,
                            'has_content': False
                        }
                        logger.warning(f"      ⏰ Query: No response within 10 seconds")
                    
                    # Delay between queries
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"  ❌ Backend response test failed: {e}")
    
    def test_log_files(self):
        """Check log files for errors."""
        logger.info("📋 Checking log files...")
        
        log_directories = [
            'logs',
            'logs/bridge',
            'logs/memory',
            'logs/llm',
            'overlay/logs',
            'overlay/logs/bridge',
            'overlay/logs/memory'
        ]
        
        log_files_found = []
        error_count = 0
        
        for log_dir in log_directories:
            if os.path.exists(log_dir):
                for filename in os.listdir(log_dir):
                    if filename.endswith('.log'):
                        log_path = os.path.join(log_dir, filename)
                        log_files_found.append(log_path)
                        
                        # Check last 50 lines for errors
                        try:
                            with open(log_path, 'r') as f:
                                lines = f.readlines()
                                recent_lines = lines[-50:] if len(lines) > 50 else lines
                                
                                for line in recent_lines:
                                    if 'ERROR' in line or 'CRITICAL' in line:
                                        error_count += 1
                                        self.test_results['errors'].append({
                                            'file': log_path,
                                            'line': line.strip(),
                                            'timestamp': datetime.now().isoformat()
                                        })
                        except Exception as e:
                            logger.debug(f"Error reading log file {log_path}: {e}")
        
        logger.info(f"  📁 Found {len(log_files_found)} log files")
        if error_count > 0:
            logger.warning(f"  ⚠️  Found {error_count} recent errors in logs")
        else:
            logger.info(f"  ✅ No recent errors found in logs")
    
    def generate_report(self):
        """Generate comprehensive diagnostic report."""
        logger.info("📊 Generating diagnostic report...")
        logger.info("=" * 80)
        
        # Port Status Summary
        logger.info("🔌 PORT STATUS:")
        for port, info in self.test_results['port_availability'].items():
            status_emoji = "✅" if info['status'] == 'in_use' else "❌"
            logger.info(f"  {status_emoji} Port {port}: {info['status'].upper()}")
            if info.get('process'):
                logger.info(f"    Process: {info['process']['name']} (PID: {info['process']['pid']})")
        
        # Connection Status Summary
        logger.info("\n🌐 CONNECTION STATUS:")
        working_connections = 0
        for server, info in self.test_results['websocket_connections'].items():
            status_emoji = "✅" if info['status'] == 'success' else "❌"
            logger.info(f"  {status_emoji} {server}: {info['status'].upper()}")
            if info['status'] == 'success':
                working_connections += 1
            elif info.get('error'):
                logger.info(f"    Error: {info['error']}")
        
        # Message Flow Summary
        logger.info("\n💬 MESSAGE FLOW:")
        successful_messages = 0
        for msg_type, info in self.test_results['message_flow'].items():
            status_emoji = "✅" if info['status'] == 'success' else "❌"
            logger.info(f"  {status_emoji} {msg_type}: {info['status'].upper()}")
            if info['status'] == 'success':
                successful_messages += 1
        
        # Backend Response Summary
        logger.info("\n🤖 BACKEND RESPONSES:")
        meaningful_responses = 0
        for query, info in self.test_results['backend_responses'].items():
            if info['status'] == 'success' and info['has_content']:
                meaningful_responses += 1
                logger.info(f"  ✅ Query successful: {info['response_type']}")
            elif info['status'] == 'success':
                logger.info(f"  ⚠️  Query responded but no content: {info['response_type']}")
            else:
                logger.info(f"  ❌ Query failed: {info['status']}")
        
        # Overall Assessment
        logger.info("\n🎯 OVERALL ASSESSMENT:")
        
        issues = []
        if working_connections == 0:
            issues.append("No working WebSocket connections")
        if successful_messages == 0:
            issues.append("Message flow not working")
        if meaningful_responses == 0:
            issues.append("Backend not providing meaningful responses")
        if len(self.test_results['errors']) > 10:
            issues.append(f"High error count in logs ({len(self.test_results['errors'])})")
        
        if not issues:
            logger.info("  ✅ SYSTEM HEALTHY: All tests passed!")
        else:
            logger.error("  ❌ ISSUES FOUND:")
            for issue in issues:
                logger.error(f"    • {issue}")
        
        # Recommendations
        logger.info("\n💡 RECOMMENDATIONS:")
        if working_connections == 0:
            logger.info("  1. Start the WebSocket servers:")
            logger.info("     ./run_enhanced_screen_memory_system.sh")
        if successful_messages == 0 and working_connections > 0:
            logger.info("  2. Check message handler registration in backend")
        if meaningful_responses == 0:
            logger.info("  3. Verify LLM service is running and configured")
            logger.info("     Check if Ollama is running: ollama list")
        
        logger.info("=" * 80)
        
        # Save report to file
        report_path = 'overlay_backend_diagnostic_report.json'
        try:
            with open(report_path, 'w') as f:
                json.dump(self.test_results, f, indent=2, default=str)
            logger.info(f"📄 Detailed report saved to: {report_path}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

def main():
    """Main diagnostic function."""
    print("🔍 OVERLAY-BACKEND CONNECTION DIAGNOSTIC")
    print("========================================")
    
    diagnostic = ConnectionDiagnostic()
    results = diagnostic.run_full_diagnostic()
    
    return 0 if not results.get('errors') else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Diagnostic interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        sys.exit(1)