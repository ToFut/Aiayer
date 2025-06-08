#!/usr/bin/env python3
"""
Memory Test Tool - Add test memories to trigger notifications

Usage:
  python add_test_memory.py [shopping|form|code|docs]

This will add test memory items for the specified scenario.
"""

import sys
import asyncio
import logging
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("add_test_memory")

def get_shopping_memory():
    """Get e-commerce shopping memory items"""
    web_memory = {
        "type": "web_content",
        "url": "https://www.example-shop.com/products/smartphone",
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
    
    app_memory = {
        "type": "application",
        "application": "Chrome",
        "title": "Latest Smartphone XYZ - Chrome",
        "searchable_text": "Browser window showing smartphone product page",
        "timestamp": time.time(),
        "source": "process_sensor"
    }
    
    return [web_memory, app_memory]

def get_form_memory():
    """Get form filling memory items"""
    web_memory = {
        "type": "web_content",
        "url": "https://www.example-service.com/signup",
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
    
    app_memory = {
        "type": "application",
        "application": "Chrome",
        "title": "Create Account - Example Service - Chrome",
        "searchable_text": "Browser window showing signup form",
        "timestamp": time.time(),
        "source": "process_sensor"
    }
    
    return [web_memory, app_memory]

def get_code_memory():
    """Get programming code memory items"""
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
    
    return [code_memory_1, code_memory_2]

def get_docs_memory():
    """Get documentation reading memory items"""
    web_memory = {
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
    
    app_memory = {
        "type": "application",
        "application": "Chrome",
        "title": "Authentication API - Developer Documentation - Chrome",
        "searchable_text": "Browser window showing API documentation",
        "timestamp": time.time(),
        "source": "process_sensor"
    }
    
    return [web_memory, app_memory]

async def add_memory_items(memory_type):
    """Add memory items based on type"""
    try:
        # Import memory components
        from memory.memory_system import MemorySystem
        
        # Create memory system instance
        memory_system = MemorySystem()
        logger.info(f"Created memory system")
        
        # Get memory items based on type
        if memory_type == "shopping":
            memory_items = get_shopping_memory()
            scenario = "E-commerce Shopping"
        elif memory_type == "form":
            memory_items = get_form_memory()
            scenario = "Form Filling"
        elif memory_type == "code":
            memory_items = get_code_memory()
            scenario = "Programming Activity"
        elif memory_type == "docs":
            memory_items = get_docs_memory()
            scenario = "Documentation Reading"
        else:
            logger.error(f"Unknown memory type: {memory_type}")
            return False
        
        # Add memory items
        logger.info(f"Adding {len(memory_items)} memory items for scenario: {scenario}")
        for i, item in enumerate(memory_items):
            memory_system.short_term_memory.append(item)
            logger.info(f"Added memory item {i+1}: {item.get('type')} - {item.get('title')}")
        
        logger.info(f"Successfully added {len(memory_items)} memory items")
        logger.info("The Memory Trigger Service should detect these items in its next cycle (typically within 60 seconds)")
        logger.info("If the frontend overlay is running, it should display notifications about this content")
        
        return True
    
    except Exception as e:
        logger.error(f"Error adding memory items: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main function"""
    # Get memory type from command line
    if len(sys.argv) < 2:
        print("Please specify a memory type: shopping, form, code, or docs")
        print("Example: python add_test_memory.py shopping")
        return False
    
    memory_type = sys.argv[1].lower()
    if memory_type not in ["shopping", "form", "code", "docs"]:
        print(f"Unknown memory type: {memory_type}")
        print("Please choose from: shopping, form, code, or docs")
        return False
    
    return await add_memory_items(memory_type)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        result = asyncio.run(main())
        if result:
            logger.info("✅ Memory items added successfully")
            sys.exit(0)
        else:
            logger.error("❌ Failed to add memory items")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)