#!/usr/bin/env python3
"""
Test script for Enhanced UI Detection System
Validates all the better approaches integrated into the system
"""

import os
import sys
import asyncio
import logging
import time
from typing import Dict, Any, List
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_ui_detection_system import EnhancedUIDetectionSystem
from browser_api_integration import BrowserAPIManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_enhanced_ui_detection")

class EnhancedUIDetectionTester:
    """Test suite for the enhanced UI detection system"""
    
    def __init__(self):
        self.detector = EnhancedUIDetectionSystem()
        self.browser_manager = BrowserAPIManager()
        self.test_results = {
            "accessibility_api": {"available": False, "tested": False, "passed": False},
            "machine_learning": {"available": False, "tested": False, "passed": False},
            "browser_apis": {"available": False, "tested": False, "passed": False},
            "ocr_nlp": {"available": False, "tested": False, "passed": False},
            "integration": {"tested": False, "passed": False}
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test of all detection methods"""
        logger.info("🧪 Starting comprehensive enhanced UI detection test")
        
        # Test 1: Check component availability
        await self._test_component_availability()
        
        # Test 2: Test individual detection methods
        await self._test_accessibility_apis()
        await self._test_machine_learning()
        await self._test_browser_apis()
        await self._test_ocr_nlp()
        
        # Test 3: Test integration
        await self._test_system_integration()
        
        # Generate test report
        self._generate_test_report()
        
        return self.test_results
    
    async def _test_component_availability(self):
        """Test availability of all detection components"""
        logger.info("📋 Testing component availability...")
        
        # Test accessibility API availability
        self.test_results["accessibility_api"]["available"] = self.detector.accessibility_detector.available
        
        # Test ML availability
        self.test_results["machine_learning"]["available"] = self.detector.ml_classifier.available
        
        # Test browser API availability
        self.test_results["browser_apis"]["available"] = self.detector.browser_detector.available
        
        # Test OCR/NLP availability
        self.test_results["ocr_nlp"]["available"] = (
            self.detector.ocr_nlp_detector.ocr_available or 
            self.detector.ocr_nlp_detector.nlp_available
        )
        
        logger.info("✅ Component availability check complete")
    
    async def _test_accessibility_apis(self):
        """Test accessibility API functionality"""
        logger.info("🔍 Testing Accessibility APIs...")
        
        try:
            if not self.detector.accessibility_detector.available:
                logger.warning("⚠️  Accessibility APIs not available")
                return
            
            # Test getting element role
            role = self.detector.accessibility_detector.get_element_role()
            
            self.test_results["accessibility_api"]["tested"] = True
            self.test_results["accessibility_api"]["passed"] = role is not None
            
            if role:
                logger.info(f"✅ Accessibility API test passed - detected role: {role}")
            else:
                logger.warning("⚠️  Accessibility API test completed but no role detected")
                
        except Exception as e:
            logger.error(f"❌ Accessibility API test failed: {e}")
            self.test_results["accessibility_api"]["tested"] = True
            self.test_results["accessibility_api"]["passed"] = False
    
    async def _test_machine_learning(self):
        """Test ML classification functionality"""
        logger.info("🤖 Testing Machine Learning Classification...")
        
        try:
            if not self.detector.ml_classifier.available:
                logger.warning("⚠️  ML classifier not available")
                return
            
            # Test element classification
            test_texts = [
                "Submit button",
                "Enter your email address",
                "Select from dropdown menu",
                "Check this option"
            ]
            
            classifications = []
            for text in test_texts:
                element_type, confidence = self.detector.ml_classifier.classify_element(text)
                classifications.append((text, element_type, confidence))
                logger.info(f"   ML classified '{text}' as '{element_type}' (confidence: {confidence:.2f})")
            
            self.test_results["machine_learning"]["tested"] = True
            self.test_results["machine_learning"]["passed"] = len(classifications) > 0
            
            logger.info("✅ ML classification test passed")
            
        except Exception as e:
            logger.error(f"❌ ML classification test failed: {e}")
            self.test_results["machine_learning"]["tested"] = True
            self.test_results["machine_learning"]["passed"] = False
    
    async def _test_browser_apis(self):
        """Test browser API functionality"""
        logger.info("🌐 Testing Browser APIs...")
        
        try:
            if not self.browser_manager.selenium_available:
                logger.warning("⚠️  Browser APIs not available")
                return
            
            # Test browser detection
            browsers = self.browser_manager.detect_running_browsers()
            logger.info(f"   Detected {len(browsers)} running browsers")
            
            # Test browser connection (non-destructive)
            connection_successful = False
            try:
                # Try to connect to existing browser without starting new one
                connection_successful = self.browser_manager._connect_to_existing_browser("chrome", 9222)
                if connection_successful:
                    logger.info("   ✅ Successfully connected to existing browser")
                    
                    # Test getting DOM elements
                    elements = self.browser_manager.get_native_dom_elements()
                    logger.info(f"   Retrieved {len(elements)} DOM elements")
                    
                    self.browser_manager.close_browser()
                else:
                    logger.info("   ℹ️  No existing browser with debugging available")
                    
            except Exception as e:
                logger.debug(f"   Browser connection test: {e}")
            
            self.test_results["browser_apis"]["tested"] = True
            self.test_results["browser_apis"]["passed"] = len(browsers) > 0 or connection_successful
            
            logger.info("✅ Browser API test completed")
            
        except Exception as e:
            logger.error(f"❌ Browser API test failed: {e}")
            self.test_results["browser_apis"]["tested"] = True
            self.test_results["browser_apis"]["passed"] = False
    
    async def _test_ocr_nlp(self):
        """Test OCR + NLP functionality"""
        logger.info("📝 Testing OCR + NLP...")
        
        try:
            # Create a simple test image with text
            test_image_path = await self._create_test_image()
            
            if not test_image_path:
                logger.warning("⚠️  Could not create test image")
                return
            
            # Test OCR
            ocr_results = self.detector.ocr_nlp_detector.extract_text_content(test_image_path)
            logger.info(f"   OCR extracted: '{ocr_results.get('text', '')[:50]}...'")
            
            # Test NLP
            if ocr_results.get("text"):
                nlp_results = self.detector.ocr_nlp_detector.analyze_intent(ocr_results["text"])
                logger.info(f"   NLP detected intent: {nlp_results.get('intent', 'unknown')}")
            
            self.test_results["ocr_nlp"]["tested"] = True
            self.test_results["ocr_nlp"]["passed"] = bool(ocr_results.get("text"))
            
            # Clean up test image
            if os.path.exists(test_image_path):
                os.remove(test_image_path)
            
            logger.info("✅ OCR + NLP test completed")
            
        except Exception as e:
            logger.error(f"❌ OCR + NLP test failed: {e}")
            self.test_results["ocr_nlp"]["tested"] = True
            self.test_results["ocr_nlp"]["passed"] = False
    
    async def _create_test_image(self) -> str:
        """Create a simple test image with text"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple image with text
            img = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use default font
            try:
                font = ImageFont.load_default()
            except:
                font = None
            
            # Draw test text
            test_text = "Submit Button\nEnter Text Here\nSearch"
            draw.text((50, 50), test_text, fill='black', font=font)
            
            # Save test image
            test_image_path = "/tmp/test_ui_image.png"
            img.save(test_image_path)
            
            return test_image_path
            
        except Exception as e:
            logger.error(f"Error creating test image: {e}")
            return None
    
    async def _test_system_integration(self):
        """Test the integrated system with a mock screenshot"""
        logger.info("🔗 Testing System Integration...")
        
        try:
            # Create a test image
            test_image_path = await self._create_test_image()
            
            if not test_image_path:
                logger.warning("⚠️  Could not create test image for integration test")
                return
            
            # Run enhanced detection
            app_context = {"app_name": "Test Application", "view_name": "Test View"}
            result = await self.detector.enhanced_detect_ui_elements(test_image_path, app_context)
            
            # Validate results
            integration_success = (
                result.timestamp > 0 and
                result.app_name == "Test Application" and
                len(result.detection_methods_used) > 0
            )
            
            self.test_results["integration"]["tested"] = True
            self.test_results["integration"]["passed"] = integration_success
            
            logger.info(f"   Integration test results:")
            logger.info(f"   - Elements detected: {len(result.elements)}")
            logger.info(f"   - Detection methods used: {result.detection_methods_used}")
            logger.info(f"   - App name: {result.app_name}")
            
            # Clean up
            if os.path.exists(test_image_path):
                os.remove(test_image_path)
            
            if integration_success:
                logger.info("✅ System integration test passed")
            else:
                logger.warning("⚠️  System integration test completed with issues")
                
        except Exception as e:
            logger.error(f"❌ System integration test failed: {e}")
            self.test_results["integration"]["tested"] = True
            self.test_results["integration"]["passed"] = False
    
    def _generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*60)
        logger.info("📊 ENHANCED UI DETECTION SYSTEM TEST REPORT")
        logger.info("="*60)
        
        total_tests = 0
        passed_tests = 0
        
        for component, results in self.test_results.items():
            if results.get("tested", False):
                total_tests += 1
                if results.get("passed", False):
                    passed_tests += 1
                    status = "✅ PASSED"
                else:
                    status = "❌ FAILED"
            else:
                status = "⏭️  SKIPPED" if not results.get("available", True) else "❓ NOT TESTED"
            
            component_name = component.replace("_", " ").title()
            available = "✅" if results.get("available", False) else "❌"
            
            logger.info(f"{component_name:20} | Available: {available} | Status: {status}")
        
        logger.info("-" * 60)
        logger.info(f"SUMMARY: {passed_tests}/{total_tests} tests passed")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            logger.info(f"SUCCESS RATE: {success_rate:.1f}%")
        
        logger.info("="*60)
        
        # Recommendations
        logger.info("🔧 RECOMMENDATIONS:")
        
        if not self.test_results["accessibility_api"]["available"]:
            logger.info("- Install accessibility libraries for your platform")
        
        if not self.test_results["machine_learning"]["available"]:
            logger.info("- Install scikit-learn for ML classification: pip install scikit-learn")
        
        if not self.test_results["browser_apis"]["available"]:
            logger.info("- Install selenium for browser automation: pip install selenium")
        
        if not self.test_results["ocr_nlp"]["available"]:
            logger.info("- Install OCR/NLP libraries: pip install easyocr spacy")
        
        logger.info("="*60)

async def main():
    """Main test function"""
    tester = EnhancedUIDetectionTester()
    
    print("🚀 Starting Enhanced UI Detection System Test Suite")
    print("This will test all the better approaches that have been integrated:")
    print("1. Accessibility APIs")
    print("2. Machine Learning Models") 
    print("3. Browser/OS APIs")
    print("4. OCR + NLP Understanding")
    print("5. System Integration")
    print()
    
    start_time = time.time()
    results = await tester.run_comprehensive_test()
    elapsed_time = time.time() - start_time
    
    print(f"\n⏱️  Total test time: {elapsed_time:.2f} seconds")
    print("🎯 Test suite completed!")
    
    return results

if __name__ == "__main__":
    try:
        results = asyncio.run(main())
        
        # Exit with appropriate code
        passed_tests = sum(1 for r in results.values() if r.get("passed", False))
        total_tests = sum(1 for r in results.values() if r.get("tested", False))
        
        if total_tests > 0 and passed_tests == total_tests:
            sys.exit(0)  # All tests passed
        elif passed_tests > 0:
            sys.exit(1)  # Some tests passed
        else:
            sys.exit(2)  # No tests passed
            
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"💥 Test suite failed with error: {e}")
        sys.exit(1)