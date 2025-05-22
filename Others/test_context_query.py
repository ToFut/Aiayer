#!/usr/bin/env python3
"""
Test Context Query

Simplified script to test a single context query with the LLM service.
"""
import json
import asyncio
import websockets
import os
import time
import sys
import argparse

async def test_context_query(query="What am I seeing?"):
    """Test a single context query with the LLM service"""
    llm_service_uri = "ws://localhost:8770"
    
    try:
        print(f"Connecting to LLM service at {llm_service_uri}")
        async with websockets.connect(llm_service_uri) as websocket:
            print(f"Connected to LLM service")
            
            # Check current context
            context_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'memory', 'last_context.json')
            if os.path.exists(context_file):
                with open(context_file, 'r') as f:
                    context = json.load(f)
                    print("\nCURRENT CONTEXT:")
                    print(json.dumps(context, indent=2))
            
            # Send query to LLM
            request = {
                "type": "llm_request",
                "query": query,
                "include_context": True,
                "request_id": f"test_{int(time.time())}"
            }
            
            print(f"\nSending query: '{query}'")
            await websocket.send(json.dumps(request))
            
            print("Waiting for response...")
            response = await websocket.recv()
            response_data = json.loads(response)
            
            # Display response
            print("\n" + "-"*80)
            print(f"QUERY: {query}")
            print("-"*80)
            
            if "error" in response_data:
                print(f"ERROR: {response_data['error']}")
            else:
                # Check if context was used
                context_used = "context_used" in response_data and response_data["context_used"]
                print(f"CONTEXT USED: {'Yes' if context_used else 'No'}")
                
                # Print full response
                print("\nRESPONSE:")
                print(response_data.get("response", "No response content"))
            
            print("-"*80)
    
    except Exception as e:
        print(f"Error: {e}")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test context queries with the LLM service")
    parser.add_argument("query", nargs="?", default="What am I seeing?", 
                        help="Query to send to the LLM service (default: 'What am I seeing?')")
    args = parser.parse_args()
    
    # Run the test
    asyncio.run(test_context_query(args.query))

if __name__ == "__main__":
    main()
