#!/usr/bin/env python3
"""
Process Sensor
Captures process-related data such as running processes, CPU usage, and memory usage.
"""
import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime
import psutil
from typing import Dict, Any, Optional

# Configure logging
os.makedirs('logs/sensors', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sensors/process_sensor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('process_sensor')

class ProcessSensor:
    """Sensor for capturing process-related data."""
    
    def __init__(self):
        """Initialize the process sensor."""
        self.last_data = None
        logger.info("Process sensor initialized")
    
    async def get_data(self) -> Dict[str, Any]:
        """Get current process data."""
        try:
            # Get process data
            data = {
                'timestamp': datetime.now().isoformat(),
                'processes': self._get_running_processes(),
                'cpu_usage': self._get_cpu_usage(),
                'memory_usage': self._get_memory_usage(),
                'disk_usage': self._get_disk_usage(),
                'network_usage': self._get_network_usage()
            }
            
            # Update last data
            self.last_data = data
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting process data: {e}")
            logger.error(traceback.format_exc())
            return self.last_data or {
                'timestamp': datetime.now().isoformat(),
                'processes': [],
                'cpu_usage': None,
                'memory_usage': None,
                'disk_usage': None,
                'network_usage': None
            }
    
    def _get_running_processes(self) -> list:
        """Get list of running processes with their details."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    process_info = proc.info
                    processes.append({
                        'pid': process_info['pid'],
                        'name': process_info['name'],
                        'username': process_info['username'],
                        'cpu_percent': process_info['cpu_percent'],
                        'memory_percent': process_info['memory_percent']
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            return processes
        except Exception as e:
            logger.error(f"Error getting running processes: {e}")
            return []
    
    def _get_cpu_usage(self) -> Dict[str, float]:
        """Get CPU usage statistics."""
        try:
            return {
                'total': psutil.cpu_percent(interval=1),
                'per_cpu': psutil.cpu_percent(interval=1, percpu=True)
            }
        except Exception as e:
            logger.error(f"Error getting CPU usage: {e}")
            return {'total': None, 'per_cpu': []}
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        try:
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            }
        except Exception as e:
            logger.error(f"Error getting memory usage: {e}")
            return {'total': None, 'available': None, 'used': None, 'percent': None}
    
    def _get_disk_usage(self) -> Dict[str, Any]:
        """Get disk usage statistics."""
        try:
            disk = psutil.disk_usage('/')
            return {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
        except Exception as e:
            logger.error(f"Error getting disk usage: {e}")
            return {'total': None, 'used': None, 'free': None, 'percent': None}
    
    def _get_network_usage(self) -> Dict[str, Any]:
        """Get network usage statistics."""
        try:
            network = psutil.net_io_counters()
            return {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
        except Exception as e:
            logger.error(f"Error getting network usage: {e}")
            return {'bytes_sent': None, 'bytes_recv': None, 'packets_sent': None, 'packets_recv': None}