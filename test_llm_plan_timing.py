#!/usr/bin/env python3
"""
Test LLM Plan Generation Timing
Measures how long it takes to get automation plans from the LLM
"""

import asyncio
import time
import logging
import json
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_direct_universal_plan():
    """Test direct universal automation plan creation timing"""
    logger.info("🔍 Testing direct universal automation plan creation timing...")
    
    try:
        # Import the universal automation handler
        start_import = time.time()
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from universal_intelligent_automation_handler import universal_automation_handler
        import_time = time.time() - start_import
        logger.info(f"✅ Import time: {import_time:.2f}s")
        
        # Test cases with different complexity
        test_cases = [
            {"query": "search for Python tutorials", "name": "Simple Web Search"},
            {"query": "search for flights from NYC to LA for next month", "name": "Flight Search"},
            {"query": "open calculator and multiply 235 by 17", "name": "App Usage"},
            {"query": "find best laptop deals on Amazon", "name": "Shopping Search"}
        ]
        
        results = []
        
        # Run tests
        for test in test_cases:
            logger.info(f"🧪 Testing: {test['name']} - \"{test['query']}\"")
            
            # Measure timing for plan creation
            start_time = time.time()
            plan_result = await universal_automation_handler.create_universal_automation_plan(
                test['query'], 
                f"test_session_{int(time.time())}"
            )
            plan_time = time.time() - start_time
            
            # Log results
            success = plan_result.get('success', False)
            logger.info(f"   ⏱️ Plan generation time: {plan_time:.2f}s")
            logger.info(f"   ✅ Success: {success}")
            
            # Add to results
            results.append({
                "test_name": test['name'],
                "query": test['query'],
                "time_seconds": plan_time,
                "success": success,
                "plan_id": plan_result.get('plan_id'),
                "request_type": plan_result.get('request_type')
            })
            
        return results
            
    except Exception as e:
        logger.error(f"❌ Error in test: {e}")
        return []

async def test_llm_service_direct():
    """Test direct LLM service response time"""
    logger.info("🔍 Testing direct LLM service response time...")
    
    try:
        # Import LLM service
        start_import = time.time()
        from llm.llm_service import LLMService
        import_time = time.time() - start_import
        logger.info(f"✅ Import time: {import_time:.2f}s")
        
        # Initialize LLM service
        start_init = time.time()
        llm_service = LLMService(model_name="llama3.2:1b")
        await llm_service.initialize()
        init_time = time.time() - start_init
        logger.info(f"✅ Initialization time: {init_time:.2f}s")
        
        # Test simple completions
        test_prompts = [
            {"prompt": "Hello, how are you?", "name": "Simple Greeting"},
            {"prompt": "Create a plan to search for flights from NYC to LA", "name": "Flight Plan"},
            {"prompt": "What is the capital of France?", "name": "Simple Question"}
        ]
        
        results = []
        
        for test in test_prompts:
            logger.info(f"🧪 Testing: {test['name']} - \"{test['prompt']}\"")
            
            # Measure timing for completion
            start_time = time.time()
            response = await llm_service.generate_completion(
                test['prompt'],
                temperature=0.7,
                max_tokens=500,
                system_prompt="You are a helpful assistant."
            )
            completion_time = time.time() - start_time
            
            # Log results
            success = response.get('success', False)
            logger.info(f"   ⏱️ Completion time: {completion_time:.2f}s")
            logger.info(f"   ✅ Success: {success}")
            
            # Add to results
            results.append({
                "test_name": test['name'],
                "prompt": test['prompt'],
                "time_seconds": completion_time,
                "success": success,
                "response_length": len(response.get('text', '')) if success else 0
            })
            
        return results
            
    except Exception as e:
        logger.error(f"❌ Error in test: {e}")
        return []

