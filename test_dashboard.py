#!/usr/bin/env python3
"""
Master Test Dashboard for SensAI/Aiayer
Provides a comprehensive interface for running tests and viewing results
"""

import os
import sys
import glob
import json
import time
import argparse
import subprocess
import datetime
import re
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
import socket
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_dashboard.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestDashboard")

# Constants
DASHBOARD_PORT = 8080
RESULTS_DIR = "test_results"
COMPONENTS = {
    "agent": ["agent_mode", "agent_automation", "automation", "execution"],
    "backend": ["backend", "enterprise", "brain_router"],
    "memory": ["memory", "search", "context", "trigger"],
    "neural_ui": ["neural_ui", "ui_detection", "ui_element"],
    "websocket": ["ws", "websocket", "overlay_connection"],
    "notification": ["notification", "overlay", "suggestion"],
    "llm": ["llm", "ollama", "streaming", "ai_response"],
    "system": ["system", "comprehensive", "performance"]
}

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass

class DashboardRequestHandler(SimpleHTTPRequestHandler):
    """Custom request handler for the test dashboard server"""
    
    def log_message(self, format, *args):
        """Override to customize logging"""
        logger.debug(format % args)
    
    def do_GET(self):
        """Handle GET requests"""
        # API endpoint for getting test list
        if self.path == '/api/tests':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            test_data = discover_tests()
            self.wfile.write(json.dumps(test_data).encode())
            return
            
        # API endpoint for getting test results
        elif self.path.startswith('/api/results'):
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            result_files = get_result_files()
            self.wfile.write(json.dumps(result_files).encode())
            return
            
        # Serve the dashboard HTML for root requests
        elif self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            with open(os.path.join(os.path.dirname(__file__), 'dashboard/index.html'), 'rb') as file:
                self.wfile.write(file.read())
            return
            
        # Default handling for other paths
        return SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        """Handle POST requests"""
        # API endpoint for running tests
        if self.path.startswith('/api/run'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request = json.loads(post_data.decode('utf-8'))
            
            # Start test execution in a separate thread
            threading.Thread(target=run_tests_from_request, args=(request,)).start()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "started"}).encode())
            return
            
        return SimpleHTTPRequestHandler.do_POST(self)

def discover_tests():
    """
    Discover all test files in the project and categorize them by component
    """
    logger.info("Discovering tests...")
    
    # Find all test files
    test_files = []
    for pattern in ["test_*.py", "*_test.py", "test*.py"]:
        test_files.extend(glob.glob(f"**/{pattern}", recursive=True))
    
    # Categorize tests by component
    categorized_tests = defaultdict(list)
    uncategorized = []
    
    for test_file in test_files:
        # Skip the dashboard itself
        if test_file == "test_dashboard.py":
            continue
            
        categorized = False
        # Check file name and content to determine component
        for component, keywords in COMPONENTS.items():
            if any(keyword in test_file.lower() for keyword in keywords):
                categorized_tests[component].append(test_file)
                categorized = True
                break
                
        # If we couldn't categorize, look at file contents
        if not categorized:
            try:
                with open(test_file, 'r') as f:
                    content = f.read().lower()
                    for component, keywords in COMPONENTS.items():
                        if any(keyword in content for keyword in keywords):
                            categorized_tests[component].append(test_file)
                            categorized = True
                            break
            except Exception as e:
                logger.warning(f"Error reading {test_file}: {e}")
                
        # If still uncategorized, add to misc
        if not categorized:
            uncategorized.append(test_file)
    
    if uncategorized:
        categorized_tests["misc"] = uncategorized
    
    logger.info(f"Found {sum(len(tests) for tests in categorized_tests.values())} tests in {len(categorized_tests)} components")
    
    return dict(categorized_tests)

