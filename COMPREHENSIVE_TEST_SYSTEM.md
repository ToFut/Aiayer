# Comprehensive Test System for Aiayer

## System Overview

The comprehensive test system is a suite of tools designed to evaluate all aspects of the Aiayer system's capabilities across different modes (agent, ask, suggest) through simulated user interactions. This document explains how to use the system, understand test results, and interpret the evaluation metrics.

## Components

The test system consists of the following key components:

1. **Backend Connectivity Checker**
   - Script: `check_backend_status.py`
   - Purpose: Verify that the Aiayer backend is running and responding correctly
   - Usage: `python3 check_backend_status.py [backend_url]`

2. **Mode-Specific Tester**
   - Script: `mode_tester.py`
   - Purpose: Test individual modes (agent, ask, suggest, general) with simple queries
   - Usage: `python3 mode_tester.py [--backend_url WS_URL] [--mode MODE]`

3. **Comprehensive Client Simulation**
   - Script: `comprehensive_client_simulation.py`
   - Purpose: Run a comprehensive test suite with 10 diverse scenarios across all modes
   - Usage: `python3 comprehensive_client_simulation.py [--backend_url WS_URL] [--report_file FILENAME]`

4. **Enhanced Client Simulation**
   - Script: `enhanced_client_simulation.py`
   - Purpose: Advanced version with detailed analytics and HTML report generation
   - Usage: `python3 enhanced_client_simulation.py [--backend_url WS_URL] [--report_prefix PREFIX]`

## Running the Tests

Ensure your Aiayer system is running before starting the tests:

```bash
# Start the enhanced system with all components
python3 enhanced_enterprise_backend_with_context.py

# Verify backend is running
python3 check_backend_status.py

# In a separate terminal, run the comprehensive test
python3 comprehensive_client_simulation.py
```

## Test Scenarios

The simulation includes 10 diverse test scenarios:

### Agent Mode Tests (3)
- UI interaction: "search for flights to Miami on Google"
- App launch: "open Safari and go to YouTube"
- Complex task: "search for Omer Adam on Spotify and play his music"

### Ask Mode Tests (4)
- System status: "what applications are currently running on my system?"
- Memory retrieval: "what websites have I visited recently?"
- Context understanding: "what's currently visible on my screen?"
- Memory integration: "how has my system usage changed in the last hour?"

### Suggest Mode Tests (3)
- Productivity: "I need to organize my work better"
- Application recommendation: "I want to edit some photos"
- Content recommendation: "I'm bored and want to watch something interesting"

## Key Features

- **Detailed Metrics:** Evaluates response quality, memory integration, contextual understanding, and response time
- **Timeout Handling:** Properly handles slow responses with configurable timeouts
- **Protocol Support:** Handles all message types used by the Aiayer system (final_response, progress_update, etc.)
- **Report Generation:** Creates JSON and HTML reports with performance metrics and improvement suggestions
- **Response Analysis:** Identifies patterns and common elements in system responses

## Evaluation Metrics

The test system evaluates the Aiayer system using the following metrics:

### 1. Response Quality (50% weight)
- Based on presence of expected keywords in responses
- Higher scores indicate more relevant responses
- Examples: For "search flights to Miami", expect words like "Google", "flight", "Miami"

### 2. Memory Integration (25% weight)
- Measures how well the system uses memory in responses
- Based on presence of memory-related indicators
- Examples: "browser", "navigation", "search engine"

### 3. Contextual Understanding (25% weight)
- Assesses how well the system understands context
- Based on presence of context-related indicators
- Examples: "opening browser", "navigating to", "typing"

### 4. Success Criteria
- A test is considered successful if:
  - It receives a response (no timeout)
  - The quality score is at least 0.6/1.0
  - The response contains sufficient relevant content

## Interpreting Results

### System Score
- 0.9-1.0: Excellent
- 0.8-0.9: Very Good
- 0.7-0.8: Good
- 0.6-0.7: Satisfactory
- 0.5-0.6: Needs Improvement
- 0.0-0.5: Poor

### Success Rate
The percentage of tests that passed according to the success criteria.

### Response Time
- < 5s: Excellent
- 5-10s: Good
- 10-20s: Acceptable
- 20-30s: Slow
- > 30s: Very Slow

## Reports

The simulation generates:

1. **Console Output**: Summary of test results and key metrics
2. **JSON Report File**: Detailed results saved in the reports/ directory 
3. **HTML Report** (enhanced simulation): Visual representation of results with charts
4. **Raw Response Files**: Complete responses saved for detailed analysis
5. **Log File**: Complete test logs saved in the logs/ directory

The report includes:
- Overall system score and rating
- Success rates and response times by mode
- Detailed test-by-test results
- Response pattern analysis
- Specific improvement suggestions

## Extending the System

The test system can be extended by:

1. Adding new test scenarios in the `_define_test_scenarios()` method
2. Creating custom evaluators for specific response types
3. Adding new metrics for more comprehensive evaluation
4. Implementing A/B testing capabilities for comparing system versions

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check that the backend is running
   - Verify the correct WebSocket URL (default: ws://localhost:8767)

2. **Response Timeouts**
   - Increase the TIMEOUT value in the script (currently set to 240 seconds)
   - Check backend logs for processing delays or errors

3. **Incorrect Protocol**
   - Ensure you're using the "chat_request" message type
   - Handle all possible response types (final_response, progress_update, etc.)

4. **Invalid JSON**
   - Check backend logs for malformed responses
   - Add robust JSON error handling in client scripts

## Next Steps

After running the tests:

1. Review the detailed report
2. Implement suggested improvements
3. Re-run tests to measure improvement
4. Focus on areas with lowest scores

The comprehensive test system provides an objective way to evaluate the entire Aiayer system's capabilities and identify specific areas for enhancement.