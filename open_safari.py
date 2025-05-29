#!/usr/bin/env python3

import asyncio
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafariLauncher:
    """Simple Safari launcher with automation"""
    
    def __init__(self):
        self.input_controller = None
        self.setup_automation()
    
    def setup_automation(self):
        """Setup automation components"""
        try:
            from agent_workflow.input_controller import InputController
            self.input_controller = InputController(safety_level="medium")
            logger.info("🤖 Input controller ready")
        except Exception as e:
            logger.error(f"Automation not available: {e}")
    
    async def open_safari(self):
        """Open Safari using Spotlight"""
        if not self.input_controller:
            logger.error("❌ Automation not available")
            return False
        
        try:
            print("🌐 Opening Safari...")
            print("=" * 30)
            
            # Step 1: Open Spotlight
            print("📍 Step 1: Opening Spotlight (Cmd+Space)")
            self.input_controller.hotkey("command", "space")
            await asyncio.sleep(1.0)
            
            # Step 2: Type Safari
            print("📝 Step 2: Typing 'Safari'")
            self.input_controller.type_text("Safari")
            await asyncio.sleep(0.5)
            
            # Step 3: Launch Safari
            print("🚀 Step 3: Launching Safari (Enter)")
            self.input_controller.press_key("enter")
            await asyncio.sleep(2.0)
            
            print("✅ Safari launched successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to open Safari: {e}")
            return False

async def main():
    """Main function to open Safari"""
    print("🌐 Safari Launcher")
    print("=" * 20)
    
    launcher = SafariLauncher()
    success = await launcher.open_safari()
    
    if success:
        print("\n🎉 SUCCESS: Safari is now open!")
    else:
        print("\n❌ FAILED: Could not open Safari")
        print("💡 You can manually open Safari from Applications or Dock")

if __name__ == "__main__":
    asyncio.run(main())