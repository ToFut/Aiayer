"""
Knowledge Base Package
Provides secure and efficient storage for assistant knowledge and memories.
"""
from memory.knowledge_base.secure_store import SecureKnowledgeStore
from memory.knowledge_base.vector_store import VectorKnowledgeStore

__all__ = ['SecureKnowledgeStore', 'VectorKnowledgeStore']