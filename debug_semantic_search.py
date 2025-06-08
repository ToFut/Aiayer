#!/usr/bin/env python3
"""
Debug Semantic Search
Comprehensive debugging of the semantic search system to identify core issues
"""
import sys
import os
import json
import asyncio
import logging
import time
import inspect
import numpy as np
from datetime import datetime
from pprint import pprint

# Add parent directory to path
sys.path.append('/Users/segevbin/Desktop/SensAI/Aiayer')

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for maximum verbosity
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Import components with detailed error handling
try:
    from memory.memory_system import MemorySystem
    logger.info("Successfully imported MemorySystem")
except ImportError as e:
    logger.error(f"Failed to import MemorySystem: {e}")
    sys.exit(1)

try:
    from memory.semantic_search_agent import SemanticSearchAgent, search_memories, add_memory
    logger.info("Successfully imported SemanticSearchAgent and functions")
except ImportError as e:
    logger.error(f"Failed to import semantic_search_agent: {e}")
    sys.exit(1)

try:
    from memory.enhanced_semantic_search import EnhancedSemanticSearch, enhanced_search
    logger.info("Successfully imported EnhancedSemanticSearch")
except ImportError as e:
    logger.error(f"Failed to import enhanced_semantic_search: {e}")
    # Continue as this might be a different implementation

# Global debug report
debug_report = {
    "timestamp": datetime.now().isoformat(),
    "system_info": {
        "python_version": sys.version,
        "platform": sys.platform
    },
    "memory_system": {},
    "search_agent": {},
    "enhanced_search": {},
    "test_results": {},
    "issues_found": [],
    "recommendations": []
}

async def debug_memory_system():
    """Debug the memory system components"""
    logger.info("======= DEBUGGING MEMORY SYSTEM =======")
    
    try:
        # Initialize memory system
        memory = MemorySystem()
        
        # Examine memory system structure
        debug_report["memory_system"]["attributes"] = dir(memory)
        debug_report["memory_system"]["methods"] = [
            method for method in dir(memory) 
            if callable(getattr(memory, method)) and not method.startswith('__')
        ]
        
        # Check memory contents
        debug_report["memory_system"]["short_term_count"] = len(memory.short_term_memory)
        debug_report["memory_system"]["long_term_count"] = len(memory.long_term_memory)
        debug_report["memory_system"]["context_count"] = len(memory.context_memory) if hasattr(memory, "context_memory") else "N/A"
        
        # Check if search methods exist
        has_search_method = hasattr(memory, "search_memory")
        debug_report["memory_system"]["has_search_method"] = has_search_method
        
        if has_search_method:
            # Examine search method signature
            search_sig = str(inspect.signature(memory.search_memory))
            debug_report["memory_system"]["search_method_signature"] = search_sig
            logger.info(f"Memory system has search_memory method with signature: {search_sig}")
        else:
            logger.warning("Memory system does not have a search_memory method")
            debug_report["issues_found"].append("Memory system lacks search_memory method")
        
        # Check integration with semantic search
        has_semantic_search = hasattr(memory, "semantic_search") or hasattr(memory, "enhanced_search")
        debug_report["memory_system"]["has_semantic_search"] = has_semantic_search
        
        logger.info(f"Memory system loaded with {debug_report['memory_system']['short_term_count']} short-term memories")
        
        # Sample memory contents
        if memory.short_term_memory:
            sample = memory.short_term_memory[0]
            debug_report["memory_system"]["sample_memory"] = {
                "type": type(sample).__name__,
                "keys": list(sample.keys()) if isinstance(sample, dict) else "Not a dict",
                "content_preview": str(sample)[:200] + "..." if len(str(sample)) > 200 else str(sample)
            }
            logger.info(f"Sample memory keys: {debug_report['memory_system']['sample_memory']['keys']}")
        
        return memory
    except Exception as e:
        logger.error(f"Error debugging memory system: {e}", exc_info=True)
        debug_report["issues_found"].append(f"Memory system error: {str(e)}")
        return None

