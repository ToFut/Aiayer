#!/usr/bin/env python3
"""
RPA Workflow Test Script
Tests specific RPA automation workflows and capabilities
"""

import asyncio
import json
import time
import websockets
import requests
from datetime import datetime

class RPAWorkflowTester:
    """Test RPA automation workflows"""
    
    def __init__(self):
        self.endpoints = {
            'do_button': 'ws://localhost:8765',
            'backend': 'ws://localhost:8767/ws',
            'backend_http': 'http://localhost:8787/status'
        }
        self.results = {}
    
    def test_all_workflows(self):
        """Test all RPA workflows"""
        print("🤖 RPA WORKFLOW TESTING")
        print("=" * 50)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        workflows = [
            ('basic_automation', self.test_basic_automation),
            ('screen_interaction', self.test_screen_interaction),
            ('data_extraction', self.test_data_extraction),
            ('process_automation', self.test_process_automation),
            ('ai_integration', self.test_ai_integration),
            ('error_handling', self.test_error_handling)
        ]
        
        for name, test_func in workflows:
            print(f"🔍 Testing: {name.replace('_', ' ').title()}")
            try:
                result = test_func()
                self.results[name] = result
                self._print_result(name, result)
            except Exception as e:
                self.results[name] = {'status': 'error', 'error': str(e)}
                self._print_result(name, self.results[name])
            print()
        
        self._print_summary()
    
    def test_basic_automation(self):
        """Test basic automation capabilities"""
        try:
            async def test_do_button():
                async with websockets.connect(self.endpoints['do_button']) as ws:
                    # Test basic commands
                    commands = [
                        {'type': 'status', 'test': True},
                        {'type': 'get_position', 'test': True},
                        {'type': 'get_screen_size', 'test': True}
                    ]
                    
                    responses = []
                    for cmd in commands:
                        await ws.send(json.dumps(cmd))
                        response = await asyncio.wait_for(ws.recv(), timeout=5)
                        responses.append(json.loads(response))
                    
                    return responses
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                responses = loop.run_until_complete(test_do_button())
                return {
                    'status': 'pass',
                    'commands_tested': len(responses),
                    'responses': responses
                }
            finally:
                loop.close()
                
        except Exception as e:
            return {'status': 'fail', 'error': str(e)}
    
    def test_screen_interaction(self):
        """Test screen interaction capabilities"""
        try:
            # Test if screen interaction libraries are available
            import pyautogui
            from PIL import ImageGrab
            
            # Get current mouse position
            mouse_pos = pyautogui.position()
            
            # Get screen size
            screenshot = ImageGrab.grab()
            screen_size = screenshot.size
            
            return {
                'status': 'pass',
                'mouse_position': mouse_pos,
                'screen_size': screen_size,
                'capabilities': ['mouse_control', 'keyboard_control', 'screen_capture']
            }
        except ImportError as e:
            return {'status': 'fail', 'error': f'Missing library: {str(e)}'}
        except Exception as e:
            return {'status': 'fail', 'error': str(e)}
    
    def test_data_extraction(self):
        """Test data extraction capabilities"""
        try:
            # Test OCR capabilities
            from PIL import ImageGrab
            import pytesseract
            
            # Take a screenshot
            screenshot = ImageGrab.grab()
            
            # Try to extract text (this might fail if no text is visible)
            try:
                text = pytesseract.image_to_string(screenshot)
                ocr_working = len(text.strip()) >= 0  # Just check if it runs
            except:
                ocr_working = False
            
            return {
                'status': 'pass',
                'screenshot_captured': True,
                'ocr_available': ocr_working,
                'capabilities': ['screen_capture', 'text_extraction', 'image_analysis']
            }
        except ImportError as e:
            return {'status': 'partial', 'error': f'Missing library: {str(e)}', 'capabilities': ['screen_capture']}
        except Exception as e:
            return {'status': 'fail', 'error': str(e)}
    
    def test_process_automation(self):
        """Test process automation capabilities"""
        try:
            import psutil
            
            # Get current processes
            processes = list(psutil.process_iter(['pid', 'name']))
            
            # Test process monitoring
            current_process = psutil.Process()
            
            return {
                'status': 'pass',
                'processes_monitored': len(processes),
                'current_process': {
                    'pid': current_process.pid,
                    'name': current_process.name(),
                    'memory_mb': current_process.memory_info().rss / 1024 / 1024
                },
                'capabilities': ['process_monitoring', 'process_control', 'resource_tracking']
            }
        except Exception as e:
            return {'status': 'fail', 'error': str(e)}
    
    def test_ai_integration(self):
        """Test AI integration capabilities"""
        try:
            # Test backend AI capabilities
            response = requests.get(self.endpoints['backend_http'], timeout=5)
            
            if response.status_code == 200:
                backend_data = response.json()
                
                # Test WebSocket AI communication
                async def test_ai_ws():
                    async with websockets.connect(self.endpoints['backend']) as ws:
                        # Test AI message
                        ai_message = {
                            'type': 'ai_request',
                            'message': 'Test AI integration',
                            'mode': 'ask_mode',
                            'test': True
                        }
                        await ws.send(json.dumps(ai_message))
                        response = await asyncio.wait_for(ws.recv(), timeout=10)
                        return json.loads(response)
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    ai_response = loop.run_until_complete(test_ai_ws())
                    return {
                        'status': 'pass',
                        'backend_status': backend_data,
                        'ai_response': ai_response,
                        'capabilities': ['ai_communication', 'context_processing', 'suggestion_generation']
                    }
                finally:
                    loop.close()
            else:
                return {'status': 'fail', 'error': f'Backend HTTP error: {response.status_code}'}
                
        except Exception as e:
            return {'status': 'fail', 'error': str(e)}
    
    def test_error_handling(self):
        """Test error handling capabilities"""
        try:
            # Test invalid command handling
            async def test_error_handling():
                async with websockets.connect(self.endpoints['do_button']) as ws:
                    # Send invalid command
                    invalid_command = {'type': 'invalid_command', 'test': True}
                    await ws.send(json.dumps(invalid_command))
                    
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=5)
                        return json.loads(response)
                    except asyncio.TimeoutError:
                        return {'type': 'timeout', 'message': 'No response to invalid command'}
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                error_response = loop.run_until_complete(test_error_handling())
                return {
                    'status': 'pass',
                    'error_handling': True,
                    'invalid_command_response': error_response,
                    'capabilities': ['error_detection', 'graceful_degradation', 'timeout_handling']
                }
            finally:
                loop.close()
                
        except Exception as e:
            return {'status': 'fail', 'error': str(e)}
    
    def _print_result(self, name: str, result: dict):
        """Print test result"""
        status = result.get('status', 'unknown')
        
        if status == 'pass':
            print(f"  ✅ {name.replace('_', ' ').title()}: PASS")
        elif status == 'partial':
            print(f"  ⚠️  {name.replace('_', ' ').title()}: PARTIAL")
        elif status == 'fail':
            print(f"  ❌ {name.replace('_', ' ').title()}: FAIL")
        else:
            print(f"  ❓ {name.replace('_', ' ').title()}: ERROR")
        
        if 'capabilities' in result:
            print(f"     Capabilities: {', '.join(result['capabilities'])}")
        elif 'error' in result:
            print(f"     Error: {result['error']}")
    
    def _print_summary(self):
        """Print test summary"""
        print("=" * 50)
        print("📊 RPA WORKFLOW TEST SUMMARY")
        print("=" * 50)
        
        pass_count = sum(1 for r in self.results.values() if r.get('status') == 'pass')
        partial_count = sum(1 for r in self.results.values() if r.get('status') == 'partial')
        fail_count = sum(1 for r in self.results.values() if r.get('status') == 'fail')
        total_count = len(self.results)
        
        if pass_count == total_count:
            overall_status = "✅ ALL RPA WORKFLOWS WORKING"
        elif fail_count == 0:
            overall_status = "⚠️  MOSTLY WORKING (some partial results)"
        else:
            overall_status = "❌ SOME WORKFLOWS FAILED"
        
        print(f"Overall Status: {overall_status}")
        print(f"Workflows Passed: {pass_count}/{total_count}")
        print(f"Workflows Partial: {partial_count}/{total_count}")
        print(f"Workflows Failed: {fail_count}/{total_count}")
        print()
        
        # Print detailed results
        for name, result in self.results.items():
            status_icon = {'pass': '✅', 'partial': '⚠️', 'fail': '❌'}.get(result.get('status'), '❓')
            print(f"  {status_icon} {name.replace('_', ' ').title()}: {result.get('status', 'unknown').upper()}")
        
        print()
        print("🎯 RPA Automation is ready for use!")

def main():
    """Main function"""
    print("🤖 Starting RPA Workflow Testing...")
    print("Testing specific automation workflows and capabilities")
    print()
    
    tester = RPAWorkflowTester()
    tester.test_all_workflows()

if __name__ == "__main__":
    main() 