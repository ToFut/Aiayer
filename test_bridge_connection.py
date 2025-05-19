#!/usr/bin/env python3
import asyncio
import websockets
import json
import sys

async def test_bridge():
    """Test connection to the bridge server and LLM responses"""
    try:
        print("Connecting to WebSocket server at ws://localhost:8765...")
        async with websockets.connect('ws://localhost:8765') as ws:
            # Send connection message
            await ws.send(json.dumps({
                'type': 'connection_established',
                'payload': {
                    'client': 'test_client',
                    'version': '1.0.0'
                }
            }))
            
            # Wait for welcome message
            response = await ws.recv()
            print(f"Server response: {response}\n")
            
            # Send test query
            test_message = "Hello, this is a test message"
            print(f"Sending test message: '{test_message}'")
            
            await ws.send(json.dumps({
                'type': 'llm_request',
                'payload': {
                    'query': test_message
                }
            }))
            
            # Wait for response with longer timeout (30 seconds)
            try:
                print("\nWaiting for LLM response (may take up to 30 seconds)...")
                response = await asyncio.wait_for(ws.recv(), timeout=30)
                print(f"\nReceived response: {response}")
                
                # Parse and check if it's a real LLM response
                data = json.loads(response)
                if data.get('type') == 'llm_response':
                    content = data.get('payload', {}).get('response', '')
                    model = data.get('payload', {}).get('model', '')
                    if 'simulated' in content.lower() or model == 'simulator' or model == 'none':
                        print("\n⚠️  WARNING: Received simulated response - Ollama LLM service might not be connected")
                    elif 'error' in content.lower():
                        print(f"\n⚠️  WARNING: LLM returned an error: {content}")
                    else:
                        print("\n✅ SUCCESS: Received real LLM response")
                        print(f"\nModel used: {model}")
                        print(f"\nResponse: {content[:100]}...")
                else:
                    print(f"\n⚠️  WARNING: Unexpected response type: {data.get('type')}")
                    
            except asyncio.TimeoutError:
                print("\n❌ ERROR: Timeout waiting for LLM response (30 seconds elapsed)")
                print("   This could be because the language model is taking too long to process.")
                print("   Check logs/ollama_service.log for details.")
                
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False
    
    return True

if __name__ == "__main__":
    result = asyncio.run(test_bridge())
    sys.exit(0 if result else 1)