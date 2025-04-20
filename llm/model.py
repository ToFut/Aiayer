"""
Enhanced Local LLM Integration Module
Provides comprehensive semantic understanding of sensor inputs.
"""

import os
import json
import logging
import asyncio
import time
import subprocess
import aiohttp
import psutil
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class CaptureResult:
    """Result of a screen capture operation."""
    text: str
    has_images: bool
    has_videos: bool
    timestamp: float
    metadata: Dict[str, Any]

@dataclass
class UserContext:
    """Comprehensive understanding of user's current context and activities."""
    primary_activity: str
    activity_context: Dict[str, Any]
    focus_areas: List[str]
    technical_context: Dict[str, Any]
    user_intent: str
    suggested_actions: List[str]
    system_state: Dict[str, Any]
    confidence_score: float
    timestamp: float
    browser_context: Optional[Dict[str, Any]] = None
    screen_context: Optional[Dict[str, Any]] = None

class LocalLLM:
    """Enhanced LLM interface for comprehensive user understanding across all sensors."""
    
    def __init__(self, model_name: str = "mistral"):
        self.model_name = model_name
        self.initialized = False
        self.logger = logging.getLogger(__name__)
        self._context_history = []
        self._max_history = 10
        self._last_analysis = None
        self._session = None
        
    async def initialize(self) -> bool:
        """Initialize the LLM service and create HTTP session."""
        try:
            # Check if model is available
            result = subprocess.run(
                ["ollama", "list"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if self.model_name in result.stdout:
                self.initialized = True
                self._session = aiohttp.ClientSession()
                self.logger.info("LLM service initialized successfully")
                return True
            else:
                self.logger.error(f"Model {self.model_name} not found in Ollama")
                return False
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM: {str(e)}")
            return False

    async def analyze_sensor_data(self, sensor_data: Dict[str, Any]) -> UserContext:
        """Analyze data from all sensors to understand user context."""
        if not self.initialized:
            if not await self.initialize():
                return self._get_default_context()

        try:
            # Prepare comprehensive prompt from all sensor data
            prompt = self._prepare_comprehensive_prompt(sensor_data)
            
            # Get LLM response
            response = await self._get_llm_response(prompt)
            
            # Parse and validate response
            understanding = self._parse_response(response)
            
            # Add system state
            understanding.system_state = self._get_system_state()
            
            # Add browser and screen context
            understanding.browser_context = sensor_data.get('browser', {})
            understanding.screen_context = sensor_data.get('screen', {})
            
            # Update context history
            self._update_context_history(understanding)
            
            return understanding
            
        except Exception as e:
            self.logger.error(f"Error during analysis: {str(e)}")
            return self._get_default_context()

    def _prepare_comprehensive_prompt(self, sensor_data: Dict[str, Any]) -> str:
        """Prepare a comprehensive prompt combining data from all sensors."""
        # Extract data from different sensors
        screen_data = sensor_data.get('screen', {})
        browser_data = sensor_data.get('browser', {})
        process_data = sensor_data.get('process', {})
        file_data = sensor_data.get('file', {})
        ai_data = sensor_data.get('ai', {})
        
        # Format the prompt
        prompt = f"""
        <s>[INST] You are an advanced AI assistant analyzing user's current context and activities.
        Analyze the following data from multiple sensors and provide a comprehensive understanding:
        
        Screen Content:
        - Active Window: {screen_data.get('active_window', 'Unknown')}
        - Detected Text: {screen_data.get('detected_text', [])}
        - UI Elements: {screen_data.get('ui_elements', [])}
        
        Browser Activity:
        - Current URL: {browser_data.get('url', 'Unknown')}
        - Page Title: {browser_data.get('title', 'Unknown')}
        - Active Tab: {browser_data.get('active_tab', 'Unknown')}
        - Recent History: {browser_data.get('recent_history', [])}
        - Form Inputs: {browser_data.get('form_inputs', [])}
        
        Process Activity:
        - Active Processes: {process_data.get('active_processes', [])}
        - CPU Usage: {process_data.get('cpu_usage', 0)}%
        - Memory Usage: {process_data.get('memory_usage', 0)}%
        
        File Activity:
        - Recent Files: {file_data.get('recent_files', [])}
        - File Changes: {file_data.get('file_changes', [])}
        
        AI Insights:
        - Patterns: {ai_data.get('patterns', [])}
        - Anomalies: {ai_data.get('anomalies', [])}
        - Predictions: {ai_data.get('predictions', [])}
        
        Provide a structured analysis including:
        1. Primary activity the user is engaged in (considering both screen and browser)
        2. Context of the activity (what they're doing and why)
        3. Key focus areas (what they're paying attention to)
        4. Technical context (tools, languages, frameworks being used)
        5. User's likely intent (what they're trying to accomplish)
        6. Suggested actions (what they might want to do next)
        
        Format the response as a JSON object with these fields.
        [/INST]</s>
        """
        
        return prompt.strip()

    async def _get_llm_response(self, prompt: str) -> str:
        """Get response from Ollama using async HTTP."""
        try:
            async with self._session.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': self.model_name,
                    'prompt': prompt,
                    'stream': False
                }
            ) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                result = await response.json()
                return result['response']
                
        except Exception as e:
            self.logger.error(f"Error getting LLM response: {str(e)}")
            raise

    def _parse_response(self, response: str) -> UserContext:
        """Parse and validate the LLM response."""
        try:
            # Parse JSON response
            result = json.loads(response)
            
            # Create UserContext object
            return UserContext(
                primary_activity=result.get('primary_activity', 'Unknown'),
                activity_context=result.get('activity_context', {}),
                focus_areas=result.get('focus_areas', []),
                technical_context=result.get('technical_context', {}),
                user_intent=result.get('user_intent', 'Unknown'),
                suggested_actions=result.get('suggested_actions', []),
                system_state={},  # Will be filled by caller
                confidence_score=result.get('confidence_score', 0.5),
                timestamp=time.time()
            )
            
        except json.JSONDecodeError:
            self.logger.error("Invalid JSON response from LLM")
            return self._get_default_context()

    def _get_system_state(self) -> Dict[str, Any]:
        """Get current system state."""
        return {
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict(),
            'active_processes': len(psutil.pids()),
            'timestamp': datetime.now().isoformat()
        }

    def _update_context_history(self, context: UserContext):
        """Update context history with new understanding."""
        self._context_history.append(context)
        if len(self._context_history) > self._max_history:
            self._context_history.pop(0)

    def _get_default_context(self) -> UserContext:
        """Return a default context when analysis fails."""
        return UserContext(
            primary_activity='Unknown',
            activity_context={},
            focus_areas=[],
            technical_context={},
            user_intent='Unknown',
            suggested_actions=[],
            system_state=self._get_system_state(),
            confidence_score=0.0,
            timestamp=time.time()
        )

    async def close(self):
        """Clean up resources."""
        if self._session:
            await self._session.close()
            self._session = None

