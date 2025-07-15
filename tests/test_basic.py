"""
Basic tests for core functionality
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that core modules can be imported"""
    try:
        from utils.config_validator import ConfigValidator
        assert ConfigValidator is not None
    except ImportError as e:
        pytest.fail(f"Failed to import ConfigValidator: {e}")
    
    try:
        from utils.health_check import HealthChecker
        assert HealthChecker is not None
    except ImportError as e:
        pytest.fail(f"Failed to import HealthChecker: {e}")

def test_config_validator():
    """Test configuration validator"""
    from utils.config_validator import ConfigValidator
    
    validator = ConfigValidator()
    
    # Test default config creation
    assert validator.DEFAULT_CONFIG is not None
    assert 'system' in validator.DEFAULT_CONFIG
    assert 'sensors' in validator.DEFAULT_CONFIG
    assert 'llm' in validator.DEFAULT_CONFIG

def test_health_checker():
    """Test health checker"""
    from utils.health_check import HealthChecker
    
    checker = HealthChecker()
    
    # Test initialization
    assert checker.start_time > 0
    assert checker.checks == {}
    assert checker.last_check is None

@pytest.mark.asyncio
async def test_health_check_async():
    """Test async health check functionality"""
    from utils.health_check import HealthChecker
    
    checker = HealthChecker()
    
    # Test health check
    health_status = await checker.check_system_health()
    
    assert health_status is not None
    assert 'status' in health_status
    assert 'timestamp' in health_status
    assert 'uptime' in health_status

def test_project_structure():
    """Test that essential project files exist"""
    project_root = Path(__file__).parent.parent
    
    essential_files = [
        'main.py',
        'requirements.txt',
        'README.md',
        'LICENSE',
        'CHANGELOG.md',
        'Dockerfile',
        'Makefile',
        'setup.py',
        '.gitignore'
    ]
    
    for file_name in essential_files:
        file_path = project_root / file_name
        assert file_path.exists(), f"Essential file {file_name} is missing"

def test_config_structure():
    """Test configuration file structure"""
    project_root = Path(__file__).parent.parent
    config_path = project_root / 'config' / 'config.yaml'
    
    if config_path.exists():
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required sections
        required_sections = ['system', 'sensors', 'llm', 'memory', 'logging']
        for section in required_sections:
            assert section in config, f"Missing required config section: {section}"

def test_dependencies():
    """Test that required dependencies are available"""
    try:
        import yaml
        assert yaml is not None
    except ImportError:
        pytest.fail("PyYAML is not available")
    
    try:
        import psutil
        assert psutil is not None
    except ImportError:
        pytest.fail("psutil is not available")
    
    # Skip FastAPI test for Python 3.13 compatibility
    if sys.version_info < (3, 13):
        try:
            import fastapi
            assert fastapi is not None
        except ImportError:
            pytest.fail("FastAPI is not available")
    else:
        pytest.skip("FastAPI test skipped for Python 3.13 compatibility")

def test_logging_setup():
    """Test logging setup"""
    try:
        from utils.logging_setup import setup_logging
        assert setup_logging is not None
    except ImportError as e:
        pytest.fail(f"Failed to import logging setup: {e}")

def test_makefile_targets():
    """Test that Makefile has essential targets"""
    project_root = Path(__file__).parent.parent
    makefile_path = project_root / 'Makefile'
    
    if makefile_path.exists():
        with open(makefile_path, 'r') as f:
            content = f.read()
        
        essential_targets = ['help', 'install', 'test', 'clean', 'setup']
        for target in essential_targets:
            assert f'{target}:' in content, f"Missing Makefile target: {target}" 