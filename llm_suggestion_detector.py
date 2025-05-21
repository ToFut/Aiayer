#!/usr/bin/env python3
"""
LLM Suggestion Detector
Analyzes LLM responses to identify suggestions and format them properly.
"""
import re
import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

class SuggestionDetector:
    """Detects and formats suggestions in LLM responses."""
    
    SUGGESTION_MARKERS = [
        r"(?i)would you like (?:me|us) to",
        r"(?i)i(?:'d| would) suggest",
        r"(?i)i notice(?:d)? (?:that|you)",
        r"(?i)(?:it appears|it seems)",
        r"(?i)may i (?:suggest|recommend)",
        r"(?i)(?:you (?:might|could|should) consider)",
        r"(?i)have you (?:thought|considered) about",
        r"(?i)(?:one|another) option (?:is|would be)",
        r"(?i)(?:a|some) suggestion(?:s)?",
        r"(?i)perhaps you (?:could|should|might want to)",
        r"(?i)(?:i recommend|i can help you|i could assist)",
        r"(?i)allow me to (?:suggest|recommend|offer)",
        r"(?i)tip:",
        r"(?i)suggestion:",
        r"(?i)recommendation:",
    ]
    
    IGNORE_CONTEXTS = [
        r"(?i)(?:in|the|this) suggestion",
        r"(?i)many suggestions",
        r"(?i)earlier suggestion",
        r"(?i)previous suggestion",
    ]
    
    # Question pattern detection to filter out direct responses
    DIRECT_QUESTION_RESPONSES = [
        r"(?i)^(?:yes|no)(?:,|\.)",
        r"(?i)^to answer your question",
        r"(?i)^you asked about",
    ]
    
    def __init__(self, confidence_threshold: float = 0.7):
        """
        Initialize the suggestion detector.
        
        Args:
            confidence_threshold: Minimum confidence to classify text as a suggestion
        """
        self.confidence_threshold = confidence_threshold
    
    def detect_suggestion(self, text: str) -> Tuple[bool, float, Optional[Dict]]:
        """
        Detect if text contains a suggestion.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (is_suggestion, confidence, suggestion_data)
        """
        # Skip if too short
        if len(text) < 20:
            return False, 0.0, None
            
        # Skip direct question responses
        for pattern in self.DIRECT_QUESTION_RESPONSES:
            if re.search(pattern, text):
                return False, 0.0, None
                
        # Calculate suggestion score based on markers
        score = 0.0
        matches = []
        
        # Look for suggestion markers
        for pattern in self.SUGGESTION_MARKERS:
            match = re.search(pattern, text)
            if match:
                # Get context around match
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end]
                
                # Check if in an ignore context
                ignore = False
                for ignore_pattern in self.IGNORE_CONTEXTS:
                    if re.search(ignore_pattern, context):
                        ignore = True
                        break
                
                if not ignore:
                    score += 0.25  # Add to score
                    matches.append({
                        'pattern': pattern,
                        'match': match.group(0),
                        'position': match.start(),
                        'context': context
                    })
                        
        # Look for question marks or calls to action
        if "?" in text:
            score += 0.2
            
        # Additional indicators of proactive suggestions
        if re.search(r"(?i)(?:do you want|would you like)", text):
            score += 0.15
            
        # Cap the score at 0.95 for certainty
        score = min(0.95, score)
        
        # Structure the suggestion if we're confident enough
        if score >= self.confidence_threshold:
            # Extract the primary suggestion text - typically a single sentence
            sentences = re.split(r'(?<=[.!?])\s+', text)
            
            # Find the sentence with the highest suggestion marker density
            best_sentence = text
            best_score = 0
            
            for sentence in sentences:
                if len(sentence) < 10:  # Skip very short sentences
                    continue
                
                sentence_score = 0
                for pattern in self.SUGGESTION_MARKERS:
                    if re.search(pattern, sentence):
                        sentence_score += 1
                
                if sentence_score > best_score:
                    best_score = sentence_score
                    best_sentence = sentence
            
            # If we couldn't find a specific sentence, use the first 100 chars
            if best_score == 0 and len(text) > 100:
                best_sentence = text[:100] + "..."
                
            # Extract a call to action if possible
            action_match = re.search(r"(?i)(?:would you like to|do you want to|should I) ([^.?!]+)", text)
            action = action_match.group(1).strip() if action_match else None
                
            suggestion_data = {
                'content': text,
                'title': best_sentence.strip(),
                'action': action,
                'confidence': score,
                'isSuggestion': True,
                'buttons': [
                    {'id': 'do', 'label': 'Yes', 'primary': True},
                    {'id': 'adjust', 'label': 'Adjust', 'primary': False},
                    {'id': 'dismiss', 'label': 'No', 'primary': False}
                ]
            }
            
            return True, score, suggestion_data
        
        return False, score, None
    
    def format_as_suggestion(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Format text as a suggestion if it contains suggestion markers.
        
        Args:
            text: Text to analyze and format
            
        Returns:
            Formatted suggestion or None if not a suggestion
        """
        is_suggestion, confidence, suggestion_data = self.detect_suggestion(text)
        
        if is_suggestion:
            logger.info(f"Detected suggestion with confidence {confidence:.2f}")
            return suggestion_data
            
        return None
        
    def process_llm_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an LLM response and detect/format suggestions.
        
        Args:
            response_data: LLM response data
            
        Returns:
            Processed response data, potentially converted to suggestion
        """
        # Extract the text content from the response
        content = None
        
        if 'content' in response_data:
            content = response_data['content']
        elif 'payload' in response_data:
            if isinstance(response_data['payload'], dict):
                content = response_data['payload'].get('response') or response_data['payload'].get('message')
            elif isinstance(response_data['payload'], str):
                content = response_data['payload']
        elif 'message' in response_data:
            content = response_data['message']
        elif 'response' in response_data:
            content = response_data['response']
        
        if not content:
            logger.warning("Could not extract content from response")
            return response_data
            
        # Detect if this is a suggestion
        is_suggestion, confidence, suggestion_data = self.detect_suggestion(content)
        
        if is_suggestion:
            logger.info(f"Converting response to suggestion with confidence {confidence:.2f}")
            
            # Create a new suggestion message
            suggestion_message = {
                "type": "suggestion",
                "content": content,
                "isSuggestion": True
            }
            
            # Add additional suggestion metadata if available
            if suggestion_data:
                for key, value in suggestion_data.items():
                    if key != 'content':  # Avoid duplicate content
                        suggestion_message[key] = value
            
            return suggestion_message
            
        # If not a suggestion, return the original response
        return response_data

# Helper function to intercept and process WebSocket messages
async def process_ws_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a WebSocket message, detecting and formatting suggestions.
    
    Args:
        message: The message data
        
    Returns:
        Processed message data
    """
    # Skip processing for non-LLM responses
    if message.get('type') not in ['llm_response', 'query_response']:
        return message
        
    # Process with suggestion detector
    detector = SuggestionDetector()
    return detector.process_llm_response(message)

# Test function
def test_detector():
    """Test the suggestion detector with various examples."""
    detector = SuggestionDetector()
    
    test_cases = [
        # Strong suggestions
        "I notice you're working with WebSocket code. Would you like me to help optimize the connection handling?",
        "Based on your recent activity, I'd suggest adding error logging to this function.",
        "It seems your code has some performance issues. May I recommend using async/await for these operations?",
        
        # Weak or non-suggestions
        "The WebSocket protocol uses a handshake mechanism to establish connections.",
        "To answer your question, WebSockets maintain persistent connections between clients and servers.",
        "Yes, the function you mentioned contains suggestion detection logic."
    ]
    
    for i, text in enumerate(test_cases):
        is_suggestion, confidence, data = detector.detect_suggestion(text)
        print(f"Test {i+1}: {'SUGGESTION' if is_suggestion else 'NOT SUGGESTION'} ({confidence:.2f})")
        print(f"Text: {text}")
        if is_suggestion:
            print(f"Title: {data.get('title')}")
        print()

if __name__ == "__main__":
    test_detector()