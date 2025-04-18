"""
Context Analysis Enhancement Strategy:

Current Limitations:
- Basic sensor data correlation
- Limited semantic understanding
- Static context interpretation

Proposed Improvements:
1. Deep Semantic Fusion
2. Predictive Context Mapping
3. Adaptive Learning Mechanism
"""
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime
import json
import asyncio
import numpy as np
from dataclasses import dataclass, field
import re

@dataclass
class ContextInsight:
    """Structured container for context insights with confidence scores"""
    current_activity: str
    context_summary: str
    potential_needs: List[str]
    attention_level: str
    confidence_score: float
    source_model: str
    timestamp: datetime = field(default_factory=datetime.now)
    raw_response: Dict = field(default_factory=dict)
    semantic_understanding: Dict = field(default_factory=dict)

class ModelOrchestrator:
    """
    Manages multiple local AI models and orchestrates their execution
    with adaptive model selection based on context complexity and performance history.
    """
    
    def __init__(self, models: Dict[str, Any], model_profiles: Optional[Dict[str, Dict]] = None):
        """
        Initialize the model orchestrator.
        
        Args:
            models: Dictionary of model instances (key: model_name, value: model_instance)
            model_profiles: Optional dictionary of model profiles containing capabilities and performance metrics
        """
        self.models = models
        self.model_profiles = model_profiles or {}
        self.performance_history = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize default model profiles if not provided
        for model_name in models:
            if model_name not in self.model_profiles:
                self.model_profiles[model_name] = {
                    "capabilities": {
                        "text_understanding": 0.5,
                        "visual_understanding": 0.3,
                        "contextual_reasoning": 0.5,
                        "memory_capacity": 0.5
                    },
                    "latency": 1.0,  # normalized latency score
                    "token_efficiency": 0.5  # efficiency in token usage
                }
            
            # Initialize performance history
            self.performance_history[model_name] = {
                "successful_executions": 0,
                "failed_executions": 0,
                "average_latency": 0.0,
                "average_confidence": 0.0
            }
    
    async def execute_model(self, model_name: str, prompt: str, system_prompt: str) -> Tuple[Dict, float]:
        """
        Execute a specific model with the given prompts.
        
        Args:
            model_name: Name of the model to execute
            prompt: User prompt to send to the model
            system_prompt: System prompt to send to the model
            
        Returns:
            Tuple of (model_response, execution_time)
        """
        model = self.models.get(model_name)
        if not model:
            self.logger.error(f"Model {model_name} not found")
            return {}, 0.0
            
        start_time = datetime.now()
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            # Support different model interfaces
            if hasattr(model, 'generate_response'):
                response = await model.generate_response(messages)
            elif hasattr(model, 'predict'):
                response = await model.predict(messages)
            elif hasattr(model, 'completion'):
                response = await model.completion(messages)
            else:
                response = await model(messages)  # Fallback to direct calling
                
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Update performance metrics
            self._update_performance_metrics(model_name, True, execution_time, 
                                           self._extract_confidence(response))
            
            return response, execution_time
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"Error executing model {model_name}: {e}")
            self._update_performance_metrics(model_name, False, execution_time, 0.0)
            return {}, execution_time
    
    def select_models_for_context(self, context_data: Dict, complexity: float = 0.5, 
                                  time_constraint: Optional[float] = None) -> List[str]:
        """
        Select appropriate models based on context complexity and time constraints.
        
        Args:
            context_data: Dictionary containing context information
            complexity: Estimated complexity of the current context (0.0-1.0)
            time_constraint: Optional time constraint in seconds
            
        Returns:
            List of model names to execute
        """
        # Calculate context profile to match with model capabilities
        context_profile = self._calculate_context_profile(context_data)
        
        # Calculate matching scores for each model
        model_scores = {}
        for model_name, profile in self.model_profiles.items():
            # Calculate capability match
            capability_score = sum(
                context_profile.get(cap, 0) * profile["capabilities"].get(cap, 0)
                for cap in set(context_profile) | set(profile["capabilities"])
            ) / len(set(context_profile) | set(profile["capabilities"]))
            
            # Factor in performance history
            perf = self.performance_history[model_name]
            total_executions = perf["successful_executions"] + perf["failed_executions"]
            reliability = perf["successful_executions"] / max(1, total_executions)
            
            # Calculate final score
            if time_constraint:
                # Prioritize faster models when time constrained
                speed_factor = 1.0 / max(0.1, profile["latency"])
                model_scores[model_name] = capability_score * 0.4 + reliability * 0.3 + speed_factor * 0.3
            else:
                model_scores[model_name] = capability_score * 0.7 + reliability * 0.3
        
        # Select models based on complexity
        if complexity > 0.8:
            # High complexity - use top models
            num_models = min(3, len(model_scores))
        elif complexity > 0.4:
            # Medium complexity
            num_models = min(2, len(model_scores))
        else:
            # Low complexity - use single best model
            num_models = 1
            
        # Sort models by score and return top N
        selected_models = sorted(model_scores.keys(), 
                               key=lambda m: model_scores[m], reverse=True)[:num_models]
        
        return selected_models
    
    def _calculate_context_profile(self, context_data: Dict) -> Dict[str, float]:
        """Calculate a profile of the current context to match with model capabilities."""
        profile = {
            "text_understanding": 0.0,
            "visual_understanding": 0.0,
            "contextual_reasoning": 0.0,
            "memory_capacity": 0.0
        }
        
        # Text content assessment
        if context_data.get("screen_text") or context_data.get("browser_title"):
            profile["text_understanding"] = 0.8
            
        # Visual content assessment
        if context_data.get("has_images") or context_data.get("has_videos"):
            profile["visual_understanding"] = 0.7
            
        # Context complexity assessment
        if len(context_data.get("recent_apps", [])) > 3 or len(context_data.get("file_events", [])) > 5:
            profile["contextual_reasoning"] = 0.9
            profile["memory_capacity"] = 0.8
        
        return profile
    
    def _extract_confidence(self, response: Dict) -> float:
        """Extract confidence score from model response if available."""
        if isinstance(response, dict):
            return response.get("confidence", 0.5)
        return 0.5
        
    def _update_performance_metrics(self, model_name: str, success: bool, latency: float, confidence: float):
        """Update performance metrics for a model."""
        history = self.performance_history[model_name]
        
        if success:
            # Update successful execution metrics
            n = history["successful_executions"]
            history["successful_executions"] += 1
            history["average_latency"] = (history["average_latency"] * n + latency) / (n + 1)
            history["average_confidence"] = (history["average_confidence"] * n + confidence) / (n + 1)
        else:
            # Update failed execution count
            history["failed_executions"] += 1

