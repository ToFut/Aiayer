#!/usr/bin/env python3
"""
Simple Continuous Memory Feeder
Directly feeds real meaningful data to memory system
"""

import asyncio
import sys
import os
import json
import time
import subprocess
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.memory_system import MemorySystem

class SimpleMemoryFeeder:
    """Simple system to feed real data to memory"""
    
    def __init__(self):
        self.memory_system = None
        self.running = False
        self.collection_count = 0
        
    async def initialize(self):
        """Initialize memory system"""
        print("🧠 Initializing memory system...")
        self.memory_system = MemorySystem()
        print("✅ Memory system ready")
        return True
    
    async def start_feeding(self, duration=60):
        """Start feeding real data for specified duration"""
        if not await self.initialize():
            return
            
        print(f"🚀 STARTING CONTINUOUS MEMORY FEEDING")
        print(f"Duration: {duration} seconds")
        print(f"📊 Feeding real meaningful data every 10 seconds")
        print()
        
        self.running = True
        end_time = time.time() + duration
        
        while self.running and time.time() < end_time:
            try:
                # Collect real system data
                real_data = await self._collect_real_system_data()
                
                # Create meaningful memory entry
                memory_entry = await self._create_meaningful_entry(real_data)
                
                # Store in memory
                memory_id = await self.memory_system.add_to_short_term_memory(memory_entry)
                
                self.collection_count += 1
                remaining = int(end_time - time.time())
                
                print(f"✅ Memory entry #{self.collection_count} stored (ID: {memory_id[:12]}...) | {remaining}s remaining")
                print(f"   Activity: {real_data['detected_activity']}")
                print(f"   App: {real_data['active_application']}")
                print(f"   Context: {memory_entry['user_activity']['professional_context']}")
                print()
                
                # Wait before next collection
                await asyncio.sleep(10)
                
            except Exception as e:
                print(f"⚠️ Collection error: {e}")
                await asyncio.sleep(5)
        
        # Final save
        await self._save_memory_state()
        
        print(f"🎯 FEEDING COMPLETE")
        print(f"   Total entries: {self.collection_count}")
        print(f"   Memory stored in: memory/memory/memory_state.json")
        
        return self.collection_count
    
    async def _collect_real_system_data(self):
        """Collect real system data"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'active_application': 'Unknown',
            'detected_activity': 'general',
            'system_processes': [],
            'meaningful_content': False
        }
        
        try:
            # Get active application (macOS)
            result = subprocess.run([
                'osascript', '-e', 
                'tell application "System Events" to get name of first application process whose frontmost is true'
            ], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                data['active_application'] = result.stdout.strip()
                
                # Detect activity type based on application
                app_lower = data['active_application'].lower()
                if any(term in app_lower for term in ['cursor', 'code', 'visual studio', 'vscode', 'xcode', 'intellij', 'pycharm', 'atom', 'sublime', 'vim', 'emacs']):
                    data['detected_activity'] = 'development'
                elif any(term in app_lower for term in ['chrome', 'safari', 'firefox', 'browser', 'edge']):
                    data['detected_activity'] = 'research'
                elif any(term in app_lower for term in ['slack', 'teams', 'discord', 'zoom', 'skype']):
                    data['detected_activity'] = 'communication'
                elif any(term in app_lower for term in ['figma', 'sketch', 'photoshop', 'canva', 'adobe']):
                    data['detected_activity'] = 'design'
                elif any(term in app_lower for term in ['excel', 'sheets', 'tableau', 'power', 'jupyter', 'notebook']):
                    data['detected_activity'] = 'analysis'
                elif any(term in app_lower for term in ['word', 'docs', 'notion', 'obsidian', 'notes']):
                    data['detected_activity'] = 'writing'
                else:
                    data['detected_activity'] = 'general'
                    
                data['meaningful_content'] = True
                
        except Exception as e:
            print(f"App detection error: {e}")
        
        try:
            # Get system processes
            import psutil
            top_processes = []
            for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_info']):
                try:
                    info = proc.info
                    if info['cpu_percent'] > 0:
                        top_processes.append({
                            'name': info['name'],
                            'cpu': info['cpu_percent'],
                            'memory_mb': info['memory_info'].rss / 1024 / 1024
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            data['system_processes'] = sorted(top_processes, key=lambda x: x['cpu'], reverse=True)[:5]
            
        except Exception as e:
            print(f"Process detection error: {e}")
        
        return data
    
    async def _create_meaningful_entry(self, real_data):
        """Create meaningful memory entry from real data"""
        
        # Determine professional context with more detail
        activity = real_data['detected_activity']
        app_name = real_data['active_application']
        
        professional_contexts = {
            'development': 'software_engineering',
            'design': 'ui_ux_design', 
            'analysis': 'data_analytics',
            'research': 'information_gathering',
            'communication': 'team_collaboration',
            'writing': 'content_creation',
            'general': 'general_computing'
        }
        
        professional_context = professional_contexts.get(activity, 'general_computing')
        
        # Determine workflow stage with more specificity
        workflow_stages = {
            'development': 'code_implementation',
            'design': 'creative_design_work',
            'analysis': 'data_analysis_processing',
            'research': 'information_research',
            'communication': 'team_collaboration',
            'writing': 'document_creation',
            'general': 'general_computing'
        }
        
        workflow_stage = workflow_stages.get(activity, 'general_computing')
        
        # Add specific activity context
        activity_specifics = []
        if activity == 'development':
            activity_specifics = [f"coding_with_{app_name.lower()}", "software_development", "programming_workflow"]
        elif activity == 'research':
            activity_specifics = [f"research_using_{app_name.lower()}", "information_gathering", "learning_workflow"]
        elif activity == 'communication':
            activity_specifics = [f"communication_via_{app_name.lower()}", "team_collaboration", "professional_communication"]
        elif activity == 'design':
            activity_specifics = [f"design_work_with_{app_name.lower()}", "creative_process", "visual_design"]
        elif activity == 'analysis':
            activity_specifics = [f"data_analysis_using_{app_name.lower()}", "analytical_thinking", "data_processing"]
        elif activity == 'writing':
            activity_specifics = [f"writing_with_{app_name.lower()}", "content_creation", "documentation"]
        else:
            activity_specifics = [f"general_use_of_{app_name.lower()}", "computing_activity"]
        
        # Calculate productivity score
        productivity_score = 0.8 if real_data['meaningful_content'] else 0.3
        if real_data['system_processes']:
            active_processes = len([p for p in real_data['system_processes'] if p['cpu'] > 5])
            productivity_score += min(active_processes / 10.0, 0.2)
        
        # Create comprehensive memory entry
        memory_entry = {
            'timestamp': real_data['timestamp'],
            'memory_type': 'continuous_real_data',
            'data_source': 'simple_continuous_feeder',
            'real_system_data': real_data,
            'user_activity': {
                'detected_activity': activity,
                'professional_context': professional_context,
                'workflow_stage': workflow_stage,
                'activity_specifics': activity_specifics,
                'productivity_score': min(productivity_score, 1.0),
                'meaningful_interaction': real_data['meaningful_content']
            },
            'application_context': {
                'active_application': real_data['active_application'],
                'application_category': self._categorize_application(real_data['active_application']),
                'usage_indicators': self._extract_usage_indicators(real_data)
            },
            'system_context': {
                'active_process_count': len(real_data['system_processes']),
                'top_processes': real_data['system_processes'][:3],
                'system_load': 'active' if real_data['system_processes'] else 'idle'
            },
            'insights': {
                'content_analysis': f"User engaged in {activity} using {real_data['active_application']}",
                'professional_assessment': f"{professional_context} workflow in {workflow_stage} stage",
                'productivity_indicator': f"Productivity score: {productivity_score:.1%}",
                'data_quality': 'high' if real_data['meaningful_content'] else 'medium'
            }
        }
        
        return memory_entry
    
    def _categorize_application(self, app_name):
        """Categorize application"""
        app_lower = app_name.lower()
        
        categories = {
            'ide': ['code', 'visual studio', 'xcode', 'intellij', 'pycharm', 'atom', 'sublime'],
            'browser': ['chrome', 'safari', 'firefox', 'edge'],
            'communication': ['slack', 'teams', 'discord', 'zoom', 'skype'],
            'design': ['figma', 'sketch', 'photoshop', 'illustrator', 'canva'],
            'productivity': ['notion', 'obsidian', 'excel', 'word', 'powerpoint'],
            'terminal': ['terminal', 'iterm', 'cmd', 'powershell'],
            'media': ['spotify', 'music', 'vlc', 'youtube']
        }
        
        for category, apps in categories.items():
            if any(app in app_lower for app in apps):
                return category
        
        return 'general'
    
    def _extract_usage_indicators(self, real_data):
        """Extract usage indicators"""
        indicators = []
        
        if real_data['meaningful_content']:
            indicators.append('active_usage')
        
        if real_data['system_processes']:
            high_cpu_procs = [p for p in real_data['system_processes'] if p['cpu'] > 10]
            if high_cpu_procs:
                indicators.append('high_processing_activity')
            
            if len(real_data['system_processes']) > 3:
                indicators.append('multitasking')
        
        activity = real_data['detected_activity']
        if activity in ['development', 'design', 'analysis']:
            indicators.append('professional_work')
        
        return indicators
    
    async def _save_memory_state(self):
        """Save current memory state"""
        try:
            if hasattr(self.memory_system, 'save_memory_state'):
                await self.memory_system.save_memory_state()
            else:
                # Manual save
                memory_data = {
                    'version': '1.0',
                    'last_update': datetime.now().isoformat(),
                    'short_term': self.memory_system.short_term_memory,
                    'long_term': self.memory_system.long_term_memory,
                    'context': self.memory_system.context_memory
                }
                
                with open('memory/memory/memory_state.json', 'w') as f:
                    json.dump(memory_data, f, indent=2)
                    
                print("💾 Memory state saved manually")
                
        except Exception as e:
            print(f"Save error: {e}")

async def main():
    """Main entry point"""
    print("🚀 SIMPLE CONTINUOUS MEMORY FEEDER")
    print("="*50)
    print("Feeding real meaningful data directly to memory system")
    print()
    
    feeder = SimpleMemoryFeeder()
    
    # Run for 1 minute
    entries_created = await feeder.start_feeding(duration=60)
    
    print()
    print("🎯 MEMORY FEEDING SUMMARY:")
    print(f"   ✅ Entries created: {entries_created}")
    print(f"   📁 Storage: memory/memory/memory_state.json")
    print(f"   🔍 View: python -c \"import json; print(json.dumps(json.load(open('memory/memory/memory_state.json')), indent=2)[:1000])\"")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Memory feeding stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")