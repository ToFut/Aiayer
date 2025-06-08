"""
Test script for memory trigger service with real-world case studies
This script adds realistic memory items to trigger notifications in the frontend.
"""

import asyncio
import time
import logging
import json
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("test_memory_cases")

# Try to import memory components
try:
    from memory.memory_system import MemorySystem
    from memory.memory_trigger_service import MemoryTriggerService
    IMPORTS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Import error: {e}")
    IMPORTS_AVAILABLE = False

async def case_study_1_web_browsing(memory_system):
    """
    CASE STUDY 1: Web Browsing - e-commerce
    User is browsing an e-commerce site looking at products
    """
    logger.info("===== CASE STUDY 1: E-commerce Browsing =====")
    
    # Add web page memory item for product browsing
    ecommerce_memory = {
        "type": "web_content",
        "url": "https://example-shop.com/products/smartphone",
        "title": "Latest Smartphone XYZ - High Performance Camera",
        "searchable_text": """
        Latest Smartphone XYZ with Revolutionary Camera

        Price: $799.99
        Availability: In Stock
        Free Shipping
        
        Product Features:
        - 6.7-inch Super AMOLED display
        - Triple camera system with 108MP main sensor
        - 5G connectivity
        - All-day battery life
        - 256GB storage
        
        Customer Reviews:
        ★★★★☆ 4.7/5 - Based on 203 reviews
        
        Add to Cart | Buy Now | Compare
        """,
        "timestamp": time.time(),
        "source": "web_browser"
    }
    
    # Add to memory
    memory_system.short_term_memory.append(ecommerce_memory)
    logger.info("Added e-commerce product browsing memory")
    
    # Add application memory
    app_memory = {
        "type": "application",
        "application": "Chrome",
        "title": "Latest Smartphone XYZ - Chrome",
        "searchable_text": "Browser window showing smartphone product page",
        "timestamp": time.time(),
        "source": "process_sensor"
    }
    
    # Add to memory
    memory_system.short_term_memory.append(app_memory)
    logger.info("Added application memory for e-commerce browsing")
    
    return True

async def case_study_2_form_filling(memory_system):
    """
    CASE STUDY 2: Form Filling
    User is filling out a registration form
    """
    logger.info("===== CASE STUDY 2: Form Filling =====")
    
    # Add web page memory item for form
    form_memory = {
        "type": "web_content",
        "url": "https://example-service.com/signup",
        "title": "Create Account - Example Service",
        "searchable_text": """
        Create Your Account
        
        Join thousands of users who trust our service.
        
        First Name: 
        Last Name:
        Email Address:
        Password:
        Confirm Password:
        
        □ I agree to the Terms of Service and Privacy Policy
        
        [Create Account]   [Cancel]
        
        Already have an account? Sign in here.
        """,
        "timestamp": time.time(),
        "source": "web_browser"
    }
    
    # Add to memory
    memory_system.short_term_memory.append(form_memory)
    logger.info("Added form filling memory")
    
    # Add application memory
    app_memory = {
        "type": "application",
        "application": "Chrome",
        "title": "Create Account - Example Service - Chrome",
        "searchable_text": "Browser window showing signup form",
        "timestamp": time.time(),
        "source": "process_sensor"
    }
    
    # Add to memory
    memory_system.short_term_memory.append(app_memory)
    logger.info("Added application memory for form filling")
    
    return True

