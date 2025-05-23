#!/usr/bin/env python3
"""
Debug UI Workflow Execution
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enterprise_workflow_engine import TaskAnalyzer, execute_agent_workflow

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_workflow():
    """Debug workflow execution"""
    
    print("🔍 Debugging UI Workflow Execution")
    print("=" * 50)
    
    # Test the task analyzer directly
    analyzer = TaskAnalyzer()
    
    test_queries = [
        "click at position 100 100",
        "type hello world", 
        "press the return key",
        "move mouse to 200 300"
    ]
    
    for query in test_queries:
        print(f"\n📝 Testing: {query}")
        print("-" * 30)
        
        # Test task analysis
        analysis = await analyzer.analyze_request(query)
        print(f"Category: {analysis['task_category']}")
        print(f"Confidence: {analysis['confidence']:.3f}")
        print(f"Executable: {analysis['executable']}")
        print(f"Detected Actions: {analysis['detected_actions']}")
        
        # Test full workflow if executable
        if analysis['executable']:
            print("\n🚀 Testing full workflow execution...")
            try:
                result = await execute_agent_workflow(query, {"test": True})
                print(f"Workflow Success: {result['success']}")
                if result['success']:
                    exec_result = result.get('execution_result', {})
                    print(f"Steps: {exec_result.get('completed_steps', 0)}/{exec_result.get('total_steps', 0)}")
                else:
                    print(f"Workflow Error: {result.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"Workflow Exception: {e}")
        else:
            print("❌ Not executable - confidence too low")

if __name__ == "__main__":
    asyncio.run(debug_workflow())