def run_test(test_file):
    """
    Run a single test and return the result
    """
    logger.info(f"Running test: {test_file}")
    
    start_time = time.time()
    result = {
        "test_file": test_file,
        "start_time": datetime.datetime.now().isoformat(),
        "status": "failed",  # Default to failed
        "output": "",
        "error": "",
        "duration": 0
    }
    
    try:
        # Run the test using Python
        process = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=300  # 5-minute timeout
        )
        
        result["output"] = process.stdout
        result["error"] = process.stderr
        result["status"] = "passed" if process.returncode == 0 else "failed"
        result["return_code"] = process.returncode
        
    except subprocess.TimeoutExpired as e:
        result["status"] = "timeout"
        result["error"] = f"Test timed out after 300 seconds: {str(e)}"
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Error running test: {str(e)}"
    
    end_time = time.time()
    result["duration"] = end_time - start_time
    result["end_time"] = datetime.datetime.now().isoformat()
    
    logger.info(f"Test {test_file} {result['status']} in {result['duration']:.2f}s")
    return result

def run_tests(test_files):
    """
    Run multiple tests and generate a report
    """
    if not test_files:
        logger.warning("No tests to run")
        return []
    
    logger.info(f"Running {len(test_files)} tests...")
    
    # Create results directory if it doesn't exist
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    results = []
    for test_file in test_files:
        result = run_test(test_file)
        results.append(result)
    
    # Save results to file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = os.path.join(RESULTS_DIR, f"test_results_{timestamp}.json")
    
    with open(result_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "tests_run": len(results),
            "tests_passed": sum(1 for r in results if r["status"] == "passed"),
            "tests_failed": sum(1 for r in results if r["status"] in ["failed", "error", "timeout"]),
            "total_duration": sum(r["duration"] for r in results),
            "results": results
        }, f, indent=2)
    
    # Generate HTML report
    generate_html_report(result_file)
    
    logger.info(f"Test results saved to {result_file}")
    return results

def run_tests_from_request(request):
    """
    Run tests based on an API request
    """
    if "component" in request:
        component = request["component"]
        all_tests = discover_tests()
        if component in all_tests:
            run_tests(all_tests[component])
        else:
            logger.error(f"Unknown component: {component}")
    elif "test" in request:
        run_tests([request["test"]])
    elif "all" in request and request["all"]:
        all_tests = discover_tests()
        all_test_files = []
        for component_tests in all_tests.values():
            all_test_files.extend(component_tests)
        run_tests(all_test_files)
    else:
        logger.error(f"Invalid test request: {request}")

def get_result_files():
    """
    Get a list of all test result files
    """
    if not os.path.exists(RESULTS_DIR):
        return []
        
    result_files = glob.glob(os.path.join(RESULTS_DIR, "test_results_*.json"))
    result_files.sort(reverse=True)  # Newest first
    
    results = []
    for file in result_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                results.append({
                    "file": os.path.basename(file),
                    "timestamp": data.get("timestamp", ""),
                    "tests_run": data.get("tests_run", 0),
                    "tests_passed": data.get("tests_passed", 0),
                    "tests_failed": data.get("tests_failed", 0),
                    "total_duration": data.get("total_duration", 0)
                })
        except Exception as e:
            logger.error(f"Error reading result file {file}: {e}")
    
    return results

def generate_html_report(result_file):
    """
    Generate an HTML report from a JSON result file
    """
    try:
        with open(result_file, 'r') as f:
            data = json.load(f)
        
        html_file = result_file.replace('.json', '.html')
        
        with open(html_file, 'w') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Test Results {data['timestamp']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ 
            background-color: #f5f5f5; 
            padding: 15px; 
            border-radius: 5px; 
            margin-bottom: 20px; 
        }}
        .passed {{ color: green; }}
        .failed {{ color: red; }}
        .test {{ 
            margin-bottom: 15px; 
            padding: 10px; 
            border: 1px solid #ddd; 
            border-radius: 3px; 
        }}
        .test.passed {{ border-left: 5px solid green; }}
        .test.failed, .test.error, .test.timeout {{ border-left: 5px solid red; }}
        .output {{ 
            background-color: #f9f9f9; 
            padding: 10px; 
            border-radius: 3px; 
            white-space: pre-wrap; 
            max-height: 300px; 
            overflow: auto; 
        }}
        .error-output {{ 
            background-color: #fff0f0; 
            padding: 10px; 
            border-radius: 3px; 
            white-space: pre-wrap; 
            max-height: 300px; 
            overflow: auto; 
        }}
    </style>
