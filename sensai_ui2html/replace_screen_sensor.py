#!/usr/bin/env python3
"""
Script to replace existing screen sensor usage with UI2HTML system
"""

import os
import re
from pathlib import Path

def find_screen_sensor_usage(root_dir: str = "."):
    """
    Find files that use screen sensors.
    
    Args:
        root_dir: Root directory to search
        
    Returns:
        List of files with screen sensor usage
    """
    python_files = []
    
    for root, dirs, files in os.walk(root_dir):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', 'node_modules', 'chroma_db']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Check for screen sensor imports
                    if any(pattern in content for pattern in [
                        'from sensors.screen_sensor',
                        'from sensors.basic_screen_sensor',
                        'import screen_sensor',
                        'ScreenSensor',
                        'BasicScreenSensor'
                    ]):
                        python_files.append(file_path)
                        
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return python_files

def show_replacement_examples():
    """Show examples of how to replace screen sensor usage."""
    
    examples = [
        {
            "title": "Basic Import Replacement",
            "before": """from sensors.screen_sensor import ScreenSensor
from sensors.basic_screen_sensor import BasicScreenSensor""",
            "after": """from sensai_ui2html.integration import ScreenSensorReplacement
# or for direct functions
from sensai_ui2html.integration import capture_screen"""
        },
        {
            "title": "Sensor Creation",
            "before": """sensor = ScreenSensor()
sensor = BasicScreenSensor(config)""",
            "after": """sensor = ScreenSensorReplacement()
sensor = ScreenSensorReplacement(config)"""
        },
        {
            "title": "Screen Capture",
            "before": """screen_data = sensor.capture_screen()
image_data = screen_data['image_data']""",
            "after": """screen_data = sensor.capture_screen()
html_content = screen_data['html_content']
ui_tree = screen_data['ui_tree']"""
        },
        {
            "title": "Enhanced Capabilities",
            "before": """# No semantic search available
# No memory persistence
# No HTML generation""",
            "after": """# Semantic memory query
results = sensor.query_ui_memory("login button", n_results=5)

# HTML generation
html_content = screen_data['html_content']

# Memory persistence (automatic)
# Snapshots stored in ChromaDB"""
        }
    ]
    
    print("=== Screen Sensor Replacement Examples ===\n")
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['title']}")
        print("-" * 50)
        print("BEFORE:")
        print(example['before'])
        print("\nAFTER:")
        print(example['after'])
        print("\n" + "="*60 + "\n")

def generate_migration_script(file_path: str):
    """
    Generate a migration script for a specific file.
    
    Args:
        file_path: Path to the file to migrate
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Apply replacements
        new_content = content
        
        # Replace imports
        new_content = re.sub(
            r'from sensors\.screen_sensor import ScreenSensor',
            'from sensai_ui2html.integration import ScreenSensorReplacement',
            new_content
        )
        new_content = re.sub(
            r'from sensors\.basic_screen_sensor import BasicScreenSensor',
            'from sensai_ui2html.integration import ScreenSensorReplacement',
            new_content
        )
        
        # Replace class instantiations
        new_content = re.sub(
            r'ScreenSensor\(\)',
            'ScreenSensorReplacement()',
            new_content
        )
        new_content = re.sub(
            r'BasicScreenSensor\(',
            'ScreenSensorReplacement(',
            new_content
        )
        
        # Generate migration file
        migration_file = file_path + '.migrated'
        with open(migration_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"Generated migration file: {migration_file}")
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    """Main function to help with migration."""
    print("SensAI.UI2HTMLMemory - Screen Sensor Migration Helper\n")
    
    # Show examples
    show_replacement_examples()
    
    # Find files with screen sensor usage
    print("=== Finding Files with Screen Sensor Usage ===\n")
    files = find_screen_sensor_usage()
    
    if files:
        print(f"Found {len(files)} files with screen sensor usage:\n")
        for i, file_path in enumerate(files, 1):
            print(f"{i}. {file_path}")
        
        print(f"\nTo migrate these files:")
        print("1. Install dependencies: pip install uiautomation chromadb openai")
        print("2. Replace imports and class names as shown in examples above")
        print("3. Update any code that expects image data to use HTML/UI tree data")
        print("4. Test the migration with the integration tests")
        
        # Offer to generate migration files
        response = input("\nGenerate migration files for these files? (y/n): ")
        if response.lower() == 'y':
            for file_path in files:
                generate_migration_script(file_path)
            print("\nMigration files generated. Review them before applying.")
    else:
        print("No files with screen sensor usage found.")
    
    print("\n=== Migration Steps ===")
    print("1. Install dependencies: pip install uiautomation chromadb openai")
    print("2. Replace imports: sensors.screen_sensor → sensai_ui2html.integration")
    print("3. Replace classes: ScreenSensor → ScreenSensorReplacement")
    print("4. Update data handling: image_data → html_content + ui_tree")
    print("5. Add semantic queries: sensor.query_ui_memory()")
    print("6. Test with: python sensai_ui2html/test_integration.py")
    
    print("\n=== Benefits ===")
    print("✓ Semantic UI understanding")
    print("✓ HTML generation for LLMs")
    print("✓ Vector memory storage")
    print("✓ Natural language queries")
    print("✓ Better integration with web systems")

if __name__ == "__main__":
    main() 