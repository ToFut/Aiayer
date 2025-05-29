#!/usr/bin/env python3
"""
Debug script to identify the root cause of JSON parsing failures
"""
import asyncio
import json
from llm.llm_service import LLMService

async def debug_json_issue():
    llm = LLMService()
    
    # Use the exact prompt that's causing issues
    prompt = '''You are an expert Mac automation agent. Your job is to create detailed, step-by-step automation plans for ANY user request.

RESPONSE FORMAT (JSON - NO COMMENTS ALLOWED):
{
  "title": "Clear title for the automation task",
  "description": "Brief description of what will be accomplished",
  "complexity_score": 0.7,
  "estimated_duration": 15,
  "steps": [
    {
      "id": "step_1",
      "description": "Human-readable description of this step",
      "action_type": "open_app",
      "target": "Safari",
      "value": "text_to_type_or_null",
      "coordinates": null,
      "estimated_duration": 3,
      "confidence": 0.9
    }
  ]
}

CRITICAL: 
- DO NOT include any comments (//) in the JSON
- Use actual numbers for estimated_duration, not "seconds" 
- Use single action_type values like "open_app", not "open_app|navigate_url"
- Use null without quotes for null values
- Provide valid JSON only

USER REQUEST: "open Safari and search SEGEV"

Provide a comprehensive JSON response.'''
    
    print('Getting LLM response...')
    response = await llm.generate_response(prompt)
    
    print('\n=== RAW RESPONSE ===')
    print(response)
    
    # Try to extract JSON like the actual code does
    response_text = response.strip()
    json_text = None
    
    # Same logic as in real_agent_automation_handler.py
    if '```json' in response_text:
        start = response_text.find('```json') + 7
        end = response_text.find('```', start)
        if end != -1:
            json_text = response_text[start:end].strip()
    elif '```' in response_text:
        start = response_text.find('```') + 3
        end = response_text.find('```', start)
        if end != -1:
            potential_json = response_text[start:end].strip()
            if potential_json.startswith('{') and potential_json.endswith('}'):
                json_text = potential_json
    
    if not json_text and '{' in response_text and '}' in response_text:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        json_text = response_text[start:end]
    
    print('\n=== EXTRACTED JSON ===')
    print(json_text)
    print(f'Length: {len(json_text) if json_text else 0}')
    
    if json_text:
        try:
            parsed = json.loads(json_text)
            print('\n✅ JSON PARSING SUCCESSFUL')
            print('Keys:', list(parsed.keys()))
        except json.JSONDecodeError as e:
            print(f'\n❌ JSON PARSING FAILED: {e}')
            print(f'Error at position: {e.pos}')
            if e.pos < len(json_text):
                # Show character-by-character context around the error
                context_start = max(0, e.pos - 20)
                context_end = min(len(json_text), e.pos + 20)
                print(f'Context: {repr(json_text[context_start:context_end])}')
                print(f'Error char: {repr(json_text[e.pos] if e.pos < len(json_text) else "EOF")}')
                
                # Show line context
                lines = json_text.split('\n')
                char_count = 0
                for line_num, line in enumerate(lines):
                    if char_count <= e.pos <= char_count + len(line) + 1:
                        col = e.pos - char_count
                        print(f'Line {line_num + 1}, Column {col}: {line}')
                        print(' ' * (col + len(f'Line {line_num + 1}, Column {col}: ')) + '^')
                        break
                    char_count += len(line) + 1
            
            # Try to fix the JSON like the actual code does
            print('\n🔧 ATTEMPTING JSON FIXES...')
            fixed_json = json_text
            
            import re
            
            # CRITICAL FIX: Remove JavaScript-style comments (// comments) - ROOT CAUSE
            fixed_json = re.sub(r'//.*?(?=\n|$)', '', fixed_json)
            
            # Remove /* */ style comments as well
            fixed_json = re.sub(r'/\*.*?\*/', '', fixed_json, flags=re.DOTALL)
            
            # Fix trailing commas
            fixed_json = re.sub(r',(\s*[}\]])', r'\1', fixed_json)
            
            # Fix pipe-separated action types to single value
            fixed_json = re.sub(r'"action_type":\s*"([^|"]+)\|[^"]*"', r'"action_type": "\1"', fixed_json)
            
            # Fix target with = signs like "application_name=Safari" -> "Safari"
            fixed_json = re.sub(r'"target":\s*"[^=]*=([^"]*)"', r'"target": "\1"', fixed_json)
            
            print(f'Fixed JSON length: {len(fixed_json)}')
            
            try:
                parsed_fixed = json.loads(fixed_json)
                print('✅ JSON FIXING SUCCESSFUL!')
                print('Keys:', list(parsed_fixed.keys()))
                if 'steps' in parsed_fixed:
                    print(f'Steps: {len(parsed_fixed["steps"])}')
            except json.JSONDecodeError as fix_error:
                print(f'❌ JSON FIXING FAILED: {fix_error}')
                print('First 300 chars of fixed JSON:')
                print(fixed_json[:300])

if __name__ == "__main__":
    asyncio.run(debug_json_issue())