"""
Universal Deep Data Access Prototype
Complete working prototype that integrates with the existing enhanced enterprise backend.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our universal deep data components
from universal_data_access_planner import UniversalDataAccessPlanner
from enhanced_data_source_workflows import WorkflowOrchestrator
from intelligent_app_detection_system import ApplicationDetector, ApplicationNavigator
from visual_data_extraction_system import DataExtractor
from universal_deep_data_integration import UniversalDeepDataRouter

# Import existing backend
from enhanced_enterprise_backend_with_context import EnhancedEnterpriseBackend

logger = logging.getLogger(__name__)

class UniversalDeepDataPrototype:
    """
    Complete prototype of the Universal Deep Data Access system.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.UniversalDeepDataPrototype")
        self.backend = None
        self.deep_data_router = None
        self.is_initialized = False
    
    async def initialize(self, port: int = 8767):
        """Initialize the complete system."""
        self.logger.info("Initializing Universal Deep Data Access Prototype")
        
        try:
            # Step 1: Initialize the enhanced backend
            self.backend = EnhancedEnterpriseBackend()
            
            # Step 2: Initialize deep data components
            self.deep_data_router = UniversalDeepDataRouter(self.backend)
            await self.deep_data_router.initialize()
            
            # Step 3: Patch the backend to use deep data capabilities
            await self._patch_backend_with_deep_data()
            
            # Step 4: Start the backend server
            await self._start_backend_server(port)
            
            self.is_initialized = True
            self.logger.info("Universal Deep Data Access Prototype initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize prototype: {e}")
            raise
    
    async def _patch_backend_with_deep_data(self):
        """Patch the backend to include deep data capabilities."""
        # Store original message handler
        original_handle_message = self.backend.handle_message
        
        async def enhanced_handle_message(data: Dict[str, Any], websocket, client_id: str) -> Dict[str, Any]:
            """Enhanced message handler with deep data access."""
            try:
                message = data.get("message", "")
                mode = data.get("mode", "auto")
                
                self.logger.info(f"Processing message with deep data system: {message}")
                
                # Route through deep data system
                result = await self.deep_data_router.route_message(
                    message, mode, websocket, client_id
                )
                
                if result.get("success") and result.get("response_type") == "deep_data_access":
                    # Deep data access was successful
                    response_text = result.get("response", "")
                    
                    # Add execution summary if available
                    execution_summary = result.get("execution_summary", {})
                    if execution_summary.get("successful_workflows", 0) > 0:
                        response_text += f"\n\n📊 Data Access Summary: Successfully accessed {execution_summary['successful_workflows']} data sources"
                    
                    return {
                        "type": "response",
                        "response": response_text,
                        "mode": mode,
                        "deep_data_used": True,
                        "execution_summary": execution_summary,
                        "query_analysis": result.get("query_analysis", {})
                    }
                else:
                    # Use original handler for standard processing
                    return await original_handle_message(data, websocket, client_id)
                    
            except Exception as e:
                self.logger.error(f"Error in enhanced message handler: {e}")
                # Fallback to original handler
                return await original_handle_message(data, websocket, client_id)
        
        # Replace the message handler
        self.backend.handle_message = enhanced_handle_message
        
        # Add utility methods to backend
        self.backend.get_deep_data_status = self._get_deep_data_status
        self.backend.test_deep_data = self._test_deep_data_access
        
        self.logger.info("Backend patched with deep data capabilities")
    
    async def _get_deep_data_status(self) -> Dict[str, Any]:
        """Get status of deep data access system."""
        return {
            "initialized": self.is_initialized,
            "components": {
                "query_analyzer": self.deep_data_router.planner is not None,
                "workflow_orchestrator": self.deep_data_router.workflow_orchestrator is not None,
                "app_detector": hasattr(self.backend, 'app_detector'),
                "visual_extractor": hasattr(self.backend, 'visual_extractor'),
                "memory_integration": hasattr(self.backend, 'memory_system')
            },
            "supported_data_sources": ["email", "browser_history", "files", "system_info"],
            "available_modes": ["ask", "suggest", "agent", "deep_access"],
            "timestamp": datetime.now().isoformat()
        }
    
    async def _test_deep_data_access(self, test_query: str = "What apps are currently running?") -> Dict[str, Any]:
        """Test the deep data access system."""
        try:
            result = await self.deep_data_router.route_message(test_query, "deep_access")
            return {
                "test_query": test_query,
                "success": result.get("success", False),
                "response_type": result.get("response_type"),
                "response": result.get("response", ""),
                "execution_summary": result.get("execution_summary", {}),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "test_query": test_query,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _start_backend_server(self, port: int):
        """Start the backend server with deep data capabilities."""
        self.logger.info(f"Starting enhanced backend server on port {port}")
        
        # Add deep data status endpoint
        async def handle_deep_data_status(websocket, path):
            """Handle deep data status requests."""
            try:
                status = await self._get_deep_data_status()
                await websocket.send(json.dumps({
                    "type": "deep_data_status",
                    "status": status
                }))
            except Exception as e:
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": f"Failed to get deep data status: {str(e)}"
                }))
        
        # Add test endpoint
        async def handle_deep_data_test(websocket, path):
            """Handle deep data test requests."""
            try:
                async for message in websocket:
                    data = json.loads(message)
                    test_query = data.get("test_query", "What apps are currently running?")
                    
                    result = await self._test_deep_data_access(test_query)
                    await websocket.send(json.dumps({
                        "type": "deep_data_test_result",
                        "result": result
                    }))
            except Exception as e:
                await websocket.send(json.dumps({
                    "type": "error",
                    "error": f"Deep data test failed: {str(e)}"
                }))
        
        # Store additional handlers
        self.backend.deep_data_status_handler = handle_deep_data_status
        self.backend.deep_data_test_handler = handle_deep_data_test
        
        # Backend will be started by the main server
        self.logger.info("Backend server configured with deep data endpoints")
    
    async def demonstrate_capabilities(self):
        """Demonstrate the capabilities of the deep data system."""
        print("\n" + "="*60)
        print("UNIVERSAL DEEP DATA ACCESS SYSTEM DEMONSTRATION")
        print("="*60)
        
        # Test queries that showcase different capabilities
        test_queries = [
            "What emails did I receive today?",
            "Show me files I created this week", 
            "What websites did I visit yesterday?",
            "What apps are currently running?",
            "Find my meeting notes from yesterday",
            "Show me my recent downloads"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Testing Query: '{query}'")
            print("-" * 50)
            
            try:
                # Analyze the query
                analysis = await self.deep_data_router.planner.analyze_query(query)
                
                print(f"   Detected Sources: {[s['source'] for s in analysis['detected_sources']]}")
                print(f"   Search Terms: {analysis['search_terms']}")
                print(f"   Complexity: {analysis['estimated_complexity']}")
                
                # Show what would be executed
                execution_plan = analysis['execution_plan']
                print(f"   Planned Steps: {len(execution_plan['steps'])}")
                for step in execution_plan['steps']:
                    print(f"     - {step['source']}: {len(step['actions'])} actions")
                
            except Exception as e:
                print(f"   Error analyzing query: {e}")
        
        print(f"\n{'='*60}")
        print("SYSTEM CAPABILITIES SUMMARY")
        print("="*60)
        
        status = await self._get_deep_data_status()
        print(f"✓ System Initialized: {status['initialized']}")
        print(f"✓ Components Active: {sum(status['components'].values())}/{len(status['components'])}")
        print(f"✓ Data Sources: {', '.join(status['supported_data_sources'])}")
        print(f"✓ Available Modes: {', '.join(status['available_modes'])}")
        
        print(f"\n{'='*60}")
        print("HOW IT WORKS FOR ANY USER MESSAGE")
        print("="*60)
        print("1. 🔍 QUERY ANALYSIS")
        print("   - Automatically detects what data sources are needed")
        print("   - Extracts search terms and time constraints")
        print("   - Creates execution plan with TeamViewer-style automation")
        
        print("\n2. 🖥️  APPLICATION DETECTION & NAVIGATION")
        print("   - Uses computer vision to detect open applications")
        print("   - Intelligently navigates to required apps (Email, Browser, Files)")
        print("   - Activates search interfaces and performs searches")
        
        print("\n3. 👁️  VISUAL DATA EXTRACTION")
        print("   - Advanced OCR to extract text from screens")
        print("   - Pattern matching to identify structured data")
        print("   - Visual analysis to understand layouts and relationships")
        
        print("\n4. 🧠 CONTEXTUAL RESPONSE GENERATION")
        print("   - Integrates collected data with existing brain router")
        print("   - Provides detailed, contextual responses")
        print("   - Stores results in memory for future reference")
        
        print(f"\n{'='*60}")
        print("READY FOR INTEGRATION")
        print("="*60)
        print("The system is now ready to handle ANY user message agnostically.")
        print("It will automatically determine if deep data access is needed")
        print("and seamlessly provide comprehensive responses using real data")
        print("from the user's computer.")

async def main():
    """Main function to run the prototype."""
    print("Universal Deep Data Access Prototype")
    print("====================================")
    
    try:
        # Initialize the prototype
        prototype = UniversalDeepDataPrototype()
        await prototype.initialize()
        
        # Demonstrate capabilities
        await prototype.demonstrate_capabilities()
        
        # The prototype is now ready - in a real deployment, 
        # this would keep the server running
        print(f"\n🚀 Prototype initialized successfully!")
        print("In a real deployment, the backend server would now be running")
        print("and ready to handle user messages with deep data access.")
        
        # For demonstration, we can test a query
        print("\n📋 Testing a sample query...")
        test_result = await prototype._test_deep_data_access(
            "What applications are currently running on my computer?"
        )
        
        print(f"Test Result:")
        print(f"  Success: {test_result['success']}")
        print(f"  Response Type: {test_result.get('response_type', 'N/A')}")
        if test_result.get('response'):
            print(f"  Response: {test_result['response'][:200]}...")
        
    except Exception as e:
        logger.error(f"Prototype failed: {e}")
        print(f"\n❌ Prototype initialization failed: {e}")
        return
    
    print(f"\n✅ Universal Deep Data Access System is ready!")
    print("The system can now agnostically handle any user message and")
    print("automatically access deep data sources when needed.")

if __name__ == "__main__":
    asyncio.run(main())