class LocalLLMAnalyzer(LocalLLM):
    """Specialized LLM analyzer for screen content."""
    
    def __init__(self, model_name: str = "mistral", timeout: int = 30):
        super().__init__(model_name)
        self.timeout = timeout
        self._cache = {}  # Simple in-memory cache
        self.logger = logging.getLogger(__name__)
        
    def _execute_llm_request(self, prompt: str) -> str:
        try:
            cmd = ["ollama", "run", self.model_name, "--timeout", str(self.timeout), prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
            if result.returncode != 0:
                self.logger.error(f"LLM request failed with return code {result.returncode}: {result.stderr}")
                return ""
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            self.logger.error(f"LLM request timed out after {self.timeout} seconds")
            return ""
        except Exception as e:
            self.logger.error(f"LLM request failed: {str(e)}")
            return ""

    async def analyze_screen_content(self, result: CaptureResult) -> Dict[str, Any]:
        """Analyze screen content using LLM."""
        # Build a simpler, more focused prompt
        prompt = "Analyze this screen content and provide a concise JSON response:\n\n"
        
        # Add regions information
        for region in result.regions:
            prompt += f"Region ({region.region_type}): {region.content}\n"
        
        # Add visual patterns if available
        if result.visual_patterns:
            prompt += "\nVisual Patterns:\n"
            for pattern in result.visual_patterns:
                prompt += f"- {pattern.pattern_type} (confidence: {pattern.confidence:.2f})\n"

        prompt += """
Please analyze the content and respond with a JSON object containing:
{
    "activity_context": {
        "main_activity": "brief description",
        "app_context": "application name/type",
        "user_focus": "current focus"
    },
    "technical_analysis": {
        "languages": ["detected programming languages"],
        "libraries": ["detected libraries/frameworks"],
        "patterns": ["identified patterns"]
    },
    "ui_ux_analysis": {
        "interface_elements": ["UI elements found"],
        "navigation": ["navigation structure"],
        "interaction_patterns": ["interaction patterns"]
    },
    "content_structure": {
        "organization": "content organization",
        "sections": ["main sections"],
        "hierarchy": ["hierarchical structure"]
    },
    "semantic_understanding": {
        "topics": ["main topics"],
        "concepts": ["key concepts"],
        "relationships": ["relationships found"]
    },
    "suggestions": ["improvement suggestions"]
}"""

        try:
            response = self._execute_llm_request(prompt)
            if not response:
                return self._get_default_screen_analysis()

            # Try to parse the response as JSON
            try:
                # Find the JSON part in the response
                start_idx = response.find('{')
                end_idx = response.rfind('}')
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response[start_idx:end_idx + 1]
                    analysis = json.loads(json_str)
                    return self._merge_with_defaults(analysis)
                else:
                    self.logger.error("No JSON found in response")
                    return self._get_default_screen_analysis()
            except json.JSONDecodeError:
                self.logger.error("Failed to parse LLM response as JSON")
                return self._get_default_screen_analysis()
                
        except Exception as e:
            self.logger.error(f"Screen content analysis failed: {str(e)}")
            return self._get_default_screen_analysis()

    def _merge_with_defaults(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Merge the analysis with default values to ensure all fields are present."""
        default = self._get_default_screen_analysis()
        
        # Helper function to merge nested dictionaries
        def merge_dict(source, target):
            for key, value in source.items():
                if key not in target:
                    target[key] = value
                elif isinstance(value, dict) and isinstance(target[key], dict):
                    merge_dict(value, target[key])
                elif isinstance(value, list) and isinstance(target[key], list):
                    if not target[key]:
                        target[key] = value
            return target

        return merge_dict(default, analysis)

    def _get_default_screen_analysis(self) -> Dict[str, Any]:
        """Return default analysis structure with unknown values."""
        return {
            "activity_context": {
                "main_activity": "unknown",
                "app_context": "unknown",
                "user_focus": "unknown"
            },
            "technical_analysis": {
                "languages": [],
                "libraries": [],
                "patterns": []
            },
            "ui_ux_analysis": {
                "interface_elements": [],
                "navigation": [],
                "interaction_patterns": []
            },
            "content_structure": {
                "organization": "unknown",
                "sections": [],
                "hierarchy": []
            },
            "semantic_understanding": {
                "topics": [],
                "concepts": [],
                "relationships": []
            },
            "suggestions": [
                "Analysis failed, please try again",
                "Check screen content quality",
                "Verify LLM service is running correctly"
            ]
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        llm = LocalLLM()
        if await llm.initialize():
            # Test with sample sensor data including browser
            context = {
                'screen': {
                    'active_window': 'Visual Studio Code',
                    'detected_text': ['main.py'],
                    'ui_elements': ['Code Editor', 'File Explorer']
                },
                'browser': {
                    'url': 'https://github.com/example/repo',
                    'title': 'Example Repository - GitHub',
                    'active_tab': 'Pull Requests',
                    'recent_history': [
                        'https://github.com/example/repo/pulls',
                        'https://github.com/example/repo/issues'
                    ],
                    'form_inputs': ['Search pull requests...']
                },
                'process': {
                    'active_processes': ['vscode', 'chrome'],
                    'cpu_usage': 30,
                    'memory_usage': 60
                },
                'file': {
                    'recent_files': ['main.py', 'README.md'],
                    'file_changes': ['Added new file', 'Modified existing file']
                },
                'ai': {
                    'patterns': ['Python', 'Code Editor', 'GitHub'],
                    'anomalies': [],
                    'predictions': ['User is working on a pull request']
                }
            }
            
            understanding = await llm.analyze_sensor_data(context)
            print("\nComprehensive Understanding:")
            print(f"Activity: {understanding.primary_activity}")
            print(f"Context: {understanding.activity_context}")
            print(f"Focus Areas: {', '.join(understanding.focus_areas)}")
            print(f"Technical Details: {understanding.technical_context}")
            print(f"User Intent: {understanding.user_intent}")
            print(f"Suggested Actions: {', '.join(understanding.suggested_actions)}")
            print(f"Browser Context: {understanding.browser_context}")
            print(f"Screen Context: {understanding.screen_context}")
            print(f"System State: {understanding.system_state}")
            print(f"Confidence Score: {understanding.confidence_score}")
    
    asyncio.run(test())