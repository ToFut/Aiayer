import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock
from agent.context_analyzer import ContextAnalyzer, ContextInsight
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/context_insight.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestContextAnalyzer:
    @pytest.fixture
    def analyzer(self):
        """Create a context analyzer instance with mock sensors."""
        # Create mock sensors with proper data
        screen_sensor = MagicMock()
        screen_sensor.get_data.return_value = {
            "text": "Test screen content",
            "has_images": True,
            "has_videos": False
        }
        
        process_sensor = MagicMock()
        process_sensor.get_data.return_value = {
            "active_app": "test_app",
            "window_title": "Test Window",
            "running_apps": ["test_app", "browser"],
            "usage_duration": 100
        }
        
        file_sensor = MagicMock()
        file_sensor.get_data.return_value = {
            "events": [
                {"path": "test.txt", "operation": "created"},
                {"path": "test.py", "operation": "modified"}
            ]
        }
        
        browser_sensor = MagicMock()
        browser_sensor.get_data.return_value = {
            "current_url": "http://test.com",
            "current_title": "Test Page",
            "tab_count": 2
        }
        
        sensors = {
            "screen": screen_sensor,
            "process": process_sensor,
            "file": file_sensor,
            "browser": browser_sensor
        }
        
        # Create mock models
        mock_model = MagicMock()
        mock_model.generate_response.return_value = {
            "message": {
                "content": json.dumps({
                    "activity": "testing",
                    "summary": "Running unit tests",
                    "needs": ["code verification"],
                    "attention": "high",
                    "confidence": 0.95
                })
            }
        }
        
        return ContextAnalyzer({"main": mock_model}, sensors)

    def test_initialization(self, analyzer):
        """Test context analyzer initialization."""
        assert analyzer is not None
        assert analyzer.sensors is not None
        assert analyzer.models is not None
        assert "screen" in analyzer.sensors
        assert "process" in analyzer.sensors
        assert "file" in analyzer.sensors
        assert "browser" in analyzer.sensors
        assert "main" in analyzer.models

    @pytest.mark.asyncio
    async def test_analyze_context(self, analyzer):
        """Test context analysis functionality."""
        insight = await analyzer.analyze_context()
        assert isinstance(insight, ContextInsight)
        assert insight.current_activity is not None
        assert insight.context_summary is not None
        assert isinstance(insight.potential_needs, list)
        assert insight.attention_level in ["high", "medium", "low"]
        assert 0 <= insight.confidence_score <= 1

    @pytest.mark.asyncio
    async def test_get_last_analysis(self, analyzer):
        """Test retrieving the last context analysis."""
        initial_analysis = await analyzer.analyze_context()
        last_analysis = analyzer.get_last_analysis()
        assert last_analysis == initial_analysis

    @pytest.mark.asyncio
    async def test_get_analysis_age(self, analyzer):
        """Test getting the age of the last analysis."""
        await analyzer.analyze_context()
        age = analyzer.get_analysis_age()
        assert isinstance(age, float)
        assert age >= 0

    def test_sensor_data_formatting(self, analyzer):
        """Test sensor data formatting."""
        formatted_data = analyzer._format_sensor_data()
        assert isinstance(formatted_data, dict)
        assert "screen" in formatted_data
        assert "process" in formatted_data
        assert "file" in formatted_data
        assert "browser" in formatted_data
        
        # Check screen data
        screen_data = formatted_data["screen"]
        assert "text" in screen_data
        assert "has_updates" in screen_data
        
        # Check process data
        process_data = formatted_data["process"]
        assert "active_app" in process_data
        assert "window_title" in process_data
        assert "has_updates" in process_data
        
        # Check file data
        file_data = formatted_data["file"]
        assert "events" in file_data
        assert "has_updates" in file_data
        
        # Check browser data
        browser_data = formatted_data["browser"]
        assert "current_url" in browser_data
        assert "current_title" in browser_data
        assert "tab_count" in browser_data
        assert "has_updates" in browser_data

    def test_clean_text(self, analyzer):
        """Test text cleaning functionality."""
        test_text = "  Hello,  World!  \n  Test 123  "
        cleaned = analyzer._clean_text(test_text)
        assert cleaned == "Hello, World! Test 123"

    def test_determine_app_category(self, analyzer):
        """Test application category determination."""
        test_cases = [
            ("Visual Studio Code", "development"),
            ("Chrome", "browser"),
            ("Slack", "communication"),
            ("Word", "document"),
            ("Spotify", "media"),
            ("Settings", "system"),
            ("UnknownApp", "other")
        ]
        
        for app_name, expected_category in test_cases:
            category = analyzer._determine_app_category(app_name)
            assert category == expected_category

    def test_extract_file_types(self, analyzer):
        """Test file type extraction."""
        events = [
            {"path": "/test/file.py"},
            {"path": "/test/document.pdf"},
            {"path": "/test/image.jpg"}
        ]
        file_types = analyzer._extract_file_types(events)
        assert set(file_types) == {"py", "pdf", "jpg"}

    def test_categorize_files(self, analyzer):
        """Test file categorization."""
        events = [
            {"path": "/test/code.py"},
            {"path": "/test/document.pdf"},
            {"path": "/test/data.csv"}
        ]
        categories = analyzer._categorize_files(events)
        assert "code" in categories
        assert "document" in categories
        assert "data" in categories

    def test_extract_file_operations(self, analyzer):
        """Test file operation extraction."""
        events = [
            {"operation": "read"},
            {"operation": "write"},
            {"operation": "delete"}
        ]
        operations = analyzer._extract_file_operations(events)
        assert set(operations) == {"read", "write", "delete"}

    def test_determine_browser_state(self, analyzer):
        """Test browser state determination."""
        test_cases = [
            ("https://www.google.com/search", "searching"),
            ("https://www.facebook.com", "social_media"),
            ("https://docs.google.com", "working"),
            ("https://example.com", "browsing"),
            ("", "inactive")
        ]
        
        for url, expected_state in test_cases:
            state = analyzer._determine_browser_state(url)
            assert state == expected_state

    def test_combine_context_data(self, analyzer):
        """Test context data combination."""
        context_data = {
            "application_context": {
                "active_app": "Visual Studio Code",
                "app_category": "development"
            },
            "file_context": {
                "file_operations": ["read", "write"]
            },
            "browser_context": {
                "current_url": "https://github.com"
            },
            "screen_context": {
                "text": "Hello World"
            }
        }
        
        combined = analyzer._combine_context_data(context_data)
        assert isinstance(combined, dict)
        assert "activity_pattern" in combined
        assert "workflow_state" in combined
        assert "focus_areas" in combined
        assert "interaction_patterns" in combined 

