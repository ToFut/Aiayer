#!/usr/bin/env python3
"""
Comprehensive SensAI System Test
Tests all major components: RPA_AVEN, AIAYER backend, LLM, sensors, memory, automation
"""

import asyncio
import json
import logging
import os
import sys
import time
import websockets
import requests
import psutil
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveSystemTest:
    """Comprehensive test suite for SensAI system"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
        
        # System endpoints
        self.endpoints = {
            'backend_ws': 'ws://localhost:8767/ws',
            'backend_http': 'http://localhost:8787/status',
            'do_button_ws': 'ws://localhost:8765',
            'llm_api': 'http://localhost:11434/api/tags',
            'rpa_aven': 'http://localhost:8080'  # RPA_AVEN typically runs on 8080
        }
        
        # Test categories
        self.test_categories = [
            'system_processes',
            'network_ports', 
            'llm_service',
            'backend_communication',
            'rpa_automation',
            'sensor_systems',
            'memory_system',
            'automation_capabilities'
        ]
    
    def run_all_tests(self):
        """Run all system tests"""
        print("🚀 COMPREHENSIVE SENSAI SYSTEM TEST")
        print("=" * 60)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all test categories
        for category in self.test_categories:
            print(f"🔍 Testing: {category.replace('_', ' ').title()}")
            test_method = getattr(self, f'test_{category}')
            try:
                result = test_method()
                self.test_results[category] = result
                self._print_test_result(category, result)
            except Exception as e:
                error_result = {
                    'status': 'error',
                    'message': str(e),
                    'details': None
                }
                self.test_results[category] = error_result
                self._print_test_result(category, error_result)
            print()
        
        # Generate final report
        self._generate_final_report()
    
    def test_system_processes(self) -> Dict[str, Any]:
        """Test if all required system processes are running"""
        required_processes = [
            'enhanced_enterprise_backend_with_context.py',
            'direct_coordinate_automation.py',
            'enhanced_fixed_process_sensor.py',
            'total_screen_analyzer.py',
            'memory_aware_suggestion_monitor.py',
            'smart_memory_feeder.py'
        ]
        
        running_processes = []
        missing_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                for required in required_processes:
                    if required in cmdline:
                        running_processes.append({
                            'name': required,
                            'pid': proc.info['pid'],
                            'memory_mb': proc.memory_info().rss / 1024 / 1024
                        })
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Check for missing processes
        running_names = [p['name'] for p in running_processes]
        for required in required_processes:
            if required not in running_names:
                missing_processes.append(required)
        
        return {
            'status': 'pass' if not missing_processes else 'fail',
            'running': running_processes,
            'missing': missing_processes,
            'total_running': len(running_processes),
            'total_required': len(required_processes)
        }
    
    def test_network_ports(self) -> Dict[str, Any]:
        """Test if required network ports are open"""
        required_ports = {
            8767: 'Backend WebSocket',
            8765: 'DO Button WebSocket', 
            8787: 'Backend HTTP Status',
            11434: 'LLM Service (Ollama)',
            8080: 'RPA_AVEN (if running)'
        }
        
        open_ports = []
        closed_ports = []
        
        for port, description in required_ports.items():
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                if result == 0:
                    open_ports.append({'port': port, 'description': description})
                else:
                    closed_ports.append({'port': port, 'description': description})
            except Exception as e:
                closed_ports.append({'port': port, 'description': description, 'error': str(e)})
        
        return {
            'status': 'pass' if len(closed_ports) == 0 else 'partial',
            'open_ports': open_ports,
            'closed_ports': closed_ports,
            'total_open': len(open_ports),
            'total_required': len(required_ports)
        }
    
    def test_llm_service(self) -> Dict[str, Any]:
        """Test LLM service (Ollama)"""
        try:
            response = requests.get(self.endpoints['llm_api'], timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                return {
                    'status': 'pass',
                    'available_models': model_names,
                    'total_models': len(models),
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                return {
                    'status': 'fail',
                    'error': f'HTTP {response.status_code}',
                    'response': response.text
                }
        except Exception as e:
            return {
                'status': 'fail',
                'error': str(e)
            }
    
    def test_backend_communication(self) -> Dict[str, Any]:
        """Test backend communication via HTTP and WebSocket"""
        results = {}
        
        # Test HTTP endpoint
        try:
            response = requests.get(self.endpoints['backend_http'], timeout=5)
            if response.status_code == 200:
                results['http'] = {
                    'status': 'pass',
                    'response': response.json(),
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                results['http'] = {
                    'status': 'fail',
                    'error': f'HTTP {response.status_code}'
                }
        except Exception as e:
            results['http'] = {
                'status': 'fail',
                'error': str(e)
            }
        
        # Test WebSocket endpoint
        try:
            async def test_websocket():
                async with websockets.connect(self.endpoints['backend_ws']) as ws:
                    # Send a test message
                    test_message = {
                        'type': 'status',
                        'timestamp': datetime.now().isoformat()
                    }
                    await ws.send(json.dumps(test_message))
                    
                    # Wait for response
                    response = await asyncio.wait_for(ws.recv(), timeout=5)
                    return json.loads(response)
            
            # Run WebSocket test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                ws_response = loop.run_until_complete(test_websocket())
                results['websocket'] = {
                    'status': 'pass',
                    'response': ws_response
                }
            finally:
                loop.close()
                
        except Exception as e:
            results['websocket'] = {
                'status': 'fail',
                'error': str(e)
            }
        
        return {
            'status': 'pass' if all(r['status'] == 'pass' for r in results.values()) else 'partial',
            'details': results
        }
    
    def test_rpa_automation(self) -> Dict[str, Any]:
        """Test RPA automation capabilities"""
        results = {}
        
        # Test DO Button WebSocket
        try:
            async def test_do_button():
                async with websockets.connect(self.endpoints['do_button_ws']) as ws:
                    # Send a test automation command
                    test_command = {
                        'type': 'click',
                        'x': 100,
                        'y': 100,
                        'test': True
                    }
                    await ws.send(json.dumps(test_command))
                    
                    # Wait for response
                    response = await asyncio.wait_for(ws.recv(), timeout=5)
                    return json.loads(response)
            
            # Run DO Button test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                do_response = loop.run_until_complete(test_do_button())
                results['do_button'] = {
                    'status': 'pass',
                    'response': do_response
                }
            finally:
                loop.close()
                
        except Exception as e:
            results['do_button'] = {
                'status': 'fail',
                'error': str(e)
            }
        
        # Test RPA_AVEN if available
        try:
            response = requests.get(self.endpoints['rpa_aven'], timeout=5)
            if response.status_code == 200:
                results['rpa_aven'] = {
                    'status': 'pass',
                    'response_time': response.elapsed.total_seconds()
                }
            else:
                results['rpa_aven'] = {
                    'status': 'not_running',
                    'note': 'RPA_AVEN server not detected on port 8080'
                }
        except Exception as e:
            results['rpa_aven'] = {
                'status': 'not_running',
                'note': 'RPA_AVEN server not detected'
            }
        
        return {
            'status': 'pass' if results.get('do_button', {}).get('status') == 'pass' else 'partial',
            'details': results
        }
    
    def test_sensor_systems(self) -> Dict[str, Any]:
        """Test sensor systems"""
        # Check if sensor cache files exist
        sensor_cache_files = [
            'cache/screen_sensor/last_screen.json',
            'cache/process_sensor/process_cache.json'
        ]
        
        existing_files = []
        missing_files = []
        
        for file_path in sensor_cache_files:
            if os.path.exists(file_path):
                # Check if file is recent (less than 5 minutes old)
                file_age = time.time() - os.path.getmtime(file_path)
                if file_age < 300:  # 5 minutes
                    existing_files.append({
                        'file': file_path,
                        'age_seconds': file_age,
                        'status': 'recent'
                    })
                else:
                    existing_files.append({
                        'file': file_path,
                        'age_seconds': file_age,
                        'status': 'stale'
                    })
            else:
                missing_files.append(file_path)
        
        return {
            'status': 'pass' if len(missing_files) == 0 else 'partial',
            'existing_files': existing_files,
            'missing_files': missing_files,
            'total_sensors': len(sensor_cache_files)
        }
    
    def test_memory_system(self) -> Dict[str, Any]:
        """Test memory system"""
        # Check memory directory and files
        memory_dir = 'memory'
        memory_files = []
        
        if os.path.exists(memory_dir):
            for root, dirs, files in os.walk(memory_dir):
                for file in files:
                    if file.endswith('.json'):
                        file_path = os.path.join(root, file)
                        file_age = time.time() - os.path.getmtime(file_path)
                        memory_files.append({
                            'file': file_path,
                            'age_seconds': file_age,
                            'size_bytes': os.path.getsize(file_path)
                        })
        
        return {
            'status': 'pass' if len(memory_files) > 0 else 'fail',
            'memory_files': memory_files,
            'total_files': len(memory_files),
            'memory_dir_exists': os.path.exists(memory_dir)
        }
    
    def test_automation_capabilities(self) -> Dict[str, Any]:
        """Test automation capabilities"""
        # Test basic automation functions
        capabilities = {
            'mouse_control': False,
            'keyboard_control': False,
            'screen_capture': False,
            'process_monitoring': False
        }
        
        try:
            # Test if PyAutoGUI is available
            import pyautogui
            capabilities['mouse_control'] = True
            capabilities['keyboard_control'] = True
        except ImportError:
            pass
        
        try:
            # Test if PIL is available for screen capture
            from PIL import ImageGrab
            capabilities['screen_capture'] = True
        except ImportError:
            pass
        
        try:
            # Test if psutil is available for process monitoring
            import psutil
            capabilities['process_monitoring'] = True
        except ImportError:
            pass
        
        available_capabilities = sum(capabilities.values())
        total_capabilities = len(capabilities)
        
        return {
            'status': 'pass' if available_capabilities >= 3 else 'partial',
            'capabilities': capabilities,
            'available': available_capabilities,
            'total': total_capabilities
        }
    
    def _print_test_result(self, category: str, result: Dict[str, Any]):
        """Print test result with appropriate formatting"""
        status = result.get('status', 'unknown')
        
        if status == 'pass':
            print(f"  ✅ {category.replace('_', ' ').title()}: PASS")
        elif status == 'partial':
            print(f"  ⚠️  {category.replace('_', ' ').title()}: PARTIAL")
        elif status == 'fail':
            print(f"  ❌ {category.replace('_', ' ').title()}: FAIL")
        else:
            print(f"  ❓ {category.replace('_', ' ').title()}: UNKNOWN")
        
        # Print details if available
        if 'details' in result and result['details']:
            print(f"     Details: {result['details']}")
        elif 'error' in result:
            print(f"     Error: {result['error']}")
    
    def _generate_final_report(self):
        """Generate final test report"""
        print("=" * 60)
        print("📊 COMPREHENSIVE SYSTEM TEST RESULTS")
        print("=" * 60)
        
        # Count results
        pass_count = sum(1 for r in self.test_results.values() if r.get('status') == 'pass')
        partial_count = sum(1 for r in self.test_results.values() if r.get('status') == 'partial')
        fail_count = sum(1 for r in self.test_results.values() if r.get('status') == 'fail')
        total_count = len(self.test_results)
        
        # Overall status
        if pass_count == total_count:
            overall_status = "✅ ALL TESTS PASSED"
        elif fail_count == 0:
            overall_status = "⚠️  MOSTLY WORKING (some partial results)"
        else:
            overall_status = "❌ SYSTEM HAS ISSUES"
        
        print(f"Overall Status: {overall_status}")
        print(f"Tests Passed: {pass_count}/{total_count}")
        print(f"Tests Partial: {partial_count}/{total_count}")
        print(f"Tests Failed: {fail_count}/{total_count}")
        print()
        
        # Detailed results
        print("Detailed Results:")
        for category, result in self.test_results.items():
            status = result.get('status', 'unknown')
            status_icon = {'pass': '✅', 'partial': '⚠️', 'fail': '❌'}.get(status, '❓')
            print(f"  {status_icon} {category.replace('_', ' ').title()}: {status.upper()}")
        
        print()
        print(f"Test completed in {time.time() - self.start_time:.2f} seconds")
        
        # Save results to file
        report_file = f"test_results/system_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'overall_status': overall_status,
                'summary': {
                    'pass': pass_count,
                    'partial': partial_count,
                    'fail': fail_count,
                    'total': total_count
                },
                'results': self.test_results
            }, f, indent=2)
        
        print(f"Detailed report saved to: {report_file}")

def main():
    """Main function"""
    print("🚀 Starting Comprehensive SensAI System Test...")
    print("This will test all major components: RPA_AVEN, AIAYER, LLM, sensors, memory, automation")
    print()
    
    tester = ComprehensiveSystemTest()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 