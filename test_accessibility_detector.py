#!/usr/bin/env python3
"""
Test Script for Accessibility UI Detector

This script evaluates the accuracy of the accessibility UI detector
by comparing its results with known ground truth data.
"""

import os
import json
import time
import logging
import argparse
import datetime
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import precision_recall_fscore_support

# Import the accessibility detector
from accessibility_ui_detector import AccessibilityUIDetector, AccessibilityAPI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_accessibility_detector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_accessibility_detector')

class AccessibilityDetectorTester:
    """
    Class to test the accuracy of the accessibility UI detector.
    """
    
    def __init__(self, ground_truth_dir=None):
        """
        Initialize the tester.
        
        Args:
            ground_truth_dir: Directory containing ground truth data files
        """
        self.detector = AccessibilityUIDetector()
        self.api = AccessibilityAPI()
        self.ground_truth_dir = ground_truth_dir or os.path.join(os.path.dirname(__file__), 'test_data', 'ground_truth')
        
        # Create ground truth directory if it doesn't exist
        os.makedirs(self.ground_truth_dir, exist_ok=True)
        
        # Results storage
        self.results = []
    
    def capture_ground_truth(self, app_name, output_file=None):
        """
        Capture ground truth data for a specific application.
        
        Args:
            app_name: Name of the application to capture
            output_file: Output file path for the ground truth data
        
        Returns:
            dict: The captured ground truth data
        """
        logger.info(f"Capturing ground truth for {app_name}")
        
        # Capture current screen state
        scan_result = self.detector.scan_screen()
        
        # Filter elements for the specific application
        app_elements = [
            element for element in scan_result.get('elements', [])
            if element.get('app', '').lower() == app_name.lower()
        ]
        
        ground_truth = {
            'timestamp': datetime.datetime.now().isoformat(),
            'app': app_name,
            'element_count': len(app_elements),
            'elements': app_elements
        }
        
        # Save to file if specified
        if output_file:
            output_path = os.path.join(self.ground_truth_dir, output_file)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(ground_truth, f, indent=2)
            
            logger.info(f"Saved ground truth to {output_path}")
        
        return ground_truth
    
    def run_test(self, ground_truth_file=None, num_trials=1, delay=0):
        """
        Run an accuracy test by comparing detector results with ground truth.
        
        Args:
            ground_truth_file: Path to the ground truth file
            num_trials: Number of test trials to run
            delay: Delay between trials in seconds
            
        Returns:
            dict: Test results
        """
        if not ground_truth_file:
            # Use the first ground truth file found
            ground_truth_files = [f for f in os.listdir(self.ground_truth_dir) 
                                if f.endswith('.json')]
            
            if not ground_truth_files:
                logger.error("No ground truth files found")
                return {
                    'error': 'No ground truth files found',
                    'trials': 0,
                    'precision': 0,
                    'recall': 0,
                    'f1_score': 0
                }
            
            ground_truth_file = os.path.join(self.ground_truth_dir, ground_truth_files[0])
        
        # Load ground truth
        with open(ground_truth_file, 'r') as f:
            ground_truth = json.load(f)
        
        logger.info(f"Running test with ground truth file: {ground_truth_file}")
        logger.info(f"Ground truth contains {len(ground_truth.get('elements', []))} elements")
        
        # Storage for precision, recall, f1 for each trial
        precision_values = []
        recall_values = []
        f1_values = []
        durations = []
        
        # Run multiple trials
        for trial in range(num_trials):
            logger.info(f"Trial {trial + 1}/{num_trials}")
            
            # Perform scan
            start_time = time.time()
            scan_result = self.detector.scan_screen()
            duration = time.time() - start_time
            durations.append(duration * 1000)  # Convert to ms
            
            # Calculate accuracy
            result = self._calculate_accuracy(scan_result, ground_truth)
            
            precision_values.append(result['precision'])
            recall_values.append(result['recall'])
            f1_values.append(result['f1_score'])
            
            # Store detailed result
            self.results.append({
                'trial': trial + 1,
                'ground_truth_file': ground_truth_file,
                'duration_ms': duration * 1000,
                'elements_detected': scan_result.get('element_count', 0),
                'ground_truth_elements': len(ground_truth.get('elements', [])),
                'matches': result['matches'],
                'precision': result['precision'],
                'recall': result['recall'],
                'f1_score': result['f1_score']
            })
            
            # Wait between trials
            if delay > 0 and trial < num_trials - 1:
                time.sleep(delay)
        
        # Calculate average metrics
        avg_precision = sum(precision_values) / len(precision_values) if precision_values else 0
        avg_recall = sum(recall_values) / len(recall_values) if recall_values else 0
        avg_f1 = sum(f1_values) / len(f1_values) if f1_values else 0
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        logger.info(f"Test completed: Precision={avg_precision:.4f}, Recall={avg_recall:.4f}, F1={avg_f1:.4f}")
        
        return {
            'trials': num_trials,
            'precision': avg_precision,
            'recall': avg_recall,
            'f1_score': avg_f1,
            'avg_duration_ms': avg_duration,
            'detailed_results': self.results
        }
    
    def _calculate_accuracy(self, scan_result, ground_truth):
        """
        Calculate accuracy metrics by comparing scan results with ground truth.
        
        Args:
            scan_result: The detector scan result
            ground_truth: The ground truth data
            
        Returns:
            dict: Accuracy metrics
        """
        detected_elements = scan_result.get('elements', [])
        gt_elements = ground_truth.get('elements', [])
        
        # Count matches (true positives)
        matches = 0
        for gt_elem in gt_elements:
            gt_bounds = gt_elem.get('bounds', {})
            gt_type = gt_elem.get('type', '')
            
            for detected_elem in detected_elements:
                detected_bounds = detected_elem.get('bounds', {})
                detected_type = detected_elem.get('type', '')
                
                # Check if bounds overlap and types match
                if (self._bounds_overlap(gt_bounds, detected_bounds) and
                        gt_type.lower() == detected_type.lower()):
                    matches += 1
                    break
        
        # Calculate precision, recall, F1
        precision = matches / len(detected_elements) if detected_elements else 0
        recall = matches / len(gt_elements) if gt_elements else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'matches': matches,
            'precision': precision,
            'recall': recall,
            'f1_score': f1
        }
    
    def _bounds_overlap(self, bounds1, bounds2, threshold=0.5):
        """
        Check if two bounding boxes overlap with a given threshold.
        
        Args:
            bounds1: First bounding box {x, y, width, height}
            bounds2: Second bounding box {x, y, width, height}
            threshold: IoU threshold for considering overlap
            
        Returns:
            bool: True if boxes overlap above threshold
        """
        # Extract coordinates
        x1, y1 = bounds1.get('x', 0), bounds1.get('y', 0)
        w1, h1 = bounds1.get('width', 0), bounds1.get('height', 0)
        x2, y2 = bounds2.get('x', 0), bounds2.get('y', 0)
        w2, h2 = bounds2.get('width', 0), bounds2.get('height', 0)
        
        # Calculate intersection area
        x_overlap = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
        y_overlap = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
        intersection = x_overlap * y_overlap
        
        # Calculate union area
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        # Calculate IoU (Intersection over Union)
        iou = intersection / union if union > 0 else 0
        
        return iou >= threshold
    
    def generate_report(self, output_file=None):
        """
        Generate a comprehensive test report.
        
        Args:
            output_file: Path to save the report
            
        Returns:
            dict: Report data
        """
        if not self.results:
            logger.warning("No test results available for report")
            return None
        
        # Calculate overall metrics
        precision_values = [r['precision'] for r in self.results]
        recall_values = [r['recall'] for r in self.results]
        f1_values = [r['f1_score'] for r in self.results]
        durations = [r['duration_ms'] for r in self.results]
        
        report = {
            'timestamp': datetime.datetime.now().isoformat(),
            'num_trials': len(self.results),
            'avg_precision': sum(precision_values) / len(precision_values),
            'avg_recall': sum(recall_values) / len(recall_values),
            'avg_f1_score': sum(f1_values) / len(f1_values),
            'avg_duration_ms': sum(durations) / len(durations),
            'precision_std_dev': np.std(precision_values),
            'recall_std_dev': np.std(recall_values),
            'f1_std_dev': np.std(f1_values),
            'duration_std_dev': np.std(durations),
            'detailed_results': self.results
        }
        
        # Save report to file
        if output_file:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Saved report to {output_file}")
            
            # Generate visualization if matplotlib is available
            try:
                self._generate_visualization(report, output_file)
            except Exception as e:
                logger.error(f"Failed to generate visualization: {str(e)}")
        
        return report
    
    def _generate_visualization(self, report, output_file):
        """
        Generate visualizations for the report.
        
        Args:
            report: Report data
            output_file: Base path for visualization files
        """
        # Extract metrics for plotting
        trial_nums = [r['trial'] for r in report['detailed_results']]
        precision = [r['precision'] for r in report['detailed_results']]
        recall = [r['recall'] for r in report['detailed_results']]
        f1 = [r['f1_score'] for r in report['detailed_results']]
        durations = [r['duration_ms'] for r in report['detailed_results']]
        
        # Create figure with subplots
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Accessibility UI Detector Test Results', fontsize=16)
        
        # Precision, Recall, F1 over trials
        axs[0, 0].plot(trial_nums, precision, 'o-', label='Precision')
        axs[0, 0].plot(trial_nums, recall, 's-', label='Recall')
        axs[0, 0].plot(trial_nums, f1, '^-', label='F1 Score')
        axs[0, 0].set_xlabel('Trial')
        axs[0, 0].set_ylabel('Score')
        axs[0, 0].set_title('Accuracy Metrics by Trial')
        axs[0, 0].legend()
        axs[0, 0].grid(True)
        
        # Duration over trials
        axs[0, 1].plot(trial_nums, durations, 'o-', color='green')
        axs[0, 1].set_xlabel('Trial')
        axs[0, 1].set_ylabel('Duration (ms)')
        axs[0, 1].set_title('Scan Duration by Trial')
        axs[0, 1].grid(True)
        
        # Average metrics bar chart
        metrics = ['Precision', 'Recall', 'F1 Score']
        values = [report['avg_precision'], report['avg_recall'], report['avg_f1_score']]
        std_devs = [report['precision_std_dev'], report['recall_std_dev'], report['f1_std_dev']]
        
        axs[1, 0].bar(metrics, values, yerr=std_devs, capsize=5, color=['blue', 'orange', 'green'])
        axs[1, 0].set_ylabel('Score')
        axs[1, 0].set_title('Average Accuracy Metrics')
        axs[1, 0].set_ylim(0, 1.1)
        axs[1, 0].grid(True, axis='y')
        
        # Elements detected vs ground truth
        detected = [r['elements_detected'] for r in report['detailed_results']]
        ground_truth = [r['ground_truth_elements'] for r in report['detailed_results']]
        matches = [r['matches'] for r in report['detailed_results']]
        
        x = np.arange(len(trial_nums))
        width = 0.25
        
        axs[1, 1].bar(x - width, ground_truth, width, label='Ground Truth')
        axs[1, 1].bar(x, detected, width, label='Detected')
        axs[1, 1].bar(x + width, matches, width, label='Matches')
        axs[1, 1].set_xlabel('Trial')
        axs[1, 1].set_ylabel('Count')
        axs[1, 1].set_title('Elements Detected vs Ground Truth')
        axs[1, 1].set_xticks(x)
        axs[1, 1].set_xticklabels(trial_nums)
        axs[1, 1].legend()
        axs[1, 1].grid(True, axis='y')
        
        # Adjust layout and save
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        # Save plot with similar name as report but with .png extension
        plot_file = os.path.splitext(output_file)[0] + '_plot.png'
        plt.savefig(plot_file, dpi=100)
        logger.info(f"Saved visualization to {plot_file}")
        
        plt.close()

