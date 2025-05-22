#!/usr/bin/env python3
"""
Enhanced Screen Memory Processor

Processes rich screen analysis data from the Total Screen Analyzer and feeds it into memory
with proper structure and insights for comprehensive understanding and storage.
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import traceback

# Configure logging
os.makedirs('logs/memory', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/enhanced_screen_memory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('enhanced_screen_memory_processor')

class EnhancedScreenMemoryProcessor:
    """
    Processes Total Screen Analyzer data and formats it for optimal memory storage
    with rich context preservation and intelligent insight extraction.
    """
    
    def __init__(self, memory_system=None):
        self.memory_system = memory_system
        self.processing_stats = {
            "total_processed": 0,
            "high_priority_items": 0,
            "application_context_items": 0,
            "workflow_detections": 0,
            "content_rich_items": 0
        }
        
        # Memory priority weights
        self.priority_weights = {
            "application_detected": 0.3,
            "workflow_identified": 0.4,
            "content_rich": 0.2,
            "user_interaction": 0.3,
            "llava_analysis": 0.2,
            "semantic_understanding": 0.3
        }
        
        logger.info("Enhanced Screen Memory Processor initialized")

    async def process_total_screen_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process comprehensive screen analysis data for memory storage.
        
        Args:
            analysis_data: Rich analysis from Total Screen Analyzer
            
        Returns:
            Processed memory item with enhanced context and insights
        """
        try:
            if not analysis_data:
                logger.warning("Received empty analysis data")
                return None
                
            logger.info("Processing total screen analysis for memory storage")
            
            # Extract memory summary if available (from Total Screen Analyzer)
            if "memory_summary" in analysis_data:
                memory_data = analysis_data["memory_summary"]
            else:
                # Fallback: process raw analysis data
                memory_data = self._extract_memory_data_from_analysis(analysis_data)
            
            # Enhance with memory-specific processing
            enhanced_memory_item = await self._enhance_for_memory_storage(memory_data, analysis_data)
            
            # Calculate memory priority and significance
            priority_score = self._calculate_memory_priority(enhanced_memory_item)
            enhanced_memory_item["memory_priority"] = priority_score
            enhanced_memory_item["is_significant"] = priority_score > 0.6
            
            # Add memory metadata
            enhanced_memory_item["memory_metadata"] = {
                "processed_at": datetime.now().isoformat(),
                "processor_version": "enhanced_screen_v1.0",
                "analysis_layers_count": len(analysis_data.get("layers", {})),
                "has_llava_analysis": "llava_analysis" in analysis_data.get("layers", {}),
                "processing_duration": analysis_data.get("analysis_duration", 0)
            }
            
            # Update processing stats
            self._update_processing_stats(enhanced_memory_item)
            
            logger.info(f"Processed screen analysis: {enhanced_memory_item.get('semantic_summary', 'unknown activity')} (priority: {priority_score:.2f})")
            return enhanced_memory_item
            
        except Exception as e:
            logger.error(f"Error processing total screen analysis: {e}")
            logger.error(traceback.format_exc())
            return None

    def _extract_memory_data_from_analysis(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract memory-relevant data from raw analysis layers"""
        try:
            layers = analysis_data.get("layers", {})
            
            # Extract from application analysis
            app_analysis = layers.get("application_analysis", {})
            window_context = layers.get("window_context", {})
            content_analysis = layers.get("content_analysis", {})
            workflow_analysis = layers.get("workflow_analysis", {})
            text_analysis = layers.get("text_analysis", {})
            
            memory_data = {
                "timestamp": analysis_data.get("timestamp", datetime.now().isoformat()),
                "image_hash": analysis_data.get("image_hash", ""),
                
                # Application context
                "application": {
                    "name": window_context.get("application_name", "Unknown"),
                    "detected_type": app_analysis.get("detected_app", "unknown"),
                    "confidence": app_analysis.get("confidence", 0.0)
                },
                
                # Content summary
                "content": {
                    "type": content_analysis.get("content_type", "unknown"),
                    "word_count": text_analysis.get("word_count", 0),
                    "has_meaningful_text": text_analysis.get("has_meaningful_content", False),
                    "primary_purpose": content_analysis.get("primary_purpose", "unknown"),
                    "interaction_level": content_analysis.get("interaction_level", "passive")
                },
                
                # User activity
                "user_activity": {
                    "current_activity": workflow_analysis.get("current_activity", "unknown"),
                    "workflow_stage": workflow_analysis.get("workflow_stage", "unknown"),
                    "user_intent": content_analysis.get("user_intent", "unknown"),
                    "productivity_context": workflow_analysis.get("productivity_context", "unknown")
                },
                
                # Text sample for context
                "text_sample": text_analysis.get("all_text", "")[:500]
            }
            
            return memory_data
            
        except Exception as e:
            logger.error(f"Error extracting memory data from analysis: {e}")
            return {}

    async def _enhance_for_memory_storage(self, memory_data: Dict[str, Any], full_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance memory data with additional context and insights"""
        try:
            enhanced_item = memory_data.copy()
            
            # Add comprehensive application context
            enhanced_item["application_context"] = self._extract_application_context(memory_data, full_analysis)
            
            # Add content insights
            enhanced_item["content_insights"] = self._extract_content_insights(memory_data, full_analysis)
            
            # Add workflow understanding
            enhanced_item["workflow_insights"] = self._extract_workflow_insights(memory_data, full_analysis)
            
            # Add visual context if available
            enhanced_item["visual_context"] = self._extract_visual_context(full_analysis)
            
            # Generate semantic tags for searchability
            enhanced_item["semantic_tags"] = self._generate_semantic_tags(enhanced_item)
            
            # Create searchable content field
            enhanced_item["searchable_content"] = self._create_searchable_content(enhanced_item)
            
            # Add memory relationships
            enhanced_item["memory_relationships"] = self._identify_memory_relationships(enhanced_item)
            
            return enhanced_item
            
        except Exception as e:
            logger.error(f"Error enhancing memory data: {e}")
            return memory_data

    def _extract_application_context(self, memory_data: Dict[str, Any], full_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed application context"""
        try:
            app_context = {
                "primary_app": memory_data.get("application", {}).get("name", "Unknown"),
                "app_category": "unknown",
                "detection_confidence": memory_data.get("application", {}).get("confidence", 0.0),
                "specific_context": {},
                "workflow_indicators": []
            }
            
            # Extract from application analysis layer
            app_analysis = full_analysis.get("layers", {}).get("application_analysis", {})
            if app_analysis.get("specific_context"):
                app_context["specific_context"] = app_analysis["specific_context"]
                
                # Determine app category from specific context
                service_type = app_analysis["specific_context"].get("service_type", "")
                if service_type:
                    if "code" in service_type or "editor" in service_type:
                        app_context["app_category"] = "development"
                    elif "browser" in service_type or "web" in service_type:
                        app_context["app_category"] = "web_browsing"
                    elif "communication" in service_type or "email" in service_type or "slack" in service_type:
                        app_context["app_category"] = "communication"
                    elif "document" in service_type or "text" in service_type:
                        app_context["app_category"] = "document_work"
                    else:
                        app_context["app_category"] = "productivity"
            
            # Extract workflow stage
            workflow_stage = app_context["specific_context"].get("workflow_stage", "")
            if workflow_stage:
                app_context["workflow_indicators"].append(f"stage: {workflow_stage}")
            
            # Add current activity
            current_activity = app_context["specific_context"].get("current_activity", "")
            if current_activity:
                app_context["workflow_indicators"].append(f"activity: {current_activity}")
            
            return app_context
            
        except Exception as e:
            logger.error(f"Error extracting application context: {e}")
            return {"primary_app": "Unknown", "app_category": "unknown"}

    def _extract_content_insights(self, memory_data: Dict[str, Any], full_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights about content being viewed/worked on"""
        try:
            content_insights = {
                "content_density": "low",
                "content_categories": [],
                "user_engagement": "passive",
                "semantic_meaning": [],
                "key_elements": []
            }
            
            # Analyze content density
            word_count = memory_data.get("content", {}).get("word_count", 0)
            if word_count > 500:
                content_insights["content_density"] = "high"
            elif word_count > 100:
                content_insights["content_density"] = "medium"
            
            # Extract text categories from analysis
            text_analysis = full_analysis.get("layers", {}).get("text_analysis", {})
            text_categories = text_analysis.get("text_categories", {})
            
            for category, items in text_categories.items():
                if items:  # If category has content
                    content_insights["content_categories"].append(category)
                    
                    # Add specific insights based on content type
                    if category == "urls" and items:
                        content_insights["key_elements"].append(f"websites: {len(items)} URLs")
                    elif category == "emails" and items:
                        content_insights["key_elements"].append(f"email addresses detected")
                    elif category == "code_snippets" and items:
                        content_insights["key_elements"].append(f"code: {len(items)} snippets")
                    elif category == "headings" and items:
                        content_insights["semantic_meaning"].extend(items[:3])  # Top 3 headings
            
            # Determine user engagement level
            interaction_level = memory_data.get("content", {}).get("interaction_level", "passive")
            if interaction_level == "active":
                content_insights["user_engagement"] = "active"
            elif word_count > 200 or len(content_insights["content_categories"]) > 2:
                content_insights["user_engagement"] = "engaged"
            
            return content_insights
            
        except Exception as e:
            logger.error(f"Error extracting content insights: {e}")
            return {"content_density": "low", "user_engagement": "passive"}

    def _extract_workflow_insights(self, memory_data: Dict[str, Any], full_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights about user workflow and productivity patterns"""
        try:
            workflow_insights = {
                "productivity_level": "standard",
                "task_complexity": "simple",
                "workflow_pattern": "unknown",
                "focus_indicators": [],
                "collaboration_signals": []
            }
            
            user_activity = memory_data.get("user_activity", {})
            
            # Analyze productivity context
            productivity_context = user_activity.get("productivity_context", "unknown")
            if productivity_context in ["creative_work", "productive_work"]:
                workflow_insights["productivity_level"] = "high"
            elif productivity_context in ["interactive_work", "collaboration"]:
                workflow_insights["productivity_level"] = "collaborative"
            
            # Determine task complexity from content analysis
            content_analysis = full_analysis.get("layers", {}).get("content_analysis", {})
            complexity = content_analysis.get("complexity_level", "simple")
            workflow_insights["task_complexity"] = complexity
            
            # Identify workflow patterns
            current_activity = user_activity.get("current_activity", "unknown")
            workflow_stage = user_activity.get("workflow_stage", "unknown")
            
            if current_activity != "unknown" and workflow_stage != "unknown":
                workflow_insights["workflow_pattern"] = f"{current_activity}_{workflow_stage}"
            
            # Extract focus indicators
            if complexity == "complex":
                workflow_insights["focus_indicators"].append("complex_task_engagement")
            
            if memory_data.get("content", {}).get("has_meaningful_text"):
                workflow_insights["focus_indicators"].append("content_heavy_interaction")
            
            # Look for collaboration signals
            text_sample = memory_data.get("text_sample", "").lower()
            collaboration_keywords = ["share", "comment", "collaborate", "team", "meeting", "discuss"]
            for keyword in collaboration_keywords:
                if keyword in text_sample:
                    workflow_insights["collaboration_signals"].append(keyword)
            
            return workflow_insights
            
        except Exception as e:
            logger.error(f"Error extracting workflow insights: {e}")
            return {"productivity_level": "standard", "task_complexity": "simple"}

    def _extract_visual_context(self, full_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract visual context from LLaVA analysis if available"""
        try:
            visual_context = {
                "has_visual_analysis": False,
                "visual_summary": "",
                "ui_elements_detected": 0,
                "layout_pattern": "unknown"
            }
            
            # Check for LLaVA analysis
            llava_analysis = full_analysis.get("layers", {}).get("llava_analysis", {})
            if llava_analysis and "error" not in llava_analysis:
                visual_context["has_visual_analysis"] = True
                visual_context["visual_summary"] = llava_analysis.get("visual_context", "")[:200]
                
                # Add application insights from LLaVA
                if "application" in llava_analysis:
                    app_name = llava_analysis["application"].get("name", "")
                    if app_name and app_name != "unknown":
                        visual_context["llava_detected_app"] = app_name
            
            # Extract UI analysis
            ui_analysis = full_analysis.get("layers", {}).get("ui_analysis", {})
            if ui_analysis:
                visual_context["ui_elements_detected"] = ui_analysis.get("total_count", 0)
                
                layout_structure = ui_analysis.get("layout_structure", {})
                visual_context["layout_pattern"] = layout_structure.get("layout_type", "unknown")
            
            return visual_context
            
        except Exception as e:
            logger.error(f"Error extracting visual context: {e}")
            return {"has_visual_analysis": False}

    def _generate_semantic_tags(self, enhanced_item: Dict[str, Any]) -> List[str]:
        """Generate semantic tags for improved searchability"""
        try:
            tags = []
            
            # Application tags
            app_name = enhanced_item.get("application", {}).get("name", "").lower()
            if app_name and app_name != "unknown":
                tags.append(f"app:{app_name}")
            
            app_category = enhanced_item.get("application_context", {}).get("app_category", "")
            if app_category != "unknown":
                tags.append(f"category:{app_category}")
            
            # Activity tags
            current_activity = enhanced_item.get("user_activity", {}).get("current_activity", "")
            if current_activity != "unknown":
                tags.append(f"activity:{current_activity}")
            
            workflow_stage = enhanced_item.get("user_activity", {}).get("workflow_stage", "")
            if workflow_stage != "unknown":
                tags.append(f"stage:{workflow_stage}")
            
            # Content tags
            content_type = enhanced_item.get("content", {}).get("type", "")
            if content_type != "unknown":
                tags.append(f"content:{content_type}")
            
            # Productivity tags
            productivity_level = enhanced_item.get("workflow_insights", {}).get("productivity_level", "")
            if productivity_level != "standard":
                tags.append(f"productivity:{productivity_level}")
            
            # Engagement tags
            user_engagement = enhanced_item.get("content_insights", {}).get("user_engagement", "")
            if user_engagement != "passive":
                tags.append(f"engagement:{user_engagement}")
            
            # Content density tags
            content_density = enhanced_item.get("content_insights", {}).get("content_density", "")
            if content_density != "low":
                tags.append(f"density:{content_density}")
            
            return list(set(tags))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error generating semantic tags: {e}")
            return []

    def _create_searchable_content(self, enhanced_item: Dict[str, Any]) -> str:
        """Create searchable content field combining all relevant text"""
        try:
            content_parts = []
            
            # Application info
            app_name = enhanced_item.get("application", {}).get("name", "")
            if app_name != "Unknown":
                content_parts.append(app_name)
            
            # Activity and workflow
            current_activity = enhanced_item.get("user_activity", {}).get("current_activity", "")
            if current_activity != "unknown":
                content_parts.append(current_activity)
            
            workflow_stage = enhanced_item.get("user_activity", {}).get("workflow_stage", "")
            if workflow_stage != "unknown":
                content_parts.append(workflow_stage)
            
            # Content insights
            semantic_meaning = enhanced_item.get("content_insights", {}).get("semantic_meaning", [])
            content_parts.extend(semantic_meaning[:3])  # Top 3 semantic elements
            
            # Text sample
            text_sample = enhanced_item.get("text_sample", "")
            if text_sample:
                # Take first 200 characters of text sample
                content_parts.append(text_sample[:200])
            
            # Visual context
            visual_summary = enhanced_item.get("visual_context", {}).get("visual_summary", "")
            if visual_summary:
                content_parts.append(visual_summary)
            
            return " | ".join(content_parts)
            
        except Exception as e:
            logger.error(f"Error creating searchable content: {e}")
            return ""

    def _identify_memory_relationships(self, enhanced_item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify relationships this memory item might have with others"""
        try:
            relationships = []
            
            # Application continuity relationship
            app_name = enhanced_item.get("application", {}).get("name", "")
            if app_name != "Unknown":
                relationships.append({
                    "type": "application_continuity",
                    "key": f"app:{app_name}",
                    "description": f"Part of {app_name} usage session"
                })
            
            # Workflow relationship
            current_activity = enhanced_item.get("user_activity", {}).get("current_activity", "")
            if current_activity != "unknown":
                relationships.append({
                    "type": "workflow_continuity",
                    "key": f"activity:{current_activity}",
                    "description": f"Part of {current_activity} workflow"
                })
            
            # Content relationship
            content_type = enhanced_item.get("content", {}).get("type", "")
            if content_type != "unknown":
                relationships.append({
                    "type": "content_similarity",
                    "key": f"content:{content_type}",
                    "description": f"Similar {content_type} content"
                })
            
            # Time-based relationship
            relationships.append({
                "type": "temporal_sequence",
                "key": f"time:{datetime.now().strftime('%Y-%m-%d-%H')}",
                "description": "Part of current time period activity"
            })
            
            return relationships
            
        except Exception as e:
            logger.error(f"Error identifying memory relationships: {e}")
            return []

    def _calculate_memory_priority(self, enhanced_item: Dict[str, Any]) -> float:
        """Calculate memory priority score based on various factors"""
        try:
            priority_score = 0.0
            
            # Application detection confidence
            app_confidence = enhanced_item.get("application", {}).get("confidence", 0.0)
            if app_confidence > 0.7:
                priority_score += self.priority_weights["application_detected"]
            
            # Workflow identification
            workflow_stage = enhanced_item.get("user_activity", {}).get("workflow_stage", "")
            if workflow_stage != "unknown":
                priority_score += self.priority_weights["workflow_identified"]
            
            # Content richness
            word_count = enhanced_item.get("content", {}).get("word_count", 0)
            if word_count > 100:
                priority_score += self.priority_weights["content_rich"]
            
            # User interaction level
            interaction_level = enhanced_item.get("content", {}).get("interaction_level", "passive")
            if interaction_level == "active":
                priority_score += self.priority_weights["user_interaction"]
            
            # LLaVA analysis availability
            has_visual_analysis = enhanced_item.get("visual_context", {}).get("has_visual_analysis", False)
            if has_visual_analysis:
                priority_score += self.priority_weights["llava_analysis"]
            
            # Semantic understanding depth
            semantic_tags_count = len(enhanced_item.get("semantic_tags", []))
            if semantic_tags_count > 3:
                priority_score += self.priority_weights["semantic_understanding"]
            
            # Productivity context boost
            productivity_level = enhanced_item.get("workflow_insights", {}).get("productivity_level", "standard")
            if productivity_level in ["high", "collaborative"]:
                priority_score += 0.2
            
            # Cap at 1.0
            return min(priority_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating memory priority: {e}")
            return 0.5  # Default medium priority

    def _update_processing_stats(self, enhanced_item: Dict[str, Any]):
        """Update processing statistics"""
        try:
            self.processing_stats["total_processed"] += 1
            
            if enhanced_item.get("memory_priority", 0) > 0.7:
                self.processing_stats["high_priority_items"] += 1
            
            if enhanced_item.get("application", {}).get("confidence", 0) > 0.7:
                self.processing_stats["application_context_items"] += 1
            
            if enhanced_item.get("user_activity", {}).get("workflow_stage", "") != "unknown":
                self.processing_stats["workflow_detections"] += 1
            
            if enhanced_item.get("content", {}).get("word_count", 0) > 100:
                self.processing_stats["content_rich_items"] += 1
                
        except Exception as e:
            logger.error(f"Error updating processing stats: {e}")

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return self.processing_stats.copy()

    async def feed_to_memory_system(self, enhanced_memory_item: Dict[str, Any]) -> bool:
        """Feed the enhanced memory item to the memory system"""
        try:
            if not self.memory_system:
                logger.warning("No memory system configured")
                return False
            
            # Determine memory type based on priority and content
            memory_priority = enhanced_memory_item.get("memory_priority", 0.5)
            
            if memory_priority > 0.8:
                # High priority -> Long-term memory
                await self.memory_system.add_to_long_term_memory(enhanced_memory_item)
                logger.info("Added high-priority item to long-term memory")
            elif memory_priority > 0.6:
                # Medium-high priority -> Context memory
                await self.memory_system.add_to_context_memory(enhanced_memory_item)
                logger.info("Added medium-priority item to context memory")
            else:
                # Standard priority -> Short-term memory
                await self.memory_system.add_to_short_term_memory(enhanced_memory_item)
                logger.info("Added standard-priority item to short-term memory")
            
            return True
            
        except Exception as e:
            logger.error(f"Error feeding to memory system: {e}")
            return False

# Usage example and integration point
async def process_and_feed_screen_analysis(analysis_data: Dict[str, Any], memory_system=None):
    """
    Main function to process Total Screen Analyzer data and feed to memory.
    This should be called by the bridge server when receiving data from Total Screen Analyzer.
    """
    try:
        processor = EnhancedScreenMemoryProcessor(memory_system)
        enhanced_item = await processor.process_total_screen_analysis(analysis_data)
        
        if enhanced_item:
            success = await processor.feed_to_memory_system(enhanced_item)
            
            if success:
                logger.info(f"Successfully processed and stored screen analysis: {enhanced_item.get('semantic_summary', 'unknown')}")
                return enhanced_item
            else:
                logger.error("Failed to feed processed item to memory system")
                return None
        else:
            logger.error("Failed to process screen analysis data")
            return None
            
    except Exception as e:
        logger.error(f"Error in process_and_feed_screen_analysis: {e}")
        return None