async def debug_semantic_search_agent():
    """Debug the semantic search agent"""
    logger.info("======= DEBUGGING SEMANTIC SEARCH AGENT =======")
    
    try:
        # Initialize search agent
        search_agent = SemanticSearchAgent()
        
        # Examine search agent structure
        debug_report["search_agent"]["attributes"] = dir(search_agent)
        debug_report["search_agent"]["methods"] = [
            method for method in dir(search_agent) 
            if callable(getattr(search_agent, method)) and not method.startswith('__')
        ]
        
        # Check vector store
        has_vector_store = hasattr(search_agent, "vector_store")
        debug_report["search_agent"]["has_vector_store"] = has_vector_store
        
        if has_vector_store:
            vector_store = search_agent.vector_store
            # Get vector store stats
            debug_report["search_agent"]["vector_store_doc_count"] = len(vector_store.documents)
            debug_report["search_agent"]["vector_store_embedding_count"] = len(vector_store.embeddings)
            
            logger.info(f"Vector store has {debug_report['search_agent']['vector_store_doc_count']} documents and {debug_report['search_agent']['vector_store_embedding_count']} embeddings")
            
            # Sample vector store contents
            if vector_store.documents:
                sample_id = next(iter(vector_store.documents.keys()))
                sample_doc = vector_store.documents[sample_id]
                sample_embedding = vector_store.embeddings.get(sample_id)
                
                debug_report["search_agent"]["sample_document"] = {
                    "id": sample_id,
                    "type": type(sample_doc).__name__,
                    "has_embedding": sample_embedding is not None,
                    "embedding_shape": sample_embedding.shape if sample_embedding is not None else None,
                    "content_preview": str(sample_doc.content)[:200] + "..." if len(str(sample_doc.content)) > 200 else str(sample_doc.content)
                }
                
                logger.info(f"Sample document id: {sample_id}, has embedding: {debug_report['search_agent']['sample_document']['has_embedding']}")
        else:
            logger.warning("Search agent does not have a vector_store attribute")
            debug_report["issues_found"].append("Search agent missing vector_store")
        
        # Check search method
        has_search_method = hasattr(search_agent, "search_memories")
        debug_report["search_agent"]["has_search_method"] = has_search_method
        
        if has_search_method:
            # Examine search method signature
            search_sig = str(inspect.signature(search_agent.search_memories))
            debug_report["search_agent"]["search_method_signature"] = search_sig
            logger.info(f"Search agent has search_memories method with signature: {search_sig}")
            
            # Check for application_context parameter
            has_app_context = 'application_context' in inspect.signature(search_agent.search_memories).parameters
            debug_report["search_agent"]["supports_application_context"] = has_app_context
            
            if not has_app_context:
                logger.warning("Search agent does not support application_context parameter")
                debug_report["issues_found"].append("Missing application_context parameter in search_memories method")
        else:
            logger.warning("Search agent does not have a search_memories method")
            debug_report["issues_found"].append("Search agent lacks search_memories method")
        
        # Check embedding function
        has_embedding_fn = (hasattr(search_agent, "_compute_tfidf_embedding") or 
                           hasattr(search_agent, "embedding_fn"))
        debug_report["search_agent"]["has_embedding_function"] = has_embedding_fn
        
        return search_agent
    except Exception as e:
        logger.error(f"Error debugging semantic search agent: {e}", exc_info=True)
        debug_report["issues_found"].append(f"Semantic search agent error: {str(e)}")
        return None

