<script>
  import { onMount } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  export let show = false;
  let messages = [];
  let input = '';
  let ws;
  let loading = false;
  let chatContainer;
  let isTyping = false;
  let isDragging = false;
  let startX, startY, initialX, initialY;
  let position = { x: 20, y: 90 };
  let reconnectAttempts = 0;
  let maxReconnectAttempts = 5;
  let reconnectDelay = 1000; // Start with 1 second delay
  let isConnected = false;
  let connectionStatus = 'disconnected';

  const quickQuestions = [
    "What can you help me with?",
    "Show me some examples",
    "How does this work?"
  ];

  function connectWebSocket() {
    try {
      if (ws && ws.readyState === WebSocket.OPEN) {
        console.log('WebSocket already connected');
        return;
      }

      console.log('Attempting to connect to WebSocket server...');
      ws = new WebSocket('ws://localhost:8766');  // Updated to use bridge server port
      
      ws.onopen = () => {
        console.log('Connected to LLM service');
        isConnected = true;
        connectionStatus = 'connected';
        reconnectAttempts = 0;
        reconnectDelay = 1000;
        
        // Send registration message
        ws.send(JSON.stringify({
          type: 'register',
          payload: {
            client_type: 'ui',
            version: '1.0.0',
            capabilities: ['overlay_display', 'user_interaction'],
            timestamp: Date.now()
          }
        }));
      };

      ws.onmessage = (event) => {
        console.log('Received message:', event.data);
        try {
          const data = JSON.parse(event.data);
          console.log('Parsed message:', data);
          
          // Skip system messages that don't need to be displayed
          const systemMessageTypes = [
            'connection_established', 
            'echo', 
            'status_response', 
            'status_update',
            'sensor_data_received', 
            'pong',
            'context_update',
            'context_update_received',
            'ack'
          ];
          
          if (systemMessageTypes.includes(data.type)) {
            console.log(`Received system message type: ${data.type}`);
            if (data.type === 'connection_established') {
              isConnected = true;
              connectionStatus = 'connected';
            }
            loading = false;
            return;
          }
          
          // Handle response messages
          if (data.type === 'llm_response' || data.type === 'query_response' || data.type === 'response') {
            const responseText = data.content || data.payload?.response || data.payload?.message || data.message || "I received your message.";
            messages = [...messages, { role: 'assistant', content: responseText }];
            loading = false;
            scrollToBottom();
          } else if (data.type === 'error') {
            const errorText = data.content || data.payload?.message || data.error || "An error occurred while processing your request.";
            messages = [...messages, { role: 'assistant', content: errorText, isError: true }];
            loading = false;
            scrollToBottom();
          } else {
            // Handle any other message types by extracting content from various possible locations
            let content = null;
            
            if (data.content) {
              content = data.content;
            } else if (data.payload) {
              if (typeof data.payload === 'string') {
                content = data.payload;
              } else if (data.payload.response) {
                content = data.payload.response;
              } else if (data.payload.message) {
                content = data.payload.message;
              } else if (data.payload.content) {
                content = data.payload.content;
              } else if (data.payload.text) {
                content = data.payload.text;
              }
            } else if (data.message) {
              content = data.message;
            } else if (data.response) {
              content = data.response;
            } else if (data.text) {
              content = data.text;
            }
            
            // If we found content to display, add it as a message
            if (content) {
              console.log(`Adding message from type ${data.type} with content:`, content);
              messages = [...messages, { 
                role: 'assistant', 
                content: content,
                messageType: data.type 
              }];
              loading = false;
              scrollToBottom();
            } else {
              console.log(`Received message with type ${data.type} but no displayable content`);
              loading = false;  // Reset loading state even if no content
            }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
          messages = [...messages, { role: 'assistant', content: "I received your message but had trouble processing it.", isError: true }];
          loading = false;
          scrollToBottom();
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        isConnected = false;
        connectionStatus = 'error';
        messages = [...messages, { 
          role: 'assistant', 
          content: "Connection error. Attempting to reconnect...", 
          isError: true 
        }];
      };

      ws.onclose = () => {
        console.log('Disconnected from LLM service');
        isConnected = false;
        connectionStatus = 'disconnected';
        
        if (reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++;
          const delay = Math.min(reconnectDelay * Math.pow(2, reconnectAttempts - 1), 30000); // Max 30 second delay
          
          messages = [...messages, { 
            role: 'assistant', 
            content: `Connection lost. Reconnecting in ${delay/1000} seconds... (Attempt ${reconnectAttempts}/${maxReconnectAttempts})`, 
            isError: true 
          }];
          
          setTimeout(connectWebSocket, delay);
        } else {
          messages = [...messages, { 
            role: 'assistant', 
            content: "Failed to reconnect after multiple attempts. Please refresh the page.", 
            isError: true 
          }];
        }
      };
    } catch (error) {
      console.error('Error creating WebSocket connection:', error);
      isConnected = false;
      connectionStatus = 'error';
      messages = [...messages, { 
        role: 'assistant', 
        content: "Failed to establish connection. Please check if the server is running.", 
        isError: true 
      }];
    }
  }

  onMount(() => {
    connectWebSocket();
  });

  function scrollToBottom() {
    if (chatContainer) {
      setTimeout(() => {
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }, 100);
    }
  }

  async function sendMessage(text = input) {
    if (!text.trim()) return;
    
    try {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        console.error('WebSocket is not connected');
        return;
      }
      
      // Add user message to chat
      messages = [...messages, { role: 'user', content: text }];
      loading = true;
      
      // Send message in the correct format
      ws.send(JSON.stringify({
        type: 'query',
        payload: {
          message: text,
          timestamp: Date.now()
        }
      }));
      
      input = '';
      scrollToBottom();
    } catch (error) {
      console.error('Error sending message:', error);
      messages = [...messages, { 
        role: 'assistant', 
        content: 'Sorry, there was an error sending your message. Please try again.' 
      }];
      loading = false;
    }
  }

  function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
    
    // Test function to create suggestions (press Ctrl+S to trigger)
    if (event.key === 's' && event.ctrlKey) {
      event.preventDefault();
      messages = [...messages, { 
        role: 'assistant', 
        content: "I noticed you're working on this project. Would you like me to help optimize the code?", 
        isSuggestion: true 
      }];
      scrollToBottom();
      console.log("Added test suggestion message:", messages[messages.length-1]);
    }
  }

  function startDrag(event) {
    if (event.target.closest('.chat-header')) {
      isDragging = true;
      startX = event.clientX;
      startY = event.clientY;
      initialX = position.x;
      initialY = position.y;
    }
  }

  function handleDrag(event) {
    if (isDragging) {
      const dx = event.clientX - startX;
      const dy = event.clientY - startY;
      position.x = initialX + dx;
      position.y = initialY + dy;
    }
  }

  function stopDrag() {
    isDragging = false;
  }

  function handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      console.log('Received message:', data);
      
      if (data.type === 'llm_response') {
        messages = [...messages, { role: 'assistant', content: data.content }];
        loading = false;
        scrollToBottom();
      } else if (data.type === 'error') {
        console.error('Server error:', data.content);
        messages = [...messages, { 
          role: 'assistant', 
          content: 'Sorry, there was an error processing your message. Please try again.' 
        }];
        loading = false;
        scrollToBottom();
      }
    } catch (error) {
      console.error('Error handling message:', error);
      loading = false;
    }
  }
