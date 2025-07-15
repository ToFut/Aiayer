#!/usr/bin/env python3
"""
Deep analysis of the automation system to identify real issues.
"""

import asyncio
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any
import re

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.enhanced_backend_server import EnhancedBackendServer
from backend.llm.llm_service import LLMService
from backend.automation_plan import AutomationPlan

class DeepAnalyzer:
    def __init__(self):
        self.backend = EnhancedBackendServer()
        self.llm_service = LLMService()
        
    async def setup(self):
        """Initialize components"""
        print("🔧 Setting up analysis environment...")
        await self.backend.initialize()
        await self.llm_service.initialize()
        print("✅ Analysis environment ready")
        
    async def cleanup(self):
        """Clean up resources"""
        print("🧹 Cleaning up...")
        await self.backend.stop()
        await self.llm_service.cleanup()
        print("✅ Cleanup completed")
        
    def analyze_llm_response(self, prompt: str, llm_response: str) -> Dict[str, Any]:
        """Deep analysis of LLM response quality"""
        analysis = {
            "prompt": prompt,
            "response_length": len(llm_response),
            "issues": [],
            "quality_score": 0,
            "specificity_score": 0,
            "completeness_score": 0
        }
        
        # Check for generic app names
        generic_apps = ["app1", "app2", "app_name", "app"]
        found_generic = []
        for app in generic_apps:
            if app in llm_response.lower():
                found_generic.append(app)
        
        if found_generic:
            analysis["issues"].append(f"Uses generic app names: {found_generic}")
            analysis["specificity_score"] -= 30
        
        # Check for template responses
        template_phrases = [
            "what this step does",
            "description",
            "wait for 2 seconds",
            "take a screenshot"
        ]
        template_count = 0
        for phrase in template_phrases:
            if phrase in llm_response.lower():
                template_count += 1
        
        if template_count > 2:
            analysis["issues"].append(f"Uses {template_count} template phrases")
            analysis["specificity_score"] -= 20
        
        # Check JSON structure
        try:
            # Extract JSON
            text = llm_response.strip()
            match = re.search(r'\{[\s\S]*?\}', text)
            if match:
                json_text = match.group(0)
                plan = json.loads(json_text)
                
                # Check steps
                steps = plan.get("steps", [])
                analysis["step_count"] = len(steps)
                
                if len(steps) == 0:
                    analysis["issues"].append("No steps generated")
                    analysis["completeness_score"] -= 50
                elif len(steps) == 1 and "open_app" in str(steps).lower():
                    analysis["issues"].append("Only generated 1 generic step")
                    analysis["completeness_score"] -= 30
                
                # Check app specificity
                apps = plan.get("apps", [])
                specific_apps = [app for app in apps if app.lower() not in generic_apps]
                analysis["specific_apps"] = specific_apps
                analysis["generic_apps"] = [app for app in apps if app.lower() in generic_apps]
                
                if not specific_apps:
                    analysis["issues"].append("No specific app names found")
                    analysis["specificity_score"] -= 40
                
            else:
                analysis["issues"].append("No valid JSON found")
                analysis["completeness_score"] -= 100
                
        except Exception as e:
            analysis["issues"].append(f"JSON parsing error: {str(e)}")
            analysis["completeness_score"] -= 100
        
        # Calculate quality score
        analysis["quality_score"] = max(0, 100 + analysis["specificity_score"] + analysis["completeness_score"])
        
        return analysis
    
    async def test_specific_prompt(self, prompt: str, expected_apps: List[str]) -> Dict[str, Any]:
        """Test a specific prompt and analyze the results"""
        print(f"\n🔍 Testing: {prompt}")
        print(f"📋 Expected apps: {expected_apps}")
        
        # Generate LLM response
        plan_prompt = f"""Create an automation plan for this user request: "{prompt}"

Return ONLY a single COMPLETE JSON object with this exact structure:
{{
  "apps": ["specific_app_names"],
  "steps": [
    {{
      "action": "specific_action",
      "app": "specific_app_name",
      "description": "specific_description"
    }}
  ]
}}

CRITICAL: Use specific app names like "Calculator", "Safari", "Finder" NOT generic names like "app1", "app2".
IMPORTANT: Return ONLY the JSON object, no other text, no explanations."""

        llm_start = time.time()
        llm_chunks = []
        try:
            async for chunk in self.llm_service.generate_response_with_fallback(plan_prompt):
                llm_chunks.append(chunk)
            llm_response = ''.join(llm_chunks)
            llm_time = time.time() - llm_start
        except Exception as e:
            llm_response = f'{{"apps": ["app1"], "steps": [{{"action": "open_app", "app": "app1", "description": "Error: {str(e)}"}}]}}'
            llm_time = time.time() - llm_start
        
        print(f"⏱️  LLM response time: {llm_time:.2f}s")
        print(f"📄 Response length: {len(llm_response)} chars")
        print(f"📄 Response preview: {llm_response[:200]}...")
        
        # Analyze the response
        analysis = self.analyze_llm_response(prompt, llm_response)
        
        print(f"\n📊 ANALYSIS RESULTS:")
        print(f"  Quality Score: {analysis['quality_score']}/100")
        print(f"  Specificity Score: {analysis['specificity_score']}")
        print(f"  Completeness Score: {analysis['completeness_score']}")
        print(f"  Step Count: {analysis.get('step_count', 0)}")
        print(f"  Specific Apps: {analysis.get('specific_apps', [])}")
        print(f"  Generic Apps: {analysis.get('generic_apps', [])}")
        
        if analysis["issues"]:
            print(f"  🚨 Issues Found:")
            for issue in analysis["issues"]:
                print(f"    - {issue}")
        else:
            print(f"  ✅ No major issues found")
        
        return {
            "prompt": prompt,
            "expected_apps": expected_apps,
            "llm_response": llm_response,
            "llm_time": llm_time,
            "analysis": analysis
        }
    
    async def run_deep_analysis(self):
        """Run deep analysis on key test cases"""
        print("🚀 Starting deep analysis...")
        print("=" * 60)
        
        await self.setup()
        
        # Test cases that should reveal issues
        test_cases = [
            {
                "prompt": "open calculator",
                "expected_apps": ["Calculator"],
                "description": "Simple app launch - should be easy"
            },
            {
                "prompt": "open safari and go to google.com",
                "expected_apps": ["Safari"],
                "description": "App with action - should be specific"
            },
            {
                "prompt": "open calculator, then open safari and go to google.com, then take a screenshot",
                "expected_apps": ["Calculator", "Safari"],
                "description": "Complex workflow - should have multiple steps"
            }
        ]
        
        results = []
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*20} Analysis {i}/{len(test_cases)} {'='*20}")
            result = await self.test_specific_prompt(
                test_case["prompt"], 
                test_case["expected_apps"]
            )
            results.append(result)
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        await self.cleanup()
        
        # Generate analysis report
        self.generate_analysis_report(results)
        
    def generate_analysis_report(self, results: List[Dict[str, Any]]):
        """Generate a detailed analysis report"""
        print("\n" + "="*60)
        print("📊 DEEP ANALYSIS REPORT")
        print("="*60)
        
        total_quality_score = sum(r["analysis"]["quality_score"] for r in results)
        avg_quality_score = total_quality_score / len(results) if results else 0
        
        print(f"\n📈 OVERALL QUALITY:")
        print(f"  Average Quality Score: {avg_quality_score:.1f}/100")
        
        if avg_quality_score < 50:
            print("  🚨 CRITICAL: System quality is very poor")
        elif avg_quality_score < 70:
            print("  ⚠️  WARNING: System quality needs improvement")
        elif avg_quality_score < 85:
            print("  📈 GOOD: System quality is acceptable")
        else:
            print("  🎉 EXCELLENT: System quality is very good")
        
        print(f"\n📋 DETAILED RESULTS:")
        for i, result in enumerate(results, 1):
            analysis = result["analysis"]
            print(f"\n  Test {i}: {result['prompt']}")
            print(f"    Quality: {analysis['quality_score']}/100")
            print(f"    Steps: {analysis.get('step_count', 0)}")
            print(f"    Specific Apps: {analysis.get('specific_apps', [])}")
            print(f"    Issues: {len(analysis['issues'])}")
            
            if analysis["issues"]:
                for issue in analysis["issues"]:
                    print(f"      - {issue}")
        
        # Identify most common issues
        all_issues = []
        for result in results:
            all_issues.extend(result["analysis"]["issues"])
        
        if all_issues:
            print(f"\n🚨 MOST COMMON ISSUES:")
            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"  {count}x: {issue}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        if avg_quality_score < 70:
            print("  1. Improve LLM prompt engineering")
            print("  2. Add better JSON extraction logic")
            print("  3. Implement app name normalization")
            print("  4. Add validation for step completeness")
            print("  5. Consider using a different LLM model")
        else:
            print("  1. Minor prompt improvements")
            print("  2. Fine-tune app name recognition")
            print("  3. Add more specific action types")

async def main():
    analyzer = DeepAnalyzer()
    await analyzer.run_deep_analysis()

if __name__ == "__main__":
    asyncio.run(main()) 