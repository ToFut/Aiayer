#!/usr/bin/env python3
"""
Lightweight Performance Monitor for SensAI
Monitors system resources and provides optimization recommendations.
"""

import psutil
import time
import json
import logging
import os
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightweightPerformanceMonitor:
    """Lightweight performance monitoring for SensAI system"""
    
    def __init__(self):
        self.monitoring = False
        self.log_file = "logs/performance_lightweight.json"
        self.alert_thresholds = {
            'cpu_percent': 50,  # Alert if CPU > 50%
            'memory_percent': 70,  # Alert if memory > 70%
            'memory_mb': 300,  # Alert if memory > 300MB
            'disk_percent': 90,  # Alert if disk > 90%
            'process_count': 10  # Alert if > 10 Python processes
        }
        
        # Create log directory
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Performance history
        self.history = {
            'cpu_usage': [],
            'memory_usage': [],
            'process_count': [],
            'alerts': []
        }
    
    def get_system_stats(self):
        """Get current system statistics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # SensAI processes
            sensai_processes = []
            python_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'cmdline']):
                try:
                    proc_info = proc.info
                    if 'python' in proc_info['name'].lower():
                        python_processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cpu_percent': proc_info['cpu_percent'],
                            'memory_mb': proc_info['memory_info'].rss / 1024 / 1024 if proc_info['memory_info'] else 0,
                            'cmdline': ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else ''
                        })
                        
                        # Check if it's a SensAI process
                        cmdline_str = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else ''
                        if any(keyword in cmdline_str.lower() for keyword in [
                            'enhanced_enterprise_backend', 'direct_coordinate_automation',
                            'lightweight_process_sensor', 'lightweight_screen_sensor',
                            'ollama', 'llm_service'
                        ]):
                            sensai_processes.append({
                                'pid': proc_info['pid'],
                                'name': proc_info['name'],
                                'cpu_percent': proc_info['cpu_percent'],
                                'memory_mb': proc_info['memory_info'].rss / 1024 / 1024 if proc_info['memory_info'] else 0,
                                'cmdline': cmdline_str
                            })
                            
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage
            sensai_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            python_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            stats = {
                'timestamp': datetime.now().isoformat(),
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                },
                'memory': {
                    'total_gb': memory.total / 1024 / 1024 / 1024,
                    'used_gb': memory.used / 1024 / 1024 / 1024,
                    'available_gb': memory.available / 1024 / 1024 / 1024,
                    'percent': memory.percent,
                    'used_mb': memory_mb
                },
                'disk': {
                    'total_gb': disk.total / 1024 / 1024 / 1024,
                    'used_gb': disk.used / 1024 / 1024 / 1024,
                    'free_gb': disk.free / 1024 / 1024 / 1024,
                    'percent': (disk.used / disk.total) * 100
                },
                'sensai_processes': sensai_processes,
                'python_processes': python_processes[:5],  # Top 5
                'process_counts': {
                    'sensai': len(sensai_processes),
                    'python': len(python_processes)
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return None
    
    def check_alerts(self, stats):
        """Check for performance alerts"""
        alerts = []
        
        if not stats:
            return alerts
        
        # CPU alert
        if stats['cpu']['percent'] > self.alert_thresholds['cpu_percent']:
            alerts.append({
                'type': 'cpu_high',
                'message': f"High CPU usage: {stats['cpu']['percent']:.1f}%",
                'severity': 'warning' if stats['cpu']['percent'] < 80 else 'critical'
            })
        
        # Memory alert
        if stats['memory']['percent'] > self.alert_thresholds['memory_percent']:
            alerts.append({
                'type': 'memory_high',
                'message': f"High memory usage: {stats['memory']['percent']:.1f}% ({stats['memory']['used_mb']:.1f}MB)",
                'severity': 'warning' if stats['memory']['percent'] < 85 else 'critical'
            })
        
        # Memory MB alert
        if stats['memory']['used_mb'] > self.alert_thresholds['memory_mb']:
            alerts.append({
                'type': 'memory_mb_high',
                'message': f"High memory usage: {stats['memory']['used_mb']:.1f}MB",
                'severity': 'warning'
            })
        
        # Disk alert
        if stats['disk']['percent'] > self.alert_thresholds['disk_percent']:
            alerts.append({
                'type': 'disk_high',
                'message': f"High disk usage: {stats['disk']['percent']:.1f}%",
                'severity': 'critical'
            })
        
        # Process count alert
        if stats['process_counts']['python'] > self.alert_thresholds['process_count']:
            alerts.append({
                'type': 'process_count_high',
                'message': f"Too many Python processes: {stats['process_counts']['python']}",
                'severity': 'warning'
            })
        
        # SensAI process alerts
        for proc in stats['sensai_processes']:
            if proc['cpu_percent'] > 20:  # High CPU for individual process
                alerts.append({
                    'type': 'process_cpu_high',
                    'message': f"High CPU in {proc['name']}: {proc['cpu_percent']:.1f}%",
                    'severity': 'warning'
                })
            
            if proc['memory_mb'] > 100:  # High memory for individual process
                alerts.append({
                    'type': 'process_memory_high',
                    'message': f"High memory in {proc['name']}: {proc['memory_mb']:.1f}MB",
                    'severity': 'warning'
                })
        
        return alerts
    
    def get_optimization_recommendations(self, stats, alerts):
        """Get optimization recommendations based on current stats"""
        recommendations = []
        
        if not stats:
            return recommendations
        
        # CPU recommendations
        if stats['cpu']['percent'] > 40:
            recommendations.append({
                'priority': 'high' if stats['cpu']['percent'] > 70 else 'medium',
                'category': 'cpu',
                'message': 'Consider reducing screen capture frequency or disabling heavy features',
                'action': 'Increase screen capture interval to 60s or disable UI analysis'
            })
        
        # Memory recommendations
        if stats['memory']['percent'] > 60:
            recommendations.append({
                'priority': 'high' if stats['memory']['percent'] > 80 else 'medium',
                'category': 'memory',
                'message': 'Memory usage is high - consider clearing cache or restarting system',
                'action': 'Run memory cleanup or restart lightweight system'
            })
        
        # Process recommendations
        if stats['process_counts']['python'] > 8:
            recommendations.append({
                'priority': 'medium',
                'category': 'processes',
                'message': 'Too many Python processes running',
                'action': 'Check for duplicate processes and stop unnecessary ones'
            })
        
        # SensAI specific recommendations
        sensai_memory = sum(proc['memory_mb'] for proc in stats['sensai_processes'])
        if sensai_memory > 200:
            recommendations.append({
                'priority': 'high',
                'category': 'sensai',
                'message': f'SensAI processes using {sensai_memory:.1f}MB - exceeding lightweight limits',
                'action': 'Restart lightweight system or disable heavy features'
            })
        
        # General recommendations
        if len(alerts) > 3:
            recommendations.append({
                'priority': 'high',
                'category': 'general',
                'message': 'Multiple performance issues detected',
                'action': 'Consider restarting the lightweight system'
            })
        
        return recommendations
    
    def log_performance(self, stats, alerts, recommendations):
        """Log performance data"""
        try:
            # Load existing logs
            logs = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    logs = json.load(f)
            
            # Add new entry
            entry = {
                'timestamp': stats['timestamp'],
                'stats': stats,
                'alerts': alerts,
                'recommendations': recommendations
            }
            
            logs.append(entry)
            
            # Keep only last 100 entries
            if len(logs) > 100:
                logs = logs[-100:]
            
            # Save to file
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error logging performance: {e}")
    
    def print_summary(self, stats, alerts, recommendations):
        """Print performance summary"""
        if not stats:
            return
        
        print("\n" + "="*60)
        print(f"LIGHTWEIGHT PERFORMANCE SUMMARY - {stats['timestamp']}")
        print("="*60)
        
        # System stats
        cpu = stats['cpu']
        mem = stats['memory']
        disk = stats['disk']
        
        print(f"CPU: {cpu['percent']:.1f}% ({cpu['count']} cores)")
        print(f"Memory: {mem['used_gb']:.1f}GB / {mem['total_gb']:.1f}GB ({mem['percent']:.1f}%)")
        print(f"Disk: {disk['used_gb']:.1f}GB / {disk['total_gb']:.1f}GB ({disk['percent']:.1f}%)")
        
        # SensAI processes
        print(f"\nSensAI Processes: {stats['process_counts']['sensai']}")
        for proc in stats['sensai_processes'][:3]:  # Top 3
            print(f"  • {proc['name']} (PID: {proc['pid']})")
            print(f"    CPU: {proc['cpu_percent']:.1f}% | Memory: {proc['memory_mb']:.1f}MB")
        
        # Alerts
        if alerts:
            print(f"\n⚠️  ALERTS ({len(alerts)}):")
            for alert in alerts:
                severity_icon = "🚨" if alert['severity'] == 'critical' else "⚠️"
                print(f"  {severity_icon} {alert['message']}")
        
        # Recommendations
        if recommendations:
            print(f"\n💡 RECOMMENDATIONS ({len(recommendations)}):")
            for rec in recommendations:
                priority_icon = "🔴" if rec['priority'] == 'high' else "🟡"
                print(f"  {priority_icon} {rec['message']}")
                print(f"     Action: {rec['action']}")
        
        # Performance status
        if not alerts:
            print(f"\n✅ System performing well (no alerts)")
        elif len(alerts) <= 2:
            print(f"\n⚠️  Minor performance issues detected")
        else:
            print(f"\n🚨 Performance issues detected - consider optimization")
        
        print("="*60)
    
    def start_monitoring(self, interval=30):
        """Start continuous monitoring"""
        self.monitoring = True
        logger.info(f"Starting lightweight performance monitoring (interval: {interval}s)")
        
        try:
            while self.monitoring:
                stats = self.get_system_stats()
                if stats:
                    alerts = self.check_alerts(stats)
                    recommendations = self.get_optimization_recommendations(stats, alerts)
                    
                    self.log_performance(stats, alerts, recommendations)
                    self.print_summary(stats, alerts, recommendations)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Performance monitoring stopped by user")
            self.monitoring = False
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        logger.info("Performance monitoring stopped")
    
    def get_quick_status(self):
        """Get quick performance status"""
        stats = self.get_system_stats()
        if not stats:
            return "Unable to get system stats"
        
        alerts = self.check_alerts(stats)
        
        if not alerts:
            return f"✅ Good - CPU: {stats['cpu']['percent']:.1f}%, Memory: {stats['memory']['percent']:.1f}%"
        elif len(alerts) <= 2:
            return f"⚠️  Minor issues - {len(alerts)} alerts"
        else:
            return f"🚨 Issues - {len(alerts)} alerts"

def main():
    """Main function"""
    monitor = LightweightPerformanceMonitor()
    
    print("🚀 Lightweight Performance Monitor for SensAI")
    print("=" * 50)
    
    # Quick status check
    status = monitor.get_quick_status()
    print(f"Current Status: {status}")
    
    # Start monitoring
    print("\nStarting continuous monitoring...")
    print("Press Ctrl+C to stop")
    
    try:
        monitor.start_monitoring(interval=30)  # Check every 30 seconds
    except KeyboardInterrupt:
        print("\nMonitoring stopped")

if __name__ == "__main__":
    main() 