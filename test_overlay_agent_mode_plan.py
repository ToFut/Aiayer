import asyncio
import websockets
import json
import re
import time

BACKEND_WS_URL = "ws://localhost:8767"
PROMPT = "Open Safari and search for SEGEV"
AGENT_MODE = "Agent"

# Helper to detect automation plan in response
def is_automation_plan(response):
    # Check for JSON response with plan_generated type
    try:
        data = json.loads(response)
        if data.get("type") == "plan_generated":
            return True
    except:
        pass
    
    # Check for text response with automation plan keywords
    return (
        "AUTOMATION EXECUTION PLAN" in response or
        "Automation Plan" in response or
        "Automation Steps" in response
    )

def extract_plan_id(response):
    # Try to parse as JSON first
    try:
        data = json.loads(response)
        if data.get("type") == "plan_generated":
            return data.get("plan_id")
    except:
        pass
    
    # Fallback to regex for text responses
    match = re.search(r"Plan ID[:：]*[` ]*([\w\-]+)", response)
    if match:
        return match.group(1)
    # Try alternative format
    match = re.search(r"plan_[0-9]+", response)
    if match:
        return match.group(0)
    return None

def extract_steps(response):
    # Try to parse as JSON first
    try:
        data = json.loads(response)
        if data.get("type") == "plan_generated" and data.get("plan"):
            plan = data.get("plan", {})
            if "steps" in plan:
                return [step.get("description", "") for step in plan["steps"]]
    except:
        pass
    
    # Fallback to regex for text responses
    steps = re.findall(r"\d+\.\s+.+", response)
    return steps

async def main():
    print(f"Connecting to backend at {BACKEND_WS_URL}...")
    async with websockets.connect(BACKEND_WS_URL) as ws:
        print("Connected.")
        # Register client
        client_id = f"test_overlay_{int(time.time())}"
        await ws.send(json.dumps({"type": "register", "client_id": client_id}))
        # Wait for registration ack (optional)
        try:
            reg_resp = await asyncio.wait_for(ws.recv(), timeout=2)
            print("Registration response:", reg_resp)
        except Exception:
            pass
        # Send Agent mode chat_request
        payload = {
            "type": "chat_request",
            "mode": AGENT_MODE,
            "message": PROMPT,
            "client_id": client_id,
            "timestamp": time.time()
        }
        print(f"Sending Agent mode prompt: {PROMPT}")
        await ws.send(json.dumps(payload))
        # Wait for response
        plan_response = None
        for _ in range(10):
            resp = await ws.recv()
            print("Received:", resp)
            if is_automation_plan(resp):
                plan_response = resp
                break
        assert plan_response, "Did not receive an automation plan response!"
        print("Automation plan detected.")
        # Check for plan ID
        plan_id = extract_plan_id(plan_response)
        assert plan_id, "No plan ID found in response!"
        print(f"Plan ID: {plan_id}")
        # Check for steps
        steps = extract_steps(plan_response)
        assert steps and len(steps) >= 2, "No actionable steps found in plan!"
        print(f"Found {len(steps)} steps:")
        for step in steps:
            print("  ", step)
        # Optionally, trigger execution
        print("Triggering plan execution...")
        exec_payload = {
            "type": "execute_plan",
            "plan_id": plan_id,
            "client_id": client_id
        }
        await ws.send(json.dumps(exec_payload))
        # Wait for execution response
        for _ in range(10):
            exec_resp = await ws.recv()
            print("Execution response:", exec_resp)
            if "executed successfully" in exec_resp or "execution_completed" in exec_resp:
                print("Execution completed.")
                break
        print("Test completed successfully.")

if __name__ == "__main__":
    asyncio.run(main()) 