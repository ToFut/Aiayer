#!/usr/bin/env python3
"""
Fix LLM Model NDJSON Handling
This script applies fixes to the LLM model.py to properly handle NDJSON responses.
"""

import os
import sys
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/fix_llm_model.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_model_py_path():
    """Get the path to the model.py file"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    model_py_path = os.path.join(base_dir, 'llm', 'model.py')
    
    if not os.path.exists(model_py_path):
        logger.error(f"❌ Could not find model.py at {model_py_path}")
        return None
    
    return model_py_path

def backup_file(file_path):
    """Create a backup of the file"""
    backup_path = f"{file_path}.bak.fix"
    try:
        with open(file_path, 'r') as src:
            with open(backup_path, 'w') as dst:
                dst.write(src.read())
        logger.info(f"✅ Created backup at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create backup: {e}")
        return False

def fix_model_py(file_path):
    """Apply fixes to model.py to ensure proper NDJSON handling"""
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Count occurrences of ContentTypeError in file (will be useful for diagnosing)
        contenttype_error_count = content.count('ContentTypeError')
        logger.info(f"Found {contenttype_error_count} occurrences of ContentTypeError in the file")
        
        # Fix 1: Improve content type checking and streaming response handling
        # Find the problematic section in generate_response method
        pattern = r"if 'application/x-ndjson' in content_type:[\s\n]+(.*?)(# For regular JSON response)"
        replacement = r"""if 'application/x-ndjson' in content_type or stream:
                                # FIXED: Always handle streaming responses properly, regardless of content type
                                text = await response.text()
                                
                                # Get the last non-empty line for final response
                                lines = [line for line in text.split('\\n') if line.strip()]
                                if not lines:
                                    self.logger.error("Empty NDJSON response")
                                    return "Error: Received empty response from LLM service"
                                
                                # For streaming response, we need to concatenate all the content parts
                                full_response = ""
                                for line in lines:
                                    try:
                                        data = json.loads(line)
                                        if 'message' in data and 'content' in data['message']:
                                            full_response += data['message']['content']
                                    except json.JSONDecodeError as e:
                                        self.logger.warning(f"Failed to parse JSON line: {e}")
                                        continue
                                
                                self.logger.info(f"Ollama response time: {time.time() - start_time:.2f}s (status: {response.status})")
                                return full_response\n                                \n                            $2"""
        
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Fix 2: Improve regular JSON response handling with better fallbacks
        pattern2 = r"# For regular JSON response(?:.*?)try:\s+data = await response\.json\(\)(.*?)except Exception as e:"
        replacement2 = r"""# For regular JSON response - First try to handle it directly as text for Ollama 0.6.8+ compatibility
                                try:
                                    text = await response.text()
                                    # Check if it's NDJSON despite the content type header
                                    if '\n' in text and text.strip().startswith('{'):
                                        # Treat as NDJSON stream
                                        lines = [line for line in text.split('\n') if line.strip()]
                                        if not lines:
                                            self.logger.error("Empty text response")
                                            return "Error: Received empty response from LLM service"
                                        
                                        # Try to parse as NDJSON
                                        full_response = ""
                                        for line in lines:
                                            try:
                                                data = json.loads(line)
                                                if 'message' in data and 'content' in data['message']:
                                                    full_response += data['message']['content']
                                            except json.JSONDecodeError:
                                                # If it's not JSON, just add the text
                                                continue
                                        
                                        if full_response:
                                            self.logger.info(f"Parsed NDJSON response: {len(full_response)} chars")
                                            return full_response
                                        
                                    # Try to parse as a single JSON object
                                    try:
                                        data = json.loads(text)
                                        if isinstance(data, dict):
                                            if 'message' in data and 'content' in data['message']:
                                                result = data['message']['content']
                                                self.logger.info(f"Successfully parsed response ({len(result)} chars)")
                                                return result
                                            elif 'response' in data:  # Fallback for older Ollama API versions
                                                result = data['response']
                                                self.logger.info(f"Successfully parsed response using fallback format ({len(result)} chars)")
                                                return result
                                            else:
                                                # Just return the text as is
                                                self.logger.info(f"Returning raw response text ({len(text)} chars)")
                                                return text
                                        else:
                                            # Just return the text as is
                                            self.logger.info(f"Returning raw response text ({len(text)} chars)")
                                            return text
                                    except json.JSONDecodeError:
                                        # If it's not JSON, just return the text
                                        self.logger.info(f"Returning non-JSON response text ({len(text)} chars)")
                                        return text
                                            
                                except Exception as e:"""
        
        updated_content = re.sub(pattern2, replacement2, updated_content, flags=re.DOTALL)
        
        # Fix 3: Increase the timeout value for LLM requests
        pattern3 = r"self\.timeout = \d+"  # Match current timeout value
        replacement3 = "self.timeout = 45  # Increased timeout for llama3.2:1b to handle long queries"
        
        updated_content = re.sub(pattern3, replacement3, updated_content)
        
        # Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.write(updated_content)
        
        logger.info(f"✅ Successfully updated {file_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to fix model.py: {e}")
        return False

def fix_backend_for_llm_responses(backend_file_path):
    """Fix the enhanced_enterprise_backend_with_context.py to ensure LLM responses are sent"""
    try:
        # Check if file exists
        if not os.path.exists(backend_file_path):
            logger.error(f"❌ Could not find backend file at {backend_file_path}")
            return False
        
        # Backup the file first
        backup_path = f"{backend_file_path}.bak.fix"
        with open(backend_file_path, 'r') as src:
            with open(backup_path, 'w') as dst:
                dst.write(src.read())
        logger.info(f"✅ Created backup of backend file at {backup_path}")
        
        # Read the backend file
        with open(backend_file_path, 'r') as file:
            content = file.read()
        
        # Find the handle_contextual_chat_request_streaming method
        # We need to add real LLM calls for General, Ask, and Suggest modes
        pattern = r"# Continue with other chat modes processing here(.*?)# Send fallback response"
        replacement = r"""# Continue with other chat modes processing here
            # Since we're falling through to here, we need to provide a response
            # based on the mode. Now with improved LLM integration!
            
            # Import the LLM model if not already imported
            try:
                from llm.model import LocalLLM
                llm_available = True
                logger.info("✅ Imported LocalLLM for direct response generation")
            except ImportError:
                llm_available = False
                logger.error("❌ Failed to import LocalLLM - using fallback responses")
            
            # Prepare to generate a response using the real LLM
            if llm_available:
                try:
                    logger.info(f"Generating real LLM response for: {message}")
                    
                    # Create system message with context
                    system_message = "You are a helpful AI assistant that responds to user questions."
                    if context and "relevant_memories" in context:
                        system_message += "\\n\\nHere's some relevant context from memory:\\n"
                        for i, memory in enumerate(context.get("relevant_memories", [])[:5]):
                            system_message += f"{i+1}. {memory}\\n"
                    
                    # Add specific instructions based on mode
                    if mode.lower() == "agent":
                        system_message += "\\n\\nThe user is in Agent Mode. Respond with a detailed step-by-step plan to automate what they want."
                    elif mode.lower() == "ask":
                        system_message += "\\n\\nThe user is in Ask Mode. Provide a detailed informative answer to their question."
                    elif mode.lower() == "suggest":
                        system_message += "\\n\\nThe user is in Suggest Mode. Provide helpful suggestions related to their request."
                    else:  # General mode
                        system_message += "\\n\\nThe user is in General Mode. Respond conversationally and helpfully."
                    
                    # Create messages for the LLM
                    messages = [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": message}
                    ]
                    
                    # Initialize and use the LLM
                    llm_model = LocalLLM(model_name="llama3.2:1b")  # Fast model
                    await llm_model.start()
                    
                    # Generate the response
                    logger.info("Generating LLM response...")
                    llm_response = await llm_model.generate_response(messages)
                    
                    # Check if we got a valid response
                    if llm_response and not llm_response.startswith("Error:"):
                        logger.info(f"✅ Received valid LLM response ({len(llm_response)} chars)")
                        response = llm_response
                    else:
                        logger.error(f"❌ LLM response error: {llm_response}")
                        # Fall back to mode-specific responses
                        if mode.lower() == "agent":
                            response = f"🎯 Agent Mode: I understand you want to '{message}'. I'll help you automate this task."
                        elif mode.lower() == "ask":
                            response = f"💭 Ask Mode: Here's what I know about '{message}'."
                        elif mode.lower() == "suggest":
                            response = f"💡 Suggest Mode: Based on your request about '{message}', I suggest exploring these options."
                        else:  # General mode
                            response = f"🤖 General Mode: I understand your message about '{message}'. How can I assist you further?"
                
                except Exception as e:
                    logger.error(f"❌ Error generating LLM response: {e}")
                    # Fall back to mode-specific responses
                    if mode.lower() == "agent":
                        response = f"🎯 Agent Mode: I understand you want to '{message}'. I'll help you automate this task."
                    elif mode.lower() == "ask":
                        response = f"💭 Ask Mode: Here's what I know about '{message}'."
                    elif mode.lower() == "suggest":
                        response = f"💡 Suggest Mode: Based on your request about '{message}', I suggest exploring these options."
                    else:  # General mode
                        response = f"🤖 General Mode: I understand your message about '{message}'. How can I assist you further?"
            else:
                # LLM not available - use fallback responses
                if mode.lower() == "agent":
                    response = f"🎯 Agent Mode: I understand you want to '{message}'. I'll help you automate this task."
                elif mode.lower() == "ask":
                    response = f"💭 Ask Mode: Here's what I know about '{message}'."
                elif mode.lower() == "suggest":
                    response = f"💡 Suggest Mode: Based on your request about '{message}', I suggest exploring these options."
                else:  # General mode
                    response = f"🤖 General Mode: I understand your message about '{message}'. How can I assist you further?"
            
            # Send fallback response"""
        
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        # Write the updated content back to the file
        with open(backend_file_path, 'w') as file:
            file.write(updated_content)
        
        logger.info(f"✅ Successfully updated backend file to handle LLM responses")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to fix backend file: {e}")
        return False

