#!/bin/bash
# Start context memory promotion with 5-minute interval

# Create logs directory if it doesn't exist
mkdir -p logs/memory

echo "Starting context memory promotion utility (5-minute interval)..."
python3 enable_context_memory_promotion.py --interval 300 --threshold 0.6 > logs/memory/context_promotion_output.log 2>&1 &

# Save PID for later shutdown
echo $! > memory/context_promotion.pid
echo "Context memory promotion started with PID: $!"
echo "To stop, run: kill $(cat memory/context_promotion.pid)"