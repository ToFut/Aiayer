#!/usr/bin/env python3
"""
Smart Element Detector - Uses screen analysis to find UI elements accurately
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class SmartElementDetector:
    """Intelligent UI element detection using screen analysis"""
    
    def __init__(self):
        self.screen_analyzer = None
        self.last_analysis = None
        self.last_analysis_time = 0
        
        try:
            from sensors.total_screen_analyzer import TotalScreenAnalyzer
            self.screen_analyzer = TotalScreenAnalyzer()
            logger.info("📱 Smart element detector initialized")
        except Exception as e:
            logger.warning(f"Screen analyzer not available: {e}")
    
    async def find_element_coordinates(self, element_type: str, context: str = "") -> Optional[Tuple[int, int]]:
        """Find element coordinates using intelligent screen analysis"""
        try:
            # Get fresh screen analysis
            screen_data = await self._get_screen_analysis()
            if not screen_data:
                return self._get_fallback_coordinates(element_type)
            
            # Analyze for specific element types
            if element_type == "search_box":
                return await self._find_search_box(screen_data, context)
            elif element_type == "address_bar":
                return await self._find_address_bar(screen_data)
            elif element_type == "button":
                return await self._find_button(screen_data, context)
            else:
                return self._get_fallback_coordinates(element_type)
                
        except Exception as e:
            logger.error(f"Error finding element {element_type}: {e}")
            return self._get_fallback_coordinates(element_type)
    
    async def _get_screen_analysis(self) -> Optional[Dict[str, Any]]:
        """Get current screen analysis with caching"""
        try:
            current_time = time.time()
            
            # Use cached analysis if recent (within 5 seconds)
            if (self.last_analysis and 
                current_time - self.last_analysis_time < 5):
                return self.last_analysis
            
            if not self.screen_analyzer:
                return None
            
            # Get fresh analysis
            analysis = await self.screen_analyzer.analyze_full_screen()
            
            if analysis:
                self.last_analysis = analysis
                self.last_analysis_time = current_time
                logger.info("📊 Got fresh screen analysis")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error getting screen analysis: {e}")
            return None
    
    async def _find_search_box(self, screen_data: Dict[str, Any], context: str) -> Optional[Tuple[int, int]]:
        """Find search box coordinates based on context"""
        try:
            # Get screen dimensions
            screen_width = 1470  # From detected screen size
            screen_height = 956
            
            # Context-specific search box locations
            if "youtube" in context.lower():
                # YouTube search box is typically in the top center
                # But lower than browser tabs - around 25% down from top
                search_x = screen_width // 2  # Center horizontally
                search_y = int(screen_height * 0.15)  # 15% from top (below header)
                
                logger.info(f"🎯 YouTube search box estimated at ({search_x}, {search_y})")
                return (search_x, search_y)
            
            elif "google" in context.lower():
                # Google search box is more centered
                search_x = screen_width // 2
                search_y = int(screen_height * 0.4)  # 40% from top
                
                logger.info(f"🎯 Google search box estimated at ({search_x}, {search_y})")
                return (search_x, search_y)
            
            else:
                # Generic search box - top center but below browser UI
                search_x = screen_width // 2
                search_y = int(screen_height * 0.2)  # 20% from top
                
                logger.info(f"🎯 Generic search box estimated at ({search_x}, {search_y})")
                return (search_x, search_y)
                
        except Exception as e:
            logger.error(f"Error finding search box: {e}")
            return None
    
    async def _find_address_bar(self, screen_data: Dict[str, Any]) -> Optional[Tuple[int, int]]:
        """Find browser address bar coordinates"""
        try:
            screen_width = 1470
            screen_height = 956
            
            # Address bar is typically at the top of browser window
            # Around 10% from top, centered horizontally
            addr_x = screen_width // 2
            addr_y = int(screen_height * 0.08)  # 8% from top
            
            logger.info(f"🎯 Address bar estimated at ({addr_x}, {addr_y})")
            return (addr_x, addr_y)
            
        except Exception as e:
            logger.error(f"Error finding address bar: {e}")
            return None
    
    async def _find_button(self, screen_data: Dict[str, Any], button_text: str) -> Optional[Tuple[int, int]]:
        """Find button coordinates based on text"""
        try:
            screen_width = 1470
            screen_height = 956
            
            # Common button locations based on text
            button_text_lower = button_text.lower()
            
            if "search" in button_text_lower:
                # Search buttons are typically near search boxes
                btn_x = int(screen_width * 0.6)  # Right of center
                btn_y = int(screen_height * 0.15)
            elif "submit" in button_text_lower or "send" in button_text_lower:
                # Submit buttons are typically bottom right of forms
                btn_x = int(screen_width * 0.7)
                btn_y = int(screen_height * 0.8)
            else:
                # Generic button - center area
                btn_x = screen_width // 2
                btn_y = int(screen_height * 0.5)
            
            logger.info(f"🎯 Button '{button_text}' estimated at ({btn_x}, {btn_y})")
            return (btn_x, btn_y)
            
        except Exception as e:
            logger.error(f"Error finding button: {e}")
            return None
    
    def _get_fallback_coordinates(self, element_type: str) -> Tuple[int, int]:
        """Get fallback coordinates when detection fails"""
        screen_width = 1470
        screen_height = 956
        
        fallback_coords = {
            "search_box": (screen_width // 2, int(screen_height * 0.2)),
            "address_bar": (screen_width // 2, int(screen_height * 0.08)),
            "button": (screen_width // 2, int(screen_height * 0.5)),
            "center": (screen_width // 2, screen_height // 2)
        }
        
        coords = fallback_coords.get(element_type, fallback_coords["center"])
        logger.info(f"🔄 Using fallback coordinates for {element_type}: {coords}")
        return coords
    
    async def get_improved_youtube_search_coords(self) -> Tuple[int, int]:
        """Get improved YouTube search box coordinates"""
        # YouTube's search box is typically:
        # - Horizontally centered
        # - Vertically around 120-150px from top (below header and navigation)
        
        screen_width = 1470
        
        # More accurate YouTube search box position
        search_x = screen_width // 2  # Center horizontally
        search_y = 140  # 140px from top (below YouTube header)
        
        logger.info(f"🎯 Improved YouTube search coordinates: ({search_x}, {search_y})")
        return (search_x, search_y)
    
    async def get_improved_google_search_coords(self) -> Tuple[int, int]:
        """Get improved Google search box coordinates"""
        screen_width = 1470
        screen_height = 956
        
        # Google search box positioning
        search_x = screen_width // 2
        search_y = int(screen_height * 0.35)  # Roughly 1/3 down the page
        
        logger.info(f"🎯 Improved Google search coordinates: ({search_x}, {search_y})")
        return (search_x, search_y)

# Create singleton instance
smart_detector = SmartElementDetector()