#!/bin/bash
# Script to open the memory test interface in a browser

echo "Opening fixed memory test interface in default browser..."
open http://localhost:8081/fixed_index.html
echo "Memory test interface should now be open in your browser."
echo "Make sure the memory test server (memory_test_server.py) is running on port 8769."