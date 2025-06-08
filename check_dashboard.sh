#!/bin/bash
# Open dashboard in browser and check its status

echo "Checking dashboard availability..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/
if [ $? -eq 0 ]; then
    echo "Dashboard is accessible at http://localhost:8081/"
    
    echo "Checking API endpoints..."
    metrics_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/api/metrics)
    echo "Metrics API status: $metrics_status"
    
    timeseries_status=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/api/time-series)
    echo "Time-series API status: $timeseries_status"
    
    echo ""
    echo "Opening dashboard in browser..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open http://localhost:8081/
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open http://localhost:8081/
    else
        # Windows or other
        echo "Please open http://localhost:8081/ in your browser"
    fi
    
    echo ""
    echo "Dashboard metrics data:"
    curl -s http://localhost:8081/api/metrics | python3 -m json.tool | head -20
    
    echo ""
    echo "Dashboard time-series data (sample):"
    curl -s http://localhost:8081/api/time-series | python3 -m json.tool | head -20
else
    echo "Dashboard is not accessible. Make sure the server is running at http://localhost:8081/"
fi