#!/usr/bin/env python3
"""
Full Chain Test - Plan Creation Only
Tests 10 different prompts with varying difficulty levels
"""

import asyncio
import json
import time
import sys
import os
from typing import Dict, Any, List

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_plan_creator import LLMPlanCreator

class FullChainTester:
    """Test the full chain from user prompt to plan creation"""
    
    def __init__(self):
        self.plan_creator = LLMPlanCreator()
        self.test_results = []
    
    def get_test_prompts(self) -> List[Dict[str, Any]]:
        """Get 10 test prompts with varying difficulty levels"""
        return [
            {
                "prompt": "Search Segev in Google",
                "difficulty": "Easy",
                "expected_type": "web_search",
                "expected_apps": ["Safari"],
                "description": "Simple web search task"
            },
            {
                "prompt": "Open Calculator and calculate 15 * 23",
                "difficulty": "Easy",
                "expected_type": "app_launch",
                "expected_apps": ["Calculator"],
                "description": "App launch with basic interaction"
            },
            {
                "prompt": "Open Safari and go to apple.com",
                "difficulty": "Easy",
                "expected_type": "web_navigation",
                "expected_apps": ["Safari"],
                "description": "Web navigation task"
            },
            {
                "prompt": "Open TextEdit and write 'Hello World'",
                "difficulty": "Medium",
                "expected_type": "text_input",
                "expected_apps": ["TextEdit"],
                "description": "Text input task"
            },
            {
                "prompt": "Click on the center of the screen",
                "difficulty": "Easy",
                "expected_type": "ui_interaction",
                "expected_apps": [],
                "description": "Basic UI interaction"
            },
            {
                "prompt": "Open Finder and navigate to Documents folder",
                "difficulty": "Medium",
                "expected_type": "file_operation",
                "expected_apps": ["Finder"],
                "description": "File system navigation"
            },
            {
                "prompt": "Open Terminal and run 'ls -la'",
                "difficulty": "Hard",
                "expected_type": "command_execution",
                "expected_apps": ["Terminal"],
                "description": "Command line task"
            },
            {
                "prompt": "Open System Preferences and go to Security settings",
                "difficulty": "Hard",
                "expected_type": "system_configuration",
                "expected_apps": ["System Preferences"],
                "description": "System configuration task"
            },
            {
                "prompt": "Open Safari, go to google.com, and search for 'Python programming'",
                "difficulty": "Hard",
                "expected_type": "complex_web_task",
                "expected_apps": ["Safari"],
                "description": "Multi-step web task"
            },
            {
                "prompt": "Open Calculator, calculate 100 / 4, then multiply by 7",
                "difficulty": "Medium",
                "expected_type": "complex_calculation",
                "expected_apps": ["Calculator"],
                "description": "Multi-step calculation"
            }
        ]
    
    async def test_plan_creation(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test plan creation for a single prompt"""
        prompt = prompt_data["prompt"]
        difficulty = prompt_data["difficulty"]
        
        print(f"\n🧪 Testing: '{prompt}' ({difficulty})")
        
        # Test plan creation
        t0 = time.time()
        try:
            result = await self.plan_creator.create_llm_plan(prompt, "test_session")
            t1 = time.time()
            
            success = result.get("success", False)
            plan = result.get("plan", {})
            steps = plan.get("steps", [])
            
            print(f"⏱️ Plan creation time: {t1-t0:.2f}s")
            print(f"✅ Success: {success}")
            print(f"📋 Plan: {plan.get('title', 'No title')}")
            print(f"🔢 Steps: {len(steps)}")
            
            # Print steps for verification
            for i, step in enumerate(steps, 1):
                desc = step.get("description", "Unknown")
                action = step.get("action_type", "Unknown")
                value = step.get("value", "")
                target = step.get("target", "")
                print(f"  {i}. {desc} ({action})")
                if value:
                    print(f"     Value: '{value}'")
                if target:
                    print(f"     Target: '{target}'")
            
            # Validate plan quality
            validation = self._validate_plan(prompt_data, plan)
            
            return {
                "prompt": prompt,
                "difficulty": difficulty,
                "success": success,
                "creation_time": t1 - t0,
                "steps_count": len(steps),
                "plan": plan,
                "validation": validation
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "prompt": prompt,
                "difficulty": difficulty,
                "success": False,
                "error": str(e),
                "creation_time": 0,
                "steps_count": 0
            }
    
    def _validate_plan(self, prompt_data: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if the plan matches the expected requirements"""
        steps = plan.get("steps", [])
        expected_type = prompt_data["expected_type"]
        expected_apps = prompt_data["expected_apps"]
        
        validation = {
            "has_required_steps": len(steps) > 0,
            "has_hotkey_step": False,
            "has_type_text_step": False,
            "has_press_key_step": False,
            "has_wait_step": False,
            "has_click_step": False,
            "step_descriptions": [],
            "action_types": [],
            "confidence_scores": []
        }
        
        for step in steps:
            action_type = step.get("action_type", "")
            description = step.get("description", "")
            confidence = step.get("confidence", 0)
            
            validation["action_types"].append(action_type)
            validation["step_descriptions"].append(description)
            validation["confidence_scores"].append(confidence)
            
            if action_type == "hotkey":
                validation["has_hotkey_step"] = True
            elif action_type == "type_text":
                validation["has_type_text_step"] = True
            elif action_type == "press_key":
                validation["has_press_key_step"] = True
            elif action_type == "wait":
                validation["has_wait_step"] = True
            elif action_type == "click":
                validation["has_click_step"] = True
        
        # Check if plan matches expected type
        validation["matches_expected_type"] = self._check_type_match(expected_type, steps)
        
        # Check if plan includes expected apps
        validation["includes_expected_apps"] = self._check_app_inclusion(expected_apps, steps)
        
        # Calculate overall quality score
        validation["quality_score"] = self._calculate_quality_score(validation)
        
        return validation
    
    def _check_type_match(self, expected_type: str, steps: List[Dict]) -> bool:
        """Check if plan steps match expected task type"""
        if expected_type == "web_search":
            return any("safari" in step.get("description", "").lower() for step in steps)
        elif expected_type == "app_launch":
            return any("hotkey" in step.get("action_type", "") for step in steps)
        elif expected_type == "ui_interaction":
            return any("click" in step.get("action_type", "") for step in steps)
        elif expected_type == "text_input":
            return any("type_text" in step.get("action_type", "") for step in steps)
        return True
    
    def _check_app_inclusion(self, expected_apps: List[str], steps: List[Dict]) -> bool:
        """Check if plan includes expected applications"""
        if not expected_apps:
            return True
        
        step_descriptions = " ".join([step.get("description", "").lower() for step in steps])
        return any(app.lower() in step_descriptions for app in expected_apps)
    
    def _calculate_quality_score(self, validation: Dict[str, Any]) -> float:
        """Calculate overall plan quality score"""
        score = 0.0
        
        # Base score for having steps
        if validation["has_required_steps"]:
            score += 0.3
        
        # Score for having appropriate action types
        if validation["has_hotkey_step"]:
            score += 0.2
        if validation["has_type_text_step"]:
            score += 0.2
        if validation["has_press_key_step"]:
            score += 0.1
        if validation["has_wait_step"]:
            score += 0.1
        if validation["has_click_step"]:
            score += 0.1
        
        # Score for matching expected type
        if validation["matches_expected_type"]:
            score += 0.3
        
        # Score for including expected apps
        if validation["includes_expected_apps"]:
            score += 0.2
        
        # Score for confidence (average confidence of steps)
        if validation["confidence_scores"]:
            avg_confidence = sum(validation["confidence_scores"]) / len(validation["confidence_scores"])
            score += avg_confidence * 0.2
        
        return min(score, 1.0)
    
    async def run_full_test(self):
        """Run the complete test suite"""
        print("🚀 Starting Full Chain Test Suite")
        print("=" * 60)
        
        # Get test prompts
        test_prompts = self.get_test_prompts()
        
        # Test each prompt
        for i, prompt_data in enumerate(test_prompts, 1):
            print(f"\n📝 Test {i}/10: {prompt_data['description']}")
            print(f"   Difficulty: {prompt_data['difficulty']}")
            print(f"   Expected Type: {prompt_data['expected_type']}")
            print(f"   Expected Apps: {prompt_data['expected_apps']}")
            
            # Test plan creation
            result = await self.test_plan_creation(prompt_data)
            
            # Store result
            self.test_results.append(result)
            
            # Print validation results
            if "validation" in result:
                validation = result["validation"]
                print(f"📊 Plan Quality Score: {validation['quality_score']:.1%}")
                print(f"   Matches Expected Type: {validation['matches_expected_type']}")
                print(f"   Includes Expected Apps: {validation['includes_expected_apps']}")
            
            print("-" * 40)
        
        # Generate summary report
        await self.generate_summary_report()
    
    async def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        print("\n" + "=" * 60)
        print("📊 FULL CHAIN TEST SUMMARY REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        successful_plans = sum(1 for r in self.test_results if r["success"])
        avg_creation_time = sum(r["creation_time"] for r in self.test_results) / total_tests
        
        print(f"📈 Overall Statistics:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful Plans: {successful_plans}/{total_tests} ({successful_plans/total_tests:.1%})")
        print(f"   Average Creation Time: {avg_creation_time:.2f}s")
        
        # Difficulty breakdown
        difficulty_stats = {}
        for result in self.test_results:
            difficulty = result["difficulty"]
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {"count": 0, "success": 0, "avg_time": 0, "avg_quality": 0}
            
            difficulty_stats[difficulty]["count"] += 1
            if result["success"]:
                difficulty_stats[difficulty]["success"] += 1
            
            difficulty_stats[difficulty]["avg_time"] += result["creation_time"]
            
            if "validation" in result:
                difficulty_stats[difficulty]["avg_quality"] += result["validation"]["quality_score"]
        
        print(f"\n🎯 Difficulty Breakdown:")
        for difficulty, stats in difficulty_stats.items():
            count = stats["count"]
            success_rate = stats["success"] / count
            avg_time = stats["avg_time"] / count
            avg_quality = stats["avg_quality"] / count
            
            print(f"   {difficulty}: {stats['success']}/{count} ({success_rate:.1%}) - {avg_time:.2f}s avg - {avg_quality:.1%} quality")
        
        # Best and worst performing tests
        successful_results = [r for r in self.test_results if r["success"]]
        if successful_results:
            best_result = max(successful_results, key=lambda x: x.get("validation", {}).get("quality_score", 0))
            worst_result = min(successful_results, key=lambda x: x.get("validation", {}).get("quality_score", 0))
            
            print(f"\n🏆 Best Performing Test:")
            print(f"   Prompt: '{best_result['prompt']}'")
            print(f"   Quality Score: {best_result['validation']['quality_score']:.1%}")
            print(f"   Creation Time: {best_result['creation_time']:.2f}s")
            
            print(f"\n⚠️ Worst Performing Test:")
            print(f"   Prompt: '{worst_result['prompt']}'")
            print(f"   Quality Score: {worst_result['validation']['quality_score']:.1%}")
            print(f"   Creation Time: {worst_result['creation_time']:.2f}s")
        
        # Action type analysis
        all_action_types = []
        for result in self.test_results:
            if "validation" in result:
                all_action_types.extend(result["validation"]["action_types"])
        
        action_type_counts = {}
        for action_type in all_action_types:
            action_type_counts[action_type] = action_type_counts.get(action_type, 0) + 1
        
        print(f"\n🔧 Action Type Usage:")
        for action_type, count in sorted(action_type_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = count / len(all_action_types) * 100
            print(f"   {action_type}: {count} times ({percentage:.1f}%)")
        
        print("\n" + "=" * 60)
        print("✅ Full Chain Test Complete!")
        print("=" * 60)

async def main():
    """Main test function"""
    tester = FullChainTester()
    await tester.run_full_test()

if __name__ == "__main__":
    asyncio.run(main()) 