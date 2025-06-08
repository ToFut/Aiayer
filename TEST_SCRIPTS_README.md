# Aiayer Test Scripts

This directory contains various test scripts for evaluating different aspects of the Aiayer system. These scripts are designed to test WebSocket connectivity, chat modes, and overall system performance.

## Quick Start

```bash
# Check if backend is running
python3 check_backend_status.py

# Test all modes with simple queries
python3 mode_tester.py

# Run comprehensive evaluation
python3 comprehensive_client_simulation.py

# Run enhanced evaluation with HTML reports
python3 enhanced_client_simulation.py
```

## Available Test Scripts

### Backend Connectivity

- **check_backend_status.py**: Simple script to check if the backend is running and responding properly
  ```bash
  python3 check_backend_status.py [backend_url]
  ```

### Simple Mode Tests

- **simple_ws_test.py**: Basic WebSocket connectivity test
- **updated_ws_test.py**: Updated test that handles the correct protocol format
- **simple_ask_mode_test.py**: Tests only the ask mode with two simple questions
- **improved_ask_mode_test.py**: Enhanced version that handles all response types and tests more questions

### Comprehensive Tests

- **mode_tester.py**: Tests all modes (agent, ask, suggest, general) with simple queries
  ```bash
  python3 mode_tester.py [--mode MODE]
  ```

- **comprehensive_client_simulation.py**: Full test suite with 10 diverse scenarios across all modes
  ```bash
  python3 comprehensive_client_simulation.py [--backend_url WS_URL] [--report_file FILENAME]
  ```

- **enhanced_client_simulation.py**: Advanced version with detailed analytics and HTML report generation
  ```bash
  python3 enhanced_client_simulation.py [--backend_url WS_URL] [--report_prefix PREFIX]
  ```

## Message Protocol

All scripts use the following message format to communicate with the Aiayer backend:

```json
{
    "type": "chat_request",
    "mode": "ask|agent|suggest|general",
    "message": "User message here",
    "session_id": "unique_session_id"
}
```

The backend responds with a "final_response" message type that contains the response text and metadata.

## Response Types

The scripts handle the following response types:

- **final_response**: The main response type from the Aiayer system
- **response**: Standard response (sometimes used for streaming)
- **agent_response**: Response specific to agent mode
- **progress_update**: Updates about processing progress
- **stream_end**: Indicates the end of a streaming response
- **error**: Error messages from the backend

## Reports and Logs

Test reports and logs are saved to:

- **reports/**: Contains JSON and HTML reports with detailed metrics
- **responses/**: Contains raw response data for analysis
- **logs/**: Contains detailed logs of test execution

## Timeout Configuration

Response timeouts can be configured in each script. The default values are:

- **simple_ask_mode_test.py**: 60 seconds
- **improved_ask_mode_test.py**: 120 seconds
- **mode_tester.py**: 90 seconds
- **comprehensive_client_simulation.py**: 240 seconds
- **enhanced_client_simulation.py**: 240 seconds

## Additional Documentation

For more detailed information, please refer to:

- **COMPREHENSIVE_TEST_SYSTEM.md**: Detailed explanation of the test system
- **SYSTEM_TESTING_SUMMARY.md**: Summary of all testing results and findings
- **COMPREHENSIVE_SYSTEM_EVALUATION_REPORT.md**: Detailed evaluation report

## Adding New Tests

To add new tests:

1. Use existing scripts as templates
2. Ensure proper WebSocket connection handling
3. Use the correct message format ("chat_request")
4. Handle all response types, especially "final_response"
5. Implement appropriate timeout handling
6. Save results to appropriate files