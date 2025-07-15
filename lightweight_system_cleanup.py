#!/usr/bin/env python3
"""
Lightweight System Cleanup for SensAI
Cleans up system resources to maintain lightweight operation.
"""

import os
import shutil
import psutil
import json
import logging
import time
from pathlib import Path
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LightweightSystemCleanup:
    """Cleanup utilities for lightweight SensAI system"""
    
    def __init__(self):
        self.cache_dirs = [
            "cache/screen_sensor",
            "cache/process_sensor", 
            "cache/ui_detection",
            "cache/llava_processor",
            "cache/professional_agent"
        ]
        
        self.log_dirs = [
            "logs/sensors",
            "logs/backend",
            "logs/memory",
            "logs/llm"
        ]
        
        self.memory_dirs = [
            "memory"
        ]
        
        # Cleanup thresholds
        self.max_cache_age_hours = 24  # Remove cache older than 24 hours
        self.max_log_age_hours = 7     # Remove logs older than 7 days
        self.max_memory_entries = 50   # Keep only 50 memory entries
        self.max_cache_size_mb = 100   # Max 100MB total cache
        
    def cleanup_cache_directories(self):
        """Clean up cache directories"""
        logger.info("🧹 Cleaning cache directories...")
        
        total_cleaned = 0
        for cache_dir in self.cache_dirs:
            if os.path.exists(cache_dir):
                cleaned = self._cleanup_directory(cache_dir, self.max_cache_age_hours)
                total_cleaned += cleaned
                logger.info(f"  {cache_dir}: {cleaned} files cleaned")
        
        logger.info(f"✅ Cache cleanup completed: {total_cleaned} files removed")
        return total_cleaned
    
    def cleanup_log_directories(self):
        """Clean up log directories"""
        logger.info("📋 Cleaning log directories...")
        
        total_cleaned = 0
        for log_dir in self.log_dirs:
            if os.path.exists(log_dir):
                cleaned = self._cleanup_directory(log_dir, self.max_log_age_hours * 24)  # Convert to hours
                total_cleaned += cleaned
                logger.info(f"  {log_dir}: {cleaned} files cleaned")
        
        logger.info(f"✅ Log cleanup completed: {total_cleaned} files removed")
        return total_cleaned
    
    def cleanup_memory_system(self):
        """Clean up memory system"""
        logger.info("🧠 Cleaning memory system...")
        
        total_cleaned = 0
        for memory_dir in self.memory_dirs:
            if os.path.exists(memory_dir):
                cleaned = self._cleanup_memory_directory(memory_dir)
                total_cleaned += cleaned
                logger.info(f"  {memory_dir}: {cleaned} entries cleaned")
        
        logger.info(f"✅ Memory cleanup completed: {total_cleaned} entries removed")
        return total_cleaned
    
    def _cleanup_directory(self, directory, max_age_hours):
        """Clean up files in a directory based on age"""
        cleaned_count = 0
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        # Check file age
                        file_mtime = os.path.getmtime(file_path)
                        if file_mtime < cutoff_time:
                            os.remove(file_path)
                            cleaned_count += 1
                    except (OSError, FileNotFoundError):
                        continue
        except Exception as e:
            logger.warning(f"Error cleaning directory {directory}: {e}")
        
        return cleaned_count
    
    def _cleanup_memory_directory(self, memory_dir):
        """Clean up memory directory - keep only recent entries"""
        cleaned_count = 0
        
        try:
            # Get all JSON files in memory directory
            json_files = []
            for root, dirs, files in os.walk(memory_dir):
                for file in files:
                    if file.endswith('.json'):
                        file_path = os.path.join(root, file)
                        try:
                            mtime = os.path.getmtime(file_path)
                            json_files.append((file_path, mtime))
                        except OSError:
                            continue
            
            # Sort by modification time (oldest first)
            json_files.sort(key=lambda x: x[1])
            
            # Keep only the most recent files
            if len(json_files) > self.max_memory_entries:
                files_to_remove = json_files[:-self.max_memory_entries]
                for file_path, _ in files_to_remove:
                    try:
                        os.remove(file_path)
                        cleaned_count += 1
                    except OSError:
                        continue
        
        except Exception as e:
            logger.warning(f"Error cleaning memory directory {memory_dir}: {e}")
        
        return cleaned_count
    
    def stop_unnecessary_processes(self):
        """Stop unnecessary SensAI processes"""
        logger.info("🛑 Stopping unnecessary processes...")
        
        stopped_count = 0
        unnecessary_keywords = [
            'memory_aware_suggestion_monitor',
            'smart_memory_feeder', 
            'performance_monitor',
            'total_screen_analyzer',
            'enhanced_fixed_process_sensor'
        ]
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                proc_info = proc.info
                cmdline_str = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else ''
                
                # Check if it's an unnecessary SensAI process
                if any(keyword in cmdline_str.lower() for keyword in unnecessary_keywords):
                    logger.info(f"  Stopping {proc_info['name']} (PID: {proc_info['pid']})")
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                        stopped_count += 1
                    except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                        try:
                            proc.kill()
                            stopped_count += 1
                        except psutil.NoSuchProcess:
                            pass
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        logger.info(f"✅ Process cleanup completed: {stopped_count} processes stopped")
        return stopped_count
    
    def optimize_memory_usage(self):
        """Optimize memory usage"""
        logger.info("💾 Optimizing memory usage...")
        
        try:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Clear Python cache
            import sys
            if hasattr(sys, 'getallocatedblocks'):
                before_blocks = sys.getallocatedblocks()
            else:
                before_blocks = 0
            
            # Clear various caches
            if hasattr(sys, 'intern'):
                sys.intern.clear()
            
            # Clear import cache
            if hasattr(sys, 'modules'):
                for module_name in list(sys.modules.keys()):
                    if module_name.startswith('_') or '.' in module_name:
                        del sys.modules[module_name]
            
            if hasattr(sys, 'getallocatedblocks'):
                after_blocks = sys.getallocatedblocks()
                freed_blocks = before_blocks - after_blocks
                logger.info(f"  Freed {freed_blocks} memory blocks")
            
            logger.info("✅ Memory optimization completed")
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing memory: {e}")
            return False
    
    def check_system_health(self):
        """Check system health and provide recommendations"""
        logger.info("🏥 Checking system health...")
        
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'issues': [],
            'recommendations': []
        }
        
        # Check disk space
        try:
            disk_usage = psutil.disk_usage('/')
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            if disk_percent > 90:
                health_report['issues'].append(f"Critical: Disk usage at {disk_percent:.1f}%")
                health_report['recommendations'].append("Free up disk space immediately")
            elif disk_percent > 80:
                health_report['issues'].append(f"Warning: Disk usage at {disk_percent:.1f}%")
                health_report['recommendations'].append("Consider freeing up disk space")
        except Exception as e:
            logger.warning(f"Could not check disk usage: {e}")
        
        # Check memory usage
        try:
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                health_report['issues'].append(f"Critical: Memory usage at {memory.percent:.1f}%")
                health_report['recommendations'].append("Restart lightweight system")
            elif memory.percent > 80:
                health_report['issues'].append(f"Warning: Memory usage at {memory.percent:.1f}%")
                health_report['recommendations'].append("Run memory cleanup")
        except Exception as e:
            logger.warning(f"Could not check memory usage: {e}")
        
        # Check SensAI processes
        sensai_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'cmdline']):
            try:
                proc_info = proc.info
                cmdline_str = ' '.join(proc_info['cmdline']) if proc_info['cmdline'] else ''
                
                if any(keyword in cmdline_str.lower() for keyword in [
                    'enhanced_enterprise_backend', 'direct_coordinate_automation',
                    'lightweight_process_sensor', 'lightweight_screen_sensor'
                ]):
                    memory_mb = proc_info['memory_info'].rss / 1024 / 1024 if proc_info['memory_info'] else 0
                    sensai_processes.append({
                        'name': proc_info['name'],
                        'pid': proc_info['pid'],
                        'cpu_percent': proc_info['cpu_percent'],
                        'memory_mb': memory_mb
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Check for high resource usage
        total_sensai_memory = sum(proc['memory_mb'] for proc in sensai_processes)
        if total_sensai_memory > 300:
            health_report['issues'].append(f"Warning: SensAI processes using {total_sensai_memory:.1f}MB")
            health_report['recommendations'].append("Restart lightweight system")
        
        # Check for high CPU usage
        high_cpu_processes = [p for p in sensai_processes if p['cpu_percent'] > 20]
        if high_cpu_processes:
            health_report['issues'].append(f"Warning: {len(high_cpu_processes)} processes with high CPU usage")
            health_report['recommendations'].append("Check for runaway processes")
        
        # Save health report
        health_file = "logs/system_health.json"
        os.makedirs(os.path.dirname(health_file), exist_ok=True)
        
        with open(health_file, 'w') as f:
            json.dump(health_report, f, indent=2)
        
        # Print summary
        if health_report['issues']:
            logger.warning(f"⚠️  {len(health_report['issues'])} health issues detected:")
            for issue in health_report['issues']:
                logger.warning(f"  • {issue}")
            
            logger.info("💡 Recommendations:")
            for rec in health_report['recommendations']:
                logger.info(f"  • {rec}")
        else:
            logger.info("✅ System health is good")
        
        return health_report
    
    def run_full_cleanup(self):
        """Run full system cleanup"""
        logger.info("🚀 Starting full lightweight system cleanup...")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all cleanup operations
        cache_cleaned = self.cleanup_cache_directories()
        log_cleaned = self.cleanup_log_directories()
        memory_cleaned = self.cleanup_memory_system()
        processes_stopped = self.stop_unnecessary_processes()
        memory_optimized = self.optimize_memory_usage()
        health_report = self.check_system_health()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Summary
        print("\n" + "=" * 60)
        print("🧹 LIGHTWEIGHT SYSTEM CLEANUP COMPLETED")
        print("=" * 60)
        print(f"⏱️  Duration: {duration:.1f} seconds")
        print(f"🗂️  Cache files removed: {cache_cleaned}")
        print(f"📋 Log files removed: {log_cleaned}")
        print(f"🧠 Memory entries removed: {memory_cleaned}")
        print(f"🛑 Processes stopped: {processes_stopped}")
        print(f"💾 Memory optimization: {'✅' if memory_optimized else '❌'}")
        print(f"🏥 Health issues: {len(health_report['issues'])}")
        
        if health_report['issues']:
            print(f"\n⚠️  Health Issues Detected:")
            for issue in health_report['issues']:
                print(f"  • {issue}")
        
        if health_report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in health_report['recommendations']:
                print(f"  • {rec}")
        
        print("\n✅ Cleanup completed successfully!")
        print("🎯 System should now be running more efficiently")
        
        return {
            'cache_cleaned': cache_cleaned,
            'log_cleaned': log_cleaned,
            'memory_cleaned': memory_cleaned,
            'processes_stopped': processes_stopped,
            'memory_optimized': memory_optimized,
            'health_issues': len(health_report['issues']),
            'duration': duration
        }

def main():
    """Main function"""
    cleanup = LightweightSystemCleanup()
    
    print("🧹 Lightweight System Cleanup for SensAI")
    print("=" * 50)
    print("This will clean up system resources to maintain lightweight operation")
    print("")
    
    # Run full cleanup
    results = cleanup.run_full_cleanup()
    
    print(f"\n📊 Cleanup Summary:")
    print(f"  • Files removed: {results['cache_cleaned'] + results['log_cleaned']}")
    print(f"  • Memory entries cleaned: {results['memory_cleaned']}")
    print(f"  • Processes stopped: {results['processes_stopped']}")
    print(f"  • Health issues: {results['health_issues']}")
    print(f"  • Total time: {results['duration']:.1f}s")

if __name__ == "__main__":
    main() 