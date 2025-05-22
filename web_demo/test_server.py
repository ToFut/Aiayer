#!/usr/bin/env python3
import asyncio
import websockets
import json
import logging
import os
from datetime import datetime
from aiohttp import web
import aiohttp
import sys

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_server')

# Test endpoints
BRIDGE_WS = 'ws://localhost:8765'
BACKEND_URL = 'http://localhost:8767'
LLM_URL = 'http://localhost:11434'  # Ollama default port

async def test_websocket():
    """Test WebSocket connection to bridge server"""
    try:
        async with websockets.connect(BRIDGE_WS) as ws:
            await ws.send(json.dumps({
                'type': 'connection_established',
                'payload': {
                    'client': 'test_client',
                    'version': '1.0.0'
                }
            }))
            response = await ws.recv()
            data = json.loads(response)
            return data.get('type') == 'server_ready'
    except Exception as e:
        logger.error(f"WebSocket test failed: {e}")
        return False

async def test_backend():
    """Test backend API health endpoint"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BACKEND_URL}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('status') == 'healthy'
    except Exception as e:
        logger.error(f"Backend test failed: {e}")
        return False

async def test_llm():
    """Test LLM service"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{LLM_URL}/api/generate", json={
                "model": "llama2",
                "prompt": "Test prompt",
                "stream": False
            }) as response:
                if response.status == 200:
                    data = await response.json()
                    return 'response' in data
    except Exception as e:
        logger.error(f"LLM test failed: {e}")
        return False

async def test_memory():
    """Test memory system through WebSocket"""
    try:
        async with websockets.connect(BRIDGE_WS) as ws:
            await ws.send(json.dumps({
                'type': 'memory_test',
                'payload': {
                    'action': 'test',
                    'data': {'test': True}
                }
            }))
            response = await ws.recv()
            data = json.loads(response)
            return data.get('type') == 'memory_response'
    except Exception as e:
        logger.error(f"Memory test failed: {e}")
        return False

async def test_screen():
    """Test screen capture"""
    try:
        async with websockets.connect(BRIDGE_WS) as ws:
            await ws.send(json.dumps({
                'type': 'screen_test',
                'payload': {
                    'action': 'capture'
                }
            }))
            response = await ws.recv()
            data = json.loads(response)
            return data.get('type') == 'screen_data'
    except Exception as e:
        logger.error(f"Screen test failed: {e}")
        return False

async def test_process():
    """Test process monitoring"""
    try:
        async with websockets.connect(BRIDGE_WS) as ws:
            await ws.send(json.dumps({
                'type': 'process_test',
                'payload': {
                    'action': 'monitor'
                }
            }))
            response = await ws.recv()
            data = json.loads(response)
            return data.get('type') == 'process_data'
    except Exception as e:
        logger.error(f"Process test failed: {e}")
        return False

async def run_all_tests():
    """Run all system tests"""
    tests = {
        'websocket': test_websocket,
        'backend': test_backend,
        'llm': test_llm,
        'memory': test_memory,
        'screen': test_screen,
        'process': test_process
    }
    
    results = {}
    for name, test_fn in tests.items():
        try:
            success = await test_fn()
            results[name] = {
                'success': success,
                'message': 'Passed' if success else 'Failed'
            }
        except Exception as e:
            results[name] = {
                'success': False,
                'message': str(e)
            }
    
    return results

async def handle_health(request):
    """Handle health check endpoint"""
    return web.json_response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

async def handle_test(request):
    """Handle test endpoint"""
    component = request.query.get('component')
    if component == 'all':
        results = await run_all_tests()
    else:
        test_fn = globals().get(f'test_{component}')
        if test_fn:
            success = await test_fn()
            results = {
                component: {
                    'success': success,
                    'message': 'Passed' if success else 'Failed'
                }
            }
        else:
            return web.json_response({
                'error': f'Unknown component: {component}'
            }, status=400)
    
    return web.json_response({
        'results': results,
        'timestamp': datetime.now().isoformat()
    })

async def init_app():
    """Initialize the web application"""
    app = web.Application()
    app.router.add_get('/health', handle_health)
    app.router.add_get('/test', handle_test)
    return app

if __name__ == '__main__':
    app = init_app()
    web.run_app(app, port=8080) 