async def debug_enhanced_semantic_search():
    """Debug the enhanced semantic search module"""
    logger.info("======= DEBUGGING ENHANCED SEMANTIC SEARCH =======")
    
    try:
        # Check enhanced search
        debug_report["enhanced_search"]["exists"] = 'enhanced_search' in locals() or 'enhanced_search' in globals()
        
        if not debug_report["enhanced_search"]["exists"]:
            try:
                # Try to access the global instance
                from memory.enhanced_semantic_search import enhanced_search
                debug_report["enhanced_search"]["exists"] = True
            except (ImportError, AttributeError):
                debug_report["enhanced_search"]["exists"] = False
        
        if debug_report["enhanced_search"]["exists"]:
            # Examine enhanced search structure
            debug_report["enhanced_search"]["attributes"] = dir(enhanced_search)
            debug_report["enhanced_search"]["methods"] = [
                method for method in dir(enhanced_search) 
                if callable(getattr(enhanced_search, method)) and not method.startswith('__')
            ]
            
            # Check indexed data
            debug_report["enhanced_search"]["vector_count"] = enhanced_search.vector_count
            debug_report["enhanced_search"]["memory_items_count"] = len(enhanced_search.memory_items)
            debug_report["enhanced_search"]["memory_vectors_count"] = len(enhanced_search.memory_vectors)
            
            logger.info(f"Enhanced search has {debug_report['enhanced_search']['memory_items_count']} memory items and {debug_report['enhanced_search']['memory_vectors_count']} memory vectors")
            
            # Sample enhanced search contents
            if enhanced_search.memory_items:
                sample_id = next(iter(enhanced_search.memory_items.keys()))
                sample_item = enhanced_search.memory_items[sample_id]
                sample_vector = enhanced_search.memory_vectors.get(sample_id)
                
                debug_report["enhanced_search"]["sample_item"] = {
                    "id": sample_id,
                    "type": type(sample_item).__name__,
                    "has_vector": sample_vector is not None,
                    "keys": list(sample_item.keys()) if isinstance(sample_item, dict) else "Not a dict",
                    "content_preview": str(sample_item)[:200] + "..." if len(str(sample_item)) > 200 else str(sample_item)
                }
                
                logger.info(f"Sample item id: {sample_id}, has vector: {debug_report['enhanced_search']['sample_item']['has_vector']}")
            
            # Check search method
            has_search_method = hasattr(enhanced_search, "search")
            debug_report["enhanced_search"]["has_search_method"] = has_search_method
            
            if has_search_method:
                # Examine search method signature
                search_sig = str(inspect.signature(enhanced_search.search))
                debug_report["enhanced_search"]["search_method_signature"] = search_sig
                logger.info(f"Enhanced search has search method with signature: {search_sig}")
                
                # Check for application_context parameter
                has_app_context = 'application_context' in inspect.signature(enhanced_search.search).parameters
                debug_report["enhanced_search"]["supports_application_context"] = has_app_context
                
                if has_app_context:
                    logger.info("Enhanced search supports application_context parameter")
                else:
                    logger.warning("Enhanced search does not support application_context parameter")
            else:
                logger.warning("Enhanced search does not have a search method")
                debug_report["issues_found"].append("Enhanced search lacks search method")
        else:
            logger.warning("Enhanced semantic search module not found or global instance not available")
            debug_report["issues_found"].append("Enhanced semantic search module not found")
        
        return enhanced_search if debug_report["enhanced_search"]["exists"] else None
    except Exception as e:
        logger.error(f"Error debugging enhanced semantic search: {e}", exc_info=True)
        debug_report["issues_found"].append(f"Enhanced semantic search error: {str(e)}")
        return None

