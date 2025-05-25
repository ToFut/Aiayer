#!/usr/bin/env python3
"""
Continuous Sensor System for Real Meaningful Memory Collection
Feeds live data continuously to memory system with deep understanding
"""

import asyncio
import sys
import os
import json
import time
import signal
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our systems
from memory.memory_system import MemorySystem
from complete_ui_understanding_system import CompleteUIUnderstandingSystem
from enhanced_memory_with_deep_ui import EnhancedMemoryWithDeepUI

# Import sensors
SENSORS_AVAILABLE = False
try:
    from sensors.enhanced_fixed_screen_sensor import EnhancedScreenSensor
    from sensors.enhanced_fixed_process_sensor import EnhancedProcessSensor
    SENSORS_AVAILABLE = True
except ImportError:
    SENSORS_AVAILABLE = False
    print("⚠️ Enhanced sensors not available, using basic monitoring")

class ContinuousSensorSystem:
    """Continuous system for feeding real meaningful data to memory"""
    
    def __init__(self):
        self.running = False
        self.memory_system = None
        self.ui_system = None
        self.enhanced_memory = None
        self.screen_sensor = None
        self.process_sensor = None
        
        # Configuration
        self.config = {
            'screen_interval': 10,    # Every 10 seconds
            'process_interval': 5,    # Every 5 seconds  
            'ui_analysis_interval': 30,  # Every 30 seconds
            'memory_consolidation_interval': 60,  # Every minute
            'log_interval': 15        # Status log every 15 seconds
        }
        
        # Performance tracking
        self.stats = {
            'total_collections': 0,
            'screen_captures': 0,
            'process_scans': 0,
            'ui_analyses': 0,
            'memory_entries': 0,
            'start_time': None,
            'last_activity': None
        }
        
    async def initialize(self):
        """Initialize all systems"""
        print("🚀 INITIALIZING CONTINUOUS SENSOR SYSTEM")
        print("="*60)
        
        try:
            # Initialize memory system
            print("🧠 Initializing memory system...")
            self.memory_system = MemorySystem()
            
            # Initialize UI understanding system
            print("🎛️ Initializing UI understanding system...")
            self.ui_system = CompleteUIUnderstandingSystem()
            
            # Initialize enhanced memory
            print("💡 Initializing enhanced memory system...")
            self.enhanced_memory = EnhancedMemoryWithDeepUI()
            
            # Initialize sensors if available
            if SENSORS_AVAILABLE:
                print("📡 Initializing enhanced sensors...")
                try:
                    self.screen_sensor = EnhancedScreenSensor()
                    self.process_sensor = EnhancedProcessSensor()
                    print("✅ Enhanced sensors initialized")
                except Exception as e:
                    print(f"⚠️ Enhanced sensor initialization error: {e}")
                    self.screen_sensor = None
                    self.process_sensor = None
            else:
                print("📡 Using basic sensor monitoring")
                self.screen_sensor = None
                self.process_sensor = None
            
            # Setup signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            print("✅ All systems initialized successfully")
            print(f"📊 Collection intervals:")
            print(f"   • Screen: every {self.config['screen_interval']}s")
            print(f"   • Process: every {self.config['process_interval']}s") 
            print(f"   • UI Analysis: every {self.config['ui_analysis_interval']}s")
            print(f"   • Memory Consolidation: every {self.config['memory_consolidation_interval']}s")
            
            return True
            
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def start_continuous_collection(self):
        """Start continuous data collection"""
        if not await self.initialize():
            return
            
        print("\n🎯 STARTING CONTINUOUS DATA COLLECTION")
        print("="*60)
        print("📊 Real-time memory feeding with meaningful content analysis")
        print("🛑 Press Ctrl+C to stop gracefully")
        print()
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        # Start all collection tasks concurrently
        tasks = [
            asyncio.create_task(self._screen_collection_loop()),
            asyncio.create_task(self._process_collection_loop()),
            asyncio.create_task(self._ui_analysis_loop()),
            asyncio.create_task(self._memory_consolidation_loop()),
            asyncio.create_task(self._status_reporting_loop())
        ]
        
        try:
            # Wait for all tasks
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            print("🛑 Collection stopped by user")
        except Exception as e:
            print(f"❌ Collection error: {e}")
        finally:
            self.running = False
            await self._cleanup()
    
    async def _screen_collection_loop(self):
        """Continuous screen data collection"""
        while self.running:
            try:
                screen_data = await self._collect_screen_data()
                if screen_data:
                    await self._process_screen_insights(screen_data)
                    self.stats['screen_captures'] += 1
                    self.stats['last_activity'] = 'screen_capture'
                
                await asyncio.sleep(self.config['screen_interval'])
                
            except Exception as e:
                print(f"⚠️ Screen collection error: {e}")
                await asyncio.sleep(self.config['screen_interval'])
    
    async def _process_collection_loop(self):
        """Continuous process data collection"""
        while self.running:
            try:
                process_data = await self._collect_process_data()
                if process_data:
                    await self._process_system_insights(process_data)
                    self.stats['process_scans'] += 1
                    self.stats['last_activity'] = 'process_scan'
                
                await asyncio.sleep(self.config['process_interval'])
                
            except Exception as e:
                print(f"⚠️ Process collection error: {e}")
                await asyncio.sleep(self.config['process_interval'])
    
    async def _ui_analysis_loop(self):
        """Continuous UI analysis"""
        while self.running:
            try:
                ui_analysis = await self.ui_system.perform_complete_ui_analysis()
                if ui_analysis:
                    await self._process_ui_insights(ui_analysis)
                    self.stats['ui_analyses'] += 1
                    self.stats['last_activity'] = 'ui_analysis'
                
                await asyncio.sleep(self.config['ui_analysis_interval'])
                
            except Exception as e:
                print(f"⚠️ UI analysis error: {e}")
                await asyncio.sleep(self.config['ui_analysis_interval'])
    
    async def _memory_consolidation_loop(self):
        """Continuous memory consolidation"""
        while self.running:
            try:
                await self._consolidate_memory()
                await asyncio.sleep(self.config['memory_consolidation_interval'])
                
            except Exception as e:
                print(f"⚠️ Memory consolidation error: {e}")
                await asyncio.sleep(self.config['memory_consolidation_interval'])
    
    async def _status_reporting_loop(self):
        """Regular status reporting"""
        while self.running:
            try:
                await self._report_status()
                await asyncio.sleep(self.config['log_interval'])
                
            except Exception as e:
                print(f"⚠️ Status reporting error: {e}")
                await asyncio.sleep(self.config['log_interval'])
    
    async def _collect_screen_data(self):
        """Collect real screen data with context"""
        try:
            if SENSORS_AVAILABLE and self.screen_sensor:
                # Use enhanced screen sensor
                screen_data = await self.screen_sensor.capture_enhanced_screen_content()
            else:
                # Use basic screen capture
                screen_data = await self._basic_screen_capture()
            
            if screen_data:
                # Add timestamp and context
                screen_data['collection_timestamp'] = datetime.now().isoformat()
                screen_data['collection_method'] = 'enhanced' if SENSORS_AVAILABLE else 'basic'
                
                # Analyze content for meaning
                screen_data['content_analysis'] = await self._analyze_screen_content(screen_data)
                
            return screen_data
            
        except Exception as e:
            print(f"Screen collection error: {e}")
            return None
    
    async def _collect_process_data(self):
        """Collect real process data with context"""
        try:
            if SENSORS_AVAILABLE and self.process_sensor:
                # Use enhanced process sensor
                process_data = await self.process_sensor.get_enhanced_process_analysis()
            else:
                # Use basic process collection
                process_data = await self._basic_process_scan()
            
            if process_data:
                # Add timestamp and context
                process_data['collection_timestamp'] = datetime.now().isoformat()
                process_data['collection_method'] = 'enhanced' if SENSORS_AVAILABLE else 'basic'
                
                # Analyze for professional context
                process_data['professional_analysis'] = await self._analyze_process_context(process_data)
                
            return process_data
            
        except Exception as e:
            print(f"Process collection error: {e}")
            return None
    
    async def _basic_screen_capture(self):
        """Basic screen capture fallback"""
        try:
            import pyautogui
            import pytesseract
            
            # Capture screenshot
            screenshot = pyautogui.screenshot()
            
            # Extract text
            extracted_text = pytesseract.image_to_string(screenshot)
            
            return {
                'method': 'basic_pyautogui',
                'extracted_text': extracted_text,
                'text_length': len(extracted_text),
                'has_content': len(extracted_text.strip()) > 0
            }
            
        except Exception as e:
            # Ultra-basic fallback - simulated based on active window
            import subprocess
            try:
                # Get active window (macOS)
                result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get name of first application process whose frontmost is true'], 
                                      capture_output=True, text=True)
                active_app = result.stdout.strip()
                
                return {
                    'method': 'basic_osascript',
                    'active_application': active_app,
                    'extracted_text': f"User is using {active_app}",
                    'text_length': len(active_app) + 15,
                    'has_content': True
                }
            except:
                return {
                    'method': 'minimal',
                    'extracted_text': "Active user session detected",
                    'text_length': 28,
                    'has_content': True
                }
    
    async def _basic_process_scan(self):
        """Basic process scanning fallback"""
        try:
            import psutil
            
            # Get running processes
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
                try:
                    info = proc.info
                    if info['cpu_percent'] > 0 or info['memory_info'].rss > 100*1024*1024:  # >100MB
                        processes.append({
                            'name': info['name'],
                            'pid': info['pid'],
                            'cpu_percent': info['cpu_percent'],
                            'memory_mb': info['memory_info'].rss / 1024 / 1024
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            processes = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:10]
            
            return {
                'method': 'basic_psutil',
                'top_processes': processes,
                'process_count': len(processes),
                'system_active': len(processes) > 0
            }
            
        except Exception as e:
            return {
                'method': 'minimal',
                'system_status': 'active',
                'timestamp': datetime.now().isoformat()
            }
    
    async def _analyze_screen_content(self, screen_data):
        """Analyze screen content for meaningful insights"""
        analysis = {
            'content_type': 'unknown',
            'activity_indicators': [],
            'professional_context': 'general',
            'engagement_level': 0.0,
            'meaningful_content': False
        }
        
        text = screen_data.get('extracted_text', '')
        if not text:
            return analysis
        
        text_lower = text.lower()
        
        # Detect content type
        if any(keyword in text_lower for keyword in ['code', 'function', 'class', 'import', 'def', 'var', 'const']):
            analysis['content_type'] = 'development'
            analysis['professional_context'] = 'software_development'
            analysis['activity_indicators'].append('coding')
            
        elif any(keyword in text_lower for keyword in ['dashboard', 'analytics', 'chart', 'graph', 'metrics']):
            analysis['content_type'] = 'analytics'
            analysis['professional_context'] = 'data_analysis'
            analysis['activity_indicators'].append('data_analysis')
            
        elif any(keyword in text_lower for keyword in ['design', 'prototype', 'figma', 'sketch', 'color']):
            analysis['content_type'] = 'design'
            analysis['professional_context'] = 'ui_ux_design'
            analysis['activity_indicators'].append('designing')
            
        elif any(keyword in text_lower for keyword in ['email', 'message', 'chat', 'slack', 'teams']):
            analysis['content_type'] = 'communication'
            analysis['professional_context'] = 'collaboration'
            analysis['activity_indicators'].append('communicating')
        
        # Calculate engagement level
        word_count = len(text.split())
        if word_count > 100:
            analysis['engagement_level'] = min(word_count / 500.0, 1.0)
            analysis['meaningful_content'] = True
        
        return analysis
    
    async def _analyze_process_context(self, process_data):
        """Analyze process data for professional context"""
        analysis = {
            'professional_tools': [],
            'development_activity': False,
            'productivity_score': 0.0,
            'multitasking_level': 'low'
        }
        
        processes = process_data.get('top_processes', [])
        if not processes:
            return analysis
        
        # Professional tool detection
        dev_tools = ['code', 'visual studio', 'xcode', 'intellij', 'pycharm', 'atom', 'sublime']
        design_tools = ['figma', 'sketch', 'photoshop', 'illustrator', 'canva']
        analysis_tools = ['tableau', 'excel', 'jupyter', 'notebook', 'powerbi']
        
        for proc in processes:
            proc_name = proc.get('name', '').lower()
            
            if any(tool in proc_name for tool in dev_tools):
                analysis['professional_tools'].append('development')
                analysis['development_activity'] = True
                
            elif any(tool in proc_name for tool in design_tools):
                analysis['professional_tools'].append('design')
                
            elif any(tool in proc_name for tool in analysis_tools):
                analysis['professional_tools'].append('analytics')
        
        # Calculate productivity score
        active_processes = len([p for p in processes if p.get('cpu_percent', 0) > 5])
        analysis['productivity_score'] = min(active_processes / 5.0, 1.0)
        
        # Multitasking level
        if len(processes) > 8:
            analysis['multitasking_level'] = 'high'
        elif len(processes) > 4:
            analysis['multitasking_level'] = 'medium'
        
        return analysis
    
    async def _process_screen_insights(self, screen_data):
        """Process screen data into memory insights"""
        try:
            # Create meaningful memory entry
            memory_entry = {
                'timestamp': datetime.now().isoformat(),
                'memory_type': 'screen_analysis',
                'data_source': 'continuous_sensor',
                'screen_context': screen_data,
                'user_activity': {
                    'content_type': screen_data['content_analysis']['content_type'],
                    'professional_context': screen_data['content_analysis']['professional_context'],
                    'activity_indicators': screen_data['content_analysis']['activity_indicators'],
                    'engagement_level': screen_data['content_analysis']['engagement_level'],
                    'meaningful_interaction': screen_data['content_analysis']['meaningful_content']
                },
                'insights': {
                    'screen_content_analysis': screen_data['content_analysis'],
                    'data_quality': 'high' if screen_data['content_analysis']['meaningful_content'] else 'medium',
                    'collection_method': screen_data.get('collection_method', 'unknown')
                }
            }
            
            # Store in memory system
            memory_id = await self.memory_system.add_to_short_term_memory(memory_entry)
            self.stats['memory_entries'] += 1
            
            print(f"📄 Screen insight stored: {screen_data['content_analysis']['content_type']} activity")
            
        except Exception as e:
            print(f"Error processing screen insights: {e}")
    
    async def _process_system_insights(self, process_data):
        """Process system data into memory insights"""
        try:
            # Create meaningful memory entry
            memory_entry = {
                'timestamp': datetime.now().isoformat(),
                'memory_type': 'system_analysis',
                'data_source': 'continuous_sensor',
                'system_context': process_data,
                'professional_activity': {
                    'tools_in_use': process_data['professional_analysis']['professional_tools'],
                    'development_active': process_data['professional_analysis']['development_activity'],
                    'productivity_level': process_data['professional_analysis']['productivity_score'],
                    'multitasking_level': process_data['professional_analysis']['multitasking_level']
                },
                'insights': {
                    'system_performance': process_data['professional_analysis'],
                    'active_process_count': process_data.get('process_count', 0),
                    'collection_method': process_data.get('collection_method', 'unknown')
                }
            }
            
            # Store in memory system
            memory_id = await self.memory_system.add_to_short_term_memory(memory_entry)
            self.stats['memory_entries'] += 1
            
            tools = process_data['professional_analysis']['professional_tools']
            if tools:
                print(f"⚙️ System insight stored: {', '.join(tools)} tools active")
            
        except Exception as e:
            print(f"Error processing system insights: {e}")
    
    async def _process_ui_insights(self, ui_analysis):
        """Process UI analysis into memory insights"""
        try:
            # Create comprehensive memory entry
            memory_entry = {
                'timestamp': datetime.now().isoformat(),
                'memory_type': 'complete_ui_analysis',
                'data_source': 'continuous_sensor',
                'ui_analysis': ui_analysis,
                'ui_understanding': {
                    'detected_elements': sum(len(subcat) for cat in ui_analysis["ui_elements"].values() for subcat in cat.values()),
                    'platform_identified': ui_analysis["saas_platform"]["platform"] if ui_analysis["saas_platform"] else None,
                    'visualizations_count': len(ui_analysis["visualizations"]),
                    'complexity_level': "high" if ui_analysis["ui_complexity_score"] > 0.7 else "medium" if ui_analysis["ui_complexity_score"] > 0.4 else "low",
                    'usability_score': ui_analysis["usability_analysis"]["overall_usability_score"]
                },
                'professional_insights': {
                    'ui_complexity': ui_analysis["ui_insights"]["ui_complexity"],
                    'workflow_stage': ui_analysis["ui_insights"]["workflow_stage"],
                    'interaction_patterns': ui_analysis["ui_insights"]["interaction_patterns"],
                    'learning_curve': ui_analysis["ui_insights"]["learning_curve_assessment"]
                }
            }
            
            # Store in memory system
            memory_id = await self.memory_system.add_to_short_term_memory(memory_entry)
            self.stats['memory_entries'] += 1
            
            platform = ui_analysis["saas_platform"]["platform"] if ui_analysis["saas_platform"] else "generic"
            elements = sum(len(subcat) for cat in ui_analysis["ui_elements"].values() for subcat in cat.values())
            print(f"🎛️ UI insight stored: {platform} interface, {elements} elements")
            
        except Exception as e:
            print(f"Error processing UI insights: {e}")
    
    async def _consolidate_memory(self):
        """Consolidate memory and create higher-level insights"""
        try:
            # This could trigger memory consolidation, pattern recognition, etc.
            if hasattr(self.memory_system, 'consolidate_patterns'):
                await self.memory_system.consolidate_patterns()
                
        except Exception as e:
            print(f"Memory consolidation error: {e}")
    
    async def _report_status(self):
        """Report system status"""
        if self.stats['start_time']:
            runtime = datetime.now() - self.stats['start_time']
            runtime_str = str(runtime).split('.')[0]  # Remove microseconds
            
            print(f"📊 Status | Runtime: {runtime_str} | "
                  f"Collections: {self.stats['total_collections']} | "
                  f"Memory Entries: {self.stats['memory_entries']} | "
                  f"Last: {self.stats['last_activity']}")
            
            self.stats['total_collections'] += 1
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    async def _cleanup(self):
        """Cleanup resources"""
        print("\n🧹 Cleaning up resources...")
        
        # Final statistics
        if self.stats['start_time']:
            runtime = datetime.now() - self.stats['start_time']
            print(f"\n📈 FINAL STATISTICS:")
            print(f"   • Runtime: {runtime}")
            print(f"   • Total Collections: {self.stats['total_collections']}")
            print(f"   • Screen Captures: {self.stats['screen_captures']}")
            print(f"   • Process Scans: {self.stats['process_scans']}")
            print(f"   • UI Analyses: {self.stats['ui_analyses']}")
            print(f"   • Memory Entries Created: {self.stats['memory_entries']}")
        
        print("✅ Cleanup complete")

async def main():
    """Main entry point"""
    print("🚀 CONTINUOUS SENSOR SYSTEM")
    print("="*50)
    print("Real-time memory feeding with meaningful content analysis")
    
    sensor_system = ContinuousSensorSystem()
    await sensor_system.start_continuous_collection()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Continuous sensor system stopped")
    except Exception as e:
        print(f"\n❌ System error: {e}")