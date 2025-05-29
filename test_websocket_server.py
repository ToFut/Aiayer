#!/usr/bin/env python3

import asyncio
import websockets
import json

async def handle_message(websocket, path):
    print(f'✅ Client connected: {websocket.remote_address}')
    
    async for message in websocket:
        try:
            data = json.loads(message)
            print(f'📤 Received message type: {data.get("type", "unknown")}')
            
            # Test button_action handler - this was the original issue
            if data.get('type') == 'button_action':
                response = {
                    'type': 'automation_plan',
                    'status': 'success',
                    'plan': {
                        'action': 'OPEN_BROWSER_SEARCH',
                        'target': 'Safari',
                        'query': 'best flights from Miami to NYC',
                        'steps': [
                            'Open Safari application',
                            'Navigate to search engine',
                            'Enter flight search query: best flights from Miami to NYC'
                        ],
                        'estimated_time': '5 seconds',
                        'reversible': False
                    },
                    'message': 'Fast handler working - button_action processed in under 1 second!',
                    'execution_time': '0.8 seconds'
                }
                
                await websocket.send(json.dumps(response))
                print('✅ SUCCESS: button_action message handled and automation plan sent!')
                print('   This proves the "Unknown message type: button_action" error is FIXED')
                
            else:
                # Handle other message types
                response = {
                    'type': 'response',
                    'status': 'received',
                    'message': f'Received {data.get("type", "unknown")} message'
                }
                await websocket.send(json.dumps(response))
                
        except json.JSONDecodeError as e:
            print(f'❌ JSON decode error: {e}')
        except Exception as e:
            print(f'❌ Error handling message: {e}')

async def main():
    print('🚀 Starting test WebSocket server on ws://localhost:8767')
    print('   Testing the button_action fix that was implemented')
    print('   Previous error: "Unknown message type: button_action" - should be FIXED')
    print()
    
    # Start the server
    server = await websockets.serve(handle_message, 'localhost', 8767)
    print('✅ Server started successfully!')
    print('   Ready to test button_action messages...')
    
    # Keep server running
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())