#!/usr/bin/env python3
"""
Comprehensive Visual Memory Feeder
Integrates with ALL advanced visual components from START_ENHANCED_SYSTEM:
- Total Screen Analyzer (visual elements, UI components, complex layouts)
- LLaVA Visual Processor (deep visual understanding)
- Enhanced Memory with Deep UI (behavioral analysis)
- Complete UI Understanding System (SaaS interfaces, charts, graphs)
"""

import json
import time
import logging
import asyncio
from datetime import datetime
from pathlib import Path
import os
import sys

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import all advanced visual components
from enhanced_memory_with_deep_ui import EnhancedMemoryWithDeepUI
from complete_ui_understanding_system import CompleteUIUnderstandingSystem
from llava_visual_processor import LLaVAVisualProcessor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ComprehensiveVisualMemoryFeeder:
    """
    Advanced memory feeder that uses ALL visual capabilities from START_ENHANCED_SYSTEM
    """
    
    def __init__(self):
        self.memory_dir = Path("/Users/segevbin/Desktop/SensAI/Aiayer/memory")
        self.cache_dir = Path("/Users/segevbin/Desktop/SensAI/Aiayer/cache")
        
        # Initialize all advanced visual components
        logger.info("🚀 Initializing comprehensive visual analysis components...")
        
        try:
            self.enhanced_memory = EnhancedMemoryWithDeepUI()
            logger.info("✅ Enhanced Memory with Deep UI initialized")
        except Exception as e:
            logger.error(f"❌ Enhanced Memory failed: {e}")
            self.enhanced_memory = None
        
        try:
            self.ui_understanding = CompleteUIUnderstandingSystem()
            logger.info("✅ Complete UI Understanding System initialized")
        except Exception as e:
            logger.error(f"❌ UI Understanding failed: {e}")
            self.ui_understanding = None
        
        try:
            self.llava_processor = LLaVAVisualProcessor()
            logger.info("✅ LLaVA Visual Processor initialized")
        except Exception as e:
            logger.error(f"❌ LLaVA processor failed: {e}")
            self.llava_processor = None
        
        logger.info("🎯 Comprehensive Visual Memory Feeder ready!")
    
    def read_total_screen_analysis(self):
        """Read the latest analysis from Total Screen Analyzer"""
        try:
            analysis_file = self.cache_dir / "total_screen_analyzer" / "latest_total_analysis.json"
            if analysis_file.exists():
                with open(analysis_file, 'r') as f:
                    data = json.load(f)
                return data
            else:
                logger.warning("No Total Screen Analysis data found")
                return None
        except Exception as e:
            logger.error(f"Error reading Total Screen Analysis: {e}")
            return None
    
    async def perform_comprehensive_analysis(self):
        """Perform comprehensive visual analysis using all available components"""
        
        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "comprehensive_visual",
            "components_used": [],
            "visual_understanding": {},
            "ui_elements": {},
            "application_context": {},
            "user_behavior": {},
            "content_analysis": {}
        }
        
        # 1. Get Total Screen Analyzer results (already running)
        logger.info("📺 Reading Total Screen Analyzer results...")
        total_screen_data = self.read_total_screen_analysis()
        if total_screen_data:
            analysis_results["components_used"].append("total_screen_analyzer")
            analysis_results["visual_understanding"]["total_screen"] = {
                "application_detected": total_screen_data.get("memory_summary", {}).get("application", {}),
                "content_type": total_screen_data.get("memory_summary", {}).get("content", {}),
                "user_activity": total_screen_data.get("memory_summary", {}).get("user_activity", {}),
                "text_content": total_screen_data.get("memory_summary", {}).get("text_sample", ""),
                "word_count": total_screen_data.get("memory_summary", {}).get("content", {}).get("word_count", 0),
                "key_insights": total_screen_data.get("memory_summary", {}).get("key_insights", [])
            }
            logger.info(f"   ✅ Total Screen: {total_screen_data.get('memory_summary', {}).get('application', {}).get('name', 'unknown')} detected")
        
        # 2. Enhanced Memory with Deep UI Analysis
        if self.enhanced_memory:
            logger.info("🧠 Performing Enhanced Memory Deep UI analysis...")
            try:
                deep_analysis = await self.enhanced_memory.capture_and_store_deep_memory()
                analysis_results["components_used"].append("enhanced_memory_deep_ui")
                analysis_results["user_behavior"]["deep_ui"] = deep_analysis
                logger.info("   ✅ Deep UI behavioral analysis complete")
            except Exception as e:
                logger.error(f"   ❌ Enhanced Memory analysis failed: {e}")
        
        # 3. Complete UI Understanding System
        if self.ui_understanding:
            logger.info("🎨 Performing Complete UI Understanding analysis...")
            try:
                ui_analysis = await self.ui_understanding.perform_complete_ui_analysis()
                analysis_results["components_used"].append("complete_ui_understanding")
                analysis_results["ui_elements"]["comprehensive"] = ui_analysis
                logger.info("   ✅ UI elements and SaaS interface analysis complete")
            except Exception as e:
                logger.error(f"   ❌ Complete UI analysis failed: {e}")
        
        # 4. LLaVA Visual Processing
        if self.llava_processor:
            logger.info("👁️  Performing LLaVA visual processing...")
            try:
                # Use screenshot from cache or take new one
                import pyautogui
                screenshot = pyautogui.screenshot()
                
                # Convert to base64 for LLaVA
                from io import BytesIO
                import base64
                buffered = BytesIO()
                screenshot.save(buffered, format="PNG")
                img_data = base64.b64encode(buffered.getvalue()).decode()
                
                # Use the correct method name
                llava_analysis = await self.llava_processor.analyze_image(
                    img_data, 
                    "Analyze this screen comprehensively: identify all UI elements, application context, user workflow, visual design patterns, interactive components, and content meaning."
                )
                
                analysis_results["components_used"].append("llava_visual_processor")
                analysis_results["visual_understanding"]["llava"] = llava_analysis
                logger.info("   ✅ LLaVA deep visual understanding complete")
            except Exception as e:
                logger.error(f"   ❌ LLaVA visual processing failed: {e}")
        
        return analysis_results
    
    def create_comprehensive_memory_entry(self, analysis_results):
        """Create a comprehensive memory entry with all visual analysis"""
        
        # Synthesize all analysis results
        memory_entry = {
            "timestamp": analysis_results["timestamp"],
            "memory_type": "comprehensive_visual_analysis",
            "analysis_components": analysis_results["components_used"],
            
            # Application Context (from multiple sources)
            "application_context": {
                "primary_application": "unknown",
                "application_type": "unknown",
                "confidence": 0,
                "detected_by": []
            },
            
            # Visual Understanding
            "visual_understanding": {
                "ui_elements_detected": [],
                "visual_design_patterns": [],
                "layout_structure": {},
                "interactive_components": [],
                "color_scheme": "unknown",
                "visual_hierarchy": []
            },
            
            # Content Analysis
            "content_analysis": {
                "text_content": "",
                "content_type": "unknown",
                "word_count": 0,
                "key_topics": [],
                "semantic_meaning": "",
                "content_complexity": "unknown"
            },
            
            # User Behavior Analysis
            "user_behavior": {
                "current_activity": "unknown",
                "workflow_stage": "unknown",
                "user_intent": "unknown",
                "productivity_level": "unknown",
                "engagement_indicators": {},
                "behavioral_patterns": []
            },
            
            # UI Component Details
            "ui_components": {
                "buttons": [],
                "forms": [],
                "navigation": [],
                "data_displays": [],
                "interactive_elements": [],
                "saas_interface_elements": []
            },
            
            # Professional Context
            "professional_context": {
                "domain": "unknown",
                "work_type": "unknown",
                "tools_in_use": [],
                "professional_level": "unknown",
                "collaboration_indicators": []
            }
        }
        
        # Synthesize data from Total Screen Analyzer
        if "total_screen_analyzer" in analysis_results["components_used"]:
            total_screen = analysis_results["visual_understanding"].get("total_screen", {})
            
            # Application context
            app_info = total_screen.get("application_detected", {})
            if app_info.get("name"):
                memory_entry["application_context"]["primary_application"] = app_info["name"]
                memory_entry["application_context"]["application_type"] = app_info.get("detected_type", "unknown")
                memory_entry["application_context"]["confidence"] = app_info.get("confidence", 0)
                memory_entry["application_context"]["detected_by"].append("total_screen_analyzer")
            
            # Content analysis
            content_info = total_screen.get("content_type", {})
            memory_entry["content_analysis"]["text_content"] = total_screen.get("text_content", "")
            memory_entry["content_analysis"]["word_count"] = total_screen.get("word_count", 0)
            memory_entry["content_analysis"]["content_type"] = content_info.get("type", "unknown")
            
            # User behavior
            user_activity = total_screen.get("user_activity", {})
            memory_entry["user_behavior"]["current_activity"] = user_activity.get("current_activity", "unknown")
            memory_entry["user_behavior"]["workflow_stage"] = user_activity.get("workflow_stage", "unknown")
            memory_entry["user_behavior"]["user_intent"] = user_activity.get("user_intent", "unknown")
            memory_entry["user_behavior"]["productivity_level"] = user_activity.get("productivity_context", "unknown")
        
        # Synthesize data from Complete UI Understanding
        if "complete_ui_understanding" in analysis_results["components_used"]:
            ui_analysis = analysis_results["ui_elements"].get("comprehensive", {})
            # Add UI element details
            if ui_analysis:
                memory_entry["ui_components"]["saas_interface_elements"] = ui_analysis.get("saas_elements", [])
                memory_entry["visual_understanding"]["ui_elements_detected"] = ui_analysis.get("detected_elements", [])
        
        # Synthesize data from LLaVA
        if "llava_visual_processor" in analysis_results["components_used"]:
            llava_data = analysis_results["visual_understanding"].get("llava", {})
            if llava_data:
                memory_entry["visual_understanding"]["visual_design_patterns"] = llava_data.get("visual_patterns", [])
                memory_entry["content_analysis"]["semantic_meaning"] = llava_data.get("content_understanding", "")
        
        # Set memory priority based on analysis richness
        component_count = len(analysis_results["components_used"])
        if component_count >= 3:
            memory_entry["memory_priority"] = "high"
        elif component_count >= 2:
            memory_entry["memory_priority"] = "medium"
        else:
            memory_entry["memory_priority"] = "low"
        
        memory_entry["analysis_quality"] = {
            "components_successful": component_count,
            "total_components": 4,
            "completeness_score": component_count / 4,
            "confidence_level": max([
                memory_entry["application_context"]["confidence"],
                0.5 if memory_entry["content_analysis"]["word_count"] > 0 else 0
            ])
        }
        
        return memory_entry
    
    def store_comprehensive_memory(self, memory_entry):
        """Store comprehensive memory entry in all relevant locations"""
        try:
            # Store in conscious memory
            conscious_file = self.memory_dir / "conscious.json"
            conscious_data = {"timestamp": datetime.now().isoformat(), "insights": []}
            
            if conscious_file.exists():
                with open(conscious_file, 'r') as f:
                    conscious_data = json.load(f)
            
            if 'insights' not in conscious_data:
                conscious_data['insights'] = []
            
            conscious_data['insights'].append(memory_entry)
            conscious_data['timestamp'] = datetime.now().isoformat()
            conscious_data['status'] = 'comprehensive_visual_learning'
            
            # Keep only last 50 insights
            if len(conscious_data['insights']) > 50:
                conscious_data['insights'] = conscious_data['insights'][-50:]
            
            with open(conscious_file, 'w') as f:
                json.dump(conscious_data, f, indent=2)
            
            # Store in memory state
            memory_state_file = self.memory_dir / "memory_state.json"
            if memory_state_file.exists():
                with open(memory_state_file, 'r') as f:
                    memory_state = json.load(f)
            else:
                memory_state = {"version": "1.0", "short_term": [], "long_term": [], "context": {}}
            
            if 'short_term' not in memory_state:
                memory_state['short_term'] = []
            
            memory_state['short_term'].append(memory_entry)
            memory_state['last_update'] = datetime.now().isoformat()
            
            # Keep only last 100 short-term memories
            if len(memory_state['short_term']) > 100:
                memory_state['short_term'] = memory_state['short_term'][-100:]
            
            with open(memory_state_file, 'w') as f:
                json.dump(memory_state, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing comprehensive memory: {e}")
            return False
    
    async def run_comprehensive_feeding(self, interval=15):
        """Run comprehensive visual memory feeding"""
        logger.info(f"🔄 Starting comprehensive visual memory feeding (interval: {interval}s)")
        logger.info("📊 Using ALL advanced visual components from START_ENHANCED_SYSTEM")
        
        try:
            while True:
                logger.info("🔍 Performing comprehensive visual analysis...")
                
                # Perform comprehensive analysis
                analysis_results = await self.perform_comprehensive_analysis()
                
                # Create memory entry
                memory_entry = self.create_comprehensive_memory_entry(analysis_results)
                
                # Store in memory
                success = self.store_comprehensive_memory(memory_entry)
                
                if success:
                    # Log summary
                    app = memory_entry["application_context"]["primary_application"]
                    activity = memory_entry["user_behavior"]["current_activity"]
                    components = len(memory_entry["analysis_components"])
                    quality = memory_entry["analysis_quality"]["completeness_score"]
                    
                    logger.info(f"✅ Comprehensive Memory Stored:")
                    logger.info(f"   📱 App: {app}")
                    logger.info(f"   🎯 Activity: {activity}")
                    logger.info(f"   🧩 Components: {components}/4")
                    logger.info(f"   📊 Quality: {quality:.2f}")
                    logger.info(f"   💾 Priority: {memory_entry['memory_priority']}")
                else:
                    logger.error("❌ Failed to store comprehensive memory")
                
                # Wait for next analysis
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Comprehensive visual memory feeding stopped by user")
        except Exception as e:
            logger.error(f"Error in comprehensive feeding: {e}")

async def main():
    """Main function to run comprehensive visual memory feeding"""
    feeder = ComprehensiveVisualMemoryFeeder()
    
    # Test single comprehensive analysis first
    logger.info("🧪 Testing comprehensive visual analysis...")
    analysis = await feeder.perform_comprehensive_analysis()
    memory_entry = feeder.create_comprehensive_memory_entry(analysis)
    
    logger.info(f"🎯 Test Results:")
    logger.info(f"   Components used: {len(analysis['components_used'])}/4")
    logger.info(f"   Quality score: {memory_entry['analysis_quality']['completeness_score']:.2f}")
    logger.info(f"   App detected: {memory_entry['application_context']['primary_application']}")
    
    # Store test result
    feeder.store_comprehensive_memory(memory_entry)
    
    # Start continuous feeding
    await feeder.run_comprehensive_feeding(interval=10)

if __name__ == "__main__":
    asyncio.run(main())