async def case_study_3_programming_activity(memory_system):
    """
    CASE STUDY 3: Programming Activity
    User is working on coding with repetitive patterns
    """
    logger.info("===== CASE STUDY 3: Programming Activity =====")
    
    # First code editing session
    code_memory_1 = {
        "type": "application_activity",
        "application": "Visual Studio Code",
        "title": "project.py - Visual Studio Code",
        "searchable_text": """
        def process_data(data):
            results = []
            for item in data:
                if item['status'] == 'active':
                    processed = transform_item(item)
                    results.append(processed)
            return results
            
        def transform_item(item):
            return {
                'id': item['id'],
                'name': item['name'],
                'value': item['value'] * 1.5,
                'status': 'processed'
            }
        """,
        "timestamp": time.time() - 300,  # 5 minutes ago
        "source": "process_sensor"
    }
    
    # Add to memory
    memory_system.short_term_memory.append(code_memory_1)
    
    # Second code editing session (repetitive pattern)
    code_memory_2 = {
        "type": "application_activity",
        "application": "Visual Studio Code",
        "title": "data_handlers.py - Visual Studio Code",
        "searchable_text": """
        def filter_data(data):
            results = []
            for item in data:
                if item['category'] == 'important':
                    filtered = clean_item(item)
                    results.append(filtered)
            return results
            
        def clean_item(item):
            return {
                'id': item['id'],
                'name': item['name'],
                'score': item['score'] * 2.0,
                'category': 'filtered'
            }
        """,
        "timestamp": time.time() - 60,  # 1 minute ago
        "source": "process_sensor"
    }
    
    # Add to memory
    memory_system.short_term_memory.append(code_memory_2)
    logger.info("Added programming activity memories showing repetitive pattern")
    
    return True

async def case_study_4_documentation_reading(memory_system):
    """
    CASE STUDY 4: Documentation Reading
    User is reading technical documentation
    """
    logger.info("===== CASE STUDY 4: Documentation Reading =====")
    
    # Add web page memory item for documentation
    docs_memory = {
        "type": "web_content",
        "url": "https://docs.example.com/api/authentication",
        "title": "Authentication API - Developer Documentation",
        "searchable_text": """
        Authentication API Reference
        
        This guide explains how to authenticate with our API using OAuth 2.0.
        
        Authentication Endpoints:
        
        POST /oauth/token
        
        Request Parameters:
        - client_id (required): Your application's client ID
        - client_secret (required): Your application's client secret
        - grant_type (required): Must be "authorization_code" or "refresh_token"
        - code (required for authorization_code): The authorization code
        - refresh_token (required for refresh_token): The refresh token
        
        Example Request:
        ```
        curl -X POST https://api.example.com/oauth/token 
          -d client_id=YOUR_CLIENT_ID 
          -d client_secret=YOUR_CLIENT_SECRET 
          -d grant_type=authorization_code 
          -d code=AUTH_CODE_HERE
        ```
        
        Response:
        ```json
        {
          "access_token": "ACCESS_TOKEN",
          "token_type": "bearer",
          "expires_in": 3600,
          "refresh_token": "REFRESH_TOKEN"
        }
        ```
        """,
        "timestamp": time.time(),
        "source": "web_browser"
    }
    
    # Add to memory
    memory_system.short_term_memory.append(docs_memory)
    logger.info("Added documentation reading memory")
    
    # Add application memory
    app_memory = {
        "type": "application",
        "application": "Chrome",
        "title": "Authentication API - Developer Documentation - Chrome",
        "searchable_text": "Browser window showing API documentation",
        "timestamp": time.time(),
        "source": "process_sensor"
    }
    
    # Add to memory
    memory_system.short_term_memory.append(app_memory)
    logger.info("Added application memory for documentation reading")
    
    return True

async def run_all_case_studies(memory_system, wait_time=70):
    """Run all case studies with pauses between them"""
    
    # Run each case study with time for detection
    await case_study_1_web_browsing(memory_system)
    logger.info(f"Waiting {wait_time} seconds for detection...")
    await asyncio.sleep(wait_time)
    
    await case_study_2_form_filling(memory_system)
    logger.info(f"Waiting {wait_time} seconds for detection...")
    await asyncio.sleep(wait_time)
    
    await case_study_3_programming_activity(memory_system)
    logger.info(f"Waiting {wait_time} seconds for detection...")
    await asyncio.sleep(wait_time)
    
    await case_study_4_documentation_reading(memory_system)
    logger.info(f"Waiting {wait_time} seconds for detection...")
    await asyncio.sleep(wait_time)
    
    logger.info("All case studies completed!")

async def main():
    """Main test function"""
    if not IMPORTS_AVAILABLE:
        logger.error("Required imports not available. Cannot run test.")
        return False
    
    try:
        logger.info("🚀 Starting memory case studies test")
        
        # Create memory system
        memory_system = MemorySystem()
        logger.info("Created memory system")
        
        # Run all case studies
        await run_all_case_studies(memory_system)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    try:
        result = asyncio.run(main())
        if result:
            logger.info("✅ Test completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Test failed")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)