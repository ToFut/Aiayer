#!/usr/bin/env python3
"""
Simple Test Dashboard for SensAI/Aiayer
A lightweight dashboard for running and viewing test results
"""

import os
import sys
import glob
import json
import time
import argparse
import subprocess
import datetime
from collections import defaultdict

# Constants
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
RESULTS_DIR = "test_results"

def discover_tests():
    """
    Discover all test files in the project and categorize them by component
    """
    print("Discovering tests...")
    
    # Find all test files
    test_files = []
    for pattern in ["test_*.py", "*_test.py", "test*.py"]:
        test_files.extend(glob.glob(f"**/{pattern}", recursive=True))
    
    # Categorize tests by component
    categorized_tests = defaultdict(list)
    uncategorized = []
    
    for test_file in test_files:
        # Skip the dashboard itself
        if test_file == "test_dashboard.py" or test_file == "simple_test_dashboard.py":
            continue
            
        categorized = False
        # Check file name to determine component
        for component, keywords in COMPONENTS.items():
            if any(keyword in test_file.lower() for keyword in keywords):
                categorized_tests[component].append(test_file)
                categorized = True
                break
                
        # If still uncategorized, add to misc
        if not categorized:
            uncategorized.append(test_file)
    
    if uncategorized:
        categorized_tests["misc"] = uncategorized
    
    return dict(categorized_tests)

def run_test(test_file):
    """
    Run a single test and return the result
    """
    print(f"Running test: {test_file}")
    
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
    
    print(f"Test {test_file} {result['status']} in {result['duration']:.2f}s")
    return result

def run_tests(test_files):
    """
    Run multiple tests and generate a report
    """
    if not test_files:
        print("No tests to run")
        return []
    
    print(f"Running {len(test_files)} tests...")
    
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
    
    print(f"Test results saved to {result_file}")
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
        
        print(f"HTML report generated: {html_file}")
        
    except Exception as e:
        print(f"Error generating HTML report: {e}")

def main():
    """
    Main function for the test dashboard
    """
    parser = argparse.ArgumentParser(description='SensAI/Aiayer Simple Test Dashboard')
    parser.add_argument('--discover', action='store_true', help='Discover tests only')
    parser.add_argument('--run-all', action='store_true', help='Run all tests')
    parser.add_argument('--run-component', help='Run tests for a specific component')
    parser.add_argument('--run-test', help='Run a specific test')
    parser.add_argument('--components', action='store_true', help='List available components')
    
    args = parser.parse_args()
    
    if args.components:
        print("Available components:")
        for component in COMPONENTS:
            print(f"  - {component}")
        return
    
    if args.discover or (not any([args.run_all, args.run_component, args.run_test, args.components])):
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
            print(f"Unknown component: {args.run_component}")
            print(f"Available components: {', '.join(tests.keys())}")
        return
    
    if args.run_test:
        run_tests([args.run_test])
        return

if __name__ == "__main__":
    main()