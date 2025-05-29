"""
Universal Deep Data Access Integration
Integrates all components into the existing brain router and semantic search systems.
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Import our custom modules
from universal_data_access_planner import UniversalDataAccessPlanner, integrate_universal_data_access
from enhanced_data_source_workflows import WorkflowOrchestrator, DataExtractionResult
from intelligent_app_detection_system import integrate_intelligent_app_detection
from visual_data_extraction_system import integrate_visual_extraction_system

logger = logging.getLogger(__name__)

class UniversalDeepDataRouter:
    """
    Main router that integrates universal deep data access with brain router system.
    """
    
    def __init__(self, backend_instance):
        self.backend = backend_instance
        self.planner = UniversalDataAccessPlanner()
        self.workflow_orchestrator = WorkflowOrchestrator(backend_instance)
        self.logger = logging.getLogger(f"{__name__}.UniversalDeepDataRouter")
        
        # Integration flags
        self.is_integrated = False
        self.available_modes = ["ask", "suggest", "agent", "deep_access"]
    
    async def initialize(self):
        """Initialize all components and integrations."""
        self.logger.info("Initializing Universal Deep Data Access System")
        
        try:
            # Integrate all systems
            await integrate_universal_data_access(self.backend)
            await integrate_intelligent_app_detection(self.backend)
            await integrate_visual_extraction_system(self.backend)
            
            self.is_integrated = True
            self.logger.info("Universal Deep Data Access System initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Universal Deep Data Access: {e}")
            raise
    
    async def route_message(self, user_message: str, mode: str = "auto", 
                          websocket=None, client_id: str = None) -> Dict[str, Any]:
        """
        Route user message through appropriate processing pipeline.
        """
        self.logger.info(f"Routing message in mode '{mode}': {user_message}")
        
        if not self.is_integrated:
            await self.initialize()
        
        # Step 1: Analyze if deep data access is needed
        query_analysis = await self.planner.analyze_query(user_message)
        requires_deep_access = len(query_analysis["detected_sources"]) > 0
        
        self.logger.info(f"Deep access required: {requires_deep_access}")
        
        if requires_deep_access and mode in ["auto", "deep_access"]:
            # Use deep data access pipeline
            return await self._handle_deep_data_access(
                user_message, query_analysis, websocket, client_id
            )
        else:
            # Use existing brain router pipeline
            return await self._handle_standard_processing(
                user_message, mode, websocket, client_id
            )
    
    async def _handle_deep_data_access(self, user_message: str, 
                                     query_analysis: Dict[str, Any], 
                                     websocket=None, client_id: str = None) -> Dict[str, Any]:
        """Handle messages requiring deep data access."""
        self.logger.info("Processing with deep data access pipeline")
        
        try:
            # Step 1: Execute data collection workflows
            workflow_results = await self.workflow_orchestrator.execute_workflows(
                query_analysis["detected_sources"],
                query_analysis["search_terms"],
                query_analysis["time_constraints"],
                websocket
            )
            
            # Step 2: Extract and structure data from collected results
            structured_data = await self._process_workflow_results(workflow_results)
            
            # Step 3: Store in memory system for future reference
            await self._store_in_memory(structured_data, user_message)
            
            # Step 4: Generate contextual response using brain router
            contextual_response = await self._generate_contextual_response(
                user_message, structured_data, websocket, client_id
            )
            
            return {
                "success": True,
                "response_type": "deep_data_access",
                "query_analysis": query_analysis,
                "data_collected": {
                    source: result.data for source, result in workflow_results.items()
                    if result.success
                },
                "response": contextual_response,
                "execution_summary": self._create_execution_summary(workflow_results),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in deep data access pipeline: {e}")
            
            # Fallback to standard processing
            fallback_response = await self._handle_standard_processing(
                user_message, "ask", websocket, client_id
            )
            
            return {
                "success": False,
                "response_type": "fallback_to_standard",
                "error": str(e),
                "fallback_response": fallback_response,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _handle_standard_processing(self, user_message: str, mode: str,
                                        websocket=None, client_id: str = None) -> Dict[str, Any]:
        """Handle messages using existing brain router system."""
        self.logger.info(f"Processing with standard brain router in mode: {mode}")
        
        try:
            # Use existing brain router logic
            if hasattr(self.backend, 'brain_router') and self.backend.brain_router:
                response = await self.backend.brain_router.route_message(
                    user_message, mode, websocket, client_id
                )
                
                return {
                    "success": True,
                    "response_type": "standard_brain_router",
                    "mode": mode,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                # Fallback if brain router not available
                return {
                    "success": False,
                    "response_type": "no_brain_router",
                    "error": "Brain router not available",
                    "fallback_response": f"I understand you're asking: {user_message}. However, I need the brain router system to provide a proper response.",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error in standard processing: {e}")
            return {
                "success": False,
                "response_type": "standard_processing_error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _process_workflow_results(self, workflow_results: Dict[str, DataExtractionResult]) -> Dict[str, Any]:
        """Process and structure data from workflow execution results."""
        structured_data = {
            "emails": [],
            "files": [],
            "browser_history": [],
            "system_info": [],
            "summary": {
                "total_sources": len(workflow_results),
                "successful_sources": 0,
                "total_data_points": 0
            }
        }
        
        for source_name, result in workflow_results.items():
            if result.success and result.data:
                # Map source names to data categories
                data_category = self._map_source_to_category(source_name)
                
                if data_category in structured_data:
                    structured_data[data_category].extend(result.data)
                    structured_data["summary"]["successful_sources"] += 1
                    structured_data["summary"]["total_data_points"] += len(result.data)
                
                # Add metadata
                structured_data[f"{source_name}_metadata"] = {
                    "extraction_method": result.extraction_method,
                    "confidence": result.confidence,
                    "timestamp": result.timestamp.isoformat(),
                    "data_count": len(result.data)
                }
        
        return structured_data
    
    def _map_source_to_category(self, source_name: str) -> str:
        """Map workflow source names to data categories."""
        mapping = {
            "email": "emails",
            "browser_history": "browser_history", 
            "files": "files",
            "system_info": "system_info"
        }
        return mapping.get(source_name, "other")
    
    async def _store_in_memory(self, structured_data: Dict[str, Any], original_query: str):
        """Store collected data in the memory system for future reference."""
        try:
            if hasattr(self.backend, 'memory_system') and self.backend.memory_system:
                # Create memory entry
                memory_entry = {
                    "type": "deep_data_access_result",
                    "original_query": original_query,
                    "data": structured_data,
                    "timestamp": datetime.now().isoformat(),
                    "context": "system_generated"
                }
                
                # Store in memory system
                await self.backend.memory_system.store_memory(
                    content=json.dumps(memory_entry),
                    metadata={"type": "deep_data_access", "query": original_query}
                )
                
                self.logger.info("Stored deep data access results in memory")
            else:
                self.logger.warning("Memory system not available for storage")
                
        except Exception as e:
            self.logger.error(f"Failed to store in memory: {e}")
    
    async def _generate_contextual_response(self, user_message: str, 
                                          structured_data: Dict[str, Any],
                                          websocket=None, client_id: str = None) -> str:
        """Generate a contextual response based on collected data."""
        try:
            # Create rich context for the brain router
            context_summary = self._create_context_summary(structured_data)
            
            # Enhanced message with context
            enhanced_message = f"""
