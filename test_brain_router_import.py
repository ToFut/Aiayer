#!/usr/bin/env python3

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Testing brain router imports...")

try:
    from brain.core.brain_router import BrainRouter, ChatRequest, ChatMode, Priority, process_chat_request
    print("✅ Brain Router core loaded")
except ImportError as e:
    print(f"❌ Brain Router core failed: {e}")

try:
    from brain.handlers.enhanced_ask_mode_handler import handle_enhanced_ask_mode
    print("✅ Enhanced Ask Handler loaded")
except ImportError as e:
    print(f"❌ Enhanced Ask Handler failed: {e}")

try:
    from brain.handlers.suggest_mode_handler import handle_suggest_mode
    print("✅ Suggest Handler loaded")
except ImportError as e:
    print(f"❌ Suggest Handler failed: {e}")

try:
    from real_agent_automation_handler import handle_real_agent_automation
    print("✅ Real Automation Handler loaded")
except ImportError as e:
    print(f"❌ Real Automation Handler failed: {e}")

print("Import test complete!")