# Port Architecture for SensAI/Aiayer System

This document explains the standardized port architecture for the SensAI/Aiayer system. Understanding this architecture is critical for debugging connection issues and ensuring components can communicate correctly.

## Port Overview

| Port | Service | Purpose |
|------|---------|---------|
| 8765 | DO Button WebSocket Server | Automation execution, interactive confirmations |
| 8767 | Enhanced Enterprise Backend | AI/LLM services, chat processing, memory integration |

## Port 8765: DO Button WebSocket Server

**Purpose:**
- Handles direct automation requests ("DO" button actions)
- Processes agent confirmations for executing automation plans
- Manages notifications/suggestions in proactive mode
- Supports real mouse and keyboard input control

**Components:**
- Server: `direct_coordinate_automation.py`
- Client: Overlay application (via config.js `doButton` configuration)

**Key Characteristics:**
- Guaranteed response even when backend is busy
- Direct coordinate execution for UI automation
- Real-time progress feedback
- Supports agent confirmation messages

## Port 8767: Enhanced Enterprise Backend

**Purpose:**
- Main AI backend server
- Processes all chat modes (Ask, Agent, Suggest, General)
- Semantic search and memory integration
- Context-aware responses and brain router

**Components:**
- Server: `real_llm_backend_8767.py` or `enhanced_enterprise_backend_with_context.py`
- Client: Overlay application (via config.js `llm`, `bridge`, and `backend` configurations)

**Key Characteristics:**
- Primary AI service endpoint
- Handles contextual memory
- Supports LLM integration
- Processes all chat modes

## Common Issues and Solutions

### No Responses in Overlay

If you're not receiving responses in the overlay:

1. Check that the overlay config is correctly pointing to port 8767:
   - `overlay/src/config.js` should have `llm`, `bridge`, and `backend` all set to `ws://localhost:8767`
   - `overlay/src/services/bridge.js` should default to `ws://localhost:8767`

2. Verify both servers are running:
   - `lsof -i :8765` should show the DO Button server
   - `lsof -i :8767` should show the Enhanced Backend

3. Run the diagnostic tool:
   - `python3 debug_overlay_websocket.py` to test all connections

### Debugging Commands

```bash
# Check what's listening on each port
lsof -i :8765
lsof -i :8767

# Restart the entire system with fixed port configuration
./restart_complete_system.sh

# Test connections to all ports
python3 debug_overlay_websocket.py
```

## Configuration Files

The following files contain port configuration that should be aligned:

1. **Overlay Configuration:**
   - `/overlay/src/config.js` - Main client configuration 
   - `/overlay/src/services/bridge.js` - Client WebSocket bridge

2. **Server Implementations:**
   - `/direct_coordinate_automation.py` - DO Button Server
   - `/real_llm_backend_8767.py` - Main Backend

3. **Startup Scripts:**
   - `/RESTART_FIXED_SYSTEM.sh` - Backend restart
   - `/RESTART_OVERLAY.sh` - Overlay restart
   - `/restart_complete_system.sh` - Complete system restart