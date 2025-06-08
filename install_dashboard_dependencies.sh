#!/bin/bash
# Install dependencies for Task Memory Dashboard

echo "Installing Dashboard dependencies..."
pip install -r dashboard_requirements.txt

# Check if installation was successful
if [ $? -eq 0 ]; then
    echo "Dependencies installed successfully!"
    echo "You can now start the dashboard with: ./start_dashboard.sh"
else
    echo "Error installing dependencies. Please check the output above."
fi