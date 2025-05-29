#!/usr/bin/env python3
"""
Test cursor + write plan
"""

import asyncio
import logging
from intelligent_automation_planner import intelligent_planner

logging.basicConfig(level=logging.INFO)

async def test():
    message = "open curser and write SEGEV"
    
    # Test intent analysis
    intent = await intelligent_planner.analyze_user_intent(message)
    print(f"Intent: {intent}")
    
    # Test plan creation
    plan = await intelligent_planner.create_intelligent_plan(message, "test")
    
    print(f"Plan: {plan.title} - {len(plan.steps)} steps")
    for i, step in enumerate(plan.steps, 1):
        print(f"  {i}. {step.description} ({step.action_type})")
        if step.value:
            print(f"     → Value: {step.value}")
        if step.target:
            print(f"     → Target: {step.target}")

if __name__ == "__main__":
    asyncio.run(test())