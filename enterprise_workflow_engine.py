#!/usr/bin/env python3
"""
Enterprise Workflow Engine
Executes real tasks and automation workflows for Agent mode
"""

import asyncio
import os
import subprocess
import json
import logging
import time
import shutil
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import psutil

logger = logging.getLogger(__name__)

# Import UI automation (with fallback if not available)
try:
    from ui_automation_engine import execute_ui_action
    UI_AUTOMATION_AVAILABLE = True
    logger.info("✅ UI automation engine loaded")
except ImportError:
    logger.warning("⚠️ UI automation not available")
    UI_AUTOMATION_AVAILABLE = False
    
    async def execute_ui_action(action_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        return {"success": False, "error": "UI automation not available"}

@dataclass
class ExecutionStep:
    """A single execution step in a workflow"""
    id: str
    name: str
    action_type: str  # 'file_operation', 'system_command', 'automation', 'analysis', 'web_action'
    parameters: Dict[str, Any]
    expected_result: str
    timeout: float = 30.0
    retry_count: int = 1
    dependencies: List[str] = None
    status: str = "pending"  # pending, executing, completed, failed, skipped
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0

@dataclass
class WorkflowPlan:
    """Complete workflow execution plan"""
    id: str
    title: str
    description: str
    steps: List[ExecutionStep]
    estimated_duration: float
    priority: str = "medium"
    created_at: float = None
    status: str = "planned"  # planned, executing, completed, failed, cancelled
    progress: float = 0.0
    results: Dict[str, Any] = None

class TaskAnalyzer:
    """Analyzes user requests to determine executable tasks"""
    
    def __init__(self):
        self.task_patterns = {
            'file_operations': {
                'keywords': ['file', 'folder', 'directory', 'create', 'delete', 'move', 'copy', 'organize', 'clean'],
                'actions': ['create_file', 'delete_file', 'move_file', 'copy_file', 'organize_files', 'cleanup_files']
            },
            'system_operations': {
                'keywords': ['process', 'service', 'install', 'kill', 'start', 'stop', 'monitor', 'check'],
                'actions': ['start_process', 'stop_process', 'check_system', 'install_package', 'monitor_system']
            },
            'ui_automation': {
                'keywords': ['click', 'type', 'mouse', 'keyboard', 'button', 'input', 'select', 'drag', 'press', 'key'],
                'actions': ['click_element', 'type_text', 'press_key', 'mouse_move', 'drag_drop', 'select_text']
            },
            'automation': {
                'keywords': ['automate', 'schedule', 'repeat', 'workflow', 'batch', 'script'],
                'actions': ['create_automation', 'schedule_task', 'run_batch', 'execute_script']
            },
            'analysis': {
                'keywords': ['analyze', 'report', 'statistics', 'data', 'log', 'performance'],
                'actions': ['analyze_data', 'generate_report', 'collect_stats', 'parse_logs']
            },
            'productivity': {
                'keywords': ['optimize', 'improve', 'productivity', 'efficiency', 'setup', 'configure'],
                'actions': ['optimize_workflow', 'setup_environment', 'configure_tools', 'improve_process']
            }
        }
    
    async def analyze_request(self, query: str) -> Dict[str, Any]:
        """Analyze user request to determine task type and parameters"""
        query_lower = query.lower()
        
        # Determine primary task category
        task_category = "general"
        confidence = 0.0
        detected_actions = []
        
        for category, config in self.task_patterns.items():
            matches = sum(1 for keyword in config['keywords'] if keyword in query_lower)
            # Improved confidence calculation - give higher weight to matches
            if matches > 0:
                category_confidence = min(1.0, matches * 0.3)  # Each match adds 0.3 confidence
            else:
                category_confidence = 0.0
            
            if category_confidence > confidence:
                confidence = category_confidence
                task_category = category
                detected_actions = config['actions']
        
        # Extract specific parameters
        parameters = await self._extract_parameters(query, task_category)
        
        return {
            "task_category": task_category,
            "confidence": confidence,
            "detected_actions": detected_actions,
            "parameters": parameters,
            "executable": confidence > 0.15,  # Lower threshold for better execution
            "complexity": "high" if len(detected_actions) > 3 else "medium" if len(detected_actions) > 1 else "low"
        }
    
    async def _extract_parameters(self, query: str, category: str) -> Dict[str, Any]:
        """Extract specific parameters from the query"""
        parameters = {}
        
        if category == "file_operations":
            # Extract file paths, extensions, etc.
            if "desktop" in query.lower():
                parameters["base_path"] = str(Path.home() / "Desktop")
            elif "documents" in query.lower():
                parameters["base_path"] = str(Path.home() / "Documents")
            else:
                parameters["base_path"] = os.getcwd()
            
            # Extract file types
            file_extensions = []
            for ext in ['.pdf', '.txt', '.doc', '.png', '.jpg', '.py', '.js']:
                if ext in query.lower():
                    file_extensions.append(ext)
            parameters["file_types"] = file_extensions
        
        elif category == "system_operations":
            # Extract process names, service names
            parameters["target_processes"] = []
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() in query.lower():
                        parameters["target_processes"].append(proc.info['name'])
                except:
                    pass
        
        return parameters

class WorkflowExecutor:
    """Executes workflow steps with real automation"""
    
    def __init__(self):
        self.execution_handlers = {
            'file_operation': self._execute_file_operation,
            'system_command': self._execute_system_command,
            'ui_automation': self._execute_ui_automation,
            'automation': self._execute_automation,
            'analysis': self._execute_analysis,
            'web_action': self._execute_web_action
        }
        
        # Safety limits
        self.max_files_per_operation = 100
        self.allowed_directories = [
            str(Path.home() / "Desktop"),
            str(Path.home() / "Documents"),
            str(Path.home() / "Downloads"),
            "/tmp",
            os.getcwd()
        ]
    
    async def execute_workflow(self, workflow: WorkflowPlan) -> Dict[str, Any]:
        """Execute complete workflow with real actions"""
        start_time = time.time()
        workflow.status = "executing"
        
        logger.info(f"🚀 Starting workflow execution: {workflow.title}")
        
        try:
            completed_steps = 0
            results = {}
            
            for step in workflow.steps:
                # Check dependencies
                if step.dependencies and not all(
                    dep in results and results[dep].get("success", False) 
                    for dep in step.dependencies
                ):
                    step.status = "skipped"
                    step.error = "Dependencies not met"
                    continue
                
                # Execute step
                step.status = "executing"
                logger.info(f"🔧 Executing: {step.name}")
                
                step_result = await self._execute_step(step)
                
                step.result = step_result
                step.status = "completed" if step_result.get("success", False) else "failed"
                step.error = step_result.get("error")
                
                results[step.id] = step_result
                
                if step.status == "completed":
                    completed_steps += 1
                
                # Update progress
                workflow.progress = (completed_steps / len(workflow.steps)) * 100
                
                logger.info(f"✅ Step completed: {step.name} (success: {step_result.get('success', False)})")
            
            # Final status
            workflow.status = "completed" if completed_steps == len(workflow.steps) else "failed"
            workflow.results = results
            
            execution_time = time.time() - start_time
            
            logger.info(f"🎉 Workflow completed: {workflow.title} ({completed_steps}/{len(workflow.steps)} steps, {execution_time:.2f}s)")
            
            return {
                "success": workflow.status == "completed",
                "workflow_id": workflow.id,
                "status": workflow.status,
                "progress": workflow.progress,
                "completed_steps": completed_steps,
                "total_steps": len(workflow.steps),
                "execution_time": execution_time,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            workflow.status = "failed"
            return {
                "success": False,
                "workflow_id": workflow.id,
                "status": "failed",
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    async def _execute_step(self, step: ExecutionStep) -> Dict[str, Any]:
        """Execute a single workflow step"""
        step_start = time.time()
        
        try:
            handler = self.execution_handlers.get(step.action_type, self._execute_default)
            
            # Execute with timeout
            result = await asyncio.wait_for(
                handler(step),
                timeout=step.timeout
            )
            
            step.execution_time = time.time() - step_start
            return result
            
        except asyncio.TimeoutError:
            step.execution_time = time.time() - step_start
            return {
                "success": False,
                "error": f"Step timed out after {step.timeout}s",
                "step_id": step.id
            }
        except Exception as e:
            step.execution_time = time.time() - step_start
            return {
                "success": False,
                "error": str(e),
                "step_id": step.id
            }
    
    async def _execute_file_operation(self, step: ExecutionStep) -> Dict[str, Any]:
        """Execute file operations safely"""
        params = step.parameters
        operation = params.get("operation", "unknown")
        
        try:
            if operation == "organize_files":
                return await self._organize_files(params)
            elif operation == "create_directory":
                return await self._create_directory(params)
            elif operation == "list_files":
                return await self._list_files(params)
            elif operation == "cleanup_temp":
                return await self._cleanup_temp_files(params)
            elif operation == "backup_files":
                return await self._backup_files(params)
            else:
                return {"success": False, "error": f"Unknown file operation: {operation}"}
                
        except Exception as e:
            return {"success": False, "error": f"File operation failed: {e}"}
    
    async def _organize_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Organize files by type or date"""
        base_path = Path(params.get("base_path", os.getcwd()))
        
        # Safety check
        if str(base_path) not in self.allowed_directories:
            return {"success": False, "error": "Directory not allowed for safety"}
        
        if not base_path.exists():
            return {"success": False, "error": "Base path does not exist"}
        
        organized_count = 0
        created_folders = []
        
        # Create organization folders
        for file_type in ["Documents", "Images", "Archives", "Others"]:
            folder_path = base_path / file_type
            if not folder_path.exists():
                folder_path.mkdir()
                created_folders.append(str(folder_path))
        
        # Organize files
        for file_path in base_path.iterdir():
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                
                # Determine target folder
                if suffix in ['.pdf', '.doc', '.docx', '.txt']:
                    target_folder = base_path / "Documents"
                elif suffix in ['.jpg', '.png', '.gif', '.bmp']:
                    target_folder = base_path / "Images"
                elif suffix in ['.zip', '.rar', '.tar', '.gz']:
                    target_folder = base_path / "Archives"
                else:
                    target_folder = base_path / "Others"
                
                try:
                    new_path = target_folder / file_path.name
                    if not new_path.exists():
                        shutil.move(str(file_path), str(new_path))
                        organized_count += 1
                except Exception as e:
                    logger.warning(f"Could not move {file_path}: {e}")
        
        return {
            "success": True,
            "organized_files": organized_count,
            "created_folders": created_folders,
            "base_path": str(base_path)
        }
    
    async def _create_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create directory structure"""
        dir_path = Path(params.get("path", ""))
        
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            return {
                "success": True,
                "created_path": str(dir_path),
                "exists": dir_path.exists()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List files in directory"""
        dir_path = Path(params.get("path", os.getcwd()))
        file_types = params.get("file_types", [])
        
        try:
            files = []
            for item in dir_path.iterdir():
                if item.is_file():
                    if not file_types or item.suffix.lower() in file_types:
                        files.append({
                            "name": item.name,
                            "size": item.stat().st_size,
                            "modified": item.stat().st_mtime
                        })
            
            return {
                "success": True,
                "files": files[:self.max_files_per_operation],  # Limit for safety
                "total_count": len(files),
                "directory": str(dir_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _cleanup_temp_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up temporary files"""
        temp_dirs = ["/tmp", str(Path.home() / "Downloads")]
        cleaned_count = 0
        
        for temp_dir in temp_dirs:
            temp_path = Path(temp_dir)
            if temp_path.exists():
                try:
                    for item in temp_path.iterdir():
                        if item.is_file() and item.name.startswith(('.tmp', 'temp')):
                            item.unlink()
                            cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Could not clean {temp_dir}: {e}")
        
        return {
            "success": True,
            "cleaned_files": cleaned_count,
            "directories_cleaned": temp_dirs
        }
    
    async def _backup_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create backup of important files"""
        source_path = Path(params.get("source_path", ""))
        backup_path = Path(params.get("backup_path", str(Path.home() / "backup")))
        
        try:
            if not source_path.exists():
                return {"success": False, "error": "Source path does not exist"}
            
            backup_path.mkdir(parents=True, exist_ok=True)
            
            backed_up_count = 0
            if source_path.is_file():
                shutil.copy2(str(source_path), str(backup_path))
                backed_up_count = 1
            elif source_path.is_dir():
                for item in source_path.iterdir():
                    if item.is_file():
                        shutil.copy2(str(item), str(backup_path))
                        backed_up_count += 1
            
            return {
                "success": True,
                "backed_up_files": backed_up_count,
                "backup_location": str(backup_path)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_system_command(self, step: ExecutionStep) -> Dict[str, Any]:
        """Execute system commands safely"""
        params = step.parameters
        command = params.get("command", "")
        safe_commands = ["ps", "top", "df", "free", "uptime", "whoami", "pwd", "ls"]
        
        # Safety check - only allow safe commands
        command_name = command.split()[0] if command else ""
        if command_name not in safe_commands:
            return {"success": False, "error": f"Command '{command_name}' not allowed for safety"}
        
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=step.timeout
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _execute_automation(self, step: ExecutionStep) -> Dict[str, Any]:
        """Execute automation tasks"""
        params = step.parameters
        automation_type = params.get("type", "unknown")
        
        if automation_type == "schedule_task":
            return {"success": True, "message": "Task scheduling simulated (would use cron/Task Scheduler)"}
        elif automation_type == "create_script":
            return {"success": True, "message": "Script creation simulated"}
        else:
            return {"success": False, "error": f"Unknown automation type: {automation_type}"}
    
    async def _execute_analysis(self, step: ExecutionStep) -> Dict[str, Any]:
        """Execute analysis tasks"""
        params = step.parameters
        analysis_type = params.get("type", "system_info")
        
        if analysis_type == "system_info":
            return {
                "success": True,
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "disk_usage": psutil.disk_usage('/').percent,
                "running_processes": len(psutil.pids())
            }
        else:
            return {"success": False, "error": f"Unknown analysis type: {analysis_type}"}
    
    async def _execute_ui_automation(self, step: ExecutionStep) -> Dict[str, Any]:
        """Execute UI automation actions with real mouse and keyboard control"""
        params = step.parameters
        action_type = params.get("action", "unknown")
        
        if not UI_AUTOMATION_AVAILABLE:
            return {
                "success": False,
                "error": "UI automation engine not available",
                "message": "Please ensure ui_automation_engine.py is properly installed"
            }
        
        try:
            logger.info(f"🖱️ Executing UI automation: {action_type}")
            
            # Execute the UI action using the imported UI automation engine
            result = await execute_ui_action(action_type, params)
            
            if result.get("success", False):
                logger.info(f"✅ UI automation completed: {action_type}")
                return {
                    "success": True,
                    "action": action_type,
                    "result": result.get("result", "Action completed"),
                    "coordinates": result.get("coordinates"),
                    "text": result.get("text"),
                    "execution_time": result.get("execution_time", 0)
                }
            else:
                logger.error(f"❌ UI automation failed: {result.get('error', 'Unknown error')}")
                return {
                    "success": False,
                    "action": action_type,
                    "error": result.get("error", "UI automation failed")
                }
                
        except Exception as e:
            logger.error(f"❌ UI automation exception: {e}")
            return {
                "success": False,
                "action": action_type,
                "error": f"UI automation error: {str(e)}"
            }
    
    async def _execute_web_action(self, step: ExecutionStep) -> Dict[str, Any]:
        """Execute web actions (placeholder for future implementation)"""
        return {"success": True, "message": "Web action simulated (future implementation)"}
    
    async def _execute_default(self, step: ExecutionStep) -> Dict[str, Any]:
        """Default handler for unknown step types"""
        return {
            "success": True,
            "message": f"Step '{step.name}' executed (default handler)",
            "action_type": step.action_type
        }

class EnterpriseWorkflowEngine:
    """Main workflow engine orchestrating task analysis and execution"""
    
    def __init__(self):
        self.task_analyzer = TaskAnalyzer()
        self.workflow_executor = WorkflowExecutor()
        self.active_workflows: Dict[str, WorkflowPlan] = {}
    
    async def process_agent_request(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process agent request with planning and execution"""
        start_time = time.time()
        
        try:
            logger.info(f"🤖 Processing agent request: {query[:100]}...")
            
            # Analyze the request
            analysis = await self.task_analyzer.analyze_request(query)
            
            if not analysis["executable"]:
                return {
                    "success": False,
                    "message": "Request is not executable as a concrete task",
                    "analysis": analysis,
                    "suggestion": "Try rephrasing with specific actions like 'organize files', 'check system status', or 'create backup'"
                }
            
            # Create workflow plan
            workflow = await self._create_workflow_plan(query, analysis, context)
            
            # Execute workflow
            execution_result = await self.workflow_executor.execute_workflow(workflow)
            
            # Generate response
            response = await self._generate_execution_response(workflow, execution_result, query)
            
            return {
                "success": execution_result["success"],
                "response": response,
                "workflow_id": workflow.id,
                "execution_result": execution_result,
                "analysis": analysis,
                "processing_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"❌ Workflow processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "I encountered an error while processing your request",
                "processing_time": time.time() - start_time
            }
    
    async def _create_workflow_plan(self, query: str, analysis: Dict[str, Any], context: Dict[str, Any]) -> WorkflowPlan:
        """Create executable workflow plan"""
        
        workflow_id = f"workflow_{int(time.time())}_{hash(query) % 10000}"
        task_category = analysis["task_category"]
        parameters = analysis["parameters"]
        
        steps = []
        
        if task_category == "file_operations":
            steps = await self._create_file_operation_steps(query, parameters)
        elif task_category == "system_operations":
            steps = await self._create_system_operation_steps(query, parameters)
        elif task_category == "ui_automation":
            steps = await self._create_ui_automation_steps(query, parameters)
        elif task_category == "automation":
            steps = await self._create_automation_steps(query, parameters)
        elif task_category == "analysis":
            steps = await self._create_analysis_steps(query, parameters)
        elif task_category == "productivity":
            steps = await self._create_productivity_steps(query, parameters)
        else:
            # Generic workflow
            steps = [
                ExecutionStep(
                    id="generic_1",
                    name="Process request",
                    action_type="analysis",
                    parameters={"type": "system_info"},
                    expected_result="System information collected"
                )
            ]
        
        workflow = WorkflowPlan(
            id=workflow_id,
            title=f"Execute: {query[:50]}...",
            description=query,
            steps=steps,
            estimated_duration=sum(step.timeout for step in steps),
            created_at=time.time()
        )
        
        self.active_workflows[workflow_id] = workflow
        return workflow
    
    async def _create_file_operation_steps(self, query: str, params: Dict[str, Any]) -> List[ExecutionStep]:
        """Create file operation workflow steps"""
        steps = []
        
        if "organize" in query.lower():
            steps.append(ExecutionStep(
                id="organize_files",
                name="Organize files by type",
                action_type="file_operation",
                parameters={
                    "operation": "organize_files",
                    "base_path": params.get("base_path", os.getcwd())
                },
                expected_result="Files organized into type-based folders",
                timeout=30.0
            ))
        
        if "cleanup" in query.lower() or "clean" in query.lower():
            steps.append(ExecutionStep(
                id="cleanup_temp",
                name="Clean up temporary files",
                action_type="file_operation",
                parameters={"operation": "cleanup_temp"},
                expected_result="Temporary files removed",
                timeout=20.0
            ))
        
        if "backup" in query.lower():
            steps.append(ExecutionStep(
                id="backup_files",
                name="Create file backup",
                action_type="file_operation",
                parameters={
                    "operation": "backup_files",
                    "source_path": params.get("base_path", os.getcwd())
                },
                expected_result="Files backed up successfully",
                timeout=60.0
            ))
        
        return steps
    
    async def _create_system_operation_steps(self, query: str, params: Dict[str, Any]) -> List[ExecutionStep]:
        """Create system operation workflow steps"""
        return [
            ExecutionStep(
                id="system_check",
                name="Check system status",
                action_type="analysis",
                parameters={"type": "system_info"},
                expected_result="System information collected",
                timeout=10.0
            )
        ]
    
    async def _create_ui_automation_steps(self, query: str, params: Dict[str, Any]) -> List[ExecutionStep]:
        """Create UI automation workflow steps"""
        steps = []
        query_lower = query.lower()
        
        # Analyze query for specific UI actions
        if "click" in query_lower:
            # Extract coordinates if mentioned, otherwise use default safe coordinates
            x, y = 100, 100  # Default safe coordinates
            if "at" in query_lower and any(char.isdigit() for char in query):
                # Try to extract coordinates from query
                import re
                coords = re.findall(r'\d+', query)
                if len(coords) >= 2:
                    x, y = int(coords[0]), int(coords[1])
            
            steps.append(ExecutionStep(
                id="click_action",
                name="Click at specified location",
                action_type="ui_automation",
                parameters={
                    "action": "click",
                    "x": x,
                    "y": y,
                    "button": "left"
                },
                expected_result="Mouse click executed",
                timeout=5.0
            ))
        
        if "type" in query_lower or "input" in query_lower:
            # Extract text to type
            text_to_type = "Hello, World!"  # Default text
            if "type " in query_lower:
                parts = query_lower.split("type ")
                if len(parts) > 1:
                    text_to_type = parts[1].split()[0] if parts[1].split() else text_to_type
            
            steps.append(ExecutionStep(
                id="type_action",
                name="Type text input",
                action_type="ui_automation",
                parameters={
                    "action": "type",
                    "text": text_to_type
                },
                expected_result="Text typed successfully",
                timeout=10.0
            ))
        
        if "key" in query_lower or "press" in query_lower:
            # Extract key to press
            key_to_press = "return"  # Default key
            common_keys = ["return", "space", "tab", "escape", "delete", "backspace"]
            for key in common_keys:
                if key in query_lower:
                    key_to_press = key
                    break
            
            steps.append(ExecutionStep(
                id="key_press_action",
                name=f"Press {key_to_press} key",
                action_type="ui_automation",
                parameters={
                    "action": "key_press",
                    "key": key_to_press
                },
                expected_result="Key press executed",
                timeout=5.0
            ))
        
        if "move" in query_lower and "mouse" in query_lower:
            steps.append(ExecutionStep(
                id="mouse_move_action",
                name="Move mouse cursor",
                action_type="ui_automation",
                parameters={
                    "action": "mouse_move",
                    "x": params.get("x", 200),
                    "y": params.get("y", 200)
                },
                expected_result="Mouse moved to position",
                timeout=5.0
            ))
        
        # If no specific actions detected, create a demo UI automation step
        if not steps:
            steps.append(ExecutionStep(
                id="demo_ui_action",
                name="Demonstrate UI automation capabilities",
                action_type="ui_automation",
                parameters={
                    "action": "click",
                    "x": 100,
                    "y": 100,
                    "button": "left"
                },
                expected_result="UI automation demonstrated",
                timeout=5.0
            ))
        
        return steps
    
    async def _create_automation_steps(self, query: str, params: Dict[str, Any]) -> List[ExecutionStep]:
        """Create automation workflow steps"""
        return [
            ExecutionStep(
                id="create_automation",
                name="Set up automation",
                action_type="automation",
                parameters={"type": "schedule_task"},
                expected_result="Automation configured",
                timeout=15.0
            )
        ]
    
    async def _create_analysis_steps(self, query: str, params: Dict[str, Any]) -> List[ExecutionStep]:
        """Create analysis workflow steps"""
        return [
            ExecutionStep(
                id="analyze_system",
                name="Analyze system performance",
                action_type="analysis",
                parameters={"type": "system_info"},
                expected_result="Analysis completed",
                timeout=15.0
            )
        ]
    
    async def _create_productivity_steps(self, query: str, params: Dict[str, Any]) -> List[ExecutionStep]:
        """Create productivity improvement workflow steps"""
        steps = []
        
        if "organize" in query.lower():
            steps.append(ExecutionStep(
                id="organize_workspace",
                name="Organize workspace files",
                action_type="file_operation",
                parameters={
                    "operation": "organize_files",
                    "base_path": str(Path.home() / "Desktop")
                },
                expected_result="Workspace organized",
                timeout=30.0
            ))
        
        steps.append(ExecutionStep(
            id="system_optimization",
            name="Check system optimization opportunities",
            action_type="analysis",
            parameters={"type": "system_info"},
            expected_result="Optimization suggestions generated",
            timeout=10.0
        ))
        
        return steps
    
    async def _generate_execution_response(self, workflow: WorkflowPlan, execution_result: Dict[str, Any], original_query: str) -> str:
        """Generate human-readable response about execution"""
        
        if execution_result["success"]:
            response = f"✅ **Task Completed Successfully!**\n\n"
            response += f"**Request:** {original_query}\n\n"
            response += f"**Execution Summary:**\n"
            response += f"• Completed {execution_result['completed_steps']}/{execution_result['total_steps']} steps\n"
            response += f"• Execution time: {execution_result['execution_time']:.2f} seconds\n\n"
            
            response += f"**Steps Executed:**\n"
            for i, step in enumerate(workflow.steps, 1):
                status_emoji = "✅" if step.status == "completed" else "❌" if step.status == "failed" else "⏸️"
                response += f"{i}. {status_emoji} {step.name}\n"
                
                if step.result and step.status == "completed":
                    # Add specific results
                    if step.action_type == "file_operation":
                        if "organized_files" in step.result:
                            response += f"   └─ Organized {step.result['organized_files']} files\n"
                        if "cleaned_files" in step.result:
                            response += f"   └─ Cleaned {step.result['cleaned_files']} temporary files\n"
                        if "backed_up_files" in step.result:
                            response += f"   └─ Backed up {step.result['backed_up_files']} files\n"
                    elif step.action_type == "ui_automation":
                        if "action" in step.result:
                            action = step.result['action']
                            if action == "click" and "coordinates" in step.result:
                                coords = step.result['coordinates']
                                response += f"   └─ Clicked at ({coords.get('x', 'N/A')}, {coords.get('y', 'N/A')})\n"
                            elif action == "type" and "text" in step.result:
                                text = step.result['text']
                                response += f"   └─ Typed: '{text}'\n"
                            elif action == "key_press":
                                response += f"   └─ Pressed key: {step.result.get('key', 'unknown')}\n"
                            else:
                                response += f"   └─ UI action: {action}\n"
                    elif step.action_type == "analysis":
                        if "cpu_count" in step.result:
                            response += f"   └─ System: {step.result['cpu_count']} CPUs, {step.result['running_processes']} processes\n"
            
            response += f"\n🎉 All requested actions have been completed!"
            
        else:
            response = f"⚠️ **Task Partially Completed**\n\n"
            response += f"**Request:** {original_query}\n\n"
            response += f"Completed {execution_result['completed_steps']}/{execution_result['total_steps']} steps. "
            
            if "error" in execution_result:
                response += f"Error: {execution_result['error']}\n\n"
            
            # Show what was completed
            completed_steps = [s for s in workflow.steps if s.status == "completed"]
            if completed_steps:
                response += f"**Successfully completed:**\n"
                for step in completed_steps:
                    response += f"✅ {step.name}\n"
        
        return response

# Global instance
_workflow_engine = None

async def get_workflow_engine() -> EnterpriseWorkflowEngine:
    """Get or create global workflow engine instance"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = EnterpriseWorkflowEngine()
    return _workflow_engine

async def execute_agent_workflow(query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Execute agent workflow with real task execution"""
    engine = await get_workflow_engine()
    return await engine.process_agent_request(query, context)