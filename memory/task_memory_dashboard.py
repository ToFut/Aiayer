#!/usr/bin/env python3
"""
Task Memory Dashboard

Provides metrics, visualization, and management interface for
task memory system. Integrates with monitoring tools to track
memory usage, task statistics, and system performance.
"""

import os
import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import uuid
import math

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/memory/task_dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("task_dashboard")

class TaskMemoryDashboard:
    """
    Dashboard for monitoring task memory metrics
    
    Tracks and visualizes key metrics about task memory usage,
    performance, and value metrics for monetization.
    """
    
    def __init__(self, dashboard_url: str = None):
        """Initialize the task memory dashboard"""
        self.dashboard_url = dashboard_url or "http://localhost:8080/api/task_metrics"
        self.memory_metrics = {
            "records_count": 0,
            "active_records_count": 0,
            "completed_records_count": 0,
            "failed_records_count": 0,
            "avg_task_size_bytes": 0,
            "total_memory_size_bytes": 0,
            "task_history_entries": 0
        }
        
        self.performance_metrics = {
            "avg_update_time_ms": 0,
            "avg_search_time_ms": 0,
            "last_update_timestamp": 0,
            "update_count": 0,
            "search_count": 0
        }
        
        self.value_metrics = {
            "total_tasks": 0,
            "total_time_saved_sec": 0,
            "total_monetary_value": 0,
            "avg_time_saved_sec": 0,
            "avg_monetary_value": 0,
            "hourly_value_rate": 0
        }
        
        self.task_completion_metrics = {
            "completion_rate": 0,
            "avg_completion_time_sec": 0,
            "success_rate": 0,
            "task_types": {}
        }
        
        # Time series data for charts
        self.time_series = {
            "timestamps": [],
            "active_tasks": [],
            "memory_usage": [],
            "value_generated": []
        }
        
        # Last update time
        self.last_metrics_update = 0
        self.last_report_time = 0
        self.update_interval = 60  # seconds
        self.report_interval = 300  # seconds (5 minutes)
        self.record_history = True
        self.history_max_points = 1000  # Maximum number of time series points to keep
        
        # Create dashboard directory if needed
        os.makedirs('logs/dashboard', exist_ok=True)
        
        logger.info("Task memory dashboard initialized")
    
    async def update_metrics(self, task_memory_manager=None, memory_system=None):
        """Update dashboard metrics"""
        self.last_metrics_update = time.time()
        
        try:
            if task_memory_manager:
                # Update records count metrics
                self.memory_metrics["records_count"] = (
                    len(task_memory_manager.task_index.get("active_tasks", {})) +
                    len(task_memory_manager.task_index.get("completed_tasks", {})) +
                    len(task_memory_manager.task_index.get("failed_tasks", {}))
                )
                
                self.memory_metrics["active_records_count"] = len(task_memory_manager.task_index.get("active_tasks", {}))
                self.memory_metrics["completed_records_count"] = len(task_memory_manager.task_index.get("completed_tasks", {}))
                self.memory_metrics["failed_records_count"] = len(task_memory_manager.task_index.get("failed_tasks", {}))
                
                # Calculate disk usage statistics
                try:
                    import os
                    total_size = 0
                    file_count = 0
                    
                    for root, dirs, files in os.walk(task_memory_manager.storage_path):
                        for file in files:
                            if file.endswith('.json'):
                                file_path = os.path.join(root, file)
                                total_size += os.path.getsize(file_path)
                                file_count += 1
                    
                    if file_count > 0:
                        self.memory_metrics["total_memory_size_bytes"] = total_size
                        self.memory_metrics["avg_task_size_bytes"] = total_size / max(1, file_count)
                except Exception as e:
                    logger.error(f"Error calculating disk usage: {e}")
                
                # Check if we have active records with execution history
                task_history_entries = 0
                for record in task_memory_manager.active_task_records.values():
                    task_history_entries += len(record.execution_history)
                
                self.memory_metrics["task_history_entries"] = task_history_entries
                
                # Update task completion metrics
                self._update_completion_metrics(task_memory_manager)
                
            # Update time series data if recording history
            if self.record_history:
                self._update_time_series()
            
            logger.debug("Updated dashboard metrics")
            
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
    
    def _update_completion_metrics(self, task_memory_manager):
        """Update task completion metrics"""
        try:
            total_tasks = self.memory_metrics["records_count"]
            completed_tasks = self.memory_metrics["completed_records_count"]
            failed_tasks = self.memory_metrics["failed_records_count"]
            
            # Calculate completion rate
            if total_tasks > 0:
                self.task_completion_metrics["completion_rate"] = (completed_tasks + failed_tasks) / total_tasks
                self.task_completion_metrics["success_rate"] = completed_tasks / max(1, completed_tasks + failed_tasks)
            
            # Calculate average completion time from active records
            completion_times = []
            task_types = {}
            
            for record in task_memory_manager.active_task_records.values():
                # Skip records that haven't been completed
                if record.status not in ["completed", "failed"]:
                    continue
                
                # Calculate completion time
                if record.created_at and record.updated_at:
                    completion_time = record.updated_at - record.created_at
                    completion_times.append(completion_time)
                
                # Track task types
                for tag in record.tags:
                    if tag != "task":  # Skip generic task tag
                        task_types[tag] = task_types.get(tag, 0) + 1
            
            # Calculate average completion time
            if completion_times:
                self.task_completion_metrics["avg_completion_time_sec"] = sum(completion_times) / len(completion_times)
            
            # Update task types distribution
            self.task_completion_metrics["task_types"] = task_types
            
            # Update value metrics if available
            if hasattr(task_memory_manager, 'value_metrics'):
                self.value_metrics.update(task_memory_manager.value_metrics)
                
        except Exception as e:
            logger.error(f"Error updating completion metrics: {e}")
    
    def _update_time_series(self):
        """Update time series data for charts"""
        now = time.time()
        
        # Add current timestamp
        self.time_series["timestamps"].append(now)
        
        # Add current metrics
        self.time_series["active_tasks"].append(self.memory_metrics["active_records_count"])
        self.time_series["memory_usage"].append(self.memory_metrics["total_memory_size_bytes"])
        self.time_series["value_generated"].append(self.value_metrics["total_monetary_value"])
        
        # Limit time series length to prevent excessive memory usage
        if len(self.time_series["timestamps"]) > self.history_max_points:
            self.time_series["timestamps"] = self.time_series["timestamps"][-self.history_max_points:]
            self.time_series["active_tasks"] = self.time_series["active_tasks"][-self.history_max_points:]
            self.time_series["memory_usage"] = self.time_series["memory_usage"][-self.history_max_points:]
            self.time_series["value_generated"] = self.time_series["value_generated"][-self.history_max_points:]
    
    async def report_metrics(self):
        """Report metrics to external dashboard or logging system"""
        self.last_report_time = time.time()
        
        try:
            # Save metrics to JSON file for external dashboards to consume
            metrics_file = os.path.join('logs/dashboard', 'task_memory_metrics.json')
            
            # Combine all metrics
            full_metrics = {
                "timestamp": time.time(),
                "memory_metrics": self.memory_metrics,
                "performance_metrics": self.performance_metrics,
                "value_metrics": self.value_metrics,
                "task_completion_metrics": self.task_completion_metrics
            }
            
            # Ensure dashboard directory exists
            os.makedirs(os.path.dirname(metrics_file), exist_ok=True)
            
            # Save to file
            with open(metrics_file, 'w') as f:
                json.dump(full_metrics, f, indent=2)
                
            # Save time series data for charts
            if self.record_history:
                time_series_file = os.path.join('logs/dashboard', 'task_memory_time_series.json')
                # Ensure directory exists
                os.makedirs(os.path.dirname(time_series_file), exist_ok=True)
                with open(time_series_file, 'w') as f:
                    json.dump(self.time_series, f)
            
            # In a real implementation, this could send metrics to a monitoring system
            # like Prometheus, Grafana, CloudWatch, etc.
            
            logger.info("Reported task memory metrics to dashboard")
            
            # Return metrics summary
            return full_metrics
            
        except Exception as e:
            logger.error(f"Error reporting metrics: {e}")
            return None
    
    def record_performance(self, operation: str, duration_ms: float):
        """Record operation performance for monitoring"""
        try:
            if operation == "update":
                # Update average update time
                total_update_time = self.performance_metrics["avg_update_time_ms"] * self.performance_metrics["update_count"]
                self.performance_metrics["update_count"] += 1
                self.performance_metrics["avg_update_time_ms"] = (total_update_time + duration_ms) / self.performance_metrics["update_count"]
                self.performance_metrics["last_update_timestamp"] = time.time()
                
            elif operation == "search":
                # Update average search time
                total_search_time = self.performance_metrics["avg_search_time_ms"] * self.performance_metrics["search_count"]
                self.performance_metrics["search_count"] += 1
                self.performance_metrics["avg_search_time_ms"] = (total_search_time + duration_ms) / self.performance_metrics["search_count"]
            
        except Exception as e:
            logger.error(f"Error recording performance: {e}")
    
    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive metrics report"""
        try:
            # Update metrics first
            await self.update_metrics()
            
            # Calculate time-based statistics
            time_based_stats = self._calculate_time_stats()
            
            # Calculate efficiency metrics
            efficiency_metrics = {
                "success_rate": self.task_completion_metrics["success_rate"],
                "avg_completion_time_sec": self.task_completion_metrics["avg_completion_time_sec"],
                "value_per_task": self.value_metrics["avg_monetary_value"],
                "time_saved_per_task": self.value_metrics["avg_time_saved_sec"]
            }
            
            # Generate ROI metrics
            roi_metrics = self._calculate_roi_metrics()
            
            # Combine all reports
            full_report = {
                "timestamp": time.time(),
                "generated_at": datetime.now().isoformat(),
                "period": "all_time",
                "summary": {
                    "total_tasks": self.memory_metrics["records_count"],
                    "active_tasks": self.memory_metrics["active_records_count"],
                    "completed_tasks": self.memory_metrics["completed_records_count"],
                    "failed_tasks": self.memory_metrics["failed_records_count"],
                    "completion_rate": self.task_completion_metrics["completion_rate"],
                    "success_rate": self.task_completion_metrics["success_rate"],
                    "total_time_saved_hours": self.value_metrics["total_time_saved_sec"] / 3600,
                    "total_value_generated": self.value_metrics["total_monetary_value"]
                },
                "memory_usage": {
                    "total_size_mb": self.memory_metrics["total_memory_size_bytes"] / (1024 * 1024),
                    "avg_task_size_kb": self.memory_metrics["avg_task_size_bytes"] / 1024,
                    "history_entries": self.memory_metrics["task_history_entries"]
                },
                "time_based_statistics": time_based_stats,
                "efficiency_metrics": efficiency_metrics,
                "roi_metrics": roi_metrics,
                "task_type_distribution": self.task_completion_metrics["task_types"]
            }
            
            # Save full report
            report_file = os.path.join('logs/dashboard', f'task_memory_report_{int(time.time())}.json')
            # Ensure directory exists
            os.makedirs(os.path.dirname(report_file), exist_ok=True)
            with open(report_file, 'w') as f:
                json.dump(full_report, f, indent=2)
                
            logger.info(f"Generated comprehensive task memory report: {report_file}")
            return full_report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {
                "error": str(e),
                "timestamp": time.time()
            }
    
    def _calculate_time_stats(self) -> Dict[str, Any]:
        """Calculate time-based statistics from time series data"""
        if not self.time_series["timestamps"] or len(self.time_series["timestamps"]) < 2:
            return {
                "daily": {"tasks_per_day": 0},
                "weekly": {"tasks_per_week": 0},
                "monthly": {"tasks_per_month": 0}
            }
        
        try:
            # Calculate time periods
            now = time.time()
            day_ago = now - (24 * 60 * 60)
            week_ago = now - (7 * 24 * 60 * 60)
            month_ago = now - (30 * 24 * 60 * 60)
            
            # Count tasks in each period
            daily_tasks = 0
            weekly_tasks = 0
            monthly_tasks = 0
            
            # Calculate memory usage growth
            daily_memory_growth = 0
            weekly_memory_growth = 0
            monthly_memory_growth = 0
            
            # Calculate value generation
            daily_value = 0
            weekly_value = 0
            monthly_value = 0
            
            # Find oldest index for each period
            daily_idx = len(self.time_series["timestamps"])
            weekly_idx = len(self.time_series["timestamps"])
            monthly_idx = len(self.time_series["timestamps"])
            
            for i, ts in enumerate(self.time_series["timestamps"]):
                if ts >= day_ago and daily_idx == len(self.time_series["timestamps"]):
                    daily_idx = i
                if ts >= week_ago and weekly_idx == len(self.time_series["timestamps"]):
                    weekly_idx = i
                if ts >= month_ago and monthly_idx == len(self.time_series["timestamps"]):
                    monthly_idx = i
            
            # Calculate differences for each period
            if daily_idx < len(self.time_series["timestamps"]):
                daily_tasks = self.time_series["active_tasks"][-1] - self.time_series["active_tasks"][daily_idx]
                daily_memory_growth = self.time_series["memory_usage"][-1] - self.time_series["memory_usage"][daily_idx]
                daily_value = self.time_series["value_generated"][-1] - self.time_series["value_generated"][daily_idx]
            
            if weekly_idx < len(self.time_series["timestamps"]):
                weekly_tasks = self.time_series["active_tasks"][-1] - self.time_series["active_tasks"][weekly_idx]
                weekly_memory_growth = self.time_series["memory_usage"][-1] - self.time_series["memory_usage"][weekly_idx]
                weekly_value = self.time_series["value_generated"][-1] - self.time_series["value_generated"][weekly_idx]
            
            if monthly_idx < len(self.time_series["timestamps"]):
                monthly_tasks = self.time_series["active_tasks"][-1] - self.time_series["active_tasks"][monthly_idx]
                monthly_memory_growth = self.time_series["memory_usage"][-1] - self.time_series["memory_usage"][monthly_idx]
                monthly_value = self.time_series["value_generated"][-1] - self.time_series["value_generated"][monthly_idx]
            
            return {
                "daily": {
                    "tasks_per_day": daily_tasks,
                    "memory_growth_kb": daily_memory_growth / 1024,
                    "value_generated": daily_value
                },
                "weekly": {
                    "tasks_per_week": weekly_tasks,
                    "memory_growth_kb": weekly_memory_growth / 1024,
                    "value_generated": weekly_value
                },
                "monthly": {
                    "tasks_per_month": monthly_tasks,
                    "memory_growth_kb": monthly_memory_growth / 1024,
                    "value_generated": monthly_value
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating time stats: {e}")
            return {
                "daily": {"tasks_per_day": 0},
                "weekly": {"tasks_per_week": 0},
                "monthly": {"tasks_per_month": 0}
            }
    
    def _calculate_roi_metrics(self) -> Dict[str, Any]:
        """Calculate return on investment metrics"""
        # Default hourly rate for monetization
        hourly_rate = 50.0
        
        try:
            # Calculate time saved in hours
            time_saved_hours = self.value_metrics["total_time_saved_sec"] / 3600
            
            # Calculate monetary value
            monetary_value = time_saved_hours * hourly_rate
            
            # Calculate efficiency ratio (value generated per task)
            efficiency = 0
            if self.value_metrics["total_tasks"] > 0:
                efficiency = monetary_value / self.value_metrics["total_tasks"]
            
            # Calculate estimated system operating cost (placeholder for demo)
            # In a real system, this would be based on actual costs
            system_operating_hours = 24  # Assuming 24 hour operation for demo
            system_hourly_cost = 10.0  # Placeholder cost
            operating_cost = system_operating_hours * system_hourly_cost
            
            # Calculate ROI
            roi = 0
            if operating_cost > 0:
                roi = (monetary_value - operating_cost) / operating_cost
            
            return {
                "time_saved_hours": time_saved_hours,
                "monetary_value": monetary_value,
                "efficiency_per_task": efficiency,
                "estimated_operating_cost": operating_cost,
                "roi": roi,
                "roi_percent": roi * 100
            }
            
        except Exception as e:
            logger.error(f"Error calculating ROI metrics: {e}")
            return {
                "time_saved_hours": 0,
                "monetary_value": 0,
                "efficiency_per_task": 0,
                "estimated_operating_cost": 0,
                "roi": 0,
                "roi_percent": 0
            }

# Create singleton instance
task_memory_dashboard = TaskMemoryDashboard()

# API functions
async def update_metrics(task_memory_manager=None, memory_system=None):
    """Update dashboard metrics"""
    await task_memory_dashboard.update_metrics(task_memory_manager, memory_system)

async def report_metrics():
    """Report metrics to external dashboard"""
    return await task_memory_dashboard.report_metrics()

def record_performance(operation: str, duration_ms: float):
    """Record operation performance"""
    task_memory_dashboard.record_performance(operation, duration_ms)

async def generate_report() -> Dict[str, Any]:
    """Generate comprehensive metrics report"""
    return await task_memory_dashboard.generate_report()

# Background task to periodically update and report metrics
async def run_dashboard():
    """Run the dashboard update and reporting background tasks"""
    while True:
        try:
            # Update metrics
            await task_memory_dashboard.update_metrics()
            
            # Check if it's time to report metrics
            if time.time() - task_memory_dashboard.last_report_time >= task_memory_dashboard.report_interval:
                await task_memory_dashboard.report_metrics()
                
        except Exception as e:
            logger.error(f"Error in dashboard background task: {e}")
            
        await asyncio.sleep(task_memory_dashboard.update_interval)

# Start dashboard background task
def start_dashboard():
    """Start the dashboard background task"""
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(run_dashboard())
        logger.info("Started task memory dashboard background task")
    except Exception as e:
        logger.error(f"Error starting dashboard task: {e}")