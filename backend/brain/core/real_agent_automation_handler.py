from typing import Dict, Any, AsyncGenerator
import asyncio
import logging

logger = logging.getLogger(__name__)

async def handle_real_agent_automation(query: str, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Handle real agent automation with streaming response formatting."""
    try:
        # Initialize handler
        handler = RealAgentAutomationHandler()
        await handler.initialize()
        
        # Stream initial response
        yield {
            "type": "status",
            "response": "🤖 Creating automation plan...",
            "success": True
        }
        
        # Create plan
        plan = await handler.create_plan(session_id, query)
        if not plan:
            yield {
                "type": "error",
                "response": "Failed to create automation plan",
                "success": False,
                "confidence": 0.0,
                "metadata": {"error": "Plan creation failed"}
            }
            return
            
        # Stream plan header
        yield {
            "type": "plan_header",
            "response": f"🤖 **Automation Plan**\n\nTask: {query}\n\nSteps:",
            "success": True
        }
        
        # Stream each step
        for i, step in enumerate(plan.steps, 1):
            yield {
                "type": "plan_step",
                "response": f"{i}. {step['description']}",
                "success": True,
                "step_number": i,
                "total_steps": len(plan.steps)
            }
            await asyncio.sleep(0.1)  # Small delay between steps for better UX
            
        # Stream final response with full plan
        plan_text = f"🤖 **Automation Plan**\n\nTask: {query}\n\nSteps:\n"
        for i, step in enumerate(plan.steps, 1):
            plan_text += f"{i}. {step['description']}\n"
            
        yield {
            "type": "final_response",
            "response": plan_text,
            "success": True,
            "confidence": 0.8,
            "metadata": {
                "plan_id": plan.task_id,
                "steps_count": len(plan.steps),
                "has_plan": True,
                "has_steps": True
            },
            "execution_plan": {
                "response": plan_text,
                "steps": plan.steps,
                "task_id": plan.task_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error in real agent automation: {e}")
        yield {
            "type": "error",
            "response": f"Error creating automation plan: {str(e)}",
            "success": False,
            "confidence": 0.0,
            "metadata": {"error": str(e)}
        } 