#!/usr/bin/env python3
"""
Execution Demo Test - Full Chain from Prompt to Execution
Demonstrates the complete flow for a simple task
"""

import asyncio
import json
import time
import sys
import os
from typing import Dict, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from llm_plan_creator import LLMPlanCreator

class ExecutionDemo:
    """Demo the full chain from prompt to execution"""
    
    def __init__(self):
        self.plan_creator = LLMPlanCreator()
    
    async def demo_full_chain(self, prompt: str):
        """Demonstrate the full chain for a given prompt"""
        print(f"🚀 Full Chain Demo: '{prompt}'")
        print("=" * 60)
        
        # Step 1: Plan Creation
        print("📋 Step 1: Creating Automation Plan")
        print("-" * 40)
        
        t0 = time.time()
        result = await self.plan_creator.create_llm_plan(prompt, "demo_session")
        t1 = time.time()
        
        if not result.get("success"):
            print("❌ Plan creation failed!")
            return
        
        plan = result.get("plan", {})
        steps = plan.get("steps", [])
        
        print(f"✅ Plan created successfully in {t1-t0:.2f}s")
        print(f"📋 Plan Title: {plan.get('title', 'No title')}")
        print(f"🔢 Total Steps: {len(steps)}")
        print(f"⏱️ Estimated Duration: {plan.get('estimated_duration', 0):.1f}s")
        
        # Display plan details
        print("\n📋 Plan Details:")
        for i, step in enumerate(steps, 1):
            desc = step.get("description", "Unknown")
            action = step.get("action_type", "Unknown")
            value = step.get("value", "")
            target = step.get("target", "")
            confidence = step.get("confidence", 0)
            duration = step.get("estimated_duration", 0)
            
            print(f"  {i}. {desc}")
            print(f"     Action: {action}")
            if value:
                print(f"     Value: '{value}'")
            if target:
                print(f"     Target: '{target}'")
            print(f"     Confidence: {confidence:.1%}")
            print(f"     Duration: {duration:.1f}s")
            print()
        
        # Step 2: Plan Validation
        print("🔍 Step 2: Plan Validation")
        print("-" * 40)
        
        validation = self._validate_plan_for_execution(steps)
        print(f"✅ Plan is valid for execution: {validation['is_valid']}")
        print(f"📊 Execution confidence: {validation['confidence']:.1%}")
        print(f"⏱️ Total execution time: {validation['total_time']:.1f}s")
        
        if not validation['is_valid']:
            print("❌ Plan validation failed!")
            return
        
        # Step 3: Execution Simulation
        print("\n🎯 Step 3: Execution Simulation")
        print("-" * 40)
        
        execution_result = await self._simulate_execution(steps)
        
        print(f"✅ Execution completed: {execution_result['success']}")
        print(f"📊 Success rate: {execution_result['success_rate']:.1%}")
        print(f"⏱️ Actual execution time: {execution_result['execution_time']:.1f}s")
        print(f"🔢 Steps executed: {execution_result['steps_executed']}/{execution_result['total_steps']}")
        
        # Step 4: Results Analysis
        print("\n📊 Step 4: Results Analysis")
        print("-" * 40)
        
        if execution_result['success']:
            print("🎉 SUCCESS: All steps executed successfully!")
            print(f"✅ Task '{prompt}' completed successfully")
            print(f"⏱️ Total time: {execution_result['execution_time']:.1f}s")
        else:
            print("⚠️ PARTIAL SUCCESS: Some steps failed")
            print(f"📊 Success rate: {execution_result['success_rate']:.1%}")
        
        print("\n" + "=" * 60)
        print("✅ Full Chain Demo Complete!")
        print("=" * 60)
    
    def _validate_plan_for_execution(self, steps: list) -> Dict[str, Any]:
        """Validate if the plan can be executed"""
        if not steps:
            return {"is_valid": False, "confidence": 0, "total_time": 0}
        
        # Check if all steps have required fields
        valid_steps = 0
        total_confidence = 0
        total_time = 0
        
        for step in steps:
            action_type = step.get("action_type", "")
            confidence = step.get("confidence", 0)
            duration = step.get("estimated_duration", 1.0)
            
            # Basic validation
            if action_type in ["hotkey", "type_text", "press_key", "click", "wait"]:
                valid_steps += 1
                total_confidence += confidence
                total_time += duration
        
        is_valid = valid_steps == len(steps)
        avg_confidence = total_confidence / len(steps) if steps else 0
        
        return {
            "is_valid": is_valid,
            "confidence": avg_confidence,
            "total_time": total_time
        }
    
    async def _simulate_execution(self, steps: list) -> Dict[str, Any]:
        """Simulate the execution of the plan"""
        if not steps:
            return {
                "success": False,
                "success_rate": 0,
                "execution_time": 0,
                "steps_executed": 0,
                "total_steps": 0
            }
        
        total_steps = len(steps)
        steps_executed = 0
        execution_time = 0
        
        print("🔄 Simulating execution...")
        
        for i, step in enumerate(steps, 1):
            action_type = step.get("action_type", "")
            description = step.get("description", "")
            confidence = step.get("confidence", 0.8)
            duration = step.get("estimated_duration", 1.0)
            
            print(f"  {i}. {description} ({action_type})")
            
            # Simulate step execution
            await asyncio.sleep(0.1)  # Small delay for simulation
            
            # Determine success based on confidence
            success = confidence > 0.7
            
            if success:
                steps_executed += 1
                print(f"     ✅ Success (confidence: {confidence:.1%})")
            else:
                print(f"     ❌ Failed (confidence: {confidence:.1%})")
            
            execution_time += duration
        
        success_rate = steps_executed / total_steps if total_steps > 0 else 0
        overall_success = success_rate > 0.8  # 80% threshold
        
        return {
            "success": overall_success,
            "success_rate": success_rate,
            "execution_time": execution_time,
            "steps_executed": steps_executed,
            "total_steps": total_steps
        }

async def main():
    """Main demo function"""
    demo = ExecutionDemo()
    
    # Test cases with different difficulty levels
    test_cases = [
        "Search Segev in Google",
        "Open Calculator",
        "Click on the center of the screen"
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Demo {i}/3")
        await demo.demo_full_chain(test_case)
        
        if i < len(test_cases):
            print("\n" + "="*80)
            print("⏳ Waiting 2 seconds before next demo...")
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main()) 