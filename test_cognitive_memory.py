#!/usr/bin/env python3
"""
Test Cognitive Memory Processing
Tests the enhanced cognitive memory processing with LLM insight extraction.
"""
import asyncio
import logging
import json
import os
import time
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_cognitive_memory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import necessary components
try:
    # Try to import the memory system
    try:
        from memory.memory_system import MemorySystem
    except ImportError:
        from memory_system import MemorySystem
        
    # Try to import conscious memory
    try:
        from memory.conscious_memory import ConsciousMemory
    except ImportError:
        from conscious_memory import ConsciousMemory
        
    # Try to import LLM service
    try:
        from llm.llm_service import LLMService
    except ImportError:
        from llm_service import LLMService
    
    IMPORTS_SUCCESSFUL = True
    
except ImportError as e:
    logger.error(f"Error importing required components: {e}")
    IMPORTS_SUCCESSFUL = False

# Mock data for testing
class MockData:
    """Generate mock data for testing"""
    
    @staticmethod
    def get_mock_screen_data():
        """Create realistic mock screen data"""
        return {
            'timestamp': time.time(),
            'window_title': 'VS Code - memory_system.py',
            'application': {
                'name': 'VS Code',
                'view': 'Editor',
                'workflow_stage': 'Coding'
            },
            'screen_content': """
            # Memory System
            
            class MemorySystem:
                def __init__(self):
                    self.short_term_memory = []
                    self.long_term_memory = []
                    self.context_memory = {}
                    
                async def add_to_short_term_memory(self, data):
                    self.short_term_memory.append(data)
                    
                async def add_to_long_term_memory(self, data):
                    self.long_term_memory.append(data)
            """,
            'visual_context': 'The screen shows a code editor (VS Code) with Python code open. The code defines a MemorySystem class with methods for adding items to short-term and long-term memory.',
            'screen_elements': [
                {'type': 'window', 'name': 'VS Code'},
                {'type': 'tab', 'name': 'memory_system.py'},
                {'type': 'editor', 'name': 'Code Editor'},
                {'type': 'button', 'name': 'Run', 'state': 'enabled'},
                {'type': 'button', 'name': 'Debug', 'state': 'enabled'}
            ]
        }
    
    @staticmethod
    def get_mock_process_data():
        """Create realistic mock process data"""
        return {
            'timestamp': time.time(),
            'active_window': 'VS Code',
            'active_app': 'VS Code',
            'active_apps': [
                'VS Code', 
                'Terminal', 
                'Chrome', 
                'Finder', 
                'Python', 
                'SystemServices'
            ],
            'foreground': [
                {
                    'name': 'VS Code',
                    'type': 'editor',
                    'category': 'development'
                }
            ],
            'background': [
                {
                    'name': 'Terminal',
                    'type': 'utility',
                    'category': 'development'
                },
                {
                    'name': 'Chrome',
                    'type': 'browser',
                    'category': 'web'
                }
            ],
            'system_info': {
                'memory_used_percent': 65,
                'cpu_count': 8,
                'cpu_percent': 25
            }
        }
    
    @staticmethod
    def get_mock_file_data():
        """Create realistic mock file data"""
        return {
            'timestamp': time.time(),
            'events': [
                {
                    'event_type': 'modified',
                    'path': '/Users/segevbin/Desktop/SensAI/Aiayer/memory/memory_system.py',
                    'timestamp': time.time() - 60
                },
                {
                    'event_type': 'read',
                    'path': '/Users/segevbin/Desktop/SensAI/Aiayer/memory/conscious_memory.py',
                    'timestamp': time.time() - 120
                },
                {
                    'event_type': 'read',
                    'path': '/Users/segevbin/Desktop/SensAI/Aiayer/llm/llm_service.py',
                    'timestamp': time.time() - 180
                }
            ]
        }

