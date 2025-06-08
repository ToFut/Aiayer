#!/bin/bash

# Fix DO Button in Neural UI
echo "=== Fixing DO Button in Neural UI ==="
echo "This script will fix the 'Available plans: None' issue with the DO button in Neural UI setup"

# Step 1: Apply the pending_plans fix
echo ""
echo "Step 1: Applying shared pending_plans fix..."
python3 fix_do_button_pending_plans.py

# Step 2: Fix plan_persistence imports
echo ""
echo "Step 2: Fixing plan_persistence imports..."

# Apply fix to fix_do_button_connection_bridge.py
echo "Fixing plan_persistence imports in fix_do_button_connection_bridge.py"
sed -i.persistence.bak "s/from plan_persistence import save_plan, load_plan/import plan_persistence\n    # Direct access to the functions from the module\n    load_plan = plan_persistence.load_plan\n    save_plan = plan_persistence.save_plan/" fix_do_button_connection_bridge.py 2>/dev/null || true

# Add fallback implementation if AttributeError occurs
if ! grep -q "except AttributeError as e" fix_do_button_connection_bridge.py; then
    echo "Adding fallback implementation for plan_persistence functions"
    awk '{print} /PLAN_PERSISTENCE_AVAILABLE = False/ {print "\nexcept AttributeError as e:\n    logger.warning(f\"⚠️ Plan persistence module missing function: {e}\")\n    # Create simple fallback implementations\n    async def save_plan(plan_id, plan_data):\n        """Fallback implementation of save_plan"""\n        active_plans[plan_id] = plan_data\n        logger.info(f\"💾 Plan {plan_id} saved to memory (persistence not available)\")\n        return True\n        \n    async def load_plan(plan_id):\n        """Fallback implementation of load_plan"""\n        if plan_id in active_plans:\n            logger.info(f\"📂 Plan {plan_id} loaded from memory (persistence not available)\")\n            return active_plans[plan_id]\n        return None\n    \n    PLAN_PERSISTENCE_AVAILABLE = True\n    logger.info(\"✅ Using fallback plan persistence functions\")"}' fix_do_button_connection_bridge.py > fix_do_button_connection_bridge.py.fixed
    mv fix_do_button_connection_bridge.py.fixed fix_do_button_connection_bridge.py
    chmod +x fix_do_button_connection_bridge.py
fi

# Apply the same fix to neural_ui_do_button_handler.py if it exists
if [ -f "neural_ui_do_button_handler.py" ]; then
    echo "Fixing plan_persistence imports in neural_ui_do_button_handler.py"
    sed -i.persistence.bak "s/from plan_persistence import save_plan, load_plan/import plan_persistence\n    # Direct access to the functions from the module\n    load_plan = plan_persistence.load_plan\n    save_plan = plan_persistence.save_plan/" neural_ui_do_button_handler.py 2>/dev/null || true
    
    # Add fallback implementation if AttributeError occurs
    if ! grep -q "except AttributeError as e" neural_ui_do_button_handler.py; then
        echo "Adding fallback implementation for plan_persistence functions"
        awk '{print} /PLAN_PERSISTENCE_AVAILABLE = False/ {print "\nexcept AttributeError as e:\n    logger.warning(f\"⚠️ Plan persistence module missing function: {e}\")\n    # Create simple fallback implementations\n    async def save_plan(plan_id, plan_data):\n        """Fallback implementation of save_plan"""\n        active_plans[plan_id] = plan_data\n        logger.info(f\"💾 Plan {plan_id} saved to memory (persistence not available)\")\n        return True\n        \n    async def load_plan(plan_id):\n        """Fallback implementation of load_plan"""\n        if plan_id in active_plans:\n            logger.info(f\"📂 Plan {plan_id} loaded from memory (persistence not available)\")\n            return active_plans[plan_id]\n        return None\n    \n    PLAN_PERSISTENCE_AVAILABLE = True\n    logger.info(\"✅ Using fallback plan persistence functions\")"}' neural_ui_do_button_handler.py > neural_ui_do_button_handler.py.fixed
        mv neural_ui_do_button_handler.py.fixed neural_ui_do_button_handler.py
        chmod +x neural_ui_do_button_handler.py
    fi
fi

# Step 3: Test the fix
echo ""
echo "Step 3: Testing the fix..."
python3 test_do_button_shared_plans.py

# Step 4: Restart the system
echo ""
echo "Step 4: Instructions to apply the fix"
echo "To apply the fix, you need to restart the system:"
echo "1. Run STOP_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh"
echo "2. Run START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh"
echo ""
echo "Would you like to restart the system now? (y/n)"
read -r restart_choice
if [[ "$restart_choice" == "y" || "$restart_choice" == "Y" ]]; then
    echo "Restarting the system..."
    ./STOP_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh
    sleep 3
    ./START_ENHANCED_SYSTEM_WITH_NEURAL_UI.sh
else
    echo "System not restarted. Please restart manually when ready."
fi