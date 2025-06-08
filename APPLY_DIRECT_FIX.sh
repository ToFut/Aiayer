#!/bin/bash
# Apply Direct Fix for Universal Automation Handler
# This script applies a direct fix for the missing _create_advanced_llm_plan method

echo "🔧 APPLYING DIRECT FIX FOR UNIVERSAL AUTOMATION HANDLER..."

# Stop any running services
echo "🛑 Stopping existing processes..."
./STOP_FIXED_SYSTEM.sh >/dev/null 2>&1

# Run the direct fix script
echo "🛠️ Running direct_fix_universal_automation.py..."
python3 direct_fix_universal_automation.py

# Check if fix was successful
if [ $? -eq 0 ]; then
    echo "✅ Direct fix completed successfully!"
else
    echo "⚠️ Direct fix encountered issues. Check logs for details."
fi

# Restart the system with all fixes applied
echo ""
echo "🔄 Restarting the system to apply changes..."
./RESTART_FIXED_SYSTEM.sh

echo ""
echo "🧪 To test Agent mode automation, try this query:"
echo "   'search for python programming tutorials on google'"
echo ""
echo "📋 If you encounter any issues, check these logs:"
echo "   - Backend: tail -f logs/backend/real_llm_8767.log"
echo "   - Universal Automation: tail -f logs/backend/enhanced_enterprise_8767_context.log"