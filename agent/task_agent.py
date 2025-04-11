"""
Task Agent Module
Orchestrates the interaction between user queries, sensor data, and the LLM.
"""
import time
import logging
import os


class TaskAgent:
    """
    Core orchestration logic for the AI assistant.
    Gathers context from sensors, formats prompts, calls LLM, and manages memory.
    """
    
    def __init__(self, sensors, llm, memory, data_filter):
        """
        Initialize the task agent.
        
        Args:
            sensors (dict): Dictionary of sensor instances
            llm: LocalLLM instance
            memory: ConversationMemory instance
            data_filter: DataFilter instance
        """
        self.sensors = sensors
        self.llm = llm
        self.memory = memory
        self.filter = data_filter
        self.logger = logging.getLogger(__name__)
        
        # Initialize with default system prompt
        self._init_system_prompt()
    
    def _init_system_prompt(self):
        """Set the default system prompt for the assistant."""
        self.base_system_prompt = """You are a helpful AI assistant running entirely locally on the user's machine. 

Key characteristics:
1. You have access to real-time context about what the user is doing through various sensors.
2. You NEVER send any data to the cloud - everything happens locally.
3. You can see the user's screen content (via OCR), active applications, and file system activity.
4. You prioritize user privacy and security in all interactions.
5. You're designed to be helpful, accurate, and respectful of user data.

Use the provided context to better understand the user's current situation and provide more relevant assistance. If asked about your capabilities, explain that you run locally using a Mistral 7B model and can observe screen content, active apps, and file activity to provide context-aware help.

Always maintain a helpful, friendly tone while being mindful of privacy concerns."""
    
    def build_context_message(self):
        """
        Gather and format context information from all sensors.
        
        Returns:
            str: Formatted context information
        """
        context_parts = []
        
        # Screen content (truncated to avoid overwhelming the context)
        if 'screen' in self.sensors:
            text = self.sensors['screen'].latest_text.strip()
            if text:
                # Take first 300 chars and truncate to the nearest sentence end
                short_text = text[:300]
                end_markers = ['. ', '! ', '? ', '\n\n']
                for marker in end_markers:
                    pos = short_text.rfind(marker)
                    if pos > 150:  # Ensure we have a reasonable amount of text
                        short_text = short_text[:pos+1]
                        break
                
                context_parts.append(f"Screen Text: \"{short_text}\"")
        
        # Active application and window title
        if 'process' in self.sensors:
            app = self.sensors['process'].active_app
            title = self.sensors['process'].active_window_title
            if app:
                app_info = f"Active Application: {app}"
                if title:
                    app_info += f" (Window: \"{title}\")"
                context_parts.append(app_info)
            
            # Include a few running applications
            running_apps = list(self.sensors['process'].running_apps)[:5]  # Limit to 5
            if running_apps:
                context_parts.append(f"Running Apps: {', '.join(running_apps)}")
        
        # Recent file events
        if 'file' in self.sensors:
            events = self.sensors['file'].get_recent_events(count=3, format_str=True)
            if events:
                context_parts.append(f"Recent File Activity: {' | '.join(events)}")
        
        # Browser info if available
        if 'browser' in self.sensors:
            url = self.sensors['browser'].current_url
            title = self.sensors['browser'].current_title
            if url:
                browser_info = f"Current Browser URL: {url}"
                if title:
                    browser_info += f" (Title: \"{title}\")"
                context_parts.append(browser_info)
        
        # Join all context parts with line breaks for better formatting
        return "\n".join(context_parts)
    
    def handle_query(self, user_query):
        """
        Process a user query and generate a response.
        Gathers context, calls LLM, filters output, and manages memory.
        
        Args:
            user_query (str): User's question or command
            
        Returns:
            str: Assistant's response
        """
        start_time = time.time()
        self.logger.info(f"Processing query: {user_query[:50]}...")
        
        # Check if user query contains sensitive data (just as a precaution)
        contains_sensitive = self.filter.contains_sensitive_data(user_query)
        if contains_sensitive:
            self.logger.warning("User query contains potentially sensitive information")
        
        # 1. Build context from sensors
        context_info = self.build_context_message()
        
        # 2. Build the prompt with system message, context, and query
        system_prompt = self.base_system_prompt
        if context_info:
            system_prompt += "\n\nCurrent context:\n" + context_info
        
        # 3. Assemble conversation messages
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # 4. Include relevant conversation history
        history = self.memory.get_recent(count=10)  # Get last 10 messages
        if history:
            messages.extend(history)
        
        # 5. Add the user's current query
        messages.append({"role": "user", "content": user_query})
        
        # 6. Generate response using LLM
        self.logger.info("Calling LLM for response")
        raw_response = self.llm.generate_response(messages)
        
        # 7. Filter the response for sensitive content
        sensitive_in_response = self.filter.contains_sensitive_data(raw_response)
        if sensitive_in_response:
            self.logger.warning("LLM response contains potentially sensitive information")
            # Sanitize response instead of blocking it completely
            sanitized_response = self.filter.sanitize(raw_response)
            
            # Add a warning note at the beginning
            final_response = ("Note: Some potentially sensitive information in the response " 
                             "has been redacted for security.\n\n" + sanitized_response)
        else:
            final_response = raw_response
        
        # 8. Save to conversation memory
        self.memory.add_message({"role": "user", "content": user_query})
        self.memory.add_message({"role": "assistant", "content": final_response})
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Query processed in {elapsed_time:.2f}s")
        
        return final_response
    
    def query_with_file_context(self, user_query, file_path):
        """
        Enhanced query handling with file content as context.
        Useful when user explicitly asks about a file.
        
        Args:
            user_query (str): User's question
            file_path (str): Path to file to use as context
            
        Returns:
            str: Assistant's response
        """
        # Check if file exists
        if not os.path.exists(file_path):
            return f"I couldn't find the file at {file_path}."
        
        # Read file content (with size limits)
        try:
            max_file_size = 100 * 1024  # 100KB limit for now
            if os.path.getsize(file_path) > max_file_size:
                return f"The file {file_path} is too large to analyze in full. Please specify a smaller file or a specific section."
            
            with open(file_path, 'r', errors='ignore') as f:
                file_content = f.read()
            
            # Truncate if still too large
            if len(file_content) > 5000:
                file_content = file_content[:5000] + "\n[... file truncated due to length ...]"
            
            # Check for sensitive data in file
            if self.filter.contains_sensitive_data(file_content):
                self.logger.warning(f"File {file_path} contains sensitive data")
                return f"The file {file_path} appears to contain sensitive information. I've avoided loading it to protect your privacy."
            
            # Create a modified context with file content
            modified_query = f"I'm asking about this file: {file_path}\n\nFile content:\n{file_content}\n\nMy question: {user_query}"
            
            # Use regular query handler but with enhanced context
            return self.handle_query(modified_query)
            
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return f"I encountered an error while trying to read {file_path}: {str(e)}"
    
    def perform_action(self, action_type, **params):
        """
        Handle actions requested by the user (placeholder).
        Can be extended to perform system actions, with appropriate safeguards.
        
        Args:
            action_type (str): Type of action to perform
            **params: Parameters for the action
            
        Returns:
            str: Result message
        """
        # This is a placeholder for future extensions
        # In a real implementation, we would add support for actions like:
        # - Opening files or applications
        # - Setting reminders
        # - Controlling system settings
        # Each with appropriate safeguards and confirmations
        
        self.logger.warning(f"Action requested but not implemented: {action_type}")
        return "I understand you want me to perform an action, but I'm currently limited to answering questions based on what I can observe. I can't directly interact with your system yet."