def main():
    """Run the tester from command line."""
    parser = argparse.ArgumentParser(description='Test Accessibility UI Detector')
    parser.add_argument('--capture', help='Capture ground truth for the specified application')
    parser.add_argument('--output', help='Output file for ground truth or report')
    parser.add_argument('--test', action='store_true', help='Run accuracy test')
    parser.add_argument('--ground-truth', help='Ground truth file for testing')
    parser.add_argument('--trials', type=int, default=1, help='Number of test trials')
    parser.add_argument('--delay', type=float, default=0, help='Delay between trials (seconds)')
    parser.add_argument('--report', action='store_true', help='Generate test report')
    
    args = parser.parse_args()
    
    tester = AccessibilityDetectorTester()
    
    if args.capture:
        output_file = args.output or f"{args.capture.lower().replace(' ', '_')}_ground_truth.json"
        tester.capture_ground_truth(args.capture, output_file)
    
    if args.test:
        results = tester.run_test(args.ground_truth, args.trials, args.delay)
        print(f"\nTest Results:")
        print(f"  Trials: {results['trials']}")
        print(f"  Precision: {results['precision']:.4f}")
        print(f"  Recall: {results['recall']:.4f}")
        print(f"  F1 Score: {results['f1_score']:.4f}")
        print(f"  Avg Duration: {results['avg_duration_ms']:.2f} ms")
    
    if args.report:
        output_file = args.output or f"accessibility_test_report_{int(time.time())}.json"
        tester.generate_report(output_file)

if __name__ == "__main__":
    main()