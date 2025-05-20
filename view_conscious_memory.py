#!/usr/bin/env python3
"""
Script to view and analyze the current conscious memory state
This provides a simple way to examine the memory contents and insights
"""
import os
import json
import argparse
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("memory.viewer")

# Set paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(SCRIPT_DIR, "memory")
CONSCIOUS_FILE = os.path.join(MEMORY_DIR, "conscious.json")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='View and analyze conscious memory')
    parser.add_argument('--format', choices=['summary', 'full', 'insights', 'json', 'prompt'], 
                       default='summary', help='Output format (default: summary)')
    parser.add_argument('--json-indent', type=int, default=2,
                      help='Indentation level for JSON output (default: 2)')
    parser.add_argument('--limit', type=int, default=5,
                      help='Limit number of entries to display (default: 5)')
    return parser.parse_args()

def load_conscious_memory():
    """Load the conscious memory file"""
    try:
        if not os.path.exists(CONSCIOUS_FILE):
            logger.error(f"Conscious memory file not found at {CONSCIOUS_FILE}")
            return None
            
        with open(CONSCIOUS_FILE, 'r') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from {CONSCIOUS_FILE}")
        return None
    except Exception as e:
        logger.error(f"Error loading {CONSCIOUS_FILE}: {e}")
        return None

def format_timestamp(timestamp_str):
    """Format timestamp string for better readability"""
    try:
        # Parse ISO format timestamp
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        # Format as readable string
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str

def print_summary(memory_data, limit=5):
    """Print a summary of the conscious memory"""
    if not memory_data:
        return
    
    print("\n=== CONSCIOUS MEMORY SUMMARY ===")
    
    # Print timestamp
    timestamp = memory_data.get("timestamp", "Unknown")
    print(f"Timestamp: {format_timestamp(timestamp)}")
    
    # Print system state
    system_state = memory_data.get("system_state", {})
    print("\nSystem State:")
    for key, value in system_state.items():
        if isinstance(value, str):
            value = format_timestamp(value)
        print(f"  {key}: {value}")
    
    # Print sensor buffer stats
    sensor_buffers = memory_data.get("sensor_buffers", {})
    print("\nSensor Buffers:")
    for sensor_type, buffer in sensor_buffers.items():
        print(f"  {sensor_type}: {len(buffer)} entries")
        
        # Print latest entry for each sensor type
        if buffer:
            latest = buffer[0]
            print(f"    Latest: {format_timestamp(latest.get('timestamp', latest.get('datetime', 'Unknown')))}")
            
            if sensor_type == "screen":
                print(f"    Image Hash: {latest.get('image_hash', 'Unknown')}")
                print(f"    Screen Size: {latest.get('screen_size', 'Unknown')}")
            elif sensor_type == "process":
                apps = latest.get("active_apps", [])
                if apps:
                    print(f"    Active Apps: {', '.join(apps[:3])}{'...' if len(apps) > 3 else ''}")
            elif sensor_type == "file":
                event_count = latest.get("event_count", 0)
                print(f"    Event Count: {event_count}")
    
    # Print insights
    insights = memory_data.get("insights", [])
    print(f"\nInsights ({len(insights)} total):")
    for i, insight in enumerate(insights[:limit]):
        if i >= limit:
            break
        timestamp = format_timestamp(insight.get("timestamp", "Unknown"))
        insight_type = insight.get("type", "Unknown")
        content = insight.get("content", "No content")
        print(f"  [{timestamp}] {insight_type}: {content}")
    
    if len(insights) > limit:
        print(f"  ... and {len(insights) - limit} more insights")
    
    print("\n================================")

def print_insights(memory_data, limit=10):
    """Print all insights from the conscious memory"""
    if not memory_data:
        return
    
    insights = memory_data.get("insights", [])
    
    print("\n=== CONSCIOUS MEMORY INSIGHTS ===")
    print(f"Total Insights: {len(insights)}")
    
    # Group insights by type
    insights_by_type = {}
    for insight in insights:
        insight_type = insight.get("type", "unknown")
        if insight_type not in insights_by_type:
            insights_by_type[insight_type] = []
        insights_by_type[insight_type].append(insight)
    
    # Print insights grouped by type
    for insight_type, type_insights in insights_by_type.items():
        print(f"\n{insight_type.upper()} INSIGHTS ({len(type_insights)} total):")
        for i, insight in enumerate(type_insights[:limit]):
            if i >= limit:
                break
            timestamp = format_timestamp(insight.get("timestamp", "Unknown"))
            content = insight.get("content", "No content")
            print(f"  [{timestamp}] {content}")
        
        if len(type_insights) > limit:
            print(f"  ... and {len(type_insights) - limit} more {insight_type} insights")
    
    print("\n================================")