async def test_search_directly(memory, search_agent, enhanced_search):
    """Test search functionality directly with debugging"""
    logger.info("======= TESTING SEARCH FUNCTIONALITY DIRECTLY =======")
    
    debug_report["test_results"]["direct_tests"] = []
    
    # Define test queries
    test_queries = [
        "development and coding",
        "memory architecture",
        "debugging errors",
        "testing search functionality",
        "AI semantic vector embeddings"
    ]
    
    # Test memory system search if available
    if memory and hasattr(memory, "search_memory"):
        logger.info("Testing memory system search_memory method...")
        memory_search_results = []
        
        for query in test_queries:
            try:
                logger.info(f"Searching memory system for: '{query}'")
                start_time = time.time()
                results = await memory.search_memory(query=query, limit=3)
                search_time = time.time() - start_time
                
                logger.info(f"Memory search for '{query}' returned {len(results)} results in {search_time:.4f}s")
                
                memory_search_results.append({
                    "query": query,
                    "result_count": len(results),
                    "search_time": search_time,
                    "success": len(results) > 0,
                    "first_result": results[0] if results else None
                })
            except Exception as e:
                logger.error(f"Error in memory search for '{query}': {e}", exc_info=True)
                memory_search_results.append({
                    "query": query,
                    "error": str(e),
                    "success": False
                })
        
        debug_report["test_results"]["memory_search"] = memory_search_results
        logger.info(f"Memory search results: {sum(1 for r in memory_search_results if r['success'])}/{len(memory_search_results)} successful")
    
    # Test semantic search agent if available
    if search_agent and hasattr(search_agent, "search_memories"):
        logger.info("Testing semantic search agent search_memories method...")
        agent_search_results = []
        
        for query in test_queries:
            try:
                logger.info(f"Searching with semantic agent for: '{query}'")
                start_time = time.time()
                results = await search_agent.search_memories(query=query, top_k=3)
                search_time = time.time() - start_time
                
                logger.info(f"Agent search for '{query}' returned {len(results)} results in {search_time:.4f}s")
                
                agent_search_results.append({
                    "query": query,
                    "result_count": len(results),
                    "search_time": search_time,
                    "success": len(results) > 0,
                    "first_result": results[0] if results else None
                })
            except Exception as e:
                logger.error(f"Error in agent search for '{query}': {e}", exc_info=True)
                agent_search_results.append({
                    "query": query,
                    "error": str(e),
                    "success": False
                })
        
        debug_report["test_results"]["agent_search"] = agent_search_results
        logger.info(f"Agent search results: {sum(1 for r in agent_search_results if r['success'])}/{len(agent_search_results)} successful")
    
    # Test enhanced semantic search if available
    if enhanced_search and hasattr(enhanced_search, "search"):
        logger.info("Testing enhanced search method...")
        enhanced_search_results = []
        
        for query in test_queries:
            try:
                logger.info(f"Searching with enhanced search for: '{query}'")
                start_time = time.time()
                results = enhanced_search.search(query=query, limit=3)
                search_time = time.time() - start_time
                
                logger.info(f"Enhanced search for '{query}' returned {len(results)} results in {search_time:.4f}s")
                
                enhanced_search_results.append({
                    "query": query,
                    "result_count": len(results),
                    "search_time": search_time,
                    "success": len(results) > 0,
                    "first_result": results[0] if results else None
                })
            except Exception as e:
                logger.error(f"Error in enhanced search for '{query}': {e}", exc_info=True)
                enhanced_search_results.append({
                    "query": query,
                    "error": str(e),
                    "success": False
                })
        
        debug_report["test_results"]["enhanced_search"] = enhanced_search_results
        logger.info(f"Enhanced search results: {sum(1 for r in enhanced_search_results if r['success'])}/{len(enhanced_search_results)} successful")

