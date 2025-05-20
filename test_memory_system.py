#!/usr/bin/env python3
"""
Test script for verifying the Conscious Memory System functionality
This tests the core memory update functions and data integration
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
logger = logging.getLogger("memory.test")

# Import memory update module
script_dir = os.path.dirname(os.path.abspath(__file__))
memory_dir = os.path.join(script_dir, "memory")

# Add memory directory to Python path
import sys
sys.path.append(script_dir)

# Set paths
MEMORY_DIR = os.path.join(script_dir, "memory")
CACHE_DIR = os.path.join(script_dir, "cache")
CONSCIOUS_FILE = os.path.join(MEMORY_DIR, "conscious.json")
SCREEN_CACHE_FILE = os.path.join(CACHE_DIR, "screen_sensor", "last_screen.json")
PROCESS_CACHE_FILE = os.path.join(CACHE_DIR, "process_sensor", "process_cache.json")
FILE_CACHE_FILE = os.path.join(CACHE_DIR, "file_sensor", "last_file.json")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test the Conscious Memory System')
    parser.add_argument('--full', action='store_true', 
                      help='Run a full test with all components')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose output')
    return parser.parse_args()

def check_file_exists(file_path, description="file"):
    """Check if a file exists and log the result"""
    if os.path.exists(file_path):
        logger.info(f"✅ {description} exists: {file_path}")
        return True
    else:
        logger.error(f"❌ {description} does not exist: {file_path}")
        return False

def check_directory_exists(dir_path, description="directory"):
    """Check if a directory exists and log the result"""
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        logger.info(f"✅ {description} exists: {dir_path}")
        return True
    else:
        logger.error(f"❌ {description} does not exist: {dir_path}")
        return False

def load_json_file(file_path):
    """Load a JSON file and return its contents"""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"File does not exist: {file_path}")
            return None
            
        with open(file_path, 'r') as f:
            data = json.load(f)
            logger.debug(f"Loaded {len(json.dumps(data))} bytes from {file_path}")
            return data
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

def check_sensor_data():
    """Check if sensor data files exist and contain valid data"""
    logger.info("Checking sensor data files...")
    
    # Check screen sensor cache
    screen_data = None
    if check_file_exists(SCREEN_CACHE_FILE, "Screen cache file"):
        screen_data = load_json_file(SCREEN_CACHE_FILE)
        if screen_data:
            logger.info(f"✅ Screen data is valid with timestamp: {screen_data.get('timestamp', 'unknown')}")
        else:
            logger.error("❌ Screen data is invalid or empty")
    
    # Check process sensor cache
    process_data = None
    if check_file_exists(PROCESS_CACHE_FILE, "Process cache file"):
        process_data = load_json_file(PROCESS_CACHE_FILE)
        if process_data:
            active_processes = process_data.get("active_processes", [])
            logger.info(f"✅ Process data is valid with {len(active_processes)} processes")
        else:
            logger.error("❌ Process data is invalid or empty")
    
    # Check file sensor cache
    file_data = None
    if check_file_exists(FILE_CACHE_FILE, "File cache file"):
        file_data = load_json_file(FILE_CACHE_FILE)
        if file_data:
            events = file_data.get("events", [])
            logger.info(f"✅ File data is valid with {len(events)} events")
        else:
            logger.error("❌ File data is invalid or empty")
    
    return screen_data, process_data, file_data

def check_conscious_memory():
    """Check if conscious memory file exists and contains valid data"""
    logger.info("Checking conscious memory file...")
    
    if check_file_exists(CONSCIOUS_FILE, "Conscious memory file"):
        conscious_data = load_json_file(CONSCIOUS_FILE)
        if conscious_data:
            # Check sensor buffers
            sensor_buffers = conscious_data.get("sensor_buffers", {})
            screen_buffer = sensor_buffers.get("screen", [])
            process_buffer = sensor_buffers.get("process", [])
            file_buffer = sensor_buffers.get("file", [])
            
            logger.info(f"✅ Conscious memory contains {len(screen_buffer)} screen entries, " +
                        f"{len(process_buffer)} process entries, " +
                        f"{len(file_buffer)} file entries")
            
            # Check insights
            insights = conscious_data.get("insights", [])
            logger.info(f"✅ Conscious memory contains {len(insights)} insights")
            
            # Check last update time
            system_state = conscious_data.get("system_state", {})
            last_update = system_state.get("last_update", "unknown")
            logger.info(f"✅ Conscious memory last updated at: {last_update}")
            
            return conscious_data
        else:
            logger.error("❌ Conscious memory data is invalid or empty")
            return None
    else:
        return None

def test_memory_update():
    """Test the memory update function by importing and running it"""
    try:
        logger.info("Testing memory update function...")
        
        # Import the update module
        sys.path.append(MEMORY_DIR)
        from update_conscious import update_conscious_memory, generate_llm_prompt
        
        # Run the update function
        logger.info("Running update_conscious_memory function...")
        conscious = update_conscious_memory()
        
        if conscious:
            logger.info(f"✅ Memory update successful")
            
            # Generate LLM prompt
            prompt = generate_llm_prompt(conscious)
            prompt_lines = prompt.strip().split('\n')
            logger.info(f"✅ Generated LLM prompt with {len(prompt_lines)} lines")
            logger.debug(f"Prompt: {prompt[:200]}...")
            
            return True
        else:
            logger.error("❌ Memory update failed")
            return False
    except ImportError as e:
        logger.error(f"❌ Failed to import update_conscious module: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing memory update: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def run_full_test():
    """Run a full test of all memory system components"""
    # These are all the components to test
    components = {
        "directories": [
            (MEMORY_DIR, "Memory directory"),
            (CACHE_DIR, "Cache directory"),
            (os.path.join(CACHE_DIR, "screen_sensor"), "Screen sensor cache directory"),
            (os.path.join(CACHE_DIR, "process_sensor"), "Process sensor cache directory"),
            (os.path.join(CACHE_DIR, "file_sensor"), "File sensor cache directory")
        ],
        "files": [
            (os.path.join(MEMORY_DIR, "update_conscious.py"), "Memory update script"),
            (SCREEN_CACHE_FILE, "Screen sensor cache file"),
            (PROCESS_CACHE_FILE, "Process sensor cache file"),
            (FILE_CACHE_FILE, "File sensor cache file")
        ],
        "functions": [
            (check_sensor_data, "Sensor data check"),
            (check_conscious_memory, "Conscious memory check"),
            (test_memory_update, "Memory update function test")
        ]
    }
    
    logger.info("Running full memory system test...")
    logger.info("=" * 50)
    
    # Check directories
    logger.info("\nChecking directories...")
    all_dirs_exist = True
    for dir_path, description in components["directories"]:
        if not check_directory_exists(dir_path, description):
            all_dirs_exist = False
    
    # Check files
    logger.info("\nChecking files...")
    all_files_exist = True
    for file_path, description in components["files"]:
        if not check_file_exists(file_path, description):
            all_files_exist = False
    
    # Run function tests
    logger.info("\nRunning functional tests...")
    all_tests_passed = True
    for func, description in components["functions"]:
        logger.info(f"Running {description}...")
        try:
            result = func()
            if result is False:  # Only count boolean False as failure
                all_tests_passed = False
                logger.error(f"❌ {description} failed")
            else:
                logger.info(f"✅ {description} completed")
        except Exception as e:
            all_tests_passed = False
            logger.error(f"❌ {description} failed with error: {e}")
    
    # Print summary
    logger.info("\n" + "=" * 50)
    logger.info("Test Summary:")
    logger.info(f"Directories: {'✅ All OK' if all_dirs_exist else '❌ Some missing'}")
    logger.info(f"Files: {'✅ All OK' if all_files_exist else '❌ Some missing'}")
    logger.info(f"Function tests: {'✅ All passed' if all_tests_passed else '❌ Some failed'}")
    
    overall_status = all_dirs_exist and all_files_exist and all_tests_passed
    logger.info("\nOverall Status: " + ("✅ PASSED" if overall_status else "❌ FAILED"))
    logger.info("=" * 50)
    
    return overall_status

def main():
    """Main test function"""
    args = parse_args()
    
    # Set log level based on verbosity
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    
    logger.info(f"Starting memory system test at {datetime.now().isoformat()}")
    
    if args.full:
        run_full_test()
    else:
        # Run basic tests
        check_directory_exists(MEMORY_DIR, "Memory directory")
        check_directory_exists(CACHE_DIR, "Cache directory")
        check_sensor_data()
        check_conscious_memory()
    
    logger.info(f"Test completed at {datetime.now().isoformat()}")

if __name__ == "__main__":
    main()