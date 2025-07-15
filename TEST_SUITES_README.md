# SensAI Comprehensive Test Suites

This document describes the complete testing framework for the SensAI system, including RPA_AVEN and AIAYER components.

## 🚀 Test Suite Overview

The SensAI system includes multiple comprehensive test suites designed to validate all aspects of the system:

### 1. **Complete Test Suite** (`complete_test_suite.py`)
**Purpose**: Comprehensive testing of all SensAI system components
**Coverage**: 10 major test categories
**Duration**: ~1-2 seconds

**Test Categories:**
- ✅ System Health (processes, ports, resources)
- ✅ Core Services (backend, LLM, DO Button, memory)
- ✅ RPA Automation (automation capabilities)
- ✅ AI Capabilities (LLM models, context processing)
- ✅ Sensor Systems (screen, process sensors)
- ✅ Memory Management (memory operations)
- ✅ Integration Workflows (end-to-end flows)
- ✅ Performance Metrics (response times, resource usage)
- ✅ Security Validation (authentication, encryption)
- ✅ Error Handling (recovery mechanisms)

### 2. **RPA_AVEN Test Suite** (`rpa_aven_test_suite.py`)
**Purpose**: Specialized testing for RPA automation components
**Coverage**: 8 RPA-specific test categories
**Duration**: ~0.5-1 second

**Test Categories:**
- ✅ RPA_AVEN Components (server, RDP, service)
- ✅ Automation Workflows (basic, screen capture, data entry)
- ✅ Screen Interaction (mouse, keyboard, screen capture)
- ✅ Process Automation (launch, monitor, control)
- ✅ Data Extraction (text, image analysis, OCR)
- ✅ Workflow Orchestration (definition, execution, monitoring)
- ✅ Error Recovery (connection, process, workflow recovery)
- ✅ Performance Metrics (response time, throughput, scalability)

### 3. **RPA Workflow Test** (`test_rpa_workflows.py`)
**Purpose**: Specific automation workflow testing
**Coverage**: 6 workflow categories
**Duration**: ~1-2 seconds

**Test Categories:**
- ✅ Basic Automation (DO Button commands)
- ✅ Screen Interaction (mouse, keyboard, screen capture)
- ✅ Data Extraction (OCR, image analysis)
- ✅ Process Automation (monitoring, control)
- ✅ AI Integration (backend communication)
- ✅ Error Handling (invalid commands, timeouts)

### 4. **Master Test Runner** (`run_all_tests.py`)
**Purpose**: Orchestrates all test suites for complete system validation
**Coverage**: All test suites combined
**Duration**: ~2-3 seconds

**Features:**
- Pre-test system status check
- Sequential test suite execution
- Comprehensive reporting
- Performance metrics
- Recommendations

## 🎯 How to Run Tests

### Quick System Test
```bash
python3 comprehensive_system_test.py
```

### Complete Test Suite
```bash
python3 complete_test_suite.py
```

### RPA_AVEN Specific Tests
```bash
python3 rpa_aven_test_suite.py
```

### RPA Workflow Tests
```bash
python3 test_rpa_workflows.py
```

### Master Test Runner (Recommended)
```bash
python3 run_all_tests.py
```

## 📊 Test Results Interpretation

### Status Levels
- **✅ PASS**: Component is fully functional
- **⚠️ PARTIAL**: Component works with minor issues
- **❌ FAIL**: Component has significant issues
- **💥 ERROR**: Component crashed or is unreachable

### Overall System Status
- **✅ ALL TESTS PASSED**: System is fully operational
- **⚠️ MOSTLY WORKING**: Minor issues detected
- **❌ SYSTEM HAS ISSUES**: Significant problems require attention

## 🔧 System Requirements

### Core Components
- Python 3.8+
- Enhanced Enterprise Backend
- Direct Coordinate Automation Server
- Enhanced Process Sensor
- Total Screen Analyzer
- Memory Aware Suggestion Monitor
- Smart Memory Feeder

