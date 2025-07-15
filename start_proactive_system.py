#!/usr/bin/env python3
"""
Start Proactive AI System
Launches the complete system with automatic task identification
"""

import asyncio
import subprocess
import sys
import time
import logging
from pathlib import Path
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProactiveSystemLauncher:
    """Launches the complete proactive AI system"""
    
    def __init__(self):
        self.rpa_process = None
        self.dashboard_process = None
        self.is_running = False
        
    async def start_complete_system(self):
        """Start the complete proactive AI system"""
        try:
            logger.info("🚀 Starting Complete Proactive AI System")
            logger.info("=" * 60)
            
            # Step 1: Start RPA Server
            await self._start_rpa_server()
            
            # Step 2: Start Proactive Dashboard
            await self._start_proactive_dashboard()
            
            # Step 3: Initialize AI Components
            await self._initialize_ai_components()
            
            # Step 4: Start Continuous Analysis
            await self._start_continuous_analysis()
            
            logger.info("✅ Complete Proactive AI System is running!")
            logger.info("📊 Dashboard: http://localhost:5003")
            logger.info("🔧 RPA Server: http://localhost:16901")
            logger.info("🤖 Automatic task identification is active")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to start system: {e}")
            return False
    
    async def _start_rpa_server(self):
        """Start the RPA_AVEN Go server"""
        try:
            logger.info("🔧 Starting RPA Server...")
            
            # Check if RPA server is already running
            import requests
            try:
                response = requests.get("http://localhost:16901/", timeout=2)
                if response.status_code == 200:
                    logger.info("✅ RPA Server already running")
                    return
            except:
                pass
            
            # Start RPA server
            rpa_path = Path(__file__).parent.parent / "RPA_AVEN" / "helper"
            
            if not rpa_path.exists():
                logger.error(f"❌ RPA_AVEN directory not found at {rpa_path}")
                return
            
            # Start the server in background
            self.rpa_process = subprocess.Popen(
                ["go", "run", "*.go"],
                cwd=str(rpa_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            for i in range(10):
                try:
                    response = requests.get("http://localhost:16901/", timeout=2)
                    if response.status_code == 200:
                        logger.info("✅ RPA Server started successfully")
                        return
                except:
                    pass
                await asyncio.sleep(1)
            
            logger.error("❌ RPA Server failed to start")
            
        except Exception as e:
            logger.error(f"❌ Error starting RPA server: {e}")
    
    async def _start_proactive_dashboard(self):
        """Start the proactive dashboard server"""
        try:
            logger.info("📊 Starting Proactive Dashboard...")
            
            # Check if dashboard is already running
            import requests
            try:
                response = requests.get("http://localhost:5003/", timeout=2)
                if response.status_code == 200:
                    logger.info("✅ Proactive Dashboard already running")
                    return
            except:
                pass
            
            # Start dashboard server
            dashboard_script = Path(__file__).parent / "proactive_dashboard_server.py"
            
            if not dashboard_script.exists():
                logger.error(f"❌ Dashboard script not found at {dashboard_script}")
                return
            
            # Start the server in background
            self.dashboard_process = subprocess.Popen(
                [sys.executable, str(dashboard_script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            for i in range(10):
                try:
                    response = requests.get("http://localhost:5003/", timeout=2)
                    if response.status_code == 200:
                        logger.info("✅ Proactive Dashboard started successfully")
                        return
                except:
                    pass
                await asyncio.sleep(1)
            
            logger.error("❌ Proactive Dashboard failed to start")
            
        except Exception as e:
            logger.error(f"❌ Error starting dashboard: {e}")
    
    async def _initialize_ai_components(self):
        """Initialize AI components"""
        try:
            logger.info("🧠 Initializing AI Components...")
            
            # Import and initialize components
            sys.path.insert(0, str(Path(__file__).parent))
            
            # Initialize proactive task identifier
            from proactive_task_identifier import initialize_proactive_identifier
            await initialize_proactive_identifier()
            
            # Initialize enhanced complete system
            from integration.enhanced_complete_system import initialize_enhanced_system
            await initialize_enhanced_system()
            
            logger.info("✅ AI Components initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing AI components: {e}")
    
    async def _start_continuous_analysis(self):
        """Start continuous UI analysis"""
        try:
            logger.info("🔍 Starting Continuous Analysis...")
            
            # Start analysis in background thread
            def run_analysis():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def continuous_analysis():
                    from integration.enhanced_complete_system import enhanced_system
                    
                    while self.is_running:
                        try:
                            # Perform UI analysis
                            analysis = await enhanced_system.understand_ui_and_suggest_tasks()
                            
                            # Log results
                            tasks_count = len(analysis.get('proactive_tasks', []))
                            logger.info(f"🔍 Analysis complete: {tasks_count} proactive tasks identified")
                            
                            # Wait before next analysis
                            await asyncio.sleep(5)
                            
                        except Exception as e:
                            logger.error(f"Error in continuous analysis: {e}")
                            await asyncio.sleep(10)
                
                loop.run_until_complete(continuous_analysis())
                loop.close()
            
            self.is_running = True
            analysis_thread = threading.Thread(target=run_analysis, daemon=True)
            analysis_thread.start()
            
            logger.info("✅ Continuous analysis started")
            
        except Exception as e:
            logger.error(f"❌ Error starting continuous analysis: {e}")
    
    def stop_system(self):
        """Stop the complete system"""
        try:
            logger.info("🛑 Stopping Proactive AI System...")
            
            self.is_running = False
            
            # Stop dashboard process
            if self.dashboard_process:
                self.dashboard_process.terminate()
                logger.info("📊 Dashboard stopped")
            
            # Stop RPA process
            if self.rpa_process:
                self.rpa_process.terminate()
                logger.info("🔧 RPA Server stopped")
            
            logger.info("✅ System stopped")
            
        except Exception as e:
            logger.error(f"❌ Error stopping system: {e}")

async def main():
    """Main function"""
    launcher = ProactiveSystemLauncher()
    
    try:
        # Start the system
        success = await launcher.start_complete_system()
        
        if success:
            logger.info("🎉 Proactive AI System is now running!")
            logger.info("📊 Open http://localhost:5003 to view the dashboard")
            logger.info("🔍 The system will automatically identify potential tasks")
            logger.info("⏹️ Press Ctrl+C to stop the system")
            
            # Keep the system running
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Received stop signal...")
        
    except Exception as e:
        logger.error(f"❌ System startup failed: {e}")
    
    finally:
        launcher.stop_system()

if __name__ == "__main__":
    asyncio.run(main()) 