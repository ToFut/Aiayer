#!/usr/bin/env python3
"""
Enhanced Application Detection
Comprehensive integration with LLaVA for detecting any application type.
"""
import os
import sys
import time
import json
import asyncio
import logging
import aiohttp
import base64
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from PIL import Image
from io import BytesIO

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_app_detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("enhanced_app_detection")

@dataclass
class AppSignature:
    """Data structure for application signatures used in detection."""
    name: str
    patterns: List[str] = field(default_factory=list)
    ui_elements: List[str] = field(default_factory=list)
    common_views: Dict[str, List[str]] = field(default_factory=dict)

@dataclass
class DetectionResult:
    """Data structure for application detection results."""
    application: str
    confidence: float = 0.0
    category: str = ""
    view: str = ""
    workflow: str = ""
    ui_elements: List[Dict[str, Any]] = field(default_factory=list)
    raw_analysis: str = ""
    analysis_time: float = 0.0
    screenshot_hash: str = ""

class EnhancedAppDetector:
    """Enhanced application detector for all application types."""
    
    def __init__(self, llava_url="http://localhost:11434"):
        self.llava_url = llava_url
        self.llava_endpoint = f"{llava_url}/api/chat"
        self.llava_model = "llava"
        self.llava_timeout = 60
        self.running = False
        self.results_dir = "results/app_detection"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Load application signatures database
        self.app_signatures = self._load_app_signatures()
        
        # Test connection
        self._test_llava_connection()
        
    def _test_llava_connection(self):
        """Test connection to LLaVA service"""
        try:
            import requests
            response = requests.get(f"{self.llava_url}/api/version", timeout=2)
            if response.status_code == 200:
                logger.info(f"Successfully connected to Ollama API at {self.llava_url}")
                return True
            else:
                logger.warning(f"Failed to connect to Ollama API at {self.llava_url}: {response.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Error connecting to LLaVA service: {e}")
            return False
    
    def _load_app_signatures(self) -> Dict[str, AppSignature]:
        """Load application signatures for enhanced detection."""
        signatures = {}
        
        # Productivity & Office Applications
        signatures["microsoft_word"] = AppSignature(
            name="Microsoft Word",
            patterns=["microsoft word", "word document", "word processing", "office word"],
            ui_elements=["ribbon", "toolbar", "formatting", "document body", "status bar"],
            common_views={
                "editing": ["document", "text editing", "word count", "page layout"],
                "review": ["track changes", "comments", "reviewing pane"],
                "references": ["table of contents", "citations", "footnotes"]
            }
        )
        
        signatures["microsoft_excel"] = AppSignature(
            name="Microsoft Excel",
            patterns=["microsoft excel", "excel spreadsheet", "excel workbook", "office excel"],
            ui_elements=["cell", "formula bar", "worksheet", "column header", "row number"],
            common_views={
                "data_entry": ["cells", "worksheet", "data entry"],
                "formulas": ["formula bar", "cell references", "functions"],
                "charts": ["chart tools", "data visualization", "graph"]
            }
        )
        
        signatures["microsoft_powerpoint"] = AppSignature(
            name="Microsoft PowerPoint",
            patterns=["microsoft powerpoint", "powerpoint presentation", "slideshow", "office powerpoint"],
            ui_elements=["slide", "slide sorter", "notes pane", "slide master"],
            common_views={
                "editing": ["slide editing", "content editing"],
                "slide_show": ["presenting", "slideshow view"],
                "outline": ["outline view", "slide thumbnails"]
            }
        )
        
        signatures["google_docs"] = AppSignature(
            name="Google Docs",
            patterns=["google docs", "google document", "docs.google.com"],
            ui_elements=["menu bar", "toolbar", "document body", "comment bubble"],
            common_views={
                "editing": ["document editing", "text document"],
                "suggesting": ["suggestion mode", "track changes"],
                "viewing": ["reading view", "published view"]
            }
        )
        
        signatures["google_sheets"] = AppSignature(
            name="Google Sheets",
            patterns=["google sheets", "google spreadsheet", "sheets.google.com"],
            ui_elements=["cell grid", "formula bar", "sheet tabs", "column letters"],
            common_views={
                "editing": ["cell editing", "formula entry"],
                "formulas": ["function list", "formula builder"],
                "charts": ["chart editor", "visualization"]
            }
        )
        
        signatures["google_slides"] = AppSignature(
            name="Google Slides",
            patterns=["google slides", "google presentation", "slides.google.com"],
            ui_elements=["slide canvas", "slide navigator", "toolbar", "shape menu"],
            common_views={
                "editing": ["slide editing", "content editing"],
                "presenting": ["presentation mode", "slideshow"],
                "animations": ["transitions", "motion effects"]
            }
        )
        
        # Email Applications
        signatures["gmail"] = AppSignature(
            name="Gmail",
            patterns=["gmail", "google mail", "mail.google.com", "gmail interface"],
            ui_elements=["compose button", "inbox", "sidebar", "email list", "search mail"],
            common_views={
                "inbox": ["inbox view", "email list", "primary tab"],
                "compose": ["compose email", "new message", "recipients field"],
                "reading": ["email content", "reading email", "message body"],
                "settings": ["gmail settings", "account settings", "preferences"]
            }
        )
        
        signatures["outlook"] = AppSignature(
            name="Microsoft Outlook",
            patterns=["microsoft outlook", "outlook email", "outlook calendar", "outlook.office"],
            ui_elements=["ribbon", "folder list", "message list", "reading pane"],
            common_views={
                "inbox": ["mail view", "inbox folder", "message list"],
                "calendar": ["calendar view", "appointments", "schedule"],
                "compose": ["new email", "message editor", "to field"],
                "contacts": ["address book", "contact list", "people"]
            }
        )
        
        # Browsers
        signatures["chrome"] = AppSignature(
            name="Google Chrome",
            patterns=["google chrome", "chrome browser", "chrome window"],
            ui_elements=["address bar", "tab bar", "bookmark bar", "extensions"],
            common_views={
                "webpage": ["web content", "website", "webpage"],
                "settings": ["chrome settings", "preferences"],
                "history": ["browsing history", "recent sites"],
                "downloads": ["downloaded files", "download manager"]
            }
        )
        
        signatures["firefox"] = AppSignature(
            name="Mozilla Firefox",
            patterns=["mozilla firefox", "firefox browser", "firefox window"],
            ui_elements=["address bar", "tab bar", "bookmark toolbar", "firefox menu"],
            common_views={
                "webpage": ["web content", "website", "webpage"],
                "settings": ["firefox preferences", "options"],
                "library": ["history", "bookmarks", "downloads"],
                "addons": ["extensions", "plugins", "firefox add-ons"]
            }
        )
        
        signatures["safari"] = AppSignature(
            name="Safari",
            patterns=["safari browser", "safari window", "apple safari"],
            ui_elements=["smart search field", "tab bar", "bookmarks", "sidebar"],
            common_views={
                "webpage": ["web content", "website", "webpage"],
                "settings": ["safari preferences", "settings"],
                "reading_list": ["reading list sidebar", "saved articles"],
                "tabs": ["tab overview", "tab grid"]
            }
        )
        
        # Code & Development
        signatures["vscode"] = AppSignature(
            name="Visual Studio Code",
            patterns=["visual studio code", "vscode", "vs code", "code editor"],
            ui_elements=["file explorer", "editor", "terminal", "status bar", "activity bar"],
            common_views={
                "editing": ["code editor", "text editor", "editing code"],
                "terminal": ["integrated terminal", "command line"],
                "debugging": ["debugger", "variables", "watch", "breakpoints"],
                "extensions": ["extensions view", "marketplace"]
            }
        )
        
        signatures["sublime_text"] = AppSignature(
            name="Sublime Text",
            patterns=["sublime text", "sublime editor"],
            ui_elements=["tab bar", "sidebar", "minimap", "status bar"],
            common_views={
                "editing": ["text editing", "code editing"],
                "find_replace": ["search panel", "find", "replace"],
                "multi_select": ["multiple cursors", "multiple selections"]
            }
        )
        
        signatures["jetbrains_ide"] = AppSignature(
            name="JetBrains IDE",
            patterns=["intellij", "pycharm", "webstorm", "phpstorm", "rubymine", "goland", "rider", "clion", "jetbrains"],
            ui_elements=["project view", "editor", "tool window", "navigation bar", "run button"],
            common_views={
                "editing": ["code editor", "source code"],
                "debugging": ["debugger", "variables", "watches"],
                "terminal": ["terminal window", "command line"],
                "project": ["project structure", "project tree"]
            }
        )
        
        # Communication & Collaboration
        signatures["slack"] = AppSignature(
            name="Slack",
            patterns=["slack", "slack workspace", "slack channel", "slack app"],
            ui_elements=["channel list", "message input", "workspace menu", "threads"],
            common_views={
                "channel": ["channel view", "message history", "channel topic"],
                "thread": ["thread view", "reply thread", "conversation thread"],
                "direct_message": ["direct message", "private message", "dm conversation"],
                "search": ["search results", "search panel", "message search"]
            }
        )
        
        signatures["teams"] = AppSignature(
            name="Microsoft Teams",
            patterns=["microsoft teams", "teams app", "teams meeting", "ms teams"],
            ui_elements=["team list", "channel list", "chat input", "activity feed"],
            common_views={
                "chat": ["conversation view", "messaging", "chat history"],
                "meeting": ["video call", "meeting controls", "participants"],
                "files": ["files tab", "document library", "shared files"],
                "activity": ["activity feed", "notifications", "mentions"]
            }
        )
        
        signatures["zoom"] = AppSignature(
            name="Zoom",
            patterns=["zoom", "zoom meeting", "zoom call", "zoom webinar"],
            ui_elements=["meeting controls", "participants panel", "chat panel", "video grid"],
            common_views={
                "meeting": ["video conference", "meeting room", "participants"],
                "webinar": ["webinar view", "attendee list", "presenter tools"],
                "waiting_room": ["waiting for host", "waiting room"],
                "settings": ["zoom settings", "preferences"]
            }
        )
        
        # Terminal & Command Line
        signatures["terminal"] = AppSignature(
            name="Terminal",
            patterns=["terminal", "command line", "shell", "bash", "console", "cmd", "powershell", "command prompt"],
            ui_elements=["command prompt", "text output", "terminal window"],
            common_views={
                "bash": ["bash shell", "unix terminal", "linux terminal"],
                "powershell": ["powershell console", "ps prompt"],
                "cmd": ["command prompt", "windows terminal", "cmd.exe"]
            }
        )
        
        # Design & Media
        signatures["photoshop"] = AppSignature(
            name="Adobe Photoshop",
            patterns=["photoshop", "adobe photoshop", "ps editor"],
            ui_elements=["layers panel", "tools panel", "properties panel", "canvas"],
            common_views={
                "editing": ["image editing", "photo manipulation"],
                "adjustment": ["adjustment layers", "image adjustments"],
                "selection": ["selection tools", "masking"],
                "painting": ["brush tools", "digital painting"]
            }
        )
        
        signatures["illustrator"] = AppSignature(
            name="Adobe Illustrator",
            patterns=["illustrator", "adobe illustrator", "ai editor", "vector editor"],
            ui_elements=["artboard", "tools panel", "layers panel", "properties panel"],
            common_views={
                "vector_editing": ["vector artwork", "path editing"],
                "drawing": ["pen tool", "shape creation"],
                "typography": ["text editing", "font settings"],
                "artboards": ["multiple artboards", "artboard navigation"]
            }
        )
        
        # Media Playback
        signatures["spotify"] = AppSignature(
            name="Spotify",
            patterns=["spotify", "spotify player", "music player", "spotify playlist"],
            ui_elements=["playback controls", "now playing", "playlist sidebar", "search bar"],
            common_views={
                "player": ["music player", "now playing view"],
                "browse": ["discover view", "browse categories"],
                "playlist": ["playlist view", "saved tracks"],
                "search": ["search results", "search view"]
            }
        )
        
        signatures["netflix"] = AppSignature(
            name="Netflix",
            patterns=["netflix", "netflix player", "streaming", "netflix browse"],
            ui_elements=["video player", "browse tiles", "profile selector", "categories"],
            common_views={
                "browse": ["content browse", "title selection"],
                "player": ["video player", "playback", "watching video"],
                "profile": ["profile selection", "who's watching"],
                "details": ["title details", "show information"]
            }
        )
        
        # Social Media
        signatures["facebook"] = AppSignature(
            name="Facebook",
            patterns=["facebook", "fb feed", "facebook timeline", "facebook.com"],
            ui_elements=["news feed", "post composer", "stories", "sidebar"],
            common_views={
                "feed": ["news feed", "home feed", "timeline"],
                "profile": ["profile page", "user profile"],
                "messages": ["messenger", "chat window"],
                "groups": ["group page", "group feed"]
            }
        )
        
        signatures["twitter"] = AppSignature(
            name="Twitter",
            patterns=["twitter", "tweet", "twitter feed", "twitter.com"],
            ui_elements=["tweet composer", "timeline", "explore tab", "notifications tab"],
            common_views={
                "home": ["home timeline", "feed", "tweets"],
                "profile": ["profile page", "user profile"],
                "explore": ["trending topics", "discover", "search"],
                "notifications": ["mentions", "activity", "notifications tab"]
            }
        )
        
        signatures["instagram"] = AppSignature(
            name="Instagram",
            patterns=["instagram", "ig feed", "instagram stories", "instagram.com"],
            ui_elements=["post grid", "stories bar", "navigation bar", "search tab"],
            common_views={
                "feed": ["home feed", "scrolling posts"],
                "profile": ["profile grid", "user profile"],
                "explore": ["discover page", "explore grid"],
                "reels": ["reels viewer", "short videos"]
            }
        )
        
        # File Management
        signatures["finder"] = AppSignature(
            name="Finder",
            patterns=["finder", "mac finder", "file browser", "finder window"],
            ui_elements=["sidebar", "file list", "toolbar", "path bar"],
            common_views={
                "icon_view": ["icon grid", "file icons"],
                "list_view": ["file list", "detailed list"],
                "column_view": ["column browser", "hierarchical view"],
                "gallery_view": ["media preview", "large previews"]
            }
        )
        
        signatures["file_explorer"] = AppSignature(
            name="File Explorer",
            patterns=["file explorer", "windows explorer", "explorer window", "this pc"],
            ui_elements=["navigation pane", "file list", "address bar", "ribbon"],
            common_views={
                "file_view": ["file list", "folder contents"],
                "navigation": ["folder tree", "directory hierarchy"],
                "search": ["search results", "file search"],
                "quick_access": ["quick access pins", "favorites"]
            }
        )
        
        # Chat and Messaging
        signatures["whatsapp"] = AppSignature(
            name="WhatsApp",
            patterns=["whatsapp", "whatsapp web", "whatsapp chat", "web.whatsapp.com"],
            ui_elements=["chat list", "message input", "user profile", "status updates"],
            common_views={
                "chat": ["conversation view", "message history"],
                "contact_list": ["chat list", "contact search"],
                "settings": ["preferences", "profile settings"],
                "media": ["media gallery", "photos view"]
            }
        )
        
        signatures["telegram"] = AppSignature(
            name="Telegram",
            patterns=["telegram", "telegram desktop", "telegram chat", "telegram web"],
            ui_elements=["chat list", "message area", "sidebar", "search"],
            common_views={
                "chat": ["message view", "conversation"],
                "contact_list": ["contact search", "chat list"],
                "settings": ["preferences", "profile settings"],
                "calls": ["call history", "voice calls"]
            }
        )
        
        # SaaS Platforms
        signatures["jira"] = AppSignature(
            name="Jira",
            patterns=["jira", "atlassian jira", "jira board", "jira project"],
            ui_elements=["navigation bar", "board view", "issue details", "backlog"],
            common_views={
                "board": ["kanban board", "sprint board", "backlog"],
                "issue": ["issue details", "ticket view"],
                "backlog": ["backlog view", "product backlog"],
                "dashboard": ["project dashboard", "overview metrics"]
            }
        )
        
        signatures["trello"] = AppSignature(
            name="Trello",
            patterns=["trello", "trello board", "trello card", "trello.com"],
            ui_elements=["board", "list", "card", "add button"],
            common_views={
                "board": ["board view", "lists and cards"],
                "card": ["card details", "card editing"],
                "menu": ["board menu", "sidebar menu"],
                "settings": ["board settings", "board preferences"]
            }
        )
        
        # Developer Tools
        signatures["github"] = AppSignature(
            name="GitHub",
            patterns=["github", "github.com", "git repository", "github repo"],
            ui_elements=["repo header", "file list", "code view", "tabs"],
            common_views={
                "code": ["repository view", "file browser"],
                "issues": ["issue list", "issue details"],
                "pull_requests": ["PR list", "code review"],
                "actions": ["workflows", "CI/CD pipelines"]
            }
        )
        
        signatures["gitlab"] = AppSignature(
            name="GitLab",
            patterns=["gitlab", "gitlab.com", "gitlab project", "gitlab repo"],
            ui_elements=["project sidebar", "file list", "pipeline graph", "merge requests"],
            common_views={
                "project": ["project overview", "repository"],
                "issues": ["issue tracker", "issue board"],
                "merge_requests": ["MR list", "code review"],
                "ci_cd": ["pipelines", "CI/CD view"]
            }
        )
        
        # Note-taking
        signatures["evernote"] = AppSignature(
            name="Evernote",
            patterns=["evernote", "evernote app", "evernote editor"],
            ui_elements=["note editor", "notebook list", "tags panel", "search box"],
            common_views={
                "editor": ["note editing", "content creation"],
                "notebook": ["notebook view", "note list"],
                "search": ["search results", "filtered notes"],
                "settings": ["account settings", "preferences"]
            }
        )
        
        signatures["onenote"] = AppSignature(
            name="Microsoft OneNote",
            patterns=["onenote", "microsoft onenote", "onenote notebook"],
            ui_elements=["ribbon", "page tabs", "section tabs", "notebook dropdown"],
            common_views={
                "page": ["note page", "content editing"],
                "section": ["section view", "page list"],
                "search": ["search results", "content search"],
                "drawing": ["ink tools", "drawing panel"]
            }
        )
        
        signatures["notion"] = AppSignature(
            name="Notion",
            patterns=["notion", "notion workspace", "notion page", "notion.so"],
            ui_elements=["sidebar", "page content", "database", "slash commands"],
            common_views={
                "page": ["page editor", "content blocks"],
                "database": ["database view", "table view", "board view"],
                "sidebar": ["workspace navigation", "page hierarchy"],
                "settings": ["settings", "workspace settings"]
            }
        )
        
        signatures["airtable"] = AppSignature(
            name="Airtable",
            patterns=["airtable", "airtable base", "airtable table", "airtable.com"],
            ui_elements=["grid view", "record fields", "view selector", "toolbar"],
            common_views={
                "grid": ["table view", "grid view", "records"],
                "kanban": ["kanban board", "card view"],
                "form": ["form view", "data entry"],
                "gallery": ["gallery view", "large cards"]
            }
        )
        
        # Add 10 more modern web applications (2025)
        signatures["figma"] = AppSignature(
            name="Figma",
            patterns=["figma", "figma design", "figma editor", "figma.com"],
            ui_elements=["canvas", "layers panel", "properties panel", "toolbar"],
            common_views={
                "design": ["canvas view", "artboard editing"],
                "prototype": ["prototype view", "interaction design"],
                "developer": ["developer handoff", "inspect view"],
                "community": ["figma community", "template browser"]
            }
        )
        
        signatures["linear"] = AppSignature(
            name="Linear",
            patterns=["linear", "linear app", "linear.app", "issue tracking"],
            ui_elements=["sidebar", "issue list", "issue details", "filters"],
            common_views={
                "issues": ["issue list", "backlog view"],
                "board": ["kanban board", "issue board"],
                "roadmap": ["roadmap view", "timeline"],
                "inbox": ["notifications", "activity feed"]
            }
        )
        
        signatures["coda"] = AppSignature(
            name="Coda",
            patterns=["coda", "coda.io", "coda document", "coda editor"],
            ui_elements=["page sidebar", "editor canvas", "formula bar", "doc outline"],
            common_views={
                "editor": ["document editor", "page view"],
                "table": ["data table", "database view"],
                "formula": ["formula editing", "calculation"],
                "canvas": ["canvas view", "drag-and-drop layout"]
            }
        )
        
        signatures["miro"] = AppSignature(
            name="Miro",
            patterns=["miro", "miro board", "whiteboard", "miro.com"],
            ui_elements=["canvas", "toolbar", "minimap", "collaboration cursor"],
            common_views={
                "board": ["whiteboard view", "infinite canvas"],
                "presentation": ["presentation mode", "frame view"],
                "template": ["template selection", "starting point"],
                "dashboard": ["board gallery", "workspace view"]
            }
        )
        
        signatures["discord"] = AppSignature(
            name="Discord",
            patterns=["discord", "discord server", "discord channel", "discord.com"],
            ui_elements=["server list", "channel list", "message area", "member list"],
            common_views={
                "text_channel": ["chat channel", "text conversation"],
                "voice_channel": ["voice chat", "audio channel"],
                "direct_messages": ["private chat", "dm view"],
                "server_settings": ["server configuration", "server management"]
            }
        )
        
        # Productivity Tools
        signatures["calendar"] = AppSignature(
            name="Calendar App",
            patterns=["calendar", "appointment", "schedule", "google calendar", "apple calendar", "outlook calendar"],
            ui_elements=["month view", "week view", "day view", "appointment details"],
            common_views={
                "month": ["month grid", "month overview"],
                "week": ["week view", "weekly schedule"],
                "day": ["day view", "daily agenda"],
                "agenda": ["list view", "upcoming events"]
            }
        )
        
        # Operating System Interfaces
        signatures["mac_os"] = AppSignature(
            name="macOS Desktop",
            patterns=["macos desktop", "mac desktop", "apple desktop", "finder desktop"],
            ui_elements=["desktop icons", "dock", "menu bar", "spotlight search"],
            common_views={
                "desktop": ["desktop view", "background", "desktop icons"],
                "launchpad": ["app grid", "application launcher"],
                "mission_control": ["window overview", "spaces view"],
                "system_preferences": ["settings panels", "system configuration"]
            }
        )
        
        signatures["windows"] = AppSignature(
            name="Windows Desktop",
            patterns=["windows desktop", "windows start menu", "windows taskbar"],
            ui_elements=["desktop icons", "taskbar", "start menu", "action center"],
            common_views={
                "desktop": ["desktop background", "desktop icons"],
                "start": ["start menu", "app list"],
                "task_view": ["timeline", "virtual desktops"],
                "settings": ["windows settings", "control panel"]
            }
        )
        
        signatures["linux_desktop"] = AppSignature(
            name="Linux Desktop",
            patterns=["linux desktop", "gnome", "kde", "ubuntu desktop", "linux mint"],
            ui_elements=["desktop icons", "panel", "dock", "application menu"],
            common_views={
                "desktop": ["desktop view", "workspace"],
                "activities": ["activities overview", "workspace switcher"],
                "application_grid": ["app drawer", "application launcher"],
                "settings": ["system settings", "preferences"]
            }
        )
        
        return signatures
    
    async def detect_application(self, image_path: str) -> DetectionResult:
        """
        Detect application from an image file with comprehensive recognition.
        
        Args:
            image_path: Path to the screenshot image
            
        Returns:
            DetectionResult: Structured detection results
        """
        try:
            # Load and prepare the image
            logger.info(f"Loading image from {image_path}")
            image = Image.open(image_path)
            
            # Generate image hash for caching
            import hashlib
            img_hash = hashlib.md5(image.tobytes()).hexdigest()
            
            # Convert image to base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            # Send to LLaVA with enhanced prompt for application detection
            start_time = time.time()
            llava_response = await self._analyze_with_llava(img_base64)
            elapsed_time = time.time() - start_time
            
            # Extract application data with improved pattern matching
            app_data = self._parse_response(llava_response)
            
            # Add additional detection using application signatures
            app_data = self._enhance_with_signatures(app_data, llava_response)
            
            # Create detection result
            result = DetectionResult(
                application=app_data.get("application", "Unknown"),
                confidence=float(app_data.get("confidence", 0.0)),
                category=app_data.get("category", ""),
                view=app_data.get("view", ""),
                workflow=app_data.get("workflow", ""),
                ui_elements=app_data.get("ui_elements", []),
                raw_analysis=llava_response,
                analysis_time=elapsed_time,
                screenshot_hash=img_hash
            )
            
            # Save result to file
            self._save_result(result)
            
            # Log detection summary
            logger.info(f"Application detected: {result.application} (confidence: {result.confidence:.2f})")
            logger.info(f"Category: {result.category}")
            logger.info(f"View: {result.view}")
            logger.info(f"Workflow: {result.workflow}")
            logger.info(f"Analysis time: {result.analysis_time:.2f} seconds")
            
            return result
        
        except Exception as e:
            logger.error(f"Error in detect_application: {e}")
            return DetectionResult(
                application="Error",
                raw_analysis=f"Error: {str(e)}"
            )
    
    async def _analyze_with_llava(self, img_base64: str) -> str:
        """
        Analyze the image with LLaVA using enhanced prompt for comprehensive app detection.
        
        Args:
            img_base64: Base64 encoded image
            
        Returns:
            str: The full textual analysis from LLaVA
        """
        # Prepare the message for LLaVA with enhanced application detection prompt
        messages = [
            {
                "role": "system",
                "content": """You are an expert screen content analyzer specializing in application detection for ALL types of applications. IMPORTANT: Your primary goal is to accurately identify any application the user is using with as much detail as possible.

When given a screen capture:

1. IDENTIFY THE EXACT APPLICATION: Determine the specific application name (not just the category). Be specific - for example, say "Microsoft Word" not just "word processor" or "Visual Studio Code" not just "code editor".

2. Categorize the application type (choose from: productivity, communication, development, media, web browser, design, system, office, social media, utility, or other)

3. Detect the specific view or mode within the application (e.g., inbox view in Gmail, editing mode in Word, repository view in GitHub)

4. Identify major UI components and their functions (navigation elements, content areas, toolbars, etc)

5. Determine what the user is doing in the application - their current task or workflow stage

6. For browsers, identify the specific website or web application being used

7. For document-based applications, note the type of content being worked on (code, spreadsheet, document, email, etc)

8. Look for distinctive UI patterns that uniquely identify this application (e.g., ribbon in Office apps, sidebar in Notion, board view in Trello, etc)

When you respond, use this exact format:
- APPLICATION: [Full application name - be specific]
- CATEGORY: [Application category]
- VIEW: [Current view or mode]
- WORKFLOW: [What the user is doing]
- UI ELEMENTS: [List key interface elements]

IMPORTANT NOTES:
- Focus on identifying the SPECIFIC application, not just its category
- Be precise about application names (e.g., "Visual Studio Code" not just "code editor")
- Don't just guess based on vague patterns - look for distinctive UI elements and layouts
- For browser-based applications, identify both the browser AND the specific web application"""
            },
            {
                "role": "user",
                "content": "What application am I using in this screenshot? Please identify the exact application name, its category, the current view, and what I appear to be doing."
            }
        ]
        
        # Prepare the payload
        payload = {
            "model": self.llava_model,
            "messages": messages,
            "images": [img_base64],
            "temperature": 0.2,
            "stream": True
        }
        
        logger.info("Sending request to LLaVA API for comprehensive application detection...")
        
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
                        line_str = line.decode('utf-8').strip()
                        if not line_str:
                            continue
                            
                        # Parse the JSON
                        try:
                            chunk = json.loads(line_str)
                            if 'message' in chunk and 'content' in chunk['message']:
                                content = chunk['message']['content']
                                full_response += content
                                # Print partial responses for interactivity
                                print(content, end="", flush=True)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON: {line_str[:50]}...")
                            
                    print("\n")  # New line after streaming completes
                    return full_response
                    
        except asyncio.TimeoutError:
            logger.error(f"LLaVA request timed out after {self.llava_timeout}s")
            return "Error: LLaVA request timed out"
        except Exception as e:
            logger.error(f"Error in LLaVA analysis: {e}")
            return f"Error: {str(e)}"
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLaVA response using enhanced patterns for all application types.
        
        Args:
            response_text: The raw text response from LLaVA
            
        Returns:
            Dict containing structured application data
        """
        result = {
            "application": "Unknown",
            "confidence": 0.5,  # Default confidence level
            "category": "",
            "view": "",
            "workflow": "",
            "ui_elements": []
        }
        
        # Process the response with more comprehensive patterns
        try:
            # Extract application name with stronger patterns
            app_patterns = [
                r"APPLICATION:\s*([^\n]+)",
                r"Application:?\s*([^\n\.]+)",
                r"The application (?:is|appears to be|looks like|shown)(?:is)?\s*([^\n\.]+)",
                r"(?:You are|User is|I can see) (?:using|in|on|working with)\s*([^\n\.]+)",
                r"This is (?:the|a|an)\s*([^\n\.]+?)(?:\s+interface|application|app|window|screen|view|\.|$)",
                r"This (?:appears to be|looks like|is) (?:the|a|an)\s*([^\n\.]+?)(?:\s+interface|application|app|window|screen|view|\.|$)",
                r"I can identify this as\s*([^\n\.]+)",
                r"The screenshot shows\s*(?:the|a|an)\s*([^\n\.]+?)(?:\s+interface|application|app|window|screen|view|\.|$)",
                r"The user is (?:working with|using|in)\s*([^\n\.]+)"
            ]
            
            # Extract category with clearer patterns
            category_patterns = [
                r"CATEGORY:\s*([^\n]+)",
                r"Category:?\s*([^\n\.]+)",
                r"This (?:is|belongs to|falls under) (?:the|a)?\s*([^\n\.]+?)(?:\s+category|type|application|app|\.|$)",
                r"Type of application:\s*([^\n\.]+)",
                r"Classification:\s*([^\n\.]+)"
            ]
            
            # Extract view with expanded patterns
            view_patterns = [
                r"VIEW:\s*([^\n]+)",
                r"View:?\s*([^\n\.]+)",
                r"(?:Current view|Mode|Page|Section):\s*([^\n\.]+)",
                r"The user is in the\s*([^\n\.]+?)(?:\s+view|mode|page|section|area|\.|$)",
                r"This is the\s*([^\n\.]+?)(?:\s+view|mode|page|section|interface|\.|$)",
                r"The (?:current|active) (?:view|mode|page|screen) is\s*([^\n\.]+)"
            ]
            
            # Extract workflow with comprehensive patterns
            workflow_patterns = [
                r"WORKFLOW:\s*([^\n]+)",
                r"Workflow:?\s*([^\n\.]+)",
                r"Task:?\s*([^\n\.]+)",
                r"(?:The user is|You are)\s*([^\n\.]+?(?:ing|ing a|ing the)[^\n\.]+)",
                r"(?:The user|You) (?:appears to be|seems to be|is|are)\s*([^\n\.]+?(?:ing|ing a|ing the)[^\n\.]+)",
                r"User activity:\s*([^\n\.]+)",
                r"Current action:\s*([^\n\.]+)",
                r"User is in the process of\s*([^\n\.]+)"
            ]
            
            # Try all patterns for application detection
            for pattern in app_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    app_name = match.group(1).strip()
                    if app_name and app_name.lower() not in ["unknown", "unclear", "not clear", "not visible"]:
                        result["application"] = app_name
                        # Boost confidence for structured format
                        if pattern.startswith("APPLICATION"):
                            result["confidence"] = 0.9
                        else:
                            result["confidence"] = 0.7
                        break
            
            # Try all patterns for category detection
            for pattern in category_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    category = match.group(1).strip()
                    if category and category.lower() not in ["unknown", "unclear", "not clear", "not visible"]:
                        result["category"] = category
                        break
            
            # Try all patterns for view detection
            for pattern in view_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    view = match.group(1).strip()
                    if view and view.lower() not in ["unknown", "unclear", "not clear", "not visible"]:
                        result["view"] = view
                        break
            
            # Try all patterns for workflow detection
            for pattern in workflow_patterns:
                match = re.search(pattern, response_text, re.IGNORECASE)
                if match:
                    workflow = match.group(1).strip()
                    if workflow and workflow.lower() not in ["unknown", "unclear", "not clear", "not visible"]:
                        result["workflow"] = workflow
                        break
            
            # Extract UI elements from formatted or unformatted lists
            ui_elements = []
            ui_section_match = re.search(r"UI ELEMENTS:?\s*(.+?)(?:\n\n|\n[A-Z-]+:|\Z)", response_text, re.DOTALL | re.IGNORECASE)
            
            if ui_section_match:
                ui_text = ui_section_match.group(1).strip()
                
                # Split by list items (bullets, dashes, or numbers)
                if "-" in ui_text or "•" in ui_text or "*" in ui_text or re.search(r"\d+\.", ui_text):
                    element_lines = re.split(r"\n+", ui_text)
                    for line in element_lines:
                        line = line.strip()
                        if not line:
                            continue
                            
                        # Clean up bullet points and numbers
                        element = re.sub(r"^[\s•\-\*]+\s*", "", line)
                        element = re.sub(r"^\d+\.\s*", "", element)
                        
                        if element:
                            ui_elements.append({"element": element})
                else:
                    # If no bullet points, try comma-separated list
                    elements = [e.strip() for e in ui_text.split(",")]
                    for element in elements:
                        if element:
                            ui_elements.append({"element": element})
            
            result["ui_elements"] = ui_elements
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing LLaVA response: {e}")
            return result
    
    def _enhance_with_signatures(self, app_data: Dict[str, Any], full_text: str) -> Dict[str, Any]:
        """
        Enhance application detection using the signature database.
        
        Args:
            app_data: Initial application data from basic parsing
            full_text: Full LLaVA response text
            
        Returns:
            Enhanced application data with signature-based detection
        """
        # If we already have high confidence, no need to enhance
        if app_data.get("confidence", 0) >= 0.9 and app_data.get("application") != "Unknown":
            return app_data
        
        # Convert text to lowercase for matching
        lower_text = full_text.lower()
        
        # Track potential matches
        matches = []
        
        # Check each signature against the response
        for app_id, signature in self.app_signatures.items():
            match_score = 0
            total_patterns = len(signature.patterns)
            matched_patterns = 0
            
            # Check for name patterns
            for pattern in signature.patterns:
                if pattern.lower() in lower_text:
                    matched_patterns += 1
            
            # Calculate pattern match score (0-0.5)
            if total_patterns > 0:
                pattern_score = (matched_patterns / total_patterns) * 0.5
                match_score += pattern_score
            
            # Check for UI elements
            ui_matched = 0
            for ui_element in signature.ui_elements:
                if ui_element.lower() in lower_text:
                    ui_matched += 1
            
            # Calculate UI element match score (0-0.3)
            if len(signature.ui_elements) > 0:
                ui_score = (ui_matched / len(signature.ui_elements)) * 0.3
                match_score += ui_score
            
            # Check for view patterns (0-0.2)
            view_matched = False
            for view_category, view_patterns in signature.common_views.items():
                for view_pattern in view_patterns:
                    if view_pattern.lower() in lower_text:
                        view_matched = True
                        # If view matches but we don't have a view yet, add it
                        if not app_data.get("view") and view_category:
                            app_data["view"] = view_category.replace("_", " ")
                        break
                if view_matched:
                    match_score += 0.2
                    break
            
            # Add to potential matches if score is significant
            if match_score > 0.2:  # Require at least some meaningful match
                matches.append({
                    "app_id": app_id,
                    "name": signature.name,
                    "score": match_score
                })
        
        # Sort matches by score
        matches.sort(key=lambda x: x["score"], reverse=True)
        
        # If we have matches, use the best one
        if matches:
            best_match = matches[0]
            
            # Only override if the confidence is higher
            if best_match["score"] > app_data.get("confidence", 0):
                app_data["application"] = best_match["name"]
                app_data["confidence"] = best_match["score"]
                
                # Add category if missing
                if not app_data.get("category"):
                    # Derive category from app_id
                    category_map = {
                        "microsoft_word": "Office",
                        "microsoft_excel": "Office",
                        "google_docs": "Office",
                        "gmail": "Communication",
                        "outlook": "Communication",
                        "chrome": "Web Browser",
                        "firefox": "Web Browser",
                        "safari": "Web Browser",
                        "vscode": "Development",
                        "sublime_text": "Development",
                        "jetbrains_ide": "Development",
                        "slack": "Communication",
                        "teams": "Communication",
                        "zoom": "Communication",
                        "terminal": "Development",
                        "photoshop": "Design",
                        "illustrator": "Design",
                        "spotify": "Media",
                        "netflix": "Media",
                        "facebook": "Social Media",
                        "twitter": "Social Media",
                        "instagram": "Social Media",
                        "finder": "Utility",
                        "file_explorer": "Utility",
                        "whatsapp": "Communication",
                        "telegram": "Communication",
                        "jira": "Productivity",
                        "trello": "Productivity",
                        "github": "Development",
                        "gitlab": "Development",
                        "evernote": "Productivity",
                        "onenote": "Productivity",
                        "notion": "Productivity",
                        "airtable": "Productivity",
                        "figma": "Design",
                        "linear": "Productivity",
                        "coda": "Productivity",
                        "miro": "Productivity",
                        "discord": "Communication",
                        "calendar": "Productivity",
                        "mac_os": "System",
                        "windows": "System",
                        "linux_desktop": "System"
                    }
                    
                    app_data["category"] = category_map.get(best_match["app_id"], "Other")
            
            # Add debug info
            logger.debug(f"Signature matches: {matches[:3]}")
        
        return app_data
    
    def _save_result(self, result: DetectionResult):
        """Save detection result to a JSON file."""
        try:
            # Create output filename based on timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{self.results_dir}/detection_{timestamp}.json"
            
            # Convert to dict for serialization
            result_dict = asdict(result)
            
            with open(filename, 'w') as f:
                json.dump(result_dict, f, indent=2)
                
            logger.info(f"Saved detection result to {filename}")
            
            # Also save as latest.json for easy access
            with open(f"{self.results_dir}/latest.json", 'w') as f:
                json.dump(result_dict, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving detection result: {e}")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Application Detection")
    parser.add_argument("image_path", help="Path to screenshot image")
    parser.add_argument("--llava-url", default="http://localhost:11434", help="URL for Ollama API (default: http://localhost:11434)")
    parser.add_argument("--save-dir", default="results/app_detection", help="Directory to save results (default: results/app_detection)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image_path):
        print(f"Error: Image file '{args.image_path}' not found")
        return 1
    
    print(f"Analyzing screenshot: {args.image_path}")
    print("Starting enhanced application detection...\n")
    
    detector = EnhancedAppDetector(llava_url=args.llava_url)
    detector.results_dir = args.save_dir
    
    # Run detection
    result = await detector.detect_application(args.image_path)
    
    # Print formatted results
    print("\n===== DETECTION RESULTS =====")
    print(f"Application: {result.application}")
    print(f"Confidence:  {result.confidence:.2f}")
    print(f"Category:    {result.category}")
    print(f"View:        {result.view}")
    print(f"Workflow:    {result.workflow}")
    print(f"Analysis time: {result.analysis_time:.2f} seconds")
    print("-----------------------------")
    print("UI Elements:")
    for ui in result.ui_elements:
        print(f"  - {ui['element']}")
    print("=============================")
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