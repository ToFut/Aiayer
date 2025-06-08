#!/bin/bash
# test_proactive_suggestion_manual.sh
#
# A manual step-by-step testing script for the proactive suggestion system
# This script guides you through testing each component individually

# Set colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored section headers
print_section() {
  echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

# Function to print steps
print_step() {
  echo -e "${YELLOW}STEP $1:${NC} $2"
}

# Function to print success messages
print_success() {
  echo -e "${GREEN}✓ $1${NC}"
}

# Function to print failure messages
print_failure() {
  echo -e "${RED}✗ $1${NC}"
}

# Function to check if a file exists
check_file_exists() {
  if [ -f "$1" ]; then
    print_success "File exists: $1"
    return 0
  else
    print_failure "File does not exist: $1"
    return 1
  fi
}

# Function to check if a process is running
check_process_running() {
  if pgrep -f "$1" > /dev/null; then
    print_success "Process is running: $1"
    return 0
  else
    print_failure "Process is not running: $1"
    return 1
  fi
}

# Function to check if a directory exists
check_directory_exists() {
  if [ -d "$1" ]; then
    print_success "Directory exists: $1"
    return 0
  else
    print_failure "Directory does not exist: $1"
    return 1
  fi
}

# Introduction
clear
print_section "PROACTIVE SUGGESTION SYSTEM - MANUAL TEST SCRIPT"
echo "This script will guide you through testing the proactive suggestion system."
echo "It will verify each component and test the entire flow from memory to execution."
echo ""
echo "Press Enter to start..."
read

# Test Step 1: Verify files exist
print_section "STEP 1: VERIFY FILES EXIST"
print_step "1" "Checking for necessary files..."

FILES_OK=true
check_file_exists "memory_aware_suggestion_monitor.py" || FILES_OK=false
check_file_exists "start_memory_suggestion_system.sh" || FILES_OK=false
check_file_exists "stop_memory_suggestion_system.sh" || FILES_OK=false
check_file_exists "PROACTIVE_SUGGESTION_SYSTEM.md" || FILES_OK=false

if [ "$FILES_OK" = true ]; then
  print_success "All required files exist"
else
  print_failure "Some required files are missing"
fi

# Test Step 2: Verify the system is properly installed
print_section "STEP 2: VERIFY SYSTEM INSTALLATION"
print_step "2.1" "Checking for required directories..."

DIRS_OK=true
check_directory_exists "memory" || DIRS_OK=false
check_directory_exists "memory/suggestions" || mkdir -p memory/suggestions
check_directory_exists "logs/memory" || mkdir -p logs/memory

if [ "$DIRS_OK" = true ]; then
  print_success "All required directories exist"
else
  print_success "Created missing directories"
fi

print_step "2.2" "Checking Python dependencies..."
if python3 -c "import asyncio, websockets, json, re" 2>/dev/null; then
  print_success "Basic Python dependencies are installed"
else
  print_failure "Missing Python dependencies"
  echo "Installing required packages..."
  pip3 install websockets
fi

# Test Step 3: Verify running processes
print_section "STEP 3: VERIFY RUNNING PROCESSES"
print_step "3.1" "Checking if the memory suggestion monitor is running..."

if check_process_running "memory_aware_suggestion_monitor.py"; then
  MONITOR_RUNNING=true
else
  MONITOR_RUNNING=false
  echo "Would you like to start the memory suggestion monitor? (y/n)"
  read START_MONITOR
  
  if [ "$START_MONITOR" = "y" ] || [ "$START_MONITOR" = "Y" ]; then
    echo "Starting memory suggestion monitor..."
    python3 memory_aware_suggestion_monitor.py > logs/memory/suggestion_monitor.log 2>&1 &
    SUGGESTION_PID=$!
    echo $SUGGESTION_PID > pids/memory_suggestion_monitor.pid
    echo "Memory suggestion monitor started with PID: $SUGGESTION_PID"
    MONITOR_RUNNING=true
  fi
fi

print_step "3.2" "Checking if the WebSocket server is running on port 8765..."
if lsof -i :8765 > /dev/null 2>&1; then
  print_success "WebSocket server is running on port 8765"
  WS_RUNNING=true
else
  print_failure "WebSocket server is not running on port 8765"
  WS_RUNNING=false
  echo "Please make sure to start the system using START_ENHANCED_SYSTEM.sh"
fi

# Test Step 4: Create a test suggestion in memory
print_section "STEP 4: CREATE TEST SUGGESTION IN MEMORY"
print_step "4.1" "Creating a test suggestion in conscious memory..."

cat > memory/test_suggestion.json << EOF
{
  "timestamp": $(date +%s),
  "insights": [
    {
      "id": "test-suggestion-$(date +%s)",
      "timestamp": $(date +%s),
      "content": "SUGGESTION: Organize Browser Tabs | You have several browser tabs open. Would you like me to help organize them? | 0.85",
      "source": "system",
      "confidence": 0.9
    }
  ],
  "recent_activities": [
    {
      "timestamp": $(date +%s),
      "task": "Opening browser tabs",
      "application": "Safari",
      "duration": 120
    }
  ]
}
EOF

if check_file_exists "memory/test_suggestion.json"; then
  print_success "Created test suggestion file"
  
  # Copy to conscious memory if it exists
  if [ -f "memory/conscious.json" ]; then
    cp memory/conscious.json memory/conscious.json.bak
    print_success "Backed up existing conscious memory"
    
    # Merge the test suggestion into conscious memory
    python3 -c "
import json
import sys

try:
    # Load both files
    with open('memory/conscious.json', 'r') as f:
        conscious = json.load(f)
    with open('memory/test_suggestion.json', 'r') as f:
        test_suggestion = json.load(f)
    
    # Merge insights
    if 'insights' in conscious:
        conscious['insights'].append(test_suggestion['insights'][0])
    else:
        conscious['insights'] = test_suggestion['insights']
    
    # Merge activities
    if 'recent_activities' in conscious:
        conscious['recent_activities'].append(test_suggestion['recent_activities'][0])
    else:
        conscious['recent_activities'] = test_suggestion['recent_activities']
    
    # Save back to conscious memory
    with open('memory/conscious.json', 'w') as f:
        json.dump(conscious, f, indent=2)
    
    print('Successfully merged test suggestion into conscious memory')
    sys.exit(0)
except Exception as e:
    print(f'Error merging suggestion: {str(e)}')
    sys.exit(1)
"
    if [ $? -eq 0 ]; then
      print_success "Merged test suggestion into conscious memory"
    else
      print_failure "Failed to merge test suggestion"
      cp memory/test_suggestion.json memory/conscious.json
      print_success "Created new conscious memory with test suggestion"
    fi
  else
    cp memory/test_suggestion.json memory/conscious.json
    print_success "Created new conscious memory with test suggestion"
  fi
else
  print_failure "Failed to create test suggestion"
fi

# Test Step 5: Monitor for suggestion detection
print_section "STEP 5: MONITOR FOR SUGGESTION DETECTION"
print_step "5.1" "Waiting for the suggestion monitor to detect the test suggestion..."

if [ "$MONITOR_RUNNING" = true ]; then
  echo "Monitoring logs for suggestion detection (10 seconds)..."
  DETECTED=false
  
  # Start monitoring the log file in the background
  tail -f logs/memory/suggestion_monitor.log | grep -m 1 "Suggestion" > /tmp/suggestion_detection &
  TAIL_PID=$!
  
  # Wait for detection or timeout
  sleep 10
  kill $TAIL_PID 2>/dev/null
  
  if [ -s /tmp/suggestion_detection ]; then
    print_success "Suggestion detected! Log output:"
    cat /tmp/suggestion_detection
    DETECTED=true
  else
    print_failure "No suggestion detection observed in logs"
    echo "Checking for suggestion files directly..."
    
    # Check if any suggestion files were created
    SUGGESTION_FILES=$(find memory/suggestions -name "suggestion_*.json" -mmin -1 2>/dev/null)
    if [ -n "$SUGGESTION_FILES" ]; then
      print_success "Found recently created suggestion files:"
      ls -la $SUGGESTION_FILES
      DETECTED=true
    else
      print_failure "No recent suggestion files found"
      DETECTED=false
    fi
  fi
else
  print_failure "Memory suggestion monitor is not running, skipping detection test"
  DETECTED=false
fi

# Test Step 6: Test WebSocket notification sending
print_section "STEP 6: TEST WEBSOCKET NOTIFICATION SENDING"
print_step "6.1" "Testing manual suggestion sending via WebSocket..."

if [ "$WS_RUNNING" = true ]; then
  echo "Testing WebSocket connection and notification sending..."
  
  # Create a Python script to test WebSocket notification
  cat > test_send_notification.py << EOF
#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys
import time

async def send_test_notification():
    try:
        print("Connecting to WebSocket server at ws://localhost:8765...")
        async with websockets.connect('ws://localhost:8765') as ws:
            # Wait for welcome message
            welcome = await ws.recv()
            print(f"Received welcome message: {welcome[:100]}...")
            
            # Create test notification
            notification = {
                "success": True,
                "response": "💡 TEST NOTIFICATION: This is a test proactive suggestion",
                "mode": "SUGGEST",
                "notification": True,
                "play_sound": True,
                "sound_type": "notification",
                "importance": "high",
                "buttons": [
                    {
                        "id": "do_it",
                        "text": "Yes, help me",
                        "action": "accept",
                        "style": "success"
                    },
                    {
                        "id": "dismiss",
                        "text": "No thanks",
                        "action": "dismiss",
                        "style": "danger"
                    }
                ],
                "interactive": True,
                "plan_id": f"test_{int(time.time())}",
                "timestamp": time.time()
            }
            
            # Send notification
            notification_json = json.dumps(notification)
            print(f"Sending test notification: {notification_json[:100]}...")
            await ws.send(notification_json)
            
            # Wait for potential response
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"Received response: {response[:100]}...")
            except asyncio.TimeoutError:
                print("No response received (this is normal)")
                
            print("Test notification sent successfully!")
            return True
            
    except Exception as e:
        print(f"Error sending test notification: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(send_test_notification())
    sys.exit(0 if result else 1)
EOF

  chmod +x test_send_notification.py
  
  echo "Sending test notification..."
  if python3 test_send_notification.py; then
    print_success "Test notification sent successfully!"
    NOTIFICATION_SENT=true
  else
    print_failure "Failed to send test notification"
    NOTIFICATION_SENT=false
  fi
else
  print_failure "WebSocket server is not running, skipping notification test"
  NOTIFICATION_SENT=false
fi

# Test Step 7: Test mode transition
print_section "STEP 7: TEST MODE TRANSITION"
print_step "7.1" "Testing mode transition from Suggest to Agent..."

if [ "$NOTIFICATION_SENT" = true ]; then
  echo "The next step requires user interaction in the overlay UI."
  echo "Please follow these steps:"
  echo ""
  echo "1. Look for the suggestion notification in the NextGen overlay"
  echo "2. Click the 'Yes, help me' button to accept the suggestion"
  echo "3. The UI should transition to Agent mode with a plan"
  echo "4. Click 'Execute Now' to run the plan"
  echo ""
  echo "Did you see the suggestion notification? (y/n)"
  read SAW_NOTIFICATION
  
  if [ "$SAW_NOTIFICATION" = "y" ] || [ "$SAW_NOTIFICATION" = "Y" ]; then
    print_success "User confirmed seeing the suggestion notification"
    
    echo "Did the UI transition to Agent mode when you clicked 'Yes, help me'? (y/n)"
    read SAW_TRANSITION
    
    if [ "$SAW_TRANSITION" = "y" ] || [ "$SAW_TRANSITION" = "Y" ]; then
      print_success "Mode transition from Suggest to Agent confirmed"
      
      echo "Did the execution plan run when you clicked 'Execute Now'? (y/n)"
      read SAW_EXECUTION
      
      if [ "$SAW_EXECUTION" = "y" ] || [ "$SAW_EXECUTION" = "Y" ]; then
        print_success "Plan execution confirmed"
        print_success "COMPLETE FLOW VERIFIED SUCCESSFULLY!"
      else
        print_failure "Plan execution not confirmed"
      fi
    else
      print_failure "Mode transition not confirmed"
    fi
  else
    print_failure "Suggestion notification not confirmed"
    
    echo "Would you like to try sending another test notification? (y/n)"
    read RETRY_NOTIFICATION
    
    if [ "$RETRY_NOTIFICATION" = "y" ] || [ "$RETRY_NOTIFICATION" = "Y" ]; then
      echo "Sending another test notification..."
      python3 test_send_notification.py
      echo "Please check the overlay UI for the notification"
    fi
  fi
else
  print_failure "Notification sending failed, cannot test mode transition"
fi

# Test Step 8: Final checks and cleanup
print_section "STEP 8: FINAL CHECKS AND CLEANUP"
print_step "8.1" "Checking logs for errors..."

if [ -f "logs/memory/suggestion_monitor.log" ]; then
  ERROR_COUNT=$(grep -c "Error\|error\|ERROR\|Exception\|exception\|EXCEPTION" logs/memory/suggestion_monitor.log)
  
  if [ $ERROR_COUNT -eq 0 ]; then
    print_success "No errors found in suggestion monitor logs"
  else
    print_failure "Found $ERROR_COUNT errors in suggestion monitor logs"
    echo "Last 5 errors:"
    grep -n "Error\|error\|ERROR\|Exception\|exception\|EXCEPTION" logs/memory/suggestion_monitor.log | tail -5
  fi
else
  print_failure "Suggestion monitor log file not found"
fi

print_step "8.2" "Cleanup (optional)..."
echo "Would you like to clean up test files? (y/n)"
read CLEANUP

if [ "$CLEANUP" = "y" ] || [ "$CLEANUP" = "Y" ]; then
  rm -f memory/test_suggestion.json test_send_notification.py /tmp/suggestion_detection
  print_success "Test files cleaned up"
fi

# Final summary
print_section "TEST SUMMARY"
echo "Proactive Suggestion System Test Results:"
echo ""
echo "1. Required Files: $([ "$FILES_OK" = true ] && echo "PASS" || echo "FAIL")"
echo "2. System Installation: $([ "$DIRS_OK" = true ] && echo "PASS" || echo "FAIL")"
echo "3. Running Processes:"
echo "   - Memory Suggestion Monitor: $([ "$MONITOR_RUNNING" = true ] && echo "PASS" || echo "FAIL")"
echo "   - WebSocket Server: $([ "$WS_RUNNING" = true ] && echo "PASS" || echo "FAIL")"
echo "4. Test Suggestion Creation: $([ -f "memory/conscious.json" ] && echo "PASS" || echo "FAIL")"
echo "5. Suggestion Detection: $([ "$DETECTED" = true ] && echo "PASS" || echo "FAIL")"
echo "6. Notification Sending: $([ "$NOTIFICATION_SENT" = true ] && echo "PASS" || echo "FAIL")"
echo "7. User Interaction Tests:"
echo "   - Notification Visibility: $([ "$SAW_NOTIFICATION" = "y" ] && echo "PASS" || echo "FAIL")"
echo "   - Mode Transition: $([ "$SAW_TRANSITION" = "y" ] && echo "PASS" || echo "FAIL")"
echo "   - Plan Execution: $([ "$SAW_EXECUTION" = "y" ] && echo "PASS" || echo "FAIL")"
echo ""

print_section "NEXT STEPS"
echo "To run the automatic test script:"
echo "python3 test_suggestion_flow.py"
echo ""
echo "To view the suggestion monitor logs:"
echo "tail -f logs/memory/suggestion_monitor.log"
echo ""
echo "To send a manual suggestion:"
echo "python3 test_send_notification.py"
echo ""
echo "Documentation can be found in:"
echo "PROACTIVE_SUGGESTION_SYSTEM.md"