#!/usr/bin/env python3
"""
Direct Context to Long-Term Memory Converter

This script provides a direct and immediate way to transfer contextual memory
to long-term memory without requiring any complex setup or integration.
It works directly with the existing memory system.
"""
import os
import sys
import json
import time
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContextToLongTermConverter:
    """Converts context memory to long-term memory directly"""
    
    def __init__(self, memory_state_file="memory/memory_state.json", threshold=0.3):
        """
        Initialize the converter
        
        Args:
            memory_state_file: Path to memory_state.json file
            threshold: Significance threshold for promotion (lower = more memories promoted)
        """
        self.memory_state_file = memory_state_file
        self.threshold = threshold
        self.temp_file = f"{memory_state_file}.tmp"
        self.backup_file = f"{memory_state_file}.bak"
        self.conversion_stats = {
            "run_time": datetime.now().isoformat(),
            "processed_memories": 0,
            "promoted_memories": 0
        }
        logger.info(f"Context to Long-Term converter initialized with threshold={threshold}")
    
    async def process(self) -> Dict[str, Any]:
        """
        Process memory state and convert context to long-term memory
        
        Returns:
            Statistics about the conversion process
        """
        try:
            # Load memory state
            memory_state = self.load_memory_state()
            if not memory_state:
                logger.error("Failed to load memory state")
                return {"error": "Failed to load memory state"}
            
            # Extract memory sections
            short_term = memory_state.get("short_term", [])
            long_term = memory_state.get("long_term", [])
            context_memory = memory_state.get("context", {})
            
            logger.info(f"Loaded memory state: {len(short_term)} short-term, {len(long_term)} long-term, {len(context_memory)} context keys")
            
            # Process context memory
            promoted_items = []
            processed_count = 0
            
            # First handle by_timestamp section
            if 'by_timestamp' in context_memory and isinstance(context_memory['by_timestamp'], dict):
                timestamp_memories = context_memory['by_timestamp']
                logger.info(f"Processing {len(timestamp_memories)} contextual memories by timestamp")
                
                for timestamp, memory in timestamp_memories.items():
                    processed_count += 1
                    
                    # Evaluate memory for promotion
                    should_promote = self.evaluate_for_promotion(memory)
                    
                    if should_promote:
                        # Prepare memory for long-term storage
                        ltm_memory = self.prepare_for_long_term(memory)
                        
                        # Add to promotion list
                        promoted_items.append(ltm_memory)
                        logger.info(f"Promoting contextual memory with ID {memory.get('memory_id', 'unknown')}")
            
            # Next handle sensor data sections
            if 'sensor_data' in context_memory and isinstance(context_memory['sensor_data'], dict):
                for sensor_type, sensor_memories in context_memory['sensor_data'].items():
                    if not isinstance(sensor_memories, dict):
                        continue
                        
                    logger.info(f"Processing {len(sensor_memories)} {sensor_type} contextual memories")
                    
                    for memory_id, memory in sensor_memories.items():
                        processed_count += 1
                        
                        # Skip if already processed via by_timestamp
                        if 'by_timestamp' in context_memory:
                            # Check if memory with this ID was already processed
                            already_processed = False
                            for ts_memory in context_memory['by_timestamp'].values():
                                if ts_memory.get('memory_id') == memory_id:
                                    already_processed = True
                                    break
                            
                            if already_processed:
                                continue
                        
                        # Evaluate memory for promotion
                        should_promote = self.evaluate_for_promotion(memory)
                        
                        if should_promote:
                            # Prepare memory for long-term storage
                            ltm_memory = self.prepare_for_long_term(memory)
                            
                            # Add to promotion list
                            promoted_items.append(ltm_memory)
                            logger.info(f"Promoting {sensor_type} contextual memory with ID {memory_id}")
            
            # Update long-term memory
            long_term.extend(promoted_items)
            
            # Save updated memory state
            memory_state["long_term"] = long_term
            memory_state["last_update"] = datetime.now().isoformat()
            self.save_memory_state(memory_state)
            
            # Update stats
            self.conversion_stats["processed_memories"] = processed_count
            self.conversion_stats["promoted_memories"] = len(promoted_items)
            
            logger.info(f"Context to Long-Term conversion complete: processed {processed_count}, promoted {len(promoted_items)}")
            return self.conversion_stats
            
        except Exception as e:
            logger.error(f"Error during context to long-term conversion: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    def load_memory_state(self) -> Dict[str, Any]:
        """Load memory state from file"""
        try:
            if not os.path.exists(self.memory_state_file):
                logger.error(f"Memory state file not found: {self.memory_state_file}")
                return {}
            
            with open(self.memory_state_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading memory state: {e}")
            return {}
    
    def save_memory_state(self, memory_state: Dict[str, Any]) -> bool:
        """Save memory state to file"""
        try:
            # Create a backup first
            if os.path.exists(self.memory_state_file):
                import shutil
                shutil.copy2(self.memory_state_file, self.backup_file)
            
            # Write to temporary file first
            with open(self.temp_file, 'w') as f:
                json.dump(memory_state, f, indent=2)
            
            # Move temporary file to real file
            import shutil
            shutil.move(self.temp_file, self.memory_state_file)
            
            logger.info(f"Memory state saved to {self.memory_state_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving memory state: {e}")
            return False
    
    def evaluate_for_promotion(self, memory: Dict[str, Any]) -> bool:
        """
        Evaluate whether a contextual memory should be promoted to long-term
        
        Args:
            memory: The memory item to evaluate
            
        Returns:
            Boolean indicating whether to promote this memory
        """
        try:
            # Skip if not a valid memory object
            if not isinstance(memory, dict):
                return False
            
            # Always promote if explicitly marked as significant
            if memory.get('is_significant', False):
                return True
            
            # Calculate significance score
            significance = 0.0
            
            # Memory with application workflow data is significant
            if 'application' in memory and isinstance(memory['application'], dict):
                app_data = memory['application']
                if app_data.get('workflow_stage'):
                    significance += 0.3
                if app_data.get('name'):
                    significance += 0.1
            
            # Memory with visual or LLAVA context is significant
            if memory.get('visual_context') or memory.get('llava_description'):
                significance += 0.3
            
            # Memory with insights is significant
            if 'insights' in memory and isinstance(memory['insights'], list):
                insight_count = len(memory['insights'])
                if insight_count > 0:
                    significance += min(0.3, 0.05 * insight_count)
            
            # Memory with activity summary is significant
            if memory.get('activity_summary') or memory.get('context_understanding'):
                significance += 0.2
            
            # Memory with semantic meaning is significant
            if memory.get('semantic_summary'):
                significance += 0.2
            
            # Memory with UI element data is significant
            if 'screen_elements' in memory and isinstance(memory['screen_elements'], list):
                if len(memory['screen_elements']) > 0:
                    significance += 0.1
            
            # Memory with relationship data is significant
            if 'memory_connections' in memory and isinstance(memory['memory_connections'], list):
                if len(memory['memory_connections']) > 0:
                    significance += 0.2
            
            # Memory about communication (email, messages) is significant
            if memory.get('email_data') or memory.get('message_data'):
                significance += 0.3
            
            # Memory with high cognitive importance is significant
            if memory.get('cognitive_memory', {}).get('memory_importance') in ['high', 'critical']:
                significance += 0.4
            
            # Check final significance against threshold
            return significance >= self.threshold
            
        except Exception as e:
            logger.error(f"Error evaluating memory for promotion: {e}")
            return False
    
    def prepare_for_long_term(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare contextual memory for long-term storage by enhancing metadata
        
        Args:
            memory: The contextual memory to prepare
            
        Returns:
            Enhanced memory object suitable for long-term storage
        """
        try:
            # Create a copy to avoid modifying the original
            ltm_memory = memory.copy()
            
            # Add promotion metadata
            ltm_memory['promoted_from'] = 'context_memory'
            ltm_memory['promoted_at'] = datetime.now().isoformat()
            
            # Generate a new memory_id for long-term storage
            ltm_memory['memory_id'] = f"ltm_ctx_{int(time.time() * 1000)}"
            
            # Reference the original context memory ID if available
            if 'memory_id' in memory:
                ltm_memory['original_memory_id'] = memory['memory_id']
            
            # Add memory type for proper categorization
            ltm_memory['memory_type'] = 'long_term'
            
            # Add importance metadata for memory value calculation
            ltm_memory['importance_score'] = 0.8  # High importance by default for promoted items
            
            # Keep track of content source
            if 'sensor_type' in memory:
                ltm_memory['content_source'] = memory['sensor_type']
            
            # Add source application context if available
            if 'application' in memory and isinstance(memory['application'], dict):
                app_name = memory['application'].get('name', 'Unknown')
                ltm_memory['source_application'] = app_name
            
            # Add semantic tags if possible
            if 'insights' in memory and isinstance(memory['insights'], list):
                semantic_tags = []
                for insight in memory['insights']:
                    if isinstance(insight, dict) and 'content' in insight:
                        tag = insight['content'].split(':')[0] if ':' in insight['content'] else insight['content']
                        semantic_tags.append(tag)
                    elif isinstance(insight, str):
                        tag = insight.split(':')[0] if ':' in insight else insight
                        semantic_tags.append(tag)
                
                if semantic_tags:
                    ltm_memory['semantic_tags'] = semantic_tags
            
            return ltm_memory
            
        except Exception as e:
            logger.error(f"Error preparing memory for long-term: {e}")
            return memory  # Return original if preparation fails

async def main():
    """Main function to run the converter"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Convert context memory to long-term memory")
    parser.add_argument("--threshold", type=float, default=0.3, 
                        help="Significance threshold for promotion (default: 0.3)")
    parser.add_argument("--memory-file", type=str, default="memory/memory_state.json",
                        help="Path to memory_state.json file")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")
    args = parser.parse_args()
    
    # Create and run converter
    converter = ContextToLongTermConverter(
        memory_state_file=args.memory_file,
        threshold=args.threshold
    )
    
    logger.info(f"Starting context to long-term conversion with threshold={args.threshold}")
    result = await converter.process()
    
    # Output results
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("\nContext to Long-Term Memory Conversion Results:")
        print("==============================================")
        print(f"Run Time: {result.get('run_time', 'Unknown')}")
        print(f"Processed Memories: {result.get('processed_memories', 0)}")
        print(f"Promoted Memories: {result.get('promoted_memories', 0)}")
        if "error" in result:
            print(f"\nError: {result['error']}")
        print("\nContext memories have been successfully promoted to long-term memory!")

if __name__ == "__main__":
    asyncio.run(main())