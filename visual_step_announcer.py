#!/usr/bin/env python3
"""
Visual Step Announcer - Provides clear visual feedback for automation steps
"""

import subprocess
import logging
import asyncio

logger = logging.getLogger(__name__)

class VisualStepAnnouncer:
    """Provides visual and audio feedback for automation steps"""
    
    def __init__(self):
        self.announcement_enabled = True
    
    async def announce_step(self, step_number: int, total_steps: int, description: str):
        """Announce the current step with visual and audio feedback"""
        if not self.announcement_enabled:
            return
        
        try:
            # Create announcement message
            announcement = f"Step {step_number} of {total_steps}: {description}"
            
            # macOS system notification
            subprocess.run([
                'osascript', '-e', 
                f'display notification "{description}" with title "Automation Step {step_number}/{total_steps}" sound name "Glass"'
            ], capture_output=True)
            
            # Optional: Text-to-speech announcement
            # subprocess.run(['say', announcement], capture_output=True)
            
            logger.info(f"📢 ANNOUNCING: {announcement}")
            
        except Exception as e:
            logger.warning(f"Could not announce step: {e}")
    
    async def announce_completion(self, success_rate: float, total_steps: int):
        """Announce automation completion"""
        if not self.announcement_enabled:
            return
        
        try:
            if success_rate == 100:
                message = f"✅ Automation completed successfully! All {total_steps} steps executed."
                sound = "Hero"
            else:
                message = f"⚠️ Automation partially completed. {success_rate:.0f}% success rate."
                sound = "Basso"
            
            subprocess.run([
                'osascript', '-e', 
                f'display notification "{message}" with title "Automation Complete" sound name "{sound}"'
            ], capture_output=True)
            
            logger.info(f"🎉 COMPLETION: {message}")
            
        except Exception as e:
            logger.warning(f"Could not announce completion: {e}")

# Create singleton instance
visual_announcer = VisualStepAnnouncer()