#!/usr/bin/env python3
"""
LLM Prompt Logger
Provides structured logging for LLM interactions, including prompts, responses, and performance metrics.
"""
import os
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
os.makedirs('logs/llm', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/llm/prompt_logger.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LLMPromptLogger:
    """Structured logger for LLM interactions."""
    
    def __init__(self, log_dir: str = "logs/llm"):
        """
        Initialize the LLM prompt logger.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create separate log files for different aspects
        self.prompt_log = self.log_dir / "prompts.jsonl"
        self.metrics_log = self.log_dir / "metrics.jsonl"
        self.error_log = self.log_dir / "errors.jsonl"
        
        # Initialize metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "total_tokens": 0,
            "last_updated": datetime.now().isoformat()
        }
        
        logger.info("LLM Prompt Logger initialized")
    
    def log_interaction(
        self,
        prompt: str,
        response: str,
        model: str,
        mode: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> None:
        """
        Log a complete LLM interaction.
        
        Args:
            prompt: The input prompt
            response: The LLM response
            model: The model used
            mode: The interaction mode (e.g., "ask", "agent", "suggest")
            context: Optional context data used
            metadata: Optional additional metadata
            start_time: Optional start time of the request
            end_time: Optional end time of the request
        """
        try:
            # Calculate timing if provided
            processing_time = None
            if start_time and end_time:
                processing_time = end_time - start_time
            
            # Create interaction log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "model": model,
                "mode": mode,
                "prompt": prompt,
                "response": response,
                "processing_time": processing_time,
                "prompt_length": len(prompt),
                "response_length": len(response),
                "context_keys": list(context.keys()) if context else [],
                "metadata": metadata or {}
            }
            
            # Write to prompt log file
            with open(self.prompt_log, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            # Update metrics
            self.metrics["total_requests"] += 1
            if processing_time is not None:
                self.metrics["successful_requests"] += 1
                self._update_average_response_time(processing_time)
            
            # Log to console
            logger.info(f"🤖 LLM Interaction logged:")
            logger.info(f"  - Model: {model}")
            logger.info(f"  - Mode: {mode}")
            logger.info(f"  - Processing time: {processing_time:.2f}s" if processing_time else "  - Processing time: N/A")
            logger.info(f"  - Prompt length: {len(prompt)} chars")
            logger.info(f"  - Response length: {len(response)} chars")
            
        except Exception as e:
            logger.error(f"Error logging LLM interaction: {e}")
            self._log_error("log_interaction", str(e))
    
    def log_error(self, error_type: str, error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an error that occurred during LLM interaction.
        
        Args:
            error_type: Type of error (e.g., "timeout", "api_error")
            error_message: Detailed error message
            context: Optional context data
        """
        try:
            error_entry = {
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {}
            }
            
            # Write to error log file
            with open(self.error_log, 'a') as f:
                f.write(json.dumps(error_entry) + '\n')
            
            # Update metrics
            self.metrics["failed_requests"] += 1
            
            # Log to console
            logger.error(f"❌ LLM Error logged:")
            logger.error(f"  - Type: {error_type}")
            logger.error(f"  - Message: {error_message}")
            
        except Exception as e:
            logger.error(f"Error logging LLM error: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return self.metrics.copy()
    
    def _update_average_response_time(self, new_time: float) -> None:
        """Update the average response time metric."""
        total_requests = self.metrics["successful_requests"]
        current_avg = self.metrics["average_response_time"]
        
        # Calculate new average
        new_avg = ((current_avg * (total_requests - 1)) + new_time) / total_requests
        self.metrics["average_response_time"] = new_avg
        self.metrics["last_updated"] = datetime.now().isoformat()
    
    def _log_error(self, operation: str, error_message: str) -> None:
        """Internal method to log errors in the logger itself."""
        try:
            error_entry = {
                "timestamp": datetime.now().isoformat(),
                "operation": operation,
                "error_message": error_message
            }
            
            with open(self.error_log, 'a') as f:
                f.write(json.dumps(error_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Critical error in error logging: {e}")

# Create global instance
prompt_logger = LLMPromptLogger() 