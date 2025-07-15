#!/usr/bin/env python3
"""
Complete AI System Demonstration
Shows the full capabilities of the universal UI automation system
"""

import asyncio
import sys
import time
from pathlib import Path

# Add Aiayer to path
sys.path.insert(0, str(Path(__file__).parent))

async def demo_complete_system():
    """Demonstrate the complete AI system capabilities"""
    print("🚀 Complete AI System Demonstration")
    print("=" * 60)
    print("This demo shows the full capabilities of the universal UI automation system")
    print("that combines RPA_AVEN's low-level automation with Aiayer's AI intelligence.")
    print()
    
    try:
        # Initialize the complete system
        print("🔧 Initializing Complete AI System...")
        from integration.complete_ai_system import initialize_complete_system
        system = await initialize_complete_system()
        print("✅ System initialized successfully!")
        print()
        
        # Demo 1: UI Understanding
        print("📊 Demo 1: Real-time UI Understanding")
        print("-" * 40)
        print("Capturing and analyzing current screen...")
        
        ui_state = await system.understand_ui()
        print(f"✅ Detected {len(ui_state.ui_elements)} UI elements")
        print(f"✅ Found {len(ui_state.active_applications)} active applications")
        
        if ui_state.ui_elements:
            print("📱 Sample UI Elements:")
            for i, element in enumerate(ui_state.ui_elements[:5]):
                print(f"   {i+1}. {element.element_type}: {element.text[:50]}...")
        print()
        
        # Demo 2: Natural Language Task Planning
        print("🎯 Demo 2: Natural Language Task Planning")
        print("-" * 40)
        test_tasks = [
            "Open Calculator",
            "Take a screenshot",
            "Open TextEdit and type 'Hello AI World'",
            "Click on any button on the screen"
        ]
        
        for task in test_tasks:
            print(f"🤖 Planning: '{task}'")
            suggestions = await system.suggest_actions(task)
            print(f"   📋 Generated {len(suggestions)} action suggestions")
            
            if suggestions:
                top_suggestion = suggestions[0]
                print(f"   🏆 Top suggestion: {top_suggestion.description}")
                print(f"   📈 Confidence: {top_suggestion.confidence:.2f}")
                print(f"   ⚡ Estimated time: {top_suggestion.estimated_time:.1f}s")
            print()
        
        # Demo 3: Real Automation Execution
        print("⚡ Demo 3: Real Automation Execution")
        print("-" * 40)
        print("Executing a simple automation task...")
        
        # Get a simple suggestion
        suggestions = await system.suggest_actions("Take a screenshot")
        if suggestions:
            print(f"🎬 Executing: {suggestions[0].description}")
            start_time = time.time()
            
            result = await system.execute_action(suggestions[0])
            
            execution_time = time.time() - start_time
            print(f"✅ Execution completed in {execution_time:.2f}s")
            print(f"📊 Success: {result.success}")
            print(f"📝 Result: {result.result_message}")
            print()
        
        # Demo 4: Memory and Learning
        print("🧠 Demo 4: Memory and Learning")
        print("-" * 40)
        print("Storing and retrieving automation context...")
        
        # Store some context
        await system.store_context("demo_session", {
            "last_action": "screenshot",
            "ui_state": "desktop",
            "timestamp": time.time()
        })
        
        # Retrieve context
        context = await system.retrieve_context("demo_session")
        print(f"✅ Retrieved context: {len(context)} items stored")
        print()
        
        # Demo 5: System Statistics
        print("📊 Demo 5: System Performance Statistics")
        print("-" * 40)
        stats = system.get_system_stats()
        
        print(f"🔍 UI Analyses: {stats['ui_analyses']}")
        print(f"⚡ Executions: {stats['executions']}")
        print(f"🧠 Memory Operations: {stats['memory_operations']}")
        print(f"⏱️ Average Response Time: {stats['avg_response_time']:.2f}s")
        print()
        
        # Demo 6: Advanced Capabilities
        print("🚀 Demo 6: Advanced Capabilities")
        print("-" * 40)
        print("The system can handle complex multi-step workflows:")
        print("• Natural language understanding")
        print("• Real-time UI adaptation")
        print("• Error recovery and learning")
        print("• Cross-platform automation")
        print("• Template-free operation")
        print("• Context-aware decision making")
        print()
        
        print("🎉 Demonstration Complete!")
        print("=" * 60)
        print("The Complete AI System is now fully operational!")
        print()
        print("💡 Try these commands in the chat interface:")
        print("   • 'Open Calculator'")
        print("   • 'Open TextEdit and type Hello World'")
        print("   • 'Take a screenshot'")
        print("   • 'Click on the close button'")
        print("   • 'Open Safari and go to google.com'")
        print()
        print("🌐 Chat Interface: http://localhost:5002")
        print("🔧 RPA Server: http://localhost:16901")
        
        return True
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(demo_complete_system()) 