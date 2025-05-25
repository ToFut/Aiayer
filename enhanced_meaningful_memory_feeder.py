#!/usr/bin/env python3
"""
Enhanced Meaningful Memory Feeder
Captures detailed, specific insights about what users are actually doing
"""

import asyncio
import sys
import os
import json
import time
import subprocess
from datetime import datetime
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.memory_system import MemorySystem

# Vision imports for screen content analysis
try:
    import pyautogui
    import pytesseract
    from PIL import Image
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

class EnhancedMeaningfulMemoryFeeder:
    """Enhanced system to capture detailed, meaningful user activity data"""
    
    def __init__(self):
        self.memory_system = None
        self.running = False
        self.collection_count = 0
        
        # Enhanced application detection
        self.application_patterns = {
            'development': {
                'keywords': ['cursor', 'code', 'visual studio', 'vscode', 'xcode', 'intellij', 'pycharm', 'atom', 'sublime', 'vim', 'emacs', 'webstorm', 'phpstorm'],
                'indicators': ['def ', 'function', 'import', 'class ', 'const ', 'var ', 'let ', '{', '}', 'git', 'npm', 'pip', 'python', 'javascript', 'typescript']
            },
            'research': {
                'keywords': ['chrome', 'safari', 'firefox', 'edge', 'browser'],
                'indicators': ['stackoverflow', 'github', 'documentation', 'docs', 'tutorial', 'api', 'reference', 'search', 'google']
            },
            'communication': {
                'keywords': ['slack', 'teams', 'discord', 'zoom', 'skype', 'telegram', 'whatsapp'],
                'indicators': ['message', 'chat', 'call', 'meeting', 'channel']
            },
            'design': {
                'keywords': ['figma', 'sketch', 'photoshop', 'illustrator', 'canva', 'adobe'],
                'indicators': ['design', 'prototype', 'color', 'font', 'pixel', 'vector']
            },
            'data_analysis': {
                'keywords': ['tableau', 'excel', 'sheets', 'jupyter', 'notebook', 'powerbi', 'r studio'],
                'indicators': ['chart', 'graph', 'data', 'analysis', 'visualization', 'dashboard']
            },
            'writing': {
                'keywords': ['word', 'docs', 'notion', 'obsidian', 'bear', 'notes', 'typora'],
                'indicators': ['document', 'article', 'writing', 'markdown', 'text']
            }
        }
        
    async def initialize(self):
        """Initialize memory system"""
        print("🧠 Initializing enhanced meaningful memory system...")
        self.memory_system = MemorySystem()
        print("✅ Enhanced memory system ready")
        return True
    
    async def start_meaningful_feeding(self, duration=120):
        """Start feeding detailed meaningful data"""
        if not await self.initialize():
            return
            
        print(f"🚀 STARTING ENHANCED MEANINGFUL MEMORY FEEDING")
        print(f"Duration: {duration} seconds")
        print(f"📊 Capturing detailed insights every 8 seconds")
        print(f"🎯 Focus: Real activity analysis, UI content, and professional context")
        print()
        
        self.running = True
        end_time = time.time() + duration
        
        while self.running and time.time() < end_time:
            try:
                # Collect comprehensive real data
                detailed_data = await self._collect_detailed_system_data()
                
                # Analyze screen content if possible
                screen_analysis = await self._analyze_screen_content()
                
                # Create meaningful memory entry
                memory_entry = await self._create_detailed_memory_entry(detailed_data, screen_analysis)
                
                # Store in memory
                memory_id = await self.memory_system.add_to_short_term_memory(memory_entry)
                
                self.collection_count += 1
                remaining = int(end_time - time.time())
                
                # Show meaningful summary
                activity_summary = memory_entry['detailed_analysis']['activity_summary']
                context_summary = memory_entry['detailed_analysis']['context_summary']
                
                print(f"✅ Entry #{self.collection_count} | {remaining}s remaining")
                print(f"   🎯 Activity: {activity_summary}")
                print(f"   🏢 Context: {context_summary}")
                print(f"   💻 App: {detailed_data['active_application']}")
                print(f"   📊 Depth: {memory_entry['meaningful_metrics']['content_depth_score']:.0%}")
                print()
                
                # Wait before next collection
                await asyncio.sleep(8)
                
            except Exception as e:
                print(f"⚠️ Collection error: {e}")
                await asyncio.sleep(5)
        
        # Final save
        await self._save_memory_state()
        
        print(f"🎯 ENHANCED FEEDING COMPLETE")
        print(f"   Total detailed entries: {self.collection_count}")
        print(f"   Memory stored with deep insights")
        
        return self.collection_count
    
    async def _collect_detailed_system_data(self):
        """Collect comprehensive system data with context"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'active_application': 'Unknown',
            'window_title': '',
            'detected_activity_type': 'general',
            'professional_domain': 'general_computing',
            'system_processes': [],
            'meaningful_content_detected': False,
            'specific_indicators': [],
            'application_context': {}
        }
        
        try:
            # Get active application and window title
            app_script = '''
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                set appName to name of frontApp
                try
                    set windowTitle to name of first window of frontApp
                on error
                    set windowTitle to ""
                end try
                return appName & "|||" & windowTitle
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', app_script], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                parts = result.stdout.strip().split('|||')
                data['active_application'] = parts[0] if len(parts) > 0 else 'Unknown'
                data['window_title'] = parts[1] if len(parts) > 1 else ''
                
                # Detailed activity analysis
                activity_analysis = self._analyze_detailed_activity(data['active_application'], data['window_title'])
                data.update(activity_analysis)
                
        except Exception as e:
            print(f"App detection error: {e}")
        
        try:
            # Enhanced process analysis
            import psutil
            
            processes = []
            for proc in psutil.process_iter(['name', 'cpu_percent', 'memory_info', 'cmdline']):
                try:
                    info = proc.info
                    if info['cpu_percent'] > 0 or info['memory_info'].rss > 50*1024*1024:  # >50MB
                        processes.append({
                            'name': info['name'],
                            'cpu': info['cpu_percent'],
                            'memory_mb': info['memory_info'].rss / 1024 / 1024,
                            'cmdline': ' '.join(info['cmdline'][:3]) if info['cmdline'] else ''
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            data['system_processes'] = sorted(processes, key=lambda x: x['cpu'], reverse=True)[:8]
            
            # Analyze processes for professional indicators
            process_analysis = self._analyze_process_patterns(processes)
            data['process_insights'] = process_analysis
            
        except Exception as e:
            print(f"Process analysis error: {e}")
        
        return data
    
    def _analyze_detailed_activity(self, app_name, window_title):
        """Perform detailed activity analysis"""
        app_lower = app_name.lower()
        window_lower = window_title.lower()
        combined_text = f"{app_lower} {window_lower}"
        
        analysis = {
            'detected_activity_type': 'general',
            'professional_domain': 'general_computing',
            'specific_indicators': [],
            'confidence_score': 0.0,
            'detailed_context': {},
            'meaningful_content_detected': False
        }
        
        # Enhanced pattern matching
        best_match = None
        best_score = 0
        
        for activity_type, patterns in self.application_patterns.items():
            score = 0
            matched_indicators = []
            
            # Check application keywords
            for keyword in patterns['keywords']:
                if keyword in app_lower:
                    score += 3  # High weight for app match
                    matched_indicators.append(f"app:{keyword}")
            
            # Check content indicators in window title
            for indicator in patterns['indicators']:
                if indicator in combined_text:
                    score += 1
                    matched_indicators.append(f"content:{indicator}")
            
            if score > best_score:
                best_score = score
                best_match = activity_type
                analysis['specific_indicators'] = matched_indicators
        
        if best_match and best_score > 0:
            analysis['detected_activity_type'] = best_match
            analysis['confidence_score'] = min(best_score / 5.0, 1.0)
            analysis['meaningful_content_detected'] = True
            
            # Set professional domain
            domain_mapping = {
                'development': 'software_engineering',
                'research': 'technical_research',
                'communication': 'team_collaboration',
                'design': 'ui_ux_design',
                'data_analysis': 'data_science',
                'writing': 'content_creation'
            }
            analysis['professional_domain'] = domain_mapping.get(best_match, 'general_computing')
            
            # Add detailed context
            analysis['detailed_context'] = self._extract_detailed_context(best_match, window_title, app_name)
        
        return analysis
    
    def _extract_detailed_context(self, activity_type, window_title, app_name):
        """Extract detailed context based on activity type"""
        context = {
            'activity_specifics': [],
            'tools_detected': [],
            'work_indicators': [],
            'complexity_level': 'basic'
        }
        
        window_lower = window_title.lower()
        
        if activity_type == 'development':
            # Programming language detection
            languages = ['python', 'javascript', 'typescript', 'java', 'c++', 'rust', 'go', 'swift']
            for lang in languages:
                if lang in window_lower:
                    context['activity_specifics'].append(f"{lang}_programming")
            
            # Development activities
            if any(term in window_lower for term in ['debug', 'error', 'exception']):
                context['activity_specifics'].append('debugging')
                context['complexity_level'] = 'advanced'
            elif any(term in window_lower for term in ['test', 'spec']):
                context['activity_specifics'].append('testing')
            elif any(term in window_lower for term in ['config', 'setup']):
                context['activity_specifics'].append('configuration')
            
            # File types
            file_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.rs', '.go', '.swift', '.html', '.css']
            for ext in file_extensions:
                if ext in window_lower:
                    context['tools_detected'].append(f"file_type{ext}")
        
        elif activity_type == 'research':
            # Research specifics
            if any(term in window_lower for term in ['stackoverflow', 'github', 'docs']):
                context['activity_specifics'].append('technical_documentation')
            elif any(term in window_lower for term in ['tutorial', 'learn', 'course']):
                context['activity_specifics'].append('learning')
            elif any(term in window_lower for term in ['api', 'reference']):
                context['activity_specifics'].append('api_research')
        
        elif activity_type == 'communication':
            # Communication specifics
            if any(term in window_lower for term in ['meeting', 'call']):
                context['activity_specifics'].append('video_conference')
            elif any(term in window_lower for term in ['channel', 'dm', 'message']):
                context['activity_specifics'].append('text_communication')
        
        # Work complexity indicators
        complexity_indicators = ['advanced', 'complex', 'enterprise', 'production', 'critical']
        if any(indicator in window_lower for indicator in complexity_indicators):
            context['complexity_level'] = 'advanced'
        elif any(indicator in window_lower for indicator in ['pro', 'professional', 'business']):
            context['complexity_level'] = 'professional'
        
        return context
    
    def _analyze_process_patterns(self, processes):
        """Analyze running processes for professional patterns"""
        analysis = {
            'development_tools_active': [],
            'productivity_tools': [],
            'system_load_type': 'light',
            'multitasking_level': 'low',
            'professional_indicators': []
        }
        
        dev_tools = ['python', 'node', 'npm', 'git', 'docker', 'java', 'gradle', 'maven']
        productivity_tools = ['slack', 'teams', 'notion', 'obsidian', 'excel']
        
        high_cpu_count = 0
        for proc in processes:
            proc_name = proc['name'].lower()
            
            # Development tools
            for tool in dev_tools:
                if tool in proc_name:
                    analysis['development_tools_active'].append(tool)
            
            # Productivity tools
            for tool in productivity_tools:
                if tool in proc_name:
                    analysis['productivity_tools'].append(tool)
            
            # System load analysis
            if proc['cpu'] > 20:
                high_cpu_count += 1
        
        # Determine system load
        if high_cpu_count > 3:
            analysis['system_load_type'] = 'heavy'
        elif high_cpu_count > 1:
            analysis['system_load_type'] = 'moderate'
        
        # Multitasking level
        if len(processes) > 15:
            analysis['multitasking_level'] = 'high'
        elif len(processes) > 8:
            analysis['multitasking_level'] = 'moderate'
        
        return analysis
    
    async def _analyze_screen_content(self):
        """Analyze screen content for additional context"""
        analysis = {
            'screen_content_available': False,
            'text_extracted': '',
            'ui_elements_detected': [],
            'content_type': 'unknown',
            'engagement_indicators': []
        }
        
        if not VISION_AVAILABLE:
            return analysis
        
        try:
            # Capture small screenshot for analysis
            screenshot = pyautogui.screenshot()
            
            # Resize for faster processing
            screenshot.thumbnail((800, 600))
            
            # Extract text
            extracted_text = pytesseract.image_to_string(screenshot)
            
            if extracted_text and len(extracted_text.strip()) > 10:
                analysis['screen_content_available'] = True
                analysis['text_extracted'] = extracted_text[:500]  # First 500 chars
                
                # Analyze content
                text_lower = extracted_text.lower()
                
                # UI elements detection
                ui_elements = []
                if any(word in text_lower for word in ['button', 'click', 'submit', 'save']):
                    ui_elements.append('interactive_buttons')
                if any(word in text_lower for word in ['menu', 'navigation', 'nav']):
                    ui_elements.append('navigation_elements')
                if any(word in text_lower for word in ['form', 'input', 'field']):
                    ui_elements.append('form_elements')
                
                analysis['ui_elements_detected'] = ui_elements
                
                # Content type detection
                if any(word in text_lower for word in ['code', 'function', 'def', 'class']):
                    analysis['content_type'] = 'source_code'
                elif any(word in text_lower for word in ['error', 'exception', 'debug']):
                    analysis['content_type'] = 'error_debugging'
                elif any(word in text_lower for word in ['document', 'article', 'text']):
                    analysis['content_type'] = 'documentation'
                elif any(word in text_lower for word in ['chart', 'graph', 'data']):
                    analysis['content_type'] = 'data_visualization'
        
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    async def _create_detailed_memory_entry(self, detailed_data, screen_analysis):
        """Create comprehensive detailed memory entry"""
        
        # Generate activity summary
        activity_type = detailed_data['detected_activity_type']
        app_name = detailed_data['active_application']
        indicators = detailed_data['specific_indicators']
        
        if activity_type != 'general' and indicators:
            activity_summary = f"{activity_type.replace('_', ' ')} work with {app_name}"
            if detailed_data['detailed_context']['activity_specifics']:
                specifics = detailed_data['detailed_context']['activity_specifics'][0]
                activity_summary += f" ({specifics.replace('_', ' ')})"
        else:
            activity_summary = f"General computing with {app_name}"
        
        # Generate context summary
        domain = detailed_data['professional_domain']
        complexity = detailed_data['detailed_context'].get('complexity_level', 'basic')
        context_summary = f"{domain.replace('_', ' ')} ({complexity} level)"
        
        # Calculate meaningful metrics
        content_depth_score = detailed_data['confidence_score']
        if screen_analysis['screen_content_available']:
            content_depth_score += 0.2
        if detailed_data['detailed_context']['activity_specifics']:
            content_depth_score += 0.2
        content_depth_score = min(content_depth_score, 1.0)
        
        # Create comprehensive entry
        memory_entry = {
            'timestamp': detailed_data['timestamp'],
            'memory_type': 'enhanced_meaningful_data',
            'data_source': 'enhanced_meaningful_feeder',
            
            # Raw data
            'raw_system_data': detailed_data,
            'screen_analysis': screen_analysis,
            
            # Processed insights
            'detailed_analysis': {
                'activity_type': activity_type,
                'activity_summary': activity_summary,
                'professional_domain': domain,
                'context_summary': context_summary,
                'specific_activities': detailed_data['detailed_context']['activity_specifics'],
                'tools_detected': detailed_data['detailed_context']['tools_detected'],
                'complexity_assessment': complexity
            },
            
            'application_intelligence': {
                'active_application': app_name,
                'window_title': detailed_data['window_title'],
                'application_category': self._get_app_category(activity_type),
                'usage_context': detailed_data['detailed_context'],
                'professional_relevance': 'high' if content_depth_score > 0.6 else 'medium'
            },
            
            'system_intelligence': {
                'process_insights': detailed_data.get('process_insights', {}),
                'development_environment': detailed_data.get('process_insights', {}).get('development_tools_active', []),
                'productivity_stack': detailed_data.get('process_insights', {}).get('productivity_tools', []),
                'system_performance': detailed_data.get('process_insights', {}).get('system_load_type', 'light'),
                'multitasking_assessment': detailed_data.get('process_insights', {}).get('multitasking_level', 'low')
            },
            
            'meaningful_metrics': {
                'content_depth_score': content_depth_score,
                'professional_context_confidence': detailed_data['confidence_score'],
                'screen_content_richness': 1.0 if screen_analysis['screen_content_available'] else 0.0,
                'activity_specificity': len(detailed_data['specific_indicators']) / 5.0,
                'overall_meaningfulness': (content_depth_score + detailed_data['confidence_score']) / 2.0
            },
            
            'insights': {
                'primary_insight': f"User engaged in {activity_summary}",
                'professional_assessment': f"Active {context_summary} with {len(detailed_data['specific_indicators'])} specific indicators",
                'productivity_context': f"System load: {detailed_data.get('process_insights', {}).get('system_load_type', 'unknown')}, complexity: {complexity}",
                'meaningful_content_quality': 'high' if content_depth_score > 0.7 else 'medium' if content_depth_score > 0.4 else 'basic'
            }
        }
        
        return memory_entry
    
    def _get_app_category(self, activity_type):
        """Get application category based on activity type"""
        category_mapping = {
            'development': 'ide_development_tool',
            'research': 'browser_research_tool', 
            'communication': 'collaboration_platform',
            'design': 'creative_design_tool',
            'data_analysis': 'analytics_platform',
            'writing': 'document_editor',
            'general': 'general_application'
        }
        return category_mapping.get(activity_type, 'general_application')
    
    async def _save_memory_state(self):
        """Save memory state with detailed content"""
        try:
            memory_data = {
                'version': '1.0',
                'last_update': datetime.now().isoformat(),
                'short_term': self.memory_system.short_term_memory,
                'long_term': self.memory_system.long_term_memory,
                'context': self.memory_system.context_memory
            }
            
            with open('memory/memory/memory_state.json', 'w') as f:
                json.dump(memory_data, f, indent=2)
                
            print("💾 Enhanced memory state saved with detailed insights")
            
        except Exception as e:
            print(f"Save error: {e}")

async def main():
    """Main entry point for enhanced meaningful feeding"""
    print("🚀 ENHANCED MEANINGFUL MEMORY FEEDER")
    print("="*60)
    print("Capturing detailed, specific insights about user activities")
    print("Going beyond generic data to meaningful professional context")
    print()
    
    feeder = EnhancedMeaningfulMemoryFeeder()
    
    # Run for 2 minutes to collect detailed data
    entries_created = await feeder.start_meaningful_feeding(duration=120)
    
    print()
    print("🎯 ENHANCED MEMORY FEEDING SUMMARY:")
    print(f"   ✅ Detailed entries created: {entries_created}")
    print(f"   📁 Storage: memory/memory/memory_state.json")
    print(f"   🔍 Deep insights: Professional context, activity specifics, tool detection")
    print(f"   🎯 View: python memory_status_report.py")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Enhanced memory feeding stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")