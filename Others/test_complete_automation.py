#!/usr/bin/env python3
"""
Test Complete Automation System
Tests the full agent automation workflow from natural language to UI interaction.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_workflow.enhanced_automation_handler import EnhancedAutomationHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AutomationTester:
    """Test the complete automation system"""
    
    def __init__(self):
        self.handler = EnhancedAutomationHandler()
        self.test_results = []
        
    async def run_comprehensive_test(self):
        """Run comprehensive automation tests"""
        print("🚀 Starting Complete Automation System Test")
        print("=" * 60)
        
        # Test 1: Screen Analysis
        print("\n🔍 Test 1: Screen Analysis")
        await self._test_screen_analysis()
        
        # Test 2: Query Commands
        print("\n❓ Test 2: Query Commands")
        await self._test_query_commands()
        
        # Test 3: Simple Automation Commands
        print("\n🎯 Test 3: Simple Automation Commands")
        await self._test_simple_automation()
        
        # Test 4: Complex Automation Commands
        print("\n🎪 Test 4: Complex Automation Commands")
        await self._test_complex_automation()
        
        # Test 5: Error Handling
        print("\n⚠️  Test 5: Error Handling")
        await self._test_error_handling()
        
        # Show summary
        await self._show_test_summary()
    
    async def _test_screen_analysis(self):
        """Test screen analysis capabilities"""
        try:
            summary = await self.handler.get_screen_summary()
            
            if "total_elements" in summary:
                print(f"   ✅ Screen analysis successful")
                print(f"   📊 Found {summary['total_elements']} UI elements")
                print(f"   🔘 Element types: {list(summary.get('element_types', {}).keys())}")
                
                if summary.get('notable_buttons'):
                    print(f"   🎯 Notable buttons: {', '.join(summary['notable_buttons'][:3])}")
                
                self._record_test("screen_analysis", True, "Screen analysis working")
            else:
                print(f"   ❌ Screen analysis failed: {summary}")
                self._record_test("screen_analysis", False, "No elements found")
                
        except Exception as e:
            print(f"   ❌ Screen analysis error: {e}")
            self._record_test("screen_analysis", False, str(e))
    
    async def _test_query_commands(self):
        """Test query command handling"""
        query_commands = [
            "what buttons are available?",
            "what elements are on screen?",
            "where is the button?"
        ]
        
        for command in query_commands:
            try:
                print(f"   🔎 Testing: '{command}'")
                result = await self.handler.handle_user_instruction(command)
                
                if result["success"]:
                    print(f"      ✅ Query handled successfully")
                    exec_result = result.get("execution_result", {})
                    if "result" in exec_result:
                        print(f"      📝 Result: {exec_result['result'][:100]}...")
                    self._record_test(f"query_{command[:10]}", True, "Query successful")
                else:
                    print(f"      ❌ Query failed: {result.get('error', 'Unknown')}")
                    self._record_test(f"query_{command[:10]}", False, result.get('error', 'Unknown'))
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"      ❌ Query error: {e}")
                self._record_test(f"query_{command[:10]}", False, str(e))
    
    async def _test_simple_automation(self):
        """Test simple automation commands"""
        # These commands should work on most screens
        simple_commands = [
            "scroll down",
            "scroll up", 
            "click the screen"  # Generic click command
        ]
        
        for command in simple_commands:
            try:
                print(f"   🎯 Testing: '{command}'")
                result = await self.handler.handle_user_instruction(command)
                
                if result["success"]:
                    print(f"      ✅ Command executed successfully")
                    exec_result = result.get("execution_result", {})
                    if "action" in exec_result:
                        print(f"      🎬 Action: {exec_result['action']}")
                    self._record_test(f"simple_{command[:10]}", True, "Command successful")
                else:
                    print(f"      ❌ Command failed: {result.get('error', 'Unknown')}")
                    # Some failures are expected for non-existent elements
                    self._record_test(f"simple_{command[:10]}", False, result.get('error', 'Unknown'))
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"      ❌ Command error: {e}")
                self._record_test(f"simple_{command[:10]}", False, str(e))
    
    async def _test_complex_automation(self):
        """Test complex automation commands"""
        # These might not find exact targets, but should parse correctly
        complex_commands = [
            "click the submit button",
            "type hello in the search box",
            "double click the file icon",
            "right click the menu"
        ]
        
        for command in complex_commands:
            try:
                print(f"   🎪 Testing: '{command}'")
                result = await self.handler.handle_user_instruction(command)
                
                if result["success"]:
                    print(f"      ✅ Complex command executed")
                    exec_result = result.get("execution_result", {})
                    if "target_element" in exec_result:
                        target = exec_result["target_element"]
                        print(f"      🎯 Target: {target.get('element_text', 'unknown')}")
                        print(f"      🎲 Confidence: {target.get('confidence', 0):.2f}")
                    self._record_test(f"complex_{command[:10]}", True, "Command successful")
                else:
                    print(f"      ⚠️  Command failed (expected for some): {result.get('error', 'Unknown')}")
                    # Show available alternatives if provided
                    exec_result = result.get("execution_result", {})
                    if "available_elements" in exec_result:
                        available = exec_result["available_elements"][:3]
                        if available:
                            print(f"      💡 Available: {', '.join(available)}")
                    self._record_test(f"complex_{command[:10]}", False, "Element not found (expected)")
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"      ❌ Command error: {e}")
                self._record_test(f"complex_{command[:10]}", False, str(e))
    
    async def _test_error_handling(self):
        """Test error handling with invalid commands"""
        error_commands = [
            "click the nonexistent magic button",
            "type in the invisible field",
            "perform impossible action",
            ""  # Empty command
        ]
        
        for command in error_commands:
            try:
                print(f"   ⚠️  Testing error case: '{command or '[empty]'}'")
                result = await self.handler.handle_user_instruction(command)
                
                # For error cases, we expect graceful failure
                if not result["success"]:
                    print(f"      ✅ Error handled gracefully")
                    error_msg = result.get('error', 'Unknown error')
                    print(f"      📝 Error message: {error_msg[:50]}...")
                    self._record_test(f"error_{len(command)}", True, "Error handled gracefully")
                else:
                    print(f"      ⚠️  Unexpected success for error case")
                    self._record_test(f"error_{len(command)}", False, "Should have failed")
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"      ✅ Exception handled: {str(e)[:50]}...")
                self._record_test(f"error_{len(command)}", True, "Exception handled")
    
    def _record_test(self, test_name: str, success: bool, details: str):
        """Record test result"""
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _show_test_summary(self):
        """Show comprehensive test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        print(f"\n🔍 Test Details:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"   {status} {result['test']}: {result['details'][:50]}...")
        
        # Show command history
        print(f"\n📜 Recent Command History:")
        history = self.handler.get_command_history(5)
        for i, cmd in enumerate(history, 1):
            status = "✅" if cmd["success"] else "❌"
            print(f"   {i}. {status} {cmd['instruction']}")
        
        # Final assessment
        print(f"\n🎯 AUTOMATION SYSTEM STATUS:")
        if passed_tests >= total_tests * 0.7:
            print("🟢 EXCELLENT - Automation system is working well!")
            print("   ✨ The agent can understand and execute commands")
            print("   🎯 UI element detection is functional")
            print("   🤖 Natural language processing is working")
        elif passed_tests >= total_tests * 0.5:
            print("🟡 GOOD - Automation system is partially working")
            print("   ⚡ Basic functionality is operational")
            print("   🔧 Some improvements needed for complex commands")
        else:
            print("🔴 NEEDS WORK - Automation system needs debugging")
            print("   🛠️  Check LLaVA and UI detection setup")
            print("   🔍 Verify screen capture capabilities")
        
        print("=" * 60)
    
    def cleanup(self):
        """Clean up resources"""
        if self.handler:
            self.handler.stop()

async def main():
    """Main test function"""
    tester = AutomationTester()
    
    try:
        await tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        logger.error(f"Test error: {e}", exc_info=True)
    finally:
        tester.cleanup()

if __name__ == "__main__":
    print("🤖 Enhanced Agent Automation - Complete System Test")
    print("This will test the full automation pipeline from command to execution")
    print("Press Ctrl+C to stop at any time\n")
    
    asyncio.run(main())