</head>
<body>
    <h1>Test Results: {data['timestamp']}</h1>
    
    <div class="summary">
        <p><strong>Tests Run:</strong> {data['tests_run']}</p>
        <p><strong>Tests Passed:</strong> <span class="passed">{data['tests_passed']}</span></p>
        <p><strong>Tests Failed:</strong> <span class="failed">{data['tests_failed']}</span></p>
        <p><strong>Total Duration:</strong> {data['total_duration']:.2f}s</p>
    </div>
    
    <h2>Test Details</h2>
""")
            
            # Group tests by component
            tests_by_component = defaultdict(list)
            for result in data['results']:
                component = "misc"
                test_file = result['test_file']
                
                for comp, keywords in COMPONENTS.items():
                    if any(keyword in test_file.lower() for keyword in keywords):
                        component = comp
                        break
                
                tests_by_component[component].append(result)
            
            # Write tests by component
            for component, tests in tests_by_component.items():
                passed = sum(1 for t in tests if t['status'] == 'passed')
                total = len(tests)
                
                f.write(f"""
    <h3>{component.title()} ({passed}/{total} passed)</h3>
""")
                
                for result in tests:
                    status = result['status']
                    duration = result['duration']
                    test_file = result['test_file']
                    
                    f.write(f"""
    <div class="test {status}">
        <h4>{test_file} - <span class="{status}">{status.upper()}</span> ({duration:.2f}s)</h4>
""")
                    
                    if result['output']:
                        f.write(f"""
        <h5>Output:</h5>
        <div class="output">{result['output']}</div>
""")
                    
                    if result['error']:
                        f.write(f"""
        <h5>Error:</h5>
        <div class="error-output">{result['error']}</div>
""")
                    
                    f.write("""
    </div>
""")
            
            f.write("""
