#!/usr/bin/env python3
"""
Fixed Meaningful Memory Feeder
Continuous data collection with enhanced application detection for meaningful content
"""

import json
import time
import psutil
import logging
from datetime import datetime
from pathlib import Path
import os
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FixedMeaningfulMemoryFeeder:
    def __init__(self):
        self.memory_dir = Path("/Users/segevbin/Desktop/SensAI/Aiayer/memory")
        self.memory_dir.mkdir(exist_ok=True)
        
        # Enhanced application detection patterns
        self.app_categories = {
            'development': {
                'patterns': ['cursor', 'code', 'visual studio', 'vscode', 'xcode', 'intellij', 
                           'pycharm', 'atom', 'sublime', 'vim', 'emacs', 'webstorm', 'android studio'],
                'context': 'software_engineering',
                'specifics': ['coding', 'debugging', 'development_workflow', 'programming']
            },
            'design': {
                'patterns': ['figma', 'sketch', 'photoshop', 'illustrator', 'canva', 'framer'],
                'context': 'ui_ux_design',
                'specifics': ['designing', 'prototyping', 'visual_creation', 'design_workflow']
            },
            'communication': {
                'patterns': ['slack', 'discord', 'teams', 'zoom', 'skype', 'telegram', 'whatsapp'],
                'context': 'team_collaboration',
                'specifics': ['messaging', 'video_calling', 'team_coordination', 'communication']
            },
            'browser': {
                'patterns': ['chrome', 'firefox', 'safari', 'edge', 'opera', 'brave'],
                'context': 'web_browsing',
                'specifics': ['research', 'browsing', 'web_activity', 'information_gathering']
            },
            'productivity': {
                'patterns': ['notion', 'obsidian', 'word', 'pages', 'docs', 'sheets', 'excel'],
                'context': 'content_creation',
                'specifics': ['writing', 'documentation', 'note_taking', 'productivity']
            }
        }
        
        logger.info("🚀 Fixed Meaningful Memory Feeder initialized")
    
    def detect_application_activity(self, process_name):
        """Enhanced application detection with meaningful categorization"""
        app_lower = process_name.lower()
        
        for category, details in self.app_categories.items():
            for pattern in details['patterns']:
                if pattern in app_lower:
                    return {
                        'category': category,
                        'professional_context': details['context'],
                        'activity_specifics': details['specifics'],
                        'detected_app': process_name,
                        'confidence': 0.95  # High confidence for exact matches
                    }
        
        # Default for unrecognized apps
        return {
            'category': 'general',
            'professional_context': 'general_computing',
            'activity_specifics': ['unknown_activity'],
            'detected_app': process_name,
            'confidence': 0.3
        }
    
    def get_current_activity(self):
        """Get detailed current activity analysis"""
        try:
            # Get active processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = proc.info
                    cpu_pct = info.get('cpu_percent', 0) or 0
                    mem_pct = info.get('memory_percent', 0) or 0
                    
                    # Include process if it has any activity or is a known important app
                    if cpu_pct > 0 or mem_pct > 0.1 or any(pattern in info['name'].lower() 
                                                          for category in self.app_categories.values() 
                                                          for pattern in category['patterns']):
                        info['cpu_percent'] = cpu_pct
                        info['memory_percent'] = mem_pct
                        processes.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage to find most active
            active_processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]
            
            activities = []
            primary_activity = None
            
            for proc in active_processes:
                activity_data = self.detect_application_activity(proc['name'])
                activity_data['cpu_usage'] = proc['cpu_percent']
                activity_data['memory_usage'] = proc['memory_percent']
                activities.append(activity_data)
                
                # Set primary activity (highest confidence non-general)
                if not primary_activity and activity_data['category'] != 'general':
                    primary_activity = activity_data
            
            # If no specific activity found, use the most active process
            if not primary_activity and activities:
                primary_activity = activities[0]
            
            return {
                'primary_activity': primary_activity,
                'all_activities': activities,
                'process_count': len(active_processes),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting current activity: {e}")
            return None
    
    def create_meaningful_memory_entry(self, activity_data):
        """Create a meaningful memory entry with detailed context"""
        if not activity_data or not activity_data.get('primary_activity'):
            return None
        
        primary = activity_data['primary_activity']
        
        # Calculate productivity and engagement scores
        productivity_score = min(primary.get('confidence', 0) * 0.8 + 
                               (primary.get('cpu_usage', 0) / 100) * 0.2, 1.0)
        
        # Create detailed memory entry
        memory_entry = {
            'timestamp': activity_data['timestamp'],
            'memory_type': 'activity_analysis',
            'user_activity': {
                'primary_activity': primary['category'],
                'application_used': primary['detected_app'],
                'professional_context': primary['professional_context'],
                'activity_specifics': primary['activity_specifics'],
                'productivity_score': round(productivity_score, 3),
                'confidence_level': primary['confidence'],
                'engagement_indicators': {
                    'cpu_usage_percent': primary.get('cpu_usage', 0),
                    'memory_usage_percent': primary.get('memory_usage', 0),
                    'active_process_count': activity_data['process_count']
                }
            },
            'context_analysis': {
                'workflow_stage': self._determine_workflow_stage(primary['category']),
                'user_intent': self._analyze_user_intent(primary),
                'productivity_context': self._get_productivity_context(productivity_score),
                'meaningful_interaction': True if primary['category'] != 'general' else False
            },
            'concurrent_activities': [
                {
                    'app': act['detected_app'],
                    'category': act['category'],
                    'context': act['professional_context']
                } for act in activity_data['all_activities'][:3]  # Top 3
            ],
            'memory_id': f"meaningful_{int(time.time() * 1000)}"
        }
        
        return memory_entry
    
    def _determine_workflow_stage(self, category):
        """Determine what stage of workflow the user is in"""
        workflow_mapping = {
            'development': 'active_coding',
            'design': 'creative_design',
            'communication': 'collaboration',
            'browser': 'information_gathering',
            'productivity': 'content_creation',
            'general': 'general_computing'
        }
        return workflow_mapping.get(category, 'unknown')
    
    def _analyze_user_intent(self, activity_data):
        """Analyze what the user is trying to accomplish"""
        category = activity_data['category']
        app = activity_data['detected_app'].lower()
        
        if category == 'development':
            if 'cursor' in app:
                return 'ai_assisted_development'
            return 'software_development'
        elif category == 'design':
            return 'visual_design_work'
        elif category == 'communication':
            return 'team_communication'
        elif category == 'browser':
            return 'research_or_browsing'
        elif category == 'productivity':
            return 'document_creation'
        else:
            return 'general_computer_use'
    
    def _get_productivity_context(self, score):
        """Get productivity context based on score"""
        if score >= 0.8:
            return 'highly_productive'
        elif score >= 0.6:
            return 'moderately_productive'
        elif score >= 0.4:
            return 'low_productivity'
        else:
            return 'minimal_activity'
    
    def store_memory_entry(self, memory_entry):
        """Store memory entry in multiple locations"""
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
            conscious_data['status'] = 'actively_learning'
            
            # Keep only last 50 insights to prevent bloat
            if len(conscious_data['insights']) > 50:
                conscious_data['insights'] = conscious_data['insights'][-50:]
            
            with open(conscious_file, 'w') as f:
                json.dump(conscious_data, f, indent=2)
            
            # Store in short-term memory
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
            
            logger.info(f"✅ Stored meaningful memory: {memory_entry['user_activity']['primary_activity']} with {memory_entry['user_activity']['application_used']}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing memory entry: {e}")
            return False
    
    def run_continuous_feeding(self, interval=10):
        """Run continuous memory feeding with meaningful content detection"""
        logger.info(f"🔄 Starting continuous meaningful memory feeding (interval: {interval}s)")
        
        try:
            while True:
                # Get current activity
                activity_data = self.get_current_activity()
                
                if activity_data:
                    # Create meaningful memory entry
                    memory_entry = self.create_meaningful_memory_entry(activity_data)
                    
                    if memory_entry:
                        # Store the entry
                        success = self.store_memory_entry(memory_entry)
                        
                        if success:
                            primary = memory_entry['user_activity']
                            logger.info(f"📝 Captured: {primary['primary_activity']} | App: {primary['application_used']} | Context: {primary['professional_context']} | Score: {primary['productivity_score']}")
                        else:
                            logger.warning("Failed to store memory entry")
                    else:
                        logger.warning("No meaningful activity detected")
                else:
                    logger.warning("Could not get activity data")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Memory feeding stopped by user")
        except Exception as e:
            logger.error(f"Error in continuous feeding: {e}")

def main():
    """Main function to run the meaningful memory feeder"""
    feeder = FixedMeaningfulMemoryFeeder()
    
    # Test current activity detection first
    logger.info("🧪 Testing current activity detection...")
    activity = feeder.get_current_activity()
    if activity:
        logger.info(f"Current activity detected: {activity['primary_activity']}")
        memory_entry = feeder.create_meaningful_memory_entry(activity)
        if memory_entry:
            logger.info(f"Memory entry created: {memory_entry['user_activity']['primary_activity']}")
            feeder.store_memory_entry(memory_entry)
        else:
            logger.warning("Could not create meaningful memory entry")
    
    # Start continuous feeding
    feeder.run_continuous_feeding(interval=5)

if __name__ == "__main__":
    main()