"""
Performance test suite for production workloads.
"""
import pytest
import asyncio
import time
import psutil
import logging
from typing import Dict, List
from datetime import datetime

from agent.task_agent import TaskAgent
from agent.context_analyzer import ContextAnalyzer
from memory.memory import ConversationMemory
from agent.data_filter import DataFilter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Collect and analyze performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {
            'response_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'context_analysis_times': []
        }
        self.start_time = time.time()
    
    def add_metric(self, metric_name: str, value: float):
        """Add a performance metric."""
        self.metrics[metric_name].append(value)
    
    def get_average(self, metric_name: str) -> float:
        """Get average value for a metric."""
        values = self.metrics[metric_name]
        return sum(values) / len(values) if values else 0
    
    def get_max(self, metric_name: str) -> float:
        """Get maximum value for a metric."""
        return max(self.metrics[metric_name]) if self.metrics[metric_name] else 0
    
    def get_min(self, metric_name: str) -> float:
        """Get minimum value for a metric."""
        return min(self.metrics[metric_name]) if self.metrics[metric_name] else 0
    
    def get_total_time(self) -> float:
        """Get total test duration."""
        return time.time() - self.start_time

@pytest.mark.asyncio
async def test_concurrent_queries(task_agent: TaskAgent):
    """Test performance with concurrent queries."""
    metrics = PerformanceMetrics()
    num_queries = 100
    queries = [f"Test query {i}" for i in range(num_queries)]
    
    # Run concurrent queries
    start_time = time.time()
    tasks = [task_agent.handle_query(query) for query in queries]
    responses = await asyncio.gather(*tasks)
    
    # Record metrics
    duration = time.time() - start_time
    metrics.add_metric('response_times', duration / num_queries)
    metrics.add_metric('memory_usage', psutil.Process().memory_percent())
    metrics.add_metric('cpu_usage', psutil.cpu_percent())
    
    # Assertions
    assert len(responses) == num_queries
    assert metrics.get_average('response_times') < 5.0  # Average response time < 5s
    assert metrics.get_max('memory_usage') < 85.0  # Max memory usage < 85%
    assert metrics.get_max('cpu_usage') < 80.0  # Max CPU usage < 80%

@pytest.mark.asyncio
async def test_context_analysis_performance(context_analyzer: ContextAnalyzer):
    """Test context analysis performance."""
    metrics = PerformanceMetrics()
    num_analyses = 50
    
    for _ in range(num_analyses):
        start_time = time.time()
        await context_analyzer.analyze_context()
        duration = time.time() - start_time
        metrics.add_metric('context_analysis_times', duration)
        metrics.add_metric('memory_usage', psutil.Process().memory_percent())
    
    # Assertions
    assert metrics.get_average('context_analysis_times') < 2.0  # Average analysis time < 2s
    assert metrics.get_max('memory_usage') < 85.0  # Max memory usage < 85%

@pytest.mark.asyncio
async def test_memory_management(conversation_memory: ConversationMemory):
    """Test memory management under load."""
    metrics = PerformanceMetrics()
    num_messages = 1000
    
    # Add messages
    start_time = time.time()
    for i in range(num_messages):
        conversation_memory.add_message({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Message {i}"
        })
        metrics.add_metric('memory_usage', psutil.Process().memory_percent())
    
    duration = time.time() - start_time
    metrics.add_metric('response_times', duration / num_messages)
    
    # Assertions
    assert metrics.get_average('response_times') < 0.01  # Average add time < 10ms
    assert metrics.get_max('memory_usage') < 85.0  # Max memory usage < 85%

@pytest.mark.asyncio
async def test_long_running_performance(task_agent: TaskAgent):
    """Test performance over an extended period."""
    metrics = PerformanceMetrics()
    duration = 300  # 5 minutes
    end_time = time.time() + duration
    
    while time.time() < end_time:
        start_time = time.time()
        await task_agent.handle_query("What's my current context?")
        response_time = time.time() - start_time
        
        metrics.add_metric('response_times', response_time)
        metrics.add_metric('memory_usage', psutil.Process().memory_percent())
        metrics.add_metric('cpu_usage', psutil.cpu_percent())
        
        await asyncio.sleep(1)  # Wait 1 second between queries
    
    # Assertions
    assert metrics.get_average('response_times') < 5.0  # Average response time < 5s
    assert metrics.get_max('memory_usage') < 85.0  # Max memory usage < 85%
    assert metrics.get_max('cpu_usage') < 80.0  # Max CPU usage < 80%

def test_resource_limits():
    """Test system resource limits."""
    process = psutil.Process()
    
    # Check memory limits
    memory_info = process.memory_info()
    assert memory_info.rss < 4 * 1024 * 1024 * 1024  # Less than 4GB
    
    # Check CPU limits
    cpu_count = psutil.cpu_count()
    assert cpu_count >= 2  # At least 2 CPUs available
    
    # Check disk space
    disk = psutil.disk_usage('/')
    assert disk.free > 10 * 1024 * 1024 * 1024  # More than 10GB free 