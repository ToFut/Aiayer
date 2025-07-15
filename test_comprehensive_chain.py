#!/usr/bin/env python3
"""
Comprehensive test of the whole automation chain with 10 different prompts
from easy to difficult scenarios.
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any
import re

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.enhanced_backend_server import EnhancedBackendServer
from backend.llm.llm_service import LLMService
from backend.automation_plan import AutomationPlan

class ComprehensiveChainTester:
    def __init__(self):
        self.backend = EnhancedBackendServer()
        self.llm_service = LLMService()
        self.test_results = []
        
    async def setup(self):
        """Initialize all components"""
        print("🔧 Setting up test environment...")
        
        # Initialize backend
        await self.backend.initialize()
        
        # Initialize LLM service
        await self.llm_service.initialize()
        
        print("✅ Test environment ready")
        
    async def cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up...")
        await self.backend.stop()
        await self.llm_service.cleanup()
        print("✅ Cleanup completed")
        
    def get_test_prompts(self) -> List[Dict[str, Any]]:
        """Define 10 test prompts from easy to difficult"""
        return [
            {
                "name": "Simple App Launch",
                "prompt": "open calculator",
                "difficulty": "Easy",
                "expected_apps": ["Calculator"],
                "description": "Basic app launch request"
            },
            {
                "name": "Multiple Apps",
                "prompt": "open calculator and safari",
                "difficulty": "Easy",
                "expected_apps": ["Calculator", "Safari"],
                "description": "Multiple app launch request"
            },
            {
                "name": "App with Action",
                "prompt": "open safari and go to google.com",
                "difficulty": "Medium",
                "expected_apps": ["Safari"],
                "description": "App launch with specific action"
            },
            {
                "name": "Complex Workflow",
                "prompt": "open calculator, then open safari and go to google.com, then take a screenshot",
                "difficulty": "Medium",
                "expected_apps": ["Calculator", "Safari"],
                "description": "Multi-step workflow with actions"
            },
            {
                "name": "System Actions",
                "prompt": "take a screenshot and save it to desktop",
                "difficulty": "Medium",
                "expected_apps": [],
                "description": "System-level actions"
            },
            {
                "name": "File Operations",
                "prompt": "open finder, navigate to desktop, create a new folder called test",
                "difficulty": "Hard",
                "expected_apps": ["Finder"],
                "description": "File system operations"
            },
            {
                "name": "Complex Automation",
                "prompt": "open safari, go to github.com, wait 3 seconds, take a screenshot, then open calculator and perform basic math",
                "difficulty": "Hard",
                "expected_apps": ["Safari", "Calculator"],
                "description": "Complex multi-app automation with timing"
            },
            {
                "name": "Edge Case - No Apps",
                "prompt": "just wait 5 seconds and take a screenshot",
                "difficulty": "Medium",
                "expected_apps": [],
                "description": "Actions without app launches"
            },
            {
                "name": "Ambiguous Request",
                "prompt": "do something productive with my computer",
                "difficulty": "Hard",
                "expected_apps": [],
                "description": "Vague request requiring interpretation"
            },
            {
                "name": "Very Complex Workflow",
                "prompt": "open safari, go to google.com, search for 'python automation', wait 2 seconds, take a screenshot, open calculator, calculate 15 * 23, then open finder and go to downloads",
                "difficulty": "Very Hard",
                "expected_apps": ["Safari", "Calculator", "Finder"],
                "description": "Complex multi-step workflow with web interaction and calculations"
            }
        ]
        
    def _extract_plan_dict(self, llm_response: str, prompt: str) -> dict:
        """Extract a plan dict from LLM response, robust to markdown/code blocks and malformed JSON."""
        # Try to extract JSON from code blocks
        text = llm_response.strip()
        
        # Remove markdown code block markers
        if '```json' in text:
            text = text.split('```json', 1)[1]
        if '```' in text:
            text = text.split('```', 1)[1]
        text = text.strip('`\n ')
        
        # Try to find the first { ... } with better regex
        match = re.search(r'\{[\s\S]*?\}', text)
        if match:
            text = match.group(0)
        
        # Try to repair common JSON issues
        text = text.replace("'", '"')
        text = re.sub(r',\s*}', '}', text)
        text = re.sub(r',\s*]', ']', text)
        
        # Fix missing commas between object properties
        text = re.sub(r'}\s*{', r'},{', text)
        text = re.sub(r'}\s*]', r'}]', text)
        text = re.sub(r'}\s*}', r'}}', text)
        
        # Fix missing commas in arrays
        text = re.sub(r'}\s*{', r'},{', text)
        
        # Fix the specific LLM issue: }}] should be }]
        text = re.sub(r'}\s*}\s*]', r'}]', text)
        
        # Fix any remaining }}] patterns
        text = re.sub(r'}}]', r'}]', text)
        
        # Try to fix missing closing braces
        brace_count = text.count('{') - text.count('}')
        if brace_count > 0:
            text += '}' * brace_count
        
        # Try to fix missing closing brackets
        bracket_count = text.count('[') - text.count(']')
        if bracket_count > 0:
            text += ']' * bracket_count
        
        # Try to parse
        try:
            plan = json.loads(text)
            
            # If plan is just steps, wrap it
            if isinstance(plan, list):
                plan = {"steps": plan}
            
            # Ensure required fields
            if "steps" not in plan or not isinstance(plan["steps"], list):
                # Try to create steps from the plan structure
                if isinstance(plan, dict):
                    steps = []
                    for key, value in plan.items():
                        if key != "task_id" and key != "completed":
                            if isinstance(value, dict):
                                steps.append(value)
                            elif isinstance(value, str):
                                steps.append({"description": value})
                    if steps:
                        plan["steps"] = steps
                    else:
                        raise ValueError("No steps in plan")
                else:
                    raise ValueError("No steps in plan")
            
            if "task_id" not in plan:
                plan["task_id"] = f"plan_{int(time.time())}"
            
            # Normalize app names
            if "apps" in plan:
                plan["apps"] = self._normalize_app_names(plan["apps"])
            
            return plan
            
        except Exception as e:
            # Try one more time with more aggressive repair
            try:
                # Remove any trailing commas before closing braces/brackets
                text = re.sub(r',(\s*[}\]])', r'\1', text)
                # Fix common LLM JSON issues
                text = re.sub(r'(\w+):\s*"([^"]*)"\s*(\w+):', r'\1: "\2", \3:', text)
                
                # More aggressive }}] fix
                text = re.sub(r'}}]', r'}]', text)
                text = re.sub(r'}\s*}\s*]', r'}]', text)
                
                # Try to complete truncated JSON
                if text.count('{') > text.count('}'):
                    text += '}' * (text.count('{') - text.count('}'))
                if text.count('[') > text.count(']'):
                    text += ']' * (text.count('[') - text.count(']'))
                
                print(f"  🔧 Attempting JSON repair: {text[:100]}...")
                
                plan = json.loads(text)
                
                # If plan is just steps, wrap it
                if isinstance(plan, list):
                    plan = {"steps": plan}
                
                # Ensure required fields
                if "steps" not in plan or not isinstance(plan["steps"], list):
                    if isinstance(plan, dict):
                        steps = []
                        for key, value in plan.items():
                            if key != "task_id" and key != "completed":
                                if isinstance(value, dict):
                                    steps.append(value)
                                elif isinstance(value, str):
                                    steps.append({"description": value})
                        if steps:
                            plan["steps"] = steps
                        else:
                            raise ValueError("No steps in plan")
                    else:
                        raise ValueError("No steps in plan")
                
                if "task_id" not in plan:
                    plan["task_id"] = f"plan_{int(time.time())}"
                
                # Normalize app names
                if "apps" in plan:
                    plan["apps"] = self._normalize_app_names(plan["apps"])
                
                return plan
                
            except Exception as e2:
                raise ValueError(f"Failed to parse plan JSON: {e}\nRaw: {text[:200]}")

    def _normalize_app_names(self, apps: List[str]) -> List[str]:
        """Normalize app names to standard format."""
        app_mapping = {
            'calc': 'Calculator',
            'calculator': 'Calculator',
            'safari': 'Safari',
            'finder': 'Finder',
            'chrome': 'Chrome',
            'google': 'Safari',  # Assume Safari for Google
            'github': 'Safari'   # Assume Safari for GitHub
        }
        normalized = []
        for app in apps:
            normalized_name = app_mapping.get(app.lower(), app)
            if normalized_name not in normalized:
                normalized.append(normalized_name)
        return normalized

    def _fallback_plan_dict(self, prompt: str) -> dict:
        """Create a minimal fallback plan dict."""
        return {
            "task_id": f"fallback_{int(time.time())}",
            "steps": [
                {"action": "execute", "description": f"Fallback: {prompt}"}
            ],
            "completed": False
        }

    def _create_fallback_response(self, prompt: str) -> str:
        """Create an intelligent fallback response based on the user prompt."""
        # Extract apps from the prompt
        apps = []
        if "calculator" in prompt.lower():
            apps.append("Calculator")
        if "safari" in prompt.lower():
            apps.append("Safari")
        if "finder" in prompt.lower():
            apps.append("Finder")
        if "chrome" in prompt.lower():
            apps.append("Chrome")
        
        # Create steps based on the prompt
        steps = []
        
        if "open" in prompt.lower():
            for app in apps:
                steps.append({
                    "action": "open_app",
                    "app": app,
                    "description": f"Open {app}"
                })
        
        if "wait" in prompt.lower():
            # Extract wait duration if mentioned
            import re
            wait_match = re.search(r'wait (\d+)', prompt.lower())
            duration = int(wait_match.group(1)) if wait_match else 2
            steps.append({
                "action": "wait",
                "duration": duration,
                "description": f"Wait for {duration} seconds"
            })
        
        if "screenshot" in prompt.lower():
            steps.append({
                "action": "screenshot",
                "description": "Take a screenshot"
            })
        
        if "go to" in prompt.lower() or "navigate" in prompt.lower():
            steps.append({
                "action": "navigate",
                "description": "Navigate to specified location"
            })
        
        # If no specific actions found, create a generic step
        if not steps:
            steps.append({
                "action": "execute",
                "description": f"Execute: {prompt}"
            })
        
        # Create the JSON response
        fallback_response = {
            "apps": apps,
            "steps": steps
        }
        
        return json.dumps(fallback_response, indent=2)

    async def test_single_prompt(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single prompt through the entire chain"""
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"📝 Prompt: {test_case['prompt']}")
        print(f"🎯 Difficulty: {test_case['difficulty']}")
        
        start_time = time.time()
        result = {
            "test_name": test_case["name"],
            "prompt": test_case["prompt"],
            "difficulty": test_case["difficulty"],
            "description": test_case["description"],
            "start_time": datetime.now().isoformat(),
            "success": False,
            "errors": [],
            "warnings": [],
            "plan": None,
            "execution_time": 0,
            "llm_response": None,
            "parsing_success": False
        }
        
        try:
            # Step 1: Generate plan using LLM
            print("  🔄 Step 1: Generating plan with LLM...")
            llm_start = time.time()
            
            plan_prompt = f"""
Create an automation plan for this user request: "{test_case['prompt']}"

Return ONLY a single COMPLETE JSON object with this exact structure:
{{
  "apps": ["app1", "app2"],
  "steps": [
    {{
      "action": "open_app",
      "app": "app_name",
      "description": "what this step does"
    }},
    {{
      "action": "wait",
      "duration": 2,
      "description": "wait for 2 seconds"
    }},
    {{
      "action": "screenshot",
      "description": "take a screenshot"
    }}
  ]
}}

CRITICAL: Make sure to complete the JSON structure with proper closing braces and brackets.
IMPORTANT: Return ONLY the JSON object, no other text, no explanations.
"""
            
            # Use generate_response (async generator)
            llm_chunks = []
            try:
                async for chunk in self.llm_service.generate_response_with_fallback(plan_prompt):
                    llm_chunks.append(chunk)
                llm_response = ''.join(llm_chunks)
                llm_time = time.time() - llm_start
                
                result["llm_response"] = llm_response
                result["llm_time"] = llm_time
                
                print(f"  ⏱️  LLM response time: {llm_time:.2f}s")
                print(f"  📄 LLM response length: {len(llm_response)} chars")
                print(f"  📄 LLM response preview: {llm_response[:200]}...")
                
            except Exception as llm_error:
                result["errors"].append(f"LLM generation failed: {str(llm_error)}")
                print(f"  ❌ LLM generation failed: {llm_error}")
                # Create a fallback response based on the prompt
                llm_response = self._create_fallback_response(test_case['prompt'])
                llm_time = time.time() - llm_start
                result["llm_response"] = llm_response
                result["llm_time"] = llm_time
                print(f"  🔄 Using fallback response")
            
            # Check if response seems incomplete
            if not llm_response.strip().endswith('}'):
                print(f"  ⚠️  LLM response appears incomplete, attempting to complete...")
                # Try to find the last complete object and close it
                if llm_response.count('{') > llm_response.count('}'):
                    missing_braces = llm_response.count('{') - llm_response.count('}')
                    llm_response += '}' * missing_braces
                    print(f"  🔧 Added {missing_braces} closing braces")
                if llm_response.count('[') > llm_response.count(']'):
                    missing_brackets = llm_response.count('[') - llm_response.count(']')
                    llm_response += ']' * missing_brackets
                    print(f"  🔧 Added {missing_brackets} closing brackets")
            
            # Step 2: Parse the plan
            print("  🔄 Step 2: Parsing LLM response...")
            parse_start = time.time()
            
            try:
                plan_dict = self._extract_plan_dict(llm_response, test_case["prompt"])
                plan = AutomationPlan.from_dict(plan_dict)
                parse_time = time.time() - parse_start
                result["parsing_success"] = True
                result["parse_time"] = parse_time
                result["plan"] = plan.to_dict()
                
                print(f"  ✅ Plan parsed successfully in {parse_time:.2f}s")
                print(f"  📋 Steps: {len(plan.steps)} steps")
                
            except Exception as parse_error:
                result["parsing_success"] = False
                result["errors"].append(f"Plan parsing failed: {str(parse_error)}")
                print(f"  ❌ Plan parsing failed: {parse_error}")
                print(f"  📄 Full LLM response: {llm_response}")
                
                # Try to create a fallback plan
                print("  🔄 Attempting fallback plan creation...")
                try:
                    fallback_plan_dict = self._fallback_plan_dict(test_case['prompt'])
                    plan = AutomationPlan.from_dict(fallback_plan_dict)
                    result["plan"] = plan.to_dict()
                    result["warnings"].append("Used fallback plan due to parsing failure")
                    print("  ✅ Fallback plan created successfully")
                except Exception as fallback_error:
                    result["errors"].append(f"Fallback plan creation failed: {str(fallback_error)}")
                    print(f"  ❌ Fallback plan creation failed: {fallback_error}")
            
            # Step 3: Execute the plan (if parsing was successful)
            if result["parsing_success"] or result["plan"]:
                print("  🔄 Step 3: Executing plan...")
                exec_start = time.time()
                
                try:
                    execution_result = await self.backend.execute_plan(plan if result["parsing_success"] else AutomationPlan.from_dict(result["plan"]))
                    exec_time = time.time() - exec_start
                    result["execution_time"] = exec_time
                    result["execution_result"] = execution_result
                    
                    print(f"  ✅ Plan executed successfully in {exec_time:.2f}s")
                    
                except Exception as exec_error:
                    result["errors"].append(f"Plan execution failed: {str(exec_error)}")
                    print(f"  ❌ Plan execution failed: {exec_error}")
            
            # Step 4: Validate results
            print("  🔄 Step 4: Validating results...")
            
            if result["plan"]:
                plan_steps = result["plan"].get("steps", [])
                expected_apps = test_case.get("expected_apps", [])
                
                # Check if expected apps are mentioned in step descriptions
                step_descriptions = [step.get("description", "").lower() for step in plan_steps]
                missing_apps = []
                for app in expected_apps:
                    if app.lower() not in " ".join(step_descriptions):
                        missing_apps.append(app)
                
                if missing_apps:
                    result["warnings"].append(f"Missing expected apps: {missing_apps}")
                    print(f"  ⚠️  Missing expected apps: {missing_apps}")
                else:
                    print("  ✅ All expected apps found in plan")
                
                # Check plan structure
                if len(plan_steps) == 0:
                    result["warnings"].append("Plan has no steps")
                    print("  ⚠️  Plan has no steps")
                else:
                    print(f"  ✅ Plan has {len(plan_steps)} steps")
            
            result["success"] = len(result["errors"]) == 0
            result["total_time"] = time.time() - start_time
            
            if result["success"]:
                print(f"  ✅ Test PASSED in {result['total_time']:.2f}s")
            else:
                print(f"  ❌ Test FAILED in {result['total_time']:.2f}s")
                print(f"  📋 Errors: {result['errors']}")
            
        except Exception as e:
            result["errors"].append(f"Unexpected error: {str(e)}")
            result["total_time"] = time.time() - start_time
            print(f"  ❌ Unexpected error: {e}")
            
        return result
    
    async def run_all_tests(self):
        """Run all test prompts"""
        print("🚀 Starting comprehensive chain testing...")
        print("=" * 60)
        
        await self.setup()
        
        test_prompts = self.get_test_prompts()
        
        for i, test_case in enumerate(test_prompts, 1):
            print(f"\n{'='*20} Test {i}/{len(test_prompts)} {'='*20}")
            result = await self.test_single_prompt(test_case)
            self.test_results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        await self.cleanup()
        
        # Generate comprehensive report
        self.generate_report()
        
    def generate_report(self):
        """Generate a comprehensive test report"""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("="*60)
        
        # Summary statistics
        total_tests = len(self.test_results)
        successful_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - successful_tests
        
        print(f"\n📈 SUMMARY:")
        print(f"  Total tests: {total_tests}")
        print(f"  Successful: {successful_tests}")
        print(f"  Failed: {failed_tests}")
        print(f"  Success rate: {(successful_tests/total_tests)*100:.1f}%")
        
        # Performance statistics
        total_time = sum(r["total_time"] for r in self.test_results)
        avg_time = total_time / total_tests if total_tests > 0 else 0
        
        llm_times = [r.get("llm_time", 0) for r in self.test_results if r.get("llm_time")]
        avg_llm_time = sum(llm_times) / len(llm_times) if llm_times else 0
        
        parse_times = [r.get("parse_time", 0) for r in self.test_results if r.get("parse_time")]
        avg_parse_time = sum(parse_times) / len(parse_times) if parse_times else 0
        
        print(f"\n⏱️  PERFORMANCE:")
        print(f"  Total test time: {total_time:.2f}s")
        print(f"  Average test time: {avg_time:.2f}s")
        print(f"  Average LLM time: {avg_llm_time:.2f}s")
        print(f"  Average parse time: {avg_parse_time:.2f}s")
        
        # Detailed results by difficulty
        print(f"\n📋 DETAILED RESULTS BY DIFFICULTY:")
        difficulties = {}
        for result in self.test_results:
            diff = result["difficulty"]
            if diff not in difficulties:
                difficulties[diff] = {"total": 0, "success": 0, "errors": []}
            difficulties[diff]["total"] += 1
            if result["success"]:
                difficulties[diff]["success"] += 1
            difficulties[diff]["errors"].extend(result["errors"])
        
        for diff, stats in difficulties.items():
            success_rate = (stats["success"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            print(f"  {diff}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
            if stats["errors"]:
                print(f"    Errors: {len(set(stats['errors']))} unique errors")
        
        # Failed tests details
        failed_results = [r for r in self.test_results if not r["success"]]
        if failed_results:
            print(f"\n❌ FAILED TESTS:")
            for result in failed_results:
                print(f"  {result['test_name']}:")
                print(f"    Prompt: {result['prompt']}")
                print(f"    Errors: {result['errors']}")
                if result["warnings"]:
                    print(f"    Warnings: {result['warnings']}")
        
        # Save detailed report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"comprehensive_test_report_{timestamp}.json"
        
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "successful_tests": successful_tests,
                    "failed_tests": failed_tests,
                    "success_rate": (successful_tests/total_tests)*100 if total_tests > 0 else 0,
                    "total_time": total_time,
                    "average_time": avg_time,
                    "average_llm_time": avg_llm_time,
                    "average_parse_time": avg_parse_time
                },
                "results": self.test_results
            }, f, indent=2)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        if successful_tests == total_tests:
            print("  🎉 EXCELLENT: All tests passed!")
        elif successful_tests >= total_tests * 0.8:
            print("  ✅ GOOD: Most tests passed, minor issues to address")
        elif successful_tests >= total_tests * 0.6:
            print("  ⚠️  FAIR: Some tests failed, needs improvement")
        else:
            print("  ❌ POOR: Many tests failed, significant issues to address")
        
        print("\n" + "="*60)

async def main():
    """Main test runner"""
    tester = ComprehensiveChainTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 