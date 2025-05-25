
# Monkey patch for get_context_for_query to use fixed implementation
import asyncio
from fix_chat_interface_visual_integration import FixedVisualMemoryAgent

# Replace the problematic function with our fixed version
_fixed_agent = FixedVisualMemoryAgent()

async def get_context_for_query(query: str, **kwargs):
    """Fixed version that actually works with visual queries"""
    return await _fixed_agent.get_context_for_query(query)

# Patch the global function
import memory.semantic_search_agent as ssa
ssa.get_context_for_query = get_context_for_query

print("✅ Semantic search agent patched with working visual memory!")
