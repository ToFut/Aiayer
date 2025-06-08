#!/usr/bin/env python3
"""
Plan Persistence System - Manages storage and retrieval of automation plans
"""

import os
import json
import time
import uuid
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
# Plan ID generation
def generate_plan_id(prefix="plan"):
    '''Generate a unique plan ID with the given prefix'''
    import time
    import uuid
    return f"{prefix}_{int(time.time())}_{str(uuid.uuid4())[:8]}"


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
STORAGE_DIR = os.path.join("cache", "plans")
os.makedirs(STORAGE_DIR, exist_ok=True)

@dataclass
class NextStepSuggestion:
    """Represents a suggested next step for a plan"""
    title: str
    description: str
    type: str = "unknown"
    priority: float = 0.5
    estimated_duration: float = 2.0

@dataclass
class PlanMetadata:
    """Metadata for a stored plan"""
    plan_id: str
    title: str
    created: float
    modified: float
    status: str = "pending"
    step_count: int = 0
    active: bool = True
    tags: List[str] = field(default_factory=list)

class PlanPersistenceManager:
    """Manages persistence of automation plans"""
    def __init__(self):
        self.metadata: Dict[str, PlanMetadata] = {}
        self.storage_dir = STORAGE_DIR
        self.loaded = False
    
    async def start(self):
        """Initialize the persistence manager"""
        if self.loaded:
            return
            
        os.makedirs(self.storage_dir, exist_ok=True)
        await self.load_metadata()
        self.loaded = True
        logger.info(f"Loaded {len(self.metadata)} plans from metadata")
    
    async def load_metadata(self):
        """Load metadata for all plans"""
        try:
            metadata_path = os.path.join(self.storage_dir, "metadata.json")
            if os.path.exists(metadata_path):
                with open(metadata_path, "r") as f:
                    metadata_dict = json.load(f)
                    
                # Convert dict to PlanMetadata objects
                for plan_id, data in metadata_dict.items():
                    self.metadata[plan_id] = PlanMetadata(
                        plan_id=plan_id,
                        title=data.get("title", "Untitled"),
                        created=data.get("created", time.time()),
                        modified=data.get("modified", time.time()),
                        status=data.get("status", "pending"),
                        step_count=data.get("step_count", 0),
                        active=data.get("active", True),
                        tags=data.get("tags", [])
                    )
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
    
    async def save_metadata(self):
        """Save metadata for all plans"""
        try:
            metadata_path = os.path.join(self.storage_dir, "metadata.json")
            metadata_dict = {}
            
            # Convert PlanMetadata objects to dict
            for plan_id, metadata in self.metadata.items():
                metadata_dict[plan_id] = {
                    "title": metadata.title,
                    "created": metadata.created,
                    "modified": metadata.modified,
                    "status": metadata.status,
                    "step_count": metadata.step_count,
                    "active": metadata.active,
                    "tags": metadata.tags
                }
                
            with open(metadata_path, "w") as f:
                json.dump(metadata_dict, f)
                
            logger.info(f"Saved metadata for {len(self.metadata)} plans")
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    async def load_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Load a plan from storage"""
        if not self.loaded:
            await self.start()
            
        try:
            # Sanitize plan_id for filename compatibility
            safe_plan_id = plan_id.replace(':', '_').replace('/', '_').replace('\\', '_')
            
            # First try with the original plan_id
            plan_path = os.path.join(self.storage_dir, f"{plan_id}.json")
            if os.path.exists(plan_path):
                with open(plan_path, "r") as f:
                    plan_data = json.load(f)
                    logger.info(f"✅ Loaded plan from {plan_path}")
                    return plan_data
                    
            # Then try with sanitized plan_id
            if safe_plan_id != plan_id:
                plan_path = os.path.join(self.storage_dir, f"{safe_plan_id}.json")
                if os.path.exists(plan_path):
                    with open(plan_path, "r") as f:
                        plan_data = json.load(f)
                        logger.info(f"✅ Loaded plan from sanitized path: {plan_path}")
                        return plan_data
            
            # Check if metadata.json has this plan
            try:
                metadata_path = os.path.join(self.storage_dir, "metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                        logger.info(f"Available plan metadata: {list(metadata.keys())}")
                        
                        # Try to find a matching plan by session_id
                        for stored_plan_id, plan_data in metadata.items():
                            if plan_id in stored_plan_id or stored_plan_id in plan_id:
                                plan_path = os.path.join(self.storage_dir, f"{stored_plan_id}.json")
                                if os.path.exists(plan_path):
                                    with open(plan_path, "r") as f:
                                        plan_data = json.load(f)
                                        logger.info(f"✅ Found matching plan: {stored_plan_id}")
                                        return plan_data
            except Exception as e:
                logger.warning(f"Could not read metadata file: {e}")
                
            # List all files in the directory
            try:
                plan_files = os.listdir(self.storage_dir)
                if plan_files:
                    logger.info(f"Available plan files: {plan_files}")
                    
                    # Try to find a matching plan by session_id
                    for filename in plan_files:
                        if filename.endswith('.json') and not filename == 'metadata.json':
                            if plan_id in filename or filename.replace('.json', '') in plan_id:
                                plan_path = os.path.join(self.storage_dir, filename)
                                with open(plan_path, "r") as f:
                                    plan_data = json.load(f)
                                    logger.info(f"✅ Found matching plan file: {filename}")
                                    return plan_data
            except Exception as e:
                logger.warning(f"Could not list directory: {e}")
                
            logger.warning(f"Plan not found: {plan_id}")
            return None
        except Exception as e:
            logger.error(f"Error loading plan {plan_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def save_plan(self, plan_id: str, plan_data: Dict[str, Any]) -> bool:
        """Save a plan to storage"""
        if not self.loaded:
            await self.start()
            
        try:
            # Extract metadata
            title = plan_data.get("title", "Untitled")
            step_count = len(plan_data.get("steps", []))
            status = plan_data.get("status", "pending")
            created = plan_data.get("created", time.time())
            modified = time.time()
            
            # Update metadata
            self.metadata[plan_id] = PlanMetadata(
                plan_id=plan_id,
                title=title,
                created=created,
                modified=modified,
                status=status,
                step_count=step_count,
                active=True,
                tags=[]
            )
            
            # Save plan data
            plan_path = os.path.join(self.storage_dir, f"{plan_id}.json")
            with open(plan_path, "w") as f:
                json.dump(plan_data, f)
                
            # Also save a copy with session_id if different
            if "session_id" in plan_data and plan_data["session_id"] != plan_id:
                session_id = plan_data["session_id"]
                session_path = os.path.join(self.storage_dir, f"{session_id}.json")
                with open(session_path, "w") as f:
                    json.dump(plan_data, f)
                logger.info(f"✅ Saved plan with session_id: {session_id}")
            
            # Save metadata
            await self.save_metadata()
            
            logger.info(f"✅ Saved plan: {plan_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving plan {plan_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def delete_plan(self, plan_id: str) -> bool:
        """Delete a plan from storage"""
        if not self.loaded:
            await self.start()
            
        try:
            plan_path = os.path.join(self.storage_dir, f"{plan_id}.json")
            if os.path.exists(plan_path):
                os.remove(plan_path)
                
            # Update metadata
            if plan_id in self.metadata:
                del self.metadata[plan_id]
                await self.save_metadata()
                
            logger.info(f"Deleted plan {plan_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting plan {plan_id}: {e}")
            return False
    
    async def get_all_plan_metadata(self) -> List[Dict[str, Any]]:
        """Get metadata for all plans"""
        if not self.loaded:
            await self.start()
            
        try:
            result = []
            for plan_id, metadata in self.metadata.items():
                result.append({
                    "plan_id": plan_id,
                    "title": metadata.title,
                    "created": metadata.created,
                    "modified": metadata.modified,
                    "status": metadata.status,
                    "step_count": metadata.step_count,
                    "active": metadata.active,
                    "tags": metadata.tags
                })
            return result
        except Exception as e:
            logger.error(f"Error getting plan metadata: {e}")
            return []

# Create singleton instance
plan_manager = PlanPersistenceManager()

# Convenience functions
async def load_plan(plan_id: str, plan_manager_instance=None) -> Optional[Dict[str, Any]]:
    """Load a plan from persistent storage"""
    logger.info(f"🔍 Loading plan with ID: {plan_id}")
    
    # Sanitize plan_id for filename compatibility (replace any characters that might cause issues)
    safe_plan_id = plan_id.replace(':', '_').replace('/', '_').replace('\\', '_')
    
    # Try to load with the given plan_id first
    instance = plan_manager_instance or plan_manager
    plan = await instance.load_plan(plan_id)
    
    if plan:
        logger.info(f"✅ Successfully loaded plan: {plan_id}")
        return plan
        
    # If not found, try loading with sanitized ID
    if safe_plan_id != plan_id:
        logger.info(f"🔄 Trying sanitized plan ID: {safe_plan_id}")
        plan = await instance.load_plan(safe_plan_id)
        if plan:
            logger.info(f"✅ Successfully loaded plan with sanitized ID: {safe_plan_id}")
            return plan
    
    # Log all available plans for debugging
    try:
        plan_dir = os.path.join(STORAGE_DIR)
        if os.path.exists(plan_dir):
            plan_files = os.listdir(plan_dir)
            logger.info(f"📋 Available plans in storage: {plan_files}")
    except Exception as e:
        logger.error(f"Error listing plan files: {e}")
    
    logger.warning(f"❌ Plan not found: {plan_id}")
    return None

async def save_plan(plan_id: str, plan_data: dict, plan_manager_instance=None) -> bool:
    """Save a plan to persistent storage and update metadata"""
    try:
        # Ensure plan_data has required fields
        if not isinstance(plan_data, dict):
            logger.error(f"Invalid plan data type: {type(plan_data)}")
            return False
            
        # Add required fields if missing
        if "timestamp" not in plan_data:
            plan_data["timestamp"] = time.time()
        if "created" not in plan_data:
            plan_data["created"] = plan_data["timestamp"]
        if "title" not in plan_data:
            plan_data["title"] = "Untitled Plan"
            
        # Make sure task_id and plan_id are set for compatibility
        if "task_id" not in plan_data:
            plan_data["task_id"] = plan_id
        if "plan_id" not in plan_data:
            plan_data["plan_id"] = plan_id
        if "id" not in plan_data:
            plan_data["id"] = plan_id
            
        # Sanitize plan_id for filename compatibility (replace any characters that might cause issues)
        safe_plan_id = plan_id.replace(':', '_').replace('/', '_').replace('\\', '_')
        
        # Create storage directory if it doesn't exist
        os.makedirs(STORAGE_DIR, exist_ok=True)
            
        # Save plan data to file
        plan_path = os.path.join(STORAGE_DIR, f"{safe_plan_id}.json")
        
        with open(plan_path, "w") as f:
            json.dump(plan_data, f)
        
        # Save to metadata
        instance = plan_manager_instance or plan_manager
        
        # Update metadata if instance is provided
        if instance and hasattr(instance, 'metadata'):
            metadata = PlanMetadata(
                plan_id=plan_id,
                title=plan_data.get("title", "Untitled"),
                created=plan_data.get("created", time.time()),
                modified=time.time(),
                status=plan_data.get("status", "pending"),
                step_count=len(plan_data.get("steps", [])),
                active=True,
                tags=[]
            )
            instance.metadata[plan_id] = metadata
            asyncio.create_task(instance.save_metadata())
        
        # Add to in-memory dictionaries
        try:
            import enhanced_enterprise_backend_with_context
            if hasattr(enhanced_enterprise_backend_with_context, 'shared_pending_plans'):
                enhanced_enterprise_backend_with_context.shared_pending_plans[plan_id] = plan_data
                logger.info(f"✅ Added plan to shared dictionary: {plan_id}")
        except Exception as e:
            logger.warning(f"⚠️ Could not add to shared dictionary: {e}")
        
        logger.info(f"✅ Plan {plan_id} saved successfully to {plan_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving plan {plan_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def delete_plan(plan_id: str, plan_manager_instance=None) -> bool:
    """Delete a plan from persistent storage"""
    instance = plan_manager_instance or plan_manager
    return await instance.delete_plan(plan_id)

async def get_all_plan_metadata(plan_manager_instance=None) -> List[Dict[str, Any]]:
    """Get metadata for all stored plans"""
    instance = plan_manager_instance or plan_manager
    return await instance.get_all_plan_metadata()

# Initialize persistence on module import
if __name__ != "__main__":
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(plan_manager.start())
        else:
            loop.run_until_complete(plan_manager.start())
        logger.info("Plan persistence system initialized")
    except Exception as e:
        logger.error(f"Error initializing plan persistence system: {e}")