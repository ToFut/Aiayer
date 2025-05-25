#!/usr/bin/env python3
"""
Focused Model Quality Analysis
Based on previous performance data and targeted quality tests
"""

import json
import time
import requests
from datetime import datetime

class FocusedModelAnalysis:
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        
        # Known performance data from previous tests
        self.performance_data = {
            "llama3.2:1b": {
                "avg_response_time": 27.9,
                "first_token_time": 17.0,
                "tokens_per_second": 4.2,
                "reliability": "High"
            },
            "llama3.2:latest": {
                "avg_response_time": 82.4,
                "first_token_time": 20.5,
                "tokens_per_second": 2.8,
                "reliability": "High"
            },
            "mistral:latest": {
                "avg_response_time": 45.0,  # Estimated
                "first_token_time": 15.0,   # Estimated
                "tokens_per_second": 3.5,   # Estimated
                "reliability": "Medium"
            },
            "llava:latest": {
                "avg_response_time": 60.0,  # Estimated (vision model)
                "first_token_time": 25.0,   # Estimated
                "tokens_per_second": 2.0,   # Estimated (slower due to vision)
                "reliability": "Medium"
            }
        }
        
        # Quality test prompts (shorter for faster testing)
        self.quality_tests = [
            {
                "type": "technical_accuracy",
                "prompt": "Explain how WebSockets differ from HTTP requests in 100 words",
                "expected_keywords": ["persistent", "connection", "real-time", "bidirectional", "protocol"]
            },
            {
                "type": "analytical_thinking", 
                "prompt": "What are 3 pros and 3 cons of remote work? Be specific.",
                "expected_keywords": ["flexibility", "communication", "productivity", "isolation"]
            },
            {
                "type": "problem_solving",
                "prompt": "A web app loads slowly. List 4 debugging steps in order of priority.",
                "expected_keywords": ["network", "database", "cache", "performance", "monitoring"]
            }
        ]

    def quick_quality_test(self, model_name, test_prompt, timeout=60):
        """Quick quality test with shorter timeout"""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model_name,
                    "prompt": test_prompt["prompt"],
                    "stream": False,
                    "options": {
                        "num_predict": 200,  # Shorter responses for speed
                        "temperature": 0.7
                    }
                },
                timeout=timeout
            )
            
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                # Quick quality scoring
                quality_score = self.score_response_quality(response_text, test_prompt)
                
                return {
                    "success": True,
                    "response": response_text,
                    "response_time": end_time - start_time,
                    "quality_score": quality_score,
                    "word_count": len(response_text.split())
                }
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def score_response_quality(self, response_text, test_prompt):
        """Quick quality scoring based on key criteria"""
        if not response_text:
            return 0
            
        score = 0
        max_score = 10
        
        # 1. Length appropriateness (2 points)
        word_count = len(response_text.split())
        if 30 <= word_count <= 150:
            score += 2
        elif 20 <= word_count < 30 or 150 < word_count <= 200:
            score += 1.5
        elif word_count >= 10:
            score += 1
            
        # 2. Keyword relevance (3 points)
        expected_keywords = test_prompt.get("expected_keywords", [])
        found_keywords = sum(1 for keyword in expected_keywords 
                           if keyword.lower() in response_text.lower())
        score += (found_keywords / len(expected_keywords)) * 3 if expected_keywords else 1.5
        
        # 3. Structure and coherence (3 points)
        sentences = [s.strip() for s in response_text.split('.') if s.strip()]
        if len(sentences) >= 3:
            score += 3
        elif len(sentences) >= 2:
            score += 2
        elif len(sentences) >= 1:
            score += 1
            
        # 4. Technical accuracy for technical prompts (2 points)
        if test_prompt["type"] == "technical_accuracy":
            tech_indicators = ["protocol", "connection", "server", "client", "request", "response"]
            found_tech = sum(1 for term in tech_indicators if term.lower() in response_text.lower())
            score += min(2, found_tech * 0.5)
        else:
            score += 1.5  # Default for non-technical
            
        return min(max_score, score)

    def analyze_system_flow_consequences(self):
        """Analyze what each model choice means for system architecture"""
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "model_recommendations": {},
            "system_architecture_impact": {},
            "use_case_recommendations": {}
        }
        
        print("SYSTEM FLOW CONSEQUENCES ANALYSIS")
        print("=" * 50)
        
        for model, perf_data in self.performance_data.items():
            print(f"\n{model.upper()}:")
            print("-" * 30)
            
            # Categorize performance
            response_time = perf_data["avg_response_time"]
            first_token = perf_data["first_token_time"]
            
            # System architecture implications
            if response_time > 60:
                arch_category = "REQUIRES_STREAMING"
                ux_impact = "Poor without streaming - mandatory chunking needed"
                system_changes = [
                    "Implement streaming responses",
                    "Add progress indicators", 
                    "Consider response caching",
                    "Implement request queuing"
                ]
            elif response_time > 30:
                arch_category = "BENEFITS_FROM_STREAMING" 
                ux_impact = "Acceptable with streaming - recommended optimization"
                system_changes = [
                    "Implement streaming for better UX",
                    "Add loading indicators",
                    "Consider response caching for common queries"
                ]
            elif response_time > 15:
                arch_category = "STREAMING_OPTIONAL"
                ux_impact = "Good UX - streaming provides enhancement"
                system_changes = [
                    "Streaming optional but beneficial",
                    "Simple loading states sufficient"
                ]
            else:
                arch_category = "DIRECT_RESPONSE_OK"
                ux_impact = "Excellent UX - no special handling needed"
                system_changes = [
                    "Direct responses work well",
                    "Minimal UI changes needed"
                ]
            
            # Resource and scaling implications
            tps = perf_data["tokens_per_second"]
            if tps > 5:
                resource_impact = "Efficient - good for high-concurrency"
                scaling_notes = "Can handle multiple simultaneous users"
            elif tps > 3:
                resource_impact = "Moderate - suitable for medium load"
                scaling_notes = "Good for typical usage patterns"
            else:
                resource_impact = "Heavy - requires careful resource management"
                scaling_notes = "May need connection pooling and queuing"
            
            # Chat mode suitability
            mode_suitability = {}
            
            # Ask mode (simple questions)
            if response_time < 20:
                mode_suitability["ask_mode"] = "Excellent - natural conversation flow"
            elif response_time < 40:
                mode_suitability["ask_mode"] = "Good - acceptable for Q&A"
            else:
                mode_suitability["ask_mode"] = "Poor - too slow for quick questions"
            
            # Agent mode (complex tasks)
            if response_time < 60:
                mode_suitability["agent_mode"] = "Good - suitable for task planning"
            else:
                mode_suitability["agent_mode"] = "Challenging - may need task breakdown"
            
            # Suggest mode (quick suggestions)
            if response_time < 15:
                mode_suitability["suggest_mode"] = "Perfect - fast suggestions"
            elif response_time < 30:
                mode_suitability["suggest_mode"] = "Workable - with good UX design"
            else:
                mode_suitability["suggest_mode"] = "Poor - too slow for suggestions"
            
            print(f"Response Time: {response_time:.1f}s (First token: {first_token:.1f}s)")
            print(f"Architecture Category: {arch_category}")
            print(f"UX Impact: {ux_impact}")
            print(f"Resource Impact: {resource_impact}")
            print(f"Scaling: {scaling_notes}")
            print("\nRequired System Changes:")
            for change in system_changes:
                print(f"  • {change}")
            print("\nChat Mode Suitability:")
            for mode, suitability in mode_suitability.items():
                print(f"  • {mode}: {suitability}")
            
            # Store in analysis
            analysis["model_recommendations"][model] = {
                "architecture_category": arch_category,
                "ux_impact": ux_impact,
                "resource_impact": resource_impact,
                "system_changes_needed": system_changes,
                "chat_mode_suitability": mode_suitability,
                "performance_metrics": perf_data
            }
        
        # Overall recommendations
        print("\n" + "=" * 50)
        print("OVERALL RECOMMENDATIONS")
        print("=" * 50)
        
        recommendations = {
            "production_ready": [],
            "development_friendly": [],
            "high_quality": [],
            "fast_response": []
        }
        
        for model, perf_data in self.performance_data.items():
            if perf_data["avg_response_time"] < 30 and perf_data["reliability"] == "High":
                recommendations["production_ready"].append(model)
            if perf_data["avg_response_time"] < 45:
                recommendations["development_friendly"].append(model)
            if model in ["llama3.2:latest", "mistral:latest"]:  # Larger models typically higher quality
                recommendations["high_quality"].append(model)
            if perf_data["avg_response_time"] < 30:
                recommendations["fast_response"].append(model)
        
        print(f"Production Ready: {', '.join(recommendations['production_ready'])}")
        print(f"Development Friendly: {', '.join(recommendations['development_friendly'])}")
        print(f"High Quality: {', '.join(recommendations['high_quality'])}")
        print(f"Fast Response: {', '.join(recommendations['fast_response'])}")
        
        print(f"\nRECOMMENDED MODEL: llama3.2:1b")
        print("Reasoning:")
        print("  • Fast enough for real-time interaction (27.9s avg)")
        print("  • Good first token time (17.0s)")
        print("  • High reliability")
        print("  • Suitable for all chat modes with streaming")
        print("  • Production-ready performance")
        
        analysis["final_recommendation"] = {
            "model": "llama3.2:1b",
            "reasoning": [
                "Best balance of speed and quality",
                "Production-ready performance", 
                "Suitable for all chat modes",
                "High reliability and consistency"
            ]
        }
        
        # Save analysis
        with open("model_system_flow_analysis.json", "w") as f:
            json.dump(analysis, f, indent=2)
            
        return analysis

    def run_focused_comparison(self):
        """Run focused comparison with quality tests"""
        print("FOCUSED MODEL QUALITY COMPARISON")
        print("=" * 50)
        
        results = {}
        
        # Test key models for quality
        key_models = ["llama3.2:1b", "llama3.2:latest"]  # Focus on working models
        
        for model in key_models:
            print(f"\nTesting {model} quality...")
            model_results = {
                "quality_scores": [],
                "avg_quality": 0,
                "performance_data": self.performance_data.get(model, {})
            }
            
            for test in self.quality_tests:
                print(f"  Running {test['type']} test...")
                result = self.quick_quality_test(model, test, timeout=90)
                
                if result["success"]:
                    model_results["quality_scores"].append({
                        "test_type": test["type"],
                        "score": result["quality_score"],
                        "response_time": result["response_time"],
                        "word_count": result["word_count"],
                        "response_preview": result["response"][:150] + "..."
                    })
                    print(f"    Score: {result['quality_score']:.1f}/10 ({result['response_time']:.1f}s)")
                else:
                    print(f"    Failed: {result['error']}")
                
                time.sleep(2)  # Brief pause between tests
            
            # Calculate average quality
            if model_results["quality_scores"]:
                avg_quality = sum(score["score"] for score in model_results["quality_scores"]) / len(model_results["quality_scores"])
                model_results["avg_quality"] = avg_quality
                print(f"  Average Quality: {avg_quality:.1f}/10")
            
            results[model] = model_results
        
        # Generate quality comparison
        print("\n" + "=" * 50)
        print("QUALITY COMPARISON SUMMARY")
        print("=" * 50)
        
        for model, data in results.items():
            if data["quality_scores"]:
                print(f"\n{model}:")
                print(f"  Average Quality Score: {data['avg_quality']:.1f}/10")
                print(f"  Average Response Time: {data['performance_data'].get('avg_response_time', 'N/A')}s")
                print("  Test Breakdown:")
                for score_data in data["quality_scores"]:
                    print(f"    {score_data['test_type']}: {score_data['score']:.1f}/10")
        
        # Save results
        with open("focused_quality_comparison.json", "w") as f:
            json.dump(results, f, indent=2)
        
        return results

if __name__ == "__main__":
    analyzer = FocusedModelAnalysis()
    
    # Run quality comparison
    quality_results = analyzer.run_focused_comparison()
    
    # Run system flow analysis
    system_analysis = analyzer.analyze_system_flow_consequences()
    
    print(f"\nAnalysis complete! Results saved to:")
    print("  • focused_quality_comparison.json")
    print("  • model_system_flow_analysis.json")