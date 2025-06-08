#!/bin/bash
# Start the backend with a 30-second timeout
timeout 30 python3 enhanced_enterprise_backend_with_context.py > logs/backend/enhanced_enterprise_8767.log 2>&1
# Check if the backend is listening on port 8767
sleep 5
if ! lsof -i :8767 > /dev/null 2>&1; then
  echo "Backend startup timed out or failed. Using simple_backend_server.py as fallback."
  python3 simple_backend_server.py > logs/backend/simple_backend.log 2>&1
fi
