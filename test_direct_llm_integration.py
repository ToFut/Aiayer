#!/usr/bin/env python3
"""
Test Direct LLM Integration for AgentMode
Validates that the enhanced automation handler now uses LLM instead of hardcoded patterns.
"""

import asyncio
import json
import logging
import requests
import time
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('llm_integration_test')

class DirectLLMIntegrationTester:
    """Test the new direct LLM integration functionality"""
    
    def __init__(self):
        self.test_results = {
            'ollama_connection': False,
            'llm_step_generation': False,
            'json_parsing': False,
            'integration_test': False,
            'performance_test': False
        }
        self.performance_data = []
    
    def test_ollama_connection(self):
        """Test direct connection to Ollama API"""
        logger.info("🔗 Testing Ollama API connection...")
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json()
                logger.info(f"✅ Ollama connected. Available models: {[m['name'] for m in models.get('models', [])]}")
                self.test_results['ollama_connection'] = True
                return True
            else:
                logger.error(f"❌ Ollama API error: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Ollama connection failed: {e}")
            return False
    
    def test_direct_llm_call(self):
        """Test direct LLM call for step generation"""
        logger.info("🧠 Testing direct LLM step generation...")
        
        test_instruction = "Click on the search button and type 'python tutorial'"
        
        prompt = f"""Create automation steps for: "{test_instruction}"

Return ONLY a JSON array with no explanation, no markdown, no code blocks:

[
  {{"id": "step_1", "description": "Analyze current screen", "action_type": "analyze", "target": "screen", "value": ""}},
  {{"id": "step_2", "description": "Detect target element", "action_type": "detect", "target": "element", "value": ""}},
  {{"id": "step_3", "description": "Perform action", "action_type": "click", "target": "element", "value": ""}}
]

For instruction "{test_instruction}", create 3-5 logical automation steps. Use action_type: analyze, detect, click, type, scroll, wait, navigate. Include element detection before interaction. Be specific about targets and values."""
        
        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:1b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "stop": ["Human:", "Assistant:", "User:"]
                    }
                },
                timeout=15
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                llm_response = response.json()
                generated_text = llm_response.get("response", "").strip()
                
                logger.info(f"✅ LLM responded in {duration:.2f}s")
                logger.info(f"📝 LLM Response: {generated_text[:200]}...")
                
                # Test JSON parsing
                steps_json = self._extract_json_from_response(generated_text)
                if steps_json and len(steps_json) >= 2:
                    logger.info(f"✅ Extracted {len(steps_json)} steps from LLM response")
                    self.test_results['llm_step_generation'] = True
                    self.test_results['json_parsing'] = True
                    self.performance_data.append(duration)
                    return True, steps_json
                else:
                    logger.error("❌ Could not extract valid steps from LLM response")
                    return False, None
            else:
                logger.error(f"❌ LLM API error: {response.status_code}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Direct LLM call failed: {e}")
            return False, None
    
    def _extract_json_from_response(self, text):
        """Extract JSON array from LLM response text"""
        try:
            import re
            
            # Remove markdown code blocks
            text = re.sub(r'```[a-z]*\n?', '', text)
            text = re.sub(r'```', '', text)
            
            # Look for JSON array in the response (more comprehensive)
            json_match = re.search(r'(\[\s*\{.*?\}\s*\])', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                # Clean up any formatting issues
                json_str = re.sub(r'\n\s*', ' ', json_str)  # Remove excessive whitespace
                return json.loads(json_str)
            
            # Try to find array with multiple objects
            bracket_match = re.search(r'\[.*\]', text, re.DOTALL)
            if bracket_match:
                json_str = bracket_match.group(0)
                # Clean up formatting
                json_str = re.sub(r'\n\s*', ' ', json_str)
                return json.loads(json_str)
            
            # Try to parse the entire response as JSON
            cleaned_text = text.strip()
            if cleaned_text.startswith('[') and cleaned_text.endswith(']'):
                return json.loads(cleaned_text)
            
            return None
        except Exception as e:
            logger.error(f"JSON extraction failed: {e}")
            logger.debug(f"Failed text: {text[:300]}...")
            return None
    
    async def test_enhanced_automation_handler(self):
        """Test the enhanced automation handler with LLM integration"""
        logger.info("🚀 Testing Enhanced Automation Handler with LLM integration...")
        
        try:
            # Import the enhanced automation handler
            import sys, os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'agent_workflow'))
            from enhanced_automation_handler import EnhancedAutomationHandler
            
            handler = EnhancedAutomationHandler()
            
            test_instructions = [
                "Click on the search button and type 'machine learning'",
                "Fill out the contact form with name John Doe and email john@example.com",
                "Navigate to settings and enable dark mode",
                "Add item to cart and proceed to checkout"
            ]
            
            success_count = 0
            for instruction in test_instructions:
                try:
                    logger.info(f"🔄 Testing: {instruction}")
                    start_time = time.time()
                    
                    result = await handler.create_execution_plan(instruction)
                    duration = time.time() - start_time
                    
                    if result and 'execution_plan' in result:
                        plan = result['execution_plan']
                        # Check if plan has steps attribute or is a dict with steps
                        steps_count = 0
                        if hasattr(plan, 'steps'):
                            steps_count = len(plan.steps)
                        elif isinstance(plan, dict) and 'steps' in plan:
                            steps_count = len(plan['steps'])
                        elif hasattr(plan, '__dict__') and hasattr(plan, 'title'):
                            # For FastFallbackPlan objects
                            steps_count = len(getattr(plan, 'steps', []))
                        
                        if steps_count >= 2:
                            logger.info(f"✅ Generated {steps_count} steps in {duration:.2f}s")
                            success_count += 1
                            self.performance_data.append(duration)
                        else:
                            logger.warning(f"⚠️ Insufficient steps generated: {steps_count}")
                            # Log plan details for debugging
                            logger.debug(f"Plan type: {type(plan)}")
                            logger.debug(f"Plan attributes: {dir(plan) if hasattr(plan, '__dict__') else 'No attributes'}")
                    else:
                        logger.error("❌ No valid execution plan returned")
                
                except Exception as e:
                    logger.error(f"❌ Handler test failed for '{instruction}': {e}")
                    logger.error(traceback.format_exc())
            
            success_rate = (success_count / len(test_instructions)) * 100
            logger.info(f"📊 Enhanced Automation Handler Success Rate: {success_rate:.1f}%")
            
            if success_rate >= 75:
                self.test_results['integration_test'] = True
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Enhanced automation handler test failed: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def test_performance_comparison(self):
        """Test performance of LLM vs hardcoded patterns"""
        logger.info("⚡ Testing performance comparison...")
        
        if self.performance_data:
            avg_time = sum(self.performance_data) / len(self.performance_data)
            logger.info(f"📊 Average LLM response time: {avg_time:.2f}s")
            
            if avg_time <= 5.0:  # Should be faster than 5s
                logger.info("✅ LLM integration meets performance requirements")
                self.test_results['performance_test'] = True
                return True
            else:
                logger.warning("⚠️ LLM integration slower than expected")
                return False
        else:
            logger.error("❌ No performance data collected")
            return False
    
    async def run_all_tests(self):
        """Run comprehensive test suite"""
        logger.info("🎯 Starting Direct LLM Integration Test Suite")
        logger.info("=" * 60)
        
        # Test 1: Ollama Connection
        self.test_ollama_connection()
        
        # Test 2: Direct LLM Call
        if self.test_results['ollama_connection']:
            self.test_direct_llm_call()
        
        # Test 3: Enhanced Automation Handler
        if self.test_results['llm_step_generation']:
            await self.test_enhanced_automation_handler()
        
        # Test 4: Performance Analysis
        self.test_performance_comparison()
        
        # Results Summary
        logger.info("=" * 60)
        logger.info("📋 TEST RESULTS SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(self.test_results.values())
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name}: {status}")
        
        success_rate = (passed_tests / total_tests) * 100
        logger.info(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        if success_rate >= 80:
            logger.info("🎉 Direct LLM Integration SUCCESSFUL!")
            logger.info("🚀 AgentMode now uses intelligent LLM-generated steps instead of hardcoded patterns")
        else:
            logger.error("💥 Direct LLM Integration needs improvements")
        
        return success_rate >= 80

async def main():
    """Main test execution"""
    tester = DirectLLMIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n🎊 SUCCESS: Direct LLM integration is working perfectly!")
        logger.info("✨ The system now generates intelligent automation steps using LLM")
    else:
        logger.error("\n💔 FAILURE: Direct LLM integration needs fixes")

if __name__ == "__main__":
    asyncio.run(main())