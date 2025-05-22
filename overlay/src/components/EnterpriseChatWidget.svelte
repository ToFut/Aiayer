<script>
  import { onMount, tick } from 'svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import { elasticOut, cubicOut } from 'svelte/easing';
  
  export let show = false;
  export let initialPosition = { x: 20, y: 90 };
  export let wsEndpoint = 'ws://localhost:8767';  // Enterprise backend port
  
  let messages = [];
  let input = '';
  let ws;
  let loading = false;
  let chatContainer;
  let isTyping = false;
  let isDragging = false;
  let showMinimized = false;
  let position = { ...initialPosition };
  let startX, startY, initialX, initialY;
  let size = { width: 400, height: 600 };
  let connectionStatus = 'disconnected';
  let currentMode = 'Ask';
  let userId = 'overlay_user_' + Date.now();
  let sessionId = 'overlay_session_' + Date.now();
  
  // Mode configurations
  const modes = {
    'Ask': {
      emoji: '🤔',
      name: 'Ask',
      description: 'Ask questions with memory context',
      color: '#667eea',
      examples: [
        'What can you help me with?',
        'How does this system work?',
        'What do you know about my patterns?'
      ]
    },
    'Agent': {
      emoji: '🤖', 
      name: 'Agent',
      description: 'Task planning and execution',
      color: '#f093fb',
      examples: [
        'Help me organize my files',
        'Create a workflow automation',
        'Set up my development environment'
      ]
    },
    'Suggest': {
      emoji: '💡',
      name: 'Suggest', 
      description: 'Proactive recommendations',
      color: '#4facfe',
      examples: [
        'I want to improve my productivity',
        'Suggest better coding practices',
        'Optimize my current workflow'
      ]
    },
    'General': {
      emoji: '💬',
      name: 'General',
      description: 'Casual conversation', 
      color: '#43e97b',
      examples: [
        'Hello, how are you today?',
        'Tell me something interesting',
        'What do you think about AI?'
      ]
    }
  };

  // Connection management
  let reconnectAttempts = 0;
  let maxReconnectAttempts = 5;
  let reconnectDelay = 1000;

  onMount(() => {
    connectToBackend();
    return () => {
      if (ws) {
        ws.close();
      }
    };
  });

  function connectToBackend() {
    if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
      return;
    }

    connectionStatus = 'connecting';
    
    try {
      ws = new WebSocket(wsEndpoint);
      
      ws.onopen = () => {
        console.log('Connected to Enterprise SensAI backend');
        connectionStatus = 'connected';
        reconnectAttempts = 0;
        
        // Add welcome message
        if (messages.length === 0) {
          addWelcomeMessage();
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleBackendMessage(data);
        } catch (error) {
          console.error('Error parsing message:', error);
        }
      };

      ws.onclose = () => {
        console.log('Disconnected from backend');
        connectionStatus = 'disconnected';
        attemptReconnect();
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        connectionStatus = 'error';
      };

    } catch (error) {
      console.error('Connection error:', error);
      connectionStatus = 'error';
      attemptReconnect();
    }
  }

  function attemptReconnect() {
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++;
      console.log(`Reconnect attempt ${reconnectAttempts}/${maxReconnectAttempts}`);
      
      setTimeout(() => {
        connectToBackend();
      }, reconnectDelay * reconnectAttempts);
    }
  }

  function addWelcomeMessage() {
    const welcomeMessage = {
      id: Date.now(),
      type: 'assistant',
      content: `👋 Welcome to Enterprise SensAI! I'm ready to help you with all 4 modes:

**🤔 Ask** - Questions with memory context
**🤖 Agent** - Task planning and execution  
**💡 Suggest** - Proactive recommendations
**💬 General** - Casual conversation

Choose a mode and start chatting!`,
      timestamp: new Date(),
      confidence: 1.0,
      mode: 'System'
    };
    
    messages = [welcomeMessage];
  }

  function handleBackendMessage(data) {
    console.log('Received message:', data);
    
    if (data.type === 'connection_established') {
      console.log('Connection established with capabilities:', data.capabilities);
      return;
    }
    
    if (data.type === 'chat_response') {
      hideTypingIndicator();
      
      const assistantMessage = {
        id: Date.now(),
        type: 'assistant',
        content: data.payload.response,
        timestamp: new Date(),
        confidence: data.payload.confidence || 0,
        mode: data.payload.mode || currentMode,
        processingTime: data.payload.processing_time,
        resources: data.payload.resources_used || []
      };
      
      messages = [...messages, assistantMessage];
      scrollToBottom();
      
    } else if (data.type === 'error') {
      hideTypingIndicator();
      showError(data.message || 'An error occurred');
    }
  }

  function selectMode(mode) {
    currentMode = mode;
    console.log(`Switched to ${mode} mode`);
  }

  function sendMessage() {
    if (!input.trim() || connectionStatus !== 'connected') return;

    const userMessage = {
      id: Date.now(),
      type: 'user', 
      content: input.trim(),
      timestamp: new Date(),
      mode: currentMode
    };

    messages = [...messages, userMessage];
    
    const messageToSend = input.trim();
    input = '';
    
    showTypingIndicator();
    
    const payload = {
      type: 'chat_request',
      mode: currentMode,
      query: messageToSend,
      user_id: userId,
      session_id: sessionId,
      timestamp: Date.now() / 1000
    };

    console.log('Sending message:', payload);
    ws.send(JSON.stringify(payload));
    
    scrollToBottom();
  }

  function showTypingIndicator() {
    isTyping = true;
  }

  function hideTypingIndicator() {
    isTyping = false;
  }

  function showError(message) {
    const errorMessage = {
      id: Date.now(),
      type: 'error',
      content: `Error: ${message}`,
      timestamp: new Date()
    };
    
    messages = [...messages, errorMessage];
    scrollToBottom();
  }

  function useExample(example) {
    input = example;
    sendMessage();
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  function scrollToBottom() {
    tick().then(() => {
      if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
    });
  }

  function formatTime(timestamp) {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function getConfidenceColor(confidence) {
    if (confidence >= 0.8) return '#00ff88';
    if (confidence >= 0.6) return '#ffaa00'; 
    return '#ff4444';
  }

  function getStatusColor() {
    switch (connectionStatus) {
      case 'connected': return '#00ff88';
      case 'connecting': return '#ffaa00';
      case 'error': return '#ff4444';
      default: return '#666';
    }
  }

  // Dragging functionality
  function startDrag(event) {
    isDragging = true;
    startX = event.clientX;
    startY = event.clientY;
    initialX = position.x;
    initialY = position.y;
    
    document.addEventListener('mousemove', onDrag);
    document.addEventListener('mouseup', stopDrag);
  }

  function onDrag(event) {
    if (!isDragging) return;
    
    const deltaX = event.clientX - startX;
    const deltaY = event.clientY - startY;
    
    position.x = Math.max(0, Math.min(initialX + deltaX, window.innerWidth - size.width));
    position.y = Math.max(0, Math.min(initialY + deltaY, window.innerHeight - size.height));
  }

  function stopDrag() {
    isDragging = false;
    document.removeEventListener('mousemove', onDrag);
    document.removeEventListener('mouseup', stopDrag);
  }

  function toggleMinimize() {
    showMinimized = !showMinimized;
  }

  function closeChat() {
    show = false;
  }
</script>

{#if show}
<div 
  class="chat-overlay" 
  class:minimized={showMinimized}
  style="left: {position.x}px; top: {position.y}px; width: {size.width}px; height: {showMinimized ? 80 : size.height}px;"
  transition:scale={{ duration: 300, easing: elasticOut }}
>
  <!-- Header -->
  <div class="chat-header" on:mousedown={startDrag}>
    <div class="header-left">
      <div class="status-indicator" style="background-color: {getStatusColor()};"></div>
      <span class="title">Enterprise SensAI</span>
    </div>
    <div class="header-controls">
      <button class="control-btn" on:click={toggleMinimize}>
        {showMinimized ? '+' : '−'}
      </button>
      <button class="control-btn" on:click={closeChat}>×</button>
    </div>
  </div>

  {#if !showMinimized}
    <!-- Mode Selector -->
    <div class="mode-selector">
      <div class="mode-tabs">
        {#each Object.entries(modes) as [modeKey, modeData]}
          <button 
            class="mode-tab" 
            class:active={currentMode === modeKey}
            style="--mode-color: {modeData.color}"
            on:click={() => selectMode(modeKey)}
          >
            {modeData.emoji} {modeData.name}
          </button>
        {/each}
      </div>
      <div class="mode-description">
        {modes[currentMode].description}
      </div>
    </div>

    <!-- Messages -->
    <div class="chat-messages" bind:this={chatContainer}>
      {#each messages as message (message.id)}
        <div class="message {message.type}" transition:fly={{ y: 20, duration: 300 }}>
          <div class="message-content">
            {@html message.content.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}
          </div>
          <div class="message-meta">
            <span class="timestamp">{formatTime(message.timestamp)}</span>
            {#if message.confidence !== undefined}
              <div class="confidence">
                <span>{Math.round(message.confidence * 100)}%</span>
                <div class="confidence-bar">
                  <div 
                    class="confidence-fill" 
                    style="width: {message.confidence * 100}%; background-color: {getConfidenceColor(message.confidence)};"
                  ></div>
                </div>
              </div>
            {/if}
          </div>
        </div>
      {/each}

      {#if isTyping}
        <div class="typing-indicator" transition:fade={{ duration: 200 }}>
          <div class="typing-dots">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
          </div>
          <span>AI is thinking...</span>
        </div>
      {/if}
    </div>

    <!-- Quick Examples -->
    {#if connectionStatus === 'connected'}
      <div class="quick-examples">
        {#each modes[currentMode].examples as example}
          <button class="example-btn" on:click={() => useExample(example)}>
            {example}
          </button>
        {/each}
      </div>
    {/if}

    <!-- Input Area -->
    <div class="input-area">
      <div class="input-container">
        <textarea
          bind:value={input}
          placeholder="Type your message..."
          class="message-input"
          on:keydown={handleKeyDown}
          disabled={connectionStatus !== 'connected'}
          rows="1"
        ></textarea>
        <button 
          class="send-btn" 
          on:click={sendMessage}
          disabled={!input.trim() || connectionStatus !== 'connected'}
          style="background: {modes[currentMode].color};"
        >
          →
        </button>
      </div>
    </div>
  {/if}
</div>
{/if}

<style>
  .chat-overlay {
    position: fixed;
    background: rgba(15, 15, 15, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 20px;
    backdrop-filter: blur(20px);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
    display: flex;
    flex-direction: column;
    z-index: 10000;
    pointer-events: auto;
    transition: all 0.3s ease;
    overflow: hidden;
  }

  .chat-overlay.minimized {
    height: 80px !important;
  }

  .chat-header {
    padding: 15px 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: grab;
    user-select: none;
  }

  .chat-header:active {
    cursor: grabbing;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    transition: background-color 0.3s ease;
  }

  .title {
    color: #fff;
    font-size: 16px;
    font-weight: 600;
  }

  .header-controls {
    display: flex;
    gap: 8px;
  }

  .control-btn {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: #fff;
    padding: 6px 10px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 14px;
  }

  .control-btn:hover {
    background: rgba(255, 255, 255, 0.2);
  }

  .mode-selector {
    padding: 15px 20px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .mode-tabs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 10px;
  }

  .mode-tab {
    padding: 10px 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.7);
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .mode-tab.active {
    background: var(--mode-color);
    color: #fff;
    border-color: var(--mode-color);
    box-shadow: 0 2px 8px rgba(255, 255, 255, 0.1);
  }

  .mode-tab:not(.active):hover {
    background: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.9);
  }

  .mode-description {
    text-align: center;
    font-size: 11px;
    color: rgba(255, 255, 255, 0.6);
    font-style: italic;
  }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 15px;
    min-height: 200px;
  }

  .message {
    max-width: 85%;
  }

  .message.user {
    align-self: flex-end;
  }

  .message.assistant, .message.error {
    align-self: flex-start;
  }

  .message-content {
    padding: 12px 16px;
    border-radius: 18px;
    word-wrap: break-word;
    line-height: 1.4;
  }

  .message.user .message-content {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
  }

  .message.assistant .message-content {
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .message.error .message-content {
    background: rgba(255, 68, 68, 0.2);
    color: #ff6b6b;
    border: 1px solid rgba(255, 68, 68, 0.3);
  }

  .message-meta {
    font-size: 10px;
    color: rgba(255, 255, 255, 0.5);
    margin-top: 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .confidence {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .confidence-bar {
    width: 30px;
    height: 3px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
    overflow: hidden;
  }

  .confidence-fill {
    height: 100%;
    transition: width 0.3s ease;
  }

  .typing-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 18px;
    max-width: 200px;
    color: rgba(255, 255, 255, 0.7);
    font-size: 12px;
  }

  .typing-dots {
    display: flex;
    gap: 4px;
  }

  .dot {
    width: 6px;
    height: 6px;
    background: rgba(255, 255, 255, 0.6);
    border-radius: 50%;
    animation: bounce 1.4s infinite;
  }

  .dot:nth-child(2) { animation-delay: 0.2s; }
  .dot:nth-child(3) { animation-delay: 0.4s; }

  @keyframes bounce {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-8px); }
  }

  .quick-examples {
    padding: 10px 20px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .example-btn {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.7);
    padding: 8px 12px;
    border-radius: 12px;
    font-size: 11px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: left;
  }

  .example-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.9);
    transform: translateY(-1px);
  }

  .input-area {
    padding: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .input-container {
    display: flex;
    gap: 10px;
    align-items: flex-end;
  }

  .message-input {
    flex: 1;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 15px;
    padding: 10px 14px;
    color: #fff;
    font-size: 14px;
    resize: none;
    max-height: 100px;
    line-height: 1.4;
    outline: none;
    transition: all 0.2s ease;
  }

  .message-input:focus {
    border-color: rgba(102, 126, 234, 0.5);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }

  .message-input::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }

  .message-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .send-btn {
    border: none;
    color: #fff;
    padding: 10px 16px;
    border-radius: 15px;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 16px;
    font-weight: bold;
    min-width: 40px;
  }

  .send-btn:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }

  .send-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Scrollbar styling */
  .chat-messages::-webkit-scrollbar {
    width: 4px;
  }

  .chat-messages::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
  }

  .chat-messages::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.3);
    border-radius: 2px;
  }

  .chat-messages::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.5);
  }
</style>