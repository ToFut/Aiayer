#!/usr/bin/env python3
"""
System Health Monitor
Monitors all system components and provides real-time status updates.
"""

import asyncio
import websockets
import json
import time
import psutil
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import aiohttp
import subprocess
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system_health.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemHealthMonitor:
    """Monitors the health of all system components."""
    
    def __init__(self):
        self.components = {
            'websocket_server': {'port': 8765, 'status': 'unknown', 'last_check': 0},
            'backend_server': {'port': 8767, 'status': 'unknown', 'last_check': 0},
            'llm_service': {'port': 8766, 'status': 'unknown', 'last_check': 0},
            'overlay_server': {'port': 8080, 'status': 'unknown', 'last_check': 0}
        }
        
        self.sensors = {
            'process_sensor': {'status': 'unknown', 'last_data': None},
            'screen_sensor': {'status': 'unknown', 'last_data': None},
            'memory_system': {'status': 'unknown', 'last_data': None}
        }
        
        self.system_metrics = {
            'cpu_percent': 0,
            'memory_percent': 0,
            'disk_usage': 0,
            'uptime': 0,
            'component_count': 0,
            'healthy_components': 0
        }
        
        self.check_interval = 10  # seconds
        self.running = False
    
    async def check_port_service(self, component: str, port: int) -> Dict[str, Any]:
        """Check if a service is responding on a specific port."""
        try:
            # Check if port is open
            proc = subprocess.run(['lsof', '-ti', f':{port}'], 
                                capture_output=True, text=True)
            
            if proc.returncode != 0:
                return {'status': 'down', 'error': 'Port not in use'}
            
            # For WebSocket services, try to connect
            if component in ['websocket_server', 'backend_server', 'llm_service']:
                try:
                    uri = f"ws://localhost:{port}"
                    async with websockets.connect(uri, ping_timeout=5) as ws:
                        # Send a ping message
                        await ws.send(json.dumps({
                            "type": "health_check",
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                        # Wait for response
                        response = await asyncio.wait_for(ws.recv(), timeout=5)
                        return {'status': 'healthy', 'response': True}
                        
                except Exception as e:
                    return {'status': 'unhealthy', 'error': str(e)}
            
            # For HTTP services
            elif component == 'overlay_server':
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f'http://localhost:{port}', 
                                             timeout=aiohttp.ClientTimeout(total=5)) as resp:
                            if resp.status == 200:
                                return {'status': 'healthy', 'response': True}
                            else:
                                return {'status': 'unhealthy', 'error': f'HTTP {resp.status}'}
                except Exception as e:
                    return {'status': 'unhealthy', 'error': str(e)}
            
            return {'status': 'unknown', 'error': 'Unknown service type'}
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    async def check_sensor_status(self, sensor_name: str) -> Dict[str, Any]:
        """Check the status of a sensor component."""
        try:
            # Check if sensor process is running
            sensor_patterns = {
                'process_sensor': 'process_sensor',
                'screen_sensor': 'screen_sensor',
                'memory_system': 'memory_system'
            }
            
            pattern = sensor_patterns.get(sensor_name, sensor_name)
            proc = subprocess.run(['pgrep', '-f', pattern], 
                                capture_output=True, text=True)
            
            if proc.returncode == 0:
                pids = proc.stdout.strip().split('\n')
                return {
                    'status': 'running',
                    'pids': pids,
                    'count': len(pids)
                }
            else:
                return {'status': 'stopped', 'pids': [], 'count': 0}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # System uptime
            boot_time = psutil.boot_time()
            uptime_seconds = time.time() - boot_time
            
            # Component health
            healthy_components = sum(1 for comp in self.components.values() 
                                   if comp['status'] == 'healthy')
            total_components = len(self.components)
            
            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_percent': round(memory_percent, 2),
                'disk_usage': round(disk_percent, 2),
                'uptime_hours': round(uptime_seconds / 3600, 2),
                'component_count': total_components,
                'healthy_components': healthy_components,
                'health_ratio': round(healthy_components / total_components * 100, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    async def run_health_check(self) -> Dict[str, Any]:
        """Run a complete health check of all components."""
        current_time = time.time()
        
        # Check all service components
        for component, config in self.components.items():
            try:
                result = await self.check_port_service(component, config['port'])
                config['status'] = result['status']
                config['last_check'] = current_time
                config['last_result'] = result
                
                logger.info(f"{component}: {result['status']}")
                
            except Exception as e:
                logger.error(f"Error checking {component}: {e}")
                config['status'] = 'error'
                config['last_result'] = {'error': str(e)}
        
        # Check sensor components
        for sensor, config in self.sensors.items():
            try:
                result = await self.check_sensor_status(sensor)
                config['status'] = result['status']
                config['last_result'] = result
                
                logger.info(f"{sensor}: {result['status']}")
                
            except Exception as e:
                logger.error(f"Error checking {sensor}: {e}")
                config['status'] = 'error'
                config['last_result'] = {'error': str(e)}
        
        # Update system metrics
        self.system_metrics = self.get_system_metrics()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'components': self.components,
            'sensors': self.sensors,
            'system_metrics': self.system_metrics,
            'overall_health': self._calculate_overall_health()
        }
    
    def _calculate_overall_health(self) -> str:
        """Calculate overall system health status."""
        healthy_services = sum(1 for comp in self.components.values() 
                             if comp['status'] == 'healthy')
        total_services = len(self.components)
        
        running_sensors = sum(1 for sensor in self.sensors.values() 
                            if sensor['status'] == 'running')
        total_sensors = len(self.sensors)
        
        service_ratio = healthy_services / total_services if total_services > 0 else 0
        sensor_ratio = running_sensors / total_sensors if total_sensors > 0 else 0
        
        overall_ratio = (service_ratio + sensor_ratio) / 2
        
        if overall_ratio >= 0.9:
            return 'excellent'
        elif overall_ratio >= 0.7:
            return 'good'
        elif overall_ratio >= 0.5:
            return 'fair'
        else:
            return 'poor'
    
    async def start_monitoring(self):
        """Start the health monitoring loop."""
        self.running = True
        logger.info("System health monitoring started")
        
        while self.running:
            try:
                health_report = await self.run_health_check()
                
                # Log summary
                overall_health = health_report['overall_health']
                healthy_count = self.system_metrics.get('healthy_components', 0)
                total_count = self.system_metrics.get('component_count', 0)
                
                logger.info(f"Health Status: {overall_health.upper()} "
                          f"({healthy_count}/{total_count} components healthy)")
                
                # Save health report
                await self._save_health_report(health_report)
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(5)  # Short delay on error
    
    async def _save_health_report(self, report: Dict[str, Any]):
        """Save health report to file."""
        try:
            os.makedirs('logs/health', exist_ok=True)
            
            # Save latest report
            with open('logs/health/latest_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            
            # Append to history
            with open('logs/health/health_history.jsonl', 'a') as f:
                f.write(json.dumps(report) + '\n')
                
        except Exception as e:
            logger.error(f"Error saving health report: {e}")
    
    def stop_monitoring(self):
        """Stop the health monitoring."""
        self.running = False
        logger.info("System health monitoring stopped")
    
    async def get_status_report(self) -> Dict[str, Any]:
        """Get current status report."""
        return await self.run_health_check()

async def main():
    """Main function for running the health monitor."""
    monitor = SystemHealthMonitor()
    
    try:
        if len(sys.argv) > 1 and sys.argv[1] == '--once':
            # Run once and exit
            report = await monitor.get_status_report()
            print(json.dumps(report, indent=2))
        else:
            # Run continuously
            await monitor.start_monitoring()
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        monitor.stop_monitoring()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())