def test_log_context_insight():
    """Test logging a ContextInsight object."""
    # Create a ContextInsight instance
    insight = ContextInsight(
        current_activity="Testing the system",
        context_summary="Running unit tests for context analyzer",
        potential_needs=["Code verification", "Bug detection"],
        attention_level="high",
        confidence_score=0.95,
        source_model="test-model",
        semantic_understanding={
            "task_purpose": "Testing",
            "workflow": "Unit Tests",
            "challenges": ["Test coverage"],
            "related_concepts": ["Mocking", "Assertions"],
            "implicit_goals": ["Code quality"]
        }
    )
    
    # Print the insight
    print("\nContext Insight:")
    print(f"Current Activity: {insight.current_activity}")
    print(f"Context Summary: {insight.context_summary}")
    print(f"Potential Needs: {', '.join(insight.potential_needs)}")
    print(f"Attention Level: {insight.attention_level}")
    print(f"Confidence Score: {insight.confidence_score}")
    print(f"Source Model: {insight.source_model}")
    print(f"Timestamp: {insight.timestamp}")
    print("Semantic Understanding:")
    for key, value in insight.semantic_understanding.items():
        print(f"  {key}: {value}")
    
    # Print as JSON
    insight_dict = {
        "current_activity": insight.current_activity,
        "context_summary": insight.context_summary,
        "potential_needs": insight.potential_needs,
        "attention_level": insight.attention_level,
        "confidence_score": insight.confidence_score,
        "source_model": insight.source_model,
        "timestamp": insight.timestamp.isoformat(),
        "semantic_understanding": insight.semantic_understanding
    }
    print("\nContext Insight (JSON):")
    print(json.dumps(insight_dict, indent=2)) 