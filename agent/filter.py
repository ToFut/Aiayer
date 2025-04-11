"""
Data Security Filter Module
Checks content for sensitive patterns and sanitizes data as needed.
"""
import re
import os
import logging


class DataFilter:
    """
    Checks and sanitizes text data for sensitive information.
    Uses regex patterns to detect PII, credentials, and other sensitive content.
    """
    
    def __init__(self, patterns_path=None):
        """
        Initialize the data filter.
        
        Args:
            patterns_path (str): Path to file containing regex patterns for sensitive data
        """
        self.patterns = []
        self.logger = logging.getLogger(__name__)
        
        # Load patterns from file or use defaults
        if patterns_path and os.path.exists(patterns_path):
            self._load_patterns_from_file(patterns_path)
        else:
            self._load_default_patterns()
            
        self.logger.info(f"Data filter initialized with {len(self.patterns)} patterns")
    
    def _load_patterns_from_file(self, file_path):
        """Load sensitive data patterns from a file."""
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Try to compile as regex, fall back to literal
                    try:
                        pattern = re.compile(line, flags=re.IGNORECASE)
                        self.patterns.append((pattern, line))
                    except re.error:
                        # If not a valid regex, escape it and treat as literal
                        escaped = re.escape(line)
                        pattern = re.compile(escaped, flags=re.IGNORECASE)
                        self.patterns.append((pattern, f"LITERAL:{line}"))
            
            self.logger.info(f"Loaded {len(self.patterns)} patterns from {file_path}")
        except Exception as e:
            self.logger.error(f"Error loading patterns from {file_path}: {e}")
            # Fall back to defaults on error
            self._load_default_patterns()
    
    def _load_default_patterns(self):
        """Load default sensitive data detection patterns."""
        default_patterns = [
            # PII
            (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "EMAIL"),
            (r"\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b", "SSN"),
            (r"\b(?:\d[ -]?){13,16}\b", "POSSIBLE_CREDIT_CARD"),
            
            # Credentials and secrets
            (r"password\s*[:=]\s*\S+", "PASSWORD_ASSIGNMENT"),
            (r"api[-_]?key\s*[:=]\s*\S+", "API_KEY"),
            (r"secret\s*[:=]\s*\S+", "SECRET"),
            (r"token\s*[:=]\s*\S+", "TOKEN"),
            (r"auth\s*[:=]\s*\S+", "AUTH"),
            
            # Common sensitive terms (broader matches)
            (r"\bpassword\b", "PASSWORD_TERM"),
            (r"\bsecret\b", "SECRET_TERM"),
            (r"\bprivate\b", "PRIVATE_TERM"),
            (r"\bconfidential\b", "CONFIDENTIAL_TERM"),
            
            # File paths that might contain sensitive info
            (r"\.env\b", "DOTENV_FILE"),
            (r"\.pem\b", "PEM_FILE"),
            (r"id_rsa\b", "SSH_KEY"),
        ]
        
        for regex, name in default_patterns:
            try:
                pattern = re.compile(regex, flags=re.IGNORECASE)
                self.patterns.append((pattern, name))
            except re.error:
                self.logger.error(f"Error compiling default pattern {name}: {regex}")
    
    def contains_sensitive_data(self, text):
        """
        Check if text contains sensitive information.
        
        Args:
            text (str): Text to check for sensitive data
            
        Returns:
            bool: True if sensitive data found, False otherwise
        """
        if not text:
            return False
        
        for pattern, name in self.patterns:
            if pattern.search(text):
                self.logger.warning(f"Sensitive data found: {name}")
                return True
        
        return False
    
    def sanitize(self, text, mask="***"):
        """
        Replace sensitive data in text with a mask.
        
        Args:
            text (str): Text to sanitize
            mask (str): String to replace sensitive data with
            
        Returns:
            str: Sanitized text
        """
        if not text:
            return text
        
        result = text
        found_patterns = []
        
        for pattern, name in self.patterns:
            matches = list(pattern.finditer(result))
            if matches:
                found_patterns.append(name)
                # Replace each match with the mask
                # Working backwards to not mess up string indices
                for match in reversed(matches):
                    start, end = match.span()
                    result = result[:start] + mask + result[end:]
        
        if found_patterns:
            self.logger.info(f"Sanitized {len(found_patterns)} types of sensitive data: {', '.join(found_patterns)}")
        
        return result
    
    def categorize_sensitive_data(self, text):
        """
        Identify types of sensitive data present in text.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            list: Names of sensitive data types found
        """
        if not text:
            return []
        
        found_categories = []
        
        for pattern, name in self.patterns:
            if pattern.search(text):
                found_categories.append(name)
        
        return found_categories


# For testing if run directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test with default patterns
    filter = DataFilter()
    
    # Test texts
    test_texts = [
        "This is a normal message with no sensitive data.",
        "My email is user@example.com",
        "The password is secure123",
        "API_KEY = as98d7foas9df87aosdf",
        "Social security number: 123-45-6789",
        "My credit card is 1234-5678-9012-3456",
        "This contains the word confidential but no actual credentials"
    ]
    
    for text in test_texts:
        contains = filter.contains_sensitive_data(text)
        sanitized = filter.sanitize(text)
        categories = filter.categorize_sensitive_data(text)
        
        print(f"\nOriginal: {text}")
        print(f"Contains sensitive data: {contains}")
        print(f"Categories: {categories}")
        print(f"Sanitized: {sanitized}")