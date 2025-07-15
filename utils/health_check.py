"""
Health check utility for Aiayer
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class HealthChecker:
    """Health check system for monitoring application status"""
    
    def __init__(self):
        self.start_time = time.time()
        self.checks = {}
        self.last_check = None
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        try:
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'uptime': time.time() - self.start_time,
                'system': await self._check_system_resources(),
                'services': await self._check_services(),
                'memory': await self._check_memory_usage(),
                'disk': await self._check_disk_usage(),
                'network': await self._check_network_status(),
                'errors': []
            }
            
            # Determine overall status
            if any(check.get('status') == 'error' for check in health_status.values() if isinstance(check, dict)):
                health_status['status'] = 'degraded'
            
            if any(check.get('status') == 'critical' for check in health_status.values() if isinstance(check, dict)):
                health_status['status'] = 'unhealthy'
            
            self.last_check = health_status
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            status = 'healthy'
            if cpu_percent > 90:
                status = 'critical'
            elif cpu_percent > 80:
                status = 'warning'
            
            return {
                'status': status,
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available': memory.available,
                'memory_total': memory.total
            }
        except Exception as e:
            logger.error(f"System resources check failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _check_services(self) -> Dict[str, Any]:
        """Check service status"""
        try:
            services = {}
            
            # Check if main processes are running
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'python' in proc.info['name'].lower() and 'main.py' in ' '.join(proc.info['cmdline'] or []):
                        services['main_process'] = {
                            'status': 'running',
                            'pid': proc.info['pid']
                        }
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            else:
                services['main_process'] = {'status': 'stopped'}
            
            # Check if required ports are in use
            ports_to_check = [5000, 5001, 8765]
            for port in ports_to_check:
                try:
                    # Simple port check
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex(('localhost', port))
                    sock.close()
                    services[f'port_{port}'] = {
                        'status': 'open' if result == 0 else 'closed'
                    }
                except Exception as e:
                    services[f'port_{port}'] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            return services
            
        except Exception as e:
            logger.error(f"Services check failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage patterns"""
        try:
            memory = psutil.virtual_memory()
            
            status = 'healthy'
            if memory.percent > 95:
                status = 'critical'
            elif memory.percent > 85:
                status = 'warning'
            
            return {
                'status': status,
                'percent_used': memory.percent,
                'available_gb': round(memory.available / (1024**3), 2),
                'total_gb': round(memory.total / (1024**3), 2),
                'swap_percent': psutil.swap_memory().percent
            }
            
        except Exception as e:
            logger.error(f"Memory usage check failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _check_disk_usage(self) -> Dict[str, Any]:
        """Check disk usage"""
        try:
            disk_usage = psutil.disk_usage('/')
            
            status = 'healthy'
            if disk_usage.percent > 95:
                status = 'critical'
            elif disk_usage.percent > 85:
                status = 'warning'
            
            return {
                'status': status,
                'percent_used': disk_usage.percent,
                'free_gb': round(disk_usage.free / (1024**3), 2),
                'total_gb': round(disk_usage.total / (1024**3), 2)
            }
            
        except Exception as e:
            logger.error(f"Disk usage check failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def _check_network_status(self) -> Dict[str, Any]:
        """Check network connectivity"""
        try:
            # Check basic network connectivity
            import socket
            
            # Try to resolve a known host
            try:
                socket.gethostbyname('google.com')
                dns_status = 'working'
            except socket.gaierror:
                dns_status = 'error'
            
            # Get network interfaces
            interfaces = {}
            for interface, stats in psutil.net_if_stats().items():
                if stats.isup:
                    interfaces[interface] = 'up'
                else:
                    interfaces[interface] = 'down'
            
            return {
                'status': 'healthy' if dns_status == 'working' else 'warning',
                'dns': dns_status,
                'interfaces': interfaces
            }
            
        except Exception as e:
            logger.error(f"Network status check failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of the last health check"""
        if not self.last_check:
            return {'status': 'unknown', 'message': 'No health check performed yet'}
        
        return {
            'status': self.last_check['status'],
            'uptime': self.last_check['uptime'],
            'timestamp': self.last_check['timestamp']
        }
    
    def register_check(self, name: str, check_func):
        """Register a custom health check"""
        self.checks[name] = check_func
    
    async def run_custom_checks(self) -> Dict[str, Any]:
        """Run all registered custom health checks"""
        results = {}
        
        for name, check_func in self.checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    results[name] = await check_func()
                else:
                    results[name] = check_func()
            except Exception as e:
                results[name] = {'status': 'error', 'error': str(e)}
        
        return results

# Global health checker instance
health_checker = HealthChecker()

async def get_health_status() -> Dict[str, Any]:
    """Get current health status"""
    return await health_checker.check_system_health()

def get_health_summary() -> Dict[str, Any]:
    """Get health summary"""
    return health_checker.get_health_summary() 