</script>

<svelte:window on:mousemove={handleDrag} on:mouseup={stopDrag} />

{#if show}
  <div 
    class="chat-container" 
    style="transform: translate({position.x}px, {position.y}px)"
    transition:fly={{ y: 20, duration: 300 }}
  >
    <div class="chat-box">
      <div class="chat-header" on:mousedown={startDrag}>
        <div class="header-content">
          <div class="title">
            <div class="title-icon">��️</div>
            SensAI
          </div>
          <div class="status">
            <span class="status-dot"></span>
            {loading ? 'Thinking...' : 'Ready'}
          </div>
        </div>
      </div>

      <div class="messages" bind:this={chatContainer}>
        {#if messages.length === 0}
          <div class="welcome-message">
            <div class="welcome-icon">👋</div>
            <h3>Welcome to the Future</h3>
            <p>How can I assist you today?</p>
            <div class="quick-questions">
              {#each quickQuestions as question}
                <button 
                  class="quick-question-btn"
                  on:click={() => sendMessage(question)}
                >
                  {question}
                </button>
              {/each}
            </div>
          </div>
        {/if}

        {#each messages as msg, i}
          <div class="message-wrapper {msg.role}" in:fade={{ duration: 200, delay: i * 50 }}>
            <!-- {JSON.stringify(msg)} --> <!-- Debug info for UI -->
            <div class="message {msg.isSuggestion ? 'isSuggestion' : ''} {msg.isError ? 'isError' : ''}">
              <div class="message-avatar">
                {#if msg.role === 'user'}
                  <div class="user-avatar">👤</div>
                {:else if msg.isError}
                  <div class="ai-avatar">⚠️</div>
                {:else if msg.isSuggestion}
                  <div class="ai-avatar">💡</div>
                {:else}
                  <div class="ai-avatar">👁️</div>
                {/if}
              </div>
              <div class="message-content">
                <div class="message-text">{msg.content}</div>
                {#if msg.isSuggestion === true}
                  <div class="suggestion-actions">
                    <button class="suggestion-btn" on:click={() => sendMessage("/dismiss")}>Dismiss</button>
                    <button class="suggestion-btn" on:click={() => sendMessage("/adjust")}>Adjust</button>
                  </div>
                {/if}
                <div class="message-time">
                  {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  {#if msg.isSuggestion}
                    <span class="suggestion-indicator">💡 Suggestion</span>
                  {/if}
                </div>
              </div>
            </div>
          </div>
        {/each}

        {#if loading}
          <div class="message-wrapper assistant" in:fade={{ duration: 200 }}>
            <div class="message">
              <div class="message-avatar">
                <div class="ai-avatar">👁️</div>
              </div>
              <div class="message-content">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        {/if}
      </div>

      <div class="input-area">
        <div class="input-wrapper">
          <textarea
            bind:value={input}
            on:keydown={handleKeydown}
            placeholder="Type your message..."
            rows="1"
            autocomplete="off"
          ></textarea>
          <button 
            class="send-button" 
            on:click={() => sendMessage()}
            disabled={!input.trim() || loading}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 2L11 13M22 2L15 22L11 13L2 9L22 2Z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<style>
  .chat-container {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(120, 120, 120, 0.25);
    z-index: 9999;
    pointer-events: none;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .chat-box {
    display: flex;
    flex-direction: column;
    height: 600px;
    width: 380px;
    background: rgba(17, 17, 17, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2),
                0 0 0 1px rgba(255, 255, 255, 0.1),
                0 0 20px rgba(52, 152, 219, 0.1);
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 10000;
    pointer-events: auto;
    animation: chatAppear 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  }

  @keyframes chatAppear {
    from {
      opacity: 0;
      transform: scale(0.95) translateY(20px) rotate(-1deg);
    }
    to {
      opacity: 1;
      transform: scale(1) translateY(0) rotate(0);
    }
  }

  .chat-header {
    padding: 20px;
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.1), rgba(41, 128, 185, 0.1));
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    cursor: move;
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .title {
    font-size: 20px;
    font-weight: 600;
    background: linear-gradient(135deg, #3498db, #2980b9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .title-icon {
    font-size: 24px;
    animation: pulse 3s infinite cubic-bezier(0.34, 1.56, 0.64, 1);
    transform-origin: center;
  }

  .status {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: #ccc;
    padding: 6px 12px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    backdrop-filter: blur(5px);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #22c55e;
    box-shadow: 0 0 10px #22c55e;
    animation: statusPulse 2s infinite cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  @keyframes statusPulse {
    0% { 
      transform: scale(1);
      opacity: 1;
      box-shadow: 0 0 10px #22c55e;
    }
    50% { 
      transform: scale(1.2);
      opacity: 0.8;
      box-shadow: 0 0 20px #22c55e;
    }
    100% { 
      transform: scale(1);
      opacity: 1;
      box-shadow: 0 0 10px #22c55e;
    }
  }

  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    background: rgba(20, 20, 20, 0.5);
    scroll-behavior: smooth;
  }

  .messages::-webkit-scrollbar {
    width: 6px;
  }

  .messages::-webkit-scrollbar-track {
    background: rgba(0, 0, 0, 0.05);
    border-radius: 3px;
  }

  .messages::-webkit-scrollbar-thumb {
    background: rgba(52, 152, 219, 0.3);
    border-radius: 3px;
  }

  .welcome-message {
    text-align: center;
    padding: 40px 20px;
    color: #666;
    animation: welcomeFade 1s ease-out;
  }

  @keyframes welcomeFade {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .welcome-icon {
    font-size: 48px;
    margin-bottom: 16px;
    animation: float 4s infinite cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  .welcome-message h3 {
    margin: 0 0 8px;
    color: #2c3e50;
    font-size: 24px;
    background: linear-gradient(135deg, #3498db, #2980b9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .welcome-message p {
    margin: 0 0 24px;
    font-size: 15px;
  }

  .quick-questions {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-width: 280px;
    margin: 0 auto;
  }

  .quick-question-btn {
    background: rgba(52, 152, 219, 0.1);
    border: 1px solid rgba(52, 152, 219, 0.2);
    border-radius: 12px;
    padding: 12px;
    color: #3498db;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    backdrop-filter: blur(5px);
  }

  .quick-question-btn:hover {
    background: rgba(52, 152, 219, 0.2);
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 4px 12px rgba(52, 152, 219, 0.2);
  }

  .message-wrapper {
    display: flex;
    flex-direction: column;
    max-width: 85%;
    animation: messageSlide 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
  }

  .message-wrapper.user {
    align-self: flex-end;
  }

  .message-wrapper.assistant {
    align-self: flex-start;
  }

  .message {
    display: flex;
    gap: 12px;
    padding: 16px;
    border-radius: 20px;
    background: rgba(40, 40, 40, 0.9);
    color: #fff;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    backdrop-filter: blur(10px);
  }

  .message.isSuggestion {
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.1), rgba(41, 128, 185, 0.1));
    border: 1px solid rgba(52, 152, 219, 0.2);
    animation: suggestionPulse 2s infinite;
  }

  .message.isError {
    background: linear-gradient(135deg, rgba(231, 76, 60, 0.1), rgba(192, 57, 43, 0.1));
    border: 1px solid rgba(231, 76, 60, 0.2);
  }

  @keyframes suggestionPulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.02); }
    100% { transform: scale(1); }
  }

  .message.isSuggestion::before {
    content: '💡';
    position: absolute;
    top: -10px;
    right: -10px;
    font-size: 24px;
    opacity: 0.5;
    transform: rotate(15deg);
  }

  .message.isError::before {
    content: '⚠️';
    position: absolute;
    top: -10px;
    right: -10px;
    font-size: 24px;
    opacity: 0.5;
  }

  .message::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(52, 152, 219, 0.3), transparent);
  }

  .message.user {
    background: linear-gradient(135deg, #3498db, #2980b9);
    color: white;
    border-radius: 20px 20px 4px 20px;
  }

  .message.assistant {
    background: rgba(40, 40, 40, 0.9);
    border-radius: 20px 20px 20px 4px;
  }

  .message:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  .message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    background: rgba(60, 60, 60, 0.9);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    flex-shrink: 0;
  }

  .message:hover .message-avatar {
    transform: scale(1.1) rotate(5deg);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  }

  .user-avatar, .ai-avatar {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #4f46e5);
    color: white;
    font-size: 18px;
    transition: all 0.3s ease;
  }

  .message-content {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .message-text {
    font-size: 14px;
    line-height: 1.6;
    word-wrap: break-word;
    position: relative;
  }

  .message-time {
    font-size: 11px;
    color: rgba(255, 255, 255, 0.6);
    margin-top: 4px;
    opacity: 0.8;
    align-self: flex-end;
  }

  .message.user .message-time {
    color: rgba(255, 255, 255, 0.8);
  }

  .input-area {
    padding: 20px;
    background: rgba(40, 40, 40, 0.9);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    pointer-events: auto;
    z-index: 10000;
  }

  .input-wrapper {
    display: flex;
    gap: 12px;
    background: rgba(30, 30, 30, 0.9);
    border: 1px solid rgba(52, 152, 219, 0.3);
    border-radius: 16px;
    padding: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    pointer-events: auto;
  }

  .input-wrapper:focus-within {
    border-color: #3498db;
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
    transform: translateY(-2px) scale(1.01);
  }

  textarea {
    flex: 1;
    border: none;
    padding: 8px;
    font-size: 14px;
    line-height: 1.5;
    resize: none;
    background: transparent;
    outline: none;
    max-height: 120px;
    min-height: 24px;
    color: #fff;
    width: 100%;
    pointer-events: auto;
    font-family: inherit;
  }

  textarea::placeholder {
    color: #94a3b8;
  }

  .send-button {
    width: 40px;
    height: 40px;
    border: none;
    border-radius: 12px;
    background: #3498db;
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }

  .send-button:hover:not(:disabled) {
    background: #2980b9;
    transform: translateY(-2px) scale(1.05);
    box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3);
  }

  .send-button:disabled {
    background: #bdc3c7;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }

  .send-button svg {
    width: 20px;
    height: 20px;
  }

  .typing-indicator {
    display: flex;
    gap: 4px;
    padding: 8px;
    align-items: center;
  }

  .typing-indicator span {
    width: 8px;
    height: 8px;
    background: #3498db;
    border-radius: 50%;
    animation: typing 1.2s infinite cubic-bezier(0.34, 1.56, 0.64, 1);
    box-shadow: 0 0 8px rgba(52, 152, 219, 0.5);
  }

  .typing-indicator span:nth-child(2) { 
    animation-delay: 0.2s;
  }

  .typing-indicator span:nth-child(3) { 
    animation-delay: 0.4s;
  }

  .suggestion-actions {
    display: flex;
    gap: 8px;
    margin-top: 8px;
    margin-bottom: 4px;
  }

  .suggestion-btn {
    background: rgba(52, 152, 219, 0.2);
    border: 1px solid rgba(52, 152, 219, 0.3);
    border-radius: 10px;
    padding: 4px 12px;
    color: #3498db;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s ease-in-out;
  }

  .suggestion-btn:hover {
    background: rgba(52, 152, 219, 0.3);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(52, 152, 219, 0.2);
  }
  
  .suggestion-indicator {
    margin-left: 8px;
    font-size: 10px;
    background: rgba(52, 152, 219, 0.1);
    padding: 2px 6px;
    border-radius: 8px;
    color: rgba(52, 152, 219, 0.8);
  }

  @keyframes messageSlide {
    0% { 
        opacity: 0; 
        transform: translateY(20px) scale(0.95) rotate(-2deg);
    }
    50% {
        opacity: 0.5;
        transform: translateY(10px) scale(0.98) rotate(-1deg);
    }
    100% { 
        opacity: 1; 
        transform: translateY(0) scale(1) rotate(0);
    }
  }

  @keyframes pulse {
    0% { 
        transform: scale(1) rotate(0);
        filter: brightness(1);
    }
    50% { 
        transform: scale(1.1) rotate(5deg);
        filter: brightness(1.2);
    }
    100% { 
        transform: scale(1) rotate(0);
        filter: brightness(1);
    }
  }

  @keyframes float {
    0% { 
        transform: translateY(0) rotate(0);
    }
    50% { 
        transform: translateY(-10px) rotate(2deg);
    }
    100% { 
        transform: translateY(0) rotate(0);
    }
  }

  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .chat-container {
      background: rgba(30, 30, 30, 0.95);
      border-color: rgba(255, 255, 255, 0.1);
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2),
                  0 0 0 1px rgba(255, 255, 255, 0.1),
                  0 0 20px rgba(52, 152, 219, 0.1);
    }

    .chat-header {
      background: rgba(40, 40, 40, 0.9);
      border-color: rgba(255, 255, 255, 0.1);
    }

    .title {
      background: linear-gradient(135deg, #3498db, #2980b9);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .status {
      background: rgba(255, 255, 255, 0.05);
      color: #ccc;
    }

    .messages {
      background: rgba(20, 20, 20, 0.5);
    }

    .welcome-message {
      color: #ccc;
    }

    .welcome-message h3 {
      color: #fff;
    }

    .quick-question-btn {
      background: rgba(52, 152, 219, 0.1);
      border-color: rgba(52, 152, 219, 0.2);
      color: #3498db;
    }

    .quick-question-btn:hover {
      background: rgba(52, 152, 219, 0.2);
    }

    .message {
      background: rgba(40, 40, 40, 0.9);
      color: #fff;
    }

    .message.user {
      background: linear-gradient(135deg, #3498db, #2980b9);
    }

    .message-avatar {
      background: rgba(60, 60, 60, 0.9);
    }

    .message-time {
      color: rgba(255, 255, 255, 0.5);
    }

    .input-area {
      background: rgba(40, 40, 40, 0.9);
      border-color: rgba(255, 255, 255, 0.1);
    }

    .input-wrapper {
      background: rgba(30, 30, 30, 0.9);
      border-color: rgba(52, 152, 219, 0.3);
    }

    .input-wrapper:focus-within {
      border-color: #3498db;
      box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
    }

    textarea {
      color: #fff;
    }

    textarea::placeholder {
      color: #64748b;
    }
  }
</style> 