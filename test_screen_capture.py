#!/usr/bin/env python3
"""
Simple test to demonstrate TotalScreenAnalyzer REALLY sees what user sees
without LLaVA delays
"""
import asyncio
import json
from datetime import datetime
from sensors.total_screen_analyzer import TotalScreenAnalyzer

async def test_real_screen_vision():
    print("🔍 Testing TotalScreenAnalyzer - What does it REALLY see?")
    print("=" * 60)
    
    # Create analyzer but disable bridge connection for direct testing
    analyzer = TotalScreenAnalyzer(bridge_uri=None, capture_interval=1, fast_mode=True)
    
    # Perform ONE comprehensive analysis
    try:
        print("📸 Capturing current screen...")
        analysis_result = await analyzer._perform_total_screen_analysis()
        
        print("✅ ANALYSIS COMPLETE!")
        print("=" * 60)
        
        # Show key visual data
        if analysis_result:
            print(f"📊 Screen Resolution: {analysis_result.get('image_resolution', 'Unknown')}")
            print(f"🖥️  Screen Hash: {analysis_result.get('image_hash', 'Unknown')}")
            
            # Show window/app detection
            app_info = analysis_result.get('application', {})
            print(f"🎯 Detected Application: {app_info.get('name', 'Unknown')}")
            print(f"📈 Detection Confidence: {app_info.get('confidence', 0)}%")
            
            # Show text extraction (first 200 chars)
            text_sample = analysis_result.get('text_sample', '')
            if text_sample:
                print(f"📝 Extracted Text Sample: {text_sample[:200]}...")
                print(f"📊 Total Text Length: {len(text_sample)} characters")
            else:
                print("📝 No text extracted")
            
            # Show UI elements detected
            ui_elements = analysis_result.get('ui_elements', [])
            print(f"🎛️  UI Elements Found: {len(ui_elements)}")
            if ui_elements:
                for i, element in enumerate(ui_elements[:3]):  # Show first 3
                    print(f"   {i+1}. {element.get('type', 'Unknown')} at {element.get('position', 'Unknown')}")
            
            # Show semantic summary
            semantic = analysis_result.get('semantic_summary', '')
            if semantic:
                print(f"🧠 Semantic Summary: {semantic}")
            
            # Show activity classification
            activity = analysis_result.get('current_activity', '')
            print(f"🎯 Activity Detected: {activity}")
            
            print("=" * 60)
            print("🎉 SUCCESS: TotalScreenAnalyzer can see and analyze your screen!")
            
            # Save full result to file for inspection
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"total_screen_analysis_{timestamp}.json"
            with open(output_file, 'w') as f:
                json.dump(analysis_result, f, indent=2, default=str)
            print(f"💾 Full analysis saved to: {output_file}")
            
        else:
            print("❌ No analysis result returned")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_screen_vision())