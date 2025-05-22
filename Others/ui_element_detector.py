#!/usr/bin/env python3
"""
UI Element Detector
Enhanced detection of application-specific UI elements to improve application context awareness.
"""
import os
import json
import time
import logging
import base64
import asyncio
import aiohttp
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from PIL import Image
from io import BytesIO

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/ui_element_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ui_element_detector")

@dataclass
class UIElement:
    """Data structure for detected UI elements"""
    element_id: str  # Unique identifier for the element
    element_type: str  # Type of UI element (button, textfield, menu, etc.)
    element_text: str = ""  # Text content of the element
    bounding_box: Optional[List[int]] = None  # [x1, y1, x2, y2] if available
    state: str = ""  # Element state (enabled, disabled, selected, etc.)
    action: str = ""  # Action associated with the element
    confidence: float = 0.0  # Confidence in detection (0-1)
    parent_component: str = ""  # Parent component/container
    interaction_hints: List[str] = field(default_factory=list)  # Ways to interact with element
    app_specific: Dict[str, Any] = field(default_factory=dict)  # App-specific attributes

@dataclass
class UIAnalysisResult:
    """Data structure for UI analysis results"""
    timestamp: float
    app_name: str
    view_name: str
    elements: List[UIElement] = field(default_factory=list)
    app_specific_patterns: Dict[str, Any] = field(default_factory=dict)
    interaction_flows: List[Dict[str, Any]] = field(default_factory=list)
    screenshot_hash: str = ""
    raw_analysis: str = ""