</body>
</html>
""")
        
        logger.info(f"HTML report generated: {html_file}")
        
    except Exception as e:
        logger.error(f"Error generating HTML report: {e}")

def create_dashboard_files():
    """
    Create necessary dashboard files if they don't exist
    """
    # Create dashboard directory
    os.makedirs("dashboard", exist_ok=True)
    
    # Create basic HTML file
    if not os.path.exists("dashboard/index.html"):
        with open("dashboard/index.html", "w") as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>SensAI/Aiayer Test Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        header {
            background-color: #333;
            color: white;
            padding: 15px 20px;
            margin-bottom: 20px;
        }
        h1, h2, h3 {
            margin: 0;
        }
        .component-card {
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            padding: 15px;
            margin-bottom: 20px;
        }
        .test-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .test-item:last-child {
            border-bottom: none;
        }
        button {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 8px 12px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        }
        button.run-all {
            background-color: #2196F3;
        }
        button.run-component {
            background-color: #ff9800;
        }
        .results-section {
            margin-top: 30px;
        }
        .result-item {
            background-color: white;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            padding: 15px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .passed {
            color: green;
        }
        .failed {
            color: red;
        }
        .tabs {
            display: flex;
            margin-bottom: 20px;
        }
        .tab {
            padding: 10px 15px;
            cursor: pointer;
            background-color: #ddd;
            border: none;
            outline: none;
        }
        .tab.active {
            background-color: white;
            border-bottom: 3px solid #4CAF50;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .status-indicator {
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-indicator.running {
            background-color: #2196F3;
            color: white;
        }
        .status-indicator.success {
            background-color: #4CAF50;
            color: white;
        }
        .status-indicator.failure {
            background-color: #f44336;
            color: white;
        }
        .loading {
            text-align: center;
            padding: 20px;
            font-style: italic;
            color: #666;
        }
    </style>
</head>
<body>
    <header>
        <h1>SensAI/Aiayer Test Dashboard</h1>
    </header>
    
    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="showTab('tests')">Tests</button>
            <button class="tab" onclick="showTab('results')">Results</button>
        </div>
        
        <div id="tests" class="tab-content active">
            <div class="actions">
                <button class="run-all" onclick="runAllTests()">Run All Tests</button>
            </div>
            
            <div id="components" class="loading">
                Loading tests...
            </div>
        </div>
        
        <div id="results" class="tab-content">
            <h2>Test Results</h2>
            <div id="results-list" class="loading">
                Loading results...
            </div>
        </div>
    </div>
    
    <script>
        // Show the selected tab
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Remove active class from all tab buttons
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show the selected tab
            document.getElementById(tabName).classList.add('active');
            
            // Set the tab button as active
            document.querySelector(`.tab[onclick="showTab('${tabName}')"]`).classList.add('active');
            
            // If switching to results tab, refresh the results
            if (tabName === 'results') {
                loadResults();
            }
        }
        
        // Load all tests
        async function loadTests() {
            try {
                const response = await fetch('/api/tests');
                const tests = await response.json();
                
                const componentsContainer = document.getElementById('components');
                componentsContainer.innerHTML = '';
                
                // Sort components alphabetically but put "system" at the end
                const sortedComponents = Object.keys(tests).sort((a, b) => {
                    if (a === 'system') return 1;
                    if (b === 'system') return -1;
                    return a.localeCompare(b);
                });
                
                for (const component of sortedComponents) {
                    const componentTests = tests[component];
                    
                    // Create component card
                    const componentCard = document.createElement('div');
                    componentCard.className = 'component-card';
                    componentCard.innerHTML = `
                        <h3>${component.charAt(0).toUpperCase() + component.slice(1)} (${componentTests.length} tests)</h3>
                        <button class="run-component" onclick="runComponentTests('${component}')">Run All ${component} Tests</button>
                        <div class="tests-list"></div>
                    `;
                    
                    // Add tests to component
                    const testsList = componentCard.querySelector('.tests-list');
                    for (const test of componentTests) {
                        const testItem = document.createElement('div');
                        testItem.className = 'test-item';
                        testItem.innerHTML = `
                            <div>${test}</div>
                            <button onclick="runTest('${test}')">Run</button>
                        `;
                        testsList.appendChild(testItem);
                    }
                    
                    componentsContainer.appendChild(componentCard);
                }
            } catch (error) {
                console.error('Error loading tests:', error);
                document.getElementById('components').innerHTML = 'Error loading tests. Please refresh the page.';
            }
        }
        
        // Load test results
        async function loadResults() {
            try {
                const response = await fetch('/api/results');
                const results = await response.json();
                
                const resultsList = document.getElementById('results-list');
                
                if (results.length === 0) {
                    resultsList.innerHTML = '<p>No test results available.</p>';
                    return;
                }
                
                resultsList.innerHTML = '';
                
                for (const result of results) {
                    const resultItem = document.createElement('div');
                    resultItem.className = 'result-item';
                    
                    const passPercentage = result.tests_run > 0 
                        ? Math.round((result.tests_passed / result.tests_run) * 100) 
                        : 0;
                    
                    resultItem.innerHTML = `
                        <div>
                            <h3>${result.timestamp}</h3>
                            <p>
                                <span class="passed">${result.tests_passed} passed</span> / 
                                <span class="failed">${result.tests_failed} failed</span> of 
                                ${result.tests_run} tests (${passPercentage}% pass rate)
                            </p>
                            <p>Total duration: ${result.total_duration.toFixed(2)}s</p>
                        </div>
                        <div>
                            <a href="/test_results/${result.file.replace('.json', '.html')}" target="_blank">
                                <button>View Report</button>
                            </a>
                        </div>
                    `;
                    
                    resultsList.appendChild(resultItem);
                }
            } catch (error) {
                console.error('Error loading results:', error);
                document.getElementById('results-list').innerHTML = 'Error loading results. Please refresh the page.';
            }
        }
        
        // Run a single test
        async function runTest(testFile) {
            try {
                const response = await fetch('/api/run', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ test: testFile })
                });
                
                alert(`Running test: ${testFile}\nCheck the Results tab for results when complete.`);
                
                // Switch to results tab after a delay
                setTimeout(() => {
                    showTab('results');
                }, 2000);
            } catch (error) {
                console.error('Error running test:', error);
                alert('Error running test. See console for details.');
            }
        }
        
        // Run all tests for a component
        async function runComponentTests(component) {
            try {
                const response = await fetch('/api/run', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ component: component })
                });
                
                alert(`Running all tests for component: ${component}\nCheck the Results tab for results when complete.`);
                
                // Switch to results tab after a delay
                setTimeout(() => {
                    showTab('results');
                }, 2000);
            } catch (error) {
                console.error('Error running component tests:', error);
                alert('Error running component tests. See console for details.');
            }
        }
        
        // Run all tests
        async function runAllTests() {
            try {
                const response = await fetch('/api/run', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ all: true })
                });
                
                alert('Running all tests.\nThis may take some time.\nCheck the Results tab for results when complete.');
                
                // Switch to results tab after a delay
                setTimeout(() => {
                    showTab('results');
                }, 2000);
            } catch (error) {
                console.error('Error running all tests:', error);
                alert('Error running all tests. See console for details.');
            }
        }
        
        // Initialize the dashboard
        window.onload = function() {
            loadTests();
            loadResults();
        };
    </script>
</body>
</html>""")
    
    # Create results directory
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)

