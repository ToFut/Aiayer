#!/usr/bin/env python3
"""
Browser API Integration Module
Provides direct access to browser DOM elements and native browser APIs
"""

import os
import json
import time
import logging
import asyncio
import subprocess
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import platform

# Browser automation imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.safari.options import Options as SafariOptions
    from selenium.webdriver.edge.options import Options as EdgeOptions
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# CDP (Chrome DevTools Protocol) for direct browser API access
try:
    import websocket
    import requests
    CDP_AVAILABLE = True
except ImportError:
    CDP_AVAILABLE = False

# Platform-specific browser control
try:
    if platform.system() == "Darwin":  # macOS
        from AppKit import NSWorkspace, NSRunningApplication
        MACOS_AVAILABLE = True
    else:
        MACOS_AVAILABLE = False
except ImportError:
    MACOS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class BrowserElement:
    """Represents a browser DOM element with native API access"""
    element_id: str
    tag_name: str
    element_type: str
    text_content: str
    inner_html: str
    attributes: Dict[str, str]
    computed_styles: Dict[str, str]
    bounding_rect: Dict[str, float]
    xpath: str
    css_selector: str
    is_visible: bool
    is_clickable: bool
    parent_element_id: str = ""
    children_count: int = 0

class BrowserAPIManager:
    """Manages browser connections and API interactions"""
    
    def __init__(self):
        self.selenium_available = SELENIUM_AVAILABLE
        self.cdp_available = CDP_AVAILABLE
        self.driver = None
        self.cdp_session = None
        self.browser_type = None
        self.debug_port = 9222
        
        logger.info(f"Browser API Manager initialized - Selenium: {self.selenium_available}, CDP: {self.cdp_available}")
    
    def detect_running_browsers(self) -> List[Dict[str, Any]]:
        """Detect currently running browsers and their details"""
        browsers = []
        
        try:
            if MACOS_AVAILABLE:
                browsers.extend(self._detect_macos_browsers())
            elif platform.system() == "Windows":
                browsers.extend(self._detect_windows_browsers())
            elif platform.system() == "Linux":
                browsers.extend(self._detect_linux_browsers())
                
        except Exception as e:
            logger.error(f"Error detecting browsers: {e}")
        
        return browsers
    
    def _detect_macos_browsers(self) -> List[Dict[str, Any]]:
        """Detect running browsers on macOS"""
        browsers = []
        
        try:
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()
            
            browser_apps = {
                "com.google.Chrome": "Chrome",
                "com.apple.Safari": "Safari",
                "org.mozilla.firefox": "Firefox",
                "com.microsoft.edgemac": "Edge",
                "com.operasoftware.Opera": "Opera"
            }
            
            for app in running_apps:
                bundle_id = app.bundleIdentifier()
                if bundle_id in browser_apps:
                    browsers.append({
                        "name": browser_apps[bundle_id],
                        "bundle_id": bundle_id,
                        "pid": app.processIdentifier(),
                        "is_active": app.isActive(),
                        "is_frontmost": app.isActive()
                    })
                    
        except Exception as e:
            logger.error(f"Error detecting macOS browsers: {e}")
        
        return browsers
    
    def _detect_windows_browsers(self) -> List[Dict[str, Any]]:
        """Detect running browsers on Windows"""
        try:
            import psutil
            browsers = []
            
            browser_processes = {
                "chrome.exe": "Chrome",
                "firefox.exe": "Firefox", 
                "msedge.exe": "Edge",
                "safari.exe": "Safari",
                "opera.exe": "Opera"
            }
            
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name']
                    if proc_name in browser_processes:
                        browsers.append({
                            "name": browser_processes[proc_name],
                            "process_name": proc_name,
                            "pid": proc.info['pid']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            return browsers
            
        except ImportError:
            logger.warning("psutil not available for Windows browser detection")
            return []
    
    def _detect_linux_browsers(self) -> List[Dict[str, Any]]:
        """Detect running browsers on Linux"""
        try:
            import psutil
            browsers = []
            
            browser_processes = {
                "google-chrome": "Chrome",
                "chromium": "Chromium",
                "firefox": "Firefox",
                "opera": "Opera"
            }
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    proc_name = proc.info['name']
                    if proc_name in browser_processes:
                        browsers.append({
                            "name": browser_processes[proc_name],
                            "process_name": proc_name,
                            "pid": proc.info['pid']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
            return browsers
            
        except ImportError:
            logger.warning("psutil not available for Linux browser detection")
            return []
    
    def connect_to_browser(self, browser_name: str = "chrome", debug_port: int = 9222) -> bool:
        """Connect to a running browser instance"""
        try:
            self.debug_port = debug_port
            
            # First try to connect to existing browser with debugging enabled
            if self._connect_to_existing_browser(browser_name, debug_port):
                return True
            
            # If that fails, start a new browser instance with debugging
            return self._start_browser_with_debugging(browser_name, debug_port)
            
        except Exception as e:
            logger.error(f"Error connecting to browser: {e}")
            return False
    
    def _connect_to_existing_browser(self, browser_name: str, debug_port: int) -> bool:
        """Try to connect to existing browser with debugging enabled"""
        try:
            if not self.selenium_available:
                return False
            
            if browser_name.lower() == "chrome":
                options = ChromeOptions()
                options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
                self.driver = webdriver.Chrome(options=options)
            elif browser_name.lower() == "firefox":
                # Firefox doesn't support remote debugging in the same way
                return False
            elif browser_name.lower() == "safari":
                # Safari has limited remote debugging support
                options = SafariOptions()
                self.driver = webdriver.Safari(options=options)
            
            if self.driver:
                self.browser_type = browser_name.lower()
                logger.info(f"Connected to existing {browser_name} instance")
                return True
                
        except Exception as e:
            logger.debug(f"Could not connect to existing browser: {e}")
        
        return False
    
    def _start_browser_with_debugging(self, browser_name: str, debug_port: int) -> bool:
        """Start new browser instance with debugging enabled"""
        try:
            if not self.selenium_available:
                return False
            
            if browser_name.lower() == "chrome":
                options = ChromeOptions()
                options.add_argument(f"--remote-debugging-port={debug_port}")
                options.add_argument("--disable-web-security")
                options.add_argument("--disable-features=VizDisplayCompositor")
                self.driver = webdriver.Chrome(options=options)
            elif browser_name.lower() == "firefox":
                options = FirefoxOptions()
                # Firefox debugging setup
                self.driver = webdriver.Firefox(options=options)
            elif browser_name.lower() == "safari":
                options = SafariOptions()
                self.driver = webdriver.Safari(options=options)
            elif browser_name.lower() == "edge":
                options = EdgeOptions()
                options.add_argument(f"--remote-debugging-port={debug_port}")
                self.driver = webdriver.Edge(options=options)
            
            if self.driver:
                self.browser_type = browser_name.lower()
                logger.info(f"Started new {browser_name} instance with debugging")
                return True
                
        except Exception as e:
            logger.error(f"Failed to start browser with debugging: {e}")
        
        return False
    
    def get_native_dom_elements(self) -> List[BrowserElement]:
        """Get DOM elements using native browser APIs"""
        if not self.driver:
            return []
        
        try:
            elements = []
            
            # Get all interactive elements
            interactive_selectors = [
                "button",
                "input", 
                "textarea",
                "select",
                "a[href]",
                "[onclick]",
                "[role='button']",
                "[role='link']",
                "[role='textbox']",
                "[tabindex]"
            ]
            
            for selector in interactive_selectors:
                web_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for i, elem in enumerate(web_elements):
                    try:
                        browser_elem = self._convert_to_browser_element(elem, f"{selector}_{i}")
                        if browser_elem:
                            elements.append(browser_elem)
                    except Exception as e:
                        logger.debug(f"Error processing element {selector}_{i}: {e}")
            
            logger.info(f"Retrieved {len(elements)} native DOM elements")
            return elements
            
        except Exception as e:
            logger.error(f"Error getting native DOM elements: {e}")
            return []
    
    def _convert_to_browser_element(self, web_element, element_id: str) -> Optional[BrowserElement]:
        """Convert Selenium WebElement to BrowserElement"""
        try:
            # Get basic properties
            tag_name = web_element.tag_name.lower()
            element_type = self._determine_element_type(web_element)
            text_content = web_element.text or ""
            
            # Get attributes
            attributes = {}
            common_attrs = ["id", "class", "name", "type", "placeholder", "value", "href", "role", "aria-label"]
            for attr in common_attrs:
                value = web_element.get_attribute(attr)
                if value:
                    attributes[attr] = value
            
            # Get computed styles (limited in Selenium)
            computed_styles = {}
            style_properties = ["display", "visibility", "opacity", "position", "z-index"]
            for prop in style_properties:
                try:
                    value = web_element.value_of_css_property(prop)
                    computed_styles[prop] = value
                except:
                    pass
            
            # Get bounding rectangle
            location = web_element.location
            size = web_element.size
            bounding_rect = {
                "x": location["x"],
                "y": location["y"], 
                "width": size["width"],
                "height": size["height"],
                "top": location["y"],
                "left": location["x"],
                "bottom": location["y"] + size["height"],
                "right": location["x"] + size["width"]
            }
            
            # Generate XPath and CSS selector
            xpath = self._generate_xpath(web_element)
            css_selector = self._generate_css_selector(web_element)
            
            # Check visibility and clickability
            is_visible = web_element.is_displayed()
            is_clickable = web_element.is_enabled() and is_visible
            
            # Get inner HTML (if possible)
            inner_html = ""
            try:
                inner_html = web_element.get_attribute("innerHTML") or ""
            except:
                pass
            
            return BrowserElement(
                element_id=element_id,
                tag_name=tag_name,
                element_type=element_type,
                text_content=text_content,
                inner_html=inner_html,
                attributes=attributes,
                computed_styles=computed_styles,
                bounding_rect=bounding_rect,
                xpath=xpath,
                css_selector=css_selector,
                is_visible=is_visible,
                is_clickable=is_clickable,
                children_count=len(web_element.find_elements(By.XPATH, "./*"))
            )
            
        except Exception as e:
            logger.error(f"Error converting WebElement to BrowserElement: {e}")
            return None
    
    def _determine_element_type(self, web_element) -> str:
        """Determine the semantic type of a web element"""
        tag_name = web_element.tag_name.lower()
        element_type = web_element.get_attribute("type")
        role = web_element.get_attribute("role")
        
        # Map based on tag and attributes
        if tag_name == "button" or (tag_name == "input" and element_type == "button"):
            return "button"
        elif tag_name == "input":
            if element_type in ["text", "email", "password", "search", "url", "tel"]:
                return "textfield"
            elif element_type == "checkbox":
                return "checkbox"
            elif element_type == "radio":
                return "radio"
            elif element_type == "submit":
                return "submit_button"
            elif element_type == "file":
                return "file_input"
            else:
                return "input"
        elif tag_name == "textarea":
            return "textarea"
        elif tag_name == "select":
            return "dropdown"
        elif tag_name == "a":
            return "link"
        elif role:
            return role
        else:
            return tag_name
    
    def _generate_xpath(self, web_element) -> str:
        """Generate XPath for the element"""
        try:
            return self.driver.execute_script("""
                function getXPath(element) {
                    if (element.id !== '') {
                        return '//*[@id="' + element.id + '"]';
                    }
                    if (element === document.body) {
                        return '/html/body';
                    }
                    
                    var ix = 0;
                    var siblings = element.parentNode.childNodes;
                    for (var i = 0; i < siblings.length; i++) {
                        var sibling = siblings[i];
                        if (sibling === element) {
                            return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                        }
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                            ix++;
                        }
                    }
                }
                return getXPath(arguments[0]);
            """, web_element)
        except:
            return ""
    
    def _generate_css_selector(self, web_element) -> str:
        """Generate CSS selector for the element"""
        try:
            element_id = web_element.get_attribute("id")
            if element_id:
                return f"#{element_id}"
            
            classes = web_element.get_attribute("class")
            if classes:
                class_selector = "." + ".".join(classes.split())
                return f"{web_element.tag_name.lower()}{class_selector}"
            
            return web_element.tag_name.lower()
        except:
            return ""
    
    def click_element_by_coordinates(self, x: int, y: int) -> bool:
        """Click element at specific coordinates using browser API"""
        try:
            if not self.driver:
                return False
            
            # Use JavaScript to click at coordinates
            self.driver.execute_script(f"""
                var element = document.elementFromPoint({x}, {y});
                if (element) {{
                    element.click();
                }}
            """)
            
            logger.info(f"Clicked at coordinates ({x}, {y})")
            return True
            
        except Exception as e:
            logger.error(f"Error clicking at coordinates: {e}")
            return False
    
    def get_element_at_coordinates(self, x: int, y: int) -> Optional[BrowserElement]:
        """Get DOM element at specific coordinates"""
        try:
            if not self.driver:
                return None
            
            # Use JavaScript to get element at coordinates
            web_element = self.driver.execute_script(f"""
                return document.elementFromPoint({x}, {y});
            """)
            
            if web_element:
                return self._convert_to_browser_element(web_element, f"coord_{x}_{y}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting element at coordinates: {e}")
            return None
    
    def execute_browser_command(self, command: str, **kwargs) -> Any:
        """Execute arbitrary browser command"""
        try:
            if not self.driver:
                return None
            
            if command == "get_page_source":
                return self.driver.page_source
            elif command == "get_current_url":
                return self.driver.current_url
            elif command == "get_title":
                return self.driver.title
            elif command == "screenshot":
                return self.driver.get_screenshot_as_base64()
            elif command == "execute_script":
                script = kwargs.get("script", "")
                return self.driver.execute_script(script)
            elif command == "navigate":
                url = kwargs.get("url", "")
                self.driver.get(url)
                return True
            
            return None
            
        except Exception as e:
            logger.error(f"Error executing browser command {command}: {e}")
            return None
    
    def close_browser(self):
        """Close browser connection"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                logger.info("Browser connection closed")
        except Exception as e:
            logger.error(f"Error closing browser: {e}")

# Chrome DevTools Protocol integration
class CDPIntegration:
    """Direct Chrome DevTools Protocol integration for advanced browser control"""
    
    def __init__(self, debug_port: int = 9222):
        self.debug_port = debug_port
        self.available = CDP_AVAILABLE
        self.session_id = None
        self.websocket_url = None
        
    def connect_to_cdp(self) -> bool:
        """Connect to Chrome DevTools Protocol"""
        try:
            if not self.available:
                return False
            
            # Get list of available tabs
            response = requests.get(f"http://localhost:{self.debug_port}/json")
            tabs = response.json()
            
            if not tabs:
                logger.error("No Chrome tabs available for CDP connection")
                return False
            
            # Use the first available tab
            tab = tabs[0]
            self.websocket_url = tab["webSocketDebuggerUrl"]
            
            logger.info(f"Connected to CDP via {self.websocket_url}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to CDP: {e}")
            return False
    
    def send_cdp_command(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send command via Chrome DevTools Protocol"""
        try:
            if not self.websocket_url:
                return {}
            
            # This would require implementing WebSocket communication
            # For now, return placeholder
            logger.info(f"CDP command: {method}")
            return {"result": "placeholder"}
            
        except Exception as e:
            logger.error(f"Error sending CDP command: {e}")
            return {}

# Create global instances
browser_api_manager = BrowserAPIManager()
cdp_integration = CDPIntegration()

async def main():
    """Test the browser API integration"""
    print("Testing Browser API Integration...")
    
    # Detect running browsers
    browsers = browser_api_manager.detect_running_browsers()
    print(f"Detected browsers: {browsers}")
    
    # Try to connect to a browser
    if browser_api_manager.connect_to_browser("chrome"):
        print("Connected to Chrome successfully")
        
        # Get DOM elements
        elements = browser_api_manager.get_native_dom_elements()
        print(f"Found {len(elements)} DOM elements")
        
        for i, elem in enumerate(elements[:5]):  # Show first 5
            print(f"{i+1}. {elem.element_type}: {elem.text_content[:50]}")
            print(f"   Clickable: {elem.is_clickable}, Visible: {elem.is_visible}")
            print(f"   Bounds: {elem.bounding_rect}")
        
        browser_api_manager.close_browser()
    else:
        print("Could not connect to browser")

if __name__ == "__main__":
    asyncio.run(main())