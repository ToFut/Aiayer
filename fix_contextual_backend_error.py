#!/usr/bin/env python3
"""
Fix for ContextualAIBackend _try_agnostic_deep_data_access error
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_backend_method():
    """Check if the method exists in the backend"""
    try:
        from enhanced_enterprise_backend_with_context import ContextualAIBackend
        
        # Create backend instance
        backend = ContextualAIBackend()
        
        # Check if the method exists
        if hasattr(backend, '_try_agnostic_deep_data_access'):
            logger.info("✅ Method _try_agnostic_deep_data_access exists in ContextualAIBackend")
            
            # Check if it's callable
            if callable(getattr(backend, '_try_agnostic_deep_data_access')):
                logger.info("✅ Method is callable")
            else:
                logger.error("❌ Method exists but is not callable")
        else:
            logger.error("❌ Method _try_agnostic_deep_data_access NOT found in ContextualAIBackend")
            
            # List all available methods
            methods = [method for method in dir(backend) if not method.startswith('__')]
            logger.info(f"Available methods: {methods[:10]}...")  # Show first 10
            
            # Check if there are similar methods
            similar = [method for method in methods if 'agnostic' in method or 'deep' in method]
            if similar:
                logger.info(f"Similar methods found: {similar}")
    
    except Exception as e:
        logger.error(f"Error checking backend: {e}")

def fix_backend_method():
    """Add the missing method if needed"""
    try:
        # Check the file content
        with open('/Users/segevbin/Desktop/SensAI/Aiayer/enhanced_enterprise_backend_with_context.py', 'r') as f:
            content = f.read()
        
        # Check if method definition exists
        if 'def _try_agnostic_deep_data_access' in content:
            logger.info("✅ Method definition found in file")
            
            # Check indentation
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if '_try_agnostic_deep_data_access' in line and 'def' in line:
                    # Check if properly indented (should be 4 spaces for class method)
                    if line.startswith('    async def '):
                        logger.info(f"✅ Method properly indented at line {i+1}")
                    else:
                        logger.error(f"❌ Method indentation issue at line {i+1}: '{line[:20]}...'")
                    break
        else:
            logger.error("❌ Method definition NOT found in file")
            
    except Exception as e:
        logger.error(f"Error checking file: {e}")

def restart_backend_suggestion():
    """Suggest how to restart the backend"""
    logger.info("\n💡 SOLUTION STEPS:")
    logger.info("1. Stop current backend: pkill -f 'enhanced_enterprise_backend'")
    logger.info("2. Restart with: ./START_ENHANCED_SYSTEM.sh")
    logger.info("3. Or run directly: python enhanced_enterprise_backend_with_context.py")
    logger.info("4. Test with: python final_performance_validation.py")

if __name__ == "__main__":
    logger.info("🔧 Fixing ContextualAIBackend Error")
    logger.info("="*40)
    
    check_backend_method()
    fix_backend_method()
    restart_backend_suggestion()