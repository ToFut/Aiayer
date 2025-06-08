#!/usr/bin/env python3
"""
Direct Memory Updater
Directly updates memory files with sensor data, bypassing complex integrations.
"""
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DirectMemoryUpdater:
    """Directly updates memory files with fresh sensor data through conscious memory."""
    
    def __init__(self, memory_system=None):
        self.cache_dir = "cache"
        self.memory_dir = "memory"
        self.memory_state_file = "memory/memory_state.json"
        self.conscious_file = "memory/conscious.json"
        self.memory_system = memory_system  # Reference to the memory system for routing through conscious memory
        
    def update_memory_with_sensor_data(self):
        """Update memory files with latest sensor data through conscious memory."""
        try:
            # Read latest sensor data
            screen_data = self._read_latest_screen_data()
            process_data = self._read_latest_process_data()
            
            if screen_data or process_data:
                if self.memory_system and hasattr(self.memory_system, 'conscious_memory'):
                    # Route data through conscious memory
                    success = self._route_through_conscious_memory(screen_data, process_data)
                    if success:
                        logger.info("✅ Memory updated via conscious memory routing")
                        return True
                    else:
                        logger.warning("⚠️ Failed to route through conscious memory, using fallback")
                        # Fallback to direct update if routing fails
                        self._update_memory_state_fallback(screen_data, process_data)
                        self._update_conscious_memory_fallback(screen_data, process_data)
                        return True
                else:
                    # No memory system reference or no conscious memory, use fallback
                    logger.warning("⚠️ No conscious memory available, using direct memory update")
                    self._update_memory_state_fallback(screen_data, process_data)
                    self._update_conscious_memory_fallback(screen_data, process_data)
                    return True
            else:
                logger.warning("⚠️ No fresh sensor data found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating memory: {e}")
            return False
            
    async def _route_through_conscious_memory(self, screen_data, process_data):
        """Route sensor data through conscious memory for proper distribution."""
        try:
            # Route screen data if available
            if screen_data:
                screen_success = await self.memory_system.conscious_memory.add_sensor_data('screen', screen_data)
                if not screen_success:
                    logger.warning("⚠️ Failed to route screen data through conscious memory")
            
            # Route process data if available
            if process_data:
                process_success = await self.memory_system.conscious_memory.add_sensor_data('process', process_data)
                if not process_success:
                    logger.warning("⚠️ Failed to route process data through conscious memory")
                    
            return True
        except Exception as e:
            logger.error(f"❌ Error routing through conscious memory: {e}")
            return False
    
    def _read_latest_screen_data(self) -> Dict[str, Any]:
        """Read latest screen analysis data."""
        try:
            screen_file = "cache/total_screen_analyzer/latest_total_analysis.json"
            if os.path.exists(screen_file):
                with open(screen_file, 'r') as f:
                    data = json.load(f)
                logger.info(f"📺 Screen data: {data.get('memory_summary', {}).get('application', {}).get('name', 'Unknown')} - {data.get('memory_summary', {}).get('content', {}).get('word_count', 0)} words")
                return data
        except Exception as e:
            logger.error(f"Error reading screen data: {e}")
        return {}
    
    def _read_latest_process_data(self) -> Dict[str, Any]:
        """Read latest process data."""
        try:
            process_file = "cache/process_sensor/process_cache.json"
            if os.path.exists(process_file):
                with open(process_file, 'r') as f:
                    data = json.load(f)
                active_apps = data.get('active_apps', [])
                logger.info(f"🖥️ Process data: {len(active_apps)} active apps")
                return data
        except Exception as e:
            logger.error(f"Error reading process data: {e}")
        return {}
    
    def _update_memory_state_fallback(self, screen_data: Dict[str, Any], process_data: Dict[str, Any]):
        """Update the main memory state file as a fallback when conscious memory is unavailable.
        WARNING: This is a fallback method and should be avoided in favor of routing through conscious memory.
        """
        try:
            # Load existing state
            memory_state = {}
            if os.path.exists(self.memory_state_file):
                with open(self.memory_state_file, 'r') as f:
                    memory_state = json.load(f)
            
            # Update with current timestamp
            current_time = datetime.now().isoformat()
            memory_state["last_update"] = current_time
            memory_state["version"] = "1.0"
            memory_state["update_method"] = "direct_fallback"  # Mark as fallback method
            
            # Initialize structure
            if "context" not in memory_state:
                memory_state["context"] = {}
            if "sensor_data" not in memory_state:
                memory_state["sensor_data"] = {}
            
            # Update context from screen data
            if screen_data:
                summary = screen_data.get('memory_summary', {})
                app_info = summary.get('application', {})
                user_activity = summary.get('user_activity', {})
                
                memory_state["context"]["active_app"] = app_info.get('name', 'Unknown')
                memory_state["context"]["screen_text"] = summary.get('text_sample', '')[:500]  # Limit size
                memory_state["context"]["workflow_stage"] = user_activity.get('workflow_stage', '')
                memory_state["context"]["user_intent"] = user_activity.get('user_intent', '')
                memory_state["context"]["semantic_summary"] = summary.get('semantic_summary', '')
                
                # Store full screen data
                memory_state["sensor_data"]["screen"] = {
                    "timestamp": screen_data.get('timestamp'),
                    "application": app_info.get('name'),
                    "word_count": summary.get('content', {}).get('word_count', 0),
                    "activity": user_activity.get('current_activity'),
                    "confidence": summary.get('analysis_confidence', 0)
                }
            
            # Update context from process data
            if process_data:
                memory_state["context"]["active_apps"] = process_data.get('active_apps', [])[:10]  # Top 10
                memory_state["context"]["system_memory_percent"] = process_data.get('system_info', {}).get('memory_used_percent', 0)
                
                # Store process data
                memory_state["sensor_data"]["process"] = {
                    "timestamp": process_data.get('timestamp'),
                    "active_processes_count": len(process_data.get('active_processes', [])),
                    "top_apps": process_data.get('active_apps', [])[:5],
                    "memory_usage": process_data.get('system_info', {}).get('memory_used_percent', 0)
                }
            
            # Save updated state
            os.makedirs(os.path.dirname(self.memory_state_file), exist_ok=True)
            with open(self.memory_state_file, 'w') as f:
                json.dump(memory_state, f, indent=2)
                
            logger.info("📝 Memory state updated successfully (FALLBACK METHOD)")
            
        except Exception as e:
            logger.error(f"Error updating memory state: {e}")
    
    def _update_conscious_memory_fallback(self, screen_data: Dict[str, Any], process_data: Dict[str, Any]):
        """Update conscious memory with sensor buffers as a fallback method.
        WARNING: This is a legacy fallback method and should be avoided in favor of 
        proper routing through the ConsciousMemory class.
        """
        try:
            current_time = datetime.now().isoformat()
            
            # Create conscious memory structure
            conscious_memory = {
                "timestamp": current_time,
                "update_method": "direct_fallback",  # Mark as fallback method
                "sensor_buffers": {
                    "screen": [],
                    "process": []
                },
                "insights": [],
                "status": "active"
            }
            
            # Add screen buffer entry
            if screen_data:
                summary = screen_data.get('memory_summary', {})
                screen_entry = {
                    "timestamp": screen_data.get('timestamp', current_time),
                    "image_hash": screen_data.get('image_hash', ''),
                    "application": summary.get('application', {}).get('name', 'Unknown'),
                    "word_count": summary.get('content', {}).get('word_count', 0),
                    "semantic_summary": summary.get('semantic_summary', ''),
                    "user_activity": summary.get('user_activity', {}),
                    "confidence": summary.get('analysis_confidence', 0)
                }
                conscious_memory["sensor_buffers"]["screen"] = [screen_entry]
                
                # Add insights
                insights = summary.get('key_insights', [])
                for insight in insights:
                    conscious_memory["insights"].append({
                        "timestamp": current_time,
                        "content": insight,
                        "type": "screen_analysis"
                    })
            
            # Add process buffer entry
            if process_data:
                process_entry = {
                    "timestamp": process_data.get('timestamp', current_time),
                    "active_processes_count": len(process_data.get('active_processes', [])),
                    "active_apps": process_data.get('active_apps', [])[:10],
                    "memory_usage": process_data.get('system_info', {}).get('memory_used_percent', 0),
                    "cpu_count": process_data.get('system_info', {}).get('cpu_count', 0)
                }
                conscious_memory["sensor_buffers"]["process"] = [process_entry]
                
                # Add process insight
                conscious_memory["insights"].append({
                    "timestamp": current_time,
                    "content": f"System running {len(process_data.get('active_processes', []))} applications with {process_data.get('system_info', {}).get('memory_used_percent', 0)}% memory usage",
                    "type": "process_analysis"
                })
            
            # Save conscious memory
            os.makedirs(os.path.dirname(self.conscious_file), exist_ok=True)
            with open(self.conscious_file, 'w') as f:
                json.dump(conscious_memory, f, indent=2)
                
            logger.info("🧠 Conscious memory updated via FALLBACK method")
            logger.warning("⚠️ Direct conscious memory update used instead of proper routing!")
            
        except Exception as e:
            logger.error(f"Error updating conscious memory: {e}")

