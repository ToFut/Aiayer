# SensAI Master System Test Plan

This document outlines steps to verify that all components of the SensAI Master System are functioning correctly after startup with the enhanced `START_MASTER_SYSTEM.sh` script.

## Initial System Verification

1. Run the startup script:
   ```bash
   ./START_MASTER_SYSTEM.sh
   ```

2. Verify all components are running:
   ```bash
   # Check for required processes
   ps aux | grep -E "neural_ui_detector|direct_coordinate_automation|enhanced_enterprise_backend|smart_memory_feeder|process_sensor|total_screen_analyzer"
   
   # Check for required ports
   lsof -i :8765 -i :8767 -i :8768
   ```

3. Check log files for any errors:
   ```bash
   grep -i "error\|exception\|fail" logs/backend/enhanced_enterprise_8767.log logs/neural_ui_detector/neural_ui_detector.log logs/do_button/do_button_server.log
   ```

## Functional Testing

### 1. Test Ask Mode

Send a test message to the backend server to verify Ask mode is working:

```bash
python3 -c '
import asyncio
import websockets
import json

async def test_ask_mode():
    uri = "ws://localhost:8767"
    async with websockets.connect(uri) as websocket:
        request = {
            "type": "message",
            "mode": "ask",
            "message": "What applications are currently running?",
            "context": {}
        }
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(test_ask_mode())
'
```

Expected result: System should respond with information about running applications.

### 2. Test Agent Mode

Send a test message to the backend server to verify Agent mode is working:

```bash
python3 -c '
import asyncio
import websockets
import json

async def test_agent_mode():
    uri = "ws://localhost:8767"
    async with websockets.connect(uri) as websocket:
        request = {
            "type": "message",
            "mode": "agent",
            "message": "Open Calculator app",
            "context": {}
        }
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(test_agent_mode())
'
```

Expected result: System should respond with a plan to open the Calculator application and display DO/DISMISS buttons.

### 3. Test DO Button Execution

Test if clicking the DO button triggers the action:

```bash
python3 -c '
import asyncio
import websockets
import json

async def test_do_button():
    uri = "ws://localhost:8767"
    
    # First send agent request to get a plan
    async with websockets.connect(uri) as websocket:
        request = {
            "type": "message",
            "mode": "agent",
            "message": "Open Calculator app",
            "context": {}
        }
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        response_data = json.loads(response)
        
        # Extract plan_id from the response
        plan_id = None
        if "plan_id" in response_data:
            plan_id = response_data["plan_id"]
        elif "data" in response_data and "plan_id" in response_data["data"]:
            plan_id = response_data["data"]["plan_id"]
        
        if not plan_id:
            print("No plan_id found in response")
            return
        
        # Now send the DO button action
        do_request = {
            "type": "button_action",
            "action": "do",
            "plan_id": plan_id
        }
        await websocket.send(json.dumps(do_request))
        do_response = await websocket.recv()
        print(json.loads(do_response))

asyncio.run(test_do_button())
'
```

Expected result: The system should execute the plan and open the Calculator application.

### 4. Test Memory Updates

Verify that memory is being updated by checking memory logs and sending a memory-related query:

```bash
# First check memory logs
tail -n 50 logs/memory/smart_feeder.log

# Then send a query about recent activity
python3 -c '
import asyncio
import websockets
import json

async def test_memory():
    uri = "ws://localhost:8767"
    async with websockets.connect(uri) as websocket:
        request = {
            "type": "message",
            "mode": "ask",
            "message": "What have I been doing recently?",
            "context": {}
        }
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(test_memory())
'
```

Expected result: System should respond with information about recent user activities that have been stored in memory.

### 5. Test Neural UI Detection

Test the Neural UI detector with a specific UI element detection query:

```bash
python3 -c '
import asyncio
import websockets
import json

async def test_neural_ui():
    uri = "ws://localhost:8768"
    async with websockets.connect(uri) as websocket:
        request = {
            "type": "detect",
            "action": "analyze_screen"
        }
        await websocket.send(json.dumps(request))
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(test_neural_ui())
'
```

Expected result: The system should return information about UI elements detected on the current screen.

## Troubleshooting

If any tests fail, check the following:

1. Are all required components running? Verify with `ps` command.
2. Are all ports open and accessible? Verify with `lsof` command.
3. Check component logs for specific error messages:
   ```bash
   tail -f logs/backend/enhanced_enterprise_8767.log
   tail -f logs/neural_ui_detector/neural_ui_detector.log
   # If using simple Neural UI detector
   tail -f logs/neural_ui_detector/simple_neural_detector.log
   tail -f logs/do_button/do_button_server.log
   tail -f logs/memory/smart_feeder.log
   ```

### Common Issues and Solutions

1. **Neural UI Detector fails to start**
   - The script automatically falls back to a simplified Neural UI detector
   - Verify with: `lsof -i :8768` to confirm a detector is running
   - Check: `cat pids/simple_neural_ui_detector.pid` to see if using the simplified version

2. **Backend server fails to initialize fully**
   - The script falls back to a simple backend server implementation
   - Verify with: `ps -p $(cat pids/enhanced_enterprise_backend.pid) -o command`
   - If it shows "simple_backend_server.py", you're running in compatibility mode

3. **Missing Python dependencies**
   - The script attempts to install key dependencies, but some may fail
   - Install manually: `pip3 install opencv-python-headless ultralytics numpy pillow websockets pyautogui pynput`

4. **Process Sensor or Screen Analyzer not found**
   - The script now checks multiple locations for these files
   - Check logs for fallback attempts: `grep "fallback" logs/backend/enhanced_enterprise_8767.log`

## System Shutdown

After testing, stop the system gracefully:

```bash
./STOP_MASTER_SYSTEM.sh
```

Verify all components have been stopped:
```bash
ps aux | grep -E "neural_ui_detector|direct_coordination|enhanced_enterprise_backend"
lsof -i :8765 -i :8767 -i :8768
```