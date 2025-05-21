#!/usr/bin/env python3
"""
Quick Check for LLM Context Integration

This script sends a direct query to the LLM service to check if context is properly integrated.
"""

import json
import asyncio
import websockets
import os
import time

async def check_llm_context():
    """Send a direct query to test context integration"""
    llm_uri = "ws://localhost:8770"
    
    try:
        print("\n===== CHECKING LLM CONTEXT INTEGRATION =====\n")
        
        # First check the current context
        context_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memory', 'last_context.json')
        if os.path.exists(context_file):
            with open(context_file, 'r') as f:
                context = json.load(f)
                print("CURRENT CONTEXT:")
                print(json.dumps(context, indent=2))
                print("\n" + "-"*80 + "\n")
        
        # Connect to LLM service
        print(f"Connecting to LLM service at {llm_uri}...")
        async with websockets.connect(llm_uri) as ws:
            print("Connected! Sending test query 'What am I seeing?'")
            
            # Send test query
            request = {
                "type": "llm_request",
                "query": "What am I seeing?",
                "include_context": True,
                "request_id": f"test_{int(time.time())}"
            }
            
            await ws.send(json.dumps(request))
            
            # Get response
            print("Waiting for response...")
            response = await ws.recv()
            data = json.loads(response)
            
            print("\nRESPONSE:")
            print("-"*80)
            
            if "error" in data:
                print(f"ERROR: {data['error']}")
            else:
                context_used = data.get("context_used", False)
                print(f"CONTEXT WAS USED: {'Yes' if context_used else 'No'}")
                print(f"\n{data.get('response', 'No response content')}")
            
            print("-"*80)
            print("\n===== CHECK COMPLETE =====")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_llm_context())