def start_dashboard_server():
    """
    Start the dashboard HTTP server
    """
    # Create necessary files
    create_dashboard_files()
    
    # Change to project root directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Create a symbolic link to the results directory in the dashboard directory
    if not os.path.exists("dashboard/test_results"):
        try:
            os.symlink("../test_results", "dashboard/test_results")
        except Exception as e:
            logger.warning(f"Could not create symlink: {e}")
    
    # Find an available port
    port = DASHBOARD_PORT
    while port < DASHBOARD_PORT + 10:
        try:
            # Try to bind to the port
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                break
        except OSError:
            logger.warning(f"Port {port} is already in use, trying next port")
            port += 1
    
    if port >= DASHBOARD_PORT + 10:
        logger.error(f"Could not find an available port in range {DASHBOARD_PORT}-{DASHBOARD_PORT+9}")
        return
    
    # Start the HTTP server
    try:
        server = ThreadedHTTPServer(('localhost', port), DashboardRequestHandler)
        logger.info(f"Starting dashboard server on http://localhost:{port}")
        
        # Open the dashboard in a web browser
        webbrowser.open(f"http://localhost:{port}")
        
        # Start the server
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error starting server: {e}")

def main():
    """
    Main function for the test dashboard
    """
    parser = argparse.ArgumentParser(description='SensAI/Aiayer Test Dashboard')
    parser.add_argument('--discover', action='store_true', help='Discover tests only')
    parser.add_argument('--run-all', action='store_true', help='Run all tests')
    parser.add_argument('--run-component', help='Run tests for a specific component')
    parser.add_argument('--run-test', help='Run a specific test')
    parser.add_argument('--start-server', action='store_true', help='Start the dashboard server')
    
    args = parser.parse_args()
    
    if args.discover:
        tests = discover_tests()
        print("Discovered tests:")
        for component, component_tests in tests.items():
            print(f"\n{component.upper()} ({len(component_tests)} tests):")
            for test in component_tests:
                print(f"  - {test}")
        return
    
    if args.run_all:
        tests = discover_tests()
        all_tests = []
        for component_tests in tests.values():
            all_tests.extend(component_tests)
        run_tests(all_tests)
        return
    
    if args.run_component:
        tests = discover_tests()
        if args.run_component in tests:
            run_tests(tests[args.run_component])
        else:
            logger.error(f"Unknown component: {args.run_component}")
            print(f"Available components: {', '.join(tests.keys())}")
        return
    
    if args.run_test:
        run_tests([args.run_test])
        return
    
    if args.start_server:
        start_dashboard_server()
        return
    
    # If no args or just running the script directly, start the server
    start_dashboard_server()

if __name__ == "__main__":
    main()