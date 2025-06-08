#!/usr/bin/env python3
"""
Comprehensive WebSocket Handler Fix Script
Adds path=None parameter to all WebSocket handlers in the codebase
to fix common "received 1000 (OK); then sent 1000 (OK)" errors
"""

import os
import re
import glob
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_websocket_handlers(directory='.', dry_run=False):
    """
    Scan all Python files in the given directory and fix WebSocket handlers
    by adding a path=None parameter if it's missing.
    """
    total_files = 0
    fixed_files = 0
    error_files = 0
    skipped_files = 0
    
    # Pattern to match async WebSocket handlers without path parameter
    handler_pattern = re.compile(r'async\s+def\s+(handle_?(?:websocket|client|message|connection|ws))?\s*\(\s*(?:self,\s*)?(\w+)\s*\):')
    
    # Pattern to match WebSocket handlers that already have path parameter
    existing_path_pattern = re.compile(r'async\s+def\s+\w+\s*\(\s*(?:self,\s*)?\w+\s*,\s*path(?:\s*=\s*None)?\s*\):')
    
    # Walk through all Python files in the directory
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                total_files += 1
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Skip files that don't use websockets
                    if 'import websockets' not in content and 'from websockets' not in content:
                        skipped_files += 1
                        continue
                    
                    # Check if the file has WebSocket serve calls
                    if 'websockets.serve(' in content or '.serve(' in content:
                        # Find handlers that need fixing
                        matches = handler_pattern.finditer(content)
                        has_changes = False
                        new_content = content
                        
                        for match in matches:
                            # Check if this handler already has a path parameter
                            if existing_path_pattern.search(content[match.start():match.start() + 100]):
                                continue
                            
                            # Extract handler name and websocket param
                            handler_name = match.group(1) or "handler"  # Default to "handler" if not named
                            websocket_param = match.group(2)
                            
                            # Build the replacement with path=None
                            old_def = match.group(0)
                            new_def = f'async def {handler_name}({websocket_param}, path=None):'
                            
                            # Make replacement
                            new_content = new_content.replace(old_def, new_def)
                            has_changes = True
                            
                            logger.info(f"In {file_path}: Fixed handler '{handler_name}' by adding path=None parameter")
                        
                        # Write changes back to file
                        if has_changes:
                            if not dry_run:
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(new_content)
                                logger.info(f"✅ Updated {file_path}")
                            else:
                                logger.info(f"🔍 Would update {file_path} (dry run)")
                            fixed_files += 1
                
                except Exception as e:
                    logger.error(f"❌ Error processing {file_path}: {e}")
                    error_files += 1
    
    # Summary
    logger.info(f"\n===== SUMMARY =====")
    logger.info(f"Total Python files scanned: {total_files}")
    logger.info(f"Files fixed: {fixed_files}")
    logger.info(f"Files skipped (no WebSockets): {skipped_files}")
    logger.info(f"Files with errors: {error_files}")
    if dry_run:
        logger.info("THIS WAS A DRY RUN. No files were actually modified.")
    
    return fixed_files

def main():
    parser = argparse.ArgumentParser(description='Fix WebSocket handlers by adding path=None parameter')
    parser.add_argument('--directory', '-d', type=str, default='.', help='Directory to scan (default: current directory)')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without making changes')
    args = parser.parse_args()
    
    logger.info(f"🔍 Starting WebSocket handler fix in {os.path.abspath(args.directory)}")
    logger.info(f"{'🔍 DRY RUN MODE' if args.dry_run else '🔧 LIVE MODE'}")
    
    fixed_count = fix_websocket_handlers(args.directory, args.dry_run)
    
    if fixed_count > 0:
        logger.info(f"✅ Fixed {fixed_count} files with WebSocket handler issues")
        logger.info("🔄 Please restart all WebSocket servers to apply the fixes")
    else:
        logger.info("ℹ️ No files needed fixing")

if __name__ == "__main__":
    main()