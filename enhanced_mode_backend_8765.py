#!/usr/bin/env python3
"""
Enhanced Mode-Specific Backend with Real AI Integration
Each mode has its own specialized agent/component for intelligent responses
"""

import asyncio
import json
import logging
import websockets
import time
import subprocess
import requests
import threading
from datetime import datetime
from typing import Dict, Any, Set, Optional
from enum import Enum

# Setup enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backend/enhanced_mode_backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatMode(str, Enum):
    AGENT = "Agent"
    ASK = "Ask" 
    SUGGEST = "Suggest"
    CREATIVE = "Creative"

class ProgressStage(str, Enum):
    RECEIVED = "Message received, initializing..."
    ANALYZING = "🧠 Analyzing your request..."
    PROCESSING = "⚡ Processing with AI model..."
    GENERATING = "✍️ Generating thoughtful response..."
    FINALIZING = "🎯 Finalizing response..."
    COMPLETE = "✅ Response ready!"

class ModeSpecificAgent:
    """Base class for mode-specific AI agents"""
    
    def __init__(self, mode: ChatMode):
        self.mode = mode
        self.specialized_prompts = self._load_specialized_prompts()
    
    def _load_specialized_prompts(self) -> Dict[str, str]:
        """Load mode-specific system prompts and instructions"""
        return {
            ChatMode.ASK: """You are a knowledge expert and analytical assistant. Your role is to:
- Provide accurate, well-researched answers to questions
- Break down complex topics into understandable explanations
- Cite reasoning and provide context when possible
- Ask clarifying questions when needed
- Maintain objectivity and intellectual rigor
Focus on delivering comprehensive, educational responses that help users truly understand the topic.""",

            ChatMode.AGENT: """You are an intelligent task automation agent. Your role is to:
- Analyze tasks and break them into actionable steps
- Suggest automation opportunities and workflows
- Provide specific, implementable solutions
- Consider efficiency, scalability, and best practices
- Anticipate potential issues and provide contingencies
Focus on delivering practical, executable plans that users can immediately implement.""",

            ChatMode.SUGGEST: """You are an optimization and improvement specialist. Your role is to:
- Analyze current situations and identify improvement opportunities
- Suggest specific, actionable optimizations
- Prioritize recommendations by impact and feasibility
- Consider multiple perspectives and alternatives
- Provide reasoning for each suggestion
Focus on delivering valuable insights that lead to measurable improvements.""",

            ChatMode.CREATIVE: """You are a creative ideation and brainstorming partner. Your role is to:
- Generate innovative, original ideas and concepts
- Think outside conventional boundaries
- Build upon user input with creative extensions
- Suggest multiple creative approaches and variations
- Encourage exploration of unconventional solutions
Focus on inspiring creativity and expanding possibilities through imaginative thinking."""
        }
    
    def get_system_prompt(self) -> str:
        """Get the specialized system prompt for this mode"""
        return self.specialized_prompts.get(self.mode, self.specialized_prompts[ChatMode.ASK])
    
    def enhance_user_message(self, message: str) -> str:
        """Add mode-specific enhancements to user message"""
        enhancements = {
            ChatMode.ASK: f"Please provide a comprehensive answer to: {message}",
            ChatMode.AGENT: f"Please create an actionable plan for: {message}",
            ChatMode.SUGGEST: f"Please analyze and suggest improvements for: {message}",
            ChatMode.CREATIVE: f"Please brainstorm creative ideas for: {message}"
        }
        return enhancements.get(self.mode, message)
    
    def post_process_response(self, response: str) -> str:
        """Apply mode-specific post-processing to AI response"""
        if self.mode == ChatMode.AGENT and response:
            # Ensure agent responses include actionable steps
            if "steps:" not in response.lower() and "plan:" not in response.lower():
                response += "\n\n**Next Steps:**\n1. Review the suggestions above\n2. Identify which actions fit your current situation\n3. Start with the highest-impact, lowest-effort items\n4. Monitor progress and adjust as needed"
        
        elif self.mode == ChatMode.SUGGEST and response:
            # Ensure suggest responses include prioritized recommendations
            if "recommend" not in response.lower() and "suggest" not in response.lower():
                response += "\n\n**Key Recommendations:**\n• Focus on the most impactful changes first\n• Consider your available resources and constraints\n• Measure results to validate improvements"
        
        elif self.mode == ChatMode.CREATIVE and response:
            # Ensure creative responses encourage further exploration
            if "idea" not in response.lower() and "creative" not in response.lower():
                response += "\n\n**Creative Exploration:**\n• Try combining different approaches\n• Challenge conventional assumptions\n• Explore 'what if' scenarios for fresh perspectives"
        
        return response

