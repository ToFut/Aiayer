import asyncio
import json
import logging
from datetime import datetime
from plan_persistence import save_plan, load_plan

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_test_plan():
    """Create a test plan for execution"""
    # Create a test plan
    plan_id = f"test_plan_{int(datetime.now().timestamp())}"
    plan_data = {
        "plan_id": plan_id,
        "title": "Test Automation Plan",
        "created": datetime.now().timestamp(),
        "modified": datetime.now().timestamp(),
        "status": "pending",
        "client_id": "test_client",
        "context": {
            "user_prompt": "Test automation task",
            "current_application": "test_app",
            "current_window": "test_window"
        },
        "plan": {
            "steps": [
                {
                    "type": "click",
                    "description": "Click test button",
                    "coordinates": {"x": 100, "y": 100}
                }
            ]
        },
        "fast": True  # Use fast automation handler
    }
    
    # Save the plan
    success = await save_plan(plan_id, plan_data)
    if success:
        logger.info(f"✅ Created test plan: {plan_id}")
        return plan_id
    else:
        logger.error("❌ Failed to create test plan")
        return None

async def test_plan_execution():
    """Test the plan execution flow"""
    try:
        # Create a test plan
        plan_id = await create_test_plan()
        if not plan_id:
            return
        
        # Load the plan to verify it was saved
        plan_data = await load_plan(plan_id)
        if not plan_data:
            logger.error("❌ Could not load test plan")
            return
            
        logger.info(f"✅ Successfully loaded test plan: {plan_id}")
        logger.info(f"Plan data: {json.dumps(plan_data, indent=2)}")
        
        # Import the backend
        from enhanced_enterprise_backend_with_context import ContextualAIBackend
        
        # Create backend instance
        backend = ContextualAIBackend()
        
        # Test plan execution
        logger.info("🚀 Testing plan execution...")
        result = await backend.execute_verified_plan(plan_id)
        
        logger.info(f"Execution result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_plan_execution()) 