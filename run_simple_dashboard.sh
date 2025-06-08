#!/bin/bash
# Run the Simple Test Dashboard for SensAI/Aiayer

# Ensure script is run from the project root
cd "$(dirname "$0")"

# Create necessary directories
mkdir -p test_results

echo "SensAI/Aiayer Simple Test Dashboard"
echo "=================================="

# Display menu
echo ""
echo "Choose an option:"
echo "1. List all tests"
echo "2. Run all tests"
echo "3. Run tests for a specific component"
echo "4. Run a specific test"
echo "5. Exit"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        # List all tests
        echo ""
        echo "Listing all tests..."
        python3 simple_test_dashboard.py --discover
        ;;
    2)
        # Run all tests
        echo ""
        echo "Running all tests..."
        python3 simple_test_dashboard.py --run-all
        ;;
    3)
        # Run tests for a specific component
        echo ""
        echo "Available components:"
        python3 simple_test_dashboard.py --components
        echo ""
        read -p "Enter component name: " component
        echo ""
        echo "Running tests for component: $component"
        python3 simple_test_dashboard.py --run-component "$component"
        ;;
    4)
        # Run a specific test
        echo ""
        python3 simple_test_dashboard.py --discover
        echo ""
        read -p "Enter test file to run: " test_file
        echo ""
        echo "Running test: $test_file"
        python3 simple_test_dashboard.py --run-test "$test_file"
        ;;
    5)
        # Exit
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting..."
        exit 1
        ;;
esac

echo ""
echo "Tests completed. Results available in test_results directory."
echo "View HTML reports for detailed test information."