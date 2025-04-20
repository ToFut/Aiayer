import pytest
import time
import asyncio
from sensors.ai_sensor import AISensor, AISensorEvent
from typing import Dict, Any, List

@pytest.fixture
def ai_sensor():
    """Create a test AI sensor instance."""
    sensor = AISensor()
    sensor.start()
    yield sensor
    sensor.stop()

@pytest.fixture
def test_event():
    """Create a test event."""
    return AISensorEvent(
        timestamp=time.time(),
        event_type='cpu_usage',
        source='test',
        data={'value': 95.0},
        confidence=0.95,
        insights=['High CPU usage detected'],
        recommendations=['Consider scaling resources'],
        metadata={'test': True}
    )

def test_sensor_initialization():
    """Test sensor initialization."""
    sensor = AISensor()
    assert not sensor.running
    assert sensor.error_count == 0
    assert isinstance(sensor.config, dict)
    assert len(sensor.events) == 0
    assert len(sensor.insights) == 0
    assert len(sensor.alerts) == 0

def test_sensor_start_stop(ai_sensor):
    """Test starting and stopping the sensor."""
    assert ai_sensor.running
    assert ai_sensor.is_healthy()
    
    ai_sensor.stop()
    assert not ai_sensor.running
    assert not ai_sensor.is_healthy()

def test_get_stats(ai_sensor):
    """Test getting system stats."""
    stats = ai_sensor.get_stats()
    assert isinstance(stats, dict)
    assert 'cpu_percent' in stats
    assert 'memory_percent' in stats
    assert 'is_running' in stats
    assert 'error_count' in stats
    assert 'events_count' in stats
    assert 'insights_count' in stats
    assert 'alerts_count' in stats

@pytest.mark.asyncio
async def test_process_event(ai_sensor, test_event):
    """Test processing an event."""
    result = await ai_sensor._process_event_async(test_event)
    assert result
    assert len(ai_sensor.events) == 1
    assert len(ai_sensor.insights) == 1  # Since confidence > 0.9
    assert len(ai_sensor.alerts) == 1    # Since CPU usage > threshold

def test_should_generate_alert(ai_sensor, test_event):
    """Test alert generation logic."""
    assert ai_sensor._should_generate_alert(test_event)
    
    # Test with below threshold event
    low_usage_event = AISensorEvent(
        timestamp=time.time(),
        event_type='cpu_usage',
        source='test',
        data={'value': 20.0},
        confidence=0.95,
        insights=[],
        recommendations=[],
        metadata={}
    )
    assert not ai_sensor._should_generate_alert(low_usage_event)

def test_queue_size_limits(ai_sensor):
    """Test queue size limits are enforced."""
    # Fill events queue
    for i in range(ai_sensor.config['event_queue_size'] + 10):
        event = AISensorEvent(
            timestamp=time.time(),
            event_type='test',
            source='test',
            data={'value': i},
            confidence=0.95,
            insights=['test'],
            recommendations=['test'],
            metadata={}
        )
        asyncio.run(ai_sensor._process_event_async(event))
    
    assert len(ai_sensor.events) == ai_sensor.config['event_queue_size']
    assert ai_sensor.events[0].data['value'] == 10  # Oldest events were removed 