#!/usr/bin/env python3
"""
Comprehensive Client Simulation
==============================

This script performs a comprehensive evaluation of the Aiayer system by simulating
10 different user interactions across all modes (agent, ask, suggest) and
measuring response quality, memory integration, and contextual understanding.

Usage:
    python comprehensive_client_simulation.py [--backend_url WS_URL] [--report_file FILENAME]

The script will:
1. Connect to the backend
2. Run 10 diverse test scenarios
3. Evaluate responses based on quality metrics
4. Generate a detailed performance report
"""

import asyncio
import json
import logging
import os
import random
import time
import websockets
import argparse
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/simulation_test_{int(time.time())}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Test configuration
DEFAULT_WS_URL = "ws://localhost:8767"
DEFAULT_REPORT_FILE = f"simulation_results_{int(time.time())}.json"
TIMEOUT = 240  # seconds (4 minutes) - based on observed response times of ~30s per query with some buffer
MODE_WEIGHTS = {
    "agent": 0.35,
    "ask": 0.40,
    "suggest": 0.25
}

class SystemSimulation:
    """
    Comprehensive simulation of client interactions with the Aiayer system.
    Tests memory capabilities, contextual understanding, and response quality.
    """

    def __init__(self, backend_url: str, report_file: str):
        self.backend_url = backend_url
        self.report_file = report_file
        self.websocket = None
        self.session_id = f"sim_{int(time.time())}"
        self.results = []
        self.mode_performance = {
            "agent": {"success": 0, "total": 0, "response_times": []},
            "ask": {"success": 0, "total": 0, "response_times": []},
            "suggest": {"success": 0, "total": 0, "response_times": []}
        }
        self.current_test = None
        self.test_scenarios = self._define_test_scenarios()

    def _define_test_scenarios(self) -> List[Dict[str, Any]]:
        """Define 10 diverse test scenarios across all modes."""
        return [
            # Agent Mode Tests (3)
            {
                "id": "agent_ui_interaction",
                "mode": "agent",
                "message": "search for flights to Miami on Google",
                "expected_keywords": ["Google", "search", "flight", "Miami"],
                "memory_indicators": ["browser", "navigation", "search engine"],
                "context_indicators": ["opening browser", "navigating to", "typing"],
                "description": "Tests agent mode's ability to interact with UI and execute complex tasks"
            },
            {
                "id": "agent_app_launch",
                "mode": "agent",
                "message": "open Safari and go to YouTube",
                "expected_keywords": ["Safari", "YouTube", "browser", "navigate"],
                "memory_indicators": ["application", "browser", "video"],
                "context_indicators": ["launching", "opening", "navigating"],
                "description": "Tests agent mode's ability to launch applications and navigate to websites"
            },
            {
                "id": "agent_complex_task",
                "mode": "agent",
                "message": "search for Omer Adam on Spotify and play his music",
                "expected_keywords": ["Spotify", "search", "Omer Adam", "music", "play"],
                "memory_indicators": ["music", "application", "audio"],
                "context_indicators": ["playing", "searching", "artist"],
                "description": "Tests agent mode's ability to perform multi-step tasks in music applications"
            },
            
            # Ask Mode Tests (4)
            {
                "id": "ask_system_status",
                "mode": "ask",
                "message": "what applications are currently running on my system?",
                "expected_keywords": ["applications", "running", "system", "active"],
                "memory_indicators": ["process", "memory", "sensor"],
                "context_indicators": ["currently", "active", "detected"],
                "description": "Tests ask mode's ability to report on system status from memory"
            },
            {
                "id": "ask_memory_retrieval",
                "mode": "ask",
                "message": "what websites have I visited recently?",
                "expected_keywords": ["websites", "visited", "browser", "recently"],
                "memory_indicators": ["browsing history", "visited", "website"],
                "context_indicators": ["recently", "detected", "browser"],
                "description": "Tests ask mode's ability to retrieve browsing history from memory"
            },
            {
                "id": "ask_context_understanding",
                "mode": "ask",
                "message": "what's currently visible on my screen?",
                "expected_keywords": ["screen", "visible", "display", "showing"],
                "memory_indicators": ["screen sensor", "visual", "ui"],
                "context_indicators": ["currently", "visible", "displayed"],
                "description": "Tests ask mode's ability to understand and describe current screen context"
            },
            {
                "id": "ask_memory_integration",
                "mode": "ask",
                "message": "how has my system usage changed in the last hour?",
                "expected_keywords": ["system", "usage", "changed", "hour"],
                "memory_indicators": ["memory", "history", "tracking"],
                "context_indicators": ["changed", "compared", "over time"],
                "description": "Tests ask mode's ability to integrate memory over time for analysis"
            },
            
            # Suggest Mode Tests (3)
            {
                "id": "suggest_productivity",
                "mode": "suggest",
                "message": "I need to organize my work better",
                "expected_keywords": ["organize", "work", "productivity", "suggestion"],
                "memory_indicators": ["applications", "tools", "workflow"],
                "context_indicators": ["might help", "consider", "try"],
                "description": "Tests suggest mode's ability to provide contextual productivity recommendations"
            },
            {
                "id": "suggest_application",
                "mode": "suggest",
                "message": "I want to edit some photos",
                "expected_keywords": ["edit", "photos", "image", "application"],
                "memory_indicators": ["applications", "photo editing", "images"],
                "context_indicators": ["suggest", "recommendation", "try"],
                "description": "Tests suggest mode's ability to recommend appropriate applications"
            },
            {
                "id": "suggest_content",
                "mode": "suggest",
                "message": "I'm bored and want to watch something interesting",
                "expected_keywords": ["watch", "video", "content", "entertainment"],
                "memory_indicators": ["viewing history", "preferences", "content"],
                "context_indicators": ["might enjoy", "based on", "recommendation"],
                "description": "Tests suggest mode's ability to recommend content based on preferences"
            }
        ]

    async def connect(self) -> bool:
        """Connect to the backend websocket server."""
        try:
            logger.info(f"Connecting to backend at {self.backend_url}")
            self.websocket = await websockets.connect(self.backend_url)
            
            # Wait for the connection established message
            connection_message = await self.websocket.recv()
            try:
                data = json.loads(connection_message)
                if data.get("type") == "connection_established":
                    client_id = data.get("client_id", "unknown")
                    logger.info(f"Successfully connected to backend with client ID: {client_id}")
                    return True
                else:
                    logger.warning(f"Unexpected connection message: {data.get('type', 'unknown')}")
                    return False
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in connection message: {connection_message[:100]}...")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to backend: {e}")
            return False

    async def run_simulation(self) -> Dict[str, Any]:
        """Run the complete simulation with all test scenarios."""
        if not await self.connect():
            return {"success": False, "error": "Failed to connect to backend"}

        logger.info("=" * 60)
        logger.info("STARTING COMPREHENSIVE SYSTEM SIMULATION")
        logger.info("=" * 60)
        logger.info(f"Testing {len(self.test_scenarios)} scenarios across all modes")
        
        start_time = time.time()
        
        # Run each test scenario
        for i, scenario in enumerate(self.test_scenarios, 1):
            logger.info("-" * 60)
            logger.info(f"Running test {i}/10: {scenario['id']} ({scenario['mode']} mode)")
            self.current_test = scenario
            
            # Run the test
            result = await self.run_test_scenario(scenario)
            self.results.append(result)
            
            # Update mode-specific metrics
            mode = scenario["mode"]
            self.mode_performance[mode]["total"] += 1
            if result["success"]:
                self.mode_performance[mode]["success"] += 1
            self.mode_performance[mode]["response_times"].append(result["response_time"])
            
            # Log result summary
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            logger.info(f"Test {i}: {status} - Quality: {result['quality_score']:.2f}/1.0 - Time: {result['response_time']:.2f}s")
            
            # Pause between tests to avoid overwhelming the system
            if i < len(self.test_scenarios):
                await asyncio.sleep(2)
        
        total_time = time.time() - start_time
        
        # Generate final report
        report = self.generate_report(total_time)
        
        # Save report to file
        with open(self.report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("=" * 60)
        logger.info(f"Simulation complete. Report saved to {self.report_file}")
        logger.info("=" * 60)
        
        # Close the connection
        if self.websocket:
            await self.websocket.close()
        
        return report

    async def run_test_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single test scenario and evaluate the response."""
        mode = scenario["mode"]
        message = scenario["message"]
        
        logger.info(f"Sending message in {mode} mode: '{message}'")
        
        # Record start time
        start_time = time.time()
        
        # Send request
        try:
            request = {
                "type": "chat_request",  # FIXED: Changed from "request" to "chat_request"
                "mode": mode,
                "message": message,
                "session_id": self.session_id
            }
            await self.websocket.send(json.dumps(request))
            
            # Collect all responses (may include progress updates)
            final_response = None
            response_parts = []
            
            # Wait for complete response with timeout
            try:
                async with asyncio.timeout(TIMEOUT):
                    while True:
                        response = await self.websocket.recv()
                        data = json.loads(response)
                        
                        # Log received message type
                        logger.debug(f"Received message type: {data.get('type', 'unknown')}")
                        
                        # Handle different message types
                        if data.get("type") == "response":
                            # Store response content
                            response_content = data.get("response", "")
                            response_parts.append(response_content)
                            final_response = data
                            
                            # If not streaming, this is the final response
                            if not data.get("streaming", False):
                                break
                                
                        elif data.get("type") == "final_response":
                            # This is the specific final response type used by this system
                            logger.info(f"Received final_response type message")
                            response_content = data.get("response", "")
                            response_parts.append(response_content)
                            final_response = data
                            break
                                
                        elif data.get("type") == "agent_response":
                            # Store agent response (for agent mode)
                            final_response = data
                            break
                            
                        elif data.get("type") == "stream_end":
                            # End of streaming response
                            break
                            
                        elif data.get("type") == "progress_update":
                            # Progress update, continue waiting for final response
                            logger.info(f"Progress update: {data.get('stage', 'unknown')}")
                            continue
                            
                        elif data.get("type") == "error":
                            # Handle error response
                            logger.error(f"Error from backend: {data.get('message', 'Unknown error')}")
                            final_response = data
                            break
            
            except asyncio.TimeoutError:
                logger.error(f"Response timeout after {TIMEOUT} seconds")
                return {
                    "test_id": scenario["id"],
                    "mode": mode,
                    "message": message,
                    "response": None,
                    "response_time": TIMEOUT,
                    "success": False,
                    "quality_score": 0,
                    "memory_score": 0,
                    "context_score": 0,
                    "explanation": "Response timed out"
                }
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # If we have accumulated response parts, combine them
            if response_parts and not final_response.get("response"):
                final_response["response"] = "".join(response_parts)
            
            # Evaluate response quality
            evaluation = self.evaluate_response(final_response, scenario)
            
            # Combine results
            result = {
                "test_id": scenario["id"],
                "mode": mode,
                "message": message,
                "response": final_response,
                "response_time": response_time,
                "success": evaluation["success"],
                "quality_score": evaluation["quality_score"],
                "memory_score": evaluation["memory_score"],
                "context_score": evaluation["context_score"],
                "explanation": evaluation["explanation"]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error during test: {e}")
            return {
                "test_id": scenario["id"],
                "mode": mode,
                "message": message,
                "response": None,
                "response_time": time.time() - start_time,
                "success": False,
                "quality_score": 0,
                "memory_score": 0, 
                "context_score": 0,
                "explanation": f"Error: {str(e)}"
            }

    def evaluate_response(self, response: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the quality of the response based on expected content,
        memory integration, and contextual understanding.
        """
        mode = scenario["mode"]
        
        # Handle None response (timeout or error)
        if response is None:
            return {
                "success": False,
                "quality_score": 0,
                "memory_score": 0,
                "context_score": 0,
                "explanation": "No response received"
            }
            
        # Extract response content based on response type
        if mode == "agent":
            # For agent mode, check for plan and steps
            if response.get("type") == "agent_response":
                response_text = json.dumps(response.get("plan", {}))
                success = "plan" in response and "steps" in response.get("plan", {})
            else:
                response_text = response.get("response", "")
                success = response.get("success", False)
        else:
            # For ask and suggest modes
            response_text = response.get("response", "")
            success = response.get("success", False) or bool(response_text)
        
        # Convert to lowercase for case-insensitive matching
        response_text_lower = response_text.lower()
        
        # Check for expected keywords
        keyword_matches = 0
        for keyword in scenario["expected_keywords"]:
            if keyword.lower() in response_text_lower:
                keyword_matches += 1
                
        keyword_score = keyword_matches / len(scenario["expected_keywords"]) if scenario["expected_keywords"] else 0
        
        # Check for memory integration indicators
        memory_matches = 0
        for indicator in scenario["memory_indicators"]:
            if indicator.lower() in response_text_lower:
                memory_matches += 1
                
        memory_score = memory_matches / len(scenario["memory_indicators"]) if scenario["memory_indicators"] else 0
        
        # Check for contextual understanding indicators
        context_matches = 0
        for indicator in scenario["context_indicators"]:
            if indicator.lower() in response_text_lower:
                context_matches += 1
                
        context_score = context_matches / len(scenario["context_indicators"]) if scenario["context_indicators"] else 0
        
        # Calculate overall quality score (weighted)
        quality_score = 0.5 * keyword_score + 0.25 * memory_score + 0.25 * context_score
        
        # Determine success based on quality threshold
        success = success and quality_score >= 0.6
        
        # Generate explanation
        explanation = f"Found {keyword_matches}/{len(scenario['expected_keywords'])} keywords, "
        explanation += f"{memory_matches}/{len(scenario['memory_indicators'])} memory indicators, "
        explanation += f"{context_matches}/{len(scenario['context_indicators'])} context indicators. "
        explanation += f"Overall quality: {quality_score:.2f}/1.0"
        
        return {
            "success": success,
            "quality_score": quality_score,
            "memory_score": memory_score,
            "context_score": context_score,
            "explanation": explanation
        }

    def generate_report(self, total_time: float) -> Dict[str, Any]:
        """Generate a comprehensive performance report."""
        # Calculate overall success rate
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        success_rate = successful_tests / total_tests if total_tests > 0 else 0
        
        # Calculate average scores
        avg_quality = sum(r["quality_score"] for r in self.results) / total_tests if total_tests > 0 else 0
        avg_memory = sum(r["memory_score"] for r in self.results) / total_tests if total_tests > 0 else 0
        avg_context = sum(r["context_score"] for r in self.results) / total_tests if total_tests > 0 else 0
        
        # Calculate average response time
        avg_response_time = sum(r["response_time"] for r in self.results) / total_tests if total_tests > 0 else 0
        
        # Calculate mode-specific metrics
        mode_metrics = {}
        for mode, data in self.mode_performance.items():
            if data["total"] > 0:
                success_rate = data["success"] / data["total"]
                avg_time = sum(data["response_times"]) / data["total"] if data["response_times"] else 0
                
                # Calculate mode-specific scores
                mode_results = [r for r in self.results if r["mode"] == mode]
                avg_quality = sum(r["quality_score"] for r in mode_results) / len(mode_results) if mode_results else 0
                avg_memory = sum(r["memory_score"] for r in mode_results) / len(mode_results) if mode_results else 0
                avg_context = sum(r["context_score"] for r in mode_results) / len(mode_results) if mode_results else 0
                
                mode_metrics[mode] = {
                    "success_rate": success_rate,
                    "total_tests": data["total"],
                    "successful_tests": data["success"],
                    "average_response_time": avg_time,
                    "average_quality_score": avg_quality,
                    "average_memory_score": avg_memory,
                    "average_context_score": avg_context
                }
            else:
                mode_metrics[mode] = {
                    "success_rate": 0,
                    "total_tests": 0,
                    "successful_tests": 0,
                    "average_response_time": 0,
                    "average_quality_score": 0,
                    "average_memory_score": 0,
                    "average_context_score": 0
                }
        
        # Calculate weighted system score
        system_score = 0
        for mode, weight in MODE_WEIGHTS.items():
            if mode in mode_metrics and mode_metrics[mode]["total_tests"] > 0:
                mode_score = (mode_metrics[mode]["success_rate"] * 0.4 + 
                             mode_metrics[mode]["average_quality_score"] * 0.3 + 
                             mode_metrics[mode]["average_memory_score"] * 0.15 + 
                             mode_metrics[mode]["average_context_score"] * 0.15)
                system_score += mode_score * weight
        
        # Determine performance rating
        if system_score >= 0.9:
            rating = "Excellent"
        elif system_score >= 0.8:
            rating = "Very Good"
        elif system_score >= 0.7:
            rating = "Good"
        elif system_score >= 0.6:
            rating = "Satisfactory"
        elif system_score >= 0.5:
            rating = "Needs Improvement"
        else:
            rating = "Poor"
        
        # Create report
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_session_id": self.session_id,
            "backend_url": self.backend_url,
            "total_time": total_time,
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "overall_success_rate": success_rate,
            "system_score": system_score,
            "performance_rating": rating,
            "average_scores": {
                "quality": avg_quality,
                "memory_integration": avg_memory,
                "contextual_understanding": avg_context,
                "response_time": avg_response_time
            },
            "mode_performance": mode_metrics,
            "test_results": self.results,
            "improvement_suggestions": self.generate_improvement_suggestions(system_score, mode_metrics)
        }
        
        return report

    def generate_improvement_suggestions(self, system_score: float, mode_metrics: Dict[str, Any]) -> List[str]:
        """Generate specific improvement suggestions based on test results."""
        suggestions = []
        
        # Overall performance suggestions
        if system_score < 0.7:
            suggestions.append("Overall system performance needs significant improvement. Consider reviewing the core architecture.")
        
        # Mode-specific suggestions
        for mode, metrics in mode_metrics.items():
            # Skip modes with no tests
            if metrics["total_tests"] == 0:
                continue
                
            # Low success rate
            if metrics["success_rate"] < 0.7:
                suggestions.append(f"{mode.capitalize()} mode has a low success rate ({metrics['success_rate']:.2f}). Review error handling and response generation.")
            
            # Slow response time
            if mode == "agent" and metrics["average_response_time"] > 15:
                suggestions.append(f"{mode.capitalize()} mode response time is high ({metrics['average_response_time']:.2f}s). Consider optimizing planning algorithms and adding warmup procedures.")
            elif mode != "agent" and metrics["average_response_time"] > 5:
                suggestions.append(f"{mode.capitalize()} mode response time is high ({metrics['average_response_time']:.2f}s). Review query optimization and response generation.")
            
            # Poor memory integration
            if metrics["average_memory_score"] < 0.6:
                suggestions.append(f"{mode.capitalize()} mode shows weak memory integration ({metrics['average_memory_score']:.2f}). Improve memory retrieval relevance and integration.")
            
            # Poor context understanding
            if metrics["average_context_score"] < 0.6:
                suggestions.append(f"{mode.capitalize()} mode shows weak contextual understanding ({metrics['average_context_score']:.2f}). Enhance context processing and relevance algorithms.")
        
        # Add general suggestions if overall performance is good
        if system_score >= 0.7:
            suggestions.append("Consider implementing more sophisticated memory pruning algorithms to improve relevance.")
            suggestions.append("Enhance cross-modal context fusion for better integration of different memory types.")
        
        return suggestions