async def test_brain_router_agent_mode():
    """Test agent mode through brain router"""
    logger.info("🔍 Testing agent mode through brain router...")
    
    try:
        # Import brain router
        start_import = time.time()
        from brain.core.brain_router import BrainRouter, ChatRequest, ChatMode
        import_time = time.time() - start_import
        logger.info(f"✅ Import time: {import_time:.2f}s")
        
        # Initialize brain router
        start_init = time.time()
        brain_router = BrainRouter()
        init_time = time.time() - start_init
        logger.info(f"✅ Initialization time: {init_time:.2f}s")
        
        # Test cases with different complexity
        test_cases = [
            {"query": "search for Python tutorials", "name": "Simple Web Search"},
            {"query": "search for flights from NYC to LA", "name": "Flight Search"},
            {"query": "open calculator and multiply 235 by 17", "name": "App Usage"}
        ]
        
        results = []
        
        # Run tests
        for test in test_cases:
            logger.info(f"🧪 Testing: {test['name']} - \"{test['query']}\"")
            
            # Create request
            request = ChatRequest(
                mode=ChatMode.AGENT,
                query=test['query'],
                user_id=f"test_user_{int(time.time())}",
                session_id=f"test_session_{int(time.time())}",
                timestamp=time.time(),
                context={}
            )
            
            # Measure timing for processing
            start_time = time.time()
            response = await brain_router.process_request(request)
            process_time = time.time() - start_time
            
            # Log results
            success = response.success
            logger.info(f"   ⏱️ Processing time: {process_time:.2f}s")
            logger.info(f"   ✅ Success: {success}")
            
            # Add to results
            results.append({
                "test_name": test['name'],
                "query": test['query'],
                "time_seconds": process_time,
                "success": success,
                "mode_used": str(response.mode_used),
                "resources_used": response.resources_used
            })
            
        return results
            
    except Exception as e:
        logger.error(f"❌ Error in test: {e}")
        return []

async def run_all_tests():
    """Run all timing tests"""
    logger.info("=" * 60)
    logger.info("🚀 Starting LLM Plan Timing Tests")
    logger.info("=" * 60)
    
    results = {}
    
    # Test 1: Universal Automation Plan
    logger.info("\n📊 TEST 1: Universal Automation Plan")
    logger.info("-" * 50)
    universal_results = await test_direct_universal_plan()
    results["universal_plan"] = universal_results
    logger.info("")
    
    # Test 2: LLM Service Direct
    logger.info("\n📊 TEST 2: LLM Service Direct")
    logger.info("-" * 50)
    llm_results = await test_llm_service_direct()
    results["llm_service"] = llm_results
    logger.info("")
    
    # Test 3: Brain Router Agent Mode
    logger.info("\n📊 TEST 3: Brain Router Agent Mode")
    logger.info("-" * 50)
    agent_results = await test_brain_router_agent_mode()
    results["agent_mode"] = agent_results
    logger.info("")
    
    # Save results
    with open('llm_plan_timing_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Show summary
    logger.info("=" * 60)
    logger.info("📝 SUMMARY")
    logger.info("=" * 60)
    
    # Universal plan times
    if universal_results:
        avg_universal = sum(r["time_seconds"] for r in universal_results) / len(universal_results)
        logger.info(f"Universal Plan Avg: {avg_universal:.2f}s")
        for r in universal_results:
            logger.info(f"  - {r['test_name']}: {r['time_seconds']:.2f}s")
    
    # LLM service times
    if llm_results:
        avg_llm = sum(r["time_seconds"] for r in llm_results) / len(llm_results)
        logger.info(f"LLM Service Avg: {avg_llm:.2f}s")
        for r in llm_results:
            logger.info(f"  - {r['test_name']}: {r['time_seconds']:.2f}s")
    
    # Agent mode times
    if agent_results:
        avg_agent = sum(r["time_seconds"] for r in agent_results) / len(agent_results)
        logger.info(f"Agent Mode Avg: {avg_agent:.2f}s")
        for r in agent_results:
            logger.info(f"  - {r['test_name']}: {r['time_seconds']:.2f}s")
    
    logger.info("=" * 60)
    logger.info("Results saved to llm_plan_timing_results.json")
    
    return results

if __name__ == "__main__":
    asyncio.run(run_all_tests())