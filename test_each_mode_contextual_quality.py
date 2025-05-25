#!/usr/bin/env python3
"""
Test Each Mode Contextual Quality
Deep test of each mode to verify contextual fetching quality and mode-specific behavior
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_mode_contextual_quality(mode, test_cases):
    """Test a specific mode with multiple contextual scenarios"""
    
    print(f"\n🔍 TESTING {mode.upper()} MODE CONTEXTUAL QUALITY")
    print("=" * 80)
    
    mode_results = []
    
    try:
        uri = "ws://localhost:8767"
        async with websockets.connect(uri, ping_timeout=20) as websocket:
            # Wait for connection
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            print(f"✅ Connected for {mode} mode testing")
            
            for i, test_case in enumerate(test_cases, 1):
                print(f"\n{i}. {mode.upper()} Test: {test_case['scenario']}")
                print(f"   Query: {test_case['query']}")
                print(f"   Expected Context: {test_case['expected_context']}")
                print(f"   Expected Behavior: {test_case['expected_behavior']}")
                print("   " + "-" * 70)
                
                # Send request
                request = {
                    "type": "chat_request",
                    "mode": mode,
                    "message": test_case['query'],
                    "client_id": f"{mode}_test_{i}",
                    "timestamp": datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(request))
                print("   📤 Request sent")
                
                # Collect response
                full_response = ""
                context_metrics = {}
                
                start_time = time.time()
                timeout = 30 if mode == "agent" else 20  # More time for agent mode
                
                while time.time() - start_time < timeout:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        data = json.loads(response)
                        
                        if data.get('type') == 'final_response':
                            full_response = data.get('response', '')
                            context_metrics = {
                                'contextual': data.get('contextual', False),
                                'confidence': data.get('confidence', 0),
                                'ai_powered': data.get('ai_powered', False),
                                'requires_confirmation': data.get('requiresConfirmation', False),
                                'execution_plan': data.get('executionPlan', {})
                            }
                            break
                            
                        elif data.get('type') == 'chat_response_metadata':
                            context_metrics.update(data.get('context_metrics', {}))
                            
                        elif data.get('type') == 'progress_update':
                            stage = data.get('stage', 'Processing...')
                            print(f"   📊 {stage}")
                        
                    except asyncio.TimeoutError:
                        print("   ⏰ Waiting...")
                        continue
                    except Exception as e:
                        print(f"   ❌ Error: {e}")
                        break
                
                # Analyze response quality
                result = analyze_contextual_response(
                    mode, test_case, full_response, context_metrics
                )
                mode_results.append(result)
                
                # Wait between tests
                time.sleep(2)
    
    except Exception as e:
        print(f"❌ Connection error for {mode} mode: {e}")
        return None
    
    return mode_results

def analyze_contextual_response(mode, test_case, response, metrics):
    """Analyze the quality of contextual response for a specific mode"""
    
    result = {
        'mode': mode,
        'scenario': test_case['scenario'],
        'query': test_case['query'],
        'response_length': len(response),
        'contextual_quality': {},
        'mode_specific_behavior': {},
        'overall_score': 0
    }
    
    # Basic contextual metrics
    confidence = metrics.get('confidence', 0)
    contextual = metrics.get('contextual', False)
    ai_powered = metrics.get('ai_powered', False)
    
    print(f"   📊 Contextual: {contextual} | Confidence: {confidence:.3f} | AI: {ai_powered}")
    
    # Check for context indicators
    context_indicators = []
    if "[Using high-confidence context]" in response:
        context_indicators.append("HIGH_CONFIDENCE")
    elif "[Using available context]" in response:
        context_indicators.append("AVAILABLE_CONTEXT")
    
    # Check for expected context terms
    response_lower = response.lower()
    found_context = []
    for expected in test_case['expected_context']:
        if expected.lower() in response_lower:
            found_context.append(expected)
    
    print(f"   🎯 Context Found: {found_context}")
    print(f"   📈 Context Indicators: {context_indicators}")
    
    # Mode-specific analysis
    mode_score = 0
    
    if mode == "ask":
        # Ask mode should provide informative answers with context
        mode_score = analyze_ask_mode_quality(response, test_case, found_context)
        
    elif mode == "agent":
        # Agent mode should show automation planning or execution
        mode_score = analyze_agent_mode_quality(response, test_case, metrics)
        
    elif mode == "suggest":
        # Suggest mode should provide actionable recommendations
        mode_score = analyze_suggest_mode_quality(response, test_case, found_context)
        
    elif mode == "general":
        # General mode should maintain conversational context
        mode_score = analyze_general_mode_quality(response, test_case, found_context)
    
    # Calculate overall contextual quality score
    contextual_score = 0
    if contextual:
        contextual_score += 30
    if confidence > 0.7:
        contextual_score += 25
    elif confidence > 0.5:
        contextual_score += 20
    elif confidence > 0.3:
        contextual_score += 15
    
    if len(found_context) >= len(test_case['expected_context']) * 0.7:
        contextual_score += 25
    elif len(found_context) > 0:
        contextual_score += 15
    
    if context_indicators:
        contextual_score += 20
    
    overall_score = (contextual_score + mode_score) / 2
    
    result.update({
        'contextual_quality': {
            'confidence': confidence,
            'contextual_active': contextual,
            'ai_powered': ai_powered,
            'context_indicators': context_indicators,
            'expected_context_found': found_context,
            'context_coverage': len(found_context) / len(test_case['expected_context']) if test_case['expected_context'] else 0
        },
        'mode_specific_behavior': {
            'behavior_score': mode_score,
            'meets_expectations': mode_score >= 70
        },
        'overall_score': overall_score
    })
    
    # Print analysis
    if overall_score >= 80:
        print(f"   ✅ EXCELLENT contextual quality ({overall_score:.1f}/100)")
    elif overall_score >= 60:
        print(f"   ✅ GOOD contextual quality ({overall_score:.1f}/100)")
    elif overall_score >= 40:
        print(f"   ⚠️  FAIR contextual quality ({overall_score:.1f}/100)")
    else:
        print(f"   ❌ POOR contextual quality ({overall_score:.1f}/100)")
    
    print(f"   📝 Response Preview: {response[:150]}...")
    
    return result

def analyze_ask_mode_quality(response, test_case, found_context):
    """Analyze Ask mode specific behavior"""
    score = 0
    response_lower = response.lower()
    
    # Should provide informative answers
    informative_indicators = [
        "based on", "according to", "i found", "information", 
        "shows", "indicates", "analysis", "data"
    ]
    
    for indicator in informative_indicators:
        if indicator in response_lower:
            score += 15
            break
    
    # Should reference specific context
    if any(ctx.lower() in response_lower for ctx in ["cursor", "development", "coding", "productivity"]):
        score += 25
    
    # Should have substantial content
    if len(response) > 100:
        score += 20
    
    # Should use question-answering language
    qa_language = ["💭", "answer", "information", "found", "shows", "indicates"]
    if any(phrase in response_lower for phrase in qa_language):
        score += 20
    
    return min(score, 100)

def analyze_agent_mode_quality(response, test_case, metrics):
    """Analyze Agent mode specific behavior"""
    score = 0
    response_lower = response.lower()
    
    # Should show automation planning or execution
    automation_indicators = [
        "🎯", "automation", "execution", "plan", "steps", "task", 
        "click", "open", "type", "command", "action"
    ]
    
    for indicator in automation_indicators:
        if indicator in response_lower:
            score += 15
    
    # Check for execution plan structure
    if metrics.get('requires_confirmation'):
        score += 30  # Shows proper automation planning
    
    # Should have action-oriented language
    action_language = ["execute", "perform", "run", "do", "action", "steps"]
    if any(phrase in response_lower for phrase in action_language):
        score += 20
    
    # Should be specific about what it will do
    if len(response) > 200:  # Detailed automation instructions
        score += 15
    
    return min(score, 100)

def analyze_suggest_mode_quality(response, test_case, found_context):
    """Analyze Suggest mode specific behavior"""
    score = 0
    response_lower = response.lower()
    
    # Should provide suggestions/recommendations
    suggestion_indicators = [
        "💡", "suggest", "recommend", "consider", "try", "could", 
        "might", "improve", "enhance", "optimize"
    ]
    
    for indicator in suggestion_indicators:
        if indicator in response_lower:
            score += 15
    
    # Should provide multiple suggestions or detailed advice
    suggestion_count = response_lower.count("💡") + response_lower.count("suggest") + response_lower.count("recommend")
    if suggestion_count >= 2:
        score += 25
    elif suggestion_count >= 1:
        score += 15
    
    # Should be actionable
    actionable_language = ["you can", "you could", "you should", "you might", "try", "consider"]
    if any(phrase in response_lower for phrase in actionable_language):
        score += 20
    
    # Should reference user patterns or context
    if any(ctx.lower() in response_lower for ctx in ["workflow", "pattern", "habit", "productivity"]):
        score += 20
    
    return min(score, 100)

def analyze_general_mode_quality(response, test_case, found_context):
    """Analyze General mode specific behavior"""
    score = 0
    response_lower = response.lower()
    
    # Should be conversational
    conversational_indicators = [
        "🤖", "hello", "hi", "how", "help", "understand", 
        "let me", "i can", "i'm", "we've", "our"
    ]
    
    for indicator in conversational_indicators:
        if indicator in response_lower:
            score += 15
            break
    
    # Should maintain context awareness
    context_language = ["remember", "recall", "previous", "before", "conversation", "we discussed"]
    if any(phrase in response_lower for phrase in context_language):
        score += 25
    
    # Should be personable and helpful
    helpful_language = ["help", "assist", "support", "here for you", "happy to"]
    if any(phrase in response_lower for phrase in helpful_language):
        score += 20
    
    # Should reference interaction history
    if any(ctx.lower() in response_lower for ctx in ["interaction", "conversation", "discussed", "mentioned"]):
        score += 20
    
    return min(score, 100)

async def main():
    """Test each mode with comprehensive contextual scenarios"""
    
    print("🧪 COMPREHENSIVE CONTEXTUAL QUALITY TEST FOR ALL MODES")
    print("=" * 80)
    
    # Define mode-specific test cases
    test_scenarios = {
        "ask": [
            {
                "scenario": "Development Tools Query",
                "query": "What development tools am I currently using?",
                "expected_context": ["Cursor", "development", "coding", "IDE"],
                "expected_behavior": "Should provide specific information about detected development tools"
            },
            {
                "scenario": "Productivity Analysis",
                "query": "How productive have I been with my coding work?",
                "expected_context": ["productivity", "score", "activity", "coding"],
                "expected_behavior": "Should analyze productivity metrics and patterns"
            },
            {
                "scenario": "Workflow Information",
                "query": "What's my typical development workflow?",
                "expected_context": ["workflow", "development", "process", "pattern"],
                "expected_behavior": "Should describe observed workflow patterns"
            }
        ],
        
        "agent": [
            {
                "scenario": "Application Launch",
                "query": "Open Chrome browser for me",
                "expected_context": ["automation", "browser", "application", "launch"],
                "expected_behavior": "Should create automation plan or execute browser opening"
            },
            {
                "scenario": "Text Input",
                "query": "Type 'Hello World' in the current text field",
                "expected_context": ["automation", "typing", "text", "input"],
                "expected_behavior": "Should plan or execute text input automation"
            },
            {
                "scenario": "Search Task",
                "query": "Search for 'Python tutorials' on Google",
                "expected_context": ["search", "google", "automation", "browser"],
                "expected_behavior": "Should create detailed automation plan for web search"
            }
        ],
        
        "suggest": [
            {
                "scenario": "Workflow Improvement",
                "query": "How can I improve my coding productivity?",
                "expected_context": ["productivity", "coding", "improvement", "workflow"],
                "expected_behavior": "Should provide specific suggestions based on usage patterns"
            },
            {
                "scenario": "Tool Recommendations",
                "query": "What tools should I use for better development?",
                "expected_context": ["tools", "development", "recommendation", "improvement"],
                "expected_behavior": "Should suggest tools based on current development context"
            },
            {
                "scenario": "Optimization Advice",
                "query": "What should I focus on next in my work?",
                "expected_context": ["focus", "work", "priority", "optimization"],
                "expected_behavior": "Should provide actionable recommendations based on context"
            }
        ],
        
        "general": [
            {
                "scenario": "Greeting with Context",
                "query": "Hello, how's my day going?",
                "expected_context": ["greeting", "conversation", "activity", "day"],
                "expected_behavior": "Should greet and reference recent activities or interactions"
            },
            {
                "scenario": "System Status",
                "query": "How are things working?",
                "expected_context": ["system", "status", "working", "functionality"],
                "expected_behavior": "Should provide status with context awareness"
            },
            {
                "scenario": "Help Request",
                "query": "Can you help me understand what I've been working on?",
                "expected_context": ["help", "working", "activity", "understanding"],
                "expected_behavior": "Should provide helpful summary of recent activities"
            }
        ]
    }
    
    all_results = {}
    
    # Test each mode
    for mode, test_cases in test_scenarios.items():
        results = await test_mode_contextual_quality(mode, test_cases)
        if results:
            all_results[mode] = results
        
        # Wait between modes
        time.sleep(3)
    
    # Generate comprehensive analysis
    print(f"\n📊 COMPREHENSIVE CONTEXTUAL ANALYSIS")
    print("=" * 80)
    
    for mode, results in all_results.items():
        print(f"\n🔍 {mode.upper()} MODE SUMMARY:")
        
        total_score = sum(r['overall_score'] for r in results) / len(results)
        avg_confidence = sum(r['contextual_quality']['confidence'] for r in results) / len(results)
        contextual_active = sum(1 for r in results if r['contextual_quality']['contextual_active'])
        
        print(f"   Overall Quality: {total_score:.1f}/100")
        print(f"   Average Confidence: {avg_confidence:.3f}")
        print(f"   Contextual Active: {contextual_active}/{len(results)} tests")
        
        # Show best and worst performing test
        best_test = max(results, key=lambda x: x['overall_score'])
        worst_test = min(results, key=lambda x: x['overall_score'])
        
        print(f"   ✅ Best: {best_test['scenario']} ({best_test['overall_score']:.1f})")
        print(f"   ⚠️  Worst: {worst_test['scenario']} ({worst_test['overall_score']:.1f})")
    
    # Overall system assessment
    if all_results:
        system_average = sum(
            sum(r['overall_score'] for r in results) / len(results) 
            for results in all_results.values()
        ) / len(all_results)
        
        print(f"\n🎯 SYSTEM-WIDE CONTEXTUAL QUALITY: {system_average:.1f}/100")
        
        if system_average >= 80:
            print("✅ EXCELLENT - All modes have strong contextual integration")
        elif system_average >= 60:
            print("✅ GOOD - Most modes working well with room for improvement")
        elif system_average >= 40:
            print("⚠️  FAIR - Contextual integration needs improvement")
        else:
            print("❌ POOR - Significant contextual integration issues")

if __name__ == "__main__":
    asyncio.run(main())