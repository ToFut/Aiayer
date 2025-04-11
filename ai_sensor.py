"""
AI Sensor Module
Implements next-generation AI-driven monitoring and analysis capabilities.
"""
import time
import logging
import threading
import numpy as np
from typing import Dict, Any, List, Optional
from collections import deque
from dataclasses import dataclass
import psutil
import gc
import json
from datetime import datetime

@dataclass
class AISensorEvent:
    """Represents an AI-analyzed event with context and insights."""
    timestamp: float
    event_type: str
    source: str
    data: Dict[str, Any]
    confidence: float
    insights: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]

class AISensor:
    """Next-generation AI-driven sensor with advanced analysis capabilities."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AI sensor.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.running = False
        self.monitor_thread = None
        
        # Initialize event queues
        self.event_queue = deque(maxlen=1000)
        self.insight_queue = deque(maxlen=100)
        self.alert_queue = deque(maxlen=50)
        
        # Initialize analysis state
        self.patterns = {}
        self.anomalies = {}
        self.trends = {}
        self.predictions = {}
        
        # Initialize resource tracking
        self.resource_history = {
            'cpu': deque(maxlen=100),
            'memory': deque(maxlen=100),
            'disk': deque(maxlen=100),
            'network': deque(maxlen=100)
        }
        
        # Initialize performance metrics
        self.performance_metrics = {
            'event_processing_time': deque(maxlen=100),
            'analysis_time': deque(maxlen=100),
            'prediction_accuracy': deque(maxlen=100),
            'anomaly_detection_rate': deque(maxlen=100)
        }
        
        # Initialize AI model state
        self.model_state = {
            'last_training_time': time.time(),
            'training_interval': 3600,  # 1 hour
            'model_version': '1.0.0',
            'feature_importance': {},
            'model_metrics': {}
        }
        
        # Initialize monitoring intervals
        self.monitor_interval = config.get('monitor', {}).get('interval_sec', 60)
        self.analysis_interval = config.get('monitor', {}).get('analysis_interval_sec', 300)
        self.prediction_interval = config.get('monitor', {}).get('prediction_interval_sec', 600)
        
        # Initialize resource limits
        self.resource_limits = {
            'max_memory_mb': config.get('monitor', {}).get('max_memory_mb', 200),
            'max_cpu_percent': config.get('monitor', {}).get('max_cpu_percent', 50),
            'max_disk_usage': config.get('monitor', {}).get('max_disk_usage', 80),
            'max_network_usage': config.get('monitor', {}).get('max_network_usage', 1000)  # KB/s
        }
        
        # Initialize locks
        self.event_lock = threading.Lock()
        self.analysis_lock = threading.Lock()
        self.resource_lock = threading.Lock()
        
    def start(self) -> bool:
        """Start the AI sensor."""
        try:
            self.logger.info("Starting AI sensor...")
            self.running = True
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            
            # Start analysis thread
            self.analysis_thread = threading.Thread(target=self._analysis_loop)
            self.analysis_thread.daemon = True
            self.analysis_thread.start()
            
            self.logger.info("AI sensor started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting AI sensor: {e}")
            return False
            
    def stop(self) -> bool:
        """Stop the AI sensor."""
        try:
            self.logger.info("Stopping AI sensor...")
            self.running = False
            
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            if self.analysis_thread:
                self.analysis_thread.join(timeout=5)
                
            self.logger.info("AI sensor stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping AI sensor: {e}")
            return False
            
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.running:
            try:
                # Check system resources
                self._check_resources()
                
                # Collect system metrics
                self._collect_metrics()
                
                # Process events
                self._process_events()
                
                # Sleep until next check
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                time.sleep(5)
                
    def _analysis_loop(self) -> None:
        """Main analysis loop."""
        while self.running:
            try:
                # Analyze patterns
                self._analyze_patterns()
                
                # Detect anomalies
                self._detect_anomalies()
                
                # Update predictions
                self._update_predictions()
                
                # Generate insights
                self._generate_insights()
                
                # Sleep until next analysis
                time.sleep(self.analysis_interval)
                
            except Exception as e:
                self.logger.error(f"Error in analysis loop: {e}")
                time.sleep(5)
                
    def _check_resources(self) -> None:
        """Check system resources."""
        try:
            with self.resource_lock:
                process = psutil.Process()
                memory_info = process.memory_info()
                cpu_percent = process.cpu_percent()
                disk_usage = psutil.disk_usage('/').percent
                network_io = psutil.net_io_counters()
                
                # Update resource history
                self.resource_history['cpu'].append(cpu_percent)
                self.resource_history['memory'].append(memory_info.rss / 1024 / 1024)
                self.resource_history['disk'].append(disk_usage)
                self.resource_history['network'].append(
                    (network_io.bytes_sent + network_io.bytes_recv) / 1024
                )
                
                # Check resource limits
                if memory_info.rss / 1024 / 1024 > self.resource_limits['max_memory_mb']:
                    self._handle_resource_alert('memory', memory_info.rss / 1024 / 1024)
                    
                if cpu_percent > self.resource_limits['max_cpu_percent']:
                    self._handle_resource_alert('cpu', cpu_percent)
                    
                if disk_usage > self.resource_limits['max_disk_usage']:
                    self._handle_resource_alert('disk', disk_usage)
                    
                network_usage = (network_io.bytes_sent + network_io.bytes_recv) / 1024
                if network_usage > self.resource_limits['max_network_usage']:
                    self._handle_resource_alert('network', network_usage)
                    
        except Exception as e:
            self.logger.error(f"Error checking resources: {e}")
            
    def _collect_metrics(self) -> None:
        """Collect system metrics."""
        try:
            # Collect process metrics
            process_metrics = self._collect_process_metrics()
            
            # Collect file system metrics
            file_metrics = self._collect_file_metrics()
            
            # Collect network metrics
            network_metrics = self._collect_network_metrics()
            
            # Create event
            event = AISensorEvent(
                timestamp=time.time(),
                event_type='metrics',
                source='system',
                data={
                    'process': process_metrics,
                    'file': file_metrics,
                    'network': network_metrics
                },
                confidence=1.0,
                insights=[],
                recommendations=[],
                metadata={'collection_time': datetime.now().isoformat()}
            )
            
            # Add to event queue
            with self.event_lock:
                self.event_queue.append(event)
                
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            
    def _process_events(self) -> None:
        """Process collected events."""
        try:
            with self.event_lock:
                while self.event_queue:
                    event = self.event_queue.popleft()
                    start_time = time.time()
                    
                    # Analyze event
                    self._analyze_event(event)
                    
                    # Update performance metrics
                    processing_time = time.time() - start_time
                    self.performance_metrics['event_processing_time'].append(processing_time)
                    
        except Exception as e:
            self.logger.error(f"Error processing events: {e}")
            
    def _analyze_patterns(self) -> None:
        """Analyze patterns in collected data."""
        try:
            with self.analysis_lock:
                # Analyze resource patterns
                for resource, history in self.resource_history.items():
                    if len(history) > 10:
                        self.patterns[resource] = self._detect_patterns(history)
                        
                # Analyze event patterns
                event_patterns = self._analyze_event_patterns()
                self.patterns['events'] = event_patterns
                
        except Exception as e:
            self.logger.error(f"Error analyzing patterns: {e}")
            
    def _detect_anomalies(self) -> None:
        """Detect anomalies in system behavior."""
        try:
            with self.analysis_lock:
                # Detect resource anomalies
                for resource, history in self.resource_history.items():
                    if len(history) > 10:
                        anomalies = self._detect_resource_anomalies(resource, history)
                        if anomalies:
                            self.anomalies[resource] = anomalies
                            
                # Detect event anomalies
                event_anomalies = self._detect_event_anomalies()
                if event_anomalies:
                    self.anomalies['events'] = event_anomalies
                    
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {e}")
            
    def _update_predictions(self) -> None:
        """Update system predictions."""
        try:
            with self.analysis_lock:
                # Predict resource usage
                for resource, history in self.resource_history.items():
                    if len(history) > 10:
                        predictions = self._predict_resource_usage(resource, history)
                        self.predictions[resource] = predictions
                        
                # Predict event patterns
                event_predictions = self._predict_event_patterns()
                self.predictions['events'] = event_predictions
                
        except Exception as e:
            self.logger.error(f"Error updating predictions: {e}")
            
    def _generate_insights(self) -> None:
        """Generate insights from analysis."""
        try:
            with self.analysis_lock:
                insights = []
                
                # Generate resource insights
                for resource, patterns in self.patterns.items():
                    if resource != 'events':
                        resource_insights = self._generate_resource_insights(resource, patterns)
                        insights.extend(resource_insights)
                        
                # Generate event insights
                event_insights = self._generate_event_insights()
                insights.extend(event_insights)
                
                # Add to insight queue
                self.insight_queue.extend(insights)
                
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            
    def _handle_resource_alert(self, resource: str, value: float) -> None:
        """Handle resource alert."""
        alert = {
            'timestamp': time.time(),
            'resource': resource,
            'value': value,
            'limit': self.resource_limits[f'max_{resource}_usage'],
            'severity': 'warning' if value < self.resource_limits[f'max_{resource}_usage'] * 1.2 else 'critical'
        }
        self.alert_queue.append(alert)
        
    def _collect_process_metrics(self) -> Dict[str, Any]:
        """Collect process metrics."""
        metrics = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': {
                'bytes_sent': psutil.net_io_counters().bytes_sent,
                'bytes_recv': psutil.net_io_counters().bytes_recv
            }
        }
        return metrics
        
    def _collect_file_metrics(self) -> Dict[str, Any]:
        """Collect file system metrics."""
        metrics = {
            'total_files': sum(1 for _ in self._walk_files('/')),
            'total_size': sum(os.path.getsize(f) for f in self._walk_files('/')),
            'file_types': self._count_file_types()
        }
        return metrics
        
    def _collect_network_metrics(self) -> Dict[str, Any]:
        """Collect network metrics."""
        io = psutil.net_io_counters()
        metrics = {
            'bytes_sent': io.bytes_sent,
            'bytes_recv': io.bytes_recv,
            'packets_sent': io.packets_sent,
            'packets_recv': io.packets_recv,
            'errin': io.errin,
            'errout': io.errout,
            'dropin': io.dropin,
            'dropout': io.dropout
        }
        return metrics
        
    def _walk_files(self, path: str) -> List[str]:
        """Walk through files in a directory."""
        for root, _, files in os.walk(path):
            for file in files:
                yield os.path.join(root, file)
                
    def _count_file_types(self) -> Dict[str, int]:
        """Count file types in the system."""
        file_types = {}
        for file in self._walk_files('/'):
            ext = os.path.splitext(file)[1]
            file_types[ext] = file_types.get(ext, 0) + 1
        return file_types
        
    def _detect_patterns(self, data: List[float]) -> Dict[str, Any]:
        """Detect patterns in time series data."""
        if len(data) < 10:
            return {}
            
        # Calculate basic statistics
        mean = np.mean(data)
        std = np.std(data)
        
        # Detect trends
        trend = 'stable'
        if len(data) > 2:
            slope = np.polyfit(range(len(data)), data, 1)[0]
            if slope > 0.1:
                trend = 'increasing'
            elif slope < -0.1:
                trend = 'decreasing'
                
        # Detect seasonality
        seasonality = self._detect_seasonality(data)
        
        return {
            'mean': mean,
            'std': std,
            'trend': trend,
            'seasonality': seasonality
        }
        
    def _detect_seasonality(self, data: List[float]) -> Optional[Dict[str, Any]]:
        """Detect seasonality in time series data."""
        if len(data) < 20:
            return None
            
        # Use autocorrelation to detect seasonality
        autocorr = np.correlate(data, data, mode='full')
        autocorr = autocorr[len(autocorr)//2:]
        
        # Find peaks in autocorrelation
        peaks = []
        for i in range(1, len(autocorr)-1):
            if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                peaks.append(i)
                
        if not peaks:
            return None
            
        # Calculate seasonality period
        period = np.mean(np.diff(peaks))
        
        return {
            'period': period,
            'strength': np.mean(autocorr[peaks]) / autocorr[0]
        }
        
    def _detect_resource_anomalies(self, resource: str, history: List[float]) -> List[Dict[str, Any]]:
        """Detect anomalies in resource usage."""
        anomalies = []
        
        if len(history) < 10:
            return anomalies
            
        # Calculate statistics
        mean = np.mean(history)
        std = np.std(history)
        
        # Detect anomalies using z-score
        for i, value in enumerate(history):
            z_score = (value - mean) / std
            if abs(z_score) > 3:  # 3 standard deviations
                anomalies.append({
                    'timestamp': time.time() - (len(history) - i) * self.monitor_interval,
                    'value': value,
                    'z_score': z_score,
                    'severity': 'critical' if abs(z_score) > 4 else 'warning'
                })
                
        return anomalies
        
    def _predict_resource_usage(self, resource: str, history: List[float]) -> Dict[str, Any]:
        """Predict future resource usage."""
        if len(history) < 10:
            return {}
            
        # Use simple linear regression for prediction
        x = np.array(range(len(history)))
        y = np.array(history)
        slope, intercept = np.polyfit(x, y, 1)
        
        # Predict next 5 values
        next_x = np.array(range(len(history), len(history) + 5))
        predictions = slope * next_x + intercept
        
        return {
            'next_values': predictions.tolist(),
            'confidence': 0.8,  # Placeholder
            'trend': 'increasing' if slope > 0 else 'decreasing'
        }
        
    def _generate_resource_insights(self, resource: str, patterns: Dict[str, Any]) -> List[str]:
        """Generate insights about resource usage."""
        insights = []
        
        # Generate trend insights
        if patterns.get('trend') == 'increasing':
            insights.append(f"{resource} usage is showing an increasing trend")
        elif patterns.get('trend') == 'decreasing':
            insights.append(f"{resource} usage is showing a decreasing trend")
            
        # Generate seasonality insights
        if patterns.get('seasonality'):
            seasonality = patterns['seasonality']
            insights.append(
                f"{resource} usage shows seasonality with period {seasonality['period']:.1f} "
                f"and strength {seasonality['strength']:.2f}"
            )
            
        return insights
        
    def get_stats(self) -> Dict[str, Any]:
        """Get current AI sensor statistics."""
        return {
            'events_processed': len(self.event_queue),
            'insights_generated': len(self.insight_queue),
            'alerts_raised': len(self.alert_queue),
            'patterns_detected': len(self.patterns),
            'anomalies_detected': len(self.anomalies),
            'predictions_made': len(self.predictions),
            'performance_metrics': {
                k: {
                    'mean': np.mean(v) if v else 0,
                    'max': max(v) if v else 0
                } for k, v in self.performance_metrics.items()
            },
            'resource_usage': {
                k: {
                    'current': v[-1] if v else 0,
                    'mean': np.mean(v) if v else 0,
                    'max': max(v) if v else 0
                } for k, v in self.resource_history.items()
            }
        }
        
    def is_healthy(self) -> bool:
        """Check if the AI sensor is healthy."""
        # Check resource usage
        for resource, history in self.resource_history.items():
            if history and history[-1] > self.resource_limits[f'max_{resource}_usage']:
                return False
                
        # Check error rate
        if len(self.alert_queue) > 10:
            return False
            
        return True 