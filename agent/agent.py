def process_query(self, query: str, timeout: int = 30) -> str:
    """Process a user query and return a response."""
    try:
        # Validate input
        if not query or not isinstance(query, str):
            return "*(Please provide a valid query)*"
        
        # Check if LLM is available
        if not self.llm:
            return "*(Error: Language model not available)*"
        
        # Prepare the conversation
        conversation = self.memory.get_conversation()
        conversation.append({"role": "user", "content": query})
        
        # Generate response with timeout
        try:
            response = self.llm.generate_response(conversation, timeout=timeout)
            
            # Validate response
            if not response or not isinstance(response, str):
                return "*(Error: Invalid response from language model)*"
            
            # Update memory
            conversation.append({"role": "assistant", "content": response})
            self.memory.update_conversation(conversation)
            
            return response
            
        except TimeoutError:
            return "*(Error: Request timed out. Please try again.)*"
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "*(Error: Could not generate response. Please try again.)*"
            
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return "*(Error: Could not process query. Please try again.)*" 