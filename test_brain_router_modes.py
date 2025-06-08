#!/usr/bin/env python3
"""
Test Brain Router with different modes to verify memory integration
"""

import asyncio
import json
import logging
import sys
import time
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import brain router
try:
    from brain.core.brain_router import process_chat_request, ChatMode
    BRAIN_ROUTER_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import brain router: {e}")
    BRAIN_ROUTER_AVAILABLE = False

# Test questions for ASK mode
ASK_QUESTIONS = [
    "What applications are currently running on my computer?",
    "What am I working on in my development environment?",
    "How many applications do I have open?",
    "What's my productivity level right now?",
    "What's my current workflow stage?"
]

# Test questions for SUGGEST mode
SUGGEST_QUESTIONS = [
    "Any suggestions for my current development work?",
    "How can I be more productive right now?",
    "What should I focus on next?",
    "Any recommended next steps for my coding?",
    "Help me optimize my current workflow"
]

async def test_ask_mode():
    """Test ASK mode with memory integration"""
    if not BRAIN_ROUTER_AVAILABLE:
        logger.error("Brain router not available, can't test ASK mode")
        return
    
    logger.info("\n🔍 TESTING ASK MODE WITH MEMORY INTEGRATION")
    logger.info("=" * 70)
    
    results = []
    
    for question in ASK_QUESTIONS:
        logger.info(f"\nQuestion: \"{question}\"")
        
        # Process request through brain router
        start_time = time.time()
        response = await process_chat_request(
            mode="Ask",
            query=question,
            user_id="test_user",
            session_id="test_session"
        )
        processing_time = time.time() - start_time
        
        # Log response
        logger.info(f"Processing time: {processing_time:.2f}s")
        logger.info(f"Mode: {response.get('mode', 'unknown')}")
        logger.info(f"Success: {response.get('success', False)}")
        logger.info(f"Confidence: {response.get('confidence', 0.0)}")
        logger.info(f"Response: {response.get('response', '')[:300]}...")
        
        # Check if memory was integrated
        memory_integrated = False
        metadata = response.get('metadata', {})
        if metadata:
            logger.info("Metadata:")
            for key, value in metadata.items():
                if key in ['enhanced_memory_used', 'semantic_search_used', 'semantic_results_count']:
                    logger.info(f"  {key}: {value}")
                    if key in ['enhanced_memory_used', 'semantic_search_used'] and value:
                        memory_integrated = True
        
        results.append({
            'question': question,
            'processing_time': processing_time,
            'confidence': response.get('confidence', 0.0),
            'success': response.get('success', False),
            'memory_integrated': memory_integrated,
            'response': response.get('response', '')
        })
    
    # Calculate statistics
    success_count = sum(1 for r in results if r['success'])
    memory_integrated_count = sum(1 for r in results if r['memory_integrated'])
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    avg_processing_time = sum(r['processing_time'] for r in results) / len(results)
    
    # Show summary
    logger.info("\n📊 ASK MODE SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Success rate: {success_count}/{len(ASK_QUESTIONS)} ({success_count/len(ASK_QUESTIONS)*100:.1f}%)")
    logger.info(f"Memory integration rate: {memory_integrated_count}/{len(ASK_QUESTIONS)} ({memory_integrated_count/len(ASK_QUESTIONS)*100:.1f}%)")
    logger.info(f"Average confidence: {avg_confidence:.2f}")
    logger.info(f"Average processing time: {avg_processing_time:.2f}s")
    
    return results

