#!/usr/bin/env python3
"""
Enhanced Client Simulation for Aiayer System
===========================================

An improved version of the comprehensive client simulation that:
1. Handles all response types properly (including final_response)
2. Provides more detailed analysis of responses
3. Saves full responses for later review
4. Generates a more readable HTML report

Usage:
    python enhanced_client_simulation.py [--backend_url WS_URL] [--report_file FILENAME]
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
import sys
import html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/enhanced_simulation_{int(time.time())}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Test configuration
DEFAULT_WS_URL = "ws://localhost:8767"
DEFAULT_REPORT_PREFIX = f"enhanced_simulation_{int(time.time())}"
TIMEOUT = 240  # seconds
MODE_WEIGHTS = {
    "agent": 0.35,
    "ask": 0.40,
    "suggest": 0.25
}

class EnhancedSystemSimulation:
    """
    Enhanced simulation of client interactions with the Aiayer system.
    Tests memory capabilities, contextual understanding, and response quality.
    Handles all response types and generates detailed reports.
    """

    def __init__(self, backend_url: str, report_prefix: str):
        self.backend_url = backend_url
        self.report_prefix = report_prefix
        self.websocket = None
        self.session_id = f"enhanced_sim_{int(time.time())}"
        self.results = []
        self.raw_responses = {}
        self.mode_performance = {
            "agent": {"success": 0, "total": 0, "response_times": []},
            "ask": {"success": 0, "total": 0, "response_times": []},
            "suggest": {"success": 0, "total": 0, "response_times": []}
        }
        self.current_test = None
        self.test_scenarios = self._define_test_scenarios()
        
        # Ensure directories exist
        os.makedirs("reports", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("responses", exist_ok=True)

    def _define_test_scenarios(self) -> List[Dict[str, Any]]:
        """Define diverse test scenarios across all modes."""
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
        logger.info("STARTING ENHANCED SYSTEM SIMULATION")
        logger.info("=" * 60)
        logger.info(f"Testing {len(self.test_scenarios)} scenarios across all modes")
        
        start_time = time.time()
        
        # Run each test scenario
        for i, scenario in enumerate(self.test_scenarios, 1):
            logger.info("-" * 60)
            logger.info(f"Running test {i}/{len(self.test_scenarios)}: {scenario['id']} ({scenario['mode']} mode)")
            self.current_test = scenario
            
            # Run the test
            result = await self.run_test_scenario(scenario)
            self.results.append(result)
            
            # Save raw response for later analysis
            self.raw_responses[scenario["id"]] = result["raw_response"]
            
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
                await asyncio.sleep(3)
        
        total_time = time.time() - start_time
        
        # Generate final report
        report = self.generate_report(total_time)
        
        # Save report to file
        json_report_path = f"reports/{self.report_prefix}.json"
        with open(json_report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML report
        html_report_path = f"reports/{self.report_prefix}.html"
        self.generate_html_report(report, html_report_path)
        
        # Save raw responses
        raw_responses_path = f"responses/{self.report_prefix}_raw.json"
        with open(raw_responses_path, 'w') as f:
            json.dump(self.raw_responses, f, indent=2)
        
        logger.info("=" * 60)
        logger.info(f"Simulation complete. Reports saved to:")
        logger.info(f"- JSON: {json_report_path}")
        logger.info(f"- HTML: {html_report_path}")
        logger.info(f"- Raw responses: {raw_responses_path}")
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
                "type": "chat_request",
                "mode": mode,
                "message": message,
                "session_id": self.session_id
            }
            await self.websocket.send(json.dumps(request))
            
            # Collect all responses (may include progress updates)
            final_response = None
            response_parts = []
            progress_updates = []
            
            # Wait for complete response with timeout
            try:
                async with asyncio.timeout(TIMEOUT):
                    while True:
                        response = await self.websocket.recv()
                        try:
                            data = json.loads(response)
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON in response: {response[:100]}...")
                            continue
                        
                        # Log received message type
                        msg_type = data.get("type", "unknown")
                        logger.info(f"Received message type: {msg_type}")
                        
                        # Handle different message types
                        if msg_type == "response":
                            # Store response content
                            response_content = data.get("response", "")
                            response_parts.append(response_content)
                            final_response = data
                            
                            # If not streaming, this is the final response
                            if not data.get("streaming", False):
                                break
                                
                        elif msg_type == "final_response":
                            # This is the specific final response type used by this system
                            logger.info(f"Received final_response type message")
                            response_content = data.get("response", "")
                            response_parts.append(response_content)
                            final_response = data
                            break
                                
                        elif msg_type == "agent_response":
                            # Store agent response (for agent mode)
                            final_response = data
                            break
                            
                        elif msg_type == "stream_end":
                            # End of streaming response
                            break
                            
                        elif msg_type == "progress_update":
                            # Log progress update
                            progress = data.get("progress", 0)
                            stage = data.get("stage", "unknown")
                            logger.info(f"Progress update: {progress}% - {stage}")
                            progress_updates.append(data)
                            continue
                            
                        elif msg_type == "error":
                            # Handle error response
                            error_msg = data.get("message", "Unknown error")
                            logger.error(f"Error from backend: {error_msg}")
                            final_response = data
                            break
            
            except asyncio.TimeoutError:
                logger.error(f"Response timeout after {TIMEOUT} seconds")
                return {
                    "test_id": scenario["id"],
                    "mode": mode,
                    "message": message,
                    "response": None,
                    "raw_response": None,
                    "response_time": TIMEOUT,
                    "success": False,
                    "quality_score": 0,
                    "memory_score": 0,
                    "context_score": 0,
                    "explanation": "Response timed out",
                    "progress_updates": progress_updates
                }
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # If we have accumulated response parts, combine them
            combined_response = "".join(response_parts)
            if combined_response and (final_response is None or not final_response.get("response")):
                if final_response is None:
                    final_response = {"type": "combined", "response": combined_response}
                else:
                    final_response["response"] = combined_response
            
            # Evaluate response quality
            evaluation = self.evaluate_response(final_response, scenario, combined_response)
            
            # Save complete response for later analysis
            with open(f"responses/{scenario['id']}_{int(time.time())}.json", 'w') as f:
                json.dump({
                    "scenario": scenario,
                    "final_response": final_response,
                    "combined_response": combined_response,
                    "progress_updates": progress_updates,
                    "response_time": response_time,
                    "evaluation": evaluation
                }, f, indent=2)
            
            # Combine results
            result = {
                "test_id": scenario["id"],
                "mode": mode,
                "message": message,
                "response": final_response.get("response") if final_response else combined_response,
                "raw_response": final_response,
                "response_time": response_time,
                "success": evaluation["success"],
                "quality_score": evaluation["quality_score"],
                "memory_score": evaluation["memory_score"],
                "context_score": evaluation["context_score"],
                "explanation": evaluation["explanation"],
                "progress_updates": progress_updates,
                "keyword_matches": evaluation["keyword_matches"],
                "memory_matches": evaluation["memory_matches"],
                "context_matches": evaluation["context_matches"]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error during test: {e}")
            return {
                "test_id": scenario["id"],
                "mode": mode,
                "message": message,
                "response": None,
                "raw_response": None,
                "response_time": time.time() - start_time,
                "success": False,
                "quality_score": 0,
                "memory_score": 0, 
                "context_score": 0,
                "explanation": f"Error: {str(e)}",
                "progress_updates": [],
                "keyword_matches": [],
                "memory_matches": [],
                "context_matches": []
            }

    def evaluate_response(self, response: Dict[str, Any], scenario: Dict[str, Any], combined_response: str = "") -> Dict[str, Any]:
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
                "explanation": "No response received",
                "keyword_matches": [],
                "memory_matches": [],
                "context_matches": []
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
        
        # Use combined_response if available and response_text is empty
        if not response_text and combined_response:
            response_text = combined_response
        
        # Convert to lowercase for case-insensitive matching
        response_text_lower = response_text.lower() if response_text else ""
        
        # Check for expected keywords
        keyword_matches = []
        for keyword in scenario["expected_keywords"]:
            if keyword.lower() in response_text_lower:
                keyword_matches.append(keyword)
                
        keyword_score = len(keyword_matches) / len(scenario["expected_keywords"]) if scenario["expected_keywords"] else 0
        
        # Check for memory integration indicators
        memory_matches = []
        for indicator in scenario["memory_indicators"]:
            if indicator.lower() in response_text_lower:
                memory_matches.append(indicator)
                
        memory_score = len(memory_matches) / len(scenario["memory_indicators"]) if scenario["memory_indicators"] else 0
        
        # Check for contextual understanding indicators
        context_matches = []
        for indicator in scenario["context_indicators"]:
            if indicator.lower() in response_text_lower:
                context_matches.append(indicator)
                
        context_score = len(context_matches) / len(scenario["context_indicators"]) if scenario["context_indicators"] else 0
        
        # Calculate overall quality score (weighted)
        quality_score = 0.5 * keyword_score + 0.25 * memory_score + 0.25 * context_score
        
        # Determine success based on quality threshold
        success = success and quality_score >= 0.6
        
        # Generate explanation
        explanation = f"Found {len(keyword_matches)}/{len(scenario['expected_keywords'])} keywords, "
        explanation += f"{len(memory_matches)}/{len(scenario['memory_indicators'])} memory indicators, "
        explanation += f"{len(context_matches)}/{len(scenario['context_indicators'])} context indicators. "
        explanation += f"Overall quality: {quality_score:.2f}/1.0"
        
        return {
            "success": success,
            "quality_score": quality_score,
            "memory_score": memory_score,
            "context_score": context_score,
            "explanation": explanation,
            "keyword_matches": keyword_matches,
            "memory_matches": memory_matches,
            "context_matches": context_matches
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
        
        # Analyze response patterns
        response_patterns = self.analyze_response_patterns()
        
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
            "response_patterns": response_patterns,
            "test_results": self.results,
            "improvement_suggestions": self.generate_improvement_suggestions(system_score, mode_metrics)
        }
        
        return report

    def analyze_response_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in responses for additional insights."""
        responses_with_emoji = 0
        responses_starting_with_screen_state = 0
        responses_mentioning_email = 0
        responses_mentioning_file_manager = 0
        responses_with_data_sources = 0
        processing_methods = set()
        data_sources = set()
        
        for result in self.results:
            if result["response"]:
                # Check for emoji at start
                if "🤖" in result["response"]:
                    responses_with_emoji += 1
                
                # Check for common starting phrases
                if "based on your current screen state" in result["response"].lower():
                    responses_starting_with_screen_state += 1
                
                # Check for common mentions
                if "email" in result["response"].lower():
                    responses_mentioning_email += 1
                
                if "file manager" in result["response"].lower():
                    responses_mentioning_file_manager += 1
            
            # Check metadata from raw response
            if isinstance(result.get("raw_response"), dict):
                if "processing_method" in result["raw_response"]:
                    processing_methods.add(result["raw_response"]["processing_method"])
                    responses_with_data_sources += 1
                
                if "data_sources" in result["raw_response"]:
                    for source in result["raw_response"]["data_sources"]:
                        data_sources.add(source)
        
        return {
            "responses_with_emoji": responses_with_emoji,
            "responses_starting_with_screen_state": responses_starting_with_screen_state,
            "responses_mentioning_email": responses_mentioning_email,
            "responses_mentioning_file_manager": responses_mentioning_file_manager,
            "responses_with_data_sources": responses_with_data_sources,
            "processing_methods": list(processing_methods),
            "data_sources": list(data_sources)
        }

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

    def generate_html_report(self, report: Dict[str, Any], output_file: str) -> None:
        """Generate an HTML report with detailed results and visualizations."""
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aiayer System Evaluation Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #1a73e8;
        }}
        .header {{
            border-bottom: 2px solid #1a73e8;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .summary-box {{
            background-color: #f5f5f5;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
        }}
        .success {{
            color: #0f9d58;
        }}
        .failure {{
            color: #db4437;
        }}
        .warning {{
            color: #f4b400;
        }}
        .metrics-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .metric-box {{
            flex: 1;
            min-width: 200px;
            background-color: #f5f5f5;
            border-radius: 5px;
            padding: 15px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .mode-section {{
            margin-bottom: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .response {{
            background-color: #f9f9f9;
            border: 1px solid #ddd;
            padding: 10px;
            border-radius: 5px;
            margin: 10px 0;
            font-family: monospace;
            white-space: pre-wrap;
            max-height: 200px;
            overflow-y: auto;
        }}
        .suggestion {{
            background-color: #e8f0fe;
            border-left: 4px solid #1a73e8;
            padding: 10px 15px;
            margin: 10px 0;
        }}
        .patterns {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 20px;
        }}
        .pattern-box {{
            flex: 1;
            min-width: 150px;
            background-color: #f0f7ff;
            border-radius: 5px;
            padding: 10px;
            text-align: center;
        }}
        .pattern-value {{
            font-size: 20px;
            font-weight: bold;
            margin: 5px 0;
        }}
        .highlight {{
            background-color: yellow;
            padding: 0 2px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Aiayer System Evaluation Report</h1>
        <p>Test Session ID: {report['test_session_id']} | Date: {report['timestamp'][:19].replace('T', ' ')}</p>
    </div>
    
    <div class="summary-box">
        <h2>Executive Summary</h2>
        <div class="metrics-container">
            <div class="metric-box">
                <p>System Score</p>
                <p class="metric-value {'success' if report['system_score'] >= 0.7 else 'warning' if report['system_score'] >= 0.5 else 'failure'}">{report['system_score']:.2f}/1.0</p>
                <p>{report['performance_rating']}</p>
            </div>
            <div class="metric-box">
                <p>Success Rate</p>
                <p class="metric-value {'success' if report['overall_success_rate'] >= 0.7 else 'warning' if report['overall_success_rate'] >= 0.5 else 'failure'}">{report['overall_success_rate']*100:.1f}%</p>
                <p>{report['successful_tests']}/{report['total_tests']} tests passed</p>
            </div>
            <div class="metric-box">
                <p>Avg Response Time</p>
                <p class="metric-value {'success' if report['average_scores']['response_time'] < 10 else 'warning' if report['average_scores']['response_time'] < 20 else 'failure'}">{report['average_scores']['response_time']:.2f}s</p>
                <p>{'Fast' if report['average_scores']['response_time'] < 10 else 'Moderate' if report['average_scores']['response_time'] < 20 else 'Slow'}</p>
            </div>
        </div>
        
        <h3>Average Scores</h3>
        <div class="metrics-container">
            <div class="metric-box">
                <p>Quality</p>
                <p class="metric-value {'success' if report['average_scores']['quality'] >= 0.7 else 'warning' if report['average_scores']['quality'] >= 0.5 else 'failure'}">{report['average_scores']['quality']:.2f}/1.0</p>
            </div>
            <div class="metric-box">
                <p>Memory Integration</p>
                <p class="metric-value {'success' if report['average_scores']['memory_integration'] >= 0.7 else 'warning' if report['average_scores']['memory_integration'] >= 0.5 else 'failure'}">{report['average_scores']['memory_integration']:.2f}/1.0</p>
            </div>
            <div class="metric-box">
                <p>Contextual Understanding</p>
                <p class="metric-value {'success' if report['average_scores']['contextual_understanding'] >= 0.7 else 'warning' if report['average_scores']['contextual_understanding'] >= 0.5 else 'failure'}">{report['average_scores']['contextual_understanding']:.2f}/1.0</p>
            </div>
        </div>
    </div>
    
    <h2>Mode Performance</h2>
"""

        # Add mode-specific sections
        for mode, metrics in report['mode_performance'].items():
            if metrics['total_tests'] > 0:
                html_content += f"""
    <div class="mode-section">
        <h3>{mode.capitalize()} Mode</h3>
        <div class="metrics-container">
            <div class="metric-box">
                <p>Success Rate</p>
                <p class="metric-value {'success' if metrics['success_rate'] >= 0.7 else 'warning' if metrics['success_rate'] >= 0.5 else 'failure'}">{metrics['success_rate']*100:.1f}%</p>
                <p>{metrics['successful_tests']}/{metrics['total_tests']} tests passed</p>
            </div>
            <div class="metric-box">
                <p>Avg Response Time</p>
                <p class="metric-value {'success' if metrics['average_response_time'] < 10 else 'warning' if metrics['average_response_time'] < 20 else 'failure'}">{metrics['average_response_time']:.2f}s</p>
            </div>
            <div class="metric-box">
                <p>Quality Score</p>
                <p class="metric-value {'success' if metrics['average_quality_score'] >= 0.7 else 'warning' if metrics['average_quality_score'] >= 0.5 else 'failure'}">{metrics['average_quality_score']:.2f}/1.0</p>
            </div>
            <div class="metric-box">
                <p>Memory Score</p>
                <p class="metric-value {'success' if metrics['average_memory_score'] >= 0.7 else 'warning' if metrics['average_memory_score'] >= 0.5 else 'failure'}">{metrics['average_memory_score']:.2f}/1.0</p>
            </div>
            <div class="metric-box">
                <p>Context Score</p>
                <p class="metric-value {'success' if metrics['average_context_score'] >= 0.7 else 'warning' if metrics['average_context_score'] >= 0.5 else 'failure'}">{metrics['average_context_score']:.2f}/1.0</p>
            </div>
        </div>
    </div>
"""

        # Response patterns section
        patterns = report.get('response_patterns', {})
        html_content += f"""
    <h2>Response Patterns</h2>
    <div class="patterns">
        <div class="pattern-box">
            <p>Responses with Emoji</p>
            <p class="pattern-value">{patterns.get('responses_with_emoji', 0)}/{report['total_tests']}</p>
        </div>
        <div class="pattern-box">
            <p>Starting with "Screen State"</p>
            <p class="pattern-value">{patterns.get('responses_starting_with_screen_state', 0)}/{report['total_tests']}</p>
        </div>
        <div class="pattern-box">
            <p>Mentioning Email</p>
            <p class="pattern-value">{patterns.get('responses_mentioning_email', 0)}/{report['total_tests']}</p>
        </div>
        <div class="pattern-box">
            <p>Mentioning File Manager</p>
            <p class="pattern-value">{patterns.get('responses_mentioning_file_manager', 0)}/{report['total_tests']}</p>
        </div>
    </div>
    
    <p><strong>Processing Methods:</strong> {', '.join(patterns.get('processing_methods', []))}</p>
    <p><strong>Data Sources:</strong> {', '.join(patterns.get('data_sources', []))}</p>
    
    <h2>Improvement Suggestions</h2>
"""

        # Add improvement suggestions
        for suggestion in report['improvement_suggestions']:
            html_content += f"""
    <div class="suggestion">
        <p>{suggestion}</p>
    </div>
"""

        # Add detailed test results
        html_content += """
    <h2>Detailed Test Results</h2>
    <table>
        <tr>
            <th>Test ID</th>
            <th>Mode</th>
            <th>Message</th>
            <th>Result</th>
            <th>Time</th>
            <th>Quality</th>
            <th>Details</th>
        </tr>
"""

        for result in report['test_results']:
            status_class = "success" if result["success"] else "failure"
            quality_class = "success" if result["quality_score"] >= 0.7 else "warning" if result["quality_score"] >= 0.5 else "failure"
            
            # Format response preview
            response_preview = html.escape(result["response"][:100] + "..." if result["response"] and len(result["response"]) > 100 else result["response"] or "")
            
            html_content += f"""
        <tr>
            <td>{result["test_id"]}</td>
            <td>{result["mode"]}</td>
            <td>{html.escape(result["message"])}</td>
            <td class="{status_class}">{"✅ PASS" if result["success"] else "❌ FAIL"}</td>
            <td>{result["response_time"]:.2f}s</td>
            <td class="{quality_class}">{result["quality_score"]:.2f}/1.0</td>
            <td>{result["explanation"]}</td>
        </tr>
"""

        # Close HTML
        html_content += """
    </table>
    
    <h2>Test Responses</h2>
"""

        # Add each test response
        for result in report['test_results']:
            response_text = result["response"] or ""
            
            # Highlight matches in response
            highlighted_response = html.escape(response_text)
            
            # Add test response section
            html_content += f"""
    <div>
        <h3>Test: {result["test_id"]} ({result["mode"]} mode)</h3>
        <p><strong>Message:</strong> {html.escape(result["message"])}</p>
        <p><strong>Result:</strong> <span class="{status_class}">{"✅ PASS" if result["success"] else "❌ FAIL"}</span> (Quality: {result["quality_score"]:.2f}/1.0, Time: {result["response_time"]:.2f}s)</p>
        
        <div class="response">{highlighted_response}</div>
        
        <p><strong>Keyword Matches:</strong> {", ".join(result.get("keyword_matches", []) or ["None"])}</p>
        <p><strong>Memory Indicators:</strong> {", ".join(result.get("memory_matches", []) or ["None"])}</p>
        <p><strong>Context Indicators:</strong> {", ".join(result.get("context_matches", []) or ["None"])}</p>
    </div>
"""

        # Finish HTML
        html_content += """
    <div class="footer">
        <p>Report generated on: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    </div>
</body>
</html>
"""

        # Write HTML to file
        with open(output_file, 'w') as f:
            f.write(html_content)

async def main():
    """Main function to run the simulation."""
    parser = argparse.ArgumentParser(description='Run an enhanced client simulation test')
    parser.add_argument('--backend_url', type=str, default=DEFAULT_WS_URL,
                        help=f'WebSocket URL of the backend (default: {DEFAULT_WS_URL})')
    parser.add_argument('--report_prefix', type=str, default=DEFAULT_REPORT_PREFIX,
                        help=f'Prefix for report files (default: {DEFAULT_REPORT_PREFIX})')
    args = parser.parse_args()
    
    # Run simulation
    simulation = EnhancedSystemSimulation(args.backend_url, args.report_prefix)
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
    
    print("\nDetailed reports saved to:")
    print(f"- JSON: reports/{args.report_prefix}.json")
    print(f"- HTML: reports/{args.report_prefix}.html")
    print(f"- Raw responses: responses/{args.report_prefix}_raw.json")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())