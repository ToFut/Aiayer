#!/usr/bin/env python3
"""
Test All Prompts - Verify all prompts generate proper plans
"""

import asyncio
import time
import sys
import os
from typing import Dict, Any, List

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_plan_creator import LLMPlanCreator

class AllPromptsTester:
    """Test that all prompts generate proper plans"""
    
    def __init__(self):
        self.plan_creator = LLMPlanCreator()
    
    def get_test_prompts(self) -> List[Dict[str, Any]]:
        """Get comprehensive test prompts"""
        return [
            # Easy prompts
            {"prompt": "Search Segev in Google", "difficulty": "Easy", "expected_steps": 4},
            {"prompt": "Open Calculator", "difficulty": "Easy", "expected_steps": 3},
            {"prompt": "Click on the center of the screen", "difficulty": "Easy", "expected_steps": 2},
            {"prompt": "Open Safari", "difficulty": "Easy", "expected_steps": 3},
            
            # Medium prompts
            {"prompt": "Open TextEdit and write 'Hello World'", "difficulty": "Medium", "expected_steps": 4},
            {"prompt": "Open Finder and navigate to Documents", "difficulty": "Medium", "expected_steps": 4},
            {"prompt": "Open Calculator and calculate 15 * 23", "difficulty": "Medium", "expected_steps": 4},
            {"prompt": "Open Terminal and run 'ls -la'", "difficulty": "Medium", "expected_steps": 4},
            
            # Hard prompts
            {"prompt": "Open Safari, go to google.com, and search for 'Python programming'", "difficulty": "Hard", "expected_steps": 6},
            {"prompt": "Open System Preferences and go to Security settings", "difficulty": "Hard", "expected_steps": 4},
            {"prompt": "Open Calculator, calculate 100 / 4, then multiply by 7", "difficulty": "Hard", "expected_steps": 5},
            {"prompt": "Open TextEdit, write a note, and save it", "difficulty": "Hard", "expected_steps": 5},
            
            # Complex prompts
            {"prompt": "Open Safari, go to apple.com, click on iPhone, and add to cart", "difficulty": "Complex", "expected_steps": 8},
            {"prompt": "Open Terminal, navigate to Documents folder, and list all files", "difficulty": "Complex", "expected_steps": 6},
            {"prompt": "Open Finder, create a new folder called 'Test', and copy a file into it", "difficulty": "Complex", "expected_steps": 7},
            {"prompt": "Open Calculator, calculate the area of a circle with radius 5", "difficulty": "Complex", "expected_steps": 6}
        ]
    
    async def test_single_prompt(self, prompt_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single prompt"""
        prompt = prompt_data["prompt"]
        difficulty = prompt_data["difficulty"]
        expected_steps = prompt_data["expected_steps"]
        
        print(f"\n🧪 Testing: '{prompt}' ({difficulty})")
        
        # Test plan creation
        t0 = time.time()
        try:
            result = await self.plan_creator.create_llm_plan(prompt, "test_session")
            t1 = time.time()
            
            success = result.get("success", False)
            plan = result.get("plan", {})
            steps = plan.get("steps", [])
            
            print(f"⏱️ Time: {t1-t0:.2f}s")
            print(f"✅ Success: {success}")
            print(f"📋 Plan: {plan.get('title', 'No title')}")
            print(f"🔢 Steps: {len(steps)} (expected: {expected_steps})")
            
            # Print steps
            for i, step in enumerate(steps, 1):
                desc = step.get("description", "Unknown")
                action = step.get("action_type", "Unknown")
                value = step.get("value", "")
                target = step.get("target", "")
                confidence = step.get("confidence", 0)
                
                print(f"  {i}. {desc} ({action}) [{confidence:.1%}]")
                if value:
                    print(f"     Value: '{value}'")
                if target:
                    print(f"     Target: '{target}'")
            
            # Validate plan quality
            quality_score = self._calculate_plan_quality(steps, expected_steps)
            
            return {
                "prompt": prompt,
                "difficulty": difficulty,
                "success": success,
                "creation_time": t1 - t0,
                "steps_count": len(steps),
                "expected_steps": expected_steps,
                "quality_score": quality_score,
                "plan": plan
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return {
                "prompt": prompt,
                "difficulty": difficulty,
                "success": False,
                "error": str(e),
                "creation_time": 0,
                "steps_count": 0,
                "expected_steps": expected_steps,
                "quality_score": 0
            }
    
    def _calculate_plan_quality(self, steps: List[Dict], expected_steps: int) -> float:
        """Calculate plan quality score"""
        if not steps:
            return 0.0
        
        # Base score for having steps
        score = 0.3
        
        # Score for step count (closer to expected is better)
        step_count = len(steps)
        if step_count >= expected_steps:
            score += 0.3
        elif step_count >= expected_steps * 0.7:  # At least 70% of expected
            score += 0.2
        elif step_count >= expected_steps * 0.5:  # At least 50% of expected
            score += 0.1
        
        # Score for action types
        action_types = set(step.get("action_type", "") for step in steps)
        if "hotkey" in action_types:
            score += 0.2
        if "type_text" in action_types:
            score += 0.2
        if "press_key" in action_types:
            score += 0.1
        if "wait" in action_types:
            score += 0.1
        
        # Score for confidence
        avg_confidence = sum(step.get("confidence", 0) for step in steps) / len(steps)
        score += avg_confidence * 0.2
        
        return min(score, 1.0)
    
    async def run_comprehensive_test(self):
        """Run comprehensive test of all prompts"""
        print("🚀 Testing All Prompts - Comprehensive Plan Generation")
        print("=" * 80)
        
        test_prompts = self.get_test_prompts()
        results = []
        
        for i, prompt_data in enumerate(test_prompts, 1):
            print(f"\n📝 Test {i}/{len(test_prompts)}")
            result = await self.test_single_prompt(prompt_data)
            results.append(result)
            
            # Print quality score
            if result["success"]:
                quality = result["quality_score"]
                print(f"📊 Quality Score: {quality:.1%}")
                if quality >= 0.8:
                    print("✅ Excellent plan!")
                elif quality >= 0.6:
                    print("⚠️ Good plan")
                else:
                    print("❌ Poor plan")
            
            print("-" * 50)
        
        # Generate summary
        await self.generate_summary(results)
    
    async def generate_summary(self, results: List[Dict[str, Any]]):
        """Generate comprehensive summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(results)
        successful_plans = sum(1 for r in results if r["success"])
        avg_time = sum(r["creation_time"] for r in results) / total_tests
        avg_quality = sum(r["quality_score"] for r in results if r["success"]) / successful_plans if successful_plans > 0 else 0
        
        print(f"📈 Overall Statistics:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Successful Plans: {successful_plans}/{total_tests} ({successful_plans/total_tests:.1%})")
        print(f"   Average Creation Time: {avg_time:.2f}s")
        print(f"   Average Quality Score: {avg_quality:.1%}")
        
        # Difficulty breakdown
        difficulty_stats = {}
        for result in results:
            difficulty = result["difficulty"]
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {"count": 0, "success": 0, "avg_time": 0, "avg_quality": 0}
            
            difficulty_stats[difficulty]["count"] += 1
            if result["success"]:
                difficulty_stats[difficulty]["success"] += 1
            
            difficulty_stats[difficulty]["avg_time"] += result["creation_time"]
            difficulty_stats[difficulty]["avg_quality"] += result["quality_score"]
        
        print(f"\n🎯 Difficulty Breakdown:")
        for difficulty, stats in difficulty_stats.items():
            count = stats["count"]
            success_rate = stats["success"] / count
            avg_time = stats["avg_time"] / count
            avg_quality = stats["avg_quality"] / count
            
            print(f"   {difficulty}: {stats['success']}/{count} ({success_rate:.1%}) - {avg_time:.2f}s avg - {avg_quality:.1%} quality")
        
        # Best and worst plans
        successful_results = [r for r in results if r["success"]]
        if successful_results:
            best_result = max(successful_results, key=lambda x: x["quality_score"])
            worst_result = min(successful_results, key=lambda x: x["quality_score"])
            
            print(f"\n🏆 Best Plan:")
            print(f"   Prompt: '{best_result['prompt']}'")
            print(f"   Quality: {best_result['quality_score']:.1%}")
            print(f"   Time: {best_result['creation_time']:.2f}s")
            
            print(f"\n⚠️ Worst Plan:")
            print(f"   Prompt: '{worst_result['prompt']}'")
            print(f"   Quality: {worst_result['quality_score']:.1%}")
            print(f"   Time: {worst_result['creation_time']:.2f}s")
        
        print("\n" + "=" * 80)
        print("✅ All Prompts Test Complete!")
        print("=" * 80)

async def main():
    """Main test function"""
    tester = AllPromptsTester()
    await tester.run_comprehensive_test()

if __name__ == "__main__":
    asyncio.run(main()) 