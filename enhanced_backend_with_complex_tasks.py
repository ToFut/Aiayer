#!/usr/bin/env python3
"""
Enhanced Enterprise Backend with Complex Task Handler + Enhanced UI Detection Integration
Integrates complex task capabilities and advanced UI detection.
"""

import asyncio
import json
import logging
import websockets
import sys
import traceback
from datetime import datetime

# Import existing backend
sys.path.append('.')
try:
    from enhanced_enterprise_backend_with_context import EnhancedEnterpriseBackend
    from enhanced_complex_task_handler import EnhancedAgentModeHandler
    from enhanced_ui_detection_system import EnhancedUIDetectionSystem
except ImportError as e:
    print(f"❌ Failed to import required modules: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/complex_task_backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ComplexTaskBackend')

class ComplexTaskEnhancedBackend(EnhancedEnterpriseBackend):
    """Enhanced backend with complex task capabilities and UI detection"""
    
    def __init__(self):
        super().__init__()
        self.complex_task_handler = EnhancedAgentModeHandler()
        # Initialize WebSocket connections tracking
        self.active_connections = {}
        # Initialize UI detection system
        try:
            self.ui_detection_system = EnhancedUIDetectionSystem()
            logger.info("Enhanced UI Detection System initialized")
        except Exception as e:
            logger.warning(f"Enhanced UI Detection System failed to initialize: {e}")
            self.ui_detection_system = None
        logger.info("Complex Task Enhanced Backend with UI Detection initialized")
    
    async def handle_agent_mode(self, message: str, context: dict = None) -> dict:
        """Enhanced agent mode with complex task capabilities"""
        try:
            # Use the enhanced complex task handler
            result = await self.complex_task_handler.handle_complex_request(
                request=message,
                user_id=context.get('user_id', 'default'),
                session_id=context.get('session_id', 'default'),
                context=context
            )
            
            # Add complex task and UI detection metadata
            ui_detection_available = self.ui_detection_system is not None
            result['enhanced_features'] = {
                'complex_task_handler': True,
                'enhanced_ui_detection': ui_detection_available,
                'max_task_complexity': 'enterprise',
                'max_concurrent_steps': 15,
                'adaptive_learning': True,
                'real_time_adaptation': True
            }
            
            if ui_detection_available:
                result['enhanced_features']['ui_detection_methods'] = [
                    'Accessibility APIs',
                    'Machine Learning',
                    'Browser APIs',
                    'OCR + NLP'
                ]
            
            return result
            
        except Exception as e:
            logger.error(f"Error in enhanced agent mode: {e}")
            logger.error(traceback.format_exc())
            
            # Fallback to original agent mode
            return await super().handle_agent_mode(message, context)
    
    async def handle_websocket(self, websocket):
        """Enhanced websocket handler with complex task support"""
        client_id = f"client_{id(websocket)}"
        self.active_connections[client_id] = {
            'websocket': websocket,
            'connected_at': datetime.now(),
            'complex_task_enabled': True
        }
        
        logger.info(f"Complex Task client connected: {client_id}")
        
        # Send enhanced connection message
        ui_detection_available = self.ui_detection_system is not None
        features = {
            'complex_task_handler': True,
            'enhanced_ui_detection': ui_detection_available,
            'max_complexity': 'enterprise',
            'parallel_execution': True,
            'adaptive_learning': True,
            'streaming_responses': True,
            'all_chat_modes': ['ask', 'agent', 'suggest', 'general']
        }
        
        if ui_detection_available:
            features['ui_detection_methods'] = [
                'Accessibility APIs',
                'Machine Learning',
                'Browser APIs',
                'OCR + NLP'
            ]
        
        await websocket.send(json.dumps({
            'type': 'connection_established',
            'message': 'Enterprise Backend 8767 with Complex Task Handler + Enhanced UI Detection',
            'client_id': client_id,
            'features': features,
            'timestamp': datetime.now().isoformat()
        }))
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if data.get('type') == 'chat_request':
                        mode = data.get('mode', 'general')
                        user_message = data.get('message', '')
                        
                        # Enhanced context with complex task support
                        context = {
                            'client_id': client_id,
                            'timestamp': datetime.now().isoformat(),
                            'domain': data.get('domain', 'general'),
                            'complexity_preference': data.get('complexity', 'auto'),
                            'parallel_execution': data.get('parallel', True),
                            'learning_enabled': data.get('learning', True)
                        }
                        
                        # Route to appropriate handler
                        if mode == 'agent':
                            response = await self.handle_agent_mode(user_message, context)
                        elif mode == 'ask':
                            response = await self.handle_ask_mode(user_message, context)
                        elif mode == 'suggest':
                            response = await self.handle_suggest_mode(user_message, context)
                        else:
                            response = await self.handle_general_mode(user_message, context)
                        
                        # Send enhanced response
                        response['complex_task_features'] = True
                        await websocket.send(json.dumps(response))
                        
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON format'
                    }))
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send(json.dumps({
                        'type': 'error',
                        'message': f'Processing error: {str(e)}'
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Complex Task client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
        finally:
            if client_id in self.active_connections:
                del self.active_connections[client_id]

async def main():
    """Start the enhanced backend server"""
    backend = ComplexTaskEnhancedBackend()
    
    logger.info("Starting Enhanced Enterprise Backend with Complex Task Handler...")
    logger.info("Port: 8767")
    logger.info("Features: Complex Task Orchestration, AI-Driven Planning, Adaptive Learning")
    
    # Start WebSocket server
    server = await websockets.serve(
        backend.handle_websocket,
        "localhost",
        8767,
        ping_interval=30,
        ping_timeout=10
    )
    
    logger.info("✅ Enhanced Backend with Complex Task Handler started on ws://localhost:8767")
    await server.wait_closed()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(traceback.format_exc())
