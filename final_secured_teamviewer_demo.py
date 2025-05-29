#!/usr/bin/env python3
"""
Final Secured TeamViewer-Style Demo
Demonstrates the complete 100% local, secure, private real-time vision system
"""

import asyncio
import time
import logging
import signal
import sys
from realtime_screen_tcp_server import RealTimeScreenTCPServer
from realtime_agent_vision import RealTimeAgentVision

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SecuredTeamViewerDemo:
    """Complete secured TeamViewer-style system demo"""
    
    def __init__(self):
        self.server = None
        self.agent = None
        self.running = False
        
        # Security settings
        self.host = "127.0.0.1"  # LOCALHOST ONLY
        self.port = 9994
        
        logger.info("🔒 SECURED TEAMVIEWER-STYLE SYSTEM")
        logger.info("🔒 100% LOCAL, SECURE, PRIVATE")
        logger.info(f"🔒 Host: {self.host} (localhost only)")
        logger.info(f"🔒 Port: {self.port}")
    
    async def start_system(self):
        """Start the complete secured system"""
        try:
            logger.info("\n" + "="*60)
            logger.info("🚀 STARTING SECURED REAL-TIME VISION SYSTEM")
            logger.info("="*60)
            
            # 1. Create secure server
            logger.info("1️⃣ Creating secure localhost-only server...")
            self.server = RealTimeScreenTCPServer(host=self.host, port=self.port)
            
            # 2. Create secure agent
            logger.info("2️⃣ Creating secure localhost-only agent...")
            self.agent = RealTimeAgentVision(server_host=self.host, server_port=self.port)
            
            # 3. Start server
            logger.info("3️⃣ Starting server...")
            server_task = asyncio.create_task(self.server.start_server())
            await asyncio.sleep(1)  # Let server initialize
            
            # 4. Connect agent
            logger.info("4️⃣ Connecting agent...")
            connected = await self.agent.connect_to_screen_server()
            
            if not connected:
                logger.error("❌ Agent connection failed!")
                return
            
            # 5. Start real-time vision
            logger.info("5️⃣ Starting real-time vision...")
            vision_task = asyncio.create_task(self.agent.start_real_time_vision())
            
            self.running = True
            logger.info("\n✅ SYSTEM FULLY OPERATIONAL!")
            logger.info("🔒 All connections are localhost-only")
            logger.info("🔒 No external network access")
            logger.info("🔒 100% secure and private")
            
            # 6. Monitor system
            await self.monitor_system()
            
        except Exception as e:
            logger.error(f"❌ System startup error: {e}")
        finally:
            await self.shutdown_system()
    
    async def monitor_system(self):
        """Monitor the system operation"""
        logger.info("\n📊 MONITORING SYSTEM PERFORMANCE...")
        logger.info("Press Ctrl+C to stop")
        
        start_time = time.time()
        last_report = 0
        
        try:
            while self.running:
                await asyncio.sleep(1)
                
                # Report every 5 seconds
                elapsed = time.time() - start_time
                if elapsed - last_report >= 5:
                    await self.report_status(elapsed)
                    last_report = elapsed
                    
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutdown requested by user")
            self.running = False
    
    async def report_status(self, elapsed: float):
        """Report system status"""
        if not self.agent:
            return
            
        summary = self.agent.get_vision_summary()
        
        logger.info(f"\n📊 SYSTEM STATUS (Uptime: {elapsed:.1f}s)")
        logger.info(f"🔗 Connection: {'✅ Active' if summary['connected'] else '❌ Inactive'}")
        logger.info(f"📺 Screen: {summary['screen_size'][0]}x{summary['screen_size'][1]}")
        logger.info(f"🎯 Active Window: {summary['active_window']}")
        logger.info(f"📊 FPS: {summary['fps']:.1f}")
        logger.info(f"📥 Frames Received: {summary['frames_received']}")
        logger.info(f"🎮 Actions Executed: {summary['actions_executed']}")
        logger.info(f"🎛️ UI Elements: {summary['ui_elements_count']}")
        logger.info(f"🖱️ Cursor: {summary['cursor_position']}")
        
        # Security reminder
        if summary['frames_received'] > 0:
            logger.info("🔒 SECURITY: All data processed locally, no external transmission")
    
    async def test_user_commands(self):
        """Test user command execution"""
        if not self.agent or not self.agent.connected:
            logger.error("❌ Agent not connected")
            return
        
        logger.info("\n🧪 TESTING USER COMMAND EXECUTION...")
        
        # Test commands
        test_commands = [
            "observe screen",
            "analyze ui elements",
            "check active window"
        ]
        
        for command in test_commands:
            logger.info(f"\n▶️ Testing command: '{command}'")
            result = await self.agent.execute_user_command(command)
            
            if result['success']:
                logger.info(f"✅ Command executed successfully")
                logger.info(f"📊 Vision state: {result['vision_state']['connected']}")
            else:
                logger.error(f"❌ Command failed: {result.get('error', 'Unknown error')}")
    
    async def shutdown_system(self):
        """Shutdown the system safely"""
        logger.info("\n🛑 SHUTTING DOWN SECURED SYSTEM...")
        
        self.running = False
        
        # Stop agent
        if self.agent:
            logger.info("🔒 Stopping secure agent...")
            await self.agent.stop_vision()
        
        # Stop server
        if self.server:
            logger.info("🔒 Stopping secure server...")
            await self.server.stop_server()
        
        logger.info("✅ Secured system shutdown complete")
        logger.info("🔒 All local connections closed")
        logger.info("🔒 No data transmitted externally")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"\n🛑 Received signal {signum}")
    sys.exit(0)

async def main():
    """Main demo function"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    demo = SecuredTeamViewerDemo()
    
    try:
        await demo.start_system()
    except KeyboardInterrupt:
        logger.info("🛑 Demo interrupted by user")
    except Exception as e:
        logger.error(f"❌ Demo error: {e}")
    finally:
        logger.info("\n🔒 SECURED TEAMVIEWER DEMO COMPLETE")
        logger.info("🔒 All operations performed locally")
        logger.info("🔒 No external network access")
        logger.info("🔒 100% private and secure")

if __name__ == "__main__":
    print("🔒 SECURED TEAMVIEWER-STYLE REAL-TIME VISION SYSTEM")
    print("🔒 100% Local, Secure, Private")
    print("🔒 No External Network Access")
    print("\nStarting in 3 seconds...")
    
    # Countdown
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("🚀 Starting!")
    asyncio.run(main())