#!/usr/bin/env python3
"""
Test Fixed UI Workflow
Verify that UI automation now works with improved confidence
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enterprise_workflow_engine import TaskAnalyzer, execute_agent_workflow

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_fixed_workflow():
    """Test the fixed workflow execution"""
    
    print("🔧 Testing Fixed UI Workflow Execution")
    print("=" * 50)
    
    analyzer = TaskAnalyzer()
    
    test_cases = [
        "click at position 100 100",
        "type hello world", 
        "press the return key",
        "click and type test message"
    ]
    
    for query in test_cases:
        print(f"\n📋 Testing: {query}")
        print("-" * 30)
        
        # Test analysis
        analysis = await analyzer.analyze_request(query)
        print(f"Category: {analysis['task_category']}")
        print(f"Confidence: {analysis['confidence']:.3f}")
        print(f"Executable: {analysis['executable']}")
        
        # Test execution if executable
        if analysis['executable']:
            print("🚀 Executing workflow...")
            try:
                result = await execute_agent_workflow(query, {"test": True})
                print(f"Success: {result['success']}")
                if result['success']:
                    exec_result = result.get('execution_result', {})
                    completed = exec_result.get('completed_steps', 0)
                    total = exec_result.get('total_steps', 0)
                    print(f"Steps: {completed}/{total}")
                    print("✅ WORKFLOW EXECUTED!")
                else:
                    print(f"Error: {result.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"Exception: {e}")
        else:
            print("❌ Not executable")

if __name__ == "__main__":
    asyncio.run(test_fixed_workflow())