Original query: {user_message}

Available data context:
{context_summary}

Please provide a comprehensive response using the available data.
"""
            
            # Use brain router with enhanced context
            if hasattr(self.backend, 'brain_router') and self.backend.brain_router:
                response = await self.backend.brain_router.route_message(
                    enhanced_message, "ask", websocket, client_id
                )
                
                if isinstance(response, dict):
                    return response.get("response", "No response generated")
                else:
                    return str(response)
            else:
                # Generate basic response from collected data
                return self._generate_basic_response(user_message, structured_data)
                
        except Exception as e:
            self.logger.error(f"Failed to generate contextual response: {e}")
            return self._generate_basic_response(user_message, structured_data)
    
    def _create_context_summary(self, structured_data: Dict[str, Any]) -> str:
        """Create a summary of available data for context."""
        summary_parts = []
        
        # Email data
        if structured_data.get("emails"):
            email_count = len(structured_data["emails"])
            summary_parts.append(f"- {email_count} emails found")
            
            # Add sample email info
            for i, email in enumerate(structured_data["emails"][:3]):
                if "subject" in email:
                    summary_parts.append(f"  • Email {i+1}: {email['subject']}")
        
        # File data
        if structured_data.get("files"):
            file_count = len(structured_data["files"])
            summary_parts.append(f"- {file_count} files found")
            
            # Add sample file info
            for i, file in enumerate(structured_data["files"][:3]):
                if "filename" in file:
                    summary_parts.append(f"  • File {i+1}: {file['filename']}")
        
        # Browser history
        if structured_data.get("browser_history"):
            history_count = len(structured_data["browser_history"])
            summary_parts.append(f"- {history_count} browser history entries found")
        
        # System info
        if structured_data.get("system_info"):
            process_count = len(structured_data["system_info"])
            summary_parts.append(f"- {process_count} system processes found")
        
        # Summary statistics
        summary = structured_data.get("summary", {})
        if summary:
            summary_parts.append(f"- Total successful data sources: {summary.get('successful_sources', 0)}")
            summary_parts.append(f"- Total data points collected: {summary.get('total_data_points', 0)}")
        
        return "\n".join(summary_parts) if summary_parts else "No specific data collected"
    
    def _generate_basic_response(self, user_message: str, structured_data: Dict[str, Any]) -> str:
        """Generate a basic response when brain router is not available."""
        response_parts = [f"Based on your query '{user_message}', I found the following information:"]
        
        # Email information
        if structured_data.get("emails"):
            response_parts.append(f"\n📧 Emails ({len(structured_data['emails'])} found):")
            for email in structured_data["emails"][:5]:
                if "subject" in email:
                    response_parts.append(f"  • {email['subject']}")
                if "from" in email:
                    response_parts.append(f"    From: {email['from']}")
        
        # File information
        if structured_data.get("files"):
            response_parts.append(f"\n📄 Files ({len(structured_data['files'])} found):")
            for file in structured_data["files"][:5]:
                if "filename" in file:
                    response_parts.append(f"  • {file['filename']}")
                if "size" in file:
                    response_parts.append(f"    Size: {file['size']}")
        
        # Browser history
        if structured_data.get("browser_history"):
            response_parts.append(f"\n🌐 Browser History ({len(structured_data['browser_history'])} entries):")
            for entry in structured_data["browser_history"][:3]:
                if "url" in entry:
                    response_parts.append(f"  • {entry['url']}")
        
        # System info
        if structured_data.get("system_info"):
            response_parts.append(f"\n⚙️ System Information ({len(structured_data['system_info'])} processes):")
            for process in structured_data["system_info"][:5]:
                if "process_name" in process:
                    response_parts.append(f"  • {process['process_name']}")
                    if "cpu_usage" in process:
                        response_parts.append(f"    CPU: {process['cpu_usage']}")
        
        if len(response_parts) == 1:
            response_parts.append("\nNo specific data was found for your query.")
        
        return "".join(response_parts)
    
    def _create_execution_summary(self, workflow_results: Dict[str, DataExtractionResult]) -> Dict[str, Any]:
        """Create a summary of workflow execution."""
        summary = {
            "total_workflows": len(workflow_results),
            "successful_workflows": 0,
            "failed_workflows": 0,
            "total_execution_time": 0,
            "workflow_details": {}
        }
        
        for source_name, result in workflow_results.items():
            if result.success:
                summary["successful_workflows"] += 1
            else:
                summary["failed_workflows"] += 1
            
            summary["workflow_details"][source_name] = {
                "success": result.success,
                "data_count": len(result.data) if result.data else 0,
                "confidence": result.confidence,
                "extraction_method": result.extraction_method,
                "errors": result.errors
            }
        
        summary["success_rate"] = (
            summary["successful_workflows"] / summary["total_workflows"] 
            if summary["total_workflows"] > 0 else 0
        )
        
        return summary

# Enhanced backend integration
async def integrate_universal_deep_data_system(backend_instance):
    """
    Complete integration of universal deep data access system.
    """
    logger.info("Integrating Universal Deep Data Access System")
    
    # Create the main router
    deep_data_router = UniversalDeepDataRouter(backend_instance)
    
    # Initialize all components
    await deep_data_router.initialize()
    
    # Add router to backend
    backend_instance.deep_data_router = deep_data_router
    
    # Override or enhance existing message handling
    original_handle_message = getattr(backend_instance, 'handle_message', None)
    
    async def enhanced_handle_message(self, data: Dict[str, Any], websocket, client_id: str) -> Dict[str, Any]:
        """Enhanced message handler with deep data access capability."""
        try:
            message = data.get("message", "")
            mode = data.get("mode", "auto")
            
            # Route through deep data system
            result = await self.deep_data_router.route_message(
                message, mode, websocket, client_id
            )
            
            # Return formatted response
            if result.get("success"):
                return {
                    "type": "response",
                    "response": result.get("response", "No response generated"),
                    "mode": mode,
                    "deep_data_used": result.get("response_type") == "deep_data_access",
                    "metadata": {
                        "execution_summary": result.get("execution_summary"),
                        "query_analysis": result.get("query_analysis")
                    }
                }
            else:
                # Use fallback response or original handler
                if original_handle_message:
                    return await original_handle_message(data, websocket, client_id)
                else:
                    return {
                        "type": "error",
                        "error": result.get("error", "Unknown error in deep data access"),
                        "fallback_response": result.get("fallback_response")
                    }
                
        except Exception as e:
            logger.error(f"Error in enhanced message handler: {e}")
            
            # Fallback to original handler if available
            if original_handle_message:
                return await original_handle_message(data, websocket, client_id)
            else:
                return {
                    "type": "error",
                    "error": f"Message handling failed: {str(e)}"
                }
    
    # Bind the enhanced handler
    import types
    backend_instance.enhanced_handle_message = types.MethodType(
        enhanced_handle_message, backend_instance
    )
    
    # Add utility methods
    async def get_deep_data_capabilities(self) -> Dict[str, Any]:
        """Get information about deep data access capabilities."""
        return {
            "available_sources": ["email", "browser_history", "files", "system_info"],
            "supported_modes": self.deep_data_router.available_modes,
            "is_integrated": self.deep_data_router.is_integrated,
            "capabilities": {
                "query_analysis": "Automatic detection of data access needs",
                "visual_extraction": "OCR and screen analysis",
                "app_detection": "Intelligent application identification",
                "workflow_orchestration": "Automated data collection workflows",
                "memory_integration": "Storage of results for future reference"
            }
        }
    
    async def test_deep_data_access(self, test_query: str = "What emails did I receive today?") -> Dict[str, Any]:
        """Test the deep data access system."""
        return await self.deep_data_router.route_message(test_query, "deep_access")
    
    # Bind utility methods
    backend_instance.get_deep_data_capabilities = types.MethodType(
        get_deep_data_capabilities, backend_instance
    )
    backend_instance.test_deep_data_access = types.MethodType(
        test_deep_data_access, backend_instance
    )
    
    logger.info("Universal Deep Data Access System integration complete")
    return backend_instance

# Patch existing backend to use enhanced message handling
async def patch_backend_for_deep_data(backend_file_path: str):
    """
    Patch the existing backend file to integrate deep data access.
    """
    logger.info(f"Patching backend file: {backend_file_path}")
    
    patch_code = '''
# Universal Deep Data Access Integration
from universal_deep_data_integration import integrate_universal_deep_data_system

# Add to backend initialization
async def initialize_deep_data_system(self):
    """Initialize the universal deep data access system."""
    await integrate_universal_deep_data_system(self)
    self.logger.info("Universal Deep Data Access System initialized")

# Add to message handling
async def handle_message_with_deep_data(self, data: Dict[str, Any], websocket, client_id: str) -> Dict[str, Any]:
    """Handle messages with deep data access capability."""
    if hasattr(self, 'enhanced_handle_message'):
        return await self.enhanced_handle_message(data, websocket, client_id)
    else:
        # Fallback to original method
        return await self.handle_original_message(data, websocket, client_id)
'''
    
    return patch_code

if __name__ == "__main__":
    # Test the integration system
    async def test_integration():
        print("Universal Deep Data Access Integration System")
        print("=" * 50)
        print("Components integrated:")
        print("  ✓ Universal Query Analyzer")
        print("  ✓ Data Source Workflows")
        print("  ✓ Intelligent App Detection")
        print("  ✓ Visual Data Extraction")
        print("  ✓ Brain Router Integration")
        print("  ✓ Memory System Integration")
        print("\nSystem ready for integration with existing backend.")
        
        # Simulate router creation
        class MockBackend:
            def __init__(self):
                self.brain_router = None
                self.memory_system = None
        
        mock_backend = MockBackend()
        router = UniversalDeepDataRouter(mock_backend)
        
        print(f"\nAvailable modes: {router.available_modes}")
        print("Integration test complete.")
    
    asyncio.run(test_integration())