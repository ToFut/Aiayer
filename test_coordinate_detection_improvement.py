#!/usr/bin/env python3
"""
Coordinate Detection Improvement Test
Tests and improves coordinate detection for UI element interactions
"""

import asyncio
import websockets
import json
import time
import uuid
from datetime import datetime

class CoordinateDetectionTest:
    def __init__(self):
        self.backend_url = "ws://localhost:8767"
        self.session_id = str(uuid.uuid4())
        self.results = []

    async def test_coordinate_detection(self):
        """Test coordinate detection capabilities"""
        try:
            print(f"🎯 Starting Coordinate Detection Test at {datetime.now()}")
            print("=" * 60)
            
            async with websockets.connect(self.backend_url) as websocket:
                print("✅ Connected to backend")
                
                # Handle connection message
                try:
                    connection_msg = await asyncio.wait_for(websocket.recv(), timeout=5)
                    print(f"📝 Connection message received")
                except asyncio.TimeoutError:
                    print("⚠️  No connection message received")

                # Test cases specifically for coordinate detection
                test_cases = [
                    {
                        "name": "Center Screen Click",
                        "message": "Click in the center of the screen",
                        "expected_coordinates": {"x": 735, "y": 478}  # Center of 1470x956
                    },
                    {
                        "name": "Top-Left Click", 
                        "message": "Click in the top-left corner",
                        "expected_coordinates": {"x": 100, "y": 100}
                    },
                    {
                        "name": "Search Button Click",
                        "message": "Click on the search button in the top-right",
                        "expected_coordinates": {"x": 1200, "y": 150}
                    },
                    {
                        "name": "Input Field Focus",
                        "message": "Click on the main input field",
                        "expected_coordinates": {"x": 735, "y": 300}
                    },
                    {
                        "name": "Menu Navigation",
                        "message": "Click on the navigation menu",
                        "expected_coordinates": {"x": 200, "y": 100}
                    }
                ]

                for i, case in enumerate(test_cases, 1):
                    print(f"\n🎯 Test {i}/5: {case['name']}")
                    print(f"📝 Message: {case['message']}")
                    
                    # Send agent request
                    message = {
                        "type": "chat_request",
                        "message": case["message"],
                        "session_id": self.session_id,
                        "mode": "agent"
                    }
                    
                    await websocket.send(json.dumps(message))
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=15)
                        response_data = json.loads(response)
                        
                        # Analyze coordinate detection
                        has_coordinates = False
                        actual_coordinates = None
                        coordinate_accuracy = "Unknown"
                        
                        # Check plan coordinates
                        if 'plan' in response_data and response_data['plan']:
                            plan = response_data['plan']
                            if 'coordinates' in plan:
                                has_coordinates = True
                                actual_coordinates = plan['coordinates']
                        
                        # Check execution plan coordinates
                        if 'executionPlan' in response_data:
                            exec_plan = response_data['executionPlan']
                            if 'coordinates' in exec_plan:
                                if not has_coordinates:
                                    has_coordinates = True
                                    actual_coordinates = exec_plan['coordinates']
                        
                        # Evaluate coordinate accuracy
                        if has_coordinates and actual_coordinates:
                            expected = case['expected_coordinates']
                            actual = actual_coordinates
                            
                            # Calculate distance from expected
                            dx = abs(actual.get('x', 0) - expected['x'])
                            dy = abs(actual.get('y', 0) - expected['y'])
                            distance = (dx**2 + dy**2)**0.5
                            
                            if distance <= 50:
                                coordinate_accuracy = "EXCELLENT"
                            elif distance <= 150:
                                coordinate_accuracy = "GOOD"
                            elif distance <= 300:
                                coordinate_accuracy = "FAIR"
                            else:
                                coordinate_accuracy = "POOR"
                        
                        # Check if coordinates are just defaults
                        is_default = (actual_coordinates and 
                                    actual_coordinates.get('x') == 640 and 
                                    actual_coordinates.get('y') == 360)
                        
                        result = {
                            "test": case['name'],
                            "has_coordinates": has_coordinates,
                            "actual_coordinates": actual_coordinates,
                            "expected_coordinates": case['expected_coordinates'],
                            "coordinate_accuracy": coordinate_accuracy,
                            "is_default_coordinates": is_default,
                            "success": has_coordinates and not is_default
                        }
                        
                        self.results.append(result)
                        
                        # Print result
                        status = "✅ PASS" if result['success'] else "❌ FAIL"
                        coord_status = "🎯 SMART" if not is_default else "🔄 DEFAULT"
                        accuracy_status = f"📊 {coordinate_accuracy}"
                        
                        print(f"{status} | {coord_status} | {accuracy_status}")
                        
                        if actual_coordinates:
                            print(f"📍 Coordinates: ({actual_coordinates.get('x', 'N/A')}, {actual_coordinates.get('y', 'N/A')})")
                        
                        if is_default:
                            print(f"⚠️  Using default coordinates instead of detecting UI elements")
                        
                    except asyncio.TimeoutError:
                        print(f"❌ Timeout")
                        self.results.append({
                            "test": case['name'],
                            "success": False,
                            "error": "Timeout"
                        })
                    
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON decode error: {e}")
                        self.results.append({
                            "test": case['name'],
                            "success": False,
                            "error": "JSON decode error"
                        })
                    
                    # Small delay between tests
                    await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
        
        return True

    def print_coordinate_analysis(self):
        """Print detailed coordinate detection analysis"""
        print("\n" + "=" * 60)
        print("🎯 COORDINATE DETECTION ANALYSIS")
        print("=" * 60)
        
        if not self.results:
            print("❌ No test results available")
            return
        
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.get('success', False))
        has_coordinates = sum(1 for r in self.results if r.get('has_coordinates', False))
        default_coordinates = sum(1 for r in self.results if r.get('is_default_coordinates', False))
        smart_coordinates = has_coordinates - default_coordinates
        
        success_rate = (successful_tests / total_tests) * 100
        coordinate_rate = (has_coordinates / total_tests) * 100
        smart_rate = (smart_coordinates / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Successful: {successful_tests} ({success_rate:.1f}%)")
        print(f"📍 Has Coordinates: {has_coordinates} ({coordinate_rate:.1f}%)")
        print(f"🎯 Smart Coordinates: {smart_coordinates} ({smart_rate:.1f}%)")
        print(f"🔄 Default Coordinates: {default_coordinates}")
        
        print("\n📋 Detailed Results:")
        print("-" * 60)
        
        for result in self.results:
            test_name = result['test']
            success = result.get('success', False)
            has_coords = result.get('has_coordinates', False)
            is_default = result.get('is_default_coordinates', False)
            accuracy = result.get('coordinate_accuracy', 'Unknown')
            actual = result.get('actual_coordinates', {})
            
            status_icon = "✅" if success else "❌"
            coord_icon = "🎯" if has_coords and not is_default else "🔄" if has_coords else "❌"
            
            coords_str = f"({actual.get('x', 'N/A')}, {actual.get('y', 'N/A')})" if actual else "None"
            
            print(f"{status_icon} {coord_icon} {test_name:<20} | {coords_str:<12} | {accuracy}")
        
        print("\n🔍 Coordinate Detection Issues:")
        print("-" * 60)
        
        if default_coordinates > smart_coordinates:
            print("⚠️  MAIN ISSUE: System using default coordinates instead of real UI detection")
            print("📋 RECOMMENDATION: Integrate with UI element detection system")
        
        if smart_rate < 50:
            print("⚠️  LOW SMART COORDINATE RATE: Need better UI element detection")
            print("📋 RECOMMENDATION: Enhance visual analysis capabilities")
        
        if smart_rate >= 80:
            print("🎉 EXCELLENT: Smart coordinate detection working well!")
        elif smart_rate >= 60:
            print("👍 GOOD: Coordinate detection partially working")
        else:
            print("❌ NEEDS WORK: Coordinate detection requires improvement")

async def main():
    """Run coordinate detection test"""
    test = CoordinateDetectionTest()
    
    print("🎯 Testing AgentMode Coordinate Detection")
    print("Goal: Improve UI element coordinate mapping")
    
    success = await test.test_coordinate_detection()
    
    if success:
        test.print_coordinate_analysis()
    else:
        print("❌ Coordinate detection test failed to complete")

if __name__ == "__main__":
    asyncio.run(main())