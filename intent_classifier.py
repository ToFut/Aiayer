#!/usr/bin/env python3
"""
Intent Classifier - Determines if user wants automation or just information
Prevents unnecessary automation plan creation for simple queries
"""

import re
import logging
from typing import Dict, Any, Tuple, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class Intent(Enum):
    """User intent types"""
    AUTOMATION_REQUEST = "automation_request"  # User wants something automated
    INFORMATION_REQUEST = "information_request"  # User wants information/search results
    SUGGESTION_REQUEST = "suggestion_request"  # User wants suggestions
    UNKNOWN = "unknown"

@dataclass
class IntentResult:
    """Result of intent classification"""
    intent: Intent
    confidence: float
    reasoning: str
    should_automate: bool
    suggested_mode: str  # Agent, Ask, Suggest
    keywords_found: List[str]

class IntentClassifier:
    """Classifies user intent to determine appropriate response type"""
    
    def __init__(self):
        # Keywords that indicate automation requests
        self.automation_keywords = {
            'action_verbs': [
                'open', 'launch', 'start', 'run', 'execute', 'perform', 'do',
                'click', 'press', 'tap', 'select', 'choose', 'navigate',
                'go to', 'visit', 'browse', 'download', 'install', 'create',
                'make', 'build', 'setup', 'configure', 'send', 'email',
                'message', 'call', 'dial', 'book', 'schedule', 'order',
                'buy', 'purchase', 'add to cart', 'checkout', 'pay',
                'upload', 'save', 'copy', 'paste', 'delete', 'move',
                'automate', 'script', 'batch process'
            ],
            'automation_phrases': [
                'help me', 'can you', 'please', 'i want to', 'i need to',
                'do this for me', 'automate this', 'set up', 'take me to',
                'navigate to', 'go ahead and', 'please open', 'please click',
                'fill out', 'complete this', 'handle this', 'take care of'
            ],
            'system_actions': [
                'open app', 'launch application', 'start program', 'run software',
                'open browser', 'open website', 'navigate to', 'visit site',
                'click button', 'press key', 'type text', 'enter data',
                'scroll down', 'scroll up', 'swipe', 'drag', 'drop'
            ]
        }
        
        # Keywords that indicate information requests
        self.information_keywords = {
            'question_words': [
                'what', 'where', 'when', 'why', 'how', 'who', 'which',
                'tell me', 'show me', 'explain', 'describe', 'define'
            ],
            'search_intent': [
                'search for', 'find', 'look up', 'look for', 'research',
                'information about', 'details about', 'learn about',
                'discover', 'explore', 'investigate', 'check out'
            ],
            'passive_verbs': [
                'see', 'view', 'watch', 'read', 'listen', 'hear',
                'check', 'verify', 'confirm', 'review', 'examine'
            ]
        }
        
        # Suggestion request keywords
        self.suggestion_keywords = {
            'suggestion_requests': [
                'suggest', 'recommend', 'advice', 'ideas', 'options',
                'alternatives', 'what should', 'what would you',
                'best way', 'better approach', 'improve', 'optimize'
            ]
        }
        
        # Patterns that typically indicate search/information requests
        self.search_patterns = [
            r'^search\s+.*',  # "search something"
            r'^find\s+.*',    # "find something"
            r'^look\s+up\s+.*',  # "look up something"
            r'^what\s+is\s+.*',  # "what is something"
            r'^who\s+is\s+.*',   # "who is someone"
            r'^where\s+is\s+.*', # "where is something"
            r'^how\s+to\s+.*',   # "how to do something" (could be either)
            r'.*\?$',            # Questions ending with ?
        ]
        
        # Patterns that indicate automation requests
        self.automation_patterns = [
            r'^(open|launch|start)\s+.*',  # "open/launch/start something"
            r'^(go|navigate)\s+to\s+.*',   # "go to/navigate to somewhere"
            r'^(click|press|tap)\s+.*',    # "click/press/tap something"
            r'^(help\s+me|can\s+you)\s+.*', # "help me/can you do something"
            r'^(please|kindly)\s+.*',      # Polite requests
            r'.*\s+(for\s+me|automatically).*', # "do X for me" or "automatically"
        ]

    def classify_intent(self, query: str) -> IntentResult:
        """Classify user intent from query text"""
        try:
            query_lower = query.lower().strip()
            
            # Initialize scoring
            automation_score = 0.0
            information_score = 0.0
            suggestion_score = 0.0
            keywords_found = []
            
            # Check for pattern matches
            automation_patterns_matched = sum(1 for pattern in self.automation_patterns 
                                            if re.match(pattern, query_lower))
            search_patterns_matched = sum(1 for pattern in self.search_patterns 
                                        if re.match(pattern, query_lower))
            
            # Pattern-based scoring
            automation_score += automation_patterns_matched * 0.3
            information_score += search_patterns_matched * 0.3
            
            # Keyword-based scoring
            for category, keywords in self.automation_keywords.items():
                for keyword in keywords:
                    if keyword in query_lower:
                        automation_score += 0.1
                        keywords_found.append(f"automation:{keyword}")
            
            for category, keywords in self.information_keywords.items():
                for keyword in keywords:
                    if keyword in query_lower:
                        information_score += 0.1
                        keywords_found.append(f"information:{keyword}")
            
            for category, keywords in self.suggestion_keywords.items():
                for keyword in keywords:
                    if keyword in query_lower:
                        suggestion_score += 0.15
                        keywords_found.append(f"suggestion:{keyword}")
            
            # Special cases for common misclassifications
            # "search X" is almost always information, not automation
            if re.match(r'^search\s+.*', query_lower):
                information_score += 0.4
                automation_score = max(0, automation_score - 0.2)
                keywords_found.append("special:search_query")
            
            # Questions are usually information requests
            if query.strip().endswith('?'):
                information_score += 0.2
                keywords_found.append("special:question_mark")
            
            # "find X" without action words is usually information
            if re.match(r'^(find|look\s+for)\s+.*', query_lower) and not any(
                word in query_lower for word in ['and open', 'and click', 'and navigate']
            ):
                information_score += 0.3
                keywords_found.append("special:find_without_action")
            
            # Determine intent
            max_score = max(automation_score, information_score, suggestion_score)
            
            if max_score < 0.1:
                intent = Intent.UNKNOWN
                confidence = 0.3
                should_automate = False
                suggested_mode = "Ask"
                reasoning = "No clear intent indicators found"
            elif automation_score == max_score:
                intent = Intent.AUTOMATION_REQUEST
                confidence = min(0.95, automation_score)
                should_automate = True
                suggested_mode = "Agent"
                reasoning = f"Automation indicators found (score: {automation_score:.2f})"
            elif suggestion_score == max_score:
                intent = Intent.SUGGESTION_REQUEST
                confidence = min(0.95, suggestion_score)
                should_automate = False
                suggested_mode = "Suggest"
                reasoning = f"Suggestion request detected (score: {suggestion_score:.2f})"
            else:
                intent = Intent.INFORMATION_REQUEST
                confidence = min(0.95, information_score)
                should_automate = False
                suggested_mode = "Ask"
                reasoning = f"Information request detected (score: {information_score:.2f})"
            
            result = IntentResult(
                intent=intent,
                confidence=confidence,
                reasoning=reasoning,
                should_automate=should_automate,
                suggested_mode=suggested_mode,
                keywords_found=keywords_found[:10]  # Limit for brevity
            )
            
            logger.info(f"Intent classified: {intent.value} (confidence: {confidence:.2f}) for query: '{query[:50]}...'")
            return result
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return IntentResult(
                intent=Intent.UNKNOWN,
                confidence=0.1,
                reasoning=f"Classification error: {str(e)}",
                should_automate=False,
                suggested_mode="Ask",
                keywords_found=[]
            )

    def should_create_automation_plan(self, query: str) -> Tuple[bool, str]:
        """Quick check if automation plan should be created"""
        result = self.classify_intent(query)
        return result.should_automate, result.reasoning

# Global instance
intent_classifier = IntentClassifier()

def classify_user_intent(query: str) -> IntentResult:
    """Classify user intent from query text"""
    return intent_classifier.classify_intent(query)

def should_automate_query(query: str) -> Tuple[bool, str]:
    """Check if query should trigger automation planning"""
    return intent_classifier.should_create_automation_plan(query)

if __name__ == "__main__":
    # Test the classifier
    test_queries = [
        "search Spotify omer adam",
        "open Safari and go to Google",
        "what is the weather today?",
        "find information about Python",
        "help me book a flight to New York",
        "suggest some good restaurants",
        "click the login button",
        "tell me about machine learning",
        "can you please open Gmail?",
        "how to learn programming?"
    ]
    
    print("Testing Intent Classifier:")
    print("=" * 60)
    
    for query in test_queries:
        result = classify_user_intent(query)
        print(f"Query: '{query}'")
        print(f"Intent: {result.intent.value}")
        print(f"Should Automate: {result.should_automate}")
        print(f"Suggested Mode: {result.suggested_mode}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Reasoning: {result.reasoning}")
        print("-" * 40)