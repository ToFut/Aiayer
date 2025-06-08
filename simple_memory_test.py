#!/usr/bin/env python3
"""
Simple Memory Test

This script uses the curl command-line tool to interact with the memory system
via HTTP requests. It tests adding and searching for memories to verify that
the memory system is working correctly.
"""

import subprocess
import json
import time
import uuid
from datetime import datetime

# Configuration
API_URL = "http://localhost:8767"
MEMORY_CONTENT = f"Test memory created at {datetime.now().isoformat()} with ID {str(uuid.uuid4())}"

def run_curl_command(url, method="GET", data=None):
    """Run a curl command and return the response"""
    cmd = ["curl", "-s"]
    
    if method == "POST":
        cmd.extend(["-X", "POST"])
        if data:
            cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(data)])
    
    cmd.append(url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running curl command: {e}")
        print(f"Command: {' '.join(cmd)}")
        print(f"Stderr: {e.stderr}")
        return None

def test_add_memory():
    """Test adding a memory using curl"""
    print(f"TEST 1: Adding memory: {MEMORY_CONTENT[:50]}...")
    
    data = {
        "type": "add_memory",
        "content": MEMORY_CONTENT,
        "source": "curl_test",
        "tags": ["test", "curl"],
        "metadata": {
            "test_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat()
        }
    }
    
    response = run_curl_command(f"{API_URL}/memory", method="POST", data=data)
    
    if response:
        try:
            result = json.loads(response)
            if result.get("success"):
                print("✅ Memory added successfully")
                return True
            else:
                print(f"❌ Failed to add memory: {result.get('error', 'Unknown error')}")
        except json.JSONDecodeError:
            print(f"❌ Failed to parse response: {response}")
    else:
        print("❌ No response from memory system")
    
    return False

def test_search_memory():
    """Test searching for memories using curl"""
    print("TEST 2: Searching for test memory...")
    
    data = {
        "type": "search_memory",
        "query": "test memory",
        "top_k": 10,
        "source_filter": "curl_test"
    }
    
    response = run_curl_command(f"{API_URL}/search", method="POST", data=data)
    
    if response:
        try:
            result = json.loads(response)
            results = result.get("results", [])
            
            if results:
                print(f"✅ Found {len(results)} search results")
                
                # Check if our test memory is in the results
                found = False
                for memory in results:
                    if MEMORY_CONTENT in memory.get("content", ""):
                        print("✅ Found our test memory in search results!")
                        found = True
                        break
                
                if not found:
                    print("⚠️ Test memory not found in results")
                
                # Print search result details
                for i, memory in enumerate(results[:3]):  # Show top 3 results
                    print(f"Result {i+1}:")
                    print(f"  Content: {memory.get('content', '')[:100]}...")
                    print(f"  Score: {memory.get('similarity_score')}")
                    print(f"  Source: {memory.get('source')}")
                
                return True
            else:
                print("❌ No search results found")
        except json.JSONDecodeError:
            print(f"❌ Failed to parse response: {response}")
    else:
        print("❌ No response from memory system")
    
    return False

def main():
    """Run the memory tests"""
    print("Starting simple memory test...")
    
    # Test 1: Add a memory
    add_success = test_add_memory()
    
    if add_success:
        # Wait a moment for the memory to be processed
        time.sleep(1)
        
        # Test 2: Search for the memory
        search_success = test_search_memory()
        
        if search_success:
            print("✅ All tests completed successfully")
            return 0
    
    print("❌ Tests failed")
    return 1

if __name__ == "__main__":
    exit(main())