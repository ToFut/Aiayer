#!/usr/bin/env python3
import asyncio
import websockets
import json
import time

# 20 different types of prompts to test universal LLM planning
TEST_PROMPTS = [
    # Web browsing
    "open YouTube and search SEGEV",
    "find the latest news on CNN",
    "check GitHub trending repositories",
    
    # App usage
    "open Calculator and compute 15 * 27",
    "create a new document in Pages",
    "open Spotify and play some music",
    
    # File operations
    "create a new folder called 'Projects' on Desktop",
    "open TextEdit and write a shopping list",
    "find all PDF files in Downloads folder",
    
    # Research tasks
    "research Python machine learning libraries",
    "find tutorials about Swift programming",
    "look up the weather forecast for New York",
    
    # Creative tasks
    "design a simple logo in Preview",
    "write a poem about automation",
    "create a presentation about AI",
    
    # Communication
    "compose an email to my team",
    "check my Messages app for new texts",
    "schedule a meeting in Calendar",
    
    # System tasks
    "check my system storage usage",
    "update my software applications"
]

async def test_single_prompt(prompt_index, prompt):
    """Test a single prompt with the universal LLM planner"""
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            # Register client
            client_id = f"test_universal_{prompt_index}"
            register_msg = {
                "type": "register",
                "client_id": client_id,
                "timestamp": int(time.time() * 1000)
            }
            await websocket.send(json.dumps(register_msg))
            
            # Send agent request
            start_time = time.time()
            agent_msg = {
                "type": "agent_mode",
                "message": prompt,
                "client_id": client_id,
                "timestamp": int(time.time() * 1000)
            }
            
            print(f"\n🧪 Test {prompt_index+1}/20: '{prompt}'")
            await websocket.send(json.dumps(agent_msg))
            
            # Listen for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=60.0)
                response_time = time.time() - start_time
                data = json.loads(response)
                
                if data.get("success"):
                    ai_powered = data.get("ai_powered", False)
                    llm_generated = data.get("llm_generated", False)
                    plan_id = data.get("plan_id", "unknown")
                    
                    # Look for plan details in buttons or response
                    buttons = data.get("buttons", [])
                    step_count = 0
                    
                    # Count steps from buttons
                    for button in buttons:
                        if "step" in button.get("text", "").lower():
                            step_count += 1
                    
                    result = {
                        "success": True,
                        "response_time": round(response_time, 2),
                        "ai_powered": ai_powered,
                        "llm_generated": llm_generated,
                        "step_count": step_count,
                        "plan_id": plan_id,
                        "has_buttons": len(buttons) > 0
                    }
                    
                    print(f"✅ Success - {response_time:.2f}s - AI:{ai_powered} LLM:{llm_generated} Steps:{step_count}")
                    return result
                else:
                    print(f"❌ Failed: {data.get('response', 'Unknown error')}")
                    return {"success": False, "error": data.get('response', 'Unknown error')}
                    
            except asyncio.TimeoutError:
                print(f"⏰ Timeout after 60s")
                return {"success": False, "error": "timeout"}
                
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return {"success": False, "error": str(e)}

async def run_comprehensive_test():
    """Run comprehensive test of universal LLM planner"""
    print("🧠 UNIVERSAL LLM AUTOMATION PLANNER TEST")
    print("=" * 60)
    print("Testing 20 different prompt types to verify LLM-based planning")
    print("Goal: Ensure ANY message type gets detailed automation plans")
    print("=" * 60)
    
    results = []
    successful_tests = 0
    
    for i, prompt in enumerate(TEST_PROMPTS):
        result = await test_single_prompt(i, prompt)
        results.append({
            "prompt": prompt,
            "result": result
        })
        
        if result.get("success"):
            successful_tests += 1
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(TEST_PROMPTS)}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {len(TEST_PROMPTS) - successful_tests}")
    print(f"Success Rate: {(successful_tests/len(TEST_PROMPTS)*100):.1f}%")
    
    # Detailed results
    print("\n📋 DETAILED RESULTS:")
    print("-" * 60)
    
    ai_powered_count = 0
    llm_generated_count = 0
    total_response_time = 0
    total_steps = 0
    
    for i, test in enumerate(results):
        prompt = test["prompt"]
        result = test["result"]
        
        if result.get("success"):
            response_time = result.get("response_time", 0)
            ai_powered = result.get("ai_powered", False)
            llm_generated = result.get("llm_generated", False)
            step_count = result.get("step_count", 0)
            
            total_response_time += response_time
            total_steps += step_count
            
            if ai_powered:
                ai_powered_count += 1
            if llm_generated:
                llm_generated_count += 1
            
            print(f"{i+1:2d}. ✅ '{prompt[:40]}...' ({response_time:.1f}s, {step_count} steps, LLM:{llm_generated})")
        else:
            error = result.get("error", "Unknown")
            print(f"{i+1:2d}. ❌ '{prompt[:40]}...' - {error}")
    
    # Statistics
    if successful_tests > 0:
        avg_response_time = total_response_time / successful_tests
        avg_steps = total_steps / successful_tests
        
        print(f"\n📈 STATISTICS:")
        print(f"Average Response Time: {avg_response_time:.2f}s")
        print(f"Average Steps per Plan: {avg_steps:.1f}")
        print(f"AI-Powered Plans: {ai_powered_count}/{successful_tests} ({ai_powered_count/successful_tests*100:.1f}%)")
        print(f"LLM-Generated Plans: {llm_generated_count}/{successful_tests} ({llm_generated_count/successful_tests*100:.1f}%)")
    
    # Verification
    print(f"\n✅ VERIFICATION:")
    if llm_generated_count == successful_tests:
        print("✅ ALL successful plans were LLM-generated (no pattern fallbacks)")
    else:
        print(f"⚠️  {successful_tests - llm_generated_count} plans used pattern fallbacks")
    
    if successful_tests >= 18:  # 90% success rate
        print("✅ Universal LLM planner is working correctly")
    else:
        print("❌ Universal LLM planner needs improvement")

if __name__ == "__main__":
    asyncio.run(run_comprehensive_test())