class EnhancedContextAnalyzer:
    def advanced_semantic_understanding(self, sensor_data):
        """
        Implement:
        - Multi-modal data fusion
        - Probabilistic intent prediction
        - Dynamic context learning
        """
        # TODO:
        # - Develop advanced embedding techniques
        # - Create cross-sensor correlation algorithm
        # - Implement adaptive learning model

class ContextAnalyzer:
    """
    Next-Gen Context Analyzer that leverages multiple local AI models for enhanced understanding.
    Provides deep semantic understanding of user's current state and activities using ensemble techniques.
    """
    
    def __init__(self, models: Dict[str, Any], sensors: Dict, model_profiles: Optional[Dict] = None):
        """
        Initialize the enhanced context analyzer.
        
        Args:
            models: Dictionary of local AI model instances
            sensors: Dictionary of sensor instances
            model_profiles: Optional dictionary of model profiles
        """
        self.models = models
        self.orchestrator = ModelOrchestrator(models, model_profiles)
        self.sensors = sensors
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.WARNING)  # Set logging level to WARNING
        self.last_analysis = None
        self.last_analysis_time = None
        self.context_history = []
        self.analysis_history = []
        self.memory_buffer = self._init_memory_buffer()
        
    def _init_memory_buffer(self) -> Dict:
        """Initialize the memory buffer for persistent context awareness."""
        return {
            "frequent_apps": {},
            "frequent_files": {},
            "recurring_activities": {},
            "time_patterns": {},
            "attention_patterns": {},
            "embedding_cache": {},
            "semantic_patterns": {}
        }
        
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        # Remove extra whitespace but preserve single spaces
        text = re.sub(r'\s+', ' ', text)
        # Ensure space between numbers and words
        text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
        text = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', text)
        return text.strip()
        
    def _format_sensor_data(self) -> Dict:
        """Format sensor data for analysis."""
        try:
            formatted_data = {}
            
            # Format screen data
            if 'screen' in self.sensors and self.sensors['screen']:
                screen_data = self.sensors['screen'].get_data()
                if screen_data:
                    formatted_data['screen'] = {
                        'text': str(screen_data.get('text', '')),
                        'has_updates': bool(screen_data.get('has_updates', False))
                    }
            
            # Format file data
            if 'file' in self.sensors and self.sensors['file']:
                file_data = self.sensors['file'].get_data()
                if file_data:
                    formatted_data['file'] = {
                        'events': [str(event) for event in file_data.get('events', [])],
                        'has_updates': bool(file_data.get('has_updates', False))
                    }
            
            # Format process data
            if 'process' in self.sensors and self.sensors['process']:
                process_data = self.sensors['process'].get_data()
                if process_data:
                    formatted_data['process'] = {
                        'active_app': str(process_data.get('active_app', '')),
                        'window_title': str(process_data.get('window_title', '')),
                        'has_updates': bool(process_data.get('has_updates', False))
                    }
            
            # Format browser data
            if 'browser' in self.sensors and self.sensors['browser']:
                browser_data = self.sensors['browser'].get_data()
                if browser_data:
                    formatted_data['browser'] = {
                        'current_url': str(browser_data.get('current_url', '')),
                        'current_title': str(browser_data.get('current_title', '')),
                        'tab_count': int(browser_data.get('tab_count', 0)),
                        'has_updates': bool(browser_data.get('has_updates', False))
                    }
            
            return formatted_data
            
        except Exception as e:
            self.logger.error(f"Error formatting sensor data: {str(e)}", exc_info=True)
            return {}
    
    def _determine_app_category(self, app_name: str) -> str:
        """Determine the category of an application based on its name and usage patterns."""
        categories = {
            "development": ["code", "editor", "ide", "terminal", "git", "github"],
            "communication": ["slack", "discord", "teams", "zoom", "mail", "message"],
            "browser": ["chrome", "firefox", "safari", "edge", "brave"],
            "document": ["word", "excel", "powerpoint", "pdf", "document"],
            "media": ["spotify", "youtube", "netflix", "player", "music"],
            "system": ["settings", "finder", "explorer", "terminal", "cmd"]
        }
        
        app_name = app_name.lower()
        for category, keywords in categories.items():
            if any(keyword in app_name for keyword in keywords):
                return category
        return "other"
    
    def _extract_file_types(self, events: List[Dict]) -> List[str]:
        """Extract unique file types from file events."""
        file_types = set()
        for event in events:
            if isinstance(event, dict) and 'path' in event:
                path = event['path']
                ext = path.split('.')[-1].lower()
                if ext:
                    file_types.add(ext)
        return list(file_types)
    
    def _categorize_files(self, events: List[Dict]) -> List[str]:
        """Categorize files based on their extensions and paths."""
        categories = set()
        for event in events:
            path = event.get("path", "").lower()
            if any(ext in path for ext in [".py", ".js", ".cpp", ".java"]):
                categories.add("code")
            elif any(ext in path for ext in [".doc", ".pdf", ".txt"]):
                categories.add("document")
            elif any(ext in path for ext in [".csv", ".json", ".xml"]):
                categories.add("data")
            elif any(ext in path for ext in [".jpg", ".png", ".gif"]):
                categories.add("media")
        return list(categories)
    
    def _extract_file_operations(self, events: List[Dict]) -> List[str]:
        """Extract file operations from events."""
        operations = set()
        for event in events:
            if isinstance(event, dict) and 'operation' in event:
                operations.add(event['operation'])
        return list(operations)
    
    def _determine_browser_state(self, browser: Union[str, Any]) -> str:
        """Determine the current state of browser activity."""
        url = browser.current_url if hasattr(browser, 'current_url') else str(browser)
        
        if not url:
            return "inactive"
            
        url = url.lower()
        if "google.com/search" in url:
            return "searching"
        elif any(domain in url for domain in ["facebook.com", "twitter.com", "instagram.com"]):
            return "social_media"
        elif any(domain in url for domain in ["docs.google.com", "github.com", "stackoverflow.com"]):
            return "working"
        else:
            return "browsing"
    
    def _combine_context_data(self, context_data: Dict) -> Dict:
        """Combine and analyze data from all sensors to determine overall context."""
        combined = {
            "activity_pattern": "",
            "workflow_state": "",
            "focus_areas": [],
            "interaction_patterns": []
        }
        
        # Analyze application context
        app_context = context_data.get("application_context", {})
        if app_context.get("active_app"):
            combined["activity_pattern"] = f"Using {app_context['active_app']} ({app_context.get('app_category', 'unknown')})"
            combined["focus_areas"].append(app_context.get("app_category", "unknown"))
            
            # Determine workflow state based on app category
            if app_context.get("app_category") == "development":
                combined["workflow_state"] = "coding"
            elif app_context.get("app_category") == "document":
                combined["workflow_state"] = "document_editing"
            elif app_context.get("app_category") == "browser":
                combined["workflow_state"] = context_data.get("browser_context", {}).get("browser_state", "browsing")
            else:
                combined["workflow_state"] = "general_use"
        
        # Analyze file context
        file_context = context_data.get("file_context", {})
        if file_context.get("file_operations"):
            combined["interaction_patterns"].extend(file_context["file_operations"])
            
        # Add file categories if available
        if file_context.get("file_categories"):
            combined["focus_areas"].extend(file_context["file_categories"])
        
        return combined
    
    async def analyze_context(self) -> ContextInsight:
        """Analyze current context using all available sensors and models."""
        try:
            # Format sensor data
            context_data = self._format_sensor_data()
            
            # Prepare enhanced context information for LLM
            llm_context_data = self._prepare_llm_context_data(context_data)
            
            # Select appropriate models
            selected_models = self.orchestrator.select_models_for_context(context_data)
            
            if not selected_models:
                selected_models = ["context"]  # Fallback to default model
            
            # Execute selected models
            responses = []
            for model_name in selected_models:
                # Check if model has context-aware capability
                model = self.models.get(model_name)
                if model and hasattr(model, 'generate_response'):
                    # Check if model supports context-aware generation
                    if hasattr(model, 'context_aware_generation'):
                        system_prompt = "Analyze the current context and provide structured, insightful guidance tailored to the user's activities."
                        user_prompt = "What is the user currently doing, and what suggestions would be most helpful?"
                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                        
                        # Use context-aware generation
                        response = await model.context_aware_generation(messages, llm_context_data)
                    else:
                        # Use enhanced context with normal generation
                        system_prompt = (
                            "You are an insightful context analyzer that understands user activities deeply. " +
                            "Analyze the provided context and suggest helpful actions. " +
                            "Consider the active application, screen content, and recent user behavior."
                        )
                        
                        # Create a detailed prompt with context information
                        user_prompt = f"""Analyze this context and provide structured insights:
                        
                        Active App: {llm_context_data.get('current_app', 'Unknown')}
                        Window Title: {llm_context_data.get('window_title', 'Unknown')}
                        Recent Activities: {', '.join(str(a) for a in llm_context_data.get('recent_activities', [])[:3])}
                        
                        Provide your analysis as a JSON object with these fields:
                        {{
                            "activity": "current activity description",
                            "summary": "concise context summary",
                            "needs": ["potential need 1", "potential need 2"],
                            "attention": "low|medium|high",
                            "confidence": 0.0-1.0,
                            "suggestions": ["specific suggestion 1", "specific suggestion 2"]
                        }}
                        """
                        
                        messages = [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ]
                        
                        # Use context data with enhanced generation
                        response = await model.generate_response(messages, llm_context_data)
                else:
                    # Fallback to standard execution
                    response, _ = await self.orchestrator.execute_model(
                        model_name,
                        json.dumps(context_data),
                        "Analyze the current context and provide structured insights."
                    )
                
                if response:
                    # Try to parse response
                    try:
                        if isinstance(response, str):
                            # Try to parse as JSON
                            content = json.loads(response)
                            responses.append({
                                "message": {"content": response},
                                "content": content,
                                "confidence": content.get("confidence", 0.5)
                            })
                        elif isinstance(response, dict) and "message" in response:
                            # Standard response format
                            responses.append(response)
                        else:
                            # Direct content
                            responses.append({
                                "message": {"content": json.dumps(response)},
                                "content": response,
                                "confidence": response.get("confidence", 0.5)
                            })
                    except json.JSONDecodeError:
                        # Not JSON, treat as text
                        responses.append({
                            "message": {"content": response},
                            "content": {"summary": response},
                            "confidence": 0.5
                        })
            
            # Process model responses
            if responses:
                # Use the response with highest confidence
                best_response = max(responses, key=lambda r: r.get("confidence", 0))
                
                # Try to get content as either direct value or in response message
                if "content" in best_response:
                    content = best_response["content"]
                else:
                    try:
                        content = json.loads(best_response["message"]["content"])
                    except (json.JSONDecodeError, KeyError, TypeError):
                        # Fallback to treating message content as is
                        content = {"summary": best_response.get("message", {}).get("content", "No content available")}
                
                # Get semantic understanding asynchronously
                semantic_understanding = await self._analyze_semantic_context(context_data)
                
                # Extract suggested actions for overlay display
                suggested_actions = []
                if "suggestions" in content and isinstance(content["suggestions"], list):
                    suggested_actions = content["suggestions"]
                elif "needs" in content and isinstance(content["needs"], list):
                    # Transform needs into suggestion format
                    for need in content["needs"]:
                        if "suggest" not in need.lower() and "recommend" not in need.lower():
                            suggested_actions.append(f"I can help you with: {need}")
                
                insight = ContextInsight(
                    current_activity=content.get("activity", "Unknown"),
                    context_summary=content.get("summary", "No summary available"),
                    potential_needs=content.get("needs", []),
                    attention_level=content.get("attention", "medium"),  # Default to medium
                    confidence_score=content.get("confidence", 0.5),
                    source_model=selected_models[0],
                    semantic_understanding=semantic_understanding
                )
                
                # Store suggestions in raw_response for overlay use
                insight.raw_response["suggestions"] = suggested_actions
            else:
                # Create default insight if no valid responses
                insight = ContextInsight(
                    current_activity="Unknown",
                    context_summary="No context analysis available",
                    potential_needs=[],
                    attention_level="medium",  # Default to medium
                    confidence_score=0.0,
                    source_model="none",
                    semantic_understanding={}
                )
            
            # Store analysis
            self.last_analysis = insight
            self.last_analysis_time = datetime.now()
            self.analysis_history.append(insight)
            
            return insight
            
        except Exception as e:
            self.logger.error(f"Error in context analysis: {e}")
            # Return error insight
            error_insight = ContextInsight(
                current_activity="Unknown",
                context_summary="Error analyzing context",
                potential_needs=[],
                attention_level="medium",  # Default to medium
                confidence_score=0.0,
                source_model="main",
                raw_response={"error": str(e)}
            )
            
            # Store error analysis
            self.last_analysis = error_insight
            self.last_analysis_time = datetime.now()
            
            return error_insight
            
    def _prepare_llm_context_data(self, sensor_data: Dict) -> Dict:
        """
        Prepare context data for the LLM in a format that maximizes relevant information.
        
        Args:
            sensor_data: Raw sensor data dictionary
            
        Returns:
            Dict: Processed context data for LLM
        """
        context_data = {}
        
        # Extract process information
        process_data = sensor_data.get('process', {})
        if process_data:
            context_data['current_app'] = process_data.get('active_app', 'Unknown')
            context_data['window_title'] = process_data.get('window_title', '')
            context_data['app_category'] = self._determine_app_category(process_data.get('active_app', ''))
        
        # Extract screen information
        screen_data = sensor_data.get('screen', {})
        if screen_data:
            # Truncate and clean screen text
            screen_text = self._clean_text(screen_data.get('text', ''))
            
            # Extract key information based on app category
            if context_data.get('app_category') == 'browser':
                # Extract visible content from browser screen
                context_data['screen_text'] = screen_text[:1500]  # Limit to first 1500 chars
            elif context_data.get('app_category') == 'development':
                # Extract code snippets and technical information
                code_pattern = r'(def |class |function |import |from |const |let |var )[^\n]+'
                code_matches = re.findall(code_pattern, screen_text)
                context_data['code_elements'] = code_matches[:10]  # Limit to first 10 matches
                context_data['screen_text'] = screen_text[:1000]   # Limit to first 1000 chars
            else:
                # General screen text
                context_data['screen_text'] = screen_text[:800]  # Limit to first 800 chars
        
        # Extract file information
        file_data = sensor_data.get('file', {})
        if file_data and isinstance(file_data.get('events'), list):
            file_events = file_data.get('events', [])
            context_data['file_types'] = self._extract_file_types(file_events)
            context_data['file_operations'] = self._extract_file_operations(file_events)[:5]  # Limit to 5 recent operations
            context_data['file_categories'] = self._categorize_files(file_events)
        
        # Extract browser information
        browser_data = sensor_data.get('browser', {})
        if browser_data:
            context_data['browser_url'] = browser_data.get('current_url', '')
            context_data['browser_title'] = browser_data.get('current_title', '')
            context_data['browser_state'] = self._determine_browser_state(browser_data) 
        
        # Add recent activities from history
        if self.analysis_history:
            recent_activities = [
                {
                    "type": "activity",
                    "details": {
                        "summary": analysis.current_activity,
                        "needs": analysis.potential_needs[:2]  # Limit to 2 needs per activity
                    }
                }
                for analysis in self.analysis_history[-5:]  # Last 5 analyses
            ]
            context_data['recent_activities'] = recent_activities
        
        return context_data
    
    async def _analyze_semantic_context(self, context_data: Dict) -> Dict:
        """Perform deep semantic analysis of the context."""
        try:
            system_prompt = """You are an advanced semantic analyzer that understands the deeper meaning and implications of user activities.
Analyze the provided context and provide insights about:
1. The purpose behind the current activity
2. The workflow or process being followed
3. Potential challenges or obstacles
4. Related concepts or domains
5. Implicit goals or intentions

Format your response as a JSON object with these fields:
{
    "purpose": "detailed purpose analysis",
    "workflow": "workflow description",
    "challenges": ["challenge 1", "challenge 2", ...],
    "related_concepts": ["concept 1", "concept 2", ...],
    "implicit_goals": ["goal 1", "goal 2", ...]
}"""
            
            user_prompt = f"""Context Data for Semantic Analysis:

{json.dumps(context_data, indent=2)}"""
            
            # Use the orchestrator to perform semantic analysis
            try:
                response, _ = await self.orchestrator.execute_model('main', user_prompt, system_prompt)
            except Exception as e:
                self.logger.error(f"Error executing model for semantic analysis: {e}")
                return {
                    "purpose": "Analysis execution error",
                    "workflow": "Error in analysis execution",
                    "challenges": [],
                    "related_concepts": [],
                    "implicit_goals": []
                }
            
            # Safely handle the response
            if not response:
                return {
                    "purpose": "No analysis available",
                    "workflow": "No workflow identified",
                    "challenges": [],
                    "related_concepts": [],
                    "implicit_goals": []
                }
                
            try:
                if isinstance(response, dict):
                    if "message" in response:
                        content = response["message"].get("content", "{}")
                        if isinstance(content, str):
                            try:
                                return json.loads(content)
                            except json.JSONDecodeError:
                                return {"purpose": content[:100] if content else "Unknown"}
                        return content
                    return response
                elif isinstance(response, str):
                    try:
                        return json.loads(response)
                    except json.JSONDecodeError:
                        return {"purpose": response[:100] if response else "Unknown"}
                else:
                    return {"purpose": "Unknown format", "format_type": str(type(response))}
            except Exception as e:
                self.logger.error(f"Error parsing semantic analysis: {e}")
                return {
                    "purpose": "Error in parsing",
                    "error": str(e),
                    "challenges": [],
                    "related_concepts": [],
                    "implicit_goals": []
                }
                
        except Exception as e:
            self.logger.error(f"Error in semantic analysis: {e}")
            return {
                "purpose": "Error in analysis",
                "error": str(e),
                "challenges": [],
                "related_concepts": [],
                "implicit_goals": []
            }
            
    def get_last_analysis(self) -> Optional[ContextInsight]:
        """Get the most recent context analysis."""
        return self.last_analysis
    
    def get_analysis_age(self) -> Optional[float]:
        """Get the age of the last analysis in seconds."""
        if self.last_analysis_time:
            return (datetime.now() - self.last_analysis_time).total_seconds()
        return None

    def analyze_overlay_context(self) -> Dict[str, Any]:
        """Analyze the current state of the overlay widget."""
        try:
            overlay_sensor = self.sensors.get('overlay')
            if not overlay_sensor:
                return {"status": "unavailable"}

            status = overlay_sensor.get_status()
            return {
                "status": "running" if status["is_running"] else "stopped",
                "process_id": status["process_id"]
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_current_context(self) -> Dict[str, Any]:
        """Get the current context from all sensors."""
        context = {
            "browser": self.analyze_browser_context(),
            "process": self.analyze_process_context(),
            "overlay": self.analyze_overlay_context(),
            "timestamp": datetime.now().isoformat()
        }
        return context

"""
Sensor Enhancement Roadmap:

Current Limitations:
- Basic sensor data collection
- Limited cross-sensor correlation
- Platform-specific implementations

Proposed Improvements:
1. Advanced Multi-Modal Sensing
2. Context-Aware Data Extraction
3. Privacy-Preserving Capture Mechanisms
4. Cross-Platform Sensor Abstraction
"""

# Example enhancement for screen_sensor.py
class EnhancedScreenSensor:
    def advanced_context_extraction(self):
        """
        Implement:
        - Advanced UI element detection
        - Semantic screen content understanding
        - Intelligent privacy filtering
        """
        # TODO: 
        # - Implement computer vision-based UI analysis
        # - Create semantic content extraction
        # - Develop intelligent redaction mechanisms

class SensorBridge:
    """
    Provides sensor abstraction and standardization for multi-modal context understanding.
    Allows incorporating custom or third-party sensors into the context analysis framework.
    """
    
    def __init__(self):
        self.registered_sensors = {}
        self.sensor_adapters = {}
        self.logger = logging.getLogger(__name__)
        
    def register_sensor(self, name: str, sensor: Any, adapter: Optional[callable] = None):
        """
        Register a sensor with optional adapter function.
        
        Args:
            name: Unique name for the sensor
            sensor: Sensor instance
            adapter: Optional adapter function to standardize sensor data
        """
        self.registered_sensors[name] = sensor
        if adapter:
            self.sensor_adapters[name] = adapter
            
    def get_sensors(self) -> Dict:
        """Get dictionary of all registered sensors."""
        return self.registered_sensors
        
    def get_standardized_data(self) -> Dict:
        """Get standardized data from all sensors."""
        data = {}
        
        for name, sensor in self.registered_sensors.items():
            try:
                if name in self.sensor_adapters:
                    # Use adapter to standardize data
                    data[name] = self.sensor_adapters[name](sensor)
                elif hasattr(sensor, 'get_data'):
                    # Use standard get_data method
                    data[name] = sensor.get_data()
                elif hasattr(sensor, 'get_raw_data'):
                    # Use raw data method
                    data[name] = sensor.get_raw_data()
                else:
                    # Try to get attributes directly
                    data[name] = {
                        attr: getattr(sensor, attr) 
                        for attr in dir(sensor) 
                        if not attr.startswith('_') and not callable(getattr(sensor, attr))
                    }
            except Exception as e:
                self.logger.error(f"Error getting data from sensor {name}: {e}")
                data[name] = {"error": str(e)}
                
        return data

def event_stream():
    while True:
        # ... check for updates ...
        time.sleep(2)  # Poll every 2 seconds