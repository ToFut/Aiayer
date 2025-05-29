#!/usr/bin/env python3
"""
Smart Memory Feeder - Intelligent Memory Pipeline
Feeds memory smartly and intelligently with deduplication, prioritization, and context awareness.
"""

import asyncio
import json
import logging
import os
import sys
import time
import websockets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
import hashlib
import psutil
import subprocess

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/smart_feeder.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('smart_memory_feeder')

class SmartMemoryFeeder:
    """Intelligent memory feeding system with deduplication and prioritization"""
    
    def __init__(self, backend_uri="ws://localhost:8767"):
        self.backend_uri = backend_uri
        self.memory_file = "memory/memory_state.json"
        self.last_state_hash = None
        self.seen_states = set()
        self.running = True
        
        # Intelligence thresholds
        self.min_change_threshold = 0.1  # Minimum change to trigger update
        self.max_update_frequency = 10   # Max updates per minute
        self.update_count = 0
        self.last_reset_time = time.time()
        
    def get_current_system_state(self) -> Dict[str, Any]:
        """Get current system state intelligently"""
        try:
            # Get running applications
            apps = self._get_significant_apps()
            
            # Get system resources
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            
            # Get active window (macOS)
            try:
                result = subprocess.run([
                    'osascript', '-e', 
                    'tell application "System Events" to get name of first application process whose frontmost is true'
                ], capture_output=True, text=True, timeout=2)
                active_app = result.stdout.strip() if result.returncode == 0 else "Unknown"
            except:
                active_app = "Unknown"
            
            return {
                "timestamp": datetime.now().isoformat(),
                "active_app": active_app,
                "running_apps": apps,
                "system_metrics": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_info.percent,
                    "available_memory_gb": memory_info.available / (1024**3)
                },
                "app_count": len(apps),
                "productivity_context": self._assess_productivity_context(apps, cpu_percent)
            }
            
        except Exception as e:
            logger.error(f"Error getting system state: {e}")
            return {}
    
    def _get_significant_apps(self) -> List[str]:
        """Get only significant running applications"""
        try:
            # Get all processes
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            significant_apps = set()
            
            # Look for applications in /Applications/
            for line in lines:
                if '/Applications/' in line and '.app' in line:
                    # Extract app name
                    parts = line.split('/Applications/')
                    if len(parts) > 1:
                        app_part = parts[1].split('.app')[0]
                        if app_part and not app_part.startswith('.'):
                            significant_apps.add(app_part)
            
            # Filter out system apps and focus on user apps
            user_apps = []
            important_keywords = ['cursor', 'chrome', 'firefox', 'safari', 'code', 'slack', 'discord', 
                                'spotify', 'zoom', 'teams', 'notion', 'obsidian', 'figma', 'photoshop']
            
            for app in significant_apps:
                app_lower = app.lower()
                # Include if it matches important keywords or is not a system app
                if any(keyword in app_lower for keyword in important_keywords) or \
                   (not app_lower.startswith('system') and not app_lower.startswith('core') and 
                    len(app) > 3):
                    user_apps.append(app)
            
            return sorted(list(set(user_apps)))
            
        except Exception as e:
            logger.error(f"Error getting apps: {e}")
            return []
    
    def _assess_productivity_context(self, apps: List[str], cpu_percent: float) -> Dict[str, Any]:
        """Assess productivity context from apps and system state"""
        context = {
            "category": "unknown",
            "confidence": 0.5,
            "activity_level": "low",
            "workflow_stage": "unknown"
        }
        
        try:
            app_categories = {
                "development": ["cursor", "code", "xcode", "terminal", "iterm", "git", "docker"],
                "design": ["figma", "sketch", "photoshop", "illustrator", "canva"],
                "communication": ["slack", "discord", "teams", "zoom", "skype", "whatsapp"],
                "productivity": ["notion", "obsidian", "evernote", "todoist", "calendar"],
                "browsing": ["chrome", "firefox", "safari", "edge"],
                "media": ["spotify", "music", "vlc", "youtube", "netflix"]
            }
            
            detected_categories = []
            for category, keywords in app_categories.items():
                if any(any(keyword in app.lower() for keyword in keywords) for app in apps):
                    detected_categories.append(category)
            
            if detected_categories:
                context["category"] = detected_categories[0]  # Primary category
                context["confidence"] = min(0.9, 0.6 + len(detected_categories) * 0.1)
            
            # Assess activity level
            if cpu_percent > 50:
                context["activity_level"] = "high"
            elif cpu_percent > 20:
                context["activity_level"] = "medium"
            else:
                context["activity_level"] = "low"
            
            # Determine workflow stage
            if "development" in detected_categories:
                if cpu_percent > 30:
                    context["workflow_stage"] = "active_coding"
                else:
                    context["workflow_stage"] = "code_review"
            elif "communication" in detected_categories:
                context["workflow_stage"] = "collaboration"
            elif "browsing" in detected_categories:
                context["workflow_stage"] = "research"
            else:
                context["workflow_stage"] = "general_computing"
                
        except Exception as e:
            logger.error(f"Error assessing context: {e}")
        
        return context
    
    def _should_update_memory(self, new_state: Dict[str, Any]) -> bool:
        """Intelligent decision on whether to update memory"""
        try:
            # Rate limiting
            if self.update_count >= self.max_update_frequency:
                time_since_reset = time.time() - self.last_reset_time
                if time_since_reset < 60:  # Within 1 minute
                    return False
                else:
                    # Reset counter
                    self.update_count = 0
                    self.last_reset_time = time.time()
            
            # Generate state hash
            state_str = json.dumps(new_state, sort_keys=True)
            state_hash = hashlib.md5(state_str.encode()).hexdigest()
            
            # Check if state is meaningfully different
            if state_hash == self.last_state_hash:
                return False
            
            # Check if we've seen this exact state recently
            if state_hash in self.seen_states:
                return False
            
            # Significant change detection
            if self.last_state_hash:
                # Load previous state for comparison
                try:
                    with open(self.memory_file, 'r') as f:
                        memory_data = json.load(f)
                    
                    if memory_data.get('short_term'):
                        last_state = memory_data['short_term'][0].get('user_activity', {})
                        
                        # Compare app changes
                        old_apps = set(last_state.get('current_applications', []))
                        new_apps = set(new_state.get('running_apps', []))
                        
                        app_change_ratio = len(old_apps.symmetric_difference(new_apps)) / max(len(old_apps.union(new_apps)), 1)
                        
                        # Only update if significant change
                        if app_change_ratio < self.min_change_threshold:
                            # Check if active app changed
                            old_active = last_state.get('application_used', '')
                            new_active = new_state.get('active_app', '')
                            
                            if old_active == new_active:
                                return False
                
                except Exception as e:
                    logger.warning(f"Error comparing states: {e}")
            
            # Add to seen states (keep last 50)
            self.seen_states.add(state_hash)
            if len(self.seen_states) > 50:
                self.seen_states.pop()
            
            self.last_state_hash = state_hash
            return True
            
        except Exception as e:
            logger.error(f"Error in should_update_memory: {e}")
            return True  # Default to updating on error
    
    def _create_memory_entry(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Create intelligent memory entry"""
        productivity = system_state.get('productivity_context', {})
        
        return {
            "timestamp": system_state["timestamp"],
            "memory_type": "intelligent_system_state",
            "user_activity": {
                "primary_activity": productivity.get('category', 'general'),
                "application_used": system_state.get('active_app', 'Unknown'),
                "professional_context": f"{productivity.get('category', 'general')}_computing",
                "activity_specifics": [
                    productivity.get('workflow_stage', 'general_computing'),
                    f"{productivity.get('activity_level', 'low')}_activity"
                ],
                "productivity_score": productivity.get('confidence', 0.5),
                "confidence_level": productivity.get('confidence', 0.5),
                "current_applications": system_state.get('running_apps', []),
                "system_metrics": system_state.get('system_metrics', {})
            },
            "context_analysis": {
                "workflow_stage": productivity.get('workflow_stage', 'general_computing'),
                "user_intent": f"{productivity.get('category', 'general')}_work",
                "productivity_context": f"{productivity.get('activity_level', 'low')}_productivity",
                "meaningful_interaction": productivity.get('confidence', 0.5) > 0.7
            },
            "concurrent_activities": [
                {
                    "app": app,
                    "category": productivity.get('category', 'general'),
                    "context": f"{productivity.get('category', 'general')}_computing"
                } for app in system_state.get('running_apps', [])[:5]
            ],
            "memory_id": f"smart_state_{int(time.time())}",
            "insights": [
                f"User actively using {len(system_state.get('running_apps', []))} applications",
                f"Primary focus on {productivity.get('category', 'general')} work",
                f"Activity level: {productivity.get('activity_level', 'low')}"
            ],
            "productivity_category": f"{productivity.get('activity_level', 'low')}_productivity",
            "intelligence_score": productivity.get('confidence', 0.5)
        }
    
    async def update_memory(self, system_state: Dict[str, Any]) -> bool:
        """Update memory with new system state"""
        try:
            memory_entry = self._create_memory_entry(system_state)
            
            # Load existing memory
            memory_data = {"short_term": [], "long_term": [], "version": "1.0"}
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    memory_data = json.load(f)
            
            # Add new entry at the beginning
            memory_data['short_term'].insert(0, memory_entry)
            memory_data['last_update'] = datetime.now().isoformat()
            
            # Keep only last 20 short term memories for efficiency
            memory_data['short_term'] = memory_data['short_term'][:20]
            
            # Write back to file
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            with open(self.memory_file, 'w') as f:
                json.dump(memory_data, f, indent=2)
            
            self.update_count += 1
            logger.info(f"Memory updated with smart entry (confidence: {memory_entry['user_activity']['confidence_level']:.2f})")
            return True
            
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            return False
    
    async def run_intelligent_feeding(self):
        """Run intelligent memory feeding loop"""
        logger.info("🧠 Starting Smart Memory Feeder")
        
        while self.running:
            try:
                # Get current system state
                system_state = self.get_current_system_state()
                
                if system_state and self._should_update_memory(system_state):
                    success = await self.update_memory(system_state)
                    if success:
                        logger.info(f"📝 Smart memory update: {system_state.get('active_app', 'Unknown')} + {len(system_state.get('running_apps', []))} apps")
                    else:
                        logger.warning("Failed to update memory")
                
                # Wait before next check (adaptive interval)
                productivity = system_state.get('productivity_context', {})
                if productivity.get('activity_level') == 'high':
                    await asyncio.sleep(5)  # More frequent updates during high activity
                elif productivity.get('activity_level') == 'medium':
                    await asyncio.sleep(10)
                else:
                    await asyncio.sleep(15)  # Less frequent during low activity
                
            except Exception as e:
                logger.error(f"Error in intelligent feeding loop: {e}")
                await asyncio.sleep(10)
    
    def stop(self):
        """Stop the memory feeder"""
        self.running = False
        logger.info("Smart Memory Feeder stopped")

async def main():
    """Main function to run smart memory feeder"""
    feeder = SmartMemoryFeeder()
    
    try:
        await feeder.run_intelligent_feeding()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        feeder.stop()

if __name__ == "__main__":
    asyncio.run(main())