### Required Libraries
- `websockets` - WebSocket communication
- `requests` - HTTP communication
- `psutil` - Process monitoring
- `pyautogui` - Screen automation
- `PIL` - Image processing
- `pytesseract` - OCR capabilities

### Network Ports
- **8767**: Backend WebSocket
- **8765**: DO Button WebSocket
- **8787**: Backend HTTP Status
- **11434**: LLM Service (Ollama)

## 📈 Performance Metrics

### Expected Performance
- **Response Time**: < 200ms for most operations
- **Memory Usage**: < 500MB total system usage
- **CPU Usage**: < 20% under normal load
- **Test Execution**: < 3 seconds for complete suite

### Resource Monitoring
- Process memory usage tracking
- CPU utilization monitoring
- Network connectivity validation
- Disk space availability

## 🛠️ Troubleshooting

### Common Issues

#### Connection Refused Errors
```bash
# Check if services are running
ps aux | grep python | grep -E "(enhanced_enterprise_backend|direct_coordinate_automation)"

# Restart system if needed
./START_ENHANCED_SYSTEM.sh
```

#### Missing Dependencies
```bash
# Install required packages
pip install websockets requests psutil pyautogui pillow pytesseract
```

#### Port Conflicts
```bash
# Check port usage
lsof -i :8767 -i :8765 -i :8787 -i :11434

# Kill conflicting processes if needed
pkill -f conflicting_process_name
```

### Test-Specific Issues

#### RPA_AVEN Not Detected
- RPA_AVEN is optional and not required for core functionality
- DO Button server provides primary automation capabilities

#### Sensor Cache Missing
```bash
# Create missing cache directories
mkdir -p cache/screen_sensor cache/process_sensor
```

#### Memory System Issues
```bash
# Check memory directory
ls -la memory/

# Restart memory services if needed
python3 smart_memory_feeder.py &
python3 memory_aware_suggestion_monitor.py &
```

## 📋 Test Reports

### Report Locations
- **Complete Test**: `test_results/comprehensive_test_YYYYMMDD_HHMMSS.json`
- **RPA_AVEN Test**: `test_results/rpa_aven_test_YYYYMMDD_HHMMSS.json`
- **Final Report**: `test_results/final_comprehensive_report_YYYYMMDD_HHMMSS.json`

### Report Contents
- Test execution timestamps
- Individual test results
- Performance metrics
- System status information
- Error details and recommendations

## 🎉 Success Criteria

### System is Fully Operational When:
- ✅ All core processes are running
- ✅ All required ports are open
- ✅ WebSocket connections are established
- ✅ LLM service is responding
- ✅ Automation capabilities are available
- ✅ Memory system is functional
- ✅ Sensor systems are active

### Production Readiness Checklist:
- [ ] All test suites pass
- [ ] Performance metrics are within acceptable ranges
- [ ] Error handling is working
- [ ] Security validation passes
- [ ] Integration workflows are functional
- [ ] RPA automation is ready
- [ ] AI capabilities are active

## 🔄 Continuous Testing

### Automated Testing
The test suites can be integrated into CI/CD pipelines for continuous validation:

```bash
# Run tests and exit with error code if any fail
python3 run_all_tests.py
if [ $? -ne 0 ]; then
    echo "Tests failed - system needs attention"
    exit 1
fi
```

### Scheduled Testing
Set up cron jobs for regular system health checks:

```bash
# Add to crontab for hourly testing
0 * * * * cd /path/to/sensai && python3 run_all_tests.py >> logs/test_results.log 2>&1
```

## 📞 Support

For issues with the test suites:
1. Check the troubleshooting section above
2. Review test result logs in `test_results/` directory
3. Verify system components are running
4. Check network connectivity and port availability

---

**Last Updated**: 2025-07-08
**Test Suite Version**: 1.0
**SensAI System Version**: Enhanced Enterprise Backend with Context 