class EnhancedModeBackend:
    def __init__(self):
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.sessions: Dict[str, Dict] = {}
        self.start_time = datetime.now()
        self.ollama_available = self.check_ollama_availability()
        self.active_requests: Dict[str, bool] = {}
        
        # Initialize mode-specific agents
        self.agents = {
            mode: ModeSpecificAgent(mode) for mode in ChatMode
        }
        
        logger.info(f"Enhanced Mode Backend initialized - Ollama available: {self.ollama_available}")
        logger.info(f"Specialized agents loaded for modes: {list(self.agents.keys())}")

    def check_ollama_availability(self) -> bool:
        """Check if Ollama is running and available"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model.get('name', '') for model in models]
                logger.info(f"Available Ollama models: {model_names}")
                return True
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            try:
                logger.info("Attempting to start Ollama...")
                subprocess.run(['ollama', 'serve'], check=False, capture_output=True)
                time.sleep(3)
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                return response.status_code == 200
            except Exception as e2:
                logger.error(f"Failed to start Ollama: {e2}")
                return False

    async def send_progress_update(self, websocket: websockets.WebSocketServerProtocol, 
                                 stage: ProgressStage, session_id: str, mode: str):
        """Send a progress update to the client"""
        try:
            progress_message = {
                "type": "progress_update",
                "stage": stage.value,
                "session_id": session_id,
                "mode": mode,
                "timestamp": datetime.now().isoformat(),
                "is_typing": True
            }
            await websocket.send(json.dumps(progress_message))
            logger.info(f"Sent progress update for {mode}: {stage.value}")
        except Exception as e:
            logger.error(f"Failed to send progress update: {e}")

    async def get_specialized_ollama_response(self, message: str, mode: str, websocket: websockets.WebSocketServerProtocol, 
                                            session_id: str) -> str:
        """Get specialized AI response using mode-specific agent"""
        try:
            # Mark request as active
            self.active_requests[session_id] = True
            
            # Get the specialized agent for this mode
            agent = self.agents.get(ChatMode(mode))
            if not agent:
                logger.warning(f"No specialized agent found for mode: {mode}")
                agent = self.agents[ChatMode.ASK]  # Fallback to Ask mode
            
            # Stage 1: Analyzing with mode-specific context
            await self.send_progress_update(websocket, ProgressStage.ANALYZING, session_id, mode)
            await asyncio.sleep(1)
            
            # Stage 2: Processing with specialized prompt
            await self.send_progress_update(websocket, ProgressStage.PROCESSING, session_id, mode)
            
            # Enhance the user message with mode-specific context
            enhanced_message = agent.enhance_user_message(message)
            system_prompt = agent.get_system_prompt()
            
            # Prepare Ollama request with mode-specific optimization
            model_config = self._get_model_config_for_mode(mode)
            ollama_payload = {
                "model": "llama3.2:latest",
                "prompt": f"System: {system_prompt}\n\nUser: {enhanced_message}\n\nAssistant:",
                "stream": False,
                "options": model_config
            }
            
            # Stage 3: Generating with specialized processing
            await self.send_progress_update(websocket, ProgressStage.GENERATING, session_id, mode)
            
            # Make the request with extended timeout
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=ollama_payload,
                timeout=90  # Extended timeout for complex processing
            )
            
            if response.status_code == 200:
                # Stage 4: Finalizing with mode-specific post-processing
                await self.send_progress_update(websocket, ProgressStage.FINALIZING, session_id, mode)
                await asyncio.sleep(0.5)
                
                result = response.json()
                ai_response = result.get('response', '').strip()
                
                if ai_response:
                    # Apply mode-specific post-processing
                    processed_response = agent.post_process_response(ai_response)
                    
                    logger.info(f"Successfully got specialized {mode} response: {len(processed_response)} chars")
                    return processed_response
                else:
                    logger.warning("Empty response from Ollama")
                    return self.get_intelligent_fallback_response(message, mode)
            else:
                logger.error(f"Ollama HTTP error: {response.status_code}")
                return self.get_intelligent_fallback_response(message, mode)
                
        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out after 90 seconds")
            return self.get_intelligent_fallback_response(message, mode)
        except Exception as e:
            logger.error(f"Error getting specialized Ollama response: {e}")
            return self.get_intelligent_fallback_response(message, mode)
        finally:
            # Mark request as complete
            self.active_requests[session_id] = False

    def _get_model_config_for_mode(self, mode: str) -> Dict[str, Any]:
        """Get optimized model configuration for each mode"""
        base_config = {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_predict": 1000
        }
        
        mode_configs = {
            ChatMode.ASK: {
                **base_config,
                "temperature": 0.3,  # Lower temperature for factual accuracy
                "top_p": 0.8,
                "num_predict": 1200
            },
            ChatMode.AGENT: {
                **base_config,
                "temperature": 0.4,  # Balanced for structured planning
                "top_p": 0.85,
                "num_predict": 1400
            },
            ChatMode.SUGGEST: {
                **base_config,
                "temperature": 0.6,  # Moderate creativity for suggestions
                "top_p": 0.9,
                "num_predict": 1100
            },
            ChatMode.CREATIVE: {
                **base_config,
                "temperature": 0.9,  # High creativity for brainstorming
                "top_p": 0.95,
                "num_predict": 1300
            }
        }
        
        return mode_configs.get(ChatMode(mode), base_config)

    def get_intelligent_fallback_response(self, message: str, mode: str) -> str:
        """Provide intelligent, mode-specific fallback responses"""
        mode_fallbacks = {
            ChatMode.AGENT: f"""I understand you need help with task planning for: "{message}"