async def test_manual_vector_search(search_agent, enhanced_search):
    """Test vector search by manually computing similarities"""
    logger.info("======= TESTING MANUAL VECTOR SEARCH =======")
    
    debug_report["test_results"]["manual_vector_tests"] = []
    
    # Define test query
    test_query = "python development coding"
    
    # Test with search agent
    if search_agent and hasattr(search_agent, "vector_store") and hasattr(search_agent, "_compute_tfidf_embedding"):
        logger.info("Testing manual vector search with search agent...")
        
        try:
            # Compute query embedding
            query_vector = search_agent._compute_tfidf_embedding(test_query)
            logger.info(f"Generated query vector with shape: {query_vector.shape}")
            
            # Get sample of documents to compare
            vector_store = search_agent.vector_store
            doc_sample = list(vector_store.documents.items())[:5]
            
            manual_similarities = []
            for doc_id, doc in doc_sample:
                if doc_id in vector_store.embeddings:
                    doc_vector = vector_store.embeddings[doc_id]
                    
                    # Calculate cosine similarity
                    query_norm = np.linalg.norm(query_vector)
                    doc_norm = np.linalg.norm(doc_vector)
                    
                    if query_norm > 0 and doc_norm > 0:
                        similarity = np.dot(query_vector, doc_vector) / (query_norm * doc_norm)
                    else:
                        similarity = 0.0
                    
                    manual_similarities.append({
                        "doc_id": doc_id,
                        "similarity": float(similarity),
                        "content_preview": doc.content[:100] if hasattr(doc, "content") else str(doc)[:100]
                    })
                    
                    logger.info(f"Manual similarity for doc {doc_id}: {similarity:.4f}")
            
            # Sort by similarity
            manual_similarities.sort(key=lambda x: x["similarity"], reverse=True)
            debug_report["test_results"]["manual_vector_tests"].append({
                "method": "search_agent",
                "query": test_query,
                "similarities": manual_similarities,
                "has_results": len(manual_similarities) > 0 and manual_similarities[0]["similarity"] > 0.5
            })
            
            if manual_similarities and manual_similarities[0]["similarity"] > 0.5:
                logger.info(f"Found manual matches with highest similarity: {manual_similarities[0]['similarity']:.4f}")
            else:
                logger.warning("No significant manual matches found")
                debug_report["issues_found"].append("No significant vector similarities in manual search")
            
        except Exception as e:
            logger.error(f"Error in manual vector search with search agent: {e}", exc_info=True)
            debug_report["issues_found"].append(f"Manual vector search error: {str(e)}")
    
    # Test with enhanced search
    if enhanced_search and hasattr(enhanced_search, "embedding_fn") and hasattr(enhanced_search, "memory_vectors"):
        logger.info("Testing manual vector search with enhanced search...")
        
        try:
            # Compute query embedding
            query_vector = enhanced_search.embedding_fn(test_query)
            logger.info(f"Generated query vector with enhanced search")
            
            # Get sample of vectors to compare
            vector_sample = list(enhanced_search.memory_vectors.items())[:5]
            
            manual_similarities = []
            for item_id, item_data in vector_sample:
                if 'vector' in item_data:
                    item_vector = item_data['vector']
                    
                    # Calculate cosine similarity
                    query_norm = np.linalg.norm(query_vector)
                    item_norm = np.linalg.norm(item_vector)
                    
                    if query_norm > 0 and item_norm > 0:
                        similarity = np.dot(query_vector, item_vector) / (query_norm * item_norm)
                    else:
                        similarity = 0.0
                    
                    content = enhanced_search.memory_items.get(item_id, {})
                    content_preview = str(content)[:100] if content else "No content available"
                    
                    manual_similarities.append({
                        "item_id": item_id,
                        "similarity": float(similarity),
                        "content_preview": content_preview
                    })
                    
                    logger.info(f"Manual similarity for item {item_id}: {similarity:.4f}")
            
            # Sort by similarity
            manual_similarities.sort(key=lambda x: x["similarity"], reverse=True)
            debug_report["test_results"]["manual_vector_tests"].append({
                "method": "enhanced_search",
                "query": test_query,
                "similarities": manual_similarities,
                "has_results": len(manual_similarities) > 0 and manual_similarities[0]["similarity"] > 0.5
            })
            
            if manual_similarities and manual_similarities[0]["similarity"] > 0.5:
                logger.info(f"Found enhanced manual matches with highest similarity: {manual_similarities[0]['similarity']:.4f}")
            else:
                logger.warning("No significant enhanced manual matches found")
                debug_report["issues_found"].append("No significant vector similarities in enhanced manual search")
            
        except Exception as e:
            logger.error(f"Error in manual vector search with enhanced search: {e}", exc_info=True)
            debug_report["issues_found"].append(f"Enhanced manual vector search error: {str(e)}")

