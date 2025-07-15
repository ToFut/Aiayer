#!/usr/bin/env python3
"""
Simple Test for Complete AI System
Quick test to verify all components are working
"""

import asyncio
import sys
import time
from pathlib import Path

# Add Aiayer to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_simple():
    """Simple test of the complete AI system"""
    print("🧪 Simple Test of Complete AI System")
    print("=" * 50)
    
    try:
        # Test 1: Check if RPA server is running
        print("1. Testing RPA Server Connection...")
        import requests
        try:
            response = requests.get("http://localhost:16901/", timeout=5)
            if response.status_code == 200:
                print("   ✅ RPA Server is running")
            else:
                print(f"   ❌ RPA Server returned status {response.status_code}")
        except Exception as e:
            print(f"   ❌ RPA Server connection failed: {e}")
            print("   💡 Start RPA server with: cd RPA_AVEN/helper && go run *.go")
            return False
        
        # Test 2: Test UI Understanding
        print("2. Testing UI Understanding...")
        try:
            from neural_ui_detector import NeuralUIDetector
            detector = NeuralUIDetector()
            result = await detector.detect_elements()
            print(f"   ✅ Neural UI Detector: {len(result.elements)} elements detected")
        except Exception as e:
            print(f"   ❌ Neural UI Detector failed: {e}")
        
        # Test 3: Test Smart Planner
        print("3. Testing Smart Planner...")
        try:
            from universal_smart_planner import UniversalSmartPlanner
            planner = UniversalSmartPlanner()
            plan = await planner.create_universal_plan("Open Calculator", "test_session")
            print(f"   ✅ Smart Planner: {len(plan.steps)} steps created")
        except Exception as e:
            print(f"   ❌ Smart Planner failed: {e}")
        
        # Test 4: Test Brain Router
        print("4. Testing Brain Router...")
        try:
            from brain.core.brain_router import get_brain_router
            router = await get_brain_router()
            print("   ✅ Brain Router initialized")
        except Exception as e:
            print(f"   ❌ Brain Router failed: {e}")
        
        # Test 5: Test Memory System
        print("5. Testing Memory System...")
        try:
            from memory.task_memory_manager import initialize as init_task_memory
            task_memory = await init_task_memory()
            print("   ✅ Task Memory Manager initialized")
        except Exception as e:
            print(f"   ❌ Task Memory Manager failed: {e}")
        
        # Test 6: Test Complete System Integration
        print("6. Testing Complete System Integration...")
        try:
            from integration.complete_ai_system import initialize_complete_system
            system = await initialize_complete_system()
            print("   ✅ Complete AI System initialized")
            
            # Test UI understanding
            ui_state = await system.understand_ui()
            print(f"   📊 UI Elements: {len(ui_state.ui_elements)}")
            print(f"   📱 Active Apps: {ui_state.active_applications}")
            
            # Test action suggestions
            suggestions = await system.suggest_actions("Open Calculator")
            print(f"   🎯 Suggestions: {len(suggestions)} generated")
            
            if suggestions:
                print(f"   🏆 Top suggestion: {suggestions[0].description}")
                print(f"   📈 Confidence: {suggestions[0].confidence:.2f}")
            
            # Test execution (if RPA server is available)
            if suggestions:
                result = await system.execute_action(suggestions[0])
                print(f"   ⚡ Execution: {result.success}")
                print(f"   ⏱️ Time: {result.execution_time:.2f}s")
            
            # Get system stats
            stats = system.get_system_stats()
            print(f"   📊 Stats: {stats['ui_analyses']} analyses, {stats['executions']} executions")
            
        except Exception as e:
            print(f"   ❌ Complete System Integration failed: {e}")
            import traceback
            traceback.print_exc()
        
        print("=" * 50)
        print("✅ Simple test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_simple()) 