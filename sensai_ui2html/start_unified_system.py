#!/usr/bin/env python3
"""
Start Unified System - Runs the complete UI2HTML + Overlay integration
"""

import asyncio
import logging
import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from unified_backend import UnifiedBackend

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('unified_system.log')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to start the unified system"""
    logger.info("🚀 Starting SensAI Unified System")
    logger.info("=" * 50)
    
    try:
        # Initialize unified backend
        backend = UnifiedBackend(host="localhost", port=8767)
        
        # Start the server
        server = await backend.start_server()
        
        logger.info("✅ Unified Backend started successfully")
        logger.info("📡 WebSocket server running on ws://localhost:8767")
        logger.info("🔗 Connect your overlay to ws://localhost:8767")
        logger.info("")
        logger.info("📊 System Status:")
        logger.info("   • UI2HTML Memory System: ✅ Active")
        logger.info("   • Real-time UI Monitoring: ✅ Active")
        logger.info("   • WebSocket Server: ✅ Active")
        logger.info("   • Agent Execution: ✅ Ready")
        logger.info("")
        logger.info("💡 Available Features:")
        logger.info("   • Real-time UI context in chat")
        logger.info("   • Semantic UI memory queries")
        logger.info("   • Agent execution capabilities")
        logger.info("   • UI automation suggestions")
        logger.info("")
        logger.info("🎯 Test the system:")
        logger.info("   1. Open your overlay (Svelte app)")
        logger.info("   2. Connect to ws://localhost:8767")
        logger.info("   3. Ask: 'What's on my screen?'")
        logger.info("   4. Get contextual responses!")
        logger.info("")
        logger.info("Press Ctrl+C to stop the system")
        logger.info("=" * 50)
        
        # Keep the server running
        await asyncio.Future()  # Run forever
        
    except KeyboardInterrupt:
        logger.info("")
        logger.info("🛑 Received shutdown signal")
        logger.info("Shutting down Unified System...")
        
        # Shutdown gracefully
        await backend.shutdown()
        
        logger.info("✅ Unified System shutdown complete")
        
    except Exception as e:
        logger.error(f"❌ Error starting Unified System: {e}")
        logger.error("Please check the logs for details")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1) 