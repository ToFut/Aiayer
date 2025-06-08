# SensAI/Aiayer Test Dashboard

A comprehensive test management system for the SensAI/Aiayer project that organizes, runs, and reports on all system tests.

## Features

- **Organized Test Discovery**: Automatically finds and categorizes all tests by component
- **Component-Based Testing**: Run tests for specific system components (Agent, Memory, Neural UI, etc.)
- **Web Dashboard Interface**: User-friendly interface to manage and run tests
- **Detailed Test Reports**: HTML reports showing test results with pass/fail status
- **Performance Metrics**: Track execution time and success rates
- **Command-Line Interface**: Run tests via CLI or web interface

## Getting Started

### Starting the Dashboard

To start the test dashboard, run:

```bash
./start_test_dashboard.sh
```

This will start the dashboard server and open it in your default web browser. The dashboard is accessible at http://localhost:8080.

### Using the Dashboard

The dashboard interface has two main tabs:

1. **Tests**: View and run tests by component
   - Run individual tests
   - Run all tests for a component
   - Run all tests for the entire system

2. **Results**: View test execution results
   - See pass/fail statistics
   - View detailed HTML reports
   - Track test execution history

### Command-Line Usage

The test dashboard can also be used from the command line:

```bash
# List all tests by component
python3 test_dashboard.py --discover

# Run all tests
python3 test_dashboard.py --run-all

# Run tests for a specific component
python3 test_dashboard.py --run-component agent

# Run a specific test
python3 test_dashboard.py --run-test test_agent_automation.py

# Start the dashboard server
python3 test_dashboard.py --start-server
```

## Test Organization

Tests are automatically categorized into the following components:

- **agent**: Agent mode and automation tests
- **backend**: Backend server and brain router tests
- **memory**: Memory system and semantic search tests
- **neural_ui**: Neural UI detection and element recognition tests
- **websocket**: WebSocket connectivity and communication tests
- **notification**: Overlay notifications and suggestions tests
- **llm**: LLM integration and response generation tests
- **system**: Comprehensive system-level tests

## Adding New Tests

To add new tests to the system:

1. Create test files following the naming convention `test_*.py` or `*_test.py`
2. Place tests in appropriate directories (component-specific folders are recommended)
3. Ensure tests exit with code 0 for success and non-zero for failure
4. Include component keywords in the test filename or content for automatic categorization

The dashboard will automatically discover and categorize new tests.

## Test Reports

Test results are stored in the `test_results` directory:

- JSON files contain raw test data
- HTML reports provide a user-friendly view of results
- Results are grouped by component
- Each test shows execution time, output, and errors

## Troubleshooting

### Common Issues

- **Dashboard not starting**: Check port 8080 is available or modify `DASHBOARD_PORT` in test_dashboard.py
- **Tests not discovered**: Ensure tests follow naming conventions and are readable
- **Tests failing unexpectedly**: Check logs in `logs/test_dashboard.log`

### Logs

Dashboard logs are stored in `logs/test_dashboard.log` for troubleshooting.

## Best Practices

- **Regular Testing**: Run the full test suite before making significant changes
- **Component Testing**: Test specific components after making changes to them
- **Test Reports**: Review test reports to identify areas needing improvement
- **Test Coverage**: Add new tests for new features or fixed bugs

## Advanced Usage

### Custom Test Categories

To add new test categories, modify the `COMPONENTS` dictionary in `test_dashboard.py`:

```python
COMPONENTS = {
    "my_new_component": ["keyword1", "keyword2"],
    # existing components...
}
```

### Test Timeouts

By default, tests have a 5-minute timeout. Adjust the `timeout` parameter in the `run_test` function for longer-running tests.

### Continuous Integration

The dashboard can be integrated into CI/CD pipelines by using the command-line interface and checking exit codes.