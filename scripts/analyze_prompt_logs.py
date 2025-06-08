#!/usr/bin/env python3
"""
Prompt Log Analyzer
Analyzes LLM prompt logs to generate insights about model performance and usage patterns.
"""
import os
import json
import logging
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PromptLogAnalyzer:
    """Analyzes LLM prompt logs to generate insights."""
    
    def __init__(self, log_dir: str = "logs/llm"):
        """
        Initialize the prompt log analyzer.
        
        Args:
            log_dir: Directory containing the log files
        """
        self.log_dir = Path(log_dir)
        self.prompt_log = self.log_dir / "prompts.jsonl"
        self.metrics_log = self.log_dir / "metrics.jsonl"
        self.error_log = self.log_dir / "errors.jsonl"
        
        # Create output directory for reports
        self.report_dir = Path("reports/prompt_analysis")
        self.report_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_logs(self, days: int = 7) -> Dict[str, Any]:
        """
        Analyze logs for the specified time period.
        
        Args:
            days: Number of days to analyze (default: 7)
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Read and filter logs by date
            cutoff_date = datetime.now() - timedelta(days=days)
            prompts = []
            errors = []
            
            # Read prompt logs
            if self.prompt_log.exists():
                with open(self.prompt_log, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            entry_date = datetime.fromisoformat(entry['timestamp'])
                            if entry_date >= cutoff_date:
                                prompts.append(entry)
                        except json.JSONDecodeError:
                            continue
            
            # Read error logs
            if self.error_log.exists():
                with open(self.error_log, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            entry_date = datetime.fromisoformat(entry['timestamp'])
                            if entry_date >= cutoff_date:
                                errors.append(entry)
                        except json.JSONDecodeError:
                            continue
            
            # Generate analysis
            analysis = {
                'total_interactions': len(prompts),
                'total_errors': len(errors),
                'average_response_time': self._calculate_average_response_time(prompts),
                'mode_distribution': self._analyze_mode_distribution(prompts),
                'error_distribution': self._analyze_error_distribution(errors),
                'prompt_length_stats': self._analyze_prompt_lengths(prompts),
                'response_length_stats': self._analyze_response_lengths(prompts),
                'context_usage': self._analyze_context_usage(prompts),
                'time_distribution': self._analyze_time_distribution(prompts)
            }
            
            # Generate visualizations
            self._generate_visualizations(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")
            return {}
    
    def _calculate_average_response_time(self, prompts: List[Dict[str, Any]]) -> float:
        """Calculate average response time from prompts."""
        times = [p['processing_time'] for p in prompts if p.get('processing_time') is not None]
        return sum(times) / len(times) if times else 0.0
    
    def _analyze_mode_distribution(self, prompts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of interaction modes."""
        mode_counts = defaultdict(int)
        for prompt in prompts:
            mode_counts[prompt.get('mode', 'unknown')] += 1
        return dict(mode_counts)
    
    def _analyze_error_distribution(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of error types."""
        error_counts = defaultdict(int)
        for error in errors:
            error_counts[error.get('error_type', 'unknown')] += 1
        return dict(error_counts)
    
    def _analyze_prompt_lengths(self, prompts: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate statistics for prompt lengths."""
        lengths = [p['prompt_length'] for p in prompts]
        return {
            'min': min(lengths) if lengths else 0,
            'max': max(lengths) if lengths else 0,
            'mean': sum(lengths) / len(lengths) if lengths else 0
        }
    
    def _analyze_response_lengths(self, prompts: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate statistics for response lengths."""
        lengths = [p['response_length'] for p in prompts]
        return {
            'min': min(lengths) if lengths else 0,
            'max': max(lengths) if lengths else 0,
            'mean': sum(lengths) / len(lengths) if lengths else 0
        }
    
    def _analyze_context_usage(self, prompts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze context usage patterns."""
        context_counts = defaultdict(int)
        for prompt in prompts:
            for key in prompt.get('context_keys', []):
                context_counts[key] += 1
        return dict(context_counts)
    
    def _analyze_time_distribution(self, prompts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of interactions by hour."""
        hour_counts = defaultdict(int)
        for prompt in prompts:
            hour = datetime.fromisoformat(prompt['timestamp']).hour
            hour_counts[hour] += 1
        return dict(hour_counts)
    
    def _generate_visualizations(self, analysis: Dict[str, Any]) -> None:
        """Generate visualization plots for the analysis."""
        try:
            # Mode distribution pie chart
            plt.figure(figsize=(10, 6))
            plt.pie(
                analysis['mode_distribution'].values(),
                labels=analysis['mode_distribution'].keys(),
                autopct='%1.1f%%'
            )
            plt.title('Distribution of Interaction Modes')
            plt.savefig(self.report_dir / 'mode_distribution.png')
            plt.close()
            
            # Error distribution bar chart
            plt.figure(figsize=(10, 6))
            plt.bar(
                analysis['error_distribution'].keys(),
                analysis['error_distribution'].values()
            )
            plt.title('Distribution of Error Types')
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(self.report_dir / 'error_distribution.png')
            plt.close()
            
            # Time distribution line chart
            plt.figure(figsize=(12, 6))
            hours = sorted(analysis['time_distribution'].keys())
            counts = [analysis['time_distribution'][h] for h in hours]
            plt.plot(hours, counts, marker='o')
            plt.title('Interaction Distribution by Hour')
            plt.xlabel('Hour of Day')
            plt.ylabel('Number of Interactions')
            plt.grid(True)
            plt.savefig(self.report_dir / 'time_distribution.png')
            plt.close()
            
            logger.info(f"Visualizations generated in {self.report_dir}")
            
        except Exception as e:
            logger.error(f"Error generating visualizations: {e}")
    
    def generate_report(self, analysis: Dict[str, Any]) -> None:
        """Generate a markdown report from the analysis."""
        try:
            report_path = self.report_dir / 'analysis_report.md'
            
            with open(report_path, 'w') as f:
                f.write("# LLM Prompt Analysis Report\n\n")
                f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Summary
                f.write("## Summary\n\n")
                f.write(f"- Total Interactions: {analysis['total_interactions']}\n")
                f.write(f"- Total Errors: {analysis['total_errors']}\n")
                f.write(f"- Average Response Time: {analysis['average_response_time']:.2f}s\n\n")
                
                # Mode Distribution
                f.write("## Mode Distribution\n\n")
                for mode, count in analysis['mode_distribution'].items():
                    percentage = (count / analysis['total_interactions']) * 100
                    f.write(f"- {mode}: {count} ({percentage:.1f}%)\n")
                f.write("\n")
                
                # Error Distribution
                f.write("## Error Distribution\n\n")
                for error_type, count in analysis['error_distribution'].items():
                    f.write(f"- {error_type}: {count}\n")
                f.write("\n")
                
                # Length Statistics
                f.write("## Prompt Length Statistics\n\n")
                f.write(f"- Minimum: {analysis['prompt_length_stats']['min']} chars\n")
                f.write(f"- Maximum: {analysis['prompt_length_stats']['max']} chars\n")
                f.write(f"- Mean: {analysis['prompt_length_stats']['mean']:.1f} chars\n\n")
                
                f.write("## Response Length Statistics\n\n")
                f.write(f"- Minimum: {analysis['response_length_stats']['min']} chars\n")
                f.write(f"- Maximum: {analysis['response_length_stats']['max']} chars\n")
                f.write(f"- Mean: {analysis['response_length_stats']['mean']:.1f} chars\n\n")
                
                # Context Usage
                f.write("## Context Usage\n\n")
                for key, count in analysis['context_usage'].items():
                    f.write(f"- {key}: {count} times\n")
                f.write("\n")
                
                # Visualizations
                f.write("## Visualizations\n\n")
                f.write("The following visualizations are available in the reports directory:\n")
                f.write("- Mode Distribution (mode_distribution.png)\n")
                f.write("- Error Distribution (error_distribution.png)\n")
                f.write("- Time Distribution (time_distribution.png)\n")
            
            logger.info(f"Analysis report generated at {report_path}")
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Analyze LLM prompt logs')
    parser.add_argument('--days', type=int, default=7,
                      help='Number of days to analyze (default: 7)')
    parser.add_argument('--log-dir', type=str, default='logs/llm',
                      help='Directory containing log files (default: logs/llm)')
    
    args = parser.parse_args()
    
    analyzer = PromptLogAnalyzer(args.log_dir)
    analysis = analyzer.analyze_logs(args.days)
    analyzer.generate_report(analysis)

if __name__ == '__main__':
    main() 