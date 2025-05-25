#!/usr/bin/env python3
"""
Memory Meaningfulness Fix
Addresses the key issues preventing the memory system from being meaningful
"""
import json
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryMeaningfulnessFixer:
    """Diagnoses and fixes memory meaningfulness issues"""
    
    def __init__(self):
        self.memory_path = "/Users/segevbin/Desktop/SensAI/Aiayer/memory"
        self.memory_state_file = f"{self.memory_path}/memory_state.json"
        self.issues_found = []
        self.fixes_applied = []
        
    def analyze_memory_state(self):
        """Analyze current memory state for meaningfulness issues"""
        logger.info("🔍 Analyzing memory state for meaningfulness issues...")
        
        try:
            with open(self.memory_state_file, 'r') as f:
                memory_state = json.load(f)
            
            # Issue 1: Check content quality
            self._check_content_quality(memory_state)
            
            # Issue 2: Check analysis depth
            self._check_analysis_depth(memory_state)
            
            # Issue 3: Check semantic meaning extraction
            self._check_semantic_extraction(memory_state)
            
            # Issue 4: Check UI element detection
            self._check_ui_detection(memory_state)
            
            # Issue 5: Check professional context understanding
            self._check_professional_context(memory_state)
            
            return memory_state
            
        except Exception as e:
            logger.error(f"Error analyzing memory state: {e}")
            return None
    
    def _check_content_quality(self, memory_state):
        """Check quality of stored content"""
        short_term = memory_state.get('short_term', [])
        
        low_quality_count = 0
        total_count = len(short_term)
        
        for item in short_term:
            # Check for generic/meaningless content
            if isinstance(item, dict):
                activity = item.get('user_activity', {}).get('primary_activity', '')
                app = item.get('user_activity', {}).get('application_used', '')
                context = item.get('context_analysis', {})
                
                # Flag low quality indicators
                quality_issues = []
                
                if activity == 'general':
                    quality_issues.append("generic_activity")
                
                if app in ['loginwindow', 'unknown']:
                    quality_issues.append("unidentified_app")
                
                if not context.get('meaningful_interaction', True):
                    quality_issues.append("not_meaningful")
                
                if context.get('confidence_level', 0) < 0.5:
                    quality_issues.append("low_confidence")
                
                if len(quality_issues) >= 2:
                    low_quality_count += 1
        
        if low_quality_count > total_count * 0.5:
            self.issues_found.append(f"Content Quality: {low_quality_count}/{total_count} memories have low quality")
    
    def _check_analysis_depth(self, memory_state):
        """Check depth of analysis in memories"""
        short_term = memory_state.get('short_term', [])
        
        shallow_analysis_count = 0
        
        for item in short_term:
            if item.get('memory_type') == 'comprehensive_visual_analysis':
                visual = item.get('visual_understanding', {})
                
                # Check for empty analysis components
                empty_components = []
                
                if not visual.get('ui_elements_detected', []):
                    empty_components.append("ui_elements")
                
                if not visual.get('visual_design_patterns', []):
                    empty_components.append("design_patterns")
                
                if not visual.get('interactive_components', []):
                    empty_components.append("interactive_components")
                
                if visual.get('color_scheme') == 'unknown':
                    empty_components.append("color_scheme")
                
                if len(empty_components) >= 3:
                    shallow_analysis_count += 1
        
        if shallow_analysis_count > 0:
            self.issues_found.append(f"Analysis Depth: {shallow_analysis_count} memories have shallow visual analysis")
    
    def _check_semantic_extraction(self, memory_state):
        """Check semantic meaning extraction"""
        short_term = memory_state.get('short_term', [])
        
        missing_semantics_count = 0
        
        for item in short_term:
            if 'content_analysis' in item:
                content = item['content_analysis']
                
                if not content.get('key_topics', []):
                    missing_semantics_count += 1
                elif content.get('semantic_meaning', '') == '':
                    missing_semantics_count += 1
        
        if missing_semantics_count > 0:
            self.issues_found.append(f"Semantic Extraction: {missing_semantics_count} memories lack semantic meaning")
    
    def _check_ui_detection(self, memory_state):
        """Check UI element detection quality"""
        short_term = memory_state.get('short_term', [])
        
        poor_ui_detection = 0
        
        for item in short_term:
            if 'ui_components' in item:
                ui = item['ui_components']
                
                # Check if all UI components are empty
                empty_ui_count = 0
                ui_fields = ['buttons', 'forms', 'navigation', 'data_displays', 'interactive_elements']
                
                for field in ui_fields:
                    if not ui.get(field, []):
                        empty_ui_count += 1
                
                if empty_ui_count == len(ui_fields):
                    poor_ui_detection += 1
        
        if poor_ui_detection > 0:
            self.issues_found.append(f"UI Detection: {poor_ui_detection} memories have no UI elements detected")
    
    def _check_professional_context(self, memory_state):
        """Check professional context understanding"""
        short_term = memory_state.get('short_term', [])
        
        unknown_context_count = 0
        
        for item in short_term:
            if 'professional_context' in item:
                prof = item['professional_context']
                
                unknown_fields = 0
                context_fields = ['domain', 'work_type', 'professional_level']
                
                for field in context_fields:
                    if prof.get(field) == 'unknown':
                        unknown_fields += 1
                
                if unknown_fields >= 2:
                    unknown_context_count += 1
        
        if unknown_context_count > 0:
            self.issues_found.append(f"Professional Context: {unknown_context_count} memories have unknown professional context")
    
    def apply_fixes(self, memory_state):
        """Apply fixes to improve memory meaningfulness"""
        logger.info("🔧 Applying fixes to improve memory meaningfulness...")
        
        if not memory_state:
            logger.error("No memory state to fix")
            return False
        
        try:
            # Fix 1: Enhance content analysis
            self._enhance_content_analysis(memory_state)
            
            # Fix 2: Improve semantic extraction
            self._improve_semantic_extraction(memory_state)
            
            # Fix 3: Add meaningful categorization
            self._add_meaningful_categorization(memory_state)
            
            # Fix 4: Enhance professional context detection
            self._enhance_professional_context(memory_state)
            
            # Save the enhanced memory state
            self._save_enhanced_memory(memory_state)
            
            return True
            
        except Exception as e:
            logger.error(f"Error applying fixes: {e}")
            return False
    
    def _enhance_content_analysis(self, memory_state):
        """Enhance content analysis in memory items"""
        short_term = memory_state.get('short_term', [])
        
        for item in short_term:
            if 'content_analysis' in item:
                content = item['content_analysis']
                text_content = content.get('text_content', '')
                
                if text_content and not content.get('key_topics', []):
                    # Extract key topics from text
                    topics = self._extract_topics_from_text(text_content)
                    content['key_topics'] = topics
                    
                    # Generate semantic meaning
                    if not content.get('semantic_meaning', ''):
                        meaning = self._generate_semantic_meaning(text_content, topics)
                        content['semantic_meaning'] = meaning
                    
                    self.fixes_applied.append("Enhanced content analysis with topics and semantic meaning")
    
    def _improve_semantic_extraction(self, memory_state):
        """Improve semantic meaning extraction"""
        short_term = memory_state.get('short_term', [])
        
        for item in short_term:
            # Add meaningful insights based on activity patterns
            if 'user_activity' in item:
                activity = item['user_activity']
                app = activity.get('application_used', '')
                
                # Generate meaningful insights
                insights = self._generate_activity_insights(activity, app)
                if insights:
                    if 'insights' not in item:
                        item['insights'] = []
                    item['insights'].extend(insights)
                    
                self.fixes_applied.append("Added activity-based insights for semantic understanding")
    
    def _add_meaningful_categorization(self, memory_state):
        """Add meaningful categorization to memories"""
        short_term = memory_state.get('short_term', [])
        
        for item in short_term:
            # Add productivity categorization
            if 'user_activity' in item:
                productivity_score = item['user_activity'].get('productivity_score', 0)
                
                if productivity_score > 0.7:
                    category = "highly_productive"
                elif productivity_score > 0.4:
                    category = "moderately_productive"
                else:
                    category = "low_productivity"
                
                item['productivity_category'] = category
                
                # Add workflow stage insights
                workflow_stage = item.get('context_analysis', {}).get('workflow_stage', '')
                if workflow_stage:
                    item['workflow_insights'] = self._generate_workflow_insights(workflow_stage)
                
                self.fixes_applied.append("Added meaningful categorization and workflow insights")
    
    def _enhance_professional_context(self, memory_state):
        """Enhance professional context detection"""
        short_term = memory_state.get('short_term', [])
        
        for item in short_term:
            if 'user_activity' in item:
                app = item['user_activity'].get('application_used', '')
                activity = item['user_activity'].get('primary_activity', '')
                
                # Improve professional context based on app and activity
                professional_context = self._determine_professional_context(app, activity)
                
                if professional_context and 'professional_context' in item:
                    item['professional_context'].update(professional_context)
                
                self.fixes_applied.append("Enhanced professional context detection")
    
    def _extract_topics_from_text(self, text):
        """Extract key topics from text content"""
        if not text:
            return []
        
        # Simple topic extraction based on common keywords
        topics = []
        text_lower = text.lower()
        
        # Development topics
        dev_keywords = ['code', 'debug', 'programming', 'development', 'git', 'api', 'function', 'class', 'variable']
        if any(keyword in text_lower for keyword in dev_keywords):
            topics.append('software_development')
        
        # Communication topics
        comm_keywords = ['chat', 'message', 'email', 'meeting', 'call', 'video', 'conference']
        if any(keyword in text_lower for keyword in comm_keywords):
            topics.append('communication')
        
        # Productivity topics
        prod_keywords = ['task', 'todo', 'project', 'deadline', 'schedule', 'calendar']
        if any(keyword in text_lower for keyword in prod_keywords):
            topics.append('productivity')
        
        # Research topics
        research_keywords = ['research', 'analysis', 'study', 'investigate', 'explore', 'learn']
        if any(keyword in text_lower for keyword in research_keywords):
            topics.append('research')
        
        return topics if topics else ['general']
    
    def _generate_semantic_meaning(self, text, topics):
        """Generate semantic meaning from text and topics"""
        if not text or not topics:
            return "General activity with limited context"
        
        # Create meaningful description based on content
        if 'software_development' in topics:
            return "Software development activity involving coding, debugging, or technical work"
        elif 'communication' in topics:
            return "Communication activity involving messaging, meetings, or collaboration"
        elif 'productivity' in topics:
            return "Productivity activity involving task management, planning, or organization"
        elif 'research' in topics:
            return "Research activity involving information gathering, analysis, or learning"
        else:
            return f"Activity involving {', '.join(topics)} with contextual interaction"
    
    def _generate_activity_insights(self, activity, app):
        """Generate meaningful insights from activity data"""
        insights = []
        
        # App-specific insights
        if 'cursor' in app.lower():
            insights.append("Using AI-assisted code editor - likely engaged in development work")
        elif 'terminal' in app.lower():
            insights.append("Command-line activity suggests technical workflow")
        elif 'browser' in app.lower():
            insights.append("Web browsing activity - research or web development")
        
        # Productivity insights
        productivity = activity.get('productivity_score', 0)
        if productivity > 0.8:
            insights.append("High productivity period with focused engagement")
        elif productivity < 0.3:
            insights.append("Low activity period - possibly idle or background tasks")
        
        return insights
    
    def _generate_workflow_insights(self, workflow_stage):
        """Generate insights based on workflow stage"""
        insights = {
            'active_coding': "Currently engaged in active development work",
            'refinement': "In refinement phase - improving or polishing work",
            'research': "In research/learning phase - gathering information",
            'planning': "In planning phase - organizing and strategizing",
            'testing': "In testing phase - validating functionality",
            'debugging': "In debugging phase - identifying and fixing issues"
        }
        
        return insights.get(workflow_stage, f"In {workflow_stage} workflow stage")
    
    def _determine_professional_context(self, app, activity):
        """Determine professional context from app and activity"""
        context = {}
        
        # Domain detection
        if any(keyword in app.lower() for keyword in ['cursor', 'vscode', 'intellij', 'terminal']):
            context['domain'] = 'software_engineering'
            context['work_type'] = 'development'
            context['professional_level'] = 'experienced'
        elif any(keyword in app.lower() for keyword in ['photoshop', 'illustrator', 'figma', 'sketch']):
            context['domain'] = 'design'
            context['work_type'] = 'creative'
            context['professional_level'] = 'skilled'
        elif any(keyword in app.lower() for keyword in ['word', 'docs', 'excel', 'sheets']):
            context['domain'] = 'office_productivity'
            context['work_type'] = 'documentation'
            context['professional_level'] = 'general'
        
        return context
    
    def _save_enhanced_memory(self, memory_state):
        """Save the enhanced memory state"""
        # Create backup
        backup_file = f"{self.memory_state_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            with open(self.memory_state_file, 'r') as f:
                original = f.read()
            with open(backup_file, 'w') as f:
                f.write(original)
            
            logger.info(f"Created backup: {backup_file}")
        except Exception as e:
            logger.warning(f"Could not create backup: {e}")
        
        # Save enhanced version
        try:
            with open(self.memory_state_file, 'w') as f:
                json.dump(memory_state, f, indent=2)
            
            logger.info("✅ Enhanced memory state saved successfully")
        except Exception as e:
            logger.error(f"Error saving enhanced memory: {e}")
            raise
    
    def run_fix(self):
        """Run the complete memory meaningfulness fix"""
        logger.info("🚀 Starting Memory Meaningfulness Fix...")
        
        # 1. Analyze current state
        memory_state = self.analyze_memory_state()
        
        if not memory_state:
            logger.error("❌ Could not analyze memory state")
            return False
        
        # 2. Report issues
        if self.issues_found:
            logger.info("❗ Issues found:")
            for issue in self.issues_found:
                logger.info(f"  - {issue}")
        else:
            logger.info("✅ No major issues found")
        
        # 3. Apply fixes
        success = self.apply_fixes(memory_state)
        
        if success:
            logger.info("✅ Fixes applied successfully:")
            for fix in self.fixes_applied:
                logger.info(f"  + {fix}")
        else:
            logger.error("❌ Failed to apply fixes")
        
        return success

def main():
    """Main entry point"""
    fixer = MemoryMeaningfulnessFixer()
    success = fixer.run_fix()
    
    if success:
        print("✅ Memory meaningfulness improved successfully!")
        print("📝 Summary:")
        print(f"  - Issues addressed: {len(fixer.issues_found)}")
        print(f"  - Fixes applied: {len(fixer.fixes_applied)}")
    else:
        print("❌ Failed to improve memory meaningfulness")
        sys.exit(1)

if __name__ == "__main__":
    main()