def print_full(memory_data, limit=5):
    """Print full details of the conscious memory with limited entries"""
    if not memory_data:
        return
    
    print("\n=== CONSCIOUS MEMORY FULL DETAILS ===")
    
    # Print timestamp
    timestamp = memory_data.get("timestamp", "Unknown")
    print(f"Timestamp: {format_timestamp(timestamp)}")
    
    # Print system state
    system_state = memory_data.get("system_state", {})
    print("\nSystem State:")
    for key, value in system_state.items():
        if isinstance(value, str):
            value = format_timestamp(value)
        print(f"  {key}: {value}")
    
    # Print sensor buffers
    sensor_buffers = memory_data.get("sensor_buffers", {})
    print("\nSensor Buffers:")
    for sensor_type, buffer in sensor_buffers.items():
        print(f"\n  {sensor_type.upper()} BUFFER ({len(buffer)} entries):")
        
        # Print latest entries for each sensor type
        for i, entry in enumerate(buffer[:limit]):
            if i >= limit:
                break
                
            entry_time = format_timestamp(entry.get("timestamp", entry.get("datetime", "Unknown")))
            print(f"\n    Entry {i+1} @ {entry_time}:")
            
            if sensor_type == "screen":
                print(f"      Image Hash: {entry.get('image_hash', 'Unknown')}")
                print(f"      Screen Size: {entry.get('screen_size', 'Unknown')}")
            elif sensor_type == "process":
                apps = entry.get("active_apps", [])
                if apps:
                    print(f"      Active Apps ({len(apps)}):")
                    for j, app in enumerate(apps[:5]):
                        print(f"        - {app}")
                    if len(apps) > 5:
                        print(f"        ... and {len(apps) - 5} more")
            elif sensor_type == "file":
                events = entry.get("events", [])
                print(f"      Events: {len(events)}")
                for j, event in enumerate(events[:3]):
                    if isinstance(event, dict):
                        print(f"        - {event.get('type', 'Unknown')}: {event.get('path', 'Unknown')}")
                    else:
                        print(f"        - {event}")
                if len(events) > 3:
                    print(f"        ... and {len(events) - 3} more")
        
        if len(buffer) > limit:
            print(f"    ... and {len(buffer) - limit} more entries")
    
    # Print insights
    insights = memory_data.get("insights", [])
    print(f"\nInsights ({len(insights)} total):")
    for i, insight in enumerate(insights[:limit]):
        if i >= limit:
            break
        timestamp = format_timestamp(insight.get("timestamp", "Unknown"))
        insight_type = insight.get("type", "Unknown")
        content = insight.get("content", "No content")
        print(f"\n  Insight {i+1}:")
        print(f"    Type: {insight_type}")
        print(f"    Time: {timestamp}")
        print(f"    Content: {content}")
    
    if len(insights) > limit:
        print(f"  ... and {len(insights) - limit} more insights")
    
    print("\n===================================")

def print_llm_prompt(memory_data):
    """Print the LLM prompt that would be generated from the memory"""
    try:
        # Import the function from update_conscious.py
        import sys
        sys.path.append(MEMORY_DIR)
        from update_conscious import generate_llm_prompt
        
        # Generate prompt
        prompt = generate_llm_prompt(memory_data)
        
        print("\n=== LLM PROMPT FROM CONSCIOUS MEMORY ===\n")
        print(prompt)
        print("\n==========================================")
    except ImportError:
        logger.error("Failed to import generate_llm_prompt from update_conscious.py")
        print("\nError: Could not generate LLM prompt. Make sure update_conscious.py is available.")
    except Exception as e:
        logger.error(f"Error generating LLM prompt: {e}")
        print(f"\nError generating LLM prompt: {e}")

def main():
    """Main function"""
    args = parse_args()
    
    # Load conscious memory
    memory_data = load_conscious_memory()
    if not memory_data:
        print("No conscious memory data available.")
        return
    
    # Process based on format
    if args.format == 'summary':
        print_summary(memory_data, args.limit)
    elif args.format == 'insights':
        print_insights(memory_data, args.limit)
    elif args.format == 'full':
        print_full(memory_data, args.limit)
    elif args.format == 'json':
        print(json.dumps(memory_data, indent=args.json_indent))
    elif args.format == 'prompt':
        print_llm_prompt(memory_data)

if __name__ == "__main__":
    main()