async def test_memory_addition_flow(memory, search_agent, enhanced_search):
    """Test the flow from adding memory to search"""
    logger.info("======= TESTING MEMORY ADDITION FLOW =======")
    
    debug_report["test_results"]["memory_addition_flow"] = {}
    
    # Create a unique test memory
    timestamp = int(time.time())
    test_memory_content = f"Test memory with unique timestamp {timestamp} for testing semantic search flow"
    
    # Try adding through memory system
    memory_system_addition = False
    if memory and hasattr(memory, "add_to_short_term_memory"):
        try:
            logger.info(f"Adding test memory through memory system: {test_memory_content}")
            memory_id = await memory.add_to_short_term_memory({
                "content": test_memory_content,
                "memory_type": "test_memory",
                "timestamp": datetime.now().isoformat()
            })
            
            memory_system_addition = memory_id is not None
            debug_report["test_results"]["memory_addition_flow"]["memory_system"] = {
                "success": memory_system_addition,
                "memory_id": memory_id
            }
            
            logger.info(f"Memory system addition {'successful' if memory_system_addition else 'failed'} with ID: {memory_id}")
        except Exception as e:
            logger.error(f"Error adding memory through memory system: {e}", exc_info=True)
            debug_report["test_results"]["memory_addition_flow"]["memory_system"] = {
                "success": False,
                "error": str(e)
            }
    
    # Try adding through search agent
    search_agent_addition = False
    if search_agent and hasattr(search_agent, "add_memory"):
        try:
            logger.info(f"Adding test memory through search agent")
            success = await search_agent.add_memory(
                content=f"Agent test memory with unique timestamp {timestamp}",
                source="test",
                tags={"test", "semantic_search"}
            )
            
            search_agent_addition = success
            debug_report["test_results"]["memory_addition_flow"]["search_agent"] = {
                "success": search_agent_addition
            }
            
            logger.info(f"Search agent addition {'successful' if search_agent_addition else 'failed'}")
        except Exception as e:
            logger.error(f"Error adding memory through search agent: {e}", exc_info=True)
            debug_report["test_results"]["memory_addition_flow"]["search_agent"] = {
                "success": False,
                "error": str(e)
            }
    
    # Try adding through enhanced search
    enhanced_search_addition = False
    if enhanced_search and hasattr(enhanced_search, "add_to_index"):
        try:
            logger.info(f"Adding test memory through enhanced search")
            enhanced_test_memory = {
                "id": f"test_{timestamp}",
                "content": f"Enhanced test memory with unique timestamp {timestamp}",
                "timestamp": datetime.now().isoformat(),
                "memory_type": "test_memory"
            }
            
            item_id = enhanced_search.add_to_index(
                item=enhanced_test_memory,
                memory_type="short_term"
            )
            
            enhanced_search_addition = item_id is not None
            debug_report["test_results"]["memory_addition_flow"]["enhanced_search"] = {
                "success": enhanced_search_addition,
                "item_id": item_id
            }
            
            logger.info(f"Enhanced search addition {'successful' if enhanced_search_addition else 'failed'} with ID: {item_id}")
        except Exception as e:
            logger.error(f"Error adding memory through enhanced search: {e}", exc_info=True)
            debug_report["test_results"]["memory_addition_flow"]["enhanced_search"] = {
                "success": False,
                "error": str(e)
            }
    
    # Wait a moment for indexing
    await asyncio.sleep(1)
    
    # Now try to search for this unique memory
    search_query = f"unique timestamp {timestamp}"
    
    # Test with memory system search
    if memory and hasattr(memory, "search_memory"):
        try:
            logger.info(f"Searching memory system for added test memory with query: '{search_query}'")
            results = await memory.search_memory(query=search_query, limit=3)
            
            found = any(search_query in str(result) for result in results) if results else False
            debug_report["test_results"]["memory_addition_flow"]["memory_system_search"] = {
                "query": search_query,
                "result_count": len(results),
                "found_test_memory": found
            }
            
            logger.info(f"Memory system search for test memory {'found' if found else 'did not find'} the test memory")
            
            if not found and memory_system_addition:
                debug_report["issues_found"].append("Memory system failed to find memory that was successfully added")
                
        except Exception as e:
            logger.error(f"Error searching memory system for test memory: {e}", exc_info=True)
            debug_report["test_results"]["memory_addition_flow"]["memory_system_search"] = {
                "query": search_query,
                "error": str(e)
            }
    
    # Test with search agent
    if search_agent and hasattr(search_agent, "search_memories"):
        try:
            logger.info(f"Searching with agent for added test memory with query: '{search_query}'")
            results = await search_agent.search_memories(query=search_query, top_k=3)
            
            found = any(search_query in str(result) for result in results) if results else False
            debug_report["test_results"]["memory_addition_flow"]["search_agent_search"] = {
                "query": search_query,
                "result_count": len(results),
                "found_test_memory": found
            }
            
            logger.info(f"Search agent search for test memory {'found' if found else 'did not find'} the test memory")
            
            if not found and search_agent_addition:
                debug_report["issues_found"].append("Search agent failed to find memory that was successfully added")
                
        except Exception as e:
            logger.error(f"Error searching with agent for test memory: {e}", exc_info=True)
            debug_report["test_results"]["memory_addition_flow"]["search_agent_search"] = {
                "query": search_query,
                "error": str(e)
            }
    
    # Test with enhanced search
    if enhanced_search and hasattr(enhanced_search, "search"):
        try:
            logger.info(f"Searching with enhanced search for added test memory with query: '{search_query}'")
            results = enhanced_search.search(query=search_query, limit=3)
            
            found = any(search_query in str(result) for result in results) if results else False
            debug_report["test_results"]["memory_addition_flow"]["enhanced_search_search"] = {
                "query": search_query,
                "result_count": len(results),
                "found_test_memory": found
            }
            
            logger.info(f"Enhanced search for test memory {'found' if found else 'did not find'} the test memory")
            
            if not found and enhanced_search_addition:
                debug_report["issues_found"].append("Enhanced search failed to find memory that was successfully added")
                
        except Exception as e:
            logger.error(f"Error searching with enhanced search for test memory: {e}", exc_info=True)
            debug_report["test_results"]["memory_addition_flow"]["enhanced_search_search"] = {
                "query": search_query,
                "error": str(e)
            }

