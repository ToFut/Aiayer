#!/usr/bin/env python3
"""
Application Integration Framework
Hook directly into applications for efficient monitoring and control
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional, Protocol
from dataclasses import dataclass, asdict
from enum import Enum
import sys
import subprocess
import psutil

# Application-specific integrations
try:
    import selenium
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    BROWSER_INTEGRATION_AVAILABLE = True
except ImportError:
    BROWSER_INTEGRATION_AVAILABLE = False

try:
    import applescript
    APPLESCRIPT_AVAILABLE = True
except ImportError:
    APPLESCRIPT_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ApplicationType(Enum):
    BROWSER = "browser"
    TERMINAL = "terminal"
    TEXT_EDITOR = "text_editor"
    IDE = "ide"
    OFFICE = "office"
    MEDIA_PLAYER = "media_player"
    COMMUNICATION = "communication"
    SYSTEM = "system"
    UNKNOWN = "unknown"

@dataclass
class ApplicationState:
    """Current state of an application"""
    app_name: str
    app_type: ApplicationType
    pid: int
    window_title: str
    is_active: bool
    current_document: Optional[str]
    cursor_position: Optional[Dict[str, int]]
    selected_text: Optional[str]
    available_actions: List[str]
    custom_properties: Dict[str, Any]
    timestamp: float

class ApplicationIntegrator(Protocol):
    """Protocol for application-specific integrators"""
    
    async def can_integrate(self, app_name: str, pid: int) -> bool:
        """Check if this integrator can handle the application"""
        ...
    
    async def get_application_state(self) -> ApplicationState:
        """Get current application state"""
        ...
    
    async def execute_action(self, action: str, parameters: Dict[str, Any]) -> bool:
        """Execute action in the application"""
        ...

class BrowserIntegrator:
    """Integration with web browsers using WebDriver and DOM APIs"""
    
    def __init__(self):
        self.driver = None
        self.app_name = ""
        self.browser_type = ""
        
    async def can_integrate(self, app_name: str, pid: int) -> bool:
        """Check if app is a supported browser"""
        browser_names = [
            "chrome", "firefox", "safari", "edge", 
            "chromium", "brave", "opera"
        ]
        return any(browser in app_name.lower() for browser in browser_names)
    
    async def initialize(self, app_name: str, pid: int) -> bool:
        """Initialize browser integration"""
        if not BROWSER_INTEGRATION_AVAILABLE:
            return False
        
        self.app_name = app_name
        
        try:
            # Try to connect to existing browser instance
            if "chrome" in app_name.lower() or "chromium" in app_name.lower():
                options = webdriver.ChromeOptions()
                options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
                self.driver = webdriver.Chrome(options=options)
                self.browser_type = "chrome"
            elif "firefox" in app_name.lower():
                # Firefox remote debugging setup
                profile = webdriver.FirefoxProfile()
                profile.set_preference("devtools.debugger.remote-enabled", True)
                self.driver = webdriver.Firefox(firefox_profile=profile)
                self.browser_type = "firefox"
            elif "safari" in app_name.lower():
                # Safari requires enabling Develop menu
                self.driver = webdriver.Safari()
                self.browser_type = "safari"
            
            if self.driver:
                logger.info(f"✅ Browser integration active: {self.browser_type}")
                return True
            
        except Exception as e:
            logger.warning(f"Browser integration failed: {e}")
            
        return False
    
    async def get_application_state(self) -> ApplicationState:
        """Get browser state via DOM APIs"""
        if not self.driver:
            return self._create_empty_state()
        
        try:
            # Get current page info
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            # Get visible elements
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            links = self.driver.find_elements(By.TAG_NAME, "a")
            
            # Get page structure
            page_structure = self._analyze_page_structure()
            
            # Get current focus
            active_element = self.driver.switch_to.active_element
            
            available_actions = [
                "navigate", "click_element", "fill_input", 
                "scroll", "take_screenshot", "execute_script"
            ]
            
            return ApplicationState(
                app_name=self.app_name,
                app_type=ApplicationType.BROWSER,
                pid=0,  # We don't track PID for WebDriver
                window_title=page_title,
                is_active=True,
                current_document=current_url,
                cursor_position=None,
                selected_text=self._get_selected_text(),
                available_actions=available_actions,
                custom_properties={
                    'url': current_url,
                    'buttons_count': len(buttons),
                    'inputs_count': len(inputs),
                    'links_count': len(links),
                    'page_structure': page_structure,
                    'active_element_tag': active_element.tag_name if active_element else None
                },
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error getting browser state: {e}")
            return self._create_empty_state()
    
    def _analyze_page_structure(self) -> Dict[str, Any]:
        """Analyze page structure for better understanding"""
        try:
            # Get semantic elements
            nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
            main_elements = self.driver.find_elements(By.TAG_NAME, "main")
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            
            # Get interactive elements
            clickable_elements = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "button, a, input[type='submit'], input[type='button'], [onclick]"
            )
            
            return {
                'navigation_sections': len(nav_elements),
                'main_content_areas': len(main_elements),
                'forms': len(forms),
                'clickable_elements': len(clickable_elements),
                'has_search_box': len(self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    "input[type='search'], input[placeholder*='search' i]"
                )) > 0
            }
            
        except Exception as e:
            logger.error(f"Error analyzing page structure: {e}")
            return {}
    
    def _get_selected_text(self) -> Optional[str]:
        """Get currently selected text"""
        try:
            return self.driver.execute_script("return window.getSelection().toString();")
        except:
            return None
    
    async def execute_action(self, action: str, parameters: Dict[str, Any]) -> bool:
        """Execute action in browser"""
        if not self.driver:
            return False
        
        try:
            if action == "navigate":
                url = parameters.get("url")
                if url:
                    self.driver.get(url)
                    return True
            
            elif action == "click_element":
                selector = parameters.get("selector")
                text = parameters.get("text")
                
                if selector:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    element.click()
                    return True
                elif text:
                    # Find element by text
                    element = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
                    element.click()
                    return True
            
            elif action == "fill_input":
                selector = parameters.get("selector")
                value = parameters.get("value")
                
                if selector and value:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    element.clear()
                    element.send_keys(value)
                    return True
            
            elif action == "scroll":
                direction = parameters.get("direction", "down")
                amount = parameters.get("amount", 500)
                
                if direction == "down":
                    self.driver.execute_script(f"window.scrollBy(0, {amount});")
                elif direction == "up":
                    self.driver.execute_script(f"window.scrollBy(0, -{amount});")
                
                return True
            
            elif action == "execute_script":
                script = parameters.get("script")
                if script:
                    result = self.driver.execute_script(script)
                    return True
            
        except Exception as e:
            logger.error(f"Error executing browser action {action}: {e}")
            
        return False
    
    def _create_empty_state(self) -> ApplicationState:
        """Create empty application state"""
        return ApplicationState(
            app_name=self.app_name,
            app_type=ApplicationType.BROWSER,
            pid=0,
            window_title="",
            is_active=False,
            current_document=None,
            cursor_position=None,
            selected_text=None,
            available_actions=[],
            custom_properties={},
            timestamp=time.time()
        )

class TerminalIntegrator:
    """Integration with terminal applications"""
    
    def __init__(self):
        self.app_name = ""
        self.pid = 0
        
    async def can_integrate(self, app_name: str, pid: int) -> bool:
        """Check if app is a terminal"""
        terminal_names = [
            "terminal", "iterm", "kitty", "alacritty", 
            "gnome-terminal", "konsole", "xterm"
        ]
        return any(term in app_name.lower() for term in terminal_names)
    
    async def initialize(self, app_name: str, pid: int) -> bool:
        """Initialize terminal integration"""
        self.app_name = app_name
        self.pid = pid
        return True
    
    async def get_application_state(self) -> ApplicationState:
        """Get terminal state"""
        try:
            # For macOS Terminal, we can use AppleScript
            if sys.platform == "darwin" and APPLESCRIPT_AVAILABLE:
                current_dir = await self._get_terminal_current_dir()
                last_command = await self._get_terminal_last_command()
            else:
                current_dir = None
                last_command = None
            
            available_actions = [
                "execute_command", "send_keys", "clear_screen",
                "change_directory", "get_output"
            ]
            
            return ApplicationState(
                app_name=self.app_name,
                app_type=ApplicationType.TERMINAL,
                pid=self.pid,
                window_title="Terminal",
                is_active=True,
                current_document=current_dir,
                cursor_position=None,
                selected_text=None,
                available_actions=available_actions,
                custom_properties={
                    'current_directory': current_dir,
                    'last_command': last_command,
                    'shell_type': self._detect_shell_type()
                },
                timestamp=time.time()
            )
            
        except Exception as e:
            logger.error(f"Error getting terminal state: {e}")
            return self._create_empty_terminal_state()
    
    async def _get_terminal_current_dir(self) -> Optional[str]:
        """Get current directory in terminal (macOS)"""
        if not APPLESCRIPT_AVAILABLE:
            return None
        
        try:
            script = '''
            tell application "Terminal"
                do shell script "pwd" in front window
            end tell
            '''
            result = applescript.run(script)
            return result.out.strip() if result.out else None
        except:
            return None
    
    async def _get_terminal_last_command(self) -> Optional[str]:
        """Get last executed command (macOS)"""
        if not APPLESCRIPT_AVAILABLE:
            return None
        
        try:
            script = '''
            tell application "Terminal"
                get history of front window
            end tell
            '''
            result = applescript.run(script)
            if result.out:
                lines = result.out.strip().split('\n')
                return lines[-1] if lines else None
        except:
            return None
    
    def _detect_shell_type(self) -> str:
        """Detect shell type"""
        try:
            shell = subprocess.check_output(['echo', '$SHELL'], text=True).strip()
            return shell.split('/')[-1] if shell else "unknown"
        except:
            return "unknown"
    
    async def execute_action(self, action: str, parameters: Dict[str, Any]) -> bool:
        """Execute terminal action"""
        if sys.platform == "darwin" and APPLESCRIPT_AVAILABLE:
            return await self._execute_macos_terminal_action(action, parameters)
        else:
            return await self._execute_generic_terminal_action(action, parameters)
    
    async def _execute_macos_terminal_action(self, action: str, parameters: Dict[str, Any]) -> bool:
        """Execute terminal action on macOS using AppleScript"""
        try:
            if action == "execute_command":
                command = parameters.get("command")
                if command:
                    script = f'''
                    tell application "Terminal"
                        do script "{command}" in front window
                    end tell
                    '''
                    applescript.run(script)
                    return True
            
            elif action == "send_keys":
                keys = parameters.get("keys")
                if keys:
                    script = f'''
                    tell application "Terminal"
                        keystroke "{keys}"
                    end tell
                    '''
                    applescript.run(script)
                    return True
            
            elif action == "clear_screen":
                script = '''
                tell application "Terminal"
                    do script "clear" in front window
                end tell
                '''
                applescript.run(script)
                return True
            
        except Exception as e:
            logger.error(f"Error executing macOS terminal action: {e}")
            
        return False
    
    async def _execute_generic_terminal_action(self, action: str, parameters: Dict[str, Any]) -> bool:
        """Generic terminal action execution"""
        # Placeholder for generic terminal integration
        # Could use tools like expect, pexpect, or direct process communication
        return False
    
    def _create_empty_terminal_state(self) -> ApplicationState:
        """Create empty terminal state"""
        return ApplicationState(
            app_name=self.app_name,
            app_type=ApplicationType.TERMINAL,
            pid=self.pid,
            window_title="Terminal",
            is_active=False,
            current_document=None,
            cursor_position=None,
            selected_text=None,
            available_actions=[],
            custom_properties={},
            timestamp=time.time()
        )

class ApplicationIntegrationFramework:
    """Main framework for application integration"""
    
    def __init__(self):
        self.integrators: List[ApplicationIntegrator] = []
        self.active_integrations: Dict[int, ApplicationIntegrator] = {}
        self.application_states: Dict[int, ApplicationState] = {}
        
        # Register built-in integrators
        self._register_integrators()
    
    def _register_integrators(self):
        """Register available application integrators"""
        self.integrators = [
            BrowserIntegrator(),
            TerminalIntegrator()
            # Add more integrators here
        ]
        
        logger.info(f"📱 Registered {len(self.integrators)} application integrators")
    
    async def detect_and_integrate_applications(self) -> List[ApplicationState]:
        """Detect running applications and integrate with them"""
        application_states = []
        
        try:
            # Get running processes
            for process in psutil.process_iter(['pid', 'name']):
                try:
                    pid = process.info['pid']
                    name = process.info['name']
                    
                    # Skip system processes
                    if self._is_system_process(name):
                        continue
                    
                    # Check if we already have an integration
                    if pid in self.active_integrations:
                        state = await self.active_integrations[pid].get_application_state()
                        application_states.append(state)
                        continue
                    
                    # Try to integrate with available integrators
                    for integrator in self.integrators:
                        if await integrator.can_integrate(name, pid):
                            if hasattr(integrator, 'initialize'):
                                success = await integrator.initialize(name, pid)
                                if success:
                                    self.active_integrations[pid] = integrator
                                    state = await integrator.get_application_state()
                                    application_states.append(state)
                                    logger.info(f"✅ Integrated with {name} (PID: {pid})")
                                    break
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                except Exception as e:
                    logger.error(f"Error processing {name}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error detecting applications: {e}")
        
        return application_states
    
    def _is_system_process(self, name: str) -> bool:
        """Check if process is a system process to skip"""
        system_processes = [
            "kernel", "launchd", "kextd", "syslogd", "mds",
            "windowserver", "loginwindow", "dock", "finder",
            "spotlight", "coreaudio", "bluetooth"
        ]
        
        return any(sys_proc in name.lower() for sys_proc in system_processes)
    
    async def execute_application_action(self, pid: int, action: str, 
                                       parameters: Dict[str, Any]) -> bool:
        """Execute action in specific application"""
        if pid not in self.active_integrations:
            logger.warning(f"No integration for PID {pid}")
            return False
        
        integrator = self.active_integrations[pid]
        return await integrator.execute_action(action, parameters)
    
    async def get_application_by_name(self, app_name: str) -> Optional[ApplicationState]:
        """Get application state by name"""
        states = await self.detect_and_integrate_applications()
        
        for state in states:
            if app_name.lower() in state.app_name.lower():
                return state
        
        return None
    
    async def get_browsers(self) -> List[ApplicationState]:
        """Get all browser applications"""
        states = await self.detect_and_integrate_applications()
        return [state for state in states if state.app_type == ApplicationType.BROWSER]
    
    async def get_terminals(self) -> List[ApplicationState]:
        """Get all terminal applications"""
        states = await self.detect_and_integrate_applications()
        return [state for state in states if state.app_type == ApplicationType.TERMINAL]
    
    def cleanup_integrations(self):
        """Clean up integrations for terminated processes"""
        dead_pids = []
        
        for pid in self.active_integrations.keys():
            try:
                process = psutil.Process(pid)
                if not process.is_running():
                    dead_pids.append(pid)
            except psutil.NoSuchProcess:
                dead_pids.append(pid)
        
        for pid in dead_pids:
            del self.active_integrations[pid]
            if pid in self.application_states:
                del self.application_states[pid]
        
        if dead_pids:
            logger.info(f"🧹 Cleaned up {len(dead_pids)} terminated integrations")

# Example usage
async def main():
    """Test application integration framework"""
    framework = ApplicationIntegrationFramework()
    
    logger.info("🔍 Detecting and integrating with applications...")
    
    # Detect applications
    applications = await framework.detect_and_integrate_applications()
    
    logger.info(f"📱 Found {len(applications)} integrated applications:")
    for app in applications:
        logger.info(f"  {app.app_name} ({app.app_type.value}) - {len(app.available_actions)} actions")
    
    # Test browser integration
    browsers = await framework.get_browsers()
    if browsers:
        logger.info(f"🌐 Found {len(browsers)} browsers")
        browser = browsers[0]
        
        # Example: Navigate to a URL
        success = await framework.execute_application_action(
            browser.pid,
            "navigate",
            {"url": "https://www.example.com"}
        )
        
        if success:
            logger.info("✅ Successfully navigated browser")
    
    # Test terminal integration
    terminals = await framework.get_terminals()
    if terminals:
        logger.info(f"💻 Found {len(terminals)} terminals")

if __name__ == "__main__":
    asyncio.run(main())