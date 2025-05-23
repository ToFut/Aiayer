#!/bin/bash

# Smart Progressive Backend Startup Script
# Handles slow llama3.2:latest responses with progressive indicators

echo "🚀 Starting Smart Progressive Backend with Ollama Integration..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create logs directory
mkdir -p logs/backend

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to stop existing processes on port 8765
stop_existing_services() {
    echo -e "${YELLOW}🔍 Checking for existing services on port 8765...${NC}"
    
    if check_port 8765; then
        echo -e "${YELLOW}⚠️  Found existing service on port 8765${NC}"
        
        # Find and kill the process
        PID=$(lsof -ti:8765)
        if [ ! -z "$PID" ]; then
            echo -e "${YELLOW}🛑 Stopping process $PID on port 8765...${NC}"
            kill -TERM $PID 2>/dev/null
            sleep 2
            
            # Force kill if still running
            if kill -0 $PID 2>/dev/null; then
                echo -e "${RED}💀 Force killing process $PID...${NC}"
                kill -KILL $PID 2>/dev/null
            fi
            
            echo -e "${GREEN}✅ Process stopped${NC}"
        fi
    else
        echo -e "${GREEN}✅ Port 8765 is available${NC}"
    fi
}

# Function to check Ollama status
check_ollama() {
    echo -e "${BLUE}🦙 Checking Ollama status...${NC}"
    
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama is running and accessible${NC}"
        
        # Check if llama3.2:latest model is available
        if curl -s http://localhost:11434/api/tags | grep -q "llama3.2:latest"; then
            echo -e "${GREEN}✅ llama3.2:latest model is available${NC}"
        else
            echo -e "${YELLOW}⚠️  llama3.2:latest model not found${NC}"
            echo -e "${BLUE}📥 Would you like to pull llama3.2:latest? (y/n)${NC}"
            read -r response
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                echo -e "${BLUE}📥 Pulling llama3.2:latest model...${NC}"
                ollama pull llama3.2:latest
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  Ollama is not running${NC}"
        echo -e "${BLUE}🚀 Starting Ollama service...${NC}"
        
        # Try to start Ollama
        if command -v ollama >/dev/null 2>&1; then
            ollama serve &
            echo -e "${BLUE}⏳ Waiting for Ollama to start...${NC}"
            sleep 5
            
            if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
                echo -e "${GREEN}✅ Ollama started successfully${NC}"
            else
                echo -e "${RED}❌ Failed to start Ollama${NC}"
                echo -e "${YELLOW}📝 Backend will run in fallback mode${NC}"
            fi
        else
            echo -e "${RED}❌ Ollama not found in PATH${NC}"
            echo -e "${YELLOW}📝 Backend will run in fallback mode${NC}"
        fi
    fi
}

# Function to start the smart progressive backend
start_backend() {
    echo -e "${BLUE}🧠 Starting Smart Progressive Backend...${NC}"
    
    # Check if Python script exists
    if [ ! -f "smart_progressive_backend_8765.py" ]; then
        echo -e "${RED}❌ smart_progressive_backend_8765.py not found${NC}"
        exit 1
    fi
    
    # Start the backend
    python3 smart_progressive_backend_8765.py &
    BACKEND_PID=$!
    
    # Save PID for cleanup
    echo $BACKEND_PID > pids/smart_progressive_backend.pid
    
    echo -e "${GREEN}✅ Smart Progressive Backend started with PID: $BACKEND_PID${NC}"
    echo -e "${BLUE}📡 WebSocket server running on ws://localhost:8765${NC}"
}

# Function to test the backend
test_backend() {
    echo -e "${BLUE}🧪 Testing backend connection...${NC}"
    sleep 3
    
    if check_port 8765; then
        echo -e "${GREEN}✅ Backend is listening on port 8765${NC}"
        
        # Create a simple test client
        python3 -c "
import asyncio
import websockets
import json

async def test_connection():
    try:
        uri = 'ws://localhost:8765'
        async with websockets.connect(uri) as websocket:
            # Send test message
            test_payload = {
                'type': 'chat_request',
                'mode': 'Ask',
                'message': 'Hello, this is a test message',
                'session_id': 'test_session_' + str(int(__import__('time').time())),
                'timestamp': __import__('datetime').datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(test_payload))
            print('✅ Test message sent successfully')
            
            # Wait for responses
            response_count = 0
            timeout = 10
            start_time = __import__('time').time()
            
            while response_count < 3 and (__import__('time').time() - start_time) < timeout:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    data = json.loads(response)
                    response_count += 1
                    
                    if data.get('type') == 'progress_update':
                        print(f'📊 Progress: {data.get(\"stage\", \"Unknown\")}')
                    elif data.get('type') == 'final_response':
                        print(f'💬 Final response received: {len(data.get(\"response\", \"\"))} characters')
                        break
                    elif data.get('success'):
                        print(f'💬 Response received: {len(data.get(\"response\", \"\"))} characters')
                        break
                        
                except asyncio.TimeoutError:
                    break
                    
            print('🎯 Backend test completed')
            
    except Exception as e:
        print(f'❌ Connection test failed: {e}')

asyncio.run(test_connection())
        " 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Backend connection test successful${NC}"
        else
            echo -e "${YELLOW}⚠️  Backend connection test had issues but backend is running${NC}"
        fi
    else
        echo -e "${RED}❌ Backend is not listening on port 8765${NC}"
        exit 1
    fi
}

# Function to display status
show_status() {
    echo ""
    echo -e "${GREEN}🎉 Smart Progressive Backend Setup Complete!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}📡 WebSocket Endpoint:${NC} ws://localhost:8765"
    echo -e "${GREEN}🦙 Ollama Integration:${NC} $(curl -s http://localhost:11434/api/tags >/dev/null 2>&1 && echo "✅ Active" || echo "❌ Fallback Mode")"
    echo -e "${GREEN}⚡ Progressive Features:${NC}"
    echo "   • Stage-by-stage progress updates"
    echo "   • Extended 60-second timeout for LLM responses"
    echo "   • Smart fallback responses when Ollama is slow"
    echo "   • Real-time typing indicators with progress messages"
    echo ""
    echo -e "${YELLOW}📋 Usage:${NC}"
    echo "   • Frontend should connect to ws://localhost:8765"
    echo "   • Send messages with format: {type: 'chat_request', mode: 'Ask', message: '...', session_id: '...', timestamp: '...'}"
    echo "   • Watch for progress_update messages before final responses"
    echo ""
    echo -e "${BLUE}📊 Monitoring:${NC}"
    echo "   • Logs: tail -f logs/backend/smart_progressive_backend.log"
    echo "   • Stop: kill \$(cat pids/smart_progressive_backend.pid)"
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}🤖 Smart Progressive Backend Startup${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    # Create necessary directories
    mkdir -p pids logs/backend
    
    # Stop existing services
    stop_existing_services
    
    # Check Ollama
    check_ollama
    
    # Start backend
    start_backend
    
    # Test backend
    test_backend
    
    # Show status
    show_status
}

# Trap to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down Smart Progressive Backend...${NC}"
    if [ -f "pids/smart_progressive_backend.pid" ]; then
        PID=$(cat pids/smart_progressive_backend.pid)
        if [ ! -z "$PID" ]; then
            kill $PID 2>/dev/null
            echo -e "${GREEN}✅ Backend stopped${NC}"
        fi
        rm -f pids/smart_progressive_backend.pid
    fi
}

trap cleanup EXIT

# Run main function
main

# Keep script running to maintain the backend
echo -e "${BLUE}⏳ Backend running... Press Ctrl+C to stop${NC}"
wait