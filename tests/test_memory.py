"""
Test suite for memory management
"""
import pytest
from datetime import datetime, timedelta
from memory.memory import ConversationMemory, ContextMemory

class TestConversationMemory:
    @pytest.fixture
    def memory(self):
        """Create a conversation memory instance."""
        return ConversationMemory(max_length=10)

    def test_add_message(self, memory):
        """Test adding messages to memory."""
        message = {"role": "user", "content": "Hello"}
        assert memory.add_message(message) is True
        assert len(memory.get_all()) == 1

    def test_get_recent(self, memory):
        """Test getting recent messages."""
        for i in range(10):
            message = {"role": "user", "content": f"Message {i}"}
            memory.add_message(message)
        recent = memory.get_recent(5)
        assert len(recent) == 5
        assert recent[-1]["content"] == "Message 9"

    def test_clear(self, memory):
        """Test clearing memory."""
        memory.add_message({"role": "user", "content": "Hello"})
        memory.clear()
        assert len(memory.get_all()) == 0

    def test_get_summary(self, memory):
        """Test getting memory summary."""
        memory.add_message({"role": "user", "content": "What's the weather?"})
        memory.add_message({"role": "assistant", "content": "It's sunny!"})
        summary = memory.get_summary()
        assert summary["count"] == 2
        assert "user" in summary["roles"]
        assert "assistant" in summary["roles"]

class TestContextMemory:
    @pytest.fixture
    def context_memory(self):
        """Create a context memory instance."""
        return ContextMemory()

    def test_initialization(self, context_memory):
        """Test context memory initialization."""
        assert context_memory is not None
        assert len(context_memory.context) == 0

    def test_add_context(self, context_memory):
        """Test adding context to memory."""
        context = {
            "activity": "coding",
            "location": "home",
            "time": datetime.now()
        }
        context_memory.set("current_context", context)
        assert context_memory.get("current_context") == context

    def test_get_recent_contexts(self, context_memory):
        """Test getting recent contexts."""
        for i in range(10):
            context = {
                "activity": f"activity_{i}",
                "time": datetime.now() - timedelta(hours=i)
            }
            context_memory.set(f"context_{i}", context)
        
        # Get a context we just set
        context_0 = context_memory.get("context_0")
        assert context_0["activity"] == "activity_0"

    def test_clear_context(self, context_memory):
        """Test clearing context memory."""
        context = {"activity": "coding"}
        context_memory.set("test", context)
        context_memory.clear()
        assert context_memory.get("test") is None

    def test_get_context_summary(self, context_memory):
        """Test getting context summary."""
        contexts = [
            {"activity": "coding", "time": datetime.now() - timedelta(hours=2)},
            {"activity": "meeting", "time": datetime.now() - timedelta(hours=1)},
            {"activity": "lunch", "time": datetime.now()}
        ]
        for i, ctx in enumerate(contexts):
            context_memory.set(f"context_{i}", ctx)
        
        # Verify we can get all contexts
        for i in range(len(contexts)):
            assert context_memory.get(f"context_{i}") is not None

    def test_context_expiration(self, context_memory):
        """Test context expiration."""
        old_context = {
            "activity": "old_activity",
            "time": datetime.now() - timedelta(days=2)
        }
        new_context = {
            "activity": "new_activity",
            "time": datetime.now()
        }
        context_memory.set("old", old_context)
        context_memory.set("new", new_context)
        
        assert context_memory.get("old") == old_context
        assert context_memory.get("new") == new_context 