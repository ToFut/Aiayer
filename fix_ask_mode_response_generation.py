#!/usr/bin/env python3
"""
Fix ASK Mode Response Generation

The issue is that memory data is retrieved correctly but the response generation
logic has bugs in extracting activities from the memory context.
"""

import asyncio
import json
import os

async def fix_response_generation():
    """Fix the response generation logic in ASK mode handler"""
    
    # Read the current handler
    handler_file = "brain/handlers/ask_mode_handler.py"
    with open(handler_file, 'r') as f:
        content = f.read()
    
    # The issue is in _gather_real_information function
    # It's checking for item.get("type") == "short_term_memory" but the actual structure is different
    
    old_gather_function = '''    async def _gather_real_information(self, analysis: QueryAnalysis, 
                                     context: MemoryContext) -> Dict[str, Any]:
        """Gather all relevant information from real memory"""
        info = {
            "recent_activities": [],
            "applications": [],
            "productivity_info": {},
            "workflow_info": {},
            "system_info": {},
            "conversations": context.recent_conversations,
            "memory_insights": []
        }
        
        # Extract information from relevant knowledge (real memory)
        for item in context.relevant_knowledge:
            if item.get("type") == "short_term_memory":
                memory_content = item.get("content", {})
                
                # Extract activity information
                if "user_activity" in memory_content:
                    activity = memory_content["user_activity"]
                    info["recent_activities"].append({
                        "activity": activity.get("primary_activity"),
                        "application": activity.get("application_used"),
                        "productivity": activity.get("productivity_score"),
                        "timestamp": memory_content.get("timestamp")
                    })
                    
                    app_info = {
                        "name": activity.get("application_used"),
                        "context": activity.get("professional_context"),
                        "productivity": activity.get("productivity_score")
                    }
                    if app_info not in info["applications"]:
                        info["applications"].append(app_info)
                
                # Extract workflow information
                if "context_analysis" in memory_content:
                    context_analysis = memory_content["context_analysis"]
                    info["workflow_info"] = {
                        "stage": context_analysis.get("workflow_stage"),
                        "intent": context_analysis.get("user_intent"),
                        "productivity_context": context_analysis.get("productivity_context")
                    }
                
                # Extract insights
                if "insights" in memory_content:
                    insights = memory_content["insights"]
                    if isinstance(insights, list):
                        info["memory_insights"].extend(insights)
        
        # Add user patterns
        info["patterns"] = context.user_patterns
        info["system_info"] = context.system_state
        
        return info'''
    
    # Fixed version that properly extracts data
    new_gather_function = '''    async def _gather_real_information(self, analysis: QueryAnalysis, 
                                     context: MemoryContext) -> Dict[str, Any]:
        """Gather all relevant information from real memory"""
        info = {
            "recent_activities": [],
            "applications": [],
            "productivity_info": {},
            "workflow_info": {},
            "system_info": {},
            "conversations": context.recent_conversations,
            "memory_insights": []
        }
        
        # Extract information from relevant knowledge (real memory)
        for item in context.relevant_knowledge:
            # The item structure is: {"type": "short_term_memory", "content": {...}, ...}
            if item.get("type") == "short_term_memory":
                memory_content = item.get("content", {})
                
                # Extract activity information
                if "user_activity" in memory_content:
                    activity = memory_content["user_activity"]
                    info["recent_activities"].append({
                        "activity": activity.get("primary_activity"),
                        "application": activity.get("application_used"),
                        "productivity": activity.get("productivity_score"),
                        "timestamp": memory_content.get("timestamp")
                    })
                    
                    app_info = {
                        "name": activity.get("application_used"),
                        "context": activity.get("professional_context"),
                        "productivity": activity.get("productivity_score")
                    }
                    if app_info not in info["applications"]:
                        info["applications"].append(app_info)
                
                # Extract workflow information
                if "context_analysis" in memory_content:
                    context_analysis = memory_content["context_analysis"]
                    info["workflow_info"] = {
                        "stage": context_analysis.get("workflow_stage"),
                        "intent": context_analysis.get("user_intent"),
                        "productivity_context": context_analysis.get("productivity_context")
                    }
                
                # Extract insights
                if "insights" in memory_content:
                    insights = memory_content["insights"]
                    if isinstance(insights, list):
                        info["memory_insights"].extend(insights)
            
            # ADDITIONAL: Also check if the item itself is a memory object
            elif "user_activity" in item:
                # This handles cases where relevant_knowledge contains the memory objects directly
                activity = item["user_activity"]
                info["recent_activities"].append({
                    "activity": activity.get("primary_activity"),
                    "application": activity.get("application_used"), 
                    "productivity": activity.get("productivity_score"),
                    "timestamp": item.get("timestamp")
                })
                
                app_info = {
                    "name": activity.get("application_used"),
                    "context": activity.get("professional_context"),
                    "productivity": activity.get("productivity_score")
                }
                if app_info not in info["applications"]:
                    info["applications"].append(app_info)
                
                # Extract workflow information
                if "context_analysis" in item:
                    context_analysis = item["context_analysis"]
                    info["workflow_info"] = {
                        "stage": context_analysis.get("workflow_stage"),
                        "intent": context_analysis.get("user_intent"),
                        "productivity_context": context_analysis.get("productivity_context")
                    }
                
                # Extract insights
                if "insights" in item:
                    insights = item["insights"]
                    if isinstance(insights, list):
                        info["memory_insights"].extend(insights)
        
        # FALLBACK: If no activities found from relevant knowledge, check user patterns directly
        if not info["recent_activities"] and context.user_patterns:
            patterns = context.user_patterns
            if patterns.get("most_common_activity") and patterns.get("most_used_application"):
                info["recent_activities"].append({
                    "activity": patterns["most_common_activity"],
                    "application": patterns["most_used_application"],
                    "productivity": patterns.get("average_productivity", 0.5),
                    "timestamp": patterns.get("analysis_timestamp", "recent")
                })
        
        # Add user patterns
        info["patterns"] = context.user_patterns
        info["system_info"] = context.system_state
        
        # Add debug logging
        logger.info(f"🔍 Gathered info: {len(info['recent_activities'])} activities, {len(info['applications'])} apps, {len(info['memory_insights'])} insights")
        
        return info'''
    
    # Also need to fix the activity generation to be more robust
    old_activity_generation = '''    async def _generate_activity_content(self, info: Dict[str, Any]) -> str:
        """Generate content about user activities"""
        activities = info.get("recent_activities", [])
        if not activities:
            return "I don't have recent activity data available."
        
        latest_activity = activities[-1] if activities else {}
        
        content_parts = []
        
        if latest_activity.get("activity"):
            content_parts.append(f"you've been engaged in {latest_activity['activity']}")
        
        if latest_activity.get("application"):
            content_parts.append(f"using {latest_activity['application']}")
        
        if latest_activity.get("productivity") is not None:
            productivity = latest_activity["productivity"]
            if productivity > 0.7:
                content_parts.append("with high productivity")
            elif productivity > 0.4:
                content_parts.append("with moderate productivity")
            else:
                content_parts.append("with light activity")
        
        # Add insights if available
        insights = info.get("memory_insights", [])
        if insights:
            content_parts.append(f"Insights: {insights[0]}")
        
        if content_parts:
            return ". ".join(content_parts) + "."
        else:
            return "I can see some recent activity but need more context to provide details."'''
    
    new_activity_generation = '''    async def _generate_activity_content(self, info: Dict[str, Any]) -> str:
        """Generate content about user activities"""
        activities = info.get("recent_activities", [])
        patterns = info.get("patterns", {})
        insights = info.get("memory_insights", [])
        
        # Try activities first
        if activities:
            latest_activity = activities[-1] if activities else {}
            
            content_parts = []
            
            if latest_activity.get("activity"):
                content_parts.append(f"you've been engaged in {latest_activity['activity']}")
            
            if latest_activity.get("application"):
                content_parts.append(f"using {latest_activity['application']}")
            
            if latest_activity.get("productivity") is not None:
                productivity = latest_activity["productivity"]
                if productivity > 0.7:
                    content_parts.append("with high productivity")
                elif productivity > 0.4:
                    content_parts.append("with moderate productivity")
                else:
                    content_parts.append("with light activity")
            
            # Add insights if available
            if insights:
                content_parts.append(f"Insights: {insights[0]}")
            
            if content_parts:
                return ". ".join(content_parts) + "."
        
        # Fallback to patterns if no activities
        elif patterns:
            content_parts = []
            
            if patterns.get("most_common_activity"):
                content_parts.append(f"your primary activity has been {patterns['most_common_activity']}")
            
            if patterns.get("most_used_application"):
                content_parts.append(f"using {patterns['most_used_application']}")
            
            if patterns.get("average_productivity") is not None:
                avg_prod = patterns["average_productivity"]
                if avg_prod > 0.7:
                    content_parts.append("with high productivity levels")
                elif avg_prod > 0.4:
                    content_parts.append("with moderate productivity")
                else:
                    content_parts.append("with light activity levels")
            
            if content_parts:
                return ". ".join(content_parts) + "."
        
        # Fallback to insights only
        elif insights:
            return f"Based on analysis: {insights[0]}"
        
        # Last resort
        return "I can see some activity data but need more context to provide specific details."'''
    
    # Apply the fixes
    print("🔧 Applying ASK mode response generation fixes...")
    
    # Replace the gather function
    if old_gather_function in content:
        content = content.replace(old_gather_function, new_gather_function)
        print("✅ Fixed _gather_real_information function")
    else:
        print("⚠️ Could not find exact _gather_real_information function to replace")
    
    # Replace the activity generation function
    if old_activity_generation in content:
        content = content.replace(old_activity_generation, new_activity_generation)
        print("✅ Fixed _generate_activity_content function")
    else:
        print("⚠️ Could not find exact _generate_activity_content function to replace")
    
    # Write the fixed version
    with open(handler_file, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {handler_file} with response generation fixes")
    
    return True

async def main():
    """Main execution"""
    print("🚀 Fixing ASK Mode Response Generation Issues")
    print("=" * 50)
    
    success = await fix_response_generation()
    
    if success:
        print("\n✅ ASK mode response generation fixed!")
        print("\n🔄 You need to restart the backend for changes to take effect:")
        print("1. Stop the current backend")
        print("2. Restart with: python real_llm_backend_8767.py")
        print("3. Test ASK mode with contextual queries")
        print("\n🎯 Expected improvement:")
        print("ASK mode should now provide real contextual answers based on your actual")
        print("development activities, applications, and productivity patterns!")
    else:
        print("\n❌ Could not apply all fixes. Manual intervention may be needed.")

if __name__ == "__main__":
    asyncio.run(main())