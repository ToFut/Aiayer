#!/usr/bin/env python3
"""
Monetization Dashboard for Universal Task Automation

Provides a web-based dashboard for:
1. Monitoring automation tasks and value metrics
2. Client usage tracking and billing
3. ROI calculator for clients
4. Performance analytics

This dashboard connects to the Universal Task Loop Controller to provide
real-time insights into task execution and business value.
"""

import os
import json
import time
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import aiohttp
from aiohttp import web
import aiohttp_cors
import socket
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monetization_dashboard.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("monetization_dashboard")

# Constants
DASHBOARD_PORT = 8080
API_VERSION = "v1"
DATA_DIR = "dashboard_data"

class MonetizationDashboard:
    """
    Dashboard server providing real-time monitoring, analytics, and billing 
    for the Universal Task Automation system
    """
    
    def __init__(self, port: int = DASHBOARD_PORT):
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        
        # Ensure data directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # Load pricing tiers and client data
        self.pricing_tiers = self._load_pricing_tiers()
        self.clients = self._load_clients()
        
        # Metrics data
        self.task_metrics = {}
        self.system_metrics = {
            "start_time": time.time(),
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_time_saved": 0.0,
            "total_monetary_value": 0.0,
            "active_clients": 0,
            "system_uptime": 0.0
        }
        
        # Active connections for real-time updates
        self.active_connections = set()
        
        # Last controller state sync time
        self.last_sync_time = 0
        
        logger.info(f"Monetization Dashboard initialized on port {port}")
    
    def setup_routes(self):
        """Set up API routes for the dashboard"""
        # API routes
        self.app.router.add_get(f'/api/{API_VERSION}/status', self.handle_status)
        self.app.router.add_get(f'/api/{API_VERSION}/metrics', self.handle_metrics)
        self.app.router.add_get(f'/api/{API_VERSION}/tasks', self.handle_tasks)
        self.app.router.add_get(f'/api/{API_VERSION}/tasks/{{task_id}}', self.handle_task_details)
        self.app.router.add_get(f'/api/{API_VERSION}/clients', self.handle_clients)
        self.app.router.add_get(f'/api/{API_VERSION}/clients/{{client_id}}', self.handle_client_details)
        self.app.router.add_post(f'/api/{API_VERSION}/clients', self.handle_add_client)
        self.app.router.add_get(f'/api/{API_VERSION}/billing', self.handle_billing)
        self.app.router.add_get(f'/api/{API_VERSION}/pricing', self.handle_pricing)
        self.app.router.add_get(f'/api/{API_VERSION}/roi_calculator', self.handle_roi_calculator)
        self.app.router.add_get(f'/api/{API_VERSION}/next_steps/{{task_id}}', self.handle_next_steps)
        
        # Websocket for real-time updates
        self.app.router.add_get('/ws', self.handle_websocket)
        
        # Endpoint for controller to push updates
        self.app.router.add_post(f'/api/{API_VERSION}/update', self.handle_controller_update)
        
        # Static routes for dashboard UI
        self.app.router.add_static('/dashboard/', path='dashboard_ui/', name='dashboard')
        self.app.router.add_get('/', self.handle_root)
        
        # Set up CORS
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*"
            )
        })
        
        # Apply CORS to all routes
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    def _load_pricing_tiers(self) -> Dict[str, Any]:
        """Load pricing tiers from file or use defaults"""
        try:
            with open(f"{DATA_DIR}/pricing_tiers.json", 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Create default pricing tiers
            default_tiers = {
                "basic": {
                    "name": "Basic Automation",
                    "price_monthly": 99.99,
                    "tasks_included": 100,
                    "overage_fee": 1.50,
                    "features": [
                        "Basic task automation",
                        "Standard reports",
                        "Email support"
                    ]
                },
                "professional": {
                    "name": "Professional Automation",
                    "price_monthly": 499.99,
                    "tasks_included": 1000,
                    "overage_fee": 0.75,
                    "features": [
                        "Advanced task automation",
                        "Priority execution",
                        "Enhanced reporting",
                        "Chat support"
                    ]
                },
                "enterprise": {
                    "name": "Enterprise Automation",
                    "price_monthly": 1999.99,
                    "tasks_included": 5000,
                    "overage_fee": 0.50,
                    "features": [
                        "Unlimited task complexity",
                        "Custom integrations",
                        "Dedicated account manager",
                        "24/7 support",
                        "Advanced analytics"
                    ]
                },
                "custom": {
                    "name": "Custom Solution",
                    "price_monthly": "Custom",
                    "tasks_included": "Custom",
                    "features": [
                        "Tailored to your specific needs",
                        "Custom development",
                        "Enterprise integrations",
                        "White-glove service"
                    ]
                }
            }
            
            # Save default tiers
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(f"{DATA_DIR}/pricing_tiers.json", 'w') as f:
                json.dump(default_tiers, f, indent=2)
            
            return default_tiers
    
    def _load_clients(self) -> Dict[str, Any]:
        """Load client data from file or use empty dict"""
        try:
            with open(f"{DATA_DIR}/clients.json", 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Create empty clients file
            empty_clients = {}
            
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(f"{DATA_DIR}/clients.json", 'w') as f:
                json.dump(empty_clients, f, indent=2)
            
            return empty_clients
    
    def _save_clients(self):
        """Save client data to file"""
        with open(f"{DATA_DIR}/clients.json", 'w') as f:
            json.dump(self.clients, f, indent=2)
    
    async def sync_with_controller(self):
        """Sync dashboard data with Universal Task Loop Controller"""
        try:
            # In a real implementation, this would make an API call to the controller
            # For this demo, we'll simulate by updating from a local file if it exists
            
            controller_file = "controller_state.json"
            if os.path.exists(controller_file):
                try:
                    with open(controller_file, 'r') as f:
                        controller_data = json.load(f)
                        
                    # Update metrics with controller data
                    metrics = controller_data.get("metrics", {})
                    self.task_metrics = metrics
                    
                    # Update system metrics
                    self.system_metrics["total_tasks"] = (
                        len(controller_data.get("active_tasks", {})) + 
                        len(controller_data.get("completed_tasks", [])) + 
                        len(controller_data.get("failed_tasks", {}))
                    )
                    self.system_metrics["completed_tasks"] = len(controller_data.get("completed_tasks", []))
                    self.system_metrics["failed_tasks"] = len(controller_data.get("failed_tasks", {}))
                    
                    # Calculate aggregated metrics
                    total_time_saved = 0.0
                    total_monetary_value = 0.0
                    
                    for task_id, task_metric in metrics.items():
                        total_time_saved += task_metric.get("time_saved", 0.0)
                        total_monetary_value += task_metric.get("monetary_value", 0.0)
                    
                    self.system_metrics["total_time_saved"] = total_time_saved
                    self.system_metrics["total_monetary_value"] = total_monetary_value
                    self.system_metrics["system_uptime"] = time.time() - self.system_metrics["start_time"]
                    
                    self.last_sync_time = time.time()
                    
                    # Broadcast updates to connected clients
                    await self._broadcast_updates()
                    
                    logger.debug(f"Synced with controller: {len(metrics)} task metrics")
                    
                except (json.JSONDecodeError, KeyError) as e:
                    logger.error(f"Error parsing controller data: {e}")
            
        except Exception as e:
            logger.error(f"Error syncing with controller: {e}")
    
    async def start(self):
        """Start the dashboard server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        # Find available port if specified port is in use
        port = self.port
        while True:
            try:
                site = web.TCPSite(runner, '0.0.0.0', port)
                await site.start()
                self.port = port
                break
            except OSError:
                logger.warning(f"Port {port} is in use, trying port {port+1}")
                port += 1
                if port > self.port + 10:
                    raise Exception(f"Could not find available port after 10 attempts (tried {self.port}-{port-1})")
        
        logger.info(f"Monetization Dashboard running at http://localhost:{self.port}/")
        
        # Start periodic tasks
        asyncio.create_task(self._periodic_sync())
        
        # Keep the server running
        while True:
            await asyncio.sleep(3600)  # 1 hour
    
    async def _periodic_sync(self, interval: int = 5):
        """Periodically sync with controller and update metrics"""
        while True:
            try:
                await self.sync_with_controller()
            except Exception as e:
                logger.error(f"Error in periodic sync: {e}")
            
            await asyncio.sleep(interval)
    
    async def _broadcast_updates(self):
        """Broadcast updates to all connected websocket clients"""
        if not self.active_connections:
            return
            
        # Prepare update data
        update_data = {
            "type": "metrics_update",
            "timestamp": time.time(),
            "system_metrics": self.system_metrics,
            "task_count": len(self.task_metrics)
        }
        
        message = json.dumps(update_data)
        
        # Send to all active connections
        for ws in self.active_connections.copy():
            try:
                await ws.send_str(message)
            except Exception as e:
                logger.error(f"Error sending to websocket: {e}")
                self.active_connections.discard(ws)
    
    # API Request Handlers
    
    async def handle_root(self, request):
        """Redirect root to dashboard"""
        raise web.HTTPFound('/dashboard/')
    
    async def handle_status(self, request):
        """Handle status request"""
        status_data = {
            "status": "ok",
            "version": API_VERSION,
            "uptime": time.time() - self.system_metrics["start_time"],
            "timestamp": time.time()
        }
        
        return web.json_response(status_data)
    
    async def handle_metrics(self, request):
        """Handle metrics request"""
        # Calculate some metrics based on task data
        active_tasks = 0
        pending_tasks = 0
        
        # In a real implementation, we would get this from the controller
        
        metrics_data = {
            "system": self.system_metrics,
            "task_summary": {
                "total": self.system_metrics["total_tasks"],
                "active": active_tasks,
                "completed": self.system_metrics["completed_tasks"],
                "failed": self.system_metrics["failed_tasks"],
                "pending": pending_tasks
            },
            "value_metrics": {
                "total_time_saved": self.system_metrics["total_time_saved"],
                "total_monetary_value": self.system_metrics["total_monetary_value"],
                "hourly_value_rate": self.system_metrics["total_monetary_value"] / max(1, self.system_metrics["total_time_saved"] / 3600)
            },
            "last_update": self.last_sync_time
        }
        
        return web.json_response(metrics_data)
    
    async def handle_tasks(self, request):
        """Handle tasks list request"""
        # Get query parameters for filtering/pagination
        limit = int(request.query.get('limit', 50))
        offset = int(request.query.get('offset', 0))
        status = request.query.get('status', None)
        
        # In a real implementation, we would get this from the controller
        tasks = []
        for task_id, metrics in self.task_metrics.items():
            task_status = "unknown"
            if metrics.get("end_time"):
                task_status = "completed"
            
            if not status or task_status == status:
                tasks.append({
                    "task_id": task_id,
                    "status": task_status,
                    "progress": metrics.get("progress", 0),
                    "time_saved": metrics.get("time_saved", 0),
                    "monetary_value": metrics.get("monetary_value", 0),
                    "steps_completed": metrics.get("steps_completed", 0),
                    "steps_total": metrics.get("steps_total", 0)
                })
        
        # Apply pagination
        paginated_tasks = tasks[offset:offset + limit]
        
        response_data = {
            "total": len(tasks),
            "limit": limit,
            "offset": offset,
            "tasks": paginated_tasks
        }
        
        return web.json_response(response_data)
    
    async def handle_task_details(self, request):
        """Handle task details request"""
        task_id = request.match_info['task_id']
        
        if task_id in self.task_metrics:
            metrics = self.task_metrics[task_id]
            
            # In a real implementation, we would get more details from the controller
            task_data = {
                "task_id": task_id,
                "metrics": metrics,
                "status": "completed" if metrics.get("end_time") else "active",
                "monetary_value": metrics.get("monetary_value", 0),
                "time_saved": metrics.get("time_saved", 0)
            }
            
            return web.json_response(task_data)
        else:
            return web.json_response({"error": "Task not found"}, status=404)
    
    async def handle_clients(self, request):
        """Handle clients list request"""
        # Get query parameters for filtering/pagination
        limit = int(request.query.get('limit', 50))
        offset = int(request.query.get('offset', 0))
        
        # Create client list
        clients = []
        for client_id, client_data in self.clients.items():
            clients.append({
                "client_id": client_id,
                "name": client_data.get("name", "Unknown"),
                "tier": client_data.get("tier", "basic"),
                "active": client_data.get("active", True)
            })
        
        # Apply pagination
        paginated_clients = clients[offset:offset + limit]
        
        response_data = {
            "total": len(clients),
            "limit": limit,
            "offset": offset,
            "clients": paginated_clients
        }
        
        return web.json_response(response_data)
    
    async def handle_client_details(self, request):
        """Handle client details request"""
        client_id = request.match_info['client_id']
        
        if client_id in self.clients:
            client_data = self.clients[client_id]
            
            # Calculate client-specific metrics
            usage = client_data.get("usage", {})
            tier_info = self.pricing_tiers.get(client_data.get("tier", "basic"), {})
            
            response_data = {
                "client_id": client_id,
                "details": client_data,
                "tier_info": tier_info,
                "current_usage": usage,
                "billing": self._calculate_client_billing(client_id)
            }
            
            return web.json_response(response_data)
        else:
            return web.json_response({"error": "Client not found"}, status=404)
    
    async def handle_add_client(self, request):
        """Handle add client request"""
        try:
            # Parse request body
            data = await request.json()
            
            # Validate required fields
            required_fields = ["name", "email", "tier"]
            for field in required_fields:
                if field not in data:
                    return web.json_response({"error": f"Missing required field: {field}"}, status=400)
            
            # Generate client ID
            client_id = f"client_{uuid.uuid4().hex[:8]}"
            
            # Create client entry
            client_data = {
                "name": data["name"],
                "email": data["email"],
                "tier": data["tier"],
                "active": True,
                "created_at": time.time(),
                "contact_info": data.get("contact_info", {}),
                "settings": data.get("settings", {}),
                "usage": {
                    "tasks_used": 0,
                    "current_period_start": time.time(),
                    "current_period_end": time.time() + (30 * 24 * 60 * 60)  # 30 days
                }
            }
            
            # Store client data
            self.clients[client_id] = client_data
            self._save_clients()
            
            # Update active clients count
            self.system_metrics["active_clients"] = len([c for c in self.clients.values() if c.get("active", True)])
            
            return web.json_response({
                "success": True,
                "client_id": client_id,
                "message": "Client added successfully"
            })
            
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error adding client: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_billing(self, request):
        """Handle billing overview request"""
        # Get query parameters
        client_id = request.query.get('client_id', None)
        
        if client_id:
            # Return billing for specific client
            if client_id not in self.clients:
                return web.json_response({"error": "Client not found"}, status=404)
                
            billing_data = self._calculate_client_billing(client_id)
            return web.json_response(billing_data)
        else:
            # Return overall billing summary
            total_monthly_recurring = 0.0
            client_billings = {}
            
            for client_id, client_data in self.clients.items():
                if client_data.get("active", True):
                    client_billing = self._calculate_client_billing(client_id)
                    client_billings[client_id] = client_billing
                    total_monthly_recurring += client_billing.get("total", 0.0)
            
            billing_summary = {
                "total_monthly_recurring": total_monthly_recurring,
                "active_clients": len([c for c in self.clients.values() if c.get("active", True)]),
                "average_monthly_per_client": total_monthly_recurring / max(1, len(client_billings)),
                "client_breakdown": client_billings
            }
            
            return web.json_response(billing_summary)
    
    def _calculate_client_billing(self, client_id: str) -> Dict[str, Any]:
        """Calculate billing for a specific client"""
        if client_id not in self.clients:
            return {}
            
        client_data = self.clients[client_id]
        tier_name = client_data.get("tier", "basic")
        tier_info = self.pricing_tiers.get(tier_name, {})
        
        # Get usage data
        usage = client_data.get("usage", {})
        tasks_used = usage.get("tasks_used", 0)
        tasks_included = tier_info.get("tasks_included", 0)
        
        # Calculate overage
        if isinstance(tasks_included, int):
            overage_tasks = max(0, tasks_used - tasks_included)
            overage_fee = tier_info.get("overage_fee", 0.0)
            overage_amount = overage_tasks * overage_fee
        else:
            # Handle "Custom" tier
            overage_tasks = 0
            overage_amount = 0.0
        
        # Calculate base fee
        if isinstance(tier_info.get("price_monthly"), (int, float)):
            base_fee = tier_info.get("price_monthly", 0.0)
        else:
            # Handle "Custom" pricing
            base_fee = 0.0
        
        # Calculate total
        total = base_fee + overage_amount
        
        return {
            "client_id": client_id,
            "tier": tier_name,
            "base_fee": base_fee,
            "tasks_used": tasks_used,
            "tasks_included": tasks_included,
            "overage_tasks": overage_tasks,
            "overage_fee_per_task": tier_info.get("overage_fee", 0.0),
            "overage_amount": overage_amount,
            "total": total,
            "period_start": usage.get("current_period_start", 0),
            "period_end": usage.get("current_period_end", 0)
        }
    
    async def handle_pricing(self, request):
        """Handle pricing tiers request"""
        return web.json_response(self.pricing_tiers)
    
    async def handle_next_steps(self, request):
        """Handle next step suggestions request"""
        # Get query parameters
        task_id = request.match_info.get('task_id', None)
        
        if not task_id:
            return web.json_response({"error": "Task ID is required"}, status=400)
            
        try:
            # Import universal task controller if available
            from universal_task_loop_controller import get_next_step_suggestions
            
            # Get next step suggestions
            suggestions = await get_next_step_suggestions(task_id)
            
            return web.json_response(suggestions)
            
        except ImportError:
            logger.error("Universal task controller not available")
            return web.json_response({
                "success": False,
                "message": "Next step suggestions feature not available",
                "suggestions": []
            })
        except Exception as e:
            logger.error(f"Error getting next step suggestions: {e}")
            return web.json_response({
                "success": False,
                "error": str(e),
                "message": "Error getting next step suggestions"
            }, status=500)
    
    async def handle_roi_calculator(self, request):
        """Handle ROI calculator request"""
        # Get query parameters
        hourly_rate = float(request.query.get('hourly_rate', 50.0))
        employees = int(request.query.get('employees', 1))
        hours_per_week = float(request.query.get('hours_per_week', 40.0))
        automation_percentage = float(request.query.get('automation_percentage', 20.0)) / 100.0
        tier = request.query.get('tier', 'professional')
        
        # Calculate ROI
        tier_info = self.pricing_tiers.get(tier, self.pricing_tiers["professional"])
        
        # Weekly cost without automation
        weekly_labor_cost = hourly_rate * hours_per_week * employees
        annual_labor_cost = weekly_labor_cost * 52
        
        # Time saved with automation
        weekly_hours_saved = hours_per_week * automation_percentage * employees
        annual_hours_saved = weekly_hours_saved * 52
        
        # Value of time saved
        weekly_value_saved = weekly_hours_saved * hourly_rate
        annual_value_saved = annual_hours_saved * hourly_rate
        
        # Cost of service
        if isinstance(tier_info.get("price_monthly"), (int, float)):
            monthly_service_cost = tier_info.get("price_monthly", 0.0)
            annual_service_cost = monthly_service_cost * 12
        else:
            # Handle "Custom" pricing
            monthly_service_cost = 0.0
            annual_service_cost = 0.0
        
        # Calculate ROI
        net_annual_savings = annual_value_saved - annual_service_cost
        roi_percentage = (net_annual_savings / annual_service_cost) * 100 if annual_service_cost > 0 else 0
        
        roi_data = {
            "inputs": {
                "hourly_rate": hourly_rate,
                "employees": employees,
                "hours_per_week": hours_per_week,
                "automation_percentage": automation_percentage * 100,
                "tier": tier
            },
            "calculations": {
                "weekly_labor_cost": weekly_labor_cost,
                "annual_labor_cost": annual_labor_cost,
                "weekly_hours_saved": weekly_hours_saved,
                "annual_hours_saved": annual_hours_saved,
                "weekly_value_saved": weekly_value_saved,
                "annual_value_saved": annual_value_saved,
                "monthly_service_cost": monthly_service_cost,
                "annual_service_cost": annual_service_cost,
                "net_annual_savings": net_annual_savings,
                "roi_percentage": roi_percentage,
                "payback_period_months": (annual_service_cost / annual_value_saved) * 12 if annual_value_saved > 0 else 0
            }
        }
        
        return web.json_response(roi_data)
    
    async def handle_controller_update(self, request):
        """Handle update from controller"""
        try:
            # Parse request body
            data = await request.json()
            
            # Update metrics
            if "metrics" in data:
                task_metrics = data["metrics"]
                self.task_metrics.update(task_metrics)
            
            # Update system metrics
            if "system_metrics" in data:
                self.system_metrics.update(data["system_metrics"])
            
            # Update client usage if provided
            if "client_usage" in data and "client_id" in data:
                client_id = data["client_id"]
                if client_id in self.clients:
                    client_data = self.clients[client_id]
                    client_data["usage"] = data["client_usage"]
                    self._save_clients()
            
            # Broadcast updates to connected clients
            await self._broadcast_updates()
            
            return web.json_response({"success": True})
            
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            logger.error(f"Error processing controller update: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_websocket(self, request):
        """Handle websocket connection for real-time updates"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        # Add to active connections
        self.active_connections.add(ws)
        logger.info(f"New websocket connection, total connections: {len(self.active_connections)}")
        
        # Send initial data
        initial_data = {
            "type": "initial_data",
            "system_metrics": self.system_metrics,
            "timestamp": time.time()
        }
        
        await ws.send_str(json.dumps(initial_data))
        
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        if data.get("action") == "get_metrics":
                            # Send latest metrics
                            await ws.send_str(json.dumps({
                                "type": "metrics_update",
                                "system_metrics": self.system_metrics,
                                "timestamp": time.time()
                            }))
                        
                    except json.JSONDecodeError:
                        logger.warning("Received invalid JSON over websocket")
                        
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"Websocket connection closed with exception {ws.exception()}")
                    break
        finally:
            # Remove from active connections
            self.active_connections.discard(ws)
            logger.info(f"Websocket connection closed, remaining connections: {len(self.active_connections)}")
        
        return ws

# HTML templates for simple dashboard UI
INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Automation Value Dashboard</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css">
    <style>
        body { padding-top: 20px; }
        .metric-card {
            height: 100%;
            transition: transform 0.2s;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .value-metric {
            font-size: 2rem;
            font-weight: bold;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #666;
        }
        .chart-container {
            height: 300px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="d-flex justify-content-between align-items-center mb-4">
            <h1>Automation Value Dashboard</h1>
            <div class="badge bg-success p-2">Live</div>
        </header>
        
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title">Tasks Completed</h5>
                        <div class="value-metric" id="tasks-completed">0</div>
                        <div class="metric-label">total automated tasks</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title">Time Saved</h5>
                        <div class="value-metric" id="time-saved">0</div>
                        <div class="metric-label">hours of manual work</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title">Value Generated</h5>
                        <div class="value-metric" id="value-generated">$0</div>
                        <div class="metric-label">based on time savings</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <h5 class="card-title">Active Clients</h5>
                        <div class="value-metric" id="active-clients">0</div>
                        <div class="metric-label">using the platform</div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mb-4">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5>Value Trend</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="valueChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>Task Distribution</h5>
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="taskDistribution"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5>Recent Tasks</h5>
                        <a href="#" class="btn btn-sm btn-primary">View All</a>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Task</th>
                                        <th>Status</th>
                                        <th>Time Saved</th>
                                        <th>Value</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="recent-tasks">
                                    <tr>
                                        <td colspan="5" class="text-center">Loading tasks...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Next Step Suggestions -->
            <div class="col-md-6 mb-4">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5>Next Step Suggestions</h5>
                        <div>
                            <select id="task-selector" class="form-select form-select-sm">
                                <option value="">Select a task</option>
                            </select>
                        </div>
                    </div>
                    <div class="card-body">
                        <div id="next-steps-container">
                            <div class="text-center text-muted">
                                <p>Select a completed task to view next step suggestions</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5>ROI Calculator</h5>
                        <button id="calculate-roi" class="btn btn-sm btn-success">Calculate</button>
                    </div>
                    <div class="card-body">
                        <form id="roi-form">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label for="hourly-rate" class="form-label">Hourly Rate ($)</label>
                                    <input type="number" class="form-control" id="hourly-rate" value="50">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label for="employees" class="form-label">Employees</label>
                                    <input type="number" class="form-control" id="employees" value="5">
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label for="hours-per-week" class="form-label">Hours Per Week</label>
                                    <input type="number" class="form-control" id="hours-per-week" value="40">
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label for="automation-percentage" class="form-label">Automation %</label>
                                    <input type="number" class="form-control" id="automation-percentage" value="20">
                                </div>
                            </div>
                            <div class="mb-3">
                                <label for="tier" class="form-label">Service Tier</label>
                                <select class="form-select" id="tier">
                                    <option value="basic">Basic</option>
                                    <option value="professional" selected>Professional</option>
                                    <option value="enterprise">Enterprise</option>
                                </select>
                            </div>
                        </form>
                        
                        <div id="roi-results" class="mt-3 p-3 bg-light rounded">
                            <div class="row">
                                <div class="col-md-6">
                                    <div class="fw-bold">Annual Savings</div>
                                    <div class="h4 text-success" id="annual-savings">$0</div>
                                </div>
                                <div class="col-md-6">
                                    <div class="fw-bold">ROI</div>
                                    <div class="h4 text-primary" id="roi-percentage">0%</div>
                                </div>
                            </div>
                            <div class="row mt-2">
                                <div class="col-md-6">
                                    <div class="fw-bold">Hours Saved Annually</div>
                                    <div id="annual-hours-saved">0</div>
                                </div>
                                <div class="col-md-6">
                                    <div class="fw-bold">Payback Period</div>
                                    <div id="payback-period">0 months</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Dashboard functionality
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize websocket connection
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            let ws = new WebSocket(wsUrl);
            
            // Sample data for charts
            let valueChartData = {
                labels: Array.from({length: 30}, (_, i) => `Day ${i+1}`),
                datasets: [{
                    label: 'Daily Value Generated',
                    data: Array.from({length: 30}, () => Math.floor(Math.random() * 1000)),
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.4,
                    fill: true
                }]
            };
            
            let taskDistributionData = {
                labels: ['Completed', 'In Progress', 'Failed'],
                datasets: [{
                    data: [70, 20, 10],
                    backgroundColor: ['#28a745', '#007bff', '#dc3545']
                }]
            };
            
            // Initialize charts
            const valueChart = new Chart(document.getElementById('valueChart'), {
                type: 'line',
                data: valueChartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value;
                                }
                            }
                        }
                    }
                }
            });
            
            const taskDistribution = new Chart(document.getElementById('taskDistribution'), {
                type: 'doughnut',
                data: taskDistributionData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
            
            // Handle websocket messages
            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'initial_data' || data.type === 'metrics_update') {
                        updateDashboardMetrics(data.system_metrics);
                    }
                } catch (e) {
                    console.error('Error parsing websocket message:', e);
                }
            };
            
            ws.onclose = function() {
                console.log('WebSocket connection closed');
                // Try to reconnect after a delay
                setTimeout(function() {
                    ws = new WebSocket(wsUrl);
                }, 5000);
            };
            
            // Update dashboard metrics
            function updateDashboardMetrics(metrics) {
                document.getElementById('tasks-completed').textContent = metrics.completed_tasks || 0;
                
                const timeInHours = (metrics.total_time_saved || 0) / 3600;
                document.getElementById('time-saved').textContent = timeInHours.toFixed(1);
                
                const formattedValue = new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                    maximumFractionDigits: 0
                }).format(metrics.total_monetary_value || 0);
                document.getElementById('value-generated').textContent = formattedValue;
                
                document.getElementById('active-clients').textContent = metrics.active_clients || 0;
                
                // Update recent tasks (would come from API in real implementation)
                updateRecentTasks();
            }
            
            // Simulate recent tasks
            function updateRecentTasks() {
                const taskNames = [
                    'Process Mailchimp Campaign', 
                    'Update CRM Contacts', 
                    'Generate Monthly Report',
                    'Process Invoices',
                    'Update Website Content'
                ];
                
                const statuses = ['Completed', 'In Progress', 'Completed', 'Completed', 'Failed'];
                const timeSaved = [1.5, 0.8, 2.2, 1.1, 0.5];
                const values = [75, 40, 110, 55, 25];
                
                let html = '';
                
                for (let i = 0; i < 5; i++) {
                    const statusClass = 
                        statuses[i] === 'Completed' ? 'success' : 
                        statuses[i] === 'In Progress' ? 'primary' : 'danger';
                    
                    const taskId = `task_${Date.now()}_${i}`;
                    
                    html += `
                        <tr data-task-id="${taskId}">
                            <td>${taskNames[i]}</td>
                            <td><span class="badge bg-${statusClass}">${statuses[i]}</span></td>
                            <td>${timeSaved[i]} hours</td>
                            <td>$${values[i]}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary suggestions-btn"
                                        onclick="document.getElementById('task-selector').value='${taskId}';
                                                 document.getElementById('task-selector').dispatchEvent(new Event('change'));">
                                    Suggestions
                                </button>
                            </td>
                        </tr>
                    `;
                }
                
                document.getElementById('recent-tasks').innerHTML = html;
            }
            
            // ROI Calculator
            document.getElementById('calculate-roi').addEventListener('click', function() {
                const hourlyRate = parseFloat(document.getElementById('hourly-rate').value);
                const employees = parseInt(document.getElementById('employees').value);
                const hoursPerWeek = parseFloat(document.getElementById('hours-per-week').value);
                const automationPercentage = parseFloat(document.getElementById('automation-percentage').value);
                const tier = document.getElementById('tier').value;
                
                // Calculate ROI
                const weeklyLaborCost = hourlyRate * hoursPerWeek * employees;
                const annualLaborCost = weeklyLaborCost * 52;
                
                const weeklyHoursSaved = hoursPerWeek * (automationPercentage / 100) * employees;
                const annualHoursSaved = weeklyHoursSaved * 52;
                
                const annualValueSaved = annualHoursSaved * hourlyRate;
                
                // Tier pricing
                const tierPricing = {
                    basic: 99.99,
                    professional: 499.99,
                    enterprise: 1999.99
                };
                
                const monthlyServiceCost = tierPricing[tier];
                const annualServiceCost = monthlyServiceCost * 12;
                
                const netAnnualSavings = annualValueSaved - annualServiceCost;
                const roiPercentage = (netAnnualSavings / annualServiceCost) * 100;
                const paybackMonths = (annualServiceCost / annualValueSaved) * 12;
                
                // Update UI
                document.getElementById('annual-savings').textContent = new Intl.NumberFormat('en-US', {
                    style: 'currency',
                    currency: 'USD',
                    maximumFractionDigits: 0
                }).format(netAnnualSavings);
                
                document.getElementById('roi-percentage').textContent = roiPercentage.toFixed(1) + '%';
                document.getElementById('annual-hours-saved').textContent = annualHoursSaved.toFixed(1) + ' hours';
                document.getElementById('payback-period').textContent = paybackMonths.toFixed(1) + ' months';
            });
            
            // Initial ROI calculation
            document.getElementById('calculate-roi').click();
            
            // Next Step Suggestions
            document.getElementById('task-selector').addEventListener('change', async function() {
                const taskId = this.value;
                if (!taskId) {
                    document.getElementById('next-steps-container').innerHTML = `
                        <div class="text-center text-muted">
                            <p>Select a completed task to view next step suggestions</p>
                        </div>
                    `;
                    return;
                }
                
                try {
                    // Fetch next step suggestions
                    const response = await fetch(`/api/${API_VERSION}/next_steps/${taskId}`);
                    const data = await response.json();
                    
                    if (!data.success || !data.suggestions || data.suggestions.length === 0) {
                        document.getElementById('next-steps-container').innerHTML = `
                            <div class="text-center text-muted">
                                <p>No suggestions available for this task</p>
                            </div>
                        `;
                        return;
                    }
                    
                    // Display suggestions
                    let html = '';
                    
                    for (const suggestion of data.suggestions) {
                        const priorityClass = 
                            suggestion.priority > 0.7 ? 'danger' : 
                            suggestion.priority > 0.4 ? 'warning' : 'info';
                            
                        html += `
                            <div class="card mb-2 suggestion-card">
                                <div class="card-body p-3">
                                    <div class="d-flex justify-content-between align-items-start">
                                        <div>
                                            <h6 class="mb-1">${suggestion.title}</h6>
                                            <p class="mb-1 text-muted small">${suggestion.description}</p>
                                            <div class="mt-2">
                                                <span class="badge bg-${priorityClass} me-2">Priority: ${Math.round(suggestion.priority * 100)}%</span>
                                                <span class="badge bg-secondary">${suggestion.type}</span>
                                            </div>
                                        </div>
                                        <button class="btn btn-sm btn-primary execute-suggestion" 
                                                data-command="${suggestion.command_template || ''}"
                                                data-title="${suggestion.title}">
                                            Execute
                                        </button>
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    
                    document.getElementById('next-steps-container').innerHTML = html;
                    
                    // Add event listeners to execute buttons
                    document.querySelectorAll('.execute-suggestion').forEach(button => {
                        button.addEventListener('click', function() {
                            const command = this.getAttribute('data-command');
                            const title = this.getAttribute('data-title');
                            
                            // Simulate execution for demo
                            alert(`Executing suggestion: ${title}\nCommand: ${command}`);
                            
                            // In a real implementation, this would submit a new task
                            // using the universal task controller
                        });
                    });
                    
                } catch (error) {
                    console.error('Error fetching next step suggestions:', error);
                    document.getElementById('next-steps-container').innerHTML = `
                        <div class="text-center text-danger">
                            <p>Error fetching suggestions: ${error.message}</p>
                        </div>
                    `;
                }
            });
            
            // Populate task selector with completed tasks
            async function populateTaskSelector() {
                try {
                    const response = await fetch(`/api/${API_VERSION}/tasks?status=completed`);
                    const data = await response.json();
                    
                    const selector = document.getElementById('task-selector');
                    selector.innerHTML = '<option value="">Select a task</option>';
                    
                    if (data.tasks && data.tasks.length > 0) {
                        for (const task of data.tasks) {
                            const option = document.createElement('option');
                            option.value = task.task_id;
                            option.textContent = task.task_id;
                            selector.appendChild(option);
                        }
                    }
                } catch (error) {
                    console.error('Error fetching tasks:', error);
                }
            }
            
            // Call once on load
            populateTaskSelector();
            
            // Update tasks table with suggestion buttons
            function updateRecentTasksWithSuggestions() {
                const taskRows = document.querySelectorAll('#recent-tasks tr');
                taskRows.forEach(row => {
                    if (!row.querySelector('.suggestions-btn')) {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 4) {
                            const actionsCell = document.createElement('td');
                            const taskId = row.getAttribute('data-task-id');
                            if (taskId) {
                                actionsCell.innerHTML = `
                                    <button class="btn btn-sm btn-outline-primary suggestions-btn"
                                            onclick="document.getElementById('task-selector').value='${taskId}';
                                                     document.getElementById('task-selector').dispatchEvent(new Event('change'));">
                                        <i class="bi bi-lightbulb"></i> Suggestions
                                    </button>
                                `;
                                row.appendChild(actionsCell);
                            }
                        }
                    }
                });
            }
            
            // Update when tasks are updated
            const originalUpdateRecentTasks = updateRecentTasks;
            updateRecentTasks = function() {
                originalUpdateRecentTasks();
                updateRecentTasksWithSuggestions();
            };
        });
    </script>
</body>
</html>
"""

# Create dashboard UI files
async def create_dashboard_files():
    """Create simple dashboard UI files"""
    os.makedirs("dashboard_ui", exist_ok=True)
    
    # Create index.html
    with open("dashboard_ui/index.html", "w") as f:
        f.write(INDEX_HTML)

async def main():
    # Create dashboard files
    await create_dashboard_files()
    
    # Start dashboard server
    dashboard = MonetizationDashboard()
    await dashboard.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Dashboard shutdown by user")
    except Exception as e:
        logger.error(f"Error running dashboard: {e}")