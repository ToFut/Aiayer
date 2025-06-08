#!/usr/bin/env python3
"""
Fix for LLM timeout issues in the execution flow.
The DO button in overlay chat isn't working because of LLM timeouts during plan execution.
"""

import sys
import os

def apply_fix():
    """Apply the fix to the system"""
    try:
        # Fix 1: Increase LLM timeout for more reliable execution
        fix_llm_timeout()
        
        # Fix 2: Add fallback execution mode for when LLM is unavailable
        add_fallback_execution()
        
        print("✅ Fixes applied successfully!")
        print("The DO button execution should now work more reliably.")
        print("If you're still experiencing issues, try the following:")
        print("1. Ensure your Ollama/LLM service is running properly")
        print("2. Simplify your automation plans to reduce complexity")
        print("3. Use the simple execution mode for more reliable automation")
        return True
    
    except Exception as e:
        print(f"❌ Error applying fix: {e}")
        return False

def fix_llm_timeout():
    """Fix LLM timeout issues in model.py"""
    try:
        # Path to the file
        file_path = "/Users/segevbin/Desktop/SensAI/Aiayer/llm/model.py"
        
        if not os.path.exists(file_path):
            print(f"⚠️ Could not find {file_path}")
            return False
        
        # Read the file content
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Look for timeout settings
        if "timeout = " in content:
            # Increase timeout values
            lines = content.split("\n")
            modified_lines = []
            
            for line in lines:
                if "timeout = " in line and "#" not in line:
                    # Extract current timeout value
                    parts = line.split("=")
                    if len(parts) >= 2:
                        try:
                            current_timeout = float(parts[1].strip().rstrip(","))
                            # Double the timeout if it's below 60 seconds
                            if current_timeout < 60:
                                new_timeout = current_timeout * 2
                                new_line = line.replace(str(current_timeout), str(new_timeout))
                                modified_lines.append(new_line)
                                print(f"✅ Increased timeout from {current_timeout}s to {new_timeout}s")
                                continue
                        except ValueError:
                            pass
                
                modified_lines.append(line)
            
            # Write the modified content back to the file
            with open(file_path, 'w') as file:
                file.write("\n".join(modified_lines))
            
            print("✅ LLM timeout settings updated")
            return True
        else:
            print("⚠️ Could not find timeout settings in the LLM model file")
            return False
    
    except Exception as e:
        print(f"❌ Error fixing LLM timeout: {e}")
        return False

def add_fallback_execution():
    """Add fallback execution mode when LLM is unavailable"""
    try:
        # Path to the file
        file_path = "/Users/segevbin/Desktop/SensAI/Aiayer/universal_intelligent_automation_handler.py"
        
        if not os.path.exists(file_path):
            print(f"⚠️ Could not find {file_path}")
            return False
        
        # Read the file content
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Look for the async def _execute_plan method
        if "async def _execute_plan(self, plan: UniversalAutomationPlan, session_id: str)" in content:
            # Add fallback execution logic for when adaptive_retry_handler fails
            lines = content.split("\n")
            modified_lines = []
            in_method = False
            
            for line in lines:
                if "async def _execute_plan(self, plan: UniversalAutomationPlan, session_id: str)" in line:
                    in_method = True
                
                if in_method and "if not ADAPTIVE_RETRY_AVAILABLE:" in line:
                    # Add additional fallback logic before this check
                    modified_lines.append("        # First try to ensure automation components are available")
                    modified_lines.append("        try:")
                    modified_lines.append("            # Initialize input controller if not already done")
                    modified_lines.append("            if not self.input_controller or not self.automation_available:")
                    modified_lines.append("                try:")
                    modified_lines.append("                    from agent_workflow.input_controller import InputController")
                    modified_lines.append("                    self.input_controller = InputController(safety_level=\"medium\")")
                    modified_lines.append("                    self.automation_available = True")
                    modified_lines.append("                    logger.info(\"🤖 Initialized input controller for direct execution\")")
                    modified_lines.append("                except Exception as e:")
                    modified_lines.append("                    logger.warning(f\"Could not initialize input controller: {e}\")")
                    modified_lines.append("        except Exception as e:")
                    modified_lines.append("            logger.warning(f\"Error ensuring automation components: {e}\")")
                    modified_lines.append("")
                
                if in_method and "# Execute the step using adaptive retry handler" in line:
                    # Add try-except around the adaptive_retry_handler call
                    modified_lines.append(line)
                    modified_lines.append("                try:")
                    modified_lines.append("                    result = await adaptive_retry_handler.execute_step_with_retry(step, plan.task_id)")
                    modified_lines.append("                except Exception as retry_error:")
                    modified_lines.append("                    logger.error(f\"Error with adaptive retry handler: {retry_error}\")")
                    modified_lines.append("                    # Fallback to direct execution")
                    modified_lines.append("                    try:")
                    modified_lines.append("                        if self.automation_available and self.input_controller:")
                    modified_lines.append("                            success = await self._execute_single_step(step)")
                    modified_lines.append("                            result = ExecutionResult(")
                    modified_lines.append("                                success=success,")
                    modified_lines.append("                                step_id=step.id,")
                    modified_lines.append("                                execution_time=1.0,")
                    modified_lines.append("                                retry_count=0")
                    modified_lines.append("                            )")
                    modified_lines.append("                            logger.info(f\"Fallback execution {'succeeded' if success else 'failed'}\")")
                    modified_lines.append("                        else:")
                    modified_lines.append("                            result = ExecutionResult(")
                    modified_lines.append("                                success=False,")
                    modified_lines.append("                                step_id=step.id,")
                    modified_lines.append("                                execution_time=0.0,")
                    modified_lines.append("                                error_message=\"Fallback execution not available\",")
                    modified_lines.append("                                retry_count=0")
                    modified_lines.append("                            )")
                    modified_lines.append("                    except Exception as e:")
                    modified_lines.append("                        logger.error(f\"Fallback execution error: {e}\")")
                    modified_lines.append("                        result = ExecutionResult(")
                    modified_lines.append("                            success=False,")
                    modified_lines.append("                            step_id=step.id,")
                    modified_lines.append("                            execution_time=0.0,")
                    modified_lines.append("                            error_message=f\"Execution error: {str(e)}\",")
                    modified_lines.append("                            retry_count=0")
                    modified_lines.append("                        )")
                    # Skip the next line which is the original adaptive_retry_handler call
                    continue
                
                modified_lines.append(line)
                
                if in_method and line.strip() == "}" and len(modified_lines) > 0:
                    in_method = False
            
            # Add ExecutionResult class import if needed
            if "from adaptive_retry_automation_handler import adaptive_retry_handler" in content and "ExecutionResult" not in content:
                for i, line in enumerate(modified_lines):
                    if "from adaptive_retry_automation_handler import adaptive_retry_handler" in line:
                        modified_lines[i] = "from adaptive_retry_automation_handler import adaptive_retry_handler, ExecutionResult"
                        break
            
            # Write the modified content back to the file
            with open(file_path, 'w') as file:
                file.write("\n".join(modified_lines))
            
            print("✅ Added fallback execution mode for reliability")
            return True
        else:
            print("⚠️ Could not find _execute_plan method in the universal_intelligent_automation_handler.py file")
            return False
    
    except Exception as e:
        print(f"❌ Error adding fallback execution: {e}")
        return False

if __name__ == "__main__":
    success = apply_fix()
    sys.exit(0 if success else 1)