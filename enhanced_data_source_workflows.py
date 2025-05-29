"""
Enhanced Data Source Workflows
Specific automation workflows for different data sources using TeamViewer-style automation.
"""

import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import cv2
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class DataExtractionResult:
    """Result of data extraction from a source."""
    success: bool
    data: List[Dict[str, Any]]
    confidence: float
    extraction_method: str
    timestamp: datetime
    source_type: str
    screenshots: List[np.ndarray] = None
    errors: List[str] = None

class EmailWorkflow:
    """Workflow for accessing and extracting email data."""
    
    def __init__(self, backend_instance):
        self.backend = backend_instance
        self.logger = logging.getLogger(f"{__name__}.EmailWorkflow")
    
    async def execute(self, search_terms: List[str], time_constraints: Dict = None, 
                     websocket=None) -> DataExtractionResult:
        """Execute email data extraction workflow."""
        self.logger.info(f"Executing email workflow with terms: {search_terms}")
        
        try:
            # Step 1: Detect and launch email application
            email_app = await self._detect_email_application()
            if not email_app:
                # Try to launch default email app
                email_app = await self._launch_default_email_app()
            
            # Step 2: Navigate to search interface
            search_activated = await self._activate_email_search()
            if not search_activated:
                return DataExtractionResult(
                    success=False, data=[], confidence=0.0,
                    extraction_method="email_automation",
                    timestamp=datetime.now(),
                    source_type="email",
                    errors=["Failed to activate email search"]
                )
            
            # Step 3: Perform search
            search_results = await self._perform_email_search(search_terms, time_constraints)
            
            # Step 4: Extract email data
            extracted_data = await self._extract_email_data(search_results)
            
            return DataExtractionResult(
                success=True,
                data=extracted_data,
                confidence=0.8,
                extraction_method="email_automation_with_ocr",
                timestamp=datetime.now(),
                source_type="email",
                screenshots=search_results.get("screenshots", [])
            )
            
        except Exception as e:
            self.logger.error(f"Email workflow error: {e}")
            return DataExtractionResult(
                success=False, data=[], confidence=0.0,
                extraction_method="email_automation",
                timestamp=datetime.now(),
                source_type="email",
                errors=[str(e)]
            )
    
    async def _detect_email_application(self) -> Optional[str]:
        """Detect currently running email applications."""
        screen = await self.backend.capture_screen_fast()
        
        # Look for email app windows using visual detection
        email_apps = ["Mail", "Gmail", "Outlook", "Thunderbird"]
        
        for app in email_apps:
            if await self._is_app_visible(screen, app):
                return app
        
        return None
    
    async def _launch_default_email_app(self) -> Optional[str]:
        """Launch the default email application."""
        # Try Mail app first on macOS, Outlook on Windows
        default_apps = ["Mail", "Outlook"]
        
        for app in default_apps:
            launch_action = {
                "type": "launch_app",
                "app_name": app,
                "verification": "window_visible"
            }
            
            result = await self.backend.execute_action_with_verification(launch_action)
            if result.get("success"):
                await asyncio.sleep(3)  # Wait for app to load
                return app
        
        return None
    
    async def _activate_email_search(self) -> bool:
        """Activate the search interface in the email application."""
        # Try common search shortcuts
        search_shortcuts = ["cmd+f", "ctrl+f", "cmd+alt+f", "/"]
        
        for shortcut in search_shortcuts:
            action = {
                "type": "keyboard_shortcut",
                "shortcut": shortcut
            }
            
            result = await self.backend.execute_action_with_verification(action)
            if result.get("success"):
                # Wait a moment and check if search interface appeared
                await asyncio.sleep(1)
                screen = await self.backend.capture_screen_fast()
                if await self._is_search_interface_visible(screen):
                    return True
        
        return False
    
    async def _perform_email_search(self, search_terms: List[str], 
                                  time_constraints: Dict = None) -> Dict[str, Any]:
        """Perform the actual email search."""
        # Construct search query
        search_query = " ".join(search_terms)
        
        # Add time constraints if specified
        if time_constraints and time_constraints.get("time_range"):
            time_range = time_constraints["time_range"]
            # Add date filters if the email client supports them
            if "today" in time_constraints.get("raw_constraints", {}):
                search_query += " date:today"
            elif "yesterday" in time_constraints.get("raw_constraints", {}):
                search_query += " date:yesterday"
        
        # Type the search query
        type_action = {
            "type": "type_text",
            "text": search_query
        }
        
        await self.backend.execute_action_with_verification(type_action)
        
        # Press Enter to execute search
        enter_action = {
            "type": "keyboard_key",
            "key": "Return"
        }
        
        await self.backend.execute_action_with_verification(enter_action)
        
        # Wait for results to load
        await asyncio.sleep(3)
        
        # Capture results screen
        results_screen = await self.backend.capture_screen_fast()
        
        return {
            "search_query": search_query,
            "screenshots": [results_screen],
            "success": True
        }
    
    async def _extract_email_data(self, search_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract structured email data from search results."""
        if not search_results.get("screenshots"):
            return []
        
        screen = search_results["screenshots"][0]
        
        # Use OCR to extract text from the screen
        extracted_text = await self._perform_ocr(screen)
        
        # Parse email information from OCR text
        emails = await self._parse_email_info(extracted_text)
        
        return emails
    
    async def _parse_email_info(self, ocr_text: str) -> List[Dict[str, Any]]:
        """Parse email information from OCR text."""
        emails = []
        
        # Email pattern matching
        email_patterns = {
            "subject": r"Subject:\s*(.+)",
            "from": r"From:\s*(.+)",
            "to": r"To:\s*(.+)",
            "date": r"Date:\s*(.+)",
            "time": r"(\d{1,2}:\d{2}(?:\s*[APap][Mm])?)"
        }
        
        lines = ocr_text.split('\n')
        current_email = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_email:
                    emails.append(current_email)
                    current_email = {}
                continue
            
            for field, pattern in email_patterns.items():
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    current_email[field] = match.group(1).strip()
        
        # Add final email if exists
        if current_email:
            emails.append(current_email)
        
        return emails
    
    async def _is_app_visible(self, screen: np.ndarray, app_name: str) -> bool:
        """Check if an application window is visible on screen."""
        # Use OCR or template matching to detect app
        ocr_text = await self._perform_ocr(screen)
        return app_name.lower() in ocr_text.lower()
    
    async def _is_search_interface_visible(self, screen: np.ndarray) -> bool:
        """Check if search interface is visible."""
        # Look for search-related UI elements
        ocr_text = await self._perform_ocr(screen)
        search_indicators = ["search", "find", "filter", "query"]
        return any(indicator in ocr_text.lower() for indicator in search_indicators)
    
    async def _perform_ocr(self, screen: np.ndarray) -> str:
        """Perform OCR on screen image."""
        try:
            # Convert to PIL Image and use existing OCR capabilities
            # This would integrate with the backend's OCR functionality
            # For now, return placeholder text
            return "OCR extracted text placeholder"
        except Exception as e:
            self.logger.error(f"OCR error: {e}")
            return ""

class BrowserHistoryWorkflow:
    """Workflow for accessing browser history data."""
    
    def __init__(self, backend_instance):
        self.backend = backend_instance
        self.logger = logging.getLogger(f"{__name__}.BrowserHistoryWorkflow")
    
    async def execute(self, search_terms: List[str], time_constraints: Dict = None,
                     websocket=None) -> DataExtractionResult:
        """Execute browser history data extraction workflow."""
        self.logger.info(f"Executing browser history workflow with terms: {search_terms}")
        
        try:
            # Step 1: Detect active browser
            browser = await self._detect_active_browser()
            if not browser:
                browser = await self._launch_default_browser()
            
            # Step 2: Open history interface
            history_opened = await self._open_browser_history(browser)
            if not history_opened:
                return DataExtractionResult(
                    success=False, data=[], confidence=0.0,
                    extraction_method="browser_automation",
                    timestamp=datetime.now(),
                    source_type="browser_history",
                    errors=["Failed to open browser history"]
                )
            
            # Step 3: Search history
            search_results = await self._search_browser_history(search_terms, time_constraints)
            
            # Step 4: Extract history data
            extracted_data = await self._extract_history_data(search_results)
            
            return DataExtractionResult(
                success=True,
                data=extracted_data,
                confidence=0.8,
                extraction_method="browser_automation_with_ocr",
                timestamp=datetime.now(),
                source_type="browser_history",
                screenshots=search_results.get("screenshots", [])
            )
            
        except Exception as e:
            self.logger.error(f"Browser history workflow error: {e}")
            return DataExtractionResult(
                success=False, data=[], confidence=0.0,
                extraction_method="browser_automation",
                timestamp=datetime.now(),
                source_type="browser_history",
                errors=[str(e)]
            )
    
    async def _detect_active_browser(self) -> Optional[str]:
        """Detect currently active browser."""
        screen = await self.backend.capture_screen_fast()
        browsers = ["Chrome", "Safari", "Firefox", "Edge"]
        
        for browser in browsers:
            if await self._is_browser_visible(screen, browser):
                return browser
        
        return None
    
    async def _launch_default_browser(self) -> Optional[str]:
        """Launch the default browser."""
        browsers = ["Chrome", "Safari", "Firefox"]
        
        for browser in browsers:
            launch_action = {
                "type": "launch_app",
                "app_name": browser
            }
            
            result = await self.backend.execute_action_with_verification(launch_action)
            if result.get("success"):
                await asyncio.sleep(2)
                return browser
        
        return None
    
    async def _open_browser_history(self, browser: str) -> bool:
        """Open browser history interface."""
        # Browser-specific history shortcuts
        history_shortcuts = {
            "Chrome": "cmd+y",
            "Safari": "cmd+y", 
            "Firefox": "cmd+shift+h",
            "Edge": "ctrl+h"
        }
        
        shortcut = history_shortcuts.get(browser, "cmd+y")
        
        action = {
            "type": "keyboard_shortcut",
            "shortcut": shortcut
        }
        
        result = await self.backend.execute_action_with_verification(action)
        
        if result.get("success"):
            await asyncio.sleep(2)  # Wait for history to load
            return True
        
        return False
    
    async def _search_browser_history(self, search_terms: List[str], 
                                    time_constraints: Dict = None) -> Dict[str, Any]:
        """Search browser history."""
        search_query = " ".join(search_terms)
        
        # Activate search in history
        search_action = {
            "type": "keyboard_shortcut",
            "shortcut": "cmd+f"
        }
        
        await self.backend.execute_action_with_verification(search_action)
        await asyncio.sleep(1)
        
        # Type search query
        type_action = {
            "type": "type_text",
            "text": search_query
        }
        
        await self.backend.execute_action_with_verification(type_action)
        await asyncio.sleep(2)
        
        # Capture results
        results_screen = await self.backend.capture_screen_fast()
        
        return {
            "search_query": search_query,
            "screenshots": [results_screen],
            "success": True
        }
    
    async def _extract_history_data(self, search_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract browser history data from search results."""
        if not search_results.get("screenshots"):
            return []
        
        screen = search_results["screenshots"][0]
        ocr_text = await self._perform_ocr(screen)
        
        # Parse history entries
        history_entries = await self._parse_history_entries(ocr_text)
        
        return history_entries
    
    async def _parse_history_entries(self, ocr_text: str) -> List[Dict[str, Any]]:
        """Parse history entries from OCR text."""
        entries = []
        
        # History entry patterns
        url_pattern = r"https?://[^\s]+"
        time_pattern = r"(\d{1,2}:\d{2}(?:\s*[APap][Mm])?)"
        date_pattern = r"(\d{1,2}/\d{1,2}/\d{2,4})"
        
        lines = ocr_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            entry = {}
            
            # Extract URL
            url_match = re.search(url_pattern, line)
            if url_match:
                entry["url"] = url_match.group(0)
            
            # Extract time
            time_match = re.search(time_pattern, line)
            if time_match:
                entry["time"] = time_match.group(1)
            
            # Extract date
            date_match = re.search(date_pattern, line)
            if date_match:
                entry["date"] = date_match.group(1)
            
            # Extract title (remaining text)
            title_text = re.sub(url_pattern, "", line)
            title_text = re.sub(time_pattern, "", title_text)
            title_text = re.sub(date_pattern, "", title_text)
            title_text = title_text.strip()
            
            if title_text:
                entry["title"] = title_text
            
            if entry:
                entries.append(entry)
        
        return entries
    
    async def _is_browser_visible(self, screen: np.ndarray, browser: str) -> bool:
        """Check if browser is visible on screen."""
        ocr_text = await self._perform_ocr(screen)
        return browser.lower() in ocr_text.lower()
    
    async def _perform_ocr(self, screen: np.ndarray) -> str:
        """Perform OCR on screen image."""
        # Placeholder for OCR functionality
        return "OCR extracted text placeholder"

class FileSystemWorkflow:
    """Workflow for accessing file system data."""
    
    def __init__(self, backend_instance):
        self.backend = backend_instance
        self.logger = logging.getLogger(f"{__name__}.FileSystemWorkflow")
    
    async def execute(self, search_terms: List[str], time_constraints: Dict = None,
                     websocket=None) -> DataExtractionResult:
        """Execute file system data extraction workflow."""
        self.logger.info(f"Executing file system workflow with terms: {search_terms}")
        
        try:
            # Step 1: Open file manager
            file_manager = await self._open_file_manager()
            if not file_manager:
                return DataExtractionResult(
                    success=False, data=[], confidence=0.0,
                    extraction_method="file_system_automation",
                    timestamp=datetime.now(),
                    source_type="files",
                    errors=["Failed to open file manager"]
                )
            
            # Step 2: Perform file search
            search_results = await self._search_files(search_terms, time_constraints)
            
            # Step 3: Extract file data
            extracted_data = await self._extract_file_data(search_results)
            
            return DataExtractionResult(
                success=True,
                data=extracted_data,
                confidence=0.8,
                extraction_method="file_system_automation_with_ocr",
                timestamp=datetime.now(),
                source_type="files",
                screenshots=search_results.get("screenshots", [])
            )
            
        except Exception as e:
            self.logger.error(f"File system workflow error: {e}")
            return DataExtractionResult(
                success=False, data=[], confidence=0.0,
                extraction_method="file_system_automation",
                timestamp=datetime.now(),
                source_type="files",
                errors=[str(e)]
            )
    
    async def _open_file_manager(self) -> bool:
        """Open the file manager application."""
        # Try to open Finder (macOS) or Explorer (Windows)
        file_managers = ["Finder", "Explorer"]
        
        for fm in file_managers:
            launch_action = {
                "type": "launch_app",
                "app_name": fm
            }
            
            result = await self.backend.execute_action_with_verification(launch_action)
            if result.get("success"):
                await asyncio.sleep(2)
                return True
        
        return False
    
    async def _search_files(self, search_terms: List[str], 
                          time_constraints: Dict = None) -> Dict[str, Any]:
        """Search for files using the file manager's search functionality."""
        # Activate search
        search_action = {
            "type": "keyboard_shortcut",
            "shortcut": "cmd+f"
        }
        
        await self.backend.execute_action_with_verification(search_action)
        await asyncio.sleep(1)
        
        # Type search terms
        search_query = " ".join(search_terms)
        type_action = {
            "type": "type_text",
            "text": search_query
        }
        
        await self.backend.execute_action_with_verification(type_action)
        
        # Press Enter to search
        enter_action = {
            "type": "keyboard_key",
            "key": "Return"
        }
        
        await self.backend.execute_action_with_verification(enter_action)
        await asyncio.sleep(3)  # Wait for search results
        
        # Capture results
        results_screen = await self.backend.capture_screen_fast()
        
        return {
            "search_query": search_query,
            "screenshots": [results_screen],
            "success": True
        }
    
    async def _extract_file_data(self, search_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract file information from search results."""
        if not search_results.get("screenshots"):
            return []
        
        screen = search_results["screenshots"][0]
        ocr_text = await self._perform_ocr(screen)
        
        # Parse file information
        files = await self._parse_file_info(ocr_text)
        
        return files
    
    async def _parse_file_info(self, ocr_text: str) -> List[Dict[str, Any]]:
        """Parse file information from OCR text."""
        files = []
        
        # File info patterns
        file_patterns = {
            "name": r"([^\s]+\.[a-zA-Z0-9]+)",
            "size": r"(\d+(?:\.\d+)?\s*[KMGT]?B)",
            "date": r"(\d{1,2}/\d{1,2}/\d{2,4})",
            "time": r"(\d{1,2}:\d{2}(?:\s*[APap][Mm])?)"
        }
        
        lines = ocr_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            file_info = {}
            
            # Extract file name
            name_match = re.search(file_patterns["name"], line)
            if name_match:
                file_info["name"] = name_match.group(1)
            
            # Extract size
            size_match = re.search(file_patterns["size"], line)
            if size_match:
                file_info["size"] = size_match.group(1)
            
            # Extract date
            date_match = re.search(file_patterns["date"], line)
            if date_match:
                file_info["date"] = date_match.group(1)
            
            # Extract time
            time_match = re.search(file_patterns["time"], line)
            if time_match:
                file_info["time"] = time_match.group(1)
            
            if file_info:
                files.append(file_info)
        
        return files
    
    async def _perform_ocr(self, screen: np.ndarray) -> str:
        """Perform OCR on screen image."""
        # Placeholder for OCR functionality
        return "OCR extracted text placeholder"

class SystemInfoWorkflow:
    """Workflow for accessing system information."""
    
    def __init__(self, backend_instance):
        self.backend = backend_instance
        self.logger = logging.getLogger(f"{__name__}.SystemInfoWorkflow")
    
    async def execute(self, search_terms: List[str], time_constraints: Dict = None,
                     websocket=None) -> DataExtractionResult:
        """Execute system information extraction workflow."""
        self.logger.info("Executing system info workflow")
        
        try:
            # Step 1: Capture current screen state
            current_screen = await self.backend.capture_screen_fast()
            
            # Step 2: Open system monitor
            monitor_opened = await self._open_system_monitor()
            if not monitor_opened:
                return DataExtractionResult(
                    success=False, data=[], confidence=0.0,
                    extraction_method="system_automation",
                    timestamp=datetime.now(),
                    source_type="system_info",
                    errors=["Failed to open system monitor"]
                )
            
            # Step 3: Extract system data
            system_data = await self._extract_system_data()
            
            return DataExtractionResult(
                success=True,
                data=system_data,
                confidence=0.9,
                extraction_method="system_automation_with_ocr",
                timestamp=datetime.now(),
                source_type="system_info",
                screenshots=[current_screen]
            )
            
        except Exception as e:
            self.logger.error(f"System info workflow error: {e}")
            return DataExtractionResult(
                success=False, data=[], confidence=0.0,
                extraction_method="system_automation",
                timestamp=datetime.now(),
                source_type="system_info",
                errors=[str(e)]
            )
    
    async def _open_system_monitor(self) -> bool:
        """Open system monitor application."""
        # Try Activity Monitor (macOS) or Task Manager (Windows)
        monitors = [
            {"name": "Activity Monitor", "shortcut": "cmd+space"},
            {"name": "Task Manager", "shortcut": "ctrl+shift+esc"}
        ]
        
        for monitor in monitors:
            launch_action = {
                "type": "keyboard_shortcut",
                "shortcut": monitor["shortcut"]
            }
            
            result = await self.backend.execute_action_with_verification(launch_action)
            if result.get("success"):
                await asyncio.sleep(2)
                
                # Type monitor name if using Spotlight
                if "cmd+space" in monitor["shortcut"]:
                    type_action = {
                        "type": "type_text",
                        "text": monitor["name"]
                    }
                    await self.backend.execute_action_with_verification(type_action)
                    
                    enter_action = {
                        "type": "keyboard_key",
                        "key": "Return"
                    }
                    await self.backend.execute_action_with_verification(enter_action)
                    await asyncio.sleep(3)
                
                return True
        
        return False
    
    async def _extract_system_data(self) -> List[Dict[str, Any]]:
        """Extract system information from monitor application."""
        monitor_screen = await self.backend.capture_screen_fast()
        ocr_text = await self._perform_ocr(monitor_screen)
        
        # Parse process information
        processes = await self._parse_process_info(ocr_text)
        
        return processes
    
    async def _parse_process_info(self, ocr_text: str) -> List[Dict[str, Any]]:
        """Parse process information from OCR text."""
        processes = []
        
        # Process info patterns
        process_patterns = {
            "name": r"([A-Za-z][A-Za-z0-9\s\-\.]+)",
            "cpu": r"(\d+(?:\.\d+)?%)",
            "memory": r"(\d+(?:\.\d+)?\s*[KMGT]?B)",
            "pid": r"PID:\s*(\d+)"
        }
        
        lines = ocr_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            process_info = {}
            
            # Extract process name (first non-numeric word)
            words = line.split()
            for word in words:
                if not word.isdigit() and not re.match(r'\d+%', word):
                    process_info["name"] = word
                    break
            
            # Extract CPU usage
            cpu_match = re.search(process_patterns["cpu"], line)
            if cpu_match:
                process_info["cpu_usage"] = cpu_match.group(1)
            
            # Extract memory usage
            memory_match = re.search(process_patterns["memory"], line)
            if memory_match:
                process_info["memory_usage"] = memory_match.group(1)
            
            if process_info and "name" in process_info:
                processes.append(process_info)
        
        return processes
    
    async def _perform_ocr(self, screen: np.ndarray) -> str:
        """Perform OCR on screen image."""
        # Placeholder for OCR functionality
        return "OCR extracted text placeholder"

class WorkflowOrchestrator:
    """Orchestrates multiple data source workflows."""
    
    def __init__(self, backend_instance):
        self.backend = backend_instance
        self.workflows = {
            "email": EmailWorkflow(backend_instance),
            "browser_history": BrowserHistoryWorkflow(backend_instance),
            "files": FileSystemWorkflow(backend_instance),
            "system_info": SystemInfoWorkflow(backend_instance)
        }
        self.logger = logging.getLogger(f"{__name__}.WorkflowOrchestrator")
    
    async def execute_workflows(self, detected_sources: List[Dict], 
                              search_terms: List[str], time_constraints: Dict = None,
                              websocket=None) -> Dict[str, DataExtractionResult]:
        """Execute multiple workflows in parallel or sequence."""
        results = {}
        
        for source in detected_sources:
            source_name = source["source"]
            
            if source_name in self.workflows:
                self.logger.info(f"Executing workflow for {source_name}")
                
                try:
                    result = await self.workflows[source_name].execute(
                        search_terms, time_constraints, websocket
                    )
                    results[source_name] = result
                    
                except Exception as e:
                    self.logger.error(f"Error executing {source_name} workflow: {e}")
                    results[source_name] = DataExtractionResult(
                        success=False, data=[], confidence=0.0,
                        extraction_method=f"{source_name}_automation",
                        timestamp=datetime.now(),
                        source_type=source_name,
                        errors=[str(e)]
                    )
            else:
                self.logger.warning(f"No workflow available for {source_name}")
                results[source_name] = DataExtractionResult(
                    success=False, data=[], confidence=0.0,
                    extraction_method="not_implemented",
                    timestamp=datetime.now(),
                    source_type=source_name,
                    errors=[f"Workflow not implemented for {source_name}"]
                )
        
        return results

if __name__ == "__main__":
    # Test the workflows
    async def test_workflows():
        # This would require a backend instance to test
        print("Workflow classes defined successfully")
        print("Available workflows:")
        for workflow_name in ["email", "browser_history", "files", "system_info"]:
            print(f"  - {workflow_name}")
    
    asyncio.run(test_workflows())