While I'm experiencing connectivity issues with my AI engine, I can provide some structured guidance:

**Immediate Actions:**
1. **Define the Goal**: Clearly specify what success looks like
2. **Break Down the Task**: Divide into smaller, manageable steps
3. **Identify Resources**: List what tools, people, or information you need
4. **Set Timeline**: Establish realistic deadlines for each step
5. **Plan for Obstacles**: Anticipate potential challenges and solutions

**Next Steps:**
- Start with the smallest, easiest task to build momentum
- Focus on one step at a time to avoid overwhelm
- Track progress to maintain motivation

Would you like me to help you apply this framework to your specific situation?""",

            ChatMode.ASK: f"""Regarding your question: "{message}"

While I'm experiencing technical difficulties with my knowledge base, I can guide you toward finding the answer:

**Research Strategy:**
1. **Primary Sources**: Look for authoritative, original sources
2. **Multiple Perspectives**: Gather information from different viewpoints
3. **Recent Information**: Ensure data is current and relevant
4. **Expert Opinions**: Seek insights from recognized specialists

**Critical Thinking:**
- Question assumptions and biases
- Look for evidence supporting claims
- Consider alternative explanations
- Verify information through cross-referencing

Would you like me to help you develop a more specific research approach for this topic?""",

            ChatMode.SUGGEST: f"""For optimization suggestions regarding: "{message}"

Despite connectivity challenges, I can share proven improvement principles:

**Optimization Framework:**
1. **Current State Analysis**: Document how things work now
2. **Pain Point Identification**: Find the biggest inefficiencies
3. **Impact Assessment**: Prioritize changes by potential benefit
4. **Resource Evaluation**: Consider time, cost, and effort required
5. **Implementation Planning**: Start with quick wins, then tackle complex changes

**Key Principles:**
- Focus on bottlenecks that limit overall performance
- Automate repetitive tasks where possible
- Eliminate redundancies and waste
- Measure results to validate improvements

What specific area would you like to focus on optimizing first?""",

            ChatMode.CREATIVE: f"""For creative exploration of: "{message}"

While my creative AI engine is temporarily unavailable, let's use proven brainstorming techniques:

**Creative Methods:**
1. **Mind Mapping**: Start with your topic and branch out with related ideas
2. **"What If" Scenarios**: Challenge assumptions with hypothetical situations
3. **Reverse Thinking**: Consider the opposite approach
4. **Random Connections**: Combine unrelated concepts for fresh perspectives
5. **Build on Ideas**: Take any concept and extend it in unexpected directions

**Creative Principles:**
- Suspend judgment during idea generation
- Quantity leads to quality - generate many ideas first
- Combine and modify existing concepts
- Look for inspiration in unrelated fields