class UIElementDetector:
    """
    Specialized detector for UI elements with application-specific enhancements.
    Provides detailed information about interface elements to improve context awareness.
    """
    
    def __init__(self, llava_url="http://localhost:11434"):
        self.llava_url = llava_url
        self.llava_endpoint = f"{llava_url}/api/chat"
        self.llava_model = "llava"
        self.llava_timeout = 90  # Increased timeout for detailed UI analysis
        
        # Path settings
        self.results_dir = "results/ui_elements"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Initialize element type classifiers
        self.element_classifiers = self._init_element_classifiers()
        
        # Initialize app-specific patterns
        self.app_patterns = self._init_app_patterns()
    
    def _init_element_classifiers(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize pattern-based classifiers for UI element types"""
        classifiers = {}
        
        # Button classifier
        classifiers["button"] = {
            "patterns": [
                r"button", r"btn", r"submit", r"cancel", r"ok", r"save",
                r"add", r"delete", r"close", r"open", r"start", r"stop"
            ],
            "visual_cues": [
                "rectangular shape", "rounded corners", "bordered element",
                "colored background", "hover effect", "clickable",
                "different shade on hover"
            ]
        }
        
        # Text field classifier
        classifiers["textfield"] = {
            "patterns": [
                r"input", r"field", r"text box", r"textbox", r"textarea",
                r"search box", r"form field", r"entry field", r"type here"
            ],
            "visual_cues": [
                "rectangular box", "cursor indicator", "blinking cursor",
                "white/empty background", "bordered area for text entry",
                "placeholder text", "text input area"
            ]
        }
        
        # Menu classifier
        classifiers["menu"] = {
            "patterns": [
                r"dropdown", r"menu", r"select", r"options", r"list box",
                r"dropdown menu", r"pull-down", r"context menu", r"submenu"
            ],
            "visual_cues": [
                "downward arrow", "expansion indicator", "collapsed list",
                "selector", "vertical list", "option list", "toggleable" 
            ]
        }
        
        # Checkbox classifier
        classifiers["checkbox"] = {
            "patterns": [
                r"checkbox", r"check box", r"tick box", r"checked", r"unchecked",
                r"toggle box", r"selectable option"
            ],
            "visual_cues": [
                "small square", "checkmark", "tick mark", "toggleable state",
                "binary selection", "marked/unmarked"
            ]
        }
        
        # Radio button classifier
        classifiers["radio"] = {
            "patterns": [
                r"radio button", r"radio option", r"option button", r"selector",
                r"single choice", r"circular button"
            ],
            "visual_cues": [
                "small circle", "filled/unfilled circle", "mutually exclusive",
                "circular selector", "single select option"
            ]
        }
        
        # Link classifier
        classifiers["link"] = {
            "patterns": [
                r"link", r"hyperlink", r"click here", r"anchor", r"navigation link",
                r"href", r"url"
            ],
            "visual_cues": [
                "underlined text", "colored text", "different color from regular text",
                "clickable text", "changes cursor to hand", "navigational element"
            ]
        }
        
        # Tab classifier
        classifiers["tab"] = {
            "patterns": [
                r"tab", r"tab panel", r"tab button", r"tab control", r"page tab",
                r"tabbed interface", r"tab navigator"
            ],
            "visual_cues": [
                "tabbed interface", "tab row", "selected/unselected state",
                "browser-like tabs", "content switcher", "header tab"
            ]
        }
        
        # Label classifier
        classifiers["label"] = {
            "patterns": [
                r"label", r"text label", r"field label", r"static text",
                r"descriptive text", r"field name"
            ],
            "visual_cues": [
                "plain text", "non-interactive", "descriptor", "informational text",
                "title text", "heading", "subheading", "static display"
            ]
        }
        
        # Icon classifier
        classifiers["icon"] = {
            "patterns": [
                r"icon", r"symbol", r"image button", r"graphical button",
                r"icon button", r"symbolic representation"
            ],
            "visual_cues": [
                "small image", "symbolic representation", "graphical element",
                "pictographic", "visual indicator"
            ]
        }
        
        # Slider classifier
        classifiers["slider"] = {
            "patterns": [
                r"slider", r"range slider", r"volume control", r"scaling control",
                r"adjustable scale", r"scroll bar", r"range control"
            ],
            "visual_cues": [
                "horizontal bar", "draggable handle", "min/max values",
                "adjustable control", "continuous value selector"
            ]
        }
        
        # Progress indicator classifier
        classifiers["progress"] = {
            "patterns": [
                r"progress bar", r"loading indicator", r"completion indicator",
                r"status bar", r"progress indicator", r"loading bar"
            ],
            "visual_cues": [
                "horizontal indicator", "filling bar", "loading animation",
                "completion status", "percentage indicator"
            ]
        }
        
        # Toggle switch classifier
        classifiers["toggle"] = {
            "patterns": [
                r"toggle", r"switch", r"on/off", r"on-off switch", r"toggle switch",
                r"enabled/disabled switch", r"state switch"
            ],
            "visual_cues": [
                "sliding switch", "on/off indicator", "binary state control",
                "toggleable control", "enabled/disabled state"
            ]
        }
        
        # Dropdown classifier
        classifiers["dropdown"] = {
            "patterns": [
                r"dropdown", r"drop-down", r"dropdown list", r"dropdown menu",
                r"select menu", r"pulldown", r"combo box"
            ],
            "visual_cues": [
                "down arrow indicator", "selection field", "expandable list",
                "selection control with options"
            ]
        }
        
        # Dialog classifier
        classifiers["dialog"] = {
            "patterns": [
                r"dialog", r"popup", r"modal", r"window", r"dialog box",
                r"alert box", r"confirmation dialog"
            ],
            "visual_cues": [
                "floating window", "overlay", "modal window", "popup box",
                "secondary window", "focus-stealing element"
            ]
        }
        
        # Toolbar classifier
        classifiers["toolbar"] = {
            "patterns": [
                r"toolbar", r"tool bar", r"action bar", r"button bar",
                r"control bar", r"command bar"
            ],
            "visual_cues": [
                "row of buttons", "horizontal control strip", "button collection",
                "action controls", "command strip"
            ]
        }
        
        # Tree view classifier
        classifiers["treeview"] = {
            "patterns": [
                r"tree view", r"tree", r"hierarchical view", r"folder tree",
                r"expandable tree", r"nested list"
            ],
            "visual_cues": [
                "expandable nodes", "hierarchical structure", "nested items",
                "collapsible sections", "parent-child relationship"
            ]
        }
        
        return classifiers
    
    def _init_app_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize application-specific UI patterns"""
        patterns = {}
        
        # Gmail patterns
        patterns["gmail"] = {
            "compose": {
                "patterns": ["compose", "new message", "new email", "write email"],
                "elements": ["to field", "subject field", "body", "send button"]
            },
            "inbox": {
                "patterns": ["inbox", "primary", "unread", "emails list"],
                "elements": ["email list", "sidebar", "search mail", "refresh"]
            },
            "reading": {
                "patterns": ["reading email", "open email", "email content", "message body"],
                "elements": ["email header", "email body", "reply button", "forward button"]
            }
        }
        
        # Visual Studio Code patterns
        patterns["vscode"] = {
            "editor": {
                "patterns": ["code editor", "editing file", "text editor", "source code"],
                "elements": ["text area", "line numbers", "scrollbar", "minimap"]
            },
            "explorer": {
                "patterns": ["file explorer", "project explorer", "file tree", "file browser"],
                "elements": ["folder structure", "file list", "tree view", "context menu"]
            },
            "terminal": {
                "patterns": ["integrated terminal", "command line", "shell", "console"],
                "elements": ["command prompt", "text output", "input line"]
            },
            "search": {
                "patterns": ["search results", "find in files", "search panel"],
                "elements": ["search box", "results list", "replace field", "match case"]
            }
        }
        
        # Microsoft Word patterns
        patterns["word"] = {
            "editing": {
                "patterns": ["document editing", "text editing", "writing", "editing content"],
                "elements": ["document area", "cursor", "text selection", "ribbon"]
            },
            "review": {
                "patterns": ["review mode", "track changes", "comments", "reviewing"],
                "elements": ["comment bubble", "tracked change", "review pane", "accept/reject"]
            },
            "formatting": {
                "patterns": ["text formatting", "style editing", "format panel"],
                "elements": ["bold button", "italic button", "underline", "font selector", "paragraph settings"]
            }
        }
        
        # Chrome/Browser patterns
        patterns["browser"] = {
            "navigation": {
                "patterns": ["browser navigation", "address bar", "url bar"],
                "elements": ["back button", "forward button", "reload button", "address field"]
            },
            "tabs": {
                "patterns": ["browser tabs", "tab bar", "multiple tabs"],
                "elements": ["tab strip", "new tab button", "active tab", "inactive tab"]
            },
            "webpage": {
                "patterns": ["web content", "website", "web page", "site content"],
                "elements": ["main content", "navigation menu", "header", "footer", "sidebar"]
            }
        }
        
        # Slack patterns
        patterns["slack"] = {
            "channel": {
                "patterns": ["channel view", "message history", "chat channel"],
                "elements": ["message list", "message input", "channel info", "member list"]
            },
            "thread": {
                "patterns": ["thread view", "reply thread", "conversation thread"],
                "elements": ["parent message", "replies", "thread input", "back to channel"]
            },
            "direct_message": {
                "patterns": ["direct message", "dm", "private chat"],
                "elements": ["conversation history", "message input", "user status"]
            }
        }
        
        # Add more applications as needed
        return patterns
    
    async def detect_ui_elements(self, image_path: str, app_context: Optional[Dict[str, Any]] = None) -> UIAnalysisResult:
        """
        Detect and analyze UI elements from a screenshot
        
        Args:
            image_path: Path to the screenshot image
            app_context: Optional context about the current application
            
        Returns:
            UIAnalysisResult with detected elements and patterns
        """
        try:
            # Load the image
            logger.info(f"Analyzing UI elements in: {image_path}")
            image = Image.open(image_path)
            
            # Generate image hash
            import hashlib
            img_hash = hashlib.md5(image.tobytes()).hexdigest()
            
            # Convert image to base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            # Prepare application context for specialized prompting
            app_name = app_context.get("app_name", "Unknown") if app_context else "Unknown"
            view_name = app_context.get("view_name", "") if app_context else ""
            
            # Perform detailed UI analysis with LLaVA
            start_time = time.time()
            llava_analysis = await self._analyze_ui_with_llava(img_base64, app_name, view_name)
            elapsed_time = time.time() - start_time
            
            # Parse the results into structured data
            ui_data = self._parse_ui_analysis(llava_analysis, app_name)
            
            # Create result object
            result = UIAnalysisResult(
                timestamp=time.time(),
                app_name=app_name,
                view_name=view_name,
                elements=ui_data["elements"],
                app_specific_patterns=ui_data["patterns"],
                interaction_flows=ui_data.get("flows", []),
                screenshot_hash=img_hash,
                raw_analysis=llava_analysis
            )
            
            # Save results
            self._save_analysis_result(result)
            
            # Log summary
            logger.info(f"UI analysis complete: {len(result.elements)} elements detected")
            logger.info(f"Analysis time: {elapsed_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting UI elements: {e}")
            return UIAnalysisResult(
                timestamp=time.time(),
                app_name="Error",
                view_name="Error",
                raw_analysis=f"Error: {str(e)}"
            )
    
    async def _analyze_ui_with_llava(self, img_base64: str, app_name: str, view_name: str) -> str:
        """
        Analyze the UI elements with LLaVA using specialized prompt
        
        Args:
            img_base64: Base64 encoded image
            app_name: Name of the application for specialized detection
            view_name: Current view name for context
            
        Returns:
            str: The full textual analysis from LLaVA
        """
        # Customize system prompt based on application
        app_specific_instructions = ""
        
        # Add application-specific instructions based on app name
        if app_name.lower() in ["gmail", "google mail", "mail"]:
            app_specific_instructions = """
For Gmail interface:
- Identify email-specific elements (compose button, inbox tabs, email list, read/unread indicators)
- Note the specific view (inbox, reading email, composing email)
- For emails, extract sender, subject, timestamp if visible
- Look for labels, importance indicators, attachment icons
"""
        elif "word" in app_name.lower() or "document" in app_name.lower():
            app_specific_instructions = """
For Word/document editing interface:
- Identify editing-specific elements (text cursor, selection, formatting tools)
- Note the specific ribbon tab that's active
- Identify document structure elements (headings, lists, tables)
- Look for editing indicators (spelling/grammar, track changes, comments)
"""
        elif "code" in app_name.lower() or "studio" in app_name.lower() or "ide" in app_name.lower():
            app_specific_instructions = """
For Code Editor interface:
- Identify code-specific elements (line numbers, syntax highlighting, error indicators)
- Note the view type (editor, terminal, explorer, debug)
- Identify language-specific features if visible
- Look for version control indicators, git status markers
"""
        elif "browser" in app_name.lower() or "chrome" in app_name.lower() or "firefox" in app_name.lower() or "safari" in app_name.lower():
            app_specific_instructions = """
For Web Browser interface:
- Identify browser controls (address bar, navigation buttons, tabs)
- Distinguish between browser UI and webpage content
- Note if this is a specific web application (Gmail, Google Docs, etc.)
- Identify webpage-specific UI elements (menus, forms, content areas)
"""
        
        # Prepare the message for LLaVA with enhanced UI element detection prompt
        system_prompt = f"""You are an expert UI element analyzer specialized in identifying and categorizing interface components with high precision. Your task is to analyze this screenshot and identify all visible UI elements with detailed attributes.

For each UI element, provide:
1. ELEMENT_TYPE: The specific type (button, textfield, menu, dropdown, checkbox, radio, link, tab, label, icon, slider, etc.)
2. ELEMENT_TEXT: Any text contained in or associated with the element
3. STATE: The current state if applicable (enabled, disabled, selected, checked, expanded, collapsed)
4. PARENT: The parent component or container this element belongs to
5. INTERACTION: How a user would interact with this element (click, type, drag, etc.)

Structure your response in this format:
UI ELEMENTS:
1. Type: [element type]
   Text: [element text]
   State: [current state]
   Parent: [parent component]
   Interaction: [how to interact]

2. Type: [element type]
   ...

{app_specific_instructions}

After listing the elements, identify application-specific patterns (toolbars, sidebars, main content areas) and how they relate to the application "{app_name}" and view "{view_name}".

Finally, identify any potential user task flows visible in the interface (what sequence of interactions would achieve common tasks in this view)."""

        # Create message payload
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Analyze this screenshot and identify all UI elements with their properties. This appears to be {app_name} in {view_name if view_name else 'some view'}. Please be very detailed and precise about element types, states, and relationships."
            }
        ]
        
        # Prepare the payload
        payload = {
            "model": self.llava_model,
            "messages": messages,
            "images": [img_base64],
            "temperature": 0.1,  # Lower temperature for precise analysis
            "stream": True
        }
        
        logger.info(f"Sending request to LLaVA API for detailed UI analysis of {app_name}...")
        
        try:
            # Send request to LLaVA
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.llava_endpoint,
                    json=payload,
                    timeout=self.llava_timeout
                ) as response:
                    logger.info(f"Received response status: {response.status}")
                    
                    if response.status != 200:
                        logger.error(f"LLaVA request failed with status {response.status}")
                        return f"Error: LLaVA request failed with status {response.status}"
                    
                    # Handle streaming response
                    full_response = ""
                    
                    # Process the streaming NDJSON response
                    logger.info("Processing streaming response...")
                    async for line in response.content:
                        try:
                            line_str = line.decode('utf-8').strip()
                            if not line_str:
                                continue
                                
                            # Parse the JSON
                            try:
                                chunk = json.loads(line_str)
                                if 'message' in chunk and 'content' in chunk['message']:
                                    content = chunk['message']['content']
                                    full_response += content
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse JSON: {line_str[:50]}...")
                        except Exception as e:
                            logger.warning(f"Error processing response line: {e}")
                            
                    return full_response
                    
        except asyncio.TimeoutError:
            logger.error(f"LLaVA request timed out after {self.llava_timeout}s")
            return "Error: LLaVA request timed out"
        except Exception as e:
            logger.error(f"Error in LLaVA analysis: {e}")
            return f"Error: {str(e)}"
    
    def _parse_ui_analysis(self, analysis_text: str, app_name: str) -> Dict[str, Any]:
        """
        Parse LLaVA UI analysis into structured data
        
        Args:
            analysis_text: Raw text from LLaVA analysis
            app_name: Application name for context
            
        Returns:
            Dict with parsed UI elements and patterns
        """
        result = {
            "elements": [],
            "patterns": {},
            "flows": []
        }
        
        try:
            # Extract UI elements section
            elements_section = re.search(r"UI ELEMENTS:?\s*(.+?)(?:PATTERNS|APPLICATION-SPECIFIC PATTERNS|TASK FLOWS|$)", 
                                        analysis_text, re.DOTALL | re.IGNORECASE)
            
            if elements_section:
                elements_text = elements_section.group(1).strip()
                
                # Find numbered elements (e.g. "1. Type: button")
                element_blocks = re.split(r"\n\s*\d+\.\s+", elements_text)
                
                # Process each element block
                for i, block in enumerate(element_blocks):
                    if i == 0 and not block.strip().startswith("Type:"):
                        continue  # Skip header text
                        
                    # Extract element properties
                    element_type_match = re.search(r"Type:\s*([^\n]+)", block, re.IGNORECASE)
                    element_text_match = re.search(r"Text:\s*([^\n]+)", block, re.IGNORECASE)
                    element_state_match = re.search(r"State:\s*([^\n]+)", block, re.IGNORECASE)
                    element_parent_match = re.search(r"Parent:\s*([^\n]+)", block, re.IGNORECASE)
                    element_interaction_match = re.search(r"Interaction:\s*([^\n]+)", block, re.IGNORECASE)
                    
                    # Create element object
                    if element_type_match:
                        element_type = element_type_match.group(1).strip().lower()
                        
                        # Normalize element type
                        element_type = self._normalize_element_type(element_type)
                        
                        element = UIElement(
                            element_id=f"element_{i}_{int(time.time())}",
                            element_type=element_type,
                            element_text=element_text_match.group(1).strip() if element_text_match else "",
                            state=element_state_match.group(1).strip() if element_state_match else "",
                            parent_component=element_parent_match.group(1).strip() if element_parent_match else "",
                            confidence=0.8  # High confidence for structured format
                        )
                        
                        # Add interaction hints
                        if element_interaction_match:
                            interaction_text = element_interaction_match.group(1).strip()
                            element.interaction_hints = [hint.strip() for hint in interaction_text.split(',')]
                        
                        # Add application-specific attributes
                        element.app_specific = self._extract_app_specific_attrs(element, app_name)
                        
                        result["elements"].append(element)
            
            # Extract patterns section
            patterns_section = re.search(r"(?:PATTERNS|APPLICATION-SPECIFIC PATTERNS):?\s*(.+?)(?:TASK FLOWS|USER FLOWS|$)", 
                                       analysis_text, re.DOTALL | re.IGNORECASE)
            
            if patterns_section:
                patterns_text = patterns_section.group(1).strip()
                
                # Extract patterns as text
                result["patterns"] = {
                    "raw_text": patterns_text,
                    "app_name": app_name
                }
                
                # Try to identify specific patterns based on app name
                app_key = None
                for key in self.app_patterns.keys():
                    if key.lower() in app_name.lower():
                        app_key = key
                        break
                
                if app_key:
                    app_patterns = self.app_patterns[app_key]
                    result["patterns"]["identified"] = {}
                    
                    for pattern_key, pattern_data in app_patterns.items():
                        for pattern in pattern_data["patterns"]:
                            if pattern.lower() in patterns_text.lower():
                                result["patterns"]["identified"][pattern_key] = True
                                break
            
            # Extract task flows section
            flows_section = re.search(r"(?:TASK FLOWS|USER FLOWS):?\s*(.+?)$", 
                                    analysis_text, re.DOTALL | re.IGNORECASE)
            
            if flows_section:
                flows_text = flows_section.group(1).strip()
                
                # Extract numbered flows
                flow_blocks = re.split(r"\n\s*\d+\.\s+", flows_text)
                
                flows = []
                for i, block in enumerate(flow_blocks):
                    if i == 0 and not re.search(r"[a-z]", block, re.IGNORECASE):
                        continue  # Skip header text
                        
                    if block.strip():
                        flows.append({"description": block.strip()})
                
                result["flows"] = flows
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing UI analysis: {e}")
            return result
    
    def _normalize_element_type(self, element_type: str) -> str:
        """
        Normalize element type to a standard set of types
        
        Args:
            element_type: Raw element type from analysis
            
        Returns:
            Normalized element type
        """
        element_type = element_type.lower()
        
        # Check against known element types
        for classifier_type in self.element_classifiers.keys():
            patterns = self.element_classifiers[classifier_type]["patterns"]
            for pattern in patterns:
                if re.search(pattern, element_type, re.IGNORECASE):
                    return classifier_type
        
        # Handle common aliases
        if "text box" in element_type or "input field" in element_type:
            return "textfield"
        elif "drop down" in element_type or "dropdown" in element_type:
            return "dropdown"
        elif "check box" in element_type:
            return "checkbox"
        elif "radio button" in element_type:
            return "radio"
        elif "scroll" in element_type:
            return "scrollbar"
        elif "icon button" in element_type:
            return "button"  # Prioritize button over icon
        elif "label" in element_type or "text label" in element_type:
            return "label"
        
        # Default fallbacks
        return element_type
    
    def _extract_app_specific_attrs(self, element: UIElement, app_name: str) -> Dict[str, Any]:
        """
        Extract application-specific attributes for the element
        
        Args:
            element: The UI element
            app_name: The application name
            
        Returns:
            Dictionary of app-specific attributes
        """
        app_specific = {}
        
        # Gmail-specific attributes
        if "gmail" in app_name.lower():
            if element.element_type == "button":
                if "compose" in element.element_text.lower():
                    app_specific["action"] = "compose_email"
                    app_specific["importance"] = "high"
                elif "send" in element.element_text.lower():
                    app_specific["action"] = "send_email"
                    app_specific["importance"] = "high"
                elif "reply" in element.element_text.lower():
                    app_specific["action"] = "reply_email"
                    app_specific["importance"] = "medium"
            elif element.element_type == "textfield":
                if any(x in element.parent_component.lower() for x in ["compose", "new email", "message"]):
                    if "to" in element.element_text.lower() or "recipient" in element.element_text.lower():
                        app_specific["field_type"] = "recipients"
                    elif "subject" in element.element_text.lower():
                        app_specific["field_type"] = "subject"
                    else:
                        app_specific["field_type"] = "message_body"
        
        # VSCode-specific attributes
        elif any(x in app_name.lower() for x in ["vscode", "visual studio code", "code editor"]):
            if element.element_type == "tree_view" or "explorer" in element.parent_component.lower():
                app_specific["panel_type"] = "file_explorer"
            elif "terminal" in element.parent_component.lower():
                app_specific["panel_type"] = "terminal"
            elif element.element_type == "textfield" and "search" in element.element_text.lower():
                app_specific["action"] = "search_code"
        
        # Word-specific attributes
        elif "word" in app_name.lower() or "document" in app_name.lower():
            if "format" in element.parent_component.lower() or "ribbon" in element.parent_component.lower():
                app_specific["toolbar_type"] = "formatting"
                if element.element_type == "button":
                    for format_action in ["bold", "italic", "underline", "font", "style"]:
                        if format_action in element.element_text.lower():
                            app_specific["format_action"] = format_action
                            break
        
        # Browser-specific attributes
        elif any(x in app_name.lower() for x in ["browser", "chrome", "firefox", "safari", "edge"]):
            if element.element_type == "textfield" and any(x in element.parent_component.lower() 
                                                        for x in ["address", "url", "navigation"]):
                app_specific["field_type"] = "address_bar"
            elif element.element_type == "tab":
                app_specific["component_type"] = "browser_tab"
            elif element.element_type == "button" and any(x in element.element_text.lower() 
                                                        for x in ["back", "forward", "reload", "refresh"]):
                app_specific["action"] = "navigation"
        
        return app_specific
    
    def _save_analysis_result(self, result: UIAnalysisResult):
        """Save analysis result to a JSON file"""
        try:
            # Create output filename based on timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{self.results_dir}/ui_analysis_{timestamp}.json"
            
            # Convert to dict for serialization
            result_dict = {
                "timestamp": result.timestamp,
                "app_name": result.app_name,
                "view_name": result.view_name,
                "elements": [asdict(elem) for elem in result.elements],
                "app_specific_patterns": result.app_specific_patterns,
                "interaction_flows": result.interaction_flows,
                "screenshot_hash": result.screenshot_hash
            }
            
            with open(filename, 'w') as f:
                json.dump(result_dict, f, indent=2)
                
            logger.info(f"Saved UI analysis result to {filename}")
            
            # Also save as latest.json for easy access
            with open(f"{self.results_dir}/latest.json", 'w') as f:
                json.dump(result_dict, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving UI analysis result: {e}")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="UI Element Detector")
    parser.add_argument("image_path", help="Path to screenshot image")
    parser.add_argument("--app", default="", help="Application name (if known)")
    parser.add_argument("--view", default="", help="View name (if known)")
    parser.add_argument("--llava-url", default="http://localhost:11434", help="URL for Ollama API (default: http://localhost:11434)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"Error: Image file '{args.image_path}' not found")
        return 1
    
    print(f"Analyzing UI elements in: {args.image_path}")
    if args.app:
        print(f"Application context: {args.app}")
    if args.view:
        print(f"View context: {args.view}")
    
    detector = UIElementDetector(llava_url=args.llava_url)
    
    # Create app context
    app_context = None
    if args.app:
        app_context = {
            "app_name": args.app,
            "view_name": args.view
        }
    
    # Run detection
    result = await detector.detect_ui_elements(args.image_path, app_context)
    
    # Print formatted results
    print("\n===== UI ELEMENT ANALYSIS =====")
    print(f"Application: {result.app_name}")
    print(f"View: {result.view_name}")
    print(f"Element count: {len(result.elements)}")
    print("\nDetected Elements:")
    
    for i, element in enumerate(result.elements):
        print(f"{i+1}. {element.element_type.upper()}: {element.element_text}")
        print(f"   State: {element.state}")
        print(f"   Parent: {element.parent_component}")
        print(f"   Interaction: {', '.join(element.interaction_hints)}")
        if element.app_specific:
            print(f"   App-specific: {element.app_specific}")
        print()
    
    print("\nApplication-Specific Patterns:")
    if result.app_specific_patterns:
        for pattern_key, pattern_value in result.app_specific_patterns.items():
            print(f"  - {pattern_key}: {pattern_value}")
    else:
        print("  No application-specific patterns detected")
    
    print("\nInteraction Flows:")
    if result.interaction_flows:
        for i, flow in enumerate(result.interaction_flows):
            print(f"{i+1}. {flow.get('description', '')}")
    else:
        print("  No interaction flows detected")
    
    print("==============================")
    print(f"\nDetailed results saved to {detector.results_dir}/latest.json")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nScript terminated by user")
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)