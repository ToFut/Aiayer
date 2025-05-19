# Semantic Search Implementation

This document explains how to use the enhanced semantic search functionality in the overlay system.

## Overview

The semantic search implementation uses vector embeddings to find relevant information based on meaning rather than just keywords. This results in more accurate search results and better context understanding.

## Components

1. **Memory System** - Stores and manages memory items with vector embeddings
2. **Memory Bridge** - Connects clients to the server with enhanced search capabilities
3. **WebSocket Server** - Provides communication between components
4. **Test Utilities** - Tools to verify search functionality

## Features

- **Vector-based semantic search** - Uses sentence transformers to create vector embeddings
- **Automatic fallback** - Falls back to token-based search when vectors aren't available
- **Context awareness** - Understands the context of conversations
- **Robust connectivity** - Handles connection issues and disconnections gracefully

## Getting Started

### Starting the System

To start the complete system with semantic search:

```bash
./start_memory_search_system.sh
```

This will start the memory system, WebSocket server, and memory bridge.

### Testing the System

You can test the semantic search functionality using the provided test utility:

```bash
# Interactive mode
./test_semantic_search_websocket.py

# Automated test
./test_semantic_search_websocket.py --test
```

### Stopping the System

To stop all components:

```bash
./stop_memory_search_system.sh
```

## Usage

### In the Overlay UI

The overlay UI should connect to the memory bridge WebSocket server running on `ws://localhost:8766` instead of directly connecting to the main WebSocket server on port 8765.

Users can perform semantic searches by asking questions like:
- "search for information about X"
- "find details related to Y"
- "what do you remember about Z"

### Advanced Configuration

The memory bridge uses the following configuration by default:
- Main WebSocket server: `ws://localhost:8765`
- Memory bridge server: `ws://localhost:8766`
- Maximum memory items: 100
- Vector model: 'all-MiniLM-L6-v2' (automatically falls back to token search if unavailable)

## Technical Details

### Vector Search

The semantic search uses the following process:
1. Text is encoded into vector embeddings using sentence transformers
2. When a query is received, it's also encoded into a vector
3. Cosine similarity is calculated between the query vector and all memory vectors
4. Results are sorted by similarity score and returned

### Token Search Fallback

If vector search is unavailable (missing dependencies or errors), the system falls back to token-based search:
1. Text is tokenized into words
2. Overlapping tokens between query and memories are counted
3. Scores are calculated based on token overlap and sequence matches
4. Results are sorted by score and returned

## Troubleshooting

### Common Issues

1. **Connection errors**
   - Ensure all components are running (`./start_memory_search_system.sh`)
   - Check logs in the `logs/` directory

2. **Search not working**
   - Verify that the client is connecting to port 8766 (bridge) not 8765
   - Check if vector model is available in logs
   - Try using the test utility to isolate issues

3. **Poor search results**
   - Seed the memory with relevant information first
   - Use more specific search queries
   - Clear memory if it contains too much noise (`/clear` in test utility)

### Logs

Check the following log files for detailed information:
- `logs/memory_system.log` - Memory system logs
- `logs/memory_bridge.log` - Memory bridge logs
- `logs/ws_server_8765.log` - WebSocket server logs
- `logs/test_semantic_search.log` - Test utility logs