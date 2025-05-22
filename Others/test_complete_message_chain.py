#!/usr/bin/env python3
"""
Complete Message Chain Test
Comprehensive testing of all 4 modes with real LLM responses
Verifies complete chain: Overlay -> Backend -> Brain Router -> Mode Handlers -> LLM -> Memory
"""

import asyncio
import websockets
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MessageChainTester:
    """Test complete message chain for all modes"""
    
    def __init__(self, ws_url="ws://localhost:8767"):
        self.ws_url = ws_url
        self.test_results = {}
        
        # Test queries for each mode
        self.test_queries = {
            "Ask": [
                "What can you help me with?",
                "How does this system work?", 
                "What are the main features available?"
            ],
            "Agent": [
                "Help me organize my files",
                "Create a plan to improve my productivity",
                "Set up an automated workflow"
            ],
            "Suggest": [
                "I want to improve my coding practices",
                "Give me suggestions for better time management",
                "What tools would help my development workflow?"
            ],
            "General": [
                "Hello, how are you today?",
                "Tell me something interesting",
                "What do you think about AI?"
            ]
        }
    
    async def run_complete_test(self):
        """Run complete test suite for all modes"""
        logger.info("🚀 Starting Complete Message Chain Test")
        
        start_time = time.time()
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                logger.info(f"✅ Connected to backend: {self.ws_url}")
                
                # Test each mode with multiple queries
                for mode, queries in self.test_queries.items():
                    logger.info(f"\n📝 Testing {mode} mode...")
                    
                    mode_results = []
                    
                    for i, query in enumerate(queries, 1):
                        logger.info(f"  {i}. Testing query: '{query[:50]}...'")
                        
                        result = await self._test_single_query(websocket, mode, query)
                        mode_results.append(result)
                        
                        # Wait between queries to avoid overwhelming the system
                        await asyncio.sleep(1)
                    
                    self.test_results[mode] = mode_results
                
                # Generate comprehensive report
                await self._generate_test_report()
                
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False
        
        total_time = time.time() - start_time
        logger.info(f"🎉 Complete test finished in {total_time:.2f}s")
        return True
    
    async def _test_single_query(self, websocket, mode, query):
        """Test a single query and measure complete chain"""
        start_time = time.time()
        
        try:
            # Send message
            message = {
                "type": "chat_request",
                "mode": mode,
                "query": query,
                "user_id": f"test_user_{int(time.time())}",
                "session_id": f"test_session_{int(time.time())}",
                "timestamp": time.time()
            }
            
            logger.info(f"📤 Sending {mode} message: {query[:30]}...")
            await websocket.send(json.dumps(message))
            
            # Wait for response
            response_raw = await asyncio.wait_for(websocket.recv(), timeout=30.0)
            response = json.loads(response_raw)
            
            processing_time = time.time() - start_time
            
            # Analyze response
            result = await self._analyze_response(response, mode, query, processing_time)
            
            logger.info(f"✅ {mode} response received (time: {processing_time:.2f}s, confidence: {result['confidence']:.2f})")
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ Timeout waiting for {mode} response")
            return {
                "success": False,
                "error": "timeout",
                "mode": mode,
                "query": query,
                "processing_time": time.time() - start_time
            }
        except Exception as e:
            logger.error(f"❌ Error testing {mode} query: {e}")
            return {
                "success": False,
                "error": str(e),
                "mode": mode,
                "query": query,
                "processing_time": time.time() - start_time
            }
    
    async def _analyze_response(self, response, mode, query, processing_time):
        """Analyze response quality and chain completeness"""
        
        # Basic response structure validation
        if response.get("type") != "chat_response":
            return {
                "success": False,
                "error": f"Invalid response type: {response.get('type')}",
                "mode": mode,
                "query": query,
                "processing_time": processing_time
            }
        
        payload = response.get("payload", {})
        
        # Extract response data
        response_text = payload.get("response", "")
        confidence = payload.get("confidence", 0.0)
        resources_used = payload.get("resources_used", [])
        metadata = payload.get("metadata", {})
        
        # Check if LLM was used (not mock response)
        llm_used = "llm" in resources_used
        llm_model = metadata.get("llm_model", "unknown")
        llm_tokens = metadata.get("llm_tokens", 0)
        
        # Quality checks
        quality_score = await self._calculate_quality_score(response_text, query, mode)
        
        # Chain verification
        chain_complete = await self._verify_chain_completeness(resources_used, metadata)
        
        return {
            "success": True,
            "mode": mode,
            "query": query,
            "response_text": response_text,
            "response_length": len(response_text),
            "confidence": confidence,
            "processing_time": processing_time,
            "llm_used": llm_used,
            "llm_model": llm_model,
            "llm_tokens": llm_tokens,
            "resources_used": resources_used,
            "quality_score": quality_score,
            "chain_complete": chain_complete,
            "metadata": metadata
        }
    
    async def _calculate_quality_score(self, response_text, query, mode):
        """Calculate response quality score"""
        score = 0.0
        
        # Length check (reasonable response length)
        if 50 <= len(response_text) <= 2000:
            score += 0.2
        
        # Relevance check (query keywords in response)
        query_words = set(query.lower().split())
        response_words = set(response_text.lower().split())
        overlap = len(query_words.intersection(response_words))
        if overlap > 0:
            score += min(overlap / len(query_words), 0.3)
        
        # Mode-specific checks
        if mode == "Agent" and any(word in response_text.lower() for word in ["step", "plan", "first", "next"]):
            score += 0.2
        elif mode == "Suggest" and any(word in response_text.lower() for word in ["suggest", "recommend", "try"]):
            score += 0.2
        elif mode == "Ask" and len(response_text) > 100:  # Detailed responses
            score += 0.2
        elif mode == "General" and any(word in response_text.lower() for word in ["hello", "help", "i"]):
            score += 0.2
        
        # Coherence check (no repeated phrases)
        words = response_text.split()
        if len(set(words)) / len(words) > 0.7:  # Good word diversity
            score += 0.1
        
        return min(score, 1.0)
    
    async def _verify_chain_completeness(self, resources_used, metadata):
        """Verify that the complete processing chain was used"""
        
        # Check required resources for complete chain
        required_resources = ["memory", "llm"]
        has_required = all(resource in resources_used for resource in required_resources)
        
        # Check metadata indicates proper processing
        has_llm_metadata = "llm_model" in metadata and "llm_tokens" in metadata
        
        # Check semantic search was used
        has_semantic_search = "semantic_search" in resources_used or "memories_found" in metadata
        
        return has_required and has_llm_metadata and has_semantic_search
    
    async def _generate_test_report(self):
        """Generate comprehensive test report"""
        
        logger.info("\n" + "="*80)
        logger.info("📊 COMPLETE MESSAGE CHAIN TEST REPORT")
        logger.info("="*80)
        
        total_tests = 0
        successful_tests = 0
        llm_responses = 0
        complete_chains = 0
        
        mode_summary = {}
        
        for mode, results in self.test_results.items():
            mode_total = len(results)
            mode_success = len([r for r in results if r.get("success", False)])
            mode_llm = len([r for r in results if r.get("llm_used", False)])
            mode_complete = len([r for r in results if r.get("chain_complete", False)])
            
            avg_confidence = sum(r.get("confidence", 0) for r in results) / len(results) if results else 0
            avg_quality = sum(r.get("quality_score", 0) for r in results) / len(results) if results else 0
            avg_time = sum(r.get("processing_time", 0) for r in results) / len(results) if results else 0
            
            mode_summary[mode] = {
                "total": mode_total,
                "successful": mode_success,
                "llm_used": mode_llm,
                "complete_chain": mode_complete,
                "avg_confidence": avg_confidence,
                "avg_quality": avg_quality,
                "avg_time": avg_time
            }
            
            total_tests += mode_total
            successful_tests += mode_success
            llm_responses += mode_llm
            complete_chains += mode_complete
            
            logger.info(f"\n🤖 {mode} Mode Results:")
            logger.info(f"   Success Rate: {mode_success}/{mode_total} ({mode_success/mode_total*100:.1f}%)")
            logger.info(f"   LLM Usage: {mode_llm}/{mode_total} ({mode_llm/mode_total*100:.1f}%)")
            logger.info(f"   Complete Chain: {mode_complete}/{mode_total} ({mode_complete/mode_total*100:.1f}%)")
            logger.info(f"   Avg Confidence: {avg_confidence:.2f}")
            logger.info(f"   Avg Quality: {avg_quality:.2f}")
            logger.info(f"   Avg Time: {avg_time:.2f}s")
            
            # Show sample responses
            for i, result in enumerate(results[:1], 1):  # Show first result
                if result.get("success"):
                    logger.info(f"   Sample Response {i}: {result['response_text'][:100]}...")
        
        # Overall summary
        logger.info(f"\n🎯 OVERALL SUMMARY:")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Success Rate: {successful_tests}/{total_tests} ({successful_tests/total_tests*100:.1f}%)")
        logger.info(f"   Real LLM Responses: {llm_responses}/{total_tests} ({llm_responses/total_tests*100:.1f}%)")
        logger.info(f"   Complete Chain: {complete_chains}/{total_tests} ({complete_chains/total_tests*100:.1f}%)")
        
        # Chain verification status
        if complete_chains == total_tests:
            logger.info("✅ ALL MODES USING COMPLETE MESSAGE CHAIN WITH REAL LLM")
        elif llm_responses > 0:
            logger.info("⚠️ PARTIAL LLM INTEGRATION - Some modes using real LLM")
        else:
            logger.info("❌ NO REAL LLM RESPONSES - Still using mock responses")
        
        logger.info("="*80)
        
        # Save detailed report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "llm_responses": llm_responses,
                "complete_chains": complete_chains,
                "success_rate": successful_tests/total_tests*100 if total_tests > 0 else 0,
                "llm_usage_rate": llm_responses/total_tests*100 if total_tests > 0 else 0,
                "chain_completion_rate": complete_chains/total_tests*100 if total_tests > 0 else 0
            },
            "mode_results": mode_summary,
            "detailed_results": self.test_results
        }
        
        with open("message_chain_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        logger.info("📁 Detailed report saved to: message_chain_test_report.json")

async def main():
    """Run the complete message chain test"""
    tester = MessageChainTester()
    success = await tester.run_complete_test()
    
    if success:
        logger.info("🎉 Message chain test completed successfully!")
        return 0
    else:
        logger.error("❌ Message chain test failed!")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))