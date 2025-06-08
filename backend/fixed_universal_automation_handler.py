import json
import re
import logging
import asyncio
import websockets
from llm.llm_service import LLMService
from real_agent_automation_handler import RealAgentAutomationHandler

logger = logging.getLogger(__name__)

# Global instances
llm_service = None
agent_handler = None

async def initialize_services():
    """Initialize global service instances."""
    global llm_service, agent_handler
    
    if llm_service is None:
        llm_service = LLMService()
        await llm_service.initialize()
        logger.info("Global LLM service initialized")
    
    if agent_handler is None:
        agent_handler = RealAgentAutomationHandler()
        await agent_handler.initialize()
        logger.info("Global agent handler initialized")

def parse_llm_response(response):
    try:
        # Try to parse as JSON
        return json.loads(response)
    except json.JSONDecodeError:
        # If JSON parsing fails, handle as markdown
        # Extract the URL from the markdown
        url_match = re.search(r'url "([^"]+)"', response)
        if url_match:
            return {"action": "open_safari", "url": url_match.group(1)}
        else:
            return {"error": "Could not parse response"}

async def handle_contextual_chat_request_streaming(websocket, path):
    try:
        # Ensure services are initialized
        await initialize_services()

        async for message in websocket:
            try:
                data = json.loads(message)
                query = data.get('query', '')
                mode = data.get('mode', 'general')
                
                if not query:
                    await websocket.send(json.dumps({"error": "No query provided"}))
                    continue

                if mode == 'agent':
                    # Generate task ID
                    task_id = f"task_{int(asyncio.get_event_loop().time() * 1000)}_{hash(query) & 0xffffffff:08x}"
                    
                    # Create and execute plan
                    plan = await agent_handler.create_plan(task_id, query)
                    if plan:
                        # Send initial plan
                        await websocket.send(json.dumps({
                            "type": "plan",
                            "content": {
                                "task_id": task_id,
                                "steps": plan.steps
                            }
                        }))
                        
                        # Execute plan
                        success = await agent_handler.execute_plan(task_id)
                        
                        # Send execution result
                        await websocket.send(json.dumps({
                            "type": "execution_result",
                            "content": {
                                "task_id": task_id,
                                "success": success
                            }
                        }))
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "content": "Failed to create plan"
                        }))
                else:
                    # For other modes, use the standard response method
                    async for chunk in llm_service.generate_response(query):
                        try:
                            await websocket.send(json.dumps({
                                "type": "chunk",
                                "content": chunk
                            }))
                        except websockets.exceptions.ConnectionClosed:
                            logger.warning("Client disconnected during streaming")
                            break

                # Send completion message
                await websocket.send(json.dumps({
                    "type": "complete",
                    "content": "Response complete"
                }))

            except json.JSONDecodeError:
                await websocket.send(json.dumps({"error": "Invalid JSON format"}))
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                await websocket.send(json.dumps({"error": str(e)}))
    except websockets.exceptions.ConnectionClosed:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Error in handle_contextual_chat_request_streaming: {e}", exc_info=True)
    finally:
        await websocket.close()

# ... existing code ... 