def analyze_results_and_generate_recommendations():
    """Analyze debug results and generate recommendations"""
    logger.info("======= ANALYZING RESULTS AND GENERATING RECOMMENDATIONS =======")
    
    # First, check if components exist and are properly connected
    component_issues = []
    
    # Check memory system
    if "memory_system" in debug_report and debug_report["memory_system"]:
        if not debug_report["memory_system"].get("has_search_method", False):
            component_issues.append("Memory system lacks search_memory method")
        
        if not debug_report["memory_system"].get("has_semantic_search", False):
            component_issues.append("Memory system not connected to semantic search")
    else:
        component_issues.append("Memory system could not be initialized or debugged")
    
    # Check search agent
    if "search_agent" in debug_report and debug_report["search_agent"]:
        if not debug_report["search_agent"].get("has_vector_store", False):
            component_issues.append("Search agent missing vector store")
        
        if not debug_report["search_agent"].get("has_search_method", False):
            component_issues.append("Search agent lacks search_memories method")
        
        if not debug_report["search_agent"].get("has_embedding_function", False):
            component_issues.append("Search agent missing embedding function")
    else:
        component_issues.append("Search agent could not be initialized or debugged")
    
    # Check enhanced search
    if "enhanced_search" in debug_report and debug_report["enhanced_search"]:
        if not debug_report["enhanced_search"].get("exists", False):
            component_issues.append("Enhanced semantic search not found")
        
        if not debug_report["enhanced_search"].get("has_search_method", False):
            component_issues.append("Enhanced search lacks search method")
    
    # Add component issues to overall issues
    for issue in component_issues:
        if issue not in debug_report["issues_found"]:
            debug_report["issues_found"].append(issue)
    
    # Analyze test results
    test_issues = []
    
    # Check memory addition flow
    memory_flow = debug_report["test_results"].get("memory_addition_flow", {})
    
    if memory_flow.get("memory_system", {}).get("success", False) and \
       not memory_flow.get("memory_system_search", {}).get("found_test_memory", False):
        test_issues.append("Memory system not properly indexing added memories")
    
    if memory_flow.get("search_agent", {}).get("success", False) and \
       not memory_flow.get("search_agent_search", {}).get("found_test_memory", False):
        test_issues.append("Search agent not properly indexing added memories")
    
    if memory_flow.get("enhanced_search", {}).get("success", False) and \
       not memory_flow.get("enhanced_search_search", {}).get("found_test_memory", False):
        test_issues.append("Enhanced search not properly indexing added memories")
    
    # Check manual vector search
    manual_tests = debug_report["test_results"].get("manual_vector_tests", [])
    
    if any(test.get("method") == "search_agent" for test in manual_tests) and \
       not any(test.get("has_results", False) for test in manual_tests if test.get("method") == "search_agent"):
        test_issues.append("Search agent vectors not showing similarity even in manual tests")
    
    if any(test.get("method") == "enhanced_search" for test in manual_tests) and \
       not any(test.get("has_results", False) for test in manual_tests if test.get("method") == "enhanced_search"):
        test_issues.append("Enhanced search vectors not showing similarity even in manual tests")
    
    # Add test issues to overall issues
    for issue in test_issues:
        if issue not in debug_report["issues_found"]:
            debug_report["issues_found"].append(issue)
    
    # Generate recommendations based on issues
    recommendations = []
    
    if "Memory system not properly indexing added memories" in debug_report["issues_found"]:
        recommendations.append("Check the memory system's integration with search indexing - added memories should be automatically indexed")
    
    if "Search agent not properly indexing added memories" in debug_report["issues_found"]:
        recommendations.append("Verify the search agent's add_memory method is properly creating vector embeddings")
    
    if "Search agent vectors not showing similarity even in manual tests" in debug_report["issues_found"]:
        recommendations.append("The search agent's embedding function may not be producing meaningful vectors - check _compute_tfidf_embedding implementation")
    
    if "Memory system lacks search_memory method" in debug_report["issues_found"]:
        recommendations.append("Implement search_memory method in MemorySystem or ensure proper delegation to semantic search")
    
    if "Memory system not connected to semantic search" in debug_report["issues_found"]:
        recommendations.append("Connect memory system to semantic search implementation")
    
    if "Missing application_context parameter in search_memories method" in debug_report["issues_found"]:
        recommendations.append("Update search_memories method to support application_context parameter for context-aware search")
    
    # Add general recommendations if issues found
    if debug_report["issues_found"]:
        recommendations.append("Run a quick test with a new memory by directly calling the vector store's search method")
        recommendations.append("Verify vector embeddings are being properly generated and stored")
        recommendations.append("Check if there's a mismatch between embedding dimensions or normalization between storage and query")
    
    debug_report["recommendations"] = recommendations

