#!/usr/bin/env python3
"""
Master Test Runner for SensAI System
Runs both complete test suite and RPA_AVEN test suite for comprehensive validation
"""

import os
import sys
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Any

def run_test_suite(test_file: str, description: str) -> Dict[str, Any]:
    """Run a specific test suite and return results"""
    print(f"🚀 Running {description}...")
    print("-" * 60)
    
    start_time = time.time()
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return {
                'status': 'pass',
                'duration': duration,
                'output': result.stdout,
                'error': None
            }
        else:
            print(f"❌ {description} failed")
            return {
                'status': 'fail',
                'duration': duration,
                'output': result.stdout,
                'error': result.stderr
            }
            
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"⏰ {description} timed out")
        return {
            'status': 'timeout',
            'duration': duration,
            'output': '',
            'error': 'Test suite timed out'
        }
    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 {description} crashed: {str(e)}")
        return {
            'status': 'error',
            'duration': duration,
            'output': '',
            'error': str(e)
        }

def check_system_status() -> Dict[str, Any]:
    """Check basic system status before running tests"""
    print("🔍 Pre-test System Status Check...")
    
    status = {
        'processes': {},
        'ports': {},
        'resources': {}
    }
    
    # Check key processes
    key_processes = [
        'enhanced_enterprise_backend_with_context.py',
        'direct_coordinate_automation.py',
        'enhanced_fixed_process_sensor.py',
        'total_screen_analyzer.py'
    ]
    
    import psutil
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            for key_process in key_processes:
                if key_process in cmdline:
                    status['processes'][key_process] = {
                        'pid': proc.info['pid'],
                        'memory_mb': proc.memory_info().rss / 1024 / 1024
                    }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    # Check key ports
    key_ports = [8767, 8765, 8787, 11434]
    import socket
    for port in key_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            status['ports'][port] = 'open' if result == 0 else 'closed'
        except Exception:
            status['ports'][port] = 'error'
    
    # Check system resources
    try:
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        status['resources'] = {
            'memory_percent': memory.percent,
            'cpu_percent': cpu_percent,
            'memory_available_gb': memory.available / (1024**3)
        }
    except Exception as e:
        status['resources'] = {'error': str(e)}
    
    return status

def generate_final_report(test_results: Dict[str, Any], system_status: Dict[str, Any]) -> None:
    """Generate final comprehensive report"""
    print("\n" + "=" * 80)
    print("📊 FINAL COMPREHENSIVE TEST REPORT")
    print("=" * 80)
    
    # Calculate overall statistics
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results.values() if r['status'] == 'pass')
    failed_tests = sum(1 for r in test_results.values() if r['status'] == 'fail')
    error_tests = sum(1 for r in test_results.values() if r['status'] in ['error', 'timeout'])
    
    # Overall status
    if passed_tests == total_tests:
        overall_status = "✅ ALL TESTS PASSED - SYSTEM FULLY OPERATIONAL"
    elif failed_tests == 0 and error_tests == 0:
        overall_status = "⚠️  MOSTLY WORKING - MINOR ISSUES DETECTED"
    elif failed_tests == 0:
        overall_status = "⚠️  WORKING WITH ERRORS - NEEDS ATTENTION"
    else:
        overall_status = "❌ SYSTEM HAS ISSUES - REQUIRES FIXES"
    
    print(f"Overall Status: {overall_status}")
    print(f"Test Results: {passed_tests}/{total_tests} passed")
    print(f"Failed Tests: {failed_tests}")
    print(f"Error Tests: {error_tests}")
    print()
    
    # System status summary
    print("System Status Summary:")
    print(f"  Running Processes: {len(system_status['processes'])}")
    print(f"  Open Ports: {sum(1 for p in system_status['ports'].values() if p == 'open')}")
    if 'memory_percent' in system_status['resources']:
        print(f"  Memory Usage: {system_status['resources']['memory_percent']:.1f}%")
        print(f"  CPU Usage: {system_status['resources']['cpu_percent']:.1f}%")
    print()
    
    # Detailed test results
    print("Detailed Test Results:")
    for test_name, result in test_results.items():
        status_icon = {
            'pass': '✅',
            'fail': '❌',
            'error': '💥',
            'timeout': '⏰'
        }.get(result['status'], '❓')
        
        print(f"  {status_icon} {test_name}: {result['status'].upper()} ({result['duration']:.2f}s)")
        if result['error']:
            print(f"     Error: {result['error'][:100]}...")
    
    print()
    print(f"Total test execution time: {sum(r['duration'] for r in test_results.values()):.2f} seconds")
    
    # Save comprehensive report
    report_file = f"test_results/final_comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'overall_status': overall_status,
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'error_tests': error_tests
            },
            'system_status': system_status,
            'test_results': test_results
        }, f, indent=2)
    
    print(f"Comprehensive report saved to: {report_file}")
    
    # Print recommendations
    print("\n" + "=" * 80)
    print("💡 RECOMMENDATIONS")
    print("=" * 80)
    
    if passed_tests == total_tests:
        print("🎉 EXCELLENT! Your SensAI system is fully operational.")
        print("   - All core components are working")
        print("   - RPA automation is ready")
        print("   - AI capabilities are active")
        print("   - System is ready for production use")
    elif failed_tests == 0:
        print("⚠️  GOOD! System is mostly working with minor issues.")
        print("   - Core functionality is operational")
        print("   - Some components may need attention")
        print("   - System is suitable for development/testing")
    else:
        print("❌ ATTENTION NEEDED! System has issues that should be addressed.")
        print("   - Some core components are not working")
        print("   - Check error logs for details")
        print("   - Fix issues before production use")
    
    print("\n" + "=" * 80)

def main():
    """Main function to run all tests"""
    print("🚀 SENSAI COMPREHENSIVE TEST RUNNER")
    print("=" * 80)
    print(f"Test execution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("This will run complete system validation including RPA_AVEN components")
    print()
    
    # Check system status before running tests
    system_status = check_system_status()
    
    # Define test suites to run
    test_suites = [
        ('complete_test_suite.py', 'Complete SensAI Test Suite'),
        ('rpa_aven_test_suite.py', 'RPA_AVEN Test Suite')
    ]
    
    # Run all test suites
    test_results = {}
    for test_file, description in test_suites:
        if os.path.exists(test_file):
            result = run_test_suite(test_file, description)
            test_results[description] = result
        else:
            print(f"❌ Test file not found: {test_file}")
            test_results[description] = {
                'status': 'error',
                'duration': 0,
                'output': '',
                'error': f'Test file not found: {test_file}'
            }
        print()
    
    # Generate final comprehensive report
    generate_final_report(test_results, system_status)

if __name__ == "__main__":
    main() 