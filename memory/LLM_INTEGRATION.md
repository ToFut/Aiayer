# Integrating the Conscious Memory System with LLMs

This guide explains how to integrate the Conscious Memory System with Large Language Models (LLMs) to create a context-aware AI assistant.

## Overview

The Conscious Memory System collects and processes data from multiple sensors (screen, process, file) to create a unified representation of the user's context. This context can be sent to an LLM to provide more relevant and personalized responses.

## Integration Process

### 1. Start the Memory System

First, ensure the memory system is running to collect and process sensor data:

```bash
./start_memory_system.sh
```

### 2. Access the Memory State

The memory system maintains a complete state in the `memory/conscious.json` file, which is updated at regular intervals. You can view this state using:

```bash
./view_conscious_memory.py --format prompt
```

### 3. Generate LLM Prompts

The memory system provides a built-in function to generate prompts for LLMs based on the current memory state:

```python
from memory.update_conscious import generate_llm_prompt

# Load the conscious memory
with open('memory/conscious.json', 'r') as f:
    conscious_memory = json.load(f)

# Generate a prompt for the LLM
prompt = generate_llm_prompt(conscious_memory)
```

### 4. LLM Integration Code

Here's an example of how to integrate with an LLM:

```python
import json
import requests
from memory.update_conscious import generate_llm_prompt

def get_memory_prompt():
    """Get a prompt based on the current memory state"""
    try:
        with open('memory/conscious.json', 'r') as f:
            conscious_memory = json.load(f)
        return generate_llm_prompt(conscious_memory)
    except Exception as e:
        print(f"Error getting memory prompt: {e}")
        return None

def send_to_llm(prompt, user_query):
    """Send a prompt to the LLM"""
    try:
        # Combine the memory prompt with the user's query
        combined_prompt = f"{prompt}\n\nUser Query: {user_query}"
        
        # Example of sending to a local LLM API
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": combined_prompt,
                "stream": False
            }
        )
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error sending to LLM: {e}"

def main():
    user_query = "What am I working on right now?"
    
    # Get context-aware prompt
    memory_prompt = get_memory_prompt()
    
    # Send to LLM
    if memory_prompt:
        response = send_to_llm(memory_prompt, user_query)
        print(f"LLM Response: {response}")
    else:
        print("Failed to get memory prompt")

if __name__ == "__main__":
    main()
```

## Prompt Structure

The generated prompt includes:

1. **Recent Insights**: Summary of what the system has observed
2. **Active Applications**: Currently running apps
3. **Recent File Activity**: Recent file changes
4. **Analysis Request**: Instructions for the LLM

Example prompt:

```
# System Context Analysis
Timestamp: 2025-05-20T00:15:00.000Z

## Recent Insights
1. Screen capture at 2025-05-20T00:14:33.785535 with resolution 2940x1912 (hash: 3b457683)
2. Active applications at 2025-05-20T00:14:43.977778: Terminal, bash, python
3. No file system events detected at 2025-05-20T00:14:43.977778
4. System state at 2025-05-20T00:14:50.000Z: Running: Terminal, bash, python; Screen: be782fbe

## Active Applications
- Terminal
- bash
- python

## Recent File Activity
- No recent file activity

## Analysis Request
Please analyze the user's current context and provide the following:

1. What is the user currently working on?
2. What tools or applications are they using?
3. What might they need help with based on this context?
4. Are there any patterns or trends in their recent activity?
```

## Advanced Integration

### 1. WebSocket Integration

For real-time updates, you can implement a WebSocket server that sends memory updates to your LLM service:

```python
import asyncio
import websockets
import json
from memory.update_conscious import generate_llm_prompt

async def memory_server(websocket, path):
    """WebSocket server that sends memory updates"""
    try:
        while True:
            # Load the latest memory state
            with open('memory/conscious.json', 'r') as f:
                conscious_memory = json.load(f)
            
            # Generate prompt
            prompt = generate_llm_prompt(conscious_memory)
            
            # Send to client
            await websocket.send(json.dumps({
                "type": "memory_update",
                "prompt": prompt,
                "timestamp": conscious_memory.get("timestamp")
            }))
            
            # Wait before next update
            await asyncio.sleep(10)
    except websockets.exceptions.ConnectionClosed:
        pass

async def main():
    server = await websockets.serve(memory_server, "localhost", 8766)
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Customizing the Prompt

You can customize the prompt generation by modifying the `generate_llm_prompt` function in `memory/update_conscious.py`:

```python
def generate_custom_llm_prompt(conscious: Dict[str, Any], focus_areas: List[str] = None) -> str:
    """Generate a custom prompt for an LLM based on the conscious memory"""
    # Start with base prompt from standard function
    prompt = generate_llm_prompt(conscious)
    
    # Add custom sections based on focus areas
    if focus_areas:
        prompt += "\n## Focus Areas\n"
        for area in focus_areas:
            prompt += f"- {area}\n"
    
    return prompt
```

## Best Practices

1. **Context Window Management**: LLMs have limited context windows. The prompt generator is designed to provide concise context, but you may need to further optimize for your specific LLM.

2. **Update Frequency**: Update the context sent to the LLM only when significant changes occur, rather than with every request.

3. **Privacy Considerations**: Filter sensitive information before sending to the LLM.

4. **Personalization**: Track which insights lead to better responses and prioritize them in future prompts.

## Troubleshooting

- **Empty Insights**: If you see no insights, make sure all sensors are running and capturing data.
- **LLM Not Using Context**: Check that the prompt is being properly sent to the LLM and that the LLM has sufficient context window size.
- **Performance Issues**: Reduce the prompt size by limiting the number of insights or active applications included.