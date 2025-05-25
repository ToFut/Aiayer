#!/usr/bin/env python3
"""
Comprehensive Model Quality Comparison and System Flow Analysis
Tests all available Ollama models for quality, speed, and system impact
"""

import asyncio
import json
import time
import requests
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelComparator:
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.models = []
        self.test_prompts = [
            {
                "type": "simple_question",
                "prompt": "What is artificial intelligence?",
                "expected_aspects": ["definition", "explanation", "examples"]
            },
            {
                "type": "complex_analysis", 
                "prompt": "Analyze the pros and cons of remote work for software development teams",
                "expected_aspects": ["multiple perspectives", "detailed analysis", "balanced view"]
            },
            {
                "type": "technical_explanation",
                "prompt": "Explain how WebSockets work and their advantages over HTTP polling",
                "expected_aspects": ["technical accuracy", "clear explanation", "comparison"]
            },
            {
                "type": "creative_task",
                "prompt": "Write a brief story about an AI that learns to paint",
                "expected_aspects": ["creativity", "narrative flow", "coherence"]
            },
            {
                "type": "problem_solving",
                "prompt": "A user reports their web app is slow. What debugging steps would you recommend?",
                "expected_aspects": ["systematic approach", "multiple solutions", "practical advice"]
            }
        ]
        
    def get_available_models(self):
        """Fetch all available Ollama models"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.models = [model['name'] for model in data.get('models', [])]
                logger.info(f"Found {len(self.models)} models: {self.models}")
                return self.models
            else:
                logger.error(f"Failed to fetch models: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            return []

    def test_model_response(self, model_name, prompt, max_tokens=500):
        """Test a single model with a prompt and measure performance"""
        start_time = time.time()
        first_token_time = None
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7
                    }
                },
                timeout=120  # 2 minute timeout
            )
            
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                return {
                    "success": True,
                    "response": response_text,
                    "response_time": end_time - start_time,
                    "token_count": len(response_text.split()),
                    "tokens_per_second": len(response_text.split()) / (end_time - start_time) if end_time > start_time else 0
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "response_time": end_time - start_time
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Timeout (120s)",
                "response_time": 120
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }

    def analyze_response_quality(self, response_text, prompt_info):
        """Analyze response quality based on multiple criteria"""
        if not response_text:
            return {"overall_score": 0, "details": "No response"}
            
        # Quality metrics
        scores = {}
        
        # 1. Length appropriateness (not too short, not too verbose)
        word_count = len(response_text.split())
        if 50 <= word_count <= 300:
            scores["length"] = 10
        elif 30 <= word_count < 50 or 300 < word_count <= 500:
            scores["length"] = 8
        elif 15 <= word_count < 30 or 500 < word_count <= 800:
            scores["length"] = 6
        else:
            scores["length"] = 4
            
        # 2. Structure and coherence
        sentences = response_text.split('.')
        if len(sentences) >= 3 and any(len(s.strip()) > 10 for s in sentences):
            scores["structure"] = 9
        elif len(sentences) >= 2:
            scores["structure"] = 7
        else:
            scores["structure"] = 5
            
        # 3. Relevance to prompt
        prompt_words = set(prompt_info["prompt"].lower().split())
        response_words = set(response_text.lower().split())
        relevance_overlap = len(prompt_words.intersection(response_words)) / len(prompt_words)
        scores["relevance"] = min(10, int(relevance_overlap * 15))
        
        # 4. Technical accuracy (basic check for technical terms)
        if prompt_info["type"] == "technical_explanation":
            tech_terms = ["websocket", "http", "protocol", "connection", "server", "client"]
            found_terms = sum(1 for term in tech_terms if term.lower() in response_text.lower())
            scores["technical"] = min(10, found_terms * 2)
        else:
            scores["technical"] = 8  # Default for non-technical prompts
            
        # 5. Completeness
        expected_aspects = prompt_info.get("expected_aspects", [])
        if expected_aspects:
            found_aspects = sum(1 for aspect in expected_aspects 
                             if any(word in response_text.lower() for word in aspect.split()))
            scores["completeness"] = min(10, (found_aspects / len(expected_aspects)) * 12)
        else:
            scores["completeness"] = 8
            
        # Calculate overall score
        overall_score = sum(scores.values()) / len(scores)
        
        return {
            "overall_score": round(overall_score, 1),
            "detailed_scores": scores,
            "word_count": word_count,
            "analysis": f"Quality: {overall_score:.1f}/10 (Length: {scores['length']}/10, Structure: {scores['structure']}/10, Relevance: {scores['relevance']}/10)"
        }

    def run_comprehensive_comparison(self):
        """Run complete model comparison"""
        logger.info("Starting comprehensive model comparison...")
        
        # Get available models
        if not self.get_available_models():
            logger.error("No models available for testing")
            return
            
        results = {
            "timestamp": datetime.now().isoformat(),
            "models_tested": len(self.models),
            "test_prompts": len(self.test_prompts),
            "results": {}
        }
        
        # Test each model
        for model in self.models:
            logger.info(f"\nTesting model: {model}")
            model_results = {
                "model_name": model,
                "prompt_results": [],
                "avg_response_time": 0,
                "avg_quality_score": 0,
                "avg_tokens_per_second": 0,
                "success_rate": 0
            }
            
            successful_tests = 0
            total_time = 0
            total_quality = 0
            total_tps = 0
            
            # Test with each prompt
            for i, prompt_info in enumerate(self.test_prompts):
                logger.info(f"  Prompt {i+1}/{len(self.test_prompts)}: {prompt_info['type']}")
                
                test_result = self.test_model_response(model, prompt_info["prompt"])
                
                if test_result["success"]:
                    quality_analysis = self.analyze_response_quality(
                        test_result["response"], prompt_info
                    )
                    
                    prompt_result = {
                        "prompt_type": prompt_info["type"],
                        "prompt": prompt_info["prompt"],
                        "response_time": test_result["response_time"],
                        "tokens_per_second": test_result["tokens_per_second"],
                        "quality_score": quality_analysis["overall_score"],
                        "quality_details": quality_analysis,
                        "response_preview": test_result["response"][:200] + "..." if len(test_result["response"]) > 200 else test_result["response"]
                    }
                    
                    successful_tests += 1
                    total_time += test_result["response_time"]
                    total_quality += quality_analysis["overall_score"]
                    total_tps += test_result["tokens_per_second"]
                    
                else:
                    prompt_result = {
                        "prompt_type": prompt_info["type"],
                        "prompt": prompt_info["prompt"],
                        "error": test_result["error"],
                        "response_time": test_result["response_time"],
                        "quality_score": 0
                    }
                
                model_results["prompt_results"].append(prompt_result)
                
                # Small delay between requests
                time.sleep(2)
            
            # Calculate averages
            if successful_tests > 0:
                model_results["avg_response_time"] = total_time / successful_tests
                model_results["avg_quality_score"] = total_quality / successful_tests
                model_results["avg_tokens_per_second"] = total_tps / successful_tests
                model_results["success_rate"] = (successful_tests / len(self.test_prompts)) * 100
            
            results["results"][model] = model_results
            
            logger.info(f"  Model {model} completed:")
            logger.info(f"    Success rate: {model_results['success_rate']:.1f}%")
            logger.info(f"    Avg response time: {model_results['avg_response_time']:.1f}s")
            logger.info(f"    Avg quality score: {model_results['avg_quality_score']:.1f}/10")
            logger.info(f"    Avg tokens/sec: {model_results['avg_tokens_per_second']:.1f}")
        
        # Generate analysis report
        self.generate_analysis_report(results)
        
        # Save detailed results
        with open("comprehensive_model_comparison_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"\nComparison complete! Results saved to comprehensive_model_comparison_results.json")
        return results

    def generate_analysis_report(self, results):
        """Generate human-readable analysis report"""
        
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE MODEL QUALITY COMPARISON REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {results['timestamp']}")
        report.append(f"Models tested: {results['models_tested']}")
        report.append(f"Test prompts: {results['test_prompts']}")
        report.append("")
        
        # Sort models by overall performance
        model_performance = []
        for model, data in results["results"].items():
            if data["success_rate"] > 0:
                # Calculate composite score (quality weighted more heavily)
                composite_score = (
                    data["avg_quality_score"] * 0.5 +  # 50% quality
                    (10 - min(10, data["avg_response_time"] / 10)) * 0.3 +  # 30% speed
                    (data["success_rate"] / 10) * 0.2  # 20% reliability
                )
                model_performance.append((model, composite_score, data))
        
        model_performance.sort(key=lambda x: x[1], reverse=True)
        
        # Model rankings
        report.append("MODEL RANKINGS (by composite performance score):")
        report.append("-" * 50)
        for i, (model, score, data) in enumerate(model_performance):
            report.append(f"{i+1}. {model}")
            report.append(f"   Composite Score: {score:.1f}/10")
            report.append(f"   Quality: {data['avg_quality_score']:.1f}/10")
            report.append(f"   Speed: {data['avg_response_time']:.1f}s")
            report.append(f"   Reliability: {data['success_rate']:.1f}%")
            report.append(f"   Tokens/sec: {data['avg_tokens_per_second']:.1f}")
            report.append("")
        
        # Detailed quality analysis
        report.append("DETAILED QUALITY ANALYSIS:")
        report.append("-" * 30)
        
        for model, _, data in model_performance:
            report.append(f"\n{model.upper()}:")
            for prompt_result in data["prompt_results"]:
                if "quality_score" in prompt_result and prompt_result["quality_score"] > 0:
                    report.append(f"  {prompt_result['prompt_type']}: {prompt_result['quality_score']:.1f}/10")
                    report.append(f"    Time: {prompt_result['response_time']:.1f}s")
                    report.append(f"    Preview: {prompt_result['response_preview']}")
                    report.append("")
        
        # System flow consequences
        report.append("\n" + "=" * 80)
        report.append("SYSTEM FLOW CONSEQUENCES ANALYSIS")
        report.append("=" * 80)
        
        if model_performance:
            fastest_model = min(model_performance, key=lambda x: x[2]['avg_response_time'])
            highest_quality = max(model_performance, key=lambda x: x[2]['avg_quality_score'])
            most_reliable = max(model_performance, key=lambda x: x[2]['success_rate'])
            
            report.append(f"Fastest Model: {fastest_model[0]} ({fastest_model[2]['avg_response_time']:.1f}s)")
            report.append(f"Highest Quality: {highest_quality[0]} ({highest_quality[2]['avg_quality_score']:.1f}/10)")
            report.append(f"Most Reliable: {most_reliable[0]} ({most_reliable[2]['success_rate']:.1f}%)")
            report.append("")
            
            report.append("SYSTEM IMPACT ANALYSIS:")
            report.append("-" * 25)
            
            for model, _, data in model_performance:
                report.append(f"\n{model}:")
                
                # User experience impact
                if data['avg_response_time'] < 10:
                    ux_impact = "Excellent UX - Real-time feel"
                elif data['avg_response_time'] < 20:
                    ux_impact = "Good UX - Acceptable wait"
                elif data['avg_response_time'] < 40:
                    ux_impact = "Poor UX - Noticeable delay"
                else:
                    ux_impact = "Bad UX - Frustrating delays"
                
                # System resource impact
                if data['avg_tokens_per_second'] > 10:
                    resource_impact = "High throughput - Good resource efficiency"
                elif data['avg_tokens_per_second'] > 5:
                    resource_impact = "Medium throughput - Moderate resources"
                else:
                    resource_impact = "Low throughput - High resource usage"
                
                # Architecture implications
                if data['avg_response_time'] > 30:
                    arch_implications = "Requires streaming/chunking for good UX"
                elif data['avg_response_time'] > 15:
                    arch_implications = "Benefits from streaming implementation"
                else:
                    arch_implications = "Can work with direct responses"
                
                report.append(f"  User Experience: {ux_impact}")
                report.append(f"  Resource Impact: {resource_impact}")
                report.append(f"  Architecture: {arch_implications}")
                report.append(f"  Recommended for: {'High-quality responses' if data['avg_quality_score'] > 8 else 'Fast interactions' if data['avg_response_time'] < 15 else 'Basic functionality'}")
        
        # Save report
        report_text = "\n".join(report)
        with open("model_comparison_analysis_report.txt", "w") as f:
            f.write(report_text)
            
        print("\n" + report_text)

if __name__ == "__main__":
    comparator = ModelComparator()
    comparator.run_comprehensive_comparison()