async def test_suggest_mode():
    """Test SUGGEST mode with memory integration"""
    if not BRAIN_ROUTER_AVAILABLE:
        logger.error("Brain router not available, can't test SUGGEST mode")
        return
    
    logger.info("\n💡 TESTING SUGGEST MODE WITH MEMORY INTEGRATION")
    logger.info("=" * 70)
    
    results = []
    
    for question in SUGGEST_QUESTIONS:
        logger.info(f"\nQuery: \"{question}\"")
        
        # Process request through brain router
        start_time = time.time()
        response = await process_chat_request(
            mode="Suggest",
            query=question,
            user_id="test_user",
            session_id="test_session"
        )
        processing_time = time.time() - start_time
        
        # Log response
        logger.info(f"Processing time: {processing_time:.2f}s")
        logger.info(f"Mode: {response.get('mode', 'unknown')}")
        logger.info(f"Success: {response.get('success', False)}")
        logger.info(f"Confidence: {response.get('confidence', 0.0)}")
        logger.info(f"Response: {response.get('response', '')[:300]}...")
        
        # Check if memory was integrated
        memory_integrated = False
        metadata = response.get('metadata', {})
        if metadata:
            logger.info("Metadata:")
            for key, value in metadata.items():
                if key in ['suggest_mode_used', 'memory_integrated', 'suggestion_categories']:
                    logger.info(f"  {key}: {value}")
                    if key in ['suggest_mode_used', 'memory_integrated'] and value:
                        memory_integrated = True
        
        results.append({
            'question': question,
            'processing_time': processing_time,
            'confidence': response.get('confidence', 0.0),
            'success': response.get('success', False),
            'memory_integrated': memory_integrated,
            'response': response.get('response', '')
        })
    
    # Calculate statistics
    success_count = sum(1 for r in results if r['success'])
    memory_integrated_count = sum(1 for r in results if r['memory_integrated'])
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    avg_processing_time = sum(r['processing_time'] for r in results) / len(results)
    
    # Show summary
    logger.info("\n📊 SUGGEST MODE SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Success rate: {success_count}/{len(SUGGEST_QUESTIONS)} ({success_count/len(SUGGEST_QUESTIONS)*100:.1f}%)")
    logger.info(f"Memory integration rate: {memory_integrated_count}/{len(SUGGEST_QUESTIONS)} ({memory_integrated_count/len(SUGGEST_QUESTIONS)*100:.1f}%)")
    logger.info(f"Average confidence: {avg_confidence:.2f}")
    logger.info(f"Average processing time: {avg_processing_time:.2f}s")
    
    return results

async def run_tests():
    """Run all tests"""
    logger.info("🧠 TESTING BRAIN ROUTER MODES WITH MEMORY INTEGRATION")
    logger.info("=" * 70)
    
    # Test ASK mode
    ask_results = await test_ask_mode()
    
    # Test SUGGEST mode
    suggest_results = await test_suggest_mode()
    
    # Final assessment
    logger.info("\n🎯 FINAL ASSESSMENT")
    logger.info("=" * 70)
    
    if ask_results and suggest_results:
        ask_integration_rate = sum(1 for r in ask_results if r['memory_integrated']) / len(ask_results)
        suggest_integration_rate = sum(1 for r in suggest_results if r['memory_integrated']) / len(suggest_results)
        overall_integration_rate = (ask_integration_rate + suggest_integration_rate) / 2
        
        if overall_integration_rate >= 0.8:
            logger.info("✅ EXCELLENT: Brain router is successfully integrating memory into responses")
        elif overall_integration_rate >= 0.6:
            logger.info("✅ GOOD: Brain router is integrating memory into most responses")
        elif overall_integration_rate >= 0.4:
            logger.info("⚠️ FAIR: Brain router integrates memory sometimes but has limitations")
        else:
            logger.info("❌ POOR: Brain router rarely integrates memory successfully")
        
        logger.info(f"Overall memory integration rate: {overall_integration_rate*100:.1f}%")
        
        # Save results to file
        with open('test_brain_router_results.json', 'w') as f:
            json.dump({
                'ask_results': ask_results,
                'suggest_results': suggest_results,
                'ask_integration_rate': ask_integration_rate,
                'suggest_integration_rate': suggest_integration_rate,
                'overall_integration_rate': overall_integration_rate,
                'timestamp': time.time()
            }, f, indent=2)
        
        logger.info("Results saved to test_brain_router_results.json")

if __name__ == "__main__":
    asyncio.run(run_tests())