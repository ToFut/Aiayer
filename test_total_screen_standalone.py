#!/usr/bin/env python3
"""
Test TotalScreenAnalyzer standalone to verify it captures meaningful data
"""
import asyncio
import json
import sys
import os
sys.path.append('sensors')

from sensors.total_screen_analyzer import TotalScreenAnalyzer

async def test_standalone_analysis():
    """Test TotalScreenAnalyzer analysis capabilities standalone"""
    print("Testing TotalScreenAnalyzer standalone analysis...")
    
    # Create analyzer in fast mode (skip LLaVA for quick test)
    analyzer = TotalScreenAnalyzer(bridge_uri="ws://localhost:8766", fast_mode=True, capture_interval=1)
    
    print("Running analysis...")
    analysis = await analyzer._perform_total_screen_analysis()
    
    if analysis:
        print(f"\n=== ANALYSIS RESULTS ===")
        print(f"Timestamp: {analysis['timestamp']}")
        print(f"Image Hash: {analysis['image_hash'][:8]}...")
        print(f"Resolution: {analysis['resolution']}")
        print(f"Analysis Duration: {analysis['analysis_duration']:.2f}s")
        
        # Check memory summary
        memory_summary = analysis.get('memory_summary', {})
        print(f"\n=== MEMORY SUMMARY ===")
        print(f"Overall Context: {memory_summary.get('overall_context', 'N/A')}")
        print(f"Semantic Summary: {memory_summary.get('semantic_summary', 'N/A')}")
        print(f"Activity Classification: {memory_summary.get('activity_classification', 'N/A')}")
        
        # Application detection
        app_info = memory_summary.get('application', {})
        print(f"\n=== APPLICATION DETECTION ===")
        print(f"Application Name: {app_info.get('name', 'N/A')}")
        print(f"Detected Type: {app_info.get('detected_type', 'N/A')}")
        print(f"Confidence: {app_info.get('confidence', 0):.2f}")
        
        # Content analysis
        content_info = memory_summary.get('content', {})
        print(f"\n=== CONTENT ANALYSIS ===")
        print(f"Content Type: {content_info.get('type', 'N/A')}")
        print(f"Word Count: {content_info.get('word_count', 0)}")
        print(f"Has Meaningful Text: {content_info.get('has_meaningful_text', False)}")
        print(f"Primary Purpose: {content_info.get('primary_purpose', 'N/A')}")
        
        # User activity
        activity_info = memory_summary.get('user_activity', {})
        print(f"\n=== USER ACTIVITY ===")
        print(f"Current Activity: {activity_info.get('current_activity', 'N/A')}")
        print(f"Workflow Stage: {activity_info.get('workflow_stage', 'N/A')}")
        print(f"User Intent: {activity_info.get('user_intent', 'N/A')}")
        print(f"Productivity Context: {activity_info.get('productivity_context', 'N/A')}")
        
        # Text sample
        text_sample = memory_summary.get('text_sample', '')
        if text_sample:
            print(f"\n=== TEXT SAMPLE (first 200 chars) ===")
            print(f"'{text_sample[:200]}{'...' if len(text_sample) > 200 else ''}'")
        
        # Key insights
        insights = memory_summary.get('key_insights', [])
        if insights:
            print(f"\n=== KEY INSIGHTS ===")
            for insight in insights:
                print(f"- {insight}")
        
        # Layer results summary
        print(f"\n=== ANALYSIS LAYERS ===")
        for layer_name, layer_data in analysis.get('layers', {}).items():
            if isinstance(layer_data, dict) and 'error' not in layer_data:
                print(f"✅ {layer_name}: Success")
            elif isinstance(layer_data, dict) and 'error' in layer_data:
                print(f"❌ {layer_name}: {layer_data['error']}")
            else:
                print(f"⚠️  {layer_name}: Unexpected result")
        
        print(f"\n=== MEMORY OPTIMIZED DATA ===")
        # Save to file for inspection
        output_file = "total_screen_analysis_test.json"
        with open(output_file, 'w') as f:
            json.dump(memory_summary, f, indent=2)
        print(f"Memory summary saved to: {output_file}")
        
        # Return quality assessment
        quality_score = 0
        if app_info.get('name') != 'Unknown':
            quality_score += 2
        if content_info.get('word_count', 0) > 0:
            quality_score += 2
        if content_info.get('has_meaningful_text'):
            quality_score += 2
        if activity_info.get('current_activity') != 'unknown':
            quality_score += 2
        if insights:
            quality_score += 2
        
        print(f"\n=== QUALITY ASSESSMENT ===")
        print(f"Quality Score: {quality_score}/10")
        if quality_score >= 8:
            print("🟢 HIGH QUALITY: Excellent visual understanding")
        elif quality_score >= 6:
            print("🟡 MEDIUM QUALITY: Good visual understanding with some gaps")
        elif quality_score >= 4:
            print("🟠 LOW QUALITY: Basic visual understanding")
        else:
            print("🔴 POOR QUALITY: Minimal visual understanding")
        
        return quality_score >= 6
    else:
        print("❌ No analysis results returned")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_standalone_analysis())
        if result:
            print("\n✅ TotalScreenAnalyzer is working correctly!")
        else:
            print("\n❌ TotalScreenAnalyzer needs improvement")
    except Exception as e:
        print(f"❌ Error testing TotalScreenAnalyzer: {e}")
        import traceback
        traceback.print_exc()