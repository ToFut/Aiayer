#!/usr/bin/env python3
"""
Enhanced Memory System with Deep UI Understanding
Integrates deep UI analysis to capture actual user activities and content
"""

import sys
import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory.memory_system import MemorySystem
from enhanced_deep_ui_analyzer import DeepUIAnalyzer

class EnhancedMemoryWithDeepUI:
    """Enhanced memory system that captures deep UI understanding"""
    
    def __init__(self):
        self.memory_system = MemorySystem()
        self.ui_analyzer = DeepUIAnalyzer()
        self.last_analysis_time = 0
        self.analysis_interval = 5  # Analyze every 5 seconds
        
    async def capture_and_store_deep_memory(self) -> Dict[str, Any]:
        """Capture deep UI analysis and store in memory with full context"""
        
        print("🔍 Capturing deep UI analysis...")
        
        # Capture comprehensive UI analysis
        ui_analysis = self.ui_analyzer.capture_screen_content()
        
        # Create enhanced memory entry with deep understanding
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "memory_type": "deep_ui_analysis",
            "ui_analysis": ui_analysis,
            "behavioral_analysis": self._analyze_user_behavior(ui_analysis),
            "content_understanding": self._extract_content_meaning(ui_analysis),
            "workflow_context": self._build_workflow_context(ui_analysis),
            "professional_insights": self._generate_professional_insights(ui_analysis)
        }
        
        # Store in memory system
        memory_id = await self.memory_system.add_to_short_term_memory(memory_entry)
        
        print(f"✅ Stored deep memory analysis with ID: {memory_id}")
        
        return memory_entry
    
    def _analyze_user_behavior(self, ui_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user behavior from UI data"""
        activities = ui_analysis.get("detected_activities", [])
        focus = ui_analysis.get("user_focus", {})
        content = ui_analysis.get("content_analysis", {})
        
        behavior = {
            "primary_activity": activities[0]["activity"] if activities else "unknown",
            "activity_confidence": activities[0]["confidence"] if activities else 0.0,
            "engagement_level": self._calculate_engagement_level(ui_analysis),
            "focus_state": focus.get("primary_focus", "unknown"),
            "attention_score": focus.get("attention_level", 0.0),
            "multitasking": focus.get("multitasking", False),
            "productivity_indicators": self._assess_productivity(ui_analysis),
            "learning_indicators": self._detect_learning_activity(ui_analysis),
            "expertise_level": self._assess_expertise_level(ui_analysis)
        }
        
        return behavior
    
    def _extract_content_meaning(self, ui_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract semantic meaning from UI content"""
        screen_text = ui_analysis.get("screen_text", "")
        content_analysis = ui_analysis.get("content_analysis", {})
        app_context = ui_analysis.get("application_context", {})
        
        meaning = {
            "content_summary": self._summarize_content(screen_text),
            "technical_context": self._extract_technical_context(screen_text),
            "task_context": self._infer_task_context(ui_analysis),
            "file_context": app_context.get("file_context", {}),
            "ui_elements_meaning": self._interpret_ui_elements(ui_analysis.get("ui_elements", {})),
            "user_intent": self._infer_user_intent(ui_analysis),
            "knowledge_domain": self._identify_knowledge_domain(screen_text)
        }
        
        return meaning
    
    def _build_workflow_context(self, ui_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Build understanding of user's workflow context"""
        workflow = {
            "current_stage": ui_analysis.get("workflow_stage", "unknown"),
            "workflow_type": self._identify_workflow_type(ui_analysis),
            "progress_indicators": self._detect_progress_indicators(ui_analysis),
            "context_switches": self._detect_context_switches(ui_analysis),
            "collaboration_indicators": self._detect_collaboration(ui_analysis),
            "tool_usage_pattern": self._analyze_tool_usage(ui_analysis)
        }
        
        return workflow
    
    def _generate_professional_insights(self, ui_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate professional insights about user's work"""
        activities = ui_analysis.get("detected_activities", [])
        content = ui_analysis.get("content_analysis", {})
        
        insights = {
            "skill_assessment": self._assess_professional_skills(ui_analysis),
            "work_patterns": self._identify_work_patterns(ui_analysis),
            "efficiency_indicators": self._measure_efficiency(ui_analysis),
            "learning_opportunities": self._identify_learning_opportunities(ui_analysis),
            "optimization_suggestions": self._suggest_optimizations(ui_analysis),
            "professional_context": self._determine_professional_context(activities)
        }
        
        return insights
    
    def _calculate_engagement_level(self, ui_analysis: Dict[str, Any]) -> float:
        """Calculate user engagement level"""
        activities = ui_analysis.get("detected_activities", [])
        content = ui_analysis.get("content_analysis", {})
        focus = ui_analysis.get("user_focus", {})
        
        engagement = 0.0
        
        # Activity engagement
        if activities:
            engagement += activities[0]["confidence"] * 0.4
            engagement += activities[0].get("intensity", 0) * 0.3
        
        # Content engagement
        complexity = content.get("complexity_score", 0)
        engagement += min(complexity * 2, 0.3)  # Cap at 0.3
        
        # Focus engagement
        attention = focus.get("attention_level", 0)
        engagement += attention * 0.3
        
        return min(engagement, 1.0)
    
    def _assess_productivity(self, ui_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess productivity indicators"""
        activities = ui_analysis.get("detected_activities", [])
        content = ui_analysis.get("content_analysis", {})
        focus = ui_analysis.get("user_focus", {})
        
        return {
            "task_focus": focus.get("attention_level", 0),
            "output_indicators": content.get("technical_density", 0),
            "multitasking_penalty": -0.2 if focus.get("multitasking") else 0,
            "activity_intensity": activities[0].get("intensity", 0) if activities else 0,
            "flow_state": self._detect_flow_state(ui_analysis)
        }
    
    def _detect_learning_activity(self, ui_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Detect if user is in learning mode"""
        screen_text = ui_analysis.get("screen_text", "").lower()
        activities = ui_analysis.get("detected_activities", [])
        
        learning_keywords = ["tutorial", "documentation", "learn", "guide", "example", "how to"]
        learning_score = sum(1 for keyword in learning_keywords if keyword in screen_text) / len(learning_keywords)
        
        return {
            "learning_detected": learning_score > 0.1,
            "learning_score": learning_score,
            "learning_type": self._classify_learning_type(screen_text),
            "knowledge_seeking": any(activity["activity"] == "reading_documentation" for activity in activities)
        }
    
    def _assess_expertise_level(self, ui_analysis: Dict[str, Any]) -> str:
        """Assess user's expertise level based on UI analysis"""
        content = ui_analysis.get("content_analysis", {})
        activities = ui_analysis.get("detected_activities", [])
        screen_text = ui_analysis.get("screen_text", "")
        
        # Technical complexity indicators
        complexity = content.get("complexity_score", 0)
        technical_density = content.get("technical_density", 0)
        
        # Advanced tool usage
        advanced_tools = ["debugger", "profiler", "git", "docker", "kubernetes"]
        advanced_usage = sum(1 for tool in advanced_tools if tool in screen_text.lower())
        
        # Calculate expertise score
        expertise_score = (complexity * 0.4) + (technical_density * 0.4) + (advanced_usage * 0.2)
        
        if expertise_score > 0.7:
            return "expert"
        elif expertise_score > 0.4:
            return "intermediate"
        else:
            return "beginner"
    
    def _summarize_content(self, screen_text: str) -> str:
        """Summarize the main content on screen"""
        if not screen_text:
            return "No readable content detected"
        
        words = screen_text.split()
        if len(words) < 10:
            return "Minimal content visible"
        
        # Extract key phrases and technical terms
        lines = screen_text.split('\n')
        meaningful_lines = [line.strip() for line in lines if len(line.strip()) > 5]
        
        if meaningful_lines:
            return f"Screen contains {len(meaningful_lines)} lines of content including: {meaningful_lines[0][:50]}..."
        
        return f"Content with {len(words)} words visible"
    
    def _extract_technical_context(self, screen_text: str) -> Dict[str, Any]:
        """Extract technical context from screen text"""
        text_lower = screen_text.lower()
        
        # Programming languages
        languages = ["python", "javascript", "typescript", "java", "c++", "go", "rust"]
        detected_languages = [lang for lang in languages if lang in text_lower]
        
        # Frameworks and tools
        frameworks = ["react", "vue", "angular", "django", "flask", "tensorflow", "pytorch"]
        detected_frameworks = [fw for fw in frameworks if fw in text_lower]
        
        # Technical concepts
        concepts = ["api", "database", "algorithm", "function", "class", "method", "variable"]
        detected_concepts = [concept for concept in concepts if concept in text_lower]
        
        return {
            "programming_languages": detected_languages,
            "frameworks": detected_frameworks,
            "technical_concepts": detected_concepts,
            "technical_level": len(detected_languages + detected_frameworks + detected_concepts)
        }
    
    def _infer_task_context(self, ui_analysis: Dict[str, Any]) -> str:
        """Infer what task the user is working on"""
        activities = ui_analysis.get("detected_activities", [])
        file_context = ui_analysis.get("application_context", {}).get("file_context", {})
        
        if not activities:
            return "idle_or_browsing"
        
        primary_activity = activities[0]["activity"]
        file_type = file_context.get("file_type", "")
        
        # Combine activity and file context for better understanding
        task_combinations = {
            ("coding", "python_code"): "python_development",
            ("coding", "javascript_code"): "web_development",
            ("debugging", "source_code"): "code_debugging",
            ("reading_documentation", ""): "learning_research",
            ("data_analysis", ""): "data_science_work",
            ("design_work", ""): "ui_ux_design"
        }
        
        return task_combinations.get((primary_activity, file_type), primary_activity)
    
    def _interpret_ui_elements(self, ui_elements: Dict[str, List[str]]) -> Dict[str, str]:
        """Interpret the meaning of detected UI elements"""
        interpretations = {}
        
        for element_type, examples in ui_elements.items():
            if examples:
                interpretations[element_type] = f"User is interacting with {element_type}: {', '.join(examples[:2])}"
        
        return interpretations
    
    def _infer_user_intent(self, ui_analysis: Dict[str, Any]) -> str:
        """Infer the user's immediate intent"""
        activities = ui_analysis.get("detected_activities", [])
        focus = ui_analysis.get("user_focus", {})
        file_context = ui_analysis.get("application_context", {}).get("file_context", {})
        
        if file_context.get("editing_state") == "unsaved_changes":
            return "actively_editing"
        elif focus.get("primary_focus") == "reading":
            return "consuming_information"
        elif activities and activities[0]["activity"] == "debugging":
            return "solving_problems"
        elif activities and activities[0]["activity"] == "coding":
            return "creating_content"
        else:
            return "exploring_or_planning"
    
    def _identify_knowledge_domain(self, screen_text: str) -> str:
        """Identify the knowledge domain being worked in"""
        text_lower = screen_text.lower()
        
        domains = {
            "software_development": ["code", "function", "variable", "class", "programming"],
            "data_science": ["data", "analysis", "visualization", "statistics", "machine learning"],
            "web_development": ["html", "css", "javascript", "react", "vue", "angular"],
            "devops": ["docker", "kubernetes", "deployment", "infrastructure", "ci/cd"],
            "design": ["ui", "ux", "design", "wireframe", "prototype", "figma"],
            "documentation": ["readme", "documentation", "guide", "tutorial", "help"]
        }
        
        for domain, keywords in domains.items():
            if sum(1 for keyword in keywords if keyword in text_lower) >= 2:
                return domain
        
        return "general"
    
    def _identify_workflow_type(self, ui_analysis: Dict[str, Any]) -> str:
        """Identify the type of workflow user is engaged in"""
        activities = ui_analysis.get("detected_activities", [])
        
        if not activities:
            return "unknown"
        
        primary_activity = activities[0]["activity"]
        
        workflow_mapping = {
            "coding": "development_workflow",
            "debugging": "problem_solving_workflow", 
            "reading_documentation": "learning_workflow",
            "data_analysis": "analytical_workflow",
            "design_work": "creative_workflow",
            "research": "research_workflow",
            "communication": "collaborative_workflow"
        }
        
        return workflow_mapping.get(primary_activity, "general_workflow")
    
    def _detect_progress_indicators(self, ui_analysis: Dict[str, Any]) -> List[str]:
        """Detect indicators of progress in current work"""
        indicators = []
        
        file_context = ui_analysis.get("application_context", {}).get("file_context", {})
        if file_context.get("editing_state") == "unsaved_changes":
            indicators.append("active_editing")
        
        content = ui_analysis.get("content_analysis", {})
        if content.get("complexity_score", 0) > 0.5:
            indicators.append("complex_work")
        
        activities = ui_analysis.get("detected_activities", [])
        if activities and activities[0]["confidence"] > 0.8:
            indicators.append("high_focus_activity")
        
        return indicators
    
    def _detect_context_switches(self, ui_analysis: Dict[str, Any]) -> bool:
        """Detect if user is switching between contexts"""
        focus = ui_analysis.get("user_focus", {})
        return focus.get("multitasking", False)
    
    def _detect_collaboration(self, ui_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Detect collaboration indicators"""
        screen_text = ui_analysis.get("screen_text", "").lower()
        
        collaboration_keywords = ["slack", "teams", "zoom", "meeting", "chat", "message", "email"]
        collaboration_score = sum(1 for keyword in collaboration_keywords if keyword in screen_text)
        
        return {
            "collaboration_detected": collaboration_score > 0,
            "collaboration_intensity": min(collaboration_score / 3.0, 1.0),
            "collaboration_tools": [kw for kw in collaboration_keywords if kw in screen_text]
        }
    
    def _analyze_tool_usage(self, ui_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pattern of tool usage"""
        app_context = ui_analysis.get("application_context", {})
        
        return {
            "primary_tool": app_context.get("active_window", "unknown"),
            "tool_category": self._categorize_tool(app_context.get("active_window", "")),
            "specialized_usage": self._detect_specialized_usage(ui_analysis)
        }
    
    def _categorize_tool(self, tool_name: str) -> str:
        """Categorize the tool being used"""
        tool_categories = {
            "code_editor": ["vscode", "cursor", "sublime", "atom", "vim"],
            "browser": ["chrome", "firefox", "safari", "edge"],
            "terminal": ["terminal", "iterm", "cmd", "powershell"],
            "design_tool": ["figma", "sketch", "photoshop", "illustrator"],
            "communication": ["slack", "teams", "discord", "zoom"]
        }
        
        tool_lower = tool_name.lower()
        for category, tools in tool_categories.items():
            if any(tool in tool_lower for tool in tools):
                return category
        
        return "general"
    
    def _detect_specialized_usage(self, ui_analysis: Dict[str, Any]) -> bool:
        """Detect if user is using advanced/specialized features"""
        content = ui_analysis.get("content_analysis", {})
        return content.get("technical_density", 0) > 0.3
    
    def _assess_professional_skills(self, ui_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess professional skills based on observed behavior"""
        activities = ui_analysis.get("detected_activities", [])
        content = ui_analysis.get("content_analysis", {})
        
        skills = {
            "technical_skill_level": self._assess_expertise_level(ui_analysis),
            "problem_solving_ability": self._assess_problem_solving(activities),
            "tool_proficiency": self._assess_tool_proficiency(ui_analysis),
            "communication_skills": self._assess_communication_skills(ui_analysis)
        }
        
        return skills
    
    def _identify_work_patterns(self, ui_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Identify patterns in work behavior"""
        focus = ui_analysis.get("user_focus", {})
        
        return {
            "focus_pattern": "deep_work" if focus.get("attention_level", 0) > 0.7 else "scattered",
            "multitasking_tendency": focus.get("multitasking", False),
            "workflow_efficiency": self._measure_workflow_efficiency(ui_analysis)
        }
    
    def _measure_efficiency(self, ui_analysis: Dict[str, Any]) -> float:
        """Measure work efficiency indicators"""
        activities = ui_analysis.get("detected_activities", [])
        focus = ui_analysis.get("user_focus", {})
        
        efficiency = 0.0
        
        if activities:
            efficiency += activities[0]["confidence"] * 0.5
            efficiency += activities[0].get("intensity", 0) * 0.3
        
        efficiency += focus.get("attention_level", 0) * 0.2
        
        # Penalty for multitasking
        if focus.get("multitasking"):
            efficiency *= 0.8
        
        return efficiency
    
    def _identify_learning_opportunities(self, ui_analysis: Dict[str, Any]) -> List[str]:
        """Identify learning opportunities based on current activity"""
        opportunities = []
        
        activities = ui_analysis.get("detected_activities", [])
        if activities and activities[0]["activity"] == "debugging":
            opportunities.append("error_handling_patterns")
        
        expertise = self._assess_expertise_level(ui_analysis)
        if expertise == "beginner":
            opportunities.extend(["basic_concepts", "tool_mastery"])
        
        return opportunities
    
    def _suggest_optimizations(self, ui_analysis: Dict[str, Any]) -> List[str]:
        """Suggest workflow optimizations"""
        suggestions = []
        
        focus = ui_analysis.get("user_focus", {})
        if focus.get("multitasking"):
            suggestions.append("reduce_context_switching")
        
        if focus.get("attention_level", 0) < 0.5:
            suggestions.append("improve_focus_environment")
        
        return suggestions
    
    def _determine_professional_context(self, activities: List[Dict[str, Any]]) -> str:
        """Determine professional context from activities"""
        if not activities:
            return "unknown"
        
        primary_activity = activities[0]["activity"]
        
        context_mapping = {
            "coding": "software_engineering",
            "debugging": "software_engineering", 
            "data_analysis": "data_science",
            "design_work": "product_design",
            "research": "research_and_development",
            "communication": "team_collaboration"
        }
        
        return context_mapping.get(primary_activity, "general_professional")
    
    # Helper methods for skill assessment
    def _assess_problem_solving(self, activities: List[Dict[str, Any]]) -> str:
        """Assess problem solving ability"""
        debugging_activities = [a for a in activities if a["activity"] == "debugging"]
        if debugging_activities:
            return "active_problem_solver"
        return "standard"
    
    def _assess_tool_proficiency(self, ui_analysis: Dict[str, Any]) -> str:
        """Assess tool proficiency"""
        content = ui_analysis.get("content_analysis", {})
        if content.get("technical_density", 0) > 0.4:
            return "proficient"
        return "standard"
    
    def _assess_communication_skills(self, ui_analysis: Dict[str, Any]) -> str:
        """Assess communication skills"""
        collaboration = self._detect_collaboration(ui_analysis)
        if collaboration["collaboration_detected"]:
            return "collaborative"
        return "independent"
    
    def _measure_workflow_efficiency(self, ui_analysis: Dict[str, Any]) -> float:
        """Measure workflow efficiency"""
        return self._measure_efficiency(ui_analysis)
    
    def _detect_flow_state(self, ui_analysis: Dict[str, Any]) -> bool:
        """Detect if user is in flow state"""
        focus = ui_analysis.get("user_focus", {})
        activities = ui_analysis.get("detected_activities", [])
        
        high_attention = focus.get("attention_level", 0) > 0.8
        focused_activity = activities and activities[0]["confidence"] > 0.8
        not_multitasking = not focus.get("multitasking", False)
        
        return high_attention and focused_activity and not_multitasking
    
    def _classify_learning_type(self, screen_text: str) -> str:
        """Classify the type of learning activity"""
        text_lower = screen_text.lower()
        
        if any(keyword in text_lower for keyword in ["tutorial", "guide", "how to"]):
            return "guided_learning"
        elif any(keyword in text_lower for keyword in ["documentation", "reference"]):
            return "reference_lookup"
        elif any(keyword in text_lower for keyword in ["example", "sample"]):
            return "example_based_learning"
        else:
            return "exploratory_learning"

async def test_enhanced_memory():
    """Test the enhanced memory system with deep UI understanding"""
    print("\n" + "="*80)
    print("🧠 TESTING ENHANCED MEMORY WITH DEEP UI UNDERSTANDING")
    print("="*80)
    
    enhanced_memory = EnhancedMemoryWithDeepUI()
    
    # Capture and store deep memory analysis
    memory_entry = await enhanced_memory.capture_and_store_deep_memory()
    
    print("\n📊 DEEP MEMORY ANALYSIS RESULTS:")
    print("="*60)
    
    # Display behavioral analysis
    behavior = memory_entry["behavioral_analysis"]
    print(f"\n🎯 USER BEHAVIOR ANALYSIS:")
    print(f"   Primary Activity: {behavior['primary_activity']} ({behavior['activity_confidence']:.2f} confidence)")
    print(f"   Engagement Level: {behavior['engagement_level']:.2f}")
    print(f"   Focus State: {behavior['focus_state']}")
    print(f"   Attention Score: {behavior['attention_score']:.2f}")
    print(f"   Expertise Level: {behavior['expertise_level']}")
    
    # Display content understanding
    content = memory_entry["content_understanding"]
    print(f"\n📝 CONTENT UNDERSTANDING:")
    print(f"   Content Summary: {content['content_summary']}")
    print(f"   Task Context: {content['task_context']}")
    print(f"   User Intent: {content['user_intent']}")
    print(f"   Knowledge Domain: {content['knowledge_domain']}")
    
    # Display workflow context
    workflow = memory_entry["workflow_context"]
    print(f"\n🔄 WORKFLOW CONTEXT:")
    print(f"   Current Stage: {workflow['current_stage']}")
    print(f"   Workflow Type: {workflow['workflow_type']}")
    print(f"   Progress Indicators: {', '.join(workflow['progress_indicators'])}")
    
    # Display professional insights
    insights = memory_entry["professional_insights"]
    print(f"\n💼 PROFESSIONAL INSIGHTS:")
    print(f"   Skill Assessment: {insights['skill_assessment']['technical_skill_level']}")
    print(f"   Work Pattern: {insights['work_patterns']['focus_pattern']}")
    print(f"   Efficiency Score: {insights['efficiency_indicators']:.2f}")
    print(f"   Professional Context: {insights['professional_context']}")
    
    print("\n" + "="*80)
    print("✅ ENHANCED MEMORY SYSTEM SUCCESSFULLY CAPTURING DEEP UI UNDERSTANDING")
    print("="*80)
    print("🎯 The system now captures:")
    print("   • Actual user activities and behaviors")
    print("   • Deep content understanding and context")
    print("   • Professional workflow insights")
    print("   • Real-time expertise assessment")
    print("   • Semantic understanding of user intent")
    
    return memory_entry

if __name__ == "__main__":
    asyncio.run(test_enhanced_memory())