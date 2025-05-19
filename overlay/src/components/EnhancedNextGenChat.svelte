<script>
  import { onMount, tick } from 'svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import { elasticOut, cubicOut } from 'svelte/easing';
  
  export let show = false;
  export let initialPosition = { x: 20, y: 90 };
  export let wsEndpoint = 'ws://localhost:8765';
  
  let messages = [];
  let input = '';
  let ws;
  let loading = false;
  let chatContainer;
  let isTyping = false;
  let isDragging = false;
  let isResizing = false;
  let showMinimized = false;
  let position = { ...initialPosition };
  let startX, startY, initialX, initialY;
  let size = { width: 380, height: 600 };
  let startWidth, startHeight;
  let resizeHandlePosition;
  let autoScrollEnabled = true;
  let unreadCount = 0;
  let connectionStatus = 'disconnected'; // disconnected, connecting, connected, error
  
  // Variables for typing animation
  let typingMessage = null;
  let typingText = '';
  let typingIndex = 0;
  let typingSpeed = { min: 15, max: 35 }; // Random speed between min and max ms
  let typingInterval;

  const quickQuestions = [
    "What can you help me with?",
    "Show me some examples",
    "How does this work?",
    "What are you monitoring?"
  ];

  // UI state toggles
  let showSettings = false;
  let darkMode = true;
  let isMuted = false;
  let showEmojis = false;
  let emojiCategories = ['😊', '🔍', '💡', '⚙️', '📄'];
  let selectedEmojiCategory = null;
  let emojiPickerVisible = false;
  
  // Common emojis by category
  const emojis = {
    '😊': ['😊', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃', '😉', '😌', '😍'],
    '🔍': ['🔍', '👀', '📱', '💻', '🖥️', '🔬', '🔭', '📊', '📈', '📉', '📰', '📝', '📌', '📎', '🔗'],
    '💡': ['💡', '⚡', '🧠', '🤔', '💭', '💬', '📢', '🔔', '📣', '📝', '📚', '🧮', '🔧', '🔨', '⚒️'],
    '⚙️': ['⚙️', '🔄', '🔃', '🔙', '🔚', '🔛', '🔜', '🔝', '↩️', '↪️', '⤴️', '⤵️', '🔀', '🔁', '🔂'],
    '📄': ['📄', '📃', '📑', '📜', '📋', '📅', '📆', '📇', '📁', '📂', '📝', '📒', '📔', '📕', '📗']
  };

  // Audio effects
  let messageSentAudio;
  let messageReceivedAudio;
  let notificationAudio;
  let audioContext;
  let audioInitialized = false;

  async function initializeAudio() {
    if (audioInitialized) return;
    
    try {
      // Initialize audio context
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
      
      // Initialize audio with proper error handling
      messageSentAudio = new Audio('/sounds/message-sent.wav');
      messageReceivedAudio = new Audio('/sounds/message-received.wav');
      notificationAudio = new Audio('/sounds/notification.wav');

      // Preload audio files
      const audioLoadPromises = [messageSentAudio, messageReceivedAudio, notificationAudio].map(audio => {
        return new Promise((resolve, reject) => {
          audio.addEventListener('canplaythrough', resolve, { once: true });
          audio.addEventListener('error', (e) => {
            console.error('Error loading audio:', e.target.error);
            reject(e.target.error);
          }, { once: true });
          audio.load();
        });
      });

      await Promise.all(audioLoadPromises);
      audioInitialized = true;
      console.log('Audio initialized successfully');
    } catch (e) {
      console.error('Error initializing audio:', e);
    }
  }

  onMount(() => {
    initializeAudio();
    connectWebSocket();
    
    // Add keyboard shortcuts
    document.addEventListener('keydown', handleGlobalKeydown);
    
    return () => {
      // Clean up event listeners
      document.removeEventListener('keydown', handleGlobalKeydown);
      if (ws) {
        ws.close();
      }
      // Clean up audio
      if (audioContext) {
        audioContext.close();
      }
    };
  });
  
  function connectWebSocket() {
    if (ws && ws.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected');
      return;
    }

    connectionStatus = 'connecting';
    ws = new WebSocket(wsEndpoint);
    
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    const reconnectDelay = 1000; // 1 second

    function attemptReconnect() {
      if (reconnectAttempts < maxReconnectAttempts) {
        reconnectAttempts++;
        console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts})...`);
        setTimeout(connectWebSocket, reconnectDelay * reconnectAttempts);
      } else {
        console.error('Max reconnection attempts reached');
        connectionStatus = 'error';
      }
    }

    ws.onmessage = (event) => {
      console.log('Received message:', event.data);
      try {
        const data = JSON.parse(event.data);
        console.log('Parsed message:', data);
        
        if (data.type === 'llm_response' || data.type === 'query_response') {
          // Handle LLM or query responses - support both new and old formats
          const responseText = data.content || data.payload?.response || data.payload?.message || "I received your message.";
          addMessage({ role: 'assistant', content: responseText });
          loading = false;
          if (showMinimized) {
            unreadCount++;
            playSound(notificationAudio);
          } else if (!isMuted) {
            playSound(messageReceivedAudio);
          }
        } else if (data.type === 'suggestion') {
          // Handle proactive suggestions - support both new and old formats
          const suggestionText = data.content || data.payload?.content || "I have a suggestion for you.";
          addMessage({ role: 'assistant', content: suggestionText, isSuggestion: true });
          if (showMinimized) {
            unreadCount++;
            playSound(notificationAudio);
          } else if (!isMuted) {
            playSound(messageReceivedAudio);
          }
        } else if (data.type === 'error') {
          // Handle error messages - support both new and old formats
          const errorText = data.content || data.payload?.message || data.error || "An error occurred while processing your request.";
          addMessage({ role: 'assistant', content: errorText, isError: true });
          loading = false;
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
        addMessage({ 
          role: 'assistant', 
          content: "I received your message but had trouble processing it.", 
          isError: true 
        });
        loading = false;
      }
    };

    ws.onopen = () => {
      console.log('Connected to LLM service');
      connectionStatus = 'connected';
      reconnectAttempts = 0; // Reset reconnect attempts on successful connection
      
      // Send initial connection identification
      ws.send(JSON.stringify({
        type: 'connection_established',
        payload: { 
          client: 'enhanced_eye_widget',
          version: '1.0.0',
          capabilities: ['chat', 'context_aware']
        }
      }));
      
      // Send initial context request
      ws.send(JSON.stringify({
        type: 'context_request',
        payload: { type: 'initial' }
      }));
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      connectionStatus = 'error';
      addMessage({ 
        role: 'assistant', 
        content: "Connection error. Please check if the LLM service is running.", 
        isError: true 
      });
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      connectionStatus = 'disconnected';
      
      if (!event.wasClean) {
        console.log('Connection was not clean, attempting to reconnect...');
        attemptReconnect();
      }
      
      addMessage({ 
        role: 'assistant', 
        content: "Disconnected from LLM service. Click to reconnect.", 
        isError: true,
        action: connectWebSocket
      });
    };
  }

  function addMessage(message) {
    // Add timestamp to the message
    message.timestamp = new Date().toISOString();
    
    // For assistant messages, use typing animation
    if (message.role === 'assistant' && !message.isError) {
      // Clear any existing typing animation
      clearTypingAnimation();
      
      // Start new typing animation
      typingMessage = { ...message, content: '' };
      typingText = message.content;
      typingIndex = 0;
      startTypingAnimation();
      
      // For display, add an empty message that will be filled in by the animation
      messages = [...messages, typingMessage];
    } else {
      // For user messages or error messages, add them immediately
      messages = [...messages, message];
    }
    
    if (autoScrollEnabled) {
      scrollToBottom();
    }
  }
  
  function clearTypingAnimation() {
    if (typingInterval) {
      clearInterval(typingInterval);
      typingInterval = null;
    }
    
    // If we were in the middle of typing, complete the message immediately
    if (typingMessage && typingIndex < typingText.length) {
      typingMessage.content = typingText;
      messages = [...messages]; // Force update
    }
    
    typingMessage = null;
    typingText = '';
    typingIndex = 0;
  }
  
  function startTypingAnimation() {
    // Clear any existing animation
    if (typingInterval) clearInterval(typingInterval);
    
    // Function to get random typing delay (simulates human typing)
    const getRandomDelay = () => Math.floor(Math.random() * 
      (typingSpeed.max - typingSpeed.min + 1)) + typingSpeed.min;
    
    // Start the animation
    typingInterval = setInterval(() => {
      if (typingIndex < typingText.length) {
        // Add the next character to the message
        typingMessage.content += typingText.charAt(typingIndex);
        typingIndex++;
        
        // Force Svelte to update the UI
        messages = [...messages];
        
        // Keep scrolling to the bottom during typing
        if (autoScrollEnabled) {
          scrollToBottom();
        }
      } else {
        // Typing finished
        clearInterval(typingInterval);
        typingInterval = null;
      }
    }, getRandomDelay());
  }

  async function scrollToBottom() {
    await tick(); // Wait for DOM update
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }

  function sendMessage(text = input) {
    if (!text.trim()) {
      console.log('Empty message, not sending');
      return;
    }
    
    if (connectionStatus !== 'connected') {
      console.log('Not connected, cannot send message');
      addMessage({ 
        role: 'assistant', 
        content: "Not connected to the server. Please check your connection and try again.", 
        isError: true 
      });
      return;
    }
    
    console.log('SENDING MESSAGE TO SERVER:', text);
    console.log('Current connection status:', connectionStatus);
    
    addMessage({ role: 'user', content: text });
    loading = true;
    
    // Use the correct message format expected by the server
    const message = {
      type: 'user_interaction',
      content: text
    };
    
    console.log('Sending message object:', JSON.stringify(message));
    
    try {
      ws.send(JSON.stringify(message));
      console.log('Message sent successfully');
    } catch (error) {
      console.error('Error sending message:', error);
      addMessage({ 
        role: 'assistant', 
        content: "Error sending message: " + error.message, 
        isError: true 
      });
      loading = false;
      return;
    }
    
    input = '';
    if (!isMuted) {
      playSound(messageSentAudio);
    }
    
    // Hide emoji picker when sending a message
    emojiPickerVisible = false;
  }

  function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    } else if (event.key === 'Escape') {
      emojiPickerVisible = false;
      showSettings = false;
    }
  }
  
  function handleGlobalKeydown(event) {
    // Ctrl+/ to toggle chat
    if (event.ctrlKey && event.key === '/') {
      event.preventDefault();
      show = !show;
    }
    
    // Escape to minimize
    if (event.key === 'Escape' && show && !showMinimized && !emojiPickerVisible && !showSettings) {
      showMinimized = true;
    }
  }

  function startDrag(event) {
    if (event.target.closest('.chat-header') && !event.target.closest('.chat-controls')) {
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
      
      // Keep the window within viewport bounds
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      
      if (position.x < 0) position.x = 0;
      if (position.y < 0) position.y = 0;
      if (position.x + size.width > viewportWidth) position.x = viewportWidth - size.width;
      if (position.y + size.height > viewportHeight) position.y = viewportHeight - size.height;
    } else if (isResizing) {
      const width = startWidth + (event.clientX - startX);
      const height = startHeight + (event.clientY - startY);
      
      // Enforce minimum and maximum dimensions
      size.width = Math.max(300, Math.min(800, width));
      size.height = Math.max(400, Math.min(800, height));
    }
  }

  function stopDrag() {
    isDragging = false;
    isResizing = false;
  }
  
  function startResize(event, position) {
    isResizing = true;
    startX = event.clientX;
    startY = event.clientY;
    startWidth = size.width;
    startHeight = size.height;
    resizeHandlePosition = position;
  }
  
  function handleInputFocus() {
    // Auto scroll to bottom when focusing input
    if (showMinimized) {
      showMinimized = false;
      unreadCount = 0;
    }
    scrollToBottom();
  }
  
  function toggleMinimize() {
    showMinimized = !showMinimized;
    if (!showMinimized) {
      unreadCount = 0;
      scrollToBottom();
    }
  }
  
  function toggleSettings() {
    showSettings = !showSettings;
  }
  
  function toggleMute() {
    isMuted = !isMuted;
  }
  
  function toggleTheme() {
    darkMode = !darkMode;
  }
  
  function toggleEmojiPicker() {
    emojiPickerVisible = !emojiPickerVisible;
    if (emojiPickerVisible) {
      selectedEmojiCategory = emojiCategories[0];
    }
  }
  
  function selectEmojiCategory(category) {
    selectedEmojiCategory = category;
  }
  
  function addEmoji(emoji) {
    input += emoji;
    // Focus textarea after adding emoji
    document.querySelector('.message-input').focus();
  }
  
  function clearChat() {
    if (confirm('Are you sure you want to clear all messages?')) {
      messages = [];
    }
  }
  
  function playSound(audio) {
    if (!isMuted && audio && audioContext && audioInitialized) {
      try {
        // Reset audio to start
        audio.currentTime = 0;
        
        // Create a new audio source
        const source = audioContext.createMediaElementSource(audio);
        source.connect(audioContext.destination);
        
        // Play the sound
        const playPromise = audio.play();
        
        if (playPromise !== undefined) {
          playPromise.catch(error => {
            console.error('Error playing audio:', error);
            // If the error is due to user interaction, we can try to resume the audio context
            if (error.name === 'NotAllowedError') {
              audioContext.resume().catch(e => console.error('Error resuming audio context:', e));
            }
          });
        }
      } catch (e) {
        console.error('Error in playSound:', e);
      }
    }
  }
  
  function handleScroll() {
    if (chatContainer) {
      // Determine if we're at the bottom
      const isAtBottom = chatContainer.scrollHeight - chatContainer.clientHeight - chatContainer.scrollTop < 30;
      autoScrollEnabled = isAtBottom;
    }
  }
  
  function formatTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  
  function getChatContainerClass() {
    return `chat-container${darkMode ? ' dark-mode' : ' light-mode'}${showMinimized ? ' minimized' : ''}`;
  }
  
  function getConnectionStatusIcon() {
    switch(connectionStatus) {
      case 'connected': return '🟢';
      case 'connecting': return '🟡';
      case 'disconnected': return '🔴';
      case 'error': return '⚠️';
      default: return '⚪';
    }
  }
  
  function getConnectionStatusText() {
    switch(connectionStatus) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      case 'disconnected': return 'Disconnected';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  }
</script>

<svelte:window on:mousemove={handleDrag} on:mouseup={stopDrag} />

{#if show}
  <div 
    class={getChatContainerClass()}
    style="transform: translate({position.x}px, {position.y}px); width: {showMinimized ? '60px' : size.width + 'px'}; height: {showMinimized ? '60px' : size.height + 'px'}"
    transition:fly={{ y: 20, duration: 300 }}
  >
    {#if showMinimized}
      <!-- Minimized view -->
      <div class="minimized-icon" role="button" tabindex="0" 
           on:click={toggleMinimize} 
           on:keydown={e => e.key === 'Enter' && toggleMinimize()}>
        <div class="icon">👁️</div>
        {#if unreadCount > 0}
          <div class="unread-badge" in:scale={{ duration: 200, easing: elasticOut }}>
            {unreadCount}
          </div>
        {/if}
      </div>
    {:else}
      <!-- Full view -->
      <div class="chat-box">
        <div class="chat-header" role="region" aria-label="Draggable chat header" on:mousedown={startDrag}>
          <div class="header-content">
            <div class="title">
              <div class="title-icon">👁️</div>
              SensAI
            </div>
            <div class="chat-controls">
              <button class="control-button" on:click={toggleSettings} title="Settings">
                ⚙️
              </button>
              <button class="control-button" on:click={toggleMinimize} title="Minimize">
                ➖
              </button>
            </div>
          </div>
          <div class="status-bar">
            <div class="connection-status" 
                 role="button" 
                 tabindex="0"
                 on:click={connectWebSocket} 
                 on:keydown={e => e.key === 'Enter' && connectWebSocket()} 
                 class:clickable={connectionStatus === 'disconnected' || connectionStatus === 'error'}>
              <span class="status-dot status-{connectionStatus}"></span>
              {getConnectionStatusText()}
            </div>
            <div class="status-info">
              {loading ? 'Thinking...' : 'Ready'}
            </div>
          </div>
        </div>

        {#if showSettings}
          <div class="settings-panel" transition:fade={{ duration: 150 }}>
            <div class="settings-header">
              <h3>Settings</h3>
              <button class="close-button" on:click={toggleSettings}>×</button>
            </div>
            <div class="settings-content">
              <div class="setting-item">
                <span>Dark Mode</span>
                <label class="toggle">
                  <input type="checkbox" bind:checked={darkMode}>
                  <span class="toggle-slider"></span>
                </label>
              </div>
              <div class="setting-item">
                <span>Sound Effects</span>
                <label class="toggle">
                  <input type="checkbox" checked={!isMuted} on:change={() => isMuted = !isMuted}>
                  <span class="toggle-slider"></span>
                </label>
              </div>
              <div class="setting-item action">
                <button class="action-button danger" on:click={clearChat}>
                  Clear Conversation
                </button>
              </div>
              <div class="setting-item action">
                <button class="action-button" on:click={connectWebSocket} disabled={connectionStatus === 'connected' || connectionStatus === 'connecting'}>
                  Reconnect
                </button>
              </div>
              <div class="setting-info">
                <p>Keyboard Shortcuts:</p>
                <ul>
                  <li><kbd>Ctrl</kbd> + <kbd>/</kbd> - Toggle chat</li>
                  <li><kbd>Esc</kbd> - Minimize chat</li>
                  <li><kbd>Enter</kbd> - Send message</li>
                  <li><kbd>Shift</kbd> + <kbd>Enter</kbd> - New line</li>
                </ul>
              </div>
            </div>
          </div>
        {/if}

        <div class="messages" bind:this={chatContainer} on:scroll={handleScroll}>
          {#if messages.length === 0}
            <div class="welcome-message">
              <div class="welcome-icon">👋</div>
              <h3>Welcome to SensAI</h3>
              <p>I can help analyze and provide insights about your system.</p>
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
              <div class="message {msg.isSuggestion ? 'suggestion' : ''} {msg.isError ? 'error' : ''}">
                <div class="message-avatar">
                  {#if msg.role === 'user'}
                    <div class="user-avatar">👤</div>
                  {:else if msg.isError}
                    <div class="ai-avatar error-avatar">⚠️</div>
                  {:else if msg.isSuggestion}
                    <div class="ai-avatar suggestion-avatar">💡</div>
                  {:else}
                    <div class="ai-avatar">👁️</div>
                  {/if}
                </div>
                <div class="message-content">
                  <div class="message-text">
                    {msg.content}
                    {#if msg.action}
                      <button class="message-action-btn" on:click={msg.action}>Reconnect</button>
                    {/if}
                  </div>
                  <div class="message-time">
                    {formatTime(msg.timestamp)}
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
          
          {#if !autoScrollEnabled && messages.length > 0}
            <button class="scroll-bottom-btn" on:click={scrollToBottom}>
              ↓
            </button>
          {/if}
        </div>

        <div class="input-area">
          <div class="input-wrapper">
            <button class="emoji-button" on:click={toggleEmojiPicker} title="Insert emoji">
              😊
            </button>
            <textarea
              bind:value={input}
              on:keydown={handleKeydown}
              on:focus={handleInputFocus}
              placeholder="Type your message..."
              rows="1"
              autocomplete="off"
              class="message-input"
            ></textarea>
            <button 
              class="send-button" 
              on:click={() => sendMessage()}
              disabled={!input.trim() || loading || connectionStatus !== 'connected'}
              title="Send message"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 2L11 13M22 2L15 22L11 13L2 9L22 2Z"/>
              </svg>
            </button>
          </div>
          
          {#if emojiPickerVisible}
            <div class="emoji-picker" transition:scale={{ duration: 200, start: 0.95, easing: cubicOut }}>
              <div class="emoji-categories">
                {#each emojiCategories as category}
                  <button 
                    class="emoji-category-btn" 
                    class:active={selectedEmojiCategory === category}
                    on:click={() => selectEmojiCategory(category)}
                  >
                    {category}
                  </button>
                {/each}
              </div>
              <div class="emoji-list">
                {#each emojis[selectedEmojiCategory] || [] as emoji}
                  <button class="emoji-btn" on:click={() => addEmoji(emoji)}>
                    {emoji}
                  </button>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      </div>
      
      <!-- Resize handle -->
      <div 
        class="resize-handle bottom-right"
        role="button"
        aria-label="Resize chat window"
        on:mousedown={(e) => startResize(e, 'bottom-right')}
        title="Resize"
      ></div>
    {/if}
  </div>
{/if}

<style>
  /* Base Styles */
  .chat-container {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 9999;
    pointer-events: auto;
    display: flex;
    background: transparent;
    border-radius: 24px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3), 
                0 0 0 1px rgba(255, 255, 255, 0.1);
    overflow: hidden;
    transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1), 
                height 0.3s cubic-bezier(0.4, 0, 0.2, 1), 
                transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .chat-container.minimized {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    overflow: visible;
  }
  
  .chat-box {
    display: flex;
    flex-direction: column;
    height: 100%;
    width: 100%;
    background: rgba(17, 17, 17, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: chatAppear 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .light-mode .chat-box {
    background: rgba(250, 250, 250, 0.95);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(0, 0, 0, 0.1);
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

  /* Header Styles */
  .chat-header {
    padding: 16px 20px;
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.1), rgba(41, 128, 185, 0.1));
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    cursor: move;
  }
  
  .light-mode .chat-header {
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.1), rgba(41, 128, 185, 0.1));
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
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
  
  .chat-controls {
    display: flex;
    gap: 8px;
  }
  
  .control-button {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    border: none;
    border-radius: 8px;
    color: #fff;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.2s;
  }
  
  .light-mode .control-button {
    background: rgba(0, 0, 0, 0.1);
    color: #333;
  }
  
  .control-button:hover {
    background: rgba(255, 255, 255, 0.2);
    transform: translateY(-2px);
  }
  
  .light-mode .control-button:hover {
    background: rgba(0, 0, 0, 0.2);
  }
  
  .status-bar {
    display: flex;
    justify-content: space-between;
    margin-top: 8px;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
  }
  
  .light-mode .status-bar {
    color: rgba(0, 0, 0, 0.6);
  }
  
  .connection-status {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 8px;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
  }
  
  .light-mode .connection-status {
    background: rgba(255, 255, 255, 0.2);
  }
  
  .connection-status.clickable {
    cursor: pointer;
  }
  
  .connection-status.clickable:hover {
    background: rgba(0, 0, 0, 0.3);
  }
  
  .light-mode .connection-status.clickable:hover {
    background: rgba(255, 255, 255, 0.3);
  }
  
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ccc;
  }
  
  .status-connected {
    background: #2ecc71;
    box-shadow: 0 0 10px #2ecc71;
    animation: statusPulse 2s infinite;
  }
  
  .status-connecting {
    background: #f39c12;
    box-shadow: 0 0 10px #f39c12;
    animation: statusPulse 1s infinite;
  }
  
  .status-disconnected, .status-error {
    background: #e74c3c;
    box-shadow: 0 0 10px #e74c3c;
  }
  
  .status-info {
    padding: 4px 8px;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
  }
  
  .light-mode .status-info {
    background: rgba(255, 255, 255, 0.2);
  }

  @keyframes statusPulse {
    0% { 
      transform: scale(1);
      opacity: 1;
    }
    50% { 
      transform: scale(1.2);
      opacity: 0.8;
    }
    100% { 
      transform: scale(1);
      opacity: 1;
    }
  }

  /* Minimized View */
  .minimized-icon {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: linear-gradient(135deg, #3498db, #2980b9);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3), 
                0 0 0 1px rgba(255, 255, 255, 0.1);
    transition: all 0.3s;
    position: relative;
    z-index: 10001;
    font-size: 24px;
    color: white;
  }
  
  .minimized-icon:hover {
    transform: scale(1.1);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4), 
                0 0 0 1px rgba(255, 255, 255, 0.2);
  }
  
  .unread-badge {
    position: absolute;
    top: -6px;
    right: -6px;
    background: #e74c3c;
    color: white;
    font-size: 12px;
    padding: 2px 6px;
    border-radius: 10px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    font-weight: bold;
    min-width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .icon {
    animation: float 4s infinite ease-in-out;
  }
  
  @keyframes float {
    0% { transform: translateY(0); }
    50% { transform: translateY(-5px); }
    100% { transform: translateY(0); }
  }

  /* Messages Area */
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    background: rgba(20, 20, 20, 0.5);
    scroll-behavior: smooth;
    position: relative;
  }
  
  .light-mode .messages {
    background: rgba(245, 245, 245, 0.5);
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
  
  .scroll-bottom-btn {
    position: absolute;
    bottom: 20px;
    right: 20px;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: rgba(52, 152, 219, 0.9);
    color: white;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    transition: all 0.2s;
  }
  
  .scroll-bottom-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
  }

  /* Welcome Message */
  .welcome-message {
    text-align: center;
    padding: 40px 20px;
    color: rgba(255, 255, 255, 0.7);
    animation: welcomeFade 1s ease-out;
  }
  
  .light-mode .welcome-message {
    color: rgba(0, 0, 0, 0.7);
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
    color: #fff;
    font-size: 24px;
    background: linear-gradient(135deg, #3498db, #2980b9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  
  .light-mode .welcome-message h3 {
    color: #333;
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
  
  .light-mode .quick-question-btn {
    background: rgba(52, 152, 219, 0.1);
    border: 1px solid rgba(52, 152, 219, 0.2);
    color: #3498db;
  }
  
  .light-mode .quick-question-btn:hover {
    background: rgba(52, 152, 219, 0.2);
  }

  /* Message Styling */
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
  
  .light-mode .message {
    background: rgba(255, 255, 255, 0.9);
    color: #333;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .message.suggestion {
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.1), rgba(41, 128, 185, 0.1));
    border: 1px solid rgba(52, 152, 219, 0.2);
    animation: suggestionPulse 2s infinite;
  }
  
  .light-mode .message.suggestion {
    background: linear-gradient(135deg, rgba(52, 152, 219, 0.1), rgba(41, 128, 185, 0.1));
    border: 1px solid rgba(52, 152, 219, 0.2);
  }

  .message.error {
    background: linear-gradient(135deg, rgba(231, 76, 60, 0.1), rgba(192, 57, 43, 0.1));
    border: 1px solid rgba(231, 76, 60, 0.2);
  }
  
  .light-mode .message.error {
    background: linear-gradient(135deg, rgba(231, 76, 60, 0.1), rgba(192, 57, 43, 0.1));
    border: 1px solid rgba(231, 76, 60, 0.2);
  }

  @keyframes suggestionPulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.02); }
    100% { transform: scale(1); }
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

  .user .message {
    background: linear-gradient(135deg, #3498db, #2980b9);
    color: white;
    border-radius: 20px 20px 4px 20px;
  }
  
  .light-mode .user .message {
    background: linear-gradient(135deg, #3498db, #2980b9);
    color: white;
  }

  .message.assistant .message-avatar {
    background: #f0f0f0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    color: #666;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .assistant .message {
    border-radius: 20px 20px 20px 4px;
  }

  .message:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.3);
  }
  
  .light-mode .message:hover {
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
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
  
  .light-mode .message-avatar {
    background: rgba(235, 235, 235, 0.9);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  .message:hover .message-avatar {
    transform: scale(1.1) rotate(5deg);
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
    font-size: 16px;
  }
  
  .light-mode .user-avatar {
    background: linear-gradient(135deg, #3498db, #2980b9);
  }
  
  .light-mode .ai-avatar {
    background: linear-gradient(135deg, #2ecc71, #27ae60);
  }
  
  .suggestion-avatar {
    background: linear-gradient(135deg, #f39c12, #e67e22);
  }
  
  .error-avatar {
    background: linear-gradient(135deg, #e74c3c, #c0392b);
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
  
  .light-mode .message-time {
    color: rgba(0, 0, 0, 0.5);
  }

  .user .message-time {
    color: rgba(255, 255, 255, 0.8);
  }
  
  .message-action-btn {
    display: inline-block;
    margin-top: 8px;
    padding: 6px 12px;
    background: rgba(52, 152, 219, 0.2);
    border: 1px solid rgba(52, 152, 219, 0.3);
    border-radius: 8px;
    color: #3498db;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .message-action-btn:hover {
    background: rgba(52, 152, 219, 0.3);
  }
  
  .light-mode .message-action-btn {
    background: rgba(52, 152, 219, 0.1);
    border: 1px solid rgba(52, 152, 219, 0.2);
  }
  
  .light-mode .message-action-btn:hover {
    background: rgba(52, 152, 219, 0.2);
  }

  /* Input Area */
  .input-area {
    padding: 16px;
    background: rgba(40, 40, 40, 0.9);
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    position: relative;
  }
  
  .light-mode .input-area {
    background: rgba(245, 245, 245, 0.9);
    border-top: 1px solid rgba(0, 0, 0, 0.1);
  }

  .input-wrapper {
    display: flex;
    gap: 10px;
    background: rgba(30, 30, 30, 0.9);
    border: 1px solid rgba(52, 152, 219, 0.3);
    border-radius: 16px;
    padding: 10px 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  
  .light-mode .input-wrapper {
    background: rgba(255, 255, 255, 0.9);
    border: 1px solid rgba(52, 152, 219, 0.3);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .input-wrapper:focus-within {
    border-color: #3498db;
    box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
    transform: translateY(-2px);
  }
  
  .emoji-button {
    background: transparent;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: #888;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    transition: all 0.2s;
  }
  
  .emoji-button:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
  }
  
  .light-mode .emoji-button:hover {
    background: rgba(0, 0, 0, 0.1);
    color: #333;
  }

  .message-input {
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
    font-family: inherit;
  }
  
  .light-mode .message-input {
    color: #333;
  }

  .message-input::placeholder {
    color: #888;
  }
  
  .light-mode .message-input::placeholder {
    color: #aaa;
  }

  .send-button {
    width: 36px;
    height: 36px;
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
    background: #505050;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
  
  .light-mode .send-button:disabled {
    background: #ccc;
  }

  .send-button svg {
    width: 18px;
    height: 18px;
  }

  /* Emoji Picker */
  .emoji-picker {
    position: absolute;
    bottom: 80px;
    left: 16px;
    right: 16px;
    background: rgba(40, 40, 40, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    padding: 12px;
    z-index: 1000;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .light-mode .emoji-picker {
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(0, 0, 0, 0.1);
  }
  
  .emoji-categories {
    display: flex;
    justify-content: space-between;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding-bottom: 8px;
    margin-bottom: 8px;
  }
  
  .light-mode .emoji-categories {
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  }
  
  .emoji-category-btn {
    background: transparent;
    border: none;
    color: #888;
    font-size: 18px;
    cursor: pointer;
    padding: 6px;
    border-radius: 8px;
    transition: all 0.2s;
  }
  
  .emoji-category-btn:hover, .emoji-category-btn.active {
    background: rgba(52, 152, 219, 0.2);
    color: #fff;
  }
  
  .light-mode .emoji-category-btn:hover, .light-mode .emoji-category-btn.active {
    background: rgba(52, 152, 219, 0.2);
    color: #333;
  }
  
  .emoji-list {
    display: grid;
    grid-template-columns: repeat(8, 1fr);
    gap: 4px;
    max-height: 150px;
    overflow-y: auto;
  }
  
  .emoji-btn {
    background: transparent;
    border: none;
    font-size: 24px;
    cursor: pointer;
    padding: 8px;
    border-radius: 8px;
    transition: all 0.2s;
  }
  
  .emoji-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: scale(1.2);
  }
  
  .light-mode .emoji-btn:hover {
    background: rgba(0, 0, 0, 0.1);
  }

  /* Typing Indicator */
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

  @keyframes typing {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.5); opacity: 0.5; }
    100% { transform: scale(1); opacity: 1; }
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

  /* Settings Panel */
  .settings-panel {
    position: absolute;
    top: 70px;
    right: 20px;
    width: 280px;
    background: rgba(30, 30, 30, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    z-index: 1000;
    border: 1px solid rgba(255, 255, 255, 0.1);
    overflow: hidden;
  }
  
  .light-mode .settings-panel {
    background: rgba(255, 255, 255, 0.95);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(0, 0, 0, 0.1);
  }
  
  .settings-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .light-mode .settings-header {
    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  }
  
  .settings-header h3 {
    margin: 0;
    font-size: 18px;
    color: #fff;
  }
  
  .light-mode .settings-header h3 {
    color: #333;
  }
  
  .close-button {
    background: transparent;
    border: none;
    color: #ccc;
    font-size: 24px;
    cursor: pointer;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    transition: all 0.2s;
  }
  
  .close-button:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #fff;
  }
  
  .light-mode .close-button {
    color: #666;
  }
  
  .light-mode .close-button:hover {
    background: rgba(0, 0, 0, 0.1);
    color: #333;
  }
  
  .settings-content {
    padding: 16px;
  }
  
  .setting-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    color: #eee;
  }
  
  .light-mode .setting-item {
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    color: #333;
  }
  
  .setting-item.action {
    justify-content: center;
  }
  
  .toggle {
    position: relative;
    display: inline-block;
    width: 40px;
    height: 20px;
  }
  
  .toggle input {
    opacity: 0;
    width: 0;
    height: 0;
  }
  
  .toggle-slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: #555;
    transition: .4s;
    border-radius: 34px;
  }
  
  .toggle-slider:before {
    position: absolute;
    content: "";
    height: 16px;
    width: 16px;
    left: 2px;
    bottom: 2px;
    background-color: white;
    transition: .4s;
    border-radius: 50%;
  }
  
  input:checked + .toggle-slider {
    background-color: #3498db;
  }
  
  input:checked + .toggle-slider:before {
    transform: translateX(20px);
  }
  
  .action-button {
    background: rgba(52, 152, 219, 0.2);
    border: 1px solid rgba(52, 152, 219, 0.3);
    border-radius: 8px;
    color: #3498db;
    padding: 8px 16px;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;
    width: 100%;
    margin: 8px 0;
  }
  
  .action-button:hover:not(:disabled) {
    background: rgba(52, 152, 219, 0.3);
  }
  
  .action-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .action-button.danger {
    background: rgba(231, 76, 60, 0.2);
    border: 1px solid rgba(231, 76, 60, 0.3);
    color: #e74c3c;
  }
  
  .action-button.danger:hover {
    background: rgba(231, 76, 60, 0.3);
  }
  
  .setting-info {
    margin-top: 16px;
    font-size: 12px;
    color: #999;
  }
  
  .light-mode .setting-info {
    color: #777;
  }
  
  .setting-info p {
    margin: 0 0 8px;
  }
  
  .setting-info ul {
    margin: 0;
    padding-left: 16px;
  }
  
  .setting-info li {
    margin-bottom: 4px;
  }
  
  kbd {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    padding: 2px 4px;
    font-size: 11px;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  .light-mode kbd {
    background: rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(0, 0, 0, 0.2);
  }

  /* Resize Handles */
  .resize-handle {
    position: absolute;
    width: 14px;
    height: 14px;
    background: rgba(52, 152, 219, 0.5);
    border-radius: 50%;
    cursor: nwse-resize;
    z-index: 10000;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
    transition: transform 0.2s, background 0.2s;
  }
  
  .resize-handle:hover {
    transform: scale(1.2);
    background: rgba(52, 152, 219, 0.8);
  }
  
  .bottom-right {
    right: -7px;
    bottom: -7px;
  }

  /* Dark Mode Styles */
  .dark-mode .chat-box {
    background: rgba(17, 17, 17, 0.95);
  }
  
  /* Light Mode Styles */
  .light-mode .chat-box {
    color: #333;
  }
  
  /* Media Queries */
  @media (max-width: 600px) {
    .chat-container {
      width: 90vw !important;
      max-width: 400px;
    }
  }
</style>