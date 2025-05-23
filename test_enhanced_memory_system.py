#!/usr/bin/env python3
"""
Test Enhanced Memory System - Verify meaningful user understanding capabilities
"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.memory_system import MemorySystem

def create_test_sensor_data(scenario: str):
    """Create realistic sensor data for different scenarios"""
    
    scenarios = {
        "coding_session": {
            "screen": {
                "active_window": {
                    "title": "main.py - Visual Studio Code",
                    "application": "Visual Studio Code"
                },
                "ui_elements": {
                    "controls": [
                        {"type": "button", "focused": True, "text": "Run"},
                        {"type": "menu", "text": "File"}
                    ],
                    "text_fields": [
                        {"type": "editor", "content": "def main():\n    print('Hello World')"}
                    ]
                },
                "text_content": {
                    "headers": ["main.py"],
                    "main_text": ["def main():", "print('Hello World')", "if __name__ == '__main__':"],
                    "raw_text": "def main():\n    print('Hello World')\n\nif __name__ == '__main__':\n    main()"
                }
            },
            "process": {
                "foreground": [
                    {
                        "name": "Visual Studio Code", 
                        "type": "development", 
                        "category": "ide",
                        "state": {"active": True, "focused": True}
                    }
                ],
                "background": [
                    {
                        "name": "Python", 
                        "type": "interpreter", 
                        "category": "development"
                    }
                ]
            }
        },
        
        "research_session": {
            "screen": {
                "active_window": {
                    "title": "How to implement async functions - Stack Overflow",
                    "application": "Google Chrome"
                },
                "ui_elements": {
                    "controls": [
                        {"type": "link", "text": "Answer"},
                        {"type": "button", "text": "Vote Up"}
                    ],
                    "navigation": [
                        {"type": "breadcrumb", "text": "Home > Questions"}
                    ]
                },
                "text_content": {
                    "headers": ["How to implement async functions in Python"],
                    "main_text": ["async def example():", "await asyncio.sleep(1)", "documentation tutorial guide"],
                    "raw_text": "How to implement async functions in Python\n\nasync def example():\n    await asyncio.sleep(1)\n\nThis is a comprehensive guide to understanding async programming..."
                }
            },
            "process": {
                "foreground": [
                    {
                        "name": "Google Chrome", 
                        "type": "browser", 
                        "category": "research"
                    }
                ],
                "background": []
            }
        },
        
        "communication_session": {
            "screen": {
                "active_window": {
                    "title": "Slack - #development",
                    "application": "Slack"
                },
                "ui_elements": {
                    "controls": [
                        {"type": "input", "focused": True, "placeholder": "Message #development"}
                    ],
                    "text_fields": [
                        {"type": "chat", "content": "Hey team, I need help with the API"}
                    ]
                },
                "text_content": {
                    "headers": ["#development"],
                    "main_text": ["Hey team, I need help with the API", "message chat communication"],
                    "raw_text": "Hey team, I need help with the API endpoint. Can someone review my code?"
                }
            },
            "process": {
                "foreground": [
                    {
                        "name": "Slack", 
                        "type": "communication", 
                        "category": "messaging"
                    }
                ],
                "background": []
            }
        },
        
        "distracted_session": {
            "screen": {
                "active_window": {
                    "title": "YouTube - Funny Cat Videos",
                    "application": "Google Chrome"
                },
                "ui_elements": {
                    "controls": [
                        {"type": "video", "state": "playing"},
                        {"type": "notification", "text": "5 new messages"}
                    ]
                },
                "text_content": {
                    "headers": ["Funny Cat Videos"],
                    "main_text": ["entertainment", "social media", "distraction"],
                    "raw_text": "Funny Cat Videos - YouTube\nWatch the funniest cat compilation..."
                }
            },
            "process": {
                "foreground": [
                    {
                        "name": "YouTube", 
                        "type": "entertainment", 
                        "category": "social"
                    },
                    {
                        "name": "Twitter", 
                        "type": "social", 
                        "category": "social"
                    },
                    {
                        "name": "Instagram", 
                        "type": "social", 
                        "category": "entertainment"
                    },
                    {
                        "name": "TikTok", 
                        "type": "entertainment", 
                        "category": "social"
                    }
                ],
                "background": []
            }
        }
    }
    
    return scenarios.get(scenario, scenarios["coding_session"])

async def test_enhanced_memory_understanding():
    """Test the enhanced memory system's understanding capabilities"""
    
    print("🧠 Testing Enhanced Memory System - Meaningful User Understanding")
    print("=" * 70)
    
    # Initialize memory system
    memory_system = MemorySystem()
    await memory_system.initialize()
    
    test_scenarios = [
        ("coding_session", "👨‍💻 Testing Development Workflow Understanding"),
        ("research_session", "🔍 Testing Research Activity Understanding"), 
        ("communication_session", "💬 Testing Communication Context Understanding"),
        ("distracted_session", "😵‍💫 Testing Distraction Detection")
    ]
    
    results = {}
    
    for scenario_name, description in test_scenarios:
        print(f"\n{description}")
        print("-" * 50)
        
        # Create test data
        sensor_data = create_test_sensor_data(scenario_name)
        
        # Process the data through enhanced memory system
        memory_system.process_sensor_data(sensor_data)
        
        # Get the processed context from current_context
        latest_context = memory_system.context_memory.get('current_context', {})
        
        if latest_context:
            user_behavior = latest_context.get('user_behavior', {})
            
            print(f"📊 User Intent Analysis:")
            print(f"   Intent: {user_behavior.get('inferred_intent', 'unknown')}")
            print(f"   Confidence: {user_behavior.get('confidence', 0.0):.2f}")
            print(f"   Workflow Stage: {user_behavior.get('workflow_stage', 'unknown')}")
            print(f"   Activity Type: {user_behavior.get('activity_type', 'unknown')}")
            
            print(f"\n🎯 Focus & Productivity Analysis:")
            focus_level = user_behavior.get('focus_level', {})
            productivity = user_behavior.get('productivity_indicator', {})
            
            print(f"   Focus Score: {focus_level.get('focus_score', 0.0):.2f}")
            print(f"   Attention Type: {focus_level.get('attention_type', 'unknown')}")
            print(f"   Productivity Score: {productivity.get('productivity_score', 0.0):.2f}")
            print(f"   Significance Score: {user_behavior.get('significance_score', 0.0):.2f}")
            
            if focus_level.get('flow_state_indicators'):
                print(f"   Flow Indicators: {', '.join(focus_level['flow_state_indicators'])}")
            if focus_level.get('distraction_indicators'):
                print(f"   Distraction Indicators: {', '.join(focus_level['distraction_indicators'])}")
            
            if productivity.get('indicators'):
                print(f"   Productivity Indicators: {', '.join(productivity['indicators'])}")
            if productivity.get('blockers'):
                print(f"   Productivity Blockers: {', '.join(productivity['blockers'])}")
            
            # Store results for analysis
            results[scenario_name] = {
                'user_behavior': user_behavior,
                'focus_level': focus_level,
                'productivity': productivity
            }
            
            print(f"✅ {scenario_name.replace('_', ' ').title()} analysis completed")
        else:
            print(f"❌ Failed to get context for {scenario_name}")
            results[scenario_name] = None
    
    # Analyze overall results
    print(f"\n🎯 Overall Enhanced Memory System Analysis")
    print("=" * 70)
    
    successful_analyses = sum(1 for result in results.values() if result is not None)
    print(f"Successfully analyzed: {successful_analyses}/{len(test_scenarios)} scenarios")
    
    # Verify intelligence of analysis
    coding_result = results.get('coding_session')
    research_result = results.get('research_session')
    comm_result = results.get('communication_session')
    distracted_result = results.get('distracted_session')
    
    intelligence_checks = []
    
    # Check if coding session was properly identified
    if coding_result:
        coding_behavior = coding_result['user_behavior']
        if (coding_behavior.get('activity_type') == 'development' and 
            coding_behavior.get('confidence', 0) > 0.7):
            intelligence_checks.append("✅ Correctly identified development activity")
        else:
            intelligence_checks.append("❌ Failed to identify development activity")
    
    # Check if research session was properly identified  
    if research_result:
        research_behavior = research_result['user_behavior']
        if (research_behavior.get('activity_type') == 'research' and
            research_behavior.get('confidence', 0) > 0.6):
            intelligence_checks.append("✅ Correctly identified research activity")
        else:
            intelligence_checks.append("❌ Failed to identify research activity")
    
    # Check if distraction was properly detected
    if distracted_result:
        distracted_focus = distracted_result['focus_level']
        distracted_productivity = distracted_result['productivity']
        if (distracted_focus.get('focus_score', 1.0) < 0.5 or 
            distracted_productivity.get('productivity_score', 1.0) < 0.5):
            intelligence_checks.append("✅ Correctly detected distracted state")
        else:
            intelligence_checks.append("❌ Failed to detect distracted state")
    
    # Check if communication was properly identified
    if comm_result:
        comm_behavior = comm_result['user_behavior']
        if comm_behavior.get('inferred_intent') == 'communicating':
            intelligence_checks.append("✅ Correctly identified communication intent")
        else:
            intelligence_checks.append("❌ Failed to identify communication intent")
    
    print(f"\n🧠 Intelligence Assessment:")
    for check in intelligence_checks:
        print(f"   {check}")
    
    intelligence_score = sum(1 for check in intelligence_checks if check.startswith("✅")) / len(intelligence_checks)
    print(f"\n📈 Overall Intelligence Score: {intelligence_score:.2%}")
    
    if intelligence_score >= 0.8:
        print("🎉 EXCELLENT: Memory system demonstrates high-level understanding!")
    elif intelligence_score >= 0.6:
        print("✅ GOOD: Memory system shows solid understanding capabilities")
    elif intelligence_score >= 0.4:
        print("⚠️  MODERATE: Memory system has basic understanding but needs improvement")
    else:
        print("❌ POOR: Memory system lacks meaningful understanding")
    
    # Test memory persistence
    print(f"\n💾 Testing Memory Persistence...")
    memory_system._save_memory_state_sync()
    
    # Verify context retrieval
    context_summary = memory_system.context_memory.get('current_context', {})
    if context_summary:
        print("✅ Memory persistence and retrieval working")
    else:
        print("❌ Memory persistence or retrieval failed")
    
    print(f"\n🎯 Enhanced Memory System Test Complete!")
    print("=" * 70)
    
    return {
        'scenarios_tested': len(test_scenarios),
        'successful_analyses': successful_analyses,
        'intelligence_score': intelligence_score,
        'results': results
    }

async def main():
    """Main function to run enhanced memory tests"""
    try:
        print("🚀 Starting Enhanced Memory System Tests...")
        results = await test_enhanced_memory_understanding()
        
        # Save test results
        with open('/Users/segevbin/Desktop/SensAI/Aiayer/enhanced_memory_test_results.json', 'w') as f:
            # Convert any non-serializable objects to strings
            serializable_results = json.loads(json.dumps(results, default=str))
            json.dump(serializable_results, f, indent=2)
        
        print(f"\n📄 Test results saved to enhanced_memory_test_results.json")
        
        return results
        
    except Exception as e:
        print(f"❌ Error during enhanced memory testing: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(main())