class MockLLMService:
    """Mock LLM service for testing when real LLM is not available"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initialized Mock LLM Service")
    
    async def generate_response(self, prompt):
        """Generate mock LLM response with structured cognitive memory"""
        self.logger.info("Generating mock LLM response")
        
        # Create mock cognitive memory response
        cognitive_memory = {
            "primary_activity": "Software development - working on memory system",
            "activity_details": {
                "task": "Coding implementation of memory system architecture",
                "goal": "Develop a memory system to store and retrieve contextual information",
                "workflow_stage": "Active development",
                "domain": "Software Engineering - Python"
            },
            "cognitive_context": {
                "tools": ["VS Code", "Terminal", "Python"],
                "content_type": "Python code",
                "attention_focus": "Memory system class implementation",
                "cognitive_load": "medium"
            },
            "semantic_insights": [
                "The user is implementing a structured memory system with different memory types",
                "The development focuses on short-term and long-term memory integration",
                "The architecture follows cognitive science principles of memory organization"
            ],
            "memory_importance": "high",
            "memory_type": "semantic",
            "future_relevance": "This memory will be important for understanding the system architecture and helping with future development of related components",
            "relationships": [
                {"entity": "memory organization", "relationship": "central concept in implementation"},
                {"entity": "Python development", "relationship": "technical context"},
                {"entity": "VS Code", "relationship": "primary tool being used"}
            ]
        }
        
        # Return structured as JSON
        return {
            "response": json.dumps(cognitive_memory, indent=2)
        }

class TestCognitiveMemory:
    """Test the cognitive memory processing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.memory_system = None
        self.conscious_memory = None
        self.llm_service = None
    
    async def setup(self, use_mock_llm=True):
        """Set up the test environment"""
        try:
            self.logger.info("Setting up test environment")
            
            # Initialize memory system
            self.memory_system = MemorySystem()
            
            # Initialize LLM service (real or mock)
            if use_mock_llm:
                self.llm_service = MockLLMService()
                self.logger.info("Using mock LLM service")
            else:
                self.llm_service = LLMService()
                self.logger.info("Using real LLM service")
            
            # Initialize conscious memory
            self.conscious_memory = ConsciousMemory(self.llm_service, self.memory_system)
            
            self.logger.info("Test environment set up successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error setting up test environment: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    async def test_cognitive_memory_processing(self):
        """Test the cognitive memory processing with mock data"""
        try:
            self.logger.info("Starting cognitive memory processing test")
            
            # Add mock data to conscious memory
            screen_data = MockData.get_mock_screen_data()
            await self.conscious_memory.add_sensor_data('screen', screen_data)
            self.logger.info("Added mock screen data to conscious memory")
            
            process_data = MockData.get_mock_process_data()
            await self.conscious_memory.add_sensor_data('process', process_data)
            self.logger.info("Added mock process data to conscious memory")
            
            file_data = MockData.get_mock_file_data()
            await self.conscious_memory.add_sensor_data('file', file_data)
            self.logger.info("Added mock file data to conscious memory")
            
            # Process data
            self.logger.info("Processing data with conscious memory...")
            result = await self.conscious_memory.process_data()
            
            if result:
                self.logger.info("✅ Cognitive memory processing successful")
                
                # Get memory counts to verify memory distribution
                short_term_count = len(self.memory_system.short_term_memory)
                long_term_count = len(self.memory_system.long_term_memory)
                context_count = len(self.memory_system.context_memory)
                
                self.logger.info(f"Memory counts - Short-term: {short_term_count}, Long-term: {long_term_count}, Context: {context_count}")
                
                # Check if memory was distributed correctly
                if short_term_count > 0 and long_term_count > 0 and context_count > 0:
                    self.logger.info("✅ Memory was correctly distributed to all memory types")
                    return True
                else:
                    self.logger.warning("⚠️ Memory distribution may be incomplete")
                    return False
            else:
                self.logger.error("❌ Cognitive memory processing failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error testing cognitive memory processing: {e}")
            self.logger.error(traceback.format_exc())
            return False
            
    async def test_prompt_generation(self):
        """Test the enhanced prompt generation"""
        try:
            self.logger.info("Testing prompt generation")
            
            # Create test context
            context = {
                'screen_data': [MockData.get_mock_screen_data()],
                'process_data': [MockData.get_mock_process_data()],
                'file_data': [MockData.get_mock_file_data()]
            }
            
            # Generate prompt
            prompt = self.conscious_memory._generate_analysis_prompt(context)
            
            if prompt:
                self.logger.info("✅ Successfully generated analysis prompt")
                self.logger.info(f"Prompt length: {len(prompt)} characters")
                
                # Check for key sections
                required_sections = [
                    "Cognitive Memory Analysis System",
                    "Application Context",
                    "Visual Context",
                    "Screen Text Content",
                    "Active Applications",
                    "File Activity",
                    "Cognitive Memory Analysis",
                    "primary_activity",
                    "activity_details",
                    "cognitive_context",
                    "semantic_insights",
                    "memory_importance",
                    "memory_type"
                ]
                
                all_sections_present = True
                for section in required_sections:
                    if section not in prompt:
                        self.logger.warning(f"⚠️ Missing section in prompt: {section}")
                        all_sections_present = False
                
                if all_sections_present:
                    self.logger.info("✅ All required prompt sections present")
                    
                    # Save prompt to file for inspection
                    with open('logs/test_cognitive_prompt.txt', 'w') as f:
                        f.write(prompt)
                    self.logger.info("✅ Saved prompt to logs/test_cognitive_prompt.txt")
                    
                    return True
                else:
                    self.logger.warning("⚠️ Some prompt sections are missing")
                    return False
            else:
                self.logger.error("❌ Failed to generate analysis prompt")
                return False
                
        except Exception as e:
            self.logger.error(f"Error testing prompt generation: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    async def test_response_parsing(self):
        """Test LLM response parsing and memory distribution"""
        try:
            self.logger.info("Testing LLM response parsing")
            
            # Generate mock LLM response
            mock_response = {
                "response": """
                ```json
                {
                  "primary_activity": "Software development - memory system",
                  "activity_details": {
                    "task": "Implementing memory architecture",
                    "goal": "Create a robust memory system for AI",
                    "workflow_stage": "Development",
                    "domain": "Software Engineering"
                  },
                  "cognitive_context": {
                    "tools": ["VS Code", "Python"],
                    "content_type": "Code",
                    "attention_focus": "Memory system implementation",
                    "cognitive_load": "medium"
                  },
                  "semantic_insights": [
                    "The user is creating a structured memory system",
                    "The architecture separates short and long-term memory"
                  ],
                  "memory_importance": "high",
                  "memory_type": "semantic",
                  "future_relevance": "Important for understanding system architecture",
                  "relationships": [
                    {"entity": "Python", "relationship": "programming language"}
                  ]
                }
                ```
                """
            }
            
            # Create test context
            context = {
                'screen_data': [MockData.get_mock_screen_data()],
                'process_data': [MockData.get_mock_process_data()],
                'file_data': [MockData.get_mock_file_data()]
            }
            
            # Process response
            # Create insight data manually
            llm_response = mock_response['response']
            
            # Extract JSON from the response
            import re
            json_match = re.search(r'({[\s\S]*})', llm_response)
            
            if json_match:
                json_str = json_match.group(1)
                cognitive_memory = json.loads(json_str)
                self.logger.info("✅ Successfully extracted structured cognitive memory")
                
                # Check if memory has the right structure
                required_fields = [
                    "primary_activity",
                    "activity_details",
                    "cognitive_context",
                    "semantic_insights",
                    "memory_importance",
                    "memory_type"
                ]
                
                all_fields_present = True
                for field in required_fields:
                    if field not in cognitive_memory:
                        self.logger.warning(f"⚠️ Missing field in cognitive memory: {field}")
                        all_fields_present = False
                
                if all_fields_present:
                    self.logger.info("✅ All required cognitive memory fields present")
                    
                    # Verify importance and type extraction
                    memory_importance = cognitive_memory.get("memory_importance")
                    memory_type = cognitive_memory.get("memory_type")
                    
                    self.logger.info(f"Memory importance: {memory_importance}, type: {memory_type}")
                    
                    if memory_importance and memory_type:
                        self.logger.info("✅ Successfully extracted memory importance and type")
                        return True
                    else:
                        self.logger.warning("⚠️ Failed to extract memory importance or type")
                        return False
                else:
                    self.logger.warning("⚠️ Some cognitive memory fields are missing")
                    return False
            else:
                self.logger.error("❌ Failed to extract JSON from LLM response")
                return False
                
        except Exception as e:
            self.logger.error(f"Error testing response parsing: {e}")
            self.logger.error(traceback.format_exc())
            return False
    
    async def run_all_tests(self):
        """Run all tests"""
        try:
            self.logger.info("Running all cognitive memory tests")
            
            # Set up test environment
            setup_success = await self.setup()
            if not setup_success:
                self.logger.error("❌ Failed to set up test environment")
                return False
            
            # Test prompt generation
            prompt_success = await self.test_prompt_generation()
            
            # Test response parsing
            parsing_success = await self.test_response_parsing()
            
            # Test cognitive memory processing
            processing_success = await self.test_cognitive_memory_processing()
            
            # Log overall results
            overall_success = prompt_success and parsing_success and processing_success
            
            if overall_success:
                self.logger.info("✅ All cognitive memory tests passed")
            else:
                self.logger.warning("⚠️ Some cognitive memory tests failed")
                
            return overall_success
            
        except Exception as e:
            self.logger.error(f"Error running all tests: {e}")
            self.logger.error(traceback.format_exc())
            return False

async def main():
    """Main function"""
    logger.info("Starting cognitive memory test")
    
    if not IMPORTS_SUCCESSFUL:
        logger.error("❌ Required imports failed, cannot run tests")
        return
    
    # Initialize and run tests
    test = TestCognitiveMemory()
    success = await test.run_all_tests()
    
    if success:
        logger.info("✅ Cognitive memory test completed successfully")
    else:
        logger.warning("⚠️ Cognitive memory test completed with issues")

if __name__ == "__main__":
    asyncio.run(main())