async def main():
    """Main function to run the simulation."""
    parser = argparse.ArgumentParser(description='Run a comprehensive client simulation test')
    parser.add_argument('--backend_url', type=str, default=DEFAULT_WS_URL,
                        help=f'WebSocket URL of the backend (default: {DEFAULT_WS_URL})')
    parser.add_argument('--report_file', type=str, default=DEFAULT_REPORT_FILE,
                        help=f'Filename for the JSON report (default: {DEFAULT_REPORT_FILE})')
    args = parser.parse_args()
    
    # Create reports directory if it doesn't exist
    os.makedirs('reports', exist_ok=True)
    report_path = os.path.join('reports', args.report_file)
    
    # Run simulation
    simulation = SystemSimulation(args.backend_url, report_path)
    report = await simulation.run_simulation()
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"SIMULATION SUMMARY")
    print("=" * 60)
    print(f"System Score: {report['system_score']:.2f}/1.0 - Rating: {report['performance_rating']}")
    print(f"Success Rate: {report['overall_success_rate']*100:.1f}% ({report['successful_tests']}/{report['total_tests']} tests passed)")
    print(f"Average Response Time: {report['average_scores']['response_time']:.2f}s")
    print("\nMode Performance:")
    for mode, metrics in report['mode_performance'].items():
        if metrics['total_tests'] > 0:
            print(f"  - {mode.capitalize()}: {metrics['success_rate']*100:.1f}% success, {metrics['average_response_time']:.2f}s avg time")
    
    print("\nTop Improvement Suggestions:")
    for i, suggestion in enumerate(report['improvement_suggestions'][:3], 1):
        print(f"  {i}. {suggestion}")
    
    print("\nDetailed report saved to:", report_path)
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())