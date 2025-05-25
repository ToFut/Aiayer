#!/usr/bin/env python3
"""
Quick fix to enable real LLM responses in the running backend
"""

import requests
import json

def fix_real_responses():
    """Enable real LLM responses by updating backend configuration"""
    
    print("🔧 Fixing AI system to give real responses...")
    
    # Load a fast model first
    print("📦 Loading llama3.2:1b model...")
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:1b",
                "prompt": "Hello, respond with just 'Ready'",
                "stream": False
            },
            timeout=30
        )
        if response.status_code == 200:
            print("✅ Model loaded successfully!")
        else:
            print(f"⚠️ Model load response: {response.status_code}")
    except Exception as e:
        print(f"❌ Model load failed: {e}")
        return False
    
    # Test the model with a simple query
    print("🧠 Testing LLM response...")
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2:1b",
                "prompt": "What is 2+2? Answer in exactly 3 words.",
                "stream": False
            },
            timeout=15
        )
        if response.status_code == 200:
            result = response.json()
            llm_response = result.get("response", "No response")
            print(f"✅ LLM test successful: {llm_response}")
            return True
        else:
            print(f"❌ LLM test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ LLM test error: {e}")
        return False

def create_real_llm_backend():
    """Create a new backend that actually calls LLM"""
    print("🚀 Creating real LLM backend...")
    
    backend_code = '''#!/usr/bin/env python3
"""
Real LLM Backend for Port 8767 - Actually calls Ollama
"""

import asyncio
import json
import logging
import websockets
import time
import requests
from datetime import datetime
from typing import Dict, Any, Set
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/real_llm_8767.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatMode(str, Enum):
    AGENT = "Agent"
    ASK = "Ask" 
    SUGGEST = "Suggest"
    GENERAL = "General"

class RealLLMBackend8767:
    def __init__(self):
        self.connected_clients: Set[str] = set()
        self.sessions: Dict[str, Dict] = {}
        self.start_time = datetime.now()
        self.ollama_url = "http://localhost:11434"
        self.model = "llama3.2:1b"  # Fast model
        
        logger.info("Real LLM Backend 8767 initialized")

    async def handle_websocket(self, websocket):
        """Handle WebSocket connections on port 8767"""
        client_id = f"client_{int(time.time() * 1000)}"
        try:
            self.connected_clients.add(client_id)
            logger.info(f"Client connected: {client_id} from {websocket.remote_address[0]}")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"Processing {data.get('type', 'unknown')} from {client_id}")
                    
                    if data.get("type") == "chat_request":
                        response = await self.handle_chat_request(data, client_id)
                        await websocket.send(json.dumps(response))
                    elif data.get("type") == "register":
                        response = await self.handle_register(data, client_id)
                        await websocket.send(json.dumps(response))
                    else:
                        # Handle other message types with default response
                        response = {
                            "type": f"{data.get('type', 'unknown')}_response",
                            "success": True,
                            "client_id": client_id,
                            "timestamp": datetime.now().isoformat()
                        }
                        await websocket.send(json.dumps(response))
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from {client_id}: {e}")
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}")
                    
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {e}")
        finally:
            self.connected_clients.discard(client_id)
            logger.info(f"Client disconnected: {client_id}")

    async def handle_register(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle client registration"""
        return {
            "type": "registration_success",
            "connection_id": client_id,
            "server_capabilities": ["real_llm_responses", "chat_modes", "contextual_responses"],
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }

    async def handle_chat_request(self, data: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        """Handle chat requests with REAL LLM calls"""
        mode = data.get("mode", "General")
        message = data.get("message", "")
        session_id = data.get("session_id", client_id)
        
        if not message.strip():
            return {
                "type": "final_response",
                "mode": mode,
                "response": f"{self.get_mode_prefix(mode)} Please provide a message to respond to.",
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # Call real LLM
            llm_response = await self.call_ollama(message, mode)
            
            # Format response with mode prefix
            formatted_response = f"{self.get_mode_prefix(mode)} {llm_response}"
            
            return {
                "type": "final_response",
                "mode": mode,
                "response": formatted_response,
                "ai_powered": True,
                "model_used": self.model,
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in chat request: {e}")
            return {
                "type": "final_response",
                "mode": mode,
                "response": f"{self.get_mode_prefix(mode)} I apologize, but I'm having trouble processing your request right now. Error: {str(e)}",
                "error": str(e),
                "client_id": client_id,
                "timestamp": datetime.now().isoformat()
            }

    async def call_ollama(self, message: str, mode: str) -> str:
        """Make actual API call to Ollama"""
        try:
            # Create mode-specific system prompt
            system_prompt = self.get_system_prompt(mode)
            
            # Prepare the request
            payload = {
                "model": self.model,
                "prompt": f"System: {system_prompt}\\n\\nUser: {message}\\n\\nAssistant:",
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            }
            
            # Make the request (synchronous in async function)
            import asyncio
            import functools
            
            def make_request():
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=20  # Increased timeout
                )
                response.raise_for_status()
                return response.json()
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, make_request)
            
            return result.get("response", "I don't have a response for that.").strip()
            
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise Exception(f"LLM service unavailable: {str(e)}")

    def get_mode_prefix(self, mode: str) -> str:
        """Get the prefix for each mode"""
        prefixes = {
            "Agent": "🤖 Agent Mode:",
            "Ask": "💭 Ask Mode:",
            "Suggest": "✨ Suggest Mode:",
            "General": "🧠 AI Assistant:"
        }
        return prefixes.get(mode, "🧠 AI Assistant:")

    def get_system_prompt(self, mode: str) -> str:
        """Get system prompt for each mode"""
        prompts = {
            "Agent": "You are an AI agent specialized in helping with tasks and automation. Provide practical, actionable guidance. Be direct and helpful.",
            "Ask": "You are an AI assistant specialized in answering questions with depth and accuracy. Provide comprehensive, informative answers.",
            "Suggest": "You are an AI assistant specialized in providing helpful suggestions and recommendations. Offer practical, actionable advice.",
            "General": "You are a helpful AI assistant. Respond naturally and helpfully to the user's message."
        }
        return prompts.get(mode, prompts["General"])

async def main():
    backend = RealLLMBackend8767()
    
    # Start WebSocket server on port 8767
    logger.info("Starting Real LLM Backend on port 8767...")
    
    async with websockets.serve(backend.handle_websocket, "localhost", 8767):
        logger.info("✅ Real LLM Backend is running on ws://localhost:8767")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    # Write the new backend
    with open("/Users/segevbin/Desktop/SensAI/Aiayer/real_llm_backend_8767.py", "w") as f:
        f.write(backend_code)
    
    print("✅ Created real_llm_backend_8767.py")
    return True

if __name__ == "__main__":
    print("🚀 Fixing AI System Response Issues")
    print("="*50)
    
    # Step 1: Test Ollama
    if fix_real_responses():
        print("\n✅ Ollama is working correctly!")
        
        # Step 2: Create real LLM backend
        if create_real_llm_backend():
            print("\n🎉 Solution created!")
            print("\n📋 NEXT STEPS:")
            print("1. Stop the current backend:")
            print("   kill $(lsof -ti:8767)")
            print("\n2. Start the new real LLM backend:")
            print("   python3 real_llm_backend_8767.py")
            print("\n3. Test your chat - it should now give real AI responses!")
            print("\n💡 The new backend will actually call Ollama and give real responses")
        else:
            print("❌ Failed to create solution")
    else:
        print("❌ Ollama is not working properly")
        print("💡 Try running: ollama serve")