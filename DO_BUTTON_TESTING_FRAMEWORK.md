# Advanced DO Button Testing Framework

This framework provides a comprehensive solution for testing and evaluating the performance of the DO button agent functionality. It enables systematic testing of the agent's ability to understand screen contents, create accurate plans, and execute automated actions.

## Overview

The testing framework consists of the following components:

1. **Test Server**: A WebSocket server that simulates agent interactions and plan execution
2. **Test Interface**: A web interface for selecting and running tests, visualizing results
3. **Screenshot Generator**: A utility to create realistic UI mockups for testing
4. **Testing Scenarios**: A collection of real-world scenarios of varying difficulty
5. **Scoring System**: A mechanism to evaluate and score agent performance
6. **Results Dashboard**: Visualization of performance metrics across tests

## Key Features

- **10 Real-World Scenarios**: Test the agent against common applications and interfaces
- **Difficulty Levels**: Tests range from easy to expert level
- **Performance Metrics**: Track success rates, execution time, and accuracy
- **Visual Feedback**: Screenshot-based testing with visual results
- **Plan Verification**: Compare expected vs. actual plans
- **Detailed Reporting**: Get comprehensive feedback on agent performance
- **Statistics Dashboard**: View trends and performance metrics across tests

## Test Scenarios

The framework includes the following test scenarios:

1. **Web Browser Search** (Medium): Test the agent's ability to interact with a search engine interface
2. **Email Composition** (Hard): Test the agent's ability to compose an email with multiple fields
3. **Spreadsheet Data Entry** (Expert): Test the agent's ability to work with a spreadsheet interface
4. **Calendar Event Creation** (Hard): Test the agent's ability to create a calendar event
5. **Social Media Post** (Medium): Test the agent's ability to create and publish a social media post
6. **File Management** (Expert): Test the agent's ability to navigate file systems and manage files
7. **Code Editing** (Expert): Test the agent's ability to edit code in an IDE
8. **Online Shopping Cart** (Medium): Test the agent's ability to navigate an e-commerce site
9. **PDF Form Filling** (Hard): Test the agent's ability to fill out a PDF form
10. **Data Visualization Tool** (Expert): Test the agent's ability to work with a data visualization interface

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Required Python packages: `websockets`, `pillow` (for screenshot generation)
- Modern web browser

### Installation

1. Clone this repository
2. Install required dependencies:
   ```bash
   pip install websockets pillow
   ```

### Generate Test Screenshots

Generate sample screenshots for the test interface:

```bash
python generate_test_screenshots.py
```

This will create realistic UI mockups in the `test_screenshots` directory.

### Start the Test Server

Launch the test server:

```bash
python advanced_agent_do_button_exam.py
```

By default, the server runs on `localhost:8766`. You can specify a different host/port with the `--host` and `--port` options.

### Open the Test Interface

Open the test interface in your web browser:

```bash
python advanced_agent_do_button_exam.py --open-browser
```

This will automatically open the test interface in your default browser.

## Running Tests

1. Connect to the test server by opening the test interface
2. Select a test scenario from the exam grid
3. Read the instructions in the message field
4. Click "Send to Agent" to initiate the test
5. The agent will analyze the screenshot and generate a plan
6. Click the "DO" button to execute the plan
7. View results in the Results tab

## Scoring System

The scoring system evaluates the agent's performance based on the following criteria:

- **Action Accuracy**: Did the agent identify the correct targets?
- **Input Accuracy**: For text inputs, did the agent enter the correct text?
- **Completeness**: Did the agent perform all required actions?
- **Execution Time**: How long did the agent take to complete the task?

Each test provides an overall score as a percentage, with detailed breakdowns for each expected action.

## Extending the Framework

### Adding New Test Scenarios

To add new test scenarios:

1. Create a new screenshot using the screenshot generator
2. Define the expected actions in the `advanced_exams` dictionary in `advanced_agent_do_button_exam.py`
3. Add the corresponding plan to the `advanced_plans` dictionary

### Customizing the Interface

The test interface can be customized by modifying the HTML/CSS/JavaScript in `advanced_agent_do_button_exam.html`.

## Results Analysis

The framework includes tools for analyzing test results:

- **Individual Test Reports**: Detailed analysis of each test execution
- **Performance Trends**: Track how agent performance evolves over time
- **Comparative Analysis**: Compare performance across different scenarios
- **Failure Analysis**: Identify common patterns in failed actions

## Integration with Production Systems

The testing framework can be integrated with production systems by:

1. Replacing the mock server with connections to real agent services
2. Using real screenshots from user sessions
3. Adapting the scoring system to match production requirements

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This framework was developed to improve the DO button functionality in the AI assistant system
- Thanks to all contributors who have helped refine and test the framework