async def main():
    """Main entry point for debugging script"""
    print("🔍 SEMANTIC SEARCH DEBUGGING")
    print("=" * 80)
    print("Running comprehensive diagnostics to identify issues with semantic search...")
    
    # Debug memory system
    memory = await debug_memory_system()
    
    # Debug semantic search agent
    search_agent = await debug_semantic_search_agent()
    
    # Debug enhanced semantic search
    enhanced_search = await debug_enhanced_semantic_search()
    
    # Test search directly
    await test_search_directly(memory, search_agent, enhanced_search)
    
    # Test manual vector search
    await test_manual_vector_search(search_agent, enhanced_search)
    
    # Test memory addition flow
    await test_memory_addition_flow(memory, search_agent, enhanced_search)
    
    # Analyze results and generate recommendations
    analyze_results_and_generate_recommendations()
    
    # Save debug report
    report_file = "semantic_search_debug_report.json"
    with open(report_file, 'w') as f:
        json.dump(debug_report, f, indent=2, default=str)
    
    # Print summary
    print("\n📊 SEMANTIC SEARCH DEBUG SUMMARY")
    print("=" * 80)
    print(f"Issues Found: {len(debug_report['issues_found'])}")
    for i, issue in enumerate(debug_report['issues_found'], 1):
        print(f"  {i}. {issue}")
    
    print("\nRecommendations:")
    for i, rec in enumerate(debug_report['recommendations'], 1):
        print(f"  {i}. {rec}")
    
    print(f"\nDetailed debug report saved to: {report_file}")

if __name__ == "__main__":
    asyncio.run(main())