# For testing if run directly
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Mock sensor data for testing
    class MockSensor:
        def __init__(self, name):
            self.name = name
            self.latest_text = f"Test content for {name} sensor"
            self.active_app = "TestApp"
            self.active_window_title = "Test Window"
            self.running_apps = ["TestApp", "Browser", "Editor"]
            self.recent_events = []
            self.current_url = "http://example.com"
            self.current_title = "Example Website"
        
        def get_recent_events(self, count=3, format_str=True):
            return ["12:34:56: modified test.txt", "12:35:01: created newfile.py"]
    
    mock_sensors = {
        "screen": MockSensor("screen"),
        "process": MockSensor("process"),
        "file": MockSensor("file"),
        "browser": MockSensor("browser")
    }
    
    # Mock other components
    class MockLLM:
        def generate_response(self, messages):
            return "This is a mock response from the LLM based on your query."
    
    from memory.memory import ConversationMemory
    from agent.filter import DataFilter
    
    # Create a test agent
    memory = ConversationMemory()
    filter = DataFilter()
    agent = TaskAgent(mock_sensors, MockLLM(), memory, filter)
    
    # Test a query
    test_query = "What am I working on right now?"
    print(f"\nTest query: {test_query}")
    response = agent.handle_query(test_query)
    print(f"\nResponse: {response}")
    
    # Show the context being generated
    print("\nContext generated:")
    print(agent.build_context_message())