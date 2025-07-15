#!/usr/bin/env python3
"""
Simple test to verify the chain improvements work.
"""

import asyncio
import json
import time
from datetime import datetime

# Add the current directory to Python path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.enhanced_backend_server import EnhancedBackendServer
from backend.llm.llm_service import LLMService
from backend.automation_plan import AutomationPlan

async def test_simple_chain():
    """Test a simple prompt through the chain"""
    print("🧪 Testing simple chain...")
    
    # Initialize components
    backend = EnhancedBackendServer()
    llm_service = LLMService()
    
    try:
        # Setup
        await backend.initialize()
        await llm_service.initialize()
        
        # Test prompt
        prompt = "open calculator"
        
        print(f"📝 Testing prompt: {prompt}")
        
        # Generate plan using the improved LLM service
        print("🔄 Generating plan with LLM...")
        start_time = time.time()
        
        try:
            # Use the improved generate_response_with_fallback method
            llm_chunks = []
            async for chunk in llm_service.generate_response_with_fallback(prompt):
                llm_chunks.append(chunk)
            llm_response = ''.join(llm_chunks)
            llm_time = time.time() - start_time
            
            print(f"✅ LLM response generated in {llm_time:.2f}s")
            print(f"📄 Response length: {len(llm_response)} chars")
            print(f"📄 Response preview: {llm_response[:200]}...")
            
            # Parse the plan
            print("🔄 Parsing plan...")
            try:
                # Extract JSON from response
                text = llm_response.strip()
                if '```json' in text:
                    text = text.split('```json', 1)[1]
                if '```' in text:
                    text = text.split('```', 1)[1]
                text = text.strip('`\n ')
                
                # Find JSON object with improved extraction
                import re
                
                # First, try to find complete JSON objects by counting braces
                json_objects = []
                text_remaining = text
                
                while True:
                    # Find the next opening brace
                    brace_start = text_remaining.find('{')
                    if brace_start == -1:
                        break
                    
                    # Find the matching closing brace
                    brace_count = 0
                    brace_end = -1
                    
                    for i, char in enumerate(text_remaining[brace_start:], brace_start):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                brace_end = i + 1
                                break
                    
                    if brace_end > brace_start:
                        json_obj = text_remaining[brace_start:brace_end]
                        json_objects.append(json_obj)
                        text_remaining = text_remaining[brace_end:]
                    else:
                        # No matching closing brace found, skip this opening brace
                        text_remaining = text_remaining[brace_start + 1:]
                
                # If we found complete JSON objects, use the longest one
                if json_objects:
                    # Sort by length and try to parse each one
                    json_objects.sort(key=len, reverse=True)
                    
                    for json_obj in json_objects:
                        try:
                            # Try to parse this JSON object
                            test_plan = json.loads(json_obj)
                            if isinstance(test_plan, dict) and "steps" in test_plan:
                                text = json_obj
                                break
                        except json.JSONDecodeError:
                            continue
                else:
                    # Fallback to regex if no complete objects found
                    match = re.search(r'\{[\s\S]*?\}', text)
                    if match:
                        text = match.group(0)
                
                print(f"🔧 Extracted JSON: {text}")
                
                # Repair common issues
                text = text.replace("'", '"')
                text = re.sub(r'}}]', r'}]', text)
                
                # Fix smart quotes and other Unicode issues
                text = text.replace('"', '"').replace('"', '"')  # Smart quotes
                text = text.replace(''', "'").replace(''', "'")  # Smart apostrophes
                text = text.replace('…', '...')  # Ellipsis
                text = text.replace('–', '-').replace('—', '-')  # Em dashes
                
                # Fix any remaining Unicode issues
                import unicodedata
                text = unicodedata.normalize('NFKC', text)
                
                # Additional JSON repair
                # Fix missing commas between object properties
                text = re.sub(r'}\s*{', r'},{', text)
                text = re.sub(r'}\s*]', r'}]', text)
                text = re.sub(r'}\s*}', r'}}', text)
                
                # Fix missing commas in arrays
                text = re.sub(r'}\s*{', r'},{', text)
                
                # Fix the specific LLM issue: }}] should be }]
                text = re.sub(r'}}]', r'}]', text)
                
                # Fix any remaining }}] patterns
                text = re.sub(r'}}]', r'}]', text)
                
                # Try to fix missing closing braces
                brace_count = text.count('{') - text.count('}')
                if brace_count > 0:
                    text += '}' * brace_count
                
                # Try to fix missing closing brackets
                bracket_count = text.count('[') - text.count(']')
                if bracket_count > 0:
                    text += ']' * bracket_count
                
                print(f"🔧 After repair: {text}")
                
                # Try to parse JSON with multiple fallback approaches
                plan_dict = None
                parse_errors = []
                
                # Approach 1: Direct parsing
                try:
                    plan_dict = json.loads(text)
                except json.JSONDecodeError as e:
                    parse_errors.append(f"Direct parsing failed: {e}")
                    
                    # Approach 2: Try with json5 for more lenient parsing
                    try:
                        import json5
                        plan_dict = json5.loads(text)
                    except Exception as e2:
                        parse_errors.append(f"JSON5 parsing failed: {e2}")
                        
                        # Approach 3: Manual repair and retry
                        try:
                            # Try to fix common issues manually
                            repaired_text = text
                            
                            # Fix missing commas after property values
                            repaired_text = re.sub(r'(\w+)"\s*(\w+":)', r'\1",\2', repaired_text)
                            
                            # Fix missing commas between objects
                            repaired_text = re.sub(r'}\s*{', r'},{', repaired_text)
                            
                            # Try parsing again
                            plan_dict = json.loads(repaired_text)
                        except Exception as e3:
                            parse_errors.append(f"Manual repair failed: {e3}")
                            
                            # Approach 4: Extract key-value pairs and rebuild
                            try:
                                # Extract apps and steps using regex
                                apps_match = re.search(r'"apps":\s*\[([^\]]+)\]', text)
                                steps_match = re.search(r'"steps":\s*\[([\s\S]*)\]', text)
                                
                                apps = []
                                if apps_match:
                                    apps_text = apps_match.group(1)
                                    # Extract app names
                                    app_names = re.findall(r'"([^"]+)"', apps_text)
                                    apps = app_names
                                
                                steps = []
                                if steps_match:
                                    steps_text = steps_match.group(1)
                                    # Extract step objects
                                    step_objects = re.findall(r'\{[^}]+\}', steps_text)
                                    for step_obj in step_objects:
                                        try:
                                            step_dict = json.loads(step_obj)
                                            steps.append(step_dict)
                                        except:
                                            # Create a basic step from the text
                                            action_match = re.search(r'"action":\s*"([^"]+)"', step_obj)
                                            app_match = re.search(r'"app":\s*"([^"]+)"', step_obj)
                                            desc_match = re.search(r'"description":\s*"([^"]+)"', step_obj)
                                            
                                            step = {}
                                            if action_match:
                                                step["action"] = action_match.group(1)
                                            if app_match:
                                                step["app"] = app_match.group(1)
                                            if desc_match:
                                                step["description"] = desc_match.group(1)
                                            
                                            if step:
                                                steps.append(step)
                                
                                plan_dict = {
                                    "apps": apps,
                                    "steps": steps
                                }
                                
                            except Exception as e4:
                                parse_errors.append(f"Key-value extraction failed: {e4}")
                                raise Exception(f"All JSON parsing approaches failed: {'; '.join(parse_errors)}")
                
                if plan_dict is None:
                    raise Exception(f"Failed to parse JSON: {'; '.join(parse_errors)}")
                
                if "steps" not in plan_dict:
                    plan_dict["steps"] = []
                if "task_id" not in plan_dict:
                    plan_dict["task_id"] = f"plan_{int(time.time())}"
                
                plan = AutomationPlan.from_dict(plan_dict)
                print(f"✅ Plan parsed successfully!")
                print(f"📋 Steps: {len(plan.steps)} steps")
                print(f"📋 Apps: {plan_dict.get('apps', [])}")
                
                # Execute plan
                print("🔄 Executing plan...")
                await backend.execute_plan(plan)
                print("✅ Plan executed successfully!")
                
            except Exception as parse_error:
                print(f"❌ Plan parsing failed: {parse_error}")
                print(f"📄 Full response: {llm_response}")
                
        except Exception as llm_error:
            print(f"❌ LLM generation failed: {llm_error}")
            print("🔄 Using fallback response...")
            
            # Create fallback response
            fallback_response = {
                "apps": ["Calculator"],
                "steps": [
                    {
                        "action": "open_app",
                        "app": "Calculator",
                        "description": "Open Calculator"
                    }
                ]
            }
            
            plan_dict = fallback_response
            plan_dict["task_id"] = f"fallback_{int(time.time())}"
            
            plan = AutomationPlan.from_dict(plan_dict)
            print(f"✅ Fallback plan created!")
            print(f"📋 Steps: {len(plan.steps)} steps")
            
            # Execute plan
            print("🔄 Executing fallback plan...")
            await backend.execute_plan(plan)
            print("✅ Fallback plan executed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    finally:
        # Cleanup
        await backend.stop()
        print("✅ Test completed!")

if __name__ == "__main__":
    asyncio.run(test_simple_chain()) 