def main():
    """Main function to apply fixes"""
    logger.info("="*50)
    logger.info("LLM MODEL NDJSON FIX TOOL")
    logger.info("="*50)
    
    # Step 1: Fix model.py
    model_py_path = get_model_py_path()
    if not model_py_path:
        return
    
    # Step 2: Backup the file
    backup_success = backup_file(model_py_path)
    if not backup_success:
        return
    
    # Step 3: Apply fixes to model.py
    fix_success = fix_model_py(model_py_path)
    if not fix_success:
        return
    
    # Step 4: Fix the backend to ensure LLM responses are sent
    backend_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'enhanced_enterprise_backend_with_context.py')
    backend_fix_success = fix_backend_for_llm_responses(backend_file_path)
    
    # Summary
    logger.info("\n"+"="*50)
    logger.info("FIX SUMMARY")
    logger.info("="*50)
    logger.info(f"Model.py fix: {'✅ SUCCESS' if fix_success else '❌ FAILED'}")
    logger.info(f"Backend fix: {'✅ SUCCESS' if backend_fix_success else '❌ FAILED'}")
    
    if fix_success and backend_fix_success:
        logger.info("\n✅✅✅ All fixes applied successfully!")
        logger.info("""
Next steps:
1. Restart the backend server:
   $ python enhanced_enterprise_backend_with_context.py
   
2. Test the system with the diagnostic tool:
   $ python fix_message_flow.py
        """)
    else:
        logger.info("\n⚠️ Some fixes could not be applied. Please check the logs for details.")

if __name__ == "__main__":
    main()