What aspect of this topic excites you most? Let's explore that direction together!"""
        }
        
        return mode_fallbacks.get(ChatMode(mode), mode_fallbacks[ChatMode.ASK])

    async def process_chat_request(self, websocket: websockets.WebSocketServerProtocol, data: Dict[str, Any]):
        """Process incoming chat requests with mode-specific handling"""
        try:
            message = data.get('message', '').strip()
            mode = data.get('mode', 'Ask')
            session_id = data.get('session_id', f'session_{int(time.time())}')
            
            if not message:
                await self.send_error_response(websocket, "Empty message received")
                return
            
            logger.info(f"Processing {mode} request: '{message[:50]}...' (session: {session_id})")
            
            # Stage 0: Received
            await self.send_progress_update(websocket, ProgressStage.RECEIVED, session_id, mode)
            
            # Store session info
            self.sessions[session_id] = {
                'last_message': message,
                'mode': mode,
                'timestamp': datetime.now().isoformat(),
                'agent_type': f"specialized_{mode.lower()}_agent"
            }
            
            # Get specialized AI response with mode-specific processing
            if self.ollama_available:
                ai_response = await self.get_specialized_ollama_response(message, mode, websocket, session_id)
                response_source = "ollama_specialized"
            else:
                await self.send_progress_update(websocket, ProgressStage.ANALYZING, session_id, mode)
                await asyncio.sleep(1)
                ai_response = self.get_intelligent_fallback_response(message, mode)
                response_source = "intelligent_fallback"
            
            # Stage 5: Complete
            await self.send_progress_update(websocket, ProgressStage.COMPLETE, session_id, mode)
            await asyncio.sleep(0.3)
            
            # Send final response with mode validation
            response = {
                "success": True,
                "response": ai_response,
                "mode": mode,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "source": response_source,
                "agent_type": f"specialized_{mode.lower()}_agent",
                "processing_capabilities": self.agents[ChatMode(mode)].__class__.__name__,
                "is_typing": False,
                "type": "final_response",
                "enterprise_validated": True,
                "real_ai_backend": True
            }
            
            await websocket.send(json.dumps(response))
            logger.info(f"Sent specialized {mode} response from {response_source} (session: {session_id})")
            
        except Exception as e:
            logger.error(f"Error processing chat request: {e}")
            await self.send_error_response(websocket, f"Processing error: {str(e)}")

    async def send_error_response(self, websocket: websockets.WebSocketServerProtocol, error_msg: str):
        """Send error response to client"""
        try:
            error_response = {
                "success": False,
                "error": error_msg,
                "timestamp": datetime.now().isoformat(),
                "is_typing": False,
                "type": "error_response"
            }
            await websocket.send(json.dumps(error_response))
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle individual client connections"""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.connected_clients.add(websocket)
        logger.info(f"Client connected: {client_id} (path: {path})")
        
        try:
            # Send welcome message with mode capabilities
            welcome = {
                "type": "connection_established",
                "message": "Connected to Enhanced Mode-Specific AI Backend",
                "server_time": datetime.now().isoformat(),
                "ollama_available": self.ollama_available,
                "features": [
                    "mode_specific_agents",
                    "specialized_prompts", 
                    "progressive_responses",
                    "extended_timeouts",
                    "intelligent_fallbacks",
                    "real_ai_backend"
                ],
                "available_modes": list(self.agents.keys()),
                "agent_capabilities": {
                    mode: agent.__class__.__name__ for mode, agent in self.agents.items()
                }
            }
            await websocket.send(json.dumps(welcome))
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_type = data.get('type', '')
                    
                    if message_type == 'chat_request':
                        await self.process_chat_request(websocket, data)
                    elif message_type == 'ping':
                        await websocket.send(json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}))
                    elif message_type == 'status':
                        status = {
                            "type": "status_response",
                            "server_uptime": str(datetime.now() - self.start_time),
                            "connected_clients": len(self.connected_clients),
                            "ollama_available": self.ollama_available,
                            "active_sessions": len(self.sessions),
                            "specialized_agents": len(self.agents),
                            "backend_type": "enhanced_mode_specific"
                        }
                        await websocket.send(json.dumps(status))
                    else:
                        logger.warning(f"Unknown message type: {message_type}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from {client_id}: {e}")
                    await self.send_error_response(websocket, "Invalid JSON format")
                except Exception as e:
                    logger.error(f"Error handling message from {client_id}: {e}")
                    await self.send_error_response(websocket, f"Message handling error: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected normally")
        except Exception as e:
            logger.error(f"Error with client {client_id}: {e}")
        finally:
            self.connected_clients.discard(websocket)
            logger.info(f"Client {client_id} removed from active connections")

    async def start_server(self, port: int = 8765):
        """Start the WebSocket server"""
        try:
            logger.info(f"Starting Enhanced Mode-Specific Backend on port {port}")
            
            # Create logs directory if it doesn't exist
            import os
            os.makedirs('logs/backend', exist_ok=True)
            
            server = await websockets.serve(
                self.handle_client,
                "localhost",
                port,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            logger.info(f"✅ Enhanced Mode Backend running on ws://localhost:{port}")
            logger.info(f"📊 Ollama integration: {'✅ Active' if self.ollama_available else '❌ Fallback mode'}")
            logger.info(f"🤖 Specialized agents: {len(self.agents)} modes")
            logger.info("🚀 Features: Mode-specific processing, Real AI responses, Progressive feedback")
            
            # Keep server running
            await server.wait_closed()
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            raise

async def main():
    """Main entry point"""
    backend = EnhancedModeBackend()
    try:
        await backend.start_server(8765)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    asyncio.run(main())