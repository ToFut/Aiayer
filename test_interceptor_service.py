#!/usr/bin/env python3
"""
Test WebSocket connection to the interceptor service on port 8766
"""
import asyncio
import websockets
import json
import sys

async def test_interceptor(url):
    """Test connection to the interceptor service"""
    print(f"Trying to connect to interceptor service at {url}...")
    try:
        async with websockets.connect(url, ping_interval=None, close_timeout=30) as ws:
            print(f"Connected to {url} successfully!")
            
            # First register as a client
            register_message = {
                "type": "register",
                "payload": {
                    "client_type": "test_client",
                    "client_name": "InterceptorTest"
                }
            }
            
            print("Registering as a client...")
            await ws.send(json.dumps(register_message))
            
            # Wait for registration response
            try:
                reg_response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"Registration response: {reg_response}")
            except asyncio.TimeoutError:
                print("No registration response received")
            
            # Send a test message asking for completion
            test_message = {
                "type": "llm_request",
                "payload": {
                    "query": "What is the capital of France?",
                    "model": "llama3.2:latest",
                    "context": {
                        "window": "Test Window",
                        "active_apps": ["Test App"],
                        "screen_content": "This is a test of the LLM interceptor service."
                    }
                }
            }
            
            print("Sending test prompt to interceptor service...")
            await ws.send(json.dumps(test_message))
            
            # Wait for multiple messages with 20 second timeout
            start_time = asyncio.get_event_loop().time()
            timeout = 20.0
            success = False
            
            # Keep receiving messages until we get a query_response or timeout
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    remaining = timeout - (asyncio.get_event_loop().time() - start_time)
                    response = await asyncio.wait_for(ws.recv(), timeout=remaining)
                    response_data = json.loads(response)
                    
                    msg_type = response_data.get('type', 'unknown')
                    print(f"\nReceived message of type: {msg_type}")
                    print(f"Full response data: {json.dumps(response_data, indent=2)}")
                    
                    # If we got an actual query response, exit the loop
                    if msg_type == 'query_response':
                        response_content = response_data.get('payload', {}).get('response', 'No content')
                        print(f"Response content: {response_content[:200]}...")
                    elif 'response' in str(response_data):
                        print("Found response in message, treating as success")
                        success = True
                        break
                except asyncio.TimeoutError:
                    print("Timed out waiting for response")
                    break
                except Exception as e:
                    print(f"Error receiving message: {e}")
                    break
            
            # Send a proper disconnect message
            try:
                await ws.send(json.dumps({"type": "disconnect"}))
                print("Sent disconnect message")
            except:
                pass
                
            return success
                
    except (ConnectionRefusedError, websockets.exceptions.WebSocketException) as e:
        print(f"Failed to connect to {url}: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error connecting to {url}: {e}")
        return False

async def main():
    """Test the interceptor service"""
    interceptor_url = "ws://localhost:8766"
    
    print("Testing Interceptor Service")
    print("==========================")
    result = await test_interceptor(interceptor_url)
    
    # Print summary
    print("\nSummary:")
    status = "✅ WORKING" if result else "❌ NOT WORKING"
    print(f"Interceptor Service at {interceptor_url}: {status}")
    
    # Exit with appropriate code
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))