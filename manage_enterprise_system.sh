#!/bin/bash

# Enterprise System Management Script

case "$1" in
    status)
        echo "🔍 Enterprise System Status:"
        if [[ -f "pids/enterprise_backend.pid" ]]; then
            PID=$(cat pids/enterprise_backend.pid)
            if ps -p $PID > /dev/null; then
                echo "  • Backend: ✅ Running (PID: $PID)"
            else
                echo "  • Backend: ❌ Not running"
            fi
        else
            echo "  • Backend: ❌ PID file not found"
        fi
        
        echo "  • Port 8765: $(lsof -i :8765 > /dev/null && echo '✅ Active' || echo '❌ Inactive')"
        ;;
    
    test)
        echo "🧪 Testing enterprise system..."
        python3 enterprise_client_example_fixed.py
        ;;
    
    logs)
        echo "📊 Enterprise System Logs:"
        echo "==========================="
        if [[ -f "logs/enterprise_reflection/backend.log" ]]; then
            echo "--- Backend Log (last 20 lines) ---"
            tail -20 logs/enterprise_reflection/backend.log
        fi
        ;;
    
    *)
        echo "Usage: $0 {status|test|logs}"
        echo "  status - Show system status"
        echo "  test   - Run connectivity test"
        echo "  logs   - Show recent logs"
        ;;
esac