def main():
    """Main function to run the direct memory updater."""
    # Try to import and get memory system
    memory_system = None
    try:
        # Attempt to import memory system
        import sys
        sys.path.append('.')  # Add current directory to path
        
        try:
            from memory.memory_system import MemorySystem
            # Create memory system instance if possible
            memory_system = MemorySystem()
            logger.info("✅ Successfully imported MemorySystem")
        except ImportError:
            logger.warning("⚠️ Could not import MemorySystem from memory.memory_system")
            
            try:
                from memory_system import MemorySystem
                # Create memory system instance if possible
                memory_system = MemorySystem()
                logger.info("✅ Successfully imported MemorySystem from root module")
            except ImportError:
                logger.warning("⚠️ Could not import MemorySystem - will use fallback methods")
                memory_system = None
    except Exception as e:
        logger.error(f"❌ Error importing memory system: {e}")
        memory_system = None
    
    # Create updater with memory system reference if available
    updater = DirectMemoryUpdater(memory_system=memory_system)
    
    logger.info("🚀 Starting Direct Memory Updater...")
    if memory_system:
        logger.info("✅ Using conscious memory routing for memory updates")
    else:
        logger.warning("⚠️ Using fallback methods for memory updates")
    
    while True:
        try:
            # Update memory with latest sensor data
            success = updater.update_memory_with_sensor_data()
            
            if success:
                logger.info("✅ Memory sync successful")
            else:
                logger.warning("⚠️ Memory sync had issues")
            
            # Wait 10 seconds before next update
            time.sleep(10)
            
        except KeyboardInterrupt:
            logger.info("🛑 Stopping Direct Memory Updater...")
            break
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()