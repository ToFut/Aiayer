from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock
import asyncio

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

class MockContextAnalyzer:
    """Mock context analyzer for testing"""
    def __init__(self):
        self._last_analysis = None
        self._last_analysis_time = datetime.now()
    
    async def analyze_context(self) -> ContextInsight:
        self._last_analysis = ContextInsight(
            current_activity="Testing the chat interface",
            context_summary="User is interacting with the mock chat interface",
            potential_needs=["Testing", "Debugging", "Development"],
            attention_level="high",
            confidence_score=0.95,
            source_model="mock-model",
            semantic_understanding={
                'task_purpose': 'Testing the chat interface',
                'workflow': 'User interaction testing',
                'challenges': ['Async handling', 'Mock responses'],
                'related_concepts': ['Testing', 'Development'],
                'implicit_goals': ['Verify functionality']
            }
        )
        self._last_analysis_time = datetime.now()
        return self._last_analysis
    
    def get_last_analysis(self) -> Optional[ContextInsight]:
        return self._last_analysis
    
    def get_analysis_age(self) -> float:
        if self._last_analysis_time:
            return (datetime.now() - self._last_analysis_time).total_seconds()
        return float('inf')

class MockSensor:
    """Mock sensor for testing."""
    def __init__(self, sensor_type: str):
        self.sensor_type = sensor_type
        self._updates = False
        self._data = {}

    def has_updates(self) -> bool:
        """Check if sensor has updates."""
        return self._updates

    def get_data(self) -> Dict[str, Any]:
        """Get sensor data."""
        return self._data

    def set_updates(self, has_updates: bool):
        """Set update status."""
        self._updates = has_updates

    def set_data(self, data: Dict[str, Any]):
        """Set sensor data."""
        self._data = data

class MockAgent:
    """Mock agent for testing"""
    def __init__(self):
        self.llm = type('obj', (object,), {'model_name': 'mock-model'})
        self.context_analyzer = MockContextAnalyzer()
        self.memory = ConversationMemory()
    
    async def handle_query(self, query: str) -> str:
        # Add user message to memory
        self.memory.add_message({"role": "user", "content": query})
        
        # Simulate context analysis
        context_analysis = await self.context_analyzer.analyze_context()
        
        # Format response with context
        response = f"""[Context Analysis]
- Current Activity: {context_analysis.current_activity}
- Context Summary: {context_analysis.context_summary}
- Potential Needs: {', '.join(context_analysis.potential_needs)}
- Attention Level: {context_analysis.attention_level}

[Semantic Understanding]
- Task Purpose: {context_analysis.semantic_understanding['task_purpose']}
- Workflow: {context_analysis.semantic_understanding['workflow']}
- Challenges: {', '.join(context_analysis.semantic_understanding['challenges'])}
- Related Concepts: {', '.join(context_analysis.semantic_understanding['related_concepts'])}
- Implicit Goals: {', '.join(context_analysis.semantic_understanding['implicit_goals'])}

[Response]
This is a mock response to: {query}
"""
        # Add assistant message to memory
        self.memory.add_message({"role": "assistant", "content": response})
        return response

class ConversationMemory:
    """Mock conversation memory for testing"""
    def __init__(self):
        self.messages = []
    
    def add_message(self, message: Dict[str, str]) -> None:
        self.messages.append(message)
    
    def get_all(self) -> List[Dict[str, str]]:
        return self.messages
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            'count': len(self.messages),
            'usage_percent': (len(self.messages) / 100) * 100
        }

class MockLLM:
    """Mock LLM for testing."""
    def __init__(self):
        self.model_name = "mock-model"
        self.generate_response = AsyncMock(return_value="Mock response")
        self.ensure_model_available = AsyncMock(return_value=True)
        self.start = AsyncMock(return_value=True)
        self.stop = AsyncMock(return_value=True)

class MockDataFilter:
    """Mock data filter for testing."""
    def __init__(self):
        self.filter_data = MagicMock(return_value={"filtered": "data"})
        self.apply_filters = MagicMock(return_value={"filtered": "data"}) 