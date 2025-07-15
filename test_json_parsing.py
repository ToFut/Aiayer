#!/usr/bin/env python3
"""
Simple test to verify JSON parsing improvements work.
"""

import json
import re
import time

def _extract_plan_dict(llm_response: str, prompt: str) -> dict:
    """Extract a plan dict from LLM response, robust to markdown/code blocks and malformed JSON."""
    # Try to extract JSON from code blocks
    text = llm_response.strip()
    
    # Remove markdown code block markers
    if '```json' in text:
        text = text.split('```json', 1)[1]
    if '```' in text:
        text = text.split('```', 1)[1]
    text = text.strip('`\n ')
    
    # Try to find the first { ... } with better regex
    match = re.search(r'\{[\s\S]*?\}', text)
    if match:
        text = match.group(0)
    
    # Try to repair common JSON issues
    text = text.replace("'", '"')
    text = re.sub(r',\s*}', '}', text)
    text = re.sub(r',\s*]', ']', text)
    
    # Fix missing commas between object properties
    text = re.sub(r'}\s*{', r'},{', text)
    text = re.sub(r'}\s*]', r'}]', text)
    text = re.sub(r'}\s*}', r'}}', text)
    
    # Fix missing commas in arrays
    text = re.sub(r'}\s*{', r'},{', text)
    
    # Fix the specific LLM issue: }}] should be }]
    text = re.sub(r'}\s*}\s*]', r'}]', text)
    
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
    
    # Try to parse
    try:
        plan = json.loads(text)
        
        # If plan is just steps, wrap it
        if isinstance(plan, list):
            plan = {"steps": plan}
        
        # Ensure required fields
        if "steps" not in plan or not isinstance(plan["steps"], list):
            # Try to create steps from the plan structure
            if isinstance(plan, dict):
                steps = []
                for key, value in plan.items():
                    if key != "task_id" and key != "completed":
                        if isinstance(value, dict):
                            steps.append(value)
                        elif isinstance(value, str):
                            steps.append({"description": value})
                if steps:
                    plan["steps"] = steps
                else:
                    raise ValueError("No steps in plan")
            else:
                raise ValueError("No steps in plan")
        
        if "task_id" not in plan:
            plan["task_id"] = f"plan_{int(time.time())}"
        
        return plan
        
    except Exception as e:
        # Try one more time with more aggressive repair
        try:
            # Remove any trailing commas before closing braces/brackets
            text = re.sub(r',(\s*[}\]])', r'\1', text)
            # Fix common LLM JSON issues
            text = re.sub(r'(\w+):\s*"([^"]*)"\s*(\w+):', r'\1: "\2", \3:', text)
            
            # More aggressive }}] fix
            text = re.sub(r'}}]', r'}]', text)
            text = re.sub(r'}\s*}\s*]', r'}]', text)
            
            # Try to complete truncated JSON
            if text.count('{') > text.count('}'):
                text += '}' * (text.count('{') - text.count('}'))
            if text.count('[') > text.count(']'):
                text += ']' * (text.count('[') - text.count(']'))
            
            print(f"  🔧 Attempting JSON repair: {text[:100]}...")
            
            plan = json.loads(text)
            
            # If plan is just steps, wrap it
            if isinstance(plan, list):
                plan = {"steps": plan}
            
            # Ensure required fields
            if "steps" not in plan or not isinstance(plan["steps"], list):
                if isinstance(plan, dict):
                    steps = []
                    for key, value in plan.items():
                        if key != "task_id" and key != "completed":
                            if isinstance(value, dict):
                                steps.append(value)
                            elif isinstance(value, str):
                                steps.append({"description": value})
                    if steps:
                        plan["steps"] = steps
                    else:
                        raise ValueError("No steps in plan")
                else:
                    raise ValueError("No steps in plan")
            
            if "task_id" not in plan:
                plan["task_id"] = f"plan_{int(time.time())}"
            
            return plan
            
        except Exception as e2:
            raise ValueError(f"Failed to parse plan JSON: {e}\nRaw: {text[:200]}")

# Test with the actual LLM response format
test_responses = [
    # The problematic response from the test
    '''{
  "apps": ["app1", "app2"],
  "steps": [
    {
      "action": "open_app",
      "app": "calculator",
      "description": "open calculator"
    }}]''',
    
    # A complete response
    '''{
  "apps": ["app1", "app2"],
  "steps": [
    {
      "action": "open_app",
      "app": "calculator",
      "description": "open calculator"
    },
    {
      "action": "wait",
      "duration": 2,
      "description": "wait for 2 seconds"
    },
    {
      "action": "screenshot",
      "description": "take a screenshot"
    }
  ]
}'''
]

print("Testing JSON parsing improvements...")
print("=" * 50)

for i, response in enumerate(test_responses, 1):
    print(f"\nTest {i}:")
    print(f"Input: {response[:100]}...")
    try:
        result = _extract_plan_dict(response, "test")
        print(f"✅ SUCCESS: Parsed {len(result.get('steps', []))} steps")
        print(f"Result: {result}")
        except Exception as e:
        print(f"❌ FAILED: {e}")