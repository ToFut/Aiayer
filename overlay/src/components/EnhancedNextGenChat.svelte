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
  let typingSpeed = { min: 10, max: 30 }; // Slightly faster typing for smoother appearance
  let typingInterval;
  let typingPaused = false;
  let typingQueue = [];
  let animationBuffer = '';
  let lastRenderTime = 0;
  let pendingAnimationUpdate = false;

  const quickQuestions = [
    "What can you help me with?",
    "Show me some examples",
    "How does this work?",
    "What are you monitoring?"
  ];
  
  // Add suggestion chips that can appear after assistant responses
  const suggestionChips = {
    general: [
      "Tell me more",
      "How does this work?",
      "Can you explain further?",
      "Show me an example"
    ],
    confirmation: [
      "Yes, that's helpful",
      "I need more details",
      "That answers my question"
    ],
    feedback: [
      "This is useful",
      "I'm still confused",
      "Thanks!"
    ]
  };

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
      // Clear any ongoing animations
      clearTypingAnimation();
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

  let activeSuggestions = [];
  
  function addMessage(message) {
    // Add timestamp to the message
    message.timestamp = new Date().toISOString();
    
    // Add isNew flag to highlight new messages
    message.isNew = true;
    
    // For assistant messages, use typing animation
    if (message.role === 'assistant' && !message.isError) {
      // Clear any existing typing animation
      clearTypingAnimation();
      
      // Add suggestion chips after assistant messages (for better engagement)
      if (messages.length > 0 && messages[messages.length-1].role === 'user') {
        // Clear previous suggestions
        activeSuggestions = [];
        
        // Generate new suggestions based on context
        setTimeout(() => {
          const suggestType = Math.random() > 0.7 ? 'confirmation' : 'general';
          
          // Randomly select 2-3 suggestions
          const count = Math.floor(Math.random() * 2) + 2; // 2-3
          const selectedSuggestions = [...suggestionChips[suggestType]];
          
          // Shuffle and take the first few
          activeSuggestions = selectedSuggestions
            .sort(() => Math.random() - 0.5)
            .slice(0, count);
          
          // Force UI update
          messages = [...messages];
        }, 1000); // Show suggestions 1 second after message appears
      }
      
      // Start new typing animation
      typingMessage = { ...message, content: '' };
      typingText = message.content;
      typingIndex = 0;
      startTypingAnimation();
      
      // For display, add an empty message that will be filled in by the animation
      messages = [...messages, typingMessage];
    } else {
      // For user messages, clear suggestion chips
      activeSuggestions = [];
      
      // For user messages or error messages, add them immediately
      messages = [...messages, message];
    }
    
    if (autoScrollEnabled) {
      scrollToBottom();
    }
    
    // Remove the "new" highlight after a short delay
    if (message.isNew) {
      setTimeout(() => {
        message.isNew = false;
        messages = [...messages]; // Force update UI
      }, 2000);
    }
  }
  
  // Handler for suggestion chips
  function handleSuggestion(text) {
    sendMessage(text);
    activeSuggestions = []; // Clear suggestions after selecting one
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
    
    // Clear all animation state
    typingMessage = null;
    typingText = '';
    typingIndex = 0;
    typingPaused = false;
    typingQueue = [];
    animationBuffer = '';
    pendingAnimationUpdate = false;
  }
  
  function startTypingAnimation() {
    // Clear any existing animation
    if (typingInterval) clearInterval(typingInterval);
    
    // Process text into chunks for more natural typing
    processTypingText();
    
    // Reset animation variables
    animationBuffer = '';
    typingMessage.content = '';
    lastRenderTime = Date.now();
    pendingAnimationUpdate = false;
    
    // Function to get random typing delay (simulates human typing)
    const getRandomDelay = () => {
      // Adjust delay based on character type for natural effect
      const currentChar = typingText.charAt(typingIndex);
      const nextChar = typingText.charAt(typingIndex + 1);
      
      // Pause longer at punctuation
      if (['.', '!', '?', ',', ';', ':'].includes(currentChar)) {
        // Longer pause at end of sentences
        if (['.', '!', '?'].includes(currentChar) && (nextChar === ' ' || !nextChar)) {
          return typingSpeed.max * 3;
        }
        // Medium pause for other punctuation
        return typingSpeed.max * 1.5;
      }
      
      // Small pause at spaces
      if (currentChar === ' ') {
        return typingSpeed.max;
      }
      
      // Regular typing speed for most characters
      return Math.floor(Math.random() * (typingSpeed.max - typingSpeed.min + 1)) + typingSpeed.min;
    };
    
    // Instead of updating the UI on every character, batch updates
    const updateMessageDisplay = () => {
      if (!pendingAnimationUpdate) return;
      
      // Apply buffered changes
      typingMessage.content = animationBuffer;
      
      // Avoid frequent UI reflows by throttling updates
      const now = Date.now();
      if (now - lastRenderTime > 100) { // Only update UI every 100ms at most
        messages = [...messages]; // Force Svelte to update the UI
        lastRenderTime = now;
      }
      
      if (autoScrollEnabled && typingIndex % 10 === 0) {
        scrollToBottom();
      }
      
      pendingAnimationUpdate = false;
    };
    
    // Run display updates using requestAnimationFrame for smoother rendering
    const scheduleRender = () => {
      if (pendingAnimationUpdate) {
        requestAnimationFrame(updateMessageDisplay);
      }
    };
    
    // Start the animation with improved performance
    typingInterval = setInterval(() => {
      if (typingPaused) {
        return; // Skip this interval if paused
      }
      
      if (typingIndex < typingText.length) {
        // Add character to buffer instead of directly to message
        animationBuffer += typingText.charAt(typingIndex);
        typingIndex++;
        
        pendingAnimationUpdate = true;
        scheduleRender();
      } else {
        // Typing finished
        clearInterval(typingInterval);
        typingInterval = null;
        
        // Ensure the complete message is displayed
        animationBuffer = typingText;
        pendingAnimationUpdate = true;
        scheduleRender();
        
        // Final update and scroll
        setTimeout(() => {
          messages = [...messages];
          if (autoScrollEnabled) {
            scrollToBottom();
          }
        }, 50);
      }
    }, getRandomDelay());
  }
  
  function processTypingText() {
    // Process text into logical chunks for more natural typing
    typingQueue = [];
    let chunks = typingText.match(/[^\s.!?,;:]+|[.!?,;:\s]/g) || [];
    
    chunks.forEach(chunk => {
      if (chunk.length > 0) {
        typingQueue.push(chunk);
      }
    });
  }

  async function scrollToBottom() {
    await tick(); // Wait for DOM update
    if (chatContainer) {
      try {
        // Use smooth scrolling when not typing (for better user experience)
        // But instant scroll during typing (to prevent jumpiness)
        if (!typingInterval) {
          chatContainer.scrollTo({
            top: chatContainer.scrollHeight,
            behavior: 'smooth'
          });
        } else {
          chatContainer.scrollTop = chatContainer.scrollHeight;
        }
      } catch (e) {
        // Fallback for browsers that don't support smooth scrolling
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }
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
    
    // Clear any ongoing typing animation before adding new messages
    clearTypingAnimation();
    
    addMessage({ role: 'user', content: text });
    loading = true;
    
    // Use the correct message format expected by the backend server
    const message = {
      type: 'llm_request',
      payload: {
        query: text,
        timestamp: Date.now()
      }
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
            <div class="message-wrapper {msg.role} {msg.isNew ? 'new-message' : ''}" 
                in:fade={{ duration: 200, delay: i * 50 }}>
              <div class="message {msg.isSuggestion ? 'suggestion' : ''} {msg.isError ? 'error' : ''} 
                          {typingMessage === msg ? 'typing-active' : ''}">
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
                    {#if msg.isNew && !typingMessage}
                      <span class="new-badge">New</span>
                    {/if}
                  </div>
                  <div class="message-time">
                    {formatTime(msg.timestamp)}
                  </div>
                </div>
                {#if msg.isNew && !typingMessage}
                  <div class="pulse-indicator"></div>
                {/if}
              </div>
            </div>
          {/each}

          {#if loading && !typingMessage}
            <div class="message-wrapper assistant thinking-wrapper" in:fade={{ duration: 200 }}>
              <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          {/if}
          
          {#if !autoScrollEnabled && messages.length > 0}
            <button class="scroll-bottom-btn" on:click={scrollToBottom}>
              ↓
            </button>
          {/if}
          
          {#if activeSuggestions.length > 0}
            <div class="suggestion-chips" transition:scale={{ duration: 200, start: 0.95 }}>
              {#each activeSuggestions as suggestion}
                <button 
                  class="suggestion-chip"
                  on:click={() => handleSuggestion(suggestion)}
                >
                  {suggestion}
                </button>
              {/each}
            </div>
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
    background: rgba(16, 18, 26, 0.94);
    backdrop-filter: blur(30px);
    border-radius: 24px;
    overflow: hidden;
    border: none;
    box-shadow: 
      0 14px 40px rgba(0, 0, 0, 0.4),
      0 0 0 1px rgba(70, 100, 255, 0.15),
      inset 0 0 0 1px rgba(255, 255, 255, 0.05);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: chatAppear 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    isolation: isolate;
  }
  
  .chat-box::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 23px;
    padding: 1px;
    background: linear-gradient(140deg, rgba(80, 120, 255, 0.5), rgba(70, 100, 220, 0.01) 70%);
    -webkit-mask: linear-gradient(#000 0 0) content-box, 
                  linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
    z-index: -1;
  }
  
  .light-mode .chat-box {
    background: rgba(245, 248, 255, 0.94);
    backdrop-filter: blur(30px);
    box-shadow: 
      0 14px 40px rgba(0, 30, 100, 0.12),
      0 0 0 1px rgba(70, 100, 255, 0.15),
      inset 0 0 0 1px rgba(255, 255, 255, 0.7);
  }
  
  .light-mode .chat-box::before {
    background: linear-gradient(140deg, rgba(80, 120, 255, 0.3), rgba(70, 100, 220, 0.01) 70%);
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
    padding: 18px 22px;
    background: linear-gradient(135deg, rgba(70, 90, 255, 0.08), rgba(40, 80, 220, 0.12));
    border-bottom: 1px solid rgba(100, 130, 255, 0.15);
    backdrop-filter: blur(15px);
    cursor: move;
    position: relative;
    overflow: hidden;
  }
  
  .chat-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, 
      rgba(70, 90, 255, 0), 
      rgba(70, 130, 255, 0.5), 
      rgba(70, 90, 255, 0));
  }
  
  .light-mode .chat-header {
    background: linear-gradient(135deg, rgba(100, 140, 255, 0.07), rgba(70, 110, 245, 0.09));
    border-bottom: 1px solid rgba(100, 130, 255, 0.1);
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .title {
    font-size: 22px;
    font-weight: 600;
    background: linear-gradient(135deg, #4a6eff, #2b5bde);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex;
    align-items: center;
    gap: 12px;
    letter-spacing: 0.5px;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
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
  
  /* Suggestion chips */
  .suggestion-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin: 16px 0;
    justify-content: center;
    padding: 10px;
    animation: slideUpFade 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .suggestion-chip {
    background: rgba(28, 32, 50, 0.95);
    color: rgba(255, 255, 255, 0.9);
    border: none;
    border-radius: 12px;
    padding: 10px 16px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    white-space: nowrap;
    box-shadow: 
      0 4px 12px rgba(0, 10, 50, 0.2),
      inset 0 0 0 1px rgba(70, 100, 255, 0.3);
    position: relative;
    overflow: hidden;
  }
  
  .suggestion-chip::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 11px;
    padding: 1px;
    background: linear-gradient(140deg, rgba(100, 140, 255, 0.5), rgba(70, 100, 255, 0.01) 70%);
    -webkit-mask: linear-gradient(#000 0 0) content-box, 
                 linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
    opacity: 0.7;
  }
  
  .light-mode .suggestion-chip {
    background: rgba(245, 248, 255, 0.95);
    color: rgba(40, 60, 120, 0.9);
    box-shadow: 
      0 4px 12px rgba(70, 100, 255, 0.08),
      inset 0 0 0 1px rgba(70, 100, 255, 0.2);
  }
  
  .light-mode .suggestion-chip::before {
    background: linear-gradient(140deg, rgba(100, 140, 255, 0.3), rgba(70, 100, 255, 0.01) 70%);
  }
  
  .suggestion-chip:hover {
    transform: translateY(-2px);
    box-shadow: 
      0 6px 16px rgba(70, 100, 255, 0.25),
      inset 0 0 0 1px rgba(70, 100, 255, 0.4);
  }
  
  .suggestion-chip:active {
    transform: translateY(1px);
    box-shadow: 
      0 2px 8px rgba(70, 100, 255, 0.2),
      inset 0 0 0 1px rgba(70, 100, 255, 0.4);
  }
  
  .light-mode .suggestion-chip:hover {
    box-shadow: 
      0 6px 16px rgba(70, 100, 255, 0.12),
      inset 0 0 0 1px rgba(70, 100, 255, 0.3);
  }
  
  @keyframes slideUpFade {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  /* Minimized View */
  .minimized-icon {
    width: 65px;
    height: 65px;
    border-radius: 50%;
    background: linear-gradient(135deg, #4a6eff, #2b5bde);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 
      0 8px 20px rgba(0, 0, 0, 0.3), 
      0 0 0 1px rgba(100, 130, 255, 0.3),
      0 0 20px rgba(70, 100, 255, 0.5),
      inset 0 1px 2px rgba(255, 255, 255, 0.2);
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
    z-index: 10001;
    font-size: 28px;
    color: white;
    overflow: visible;
  }
  
  .minimized-icon::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
    z-index: 1;
  }
  
  .minimized-icon:hover {
    transform: scale(1.12) rotate(5deg);
    box-shadow: 
      0 10px 30px rgba(0, 0, 0, 0.4), 
      0 0 0 1px rgba(100, 130, 255, 0.4),
      0 0 30px rgba(70, 100, 255, 0.6),
      inset 0 1px 2px rgba(255, 255, 255, 0.3);
  }
  
  .unread-badge {
    position: absolute;
    top: -8px;
    right: -8px;
    background: linear-gradient(135deg, #ff5a5f, #ff3a3f);
    color: white;
    font-size: 13px;
    padding: 3px 8px;
    border-radius: 12px;
    box-shadow: 
      0 4px 10px rgba(255, 60, 60, 0.5),
      0 0 0 1px rgba(255, 255, 255, 0.1),
      inset 0 1px 1px rgba(255, 255, 255, 0.3);
    font-weight: bold;
    min-width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2;
    letter-spacing: 0.5px;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
    animation: pulse-badge 2s infinite ease-in-out;
  }
  
  @keyframes pulse-badge {
    0% { transform: scale(1); }
    50% { transform: scale(1.15); }
    100% { transform: scale(1); }
  }
  
  .icon {
    animation: float 4s infinite ease-in-out;
    position: relative;
    z-index: 2;
  }
  
  @keyframes float {
    0% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-5px) scale(1.05); }
    100% { transform: translateY(0) scale(1); }
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
    overscroll-behavior: contain; /* Prevent scroll chaining */
    -webkit-overflow-scrolling: touch; /* Improve scroll on iOS */
    scroll-padding: 20px; /* Space for auto-scrolling */
    will-change: transform; /* Optimize scrolling */
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
    contain: content; /* Improve rendering performance */
    margin-bottom: 14px; /* Increase spacing between messages */
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }
  
  /* New message highlight effect */
  .message-wrapper:has(.message:not(.typing-active)) .message-content:has(+ .message-time)::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: inherit;
    pointer-events: none;
    animation: newMessageGlow 2s ease-out forwards;
    z-index: -1;
  }
  
  @keyframes newMessageGlow {
    0% { 
      box-shadow: 0 0 0 0 rgba(80, 120, 255, 0.8);
      opacity: 1;
    }
    70% { 
      box-shadow: 0 0 0 10px rgba(80, 120, 255, 0);
      opacity: 0.5;
    }
    100% { 
      box-shadow: 0 0 0 0 rgba(80, 120, 255, 0);
      opacity: 0;
    }
  }

  .message-wrapper.user {
    align-self: flex-end;
  }

  .message-wrapper.assistant {
    align-self: flex-start;
  }

  .message {
    display: flex;
    gap: 14px;
    padding: 18px;
    border-radius: 18px;
    background: rgba(28, 32, 44, 0.92);
    color: #fff;
    box-shadow: 
      0 6px 16px rgba(0, 0, 0, 0.35),
      0 1px 3px rgba(0, 0, 0, 0.1),
      inset 0 0 0 1px rgba(80, 120, 255, 0.15);
    position: relative;
    overflow: hidden;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
                box-shadow 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
                background-color 0.3s ease;
    backdrop-filter: blur(20px);
    border: none;
    will-change: transform, opacity; /* Optimize for animations */
    transform: translateZ(0); /* Force GPU acceleration */
  }
  
  .message::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 17px; /* 1px less than parent */
    padding: 1px;
    background: linear-gradient(140deg, rgba(80, 120, 255, 0.4), rgba(70, 100, 220, 0.01) 70%);
    -webkit-mask: linear-gradient(#000 0 0) content-box, 
                  linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
  }
  
  .light-mode .message {
    background: rgba(250, 252, 255, 0.92);
    color: #333;
    box-shadow: 
      0 6px 16px rgba(0, 30, 100, 0.08),
      0 1px 3px rgba(0, 50, 150, 0.05),
      inset 0 0 0 1px rgba(255, 255, 255, 0.7);
    border: none;
  }
  
  .light-mode .message::before {
    background: linear-gradient(140deg, rgba(70, 100, 255, 0.3), rgba(70, 100, 220, 0.01) 70%);
  }

  .message.suggestion {
    background: rgba(28, 32, 50, 0.95);
    border: none;
    animation: suggestionPulse 3s infinite;
    box-shadow: 
      0 8px 20px rgba(70, 100, 255, 0.15),
      0 2px 5px rgba(70, 100, 255, 0.1),
      inset 0 0 0 1px rgba(70, 100, 255, 0.3);
  }
  
  .message.suggestion::before {
    background: linear-gradient(140deg, rgba(100, 150, 255, 0.5), rgba(70, 100, 255, 0.01) 80%);
    border-radius: 17px;
  }
  
  .light-mode .message.suggestion {
    background: rgba(245, 250, 255, 0.95);
    box-shadow: 
      0 8px 20px rgba(70, 100, 255, 0.08),
      0 2px 5px rgba(70, 100, 255, 0.05),
      inset 0 0 0 1px rgba(70, 100, 255, 0.2);
  }
  
  .light-mode .message.suggestion::before {
    background: linear-gradient(140deg, rgba(100, 150, 255, 0.3), rgba(70, 100, 255, 0.01) 80%);
  }

  .message.error {
    background: rgba(35, 28, 30, 0.95);
    border: none;
    box-shadow: 
      0 8px 20px rgba(255, 70, 80, 0.15),
      0 2px 5px rgba(255, 70, 80, 0.1),
      inset 0 0 0 1px rgba(255, 70, 80, 0.3);
  }
  
  .message.error::before {
    background: linear-gradient(140deg, rgba(255, 70, 80, 0.5), rgba(230, 50, 70, 0.01) 80%);
    border-radius: 17px;
  }
  
  .light-mode .message.error {
    background: rgba(255, 245, 245, 0.95);
    box-shadow: 
      0 8px 20px rgba(255, 70, 80, 0.08),
      0 2px 5px rgba(255, 70, 80, 0.05),
      inset 0 0 0 1px rgba(255, 70, 80, 0.2);
  }
  
  .light-mode .message.error::before {
    background: linear-gradient(140deg, rgba(255, 70, 80, 0.3), rgba(230, 50, 70, 0.01) 80%);
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
    background: linear-gradient(145deg, #4568ff, #3050e0);
    color: white;
    border-radius: 18px 18px 4px 18px;
    box-shadow: 
      0 8px 20px rgba(50, 80, 255, 0.25),
      0 2px 5px rgba(50, 80, 255, 0.15),
      inset 0 1px 1px rgba(255, 255, 255, 0.15);
    border: none;
  }
  
  .user .message::before {
    background: linear-gradient(140deg, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.01) 60%);
  }
  
  .thinking-wrapper {
    justify-content: center;
    margin: 10px 0;
    transition: none;
    max-width: 200px;
    align-self: center;
  }
  
  .light-mode .user .message {
    background: linear-gradient(135deg, #4a6eff, #2b5bde);
    color: white;
    box-shadow: 
      0 6px 16px rgba(70, 100, 255, 0.15),
      0 0 15px rgba(70, 100, 255, 0.1),
      inset 0 0 10px rgba(255, 255, 255, 0.15);
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
    width: 38px;
    height: 38px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    background: rgba(40, 45, 60, 0.9);
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.15),
      inset 0 0 0 1px rgba(255, 255, 255, 0.1);
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    flex-shrink: 0;
    position: relative;
    transform: translateZ(0);
  }
  
  .message-avatar::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 11px;
    padding: 1px;
    background: linear-gradient(140deg, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.01) 70%);
    -webkit-mask: linear-gradient(#000 0 0) content-box, 
                  linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
  }
  
  .light-mode .message-avatar {
    background: rgba(240, 245, 255, 0.95);
    box-shadow: 
      0 4px 12px rgba(0, 30, 100, 0.1),
      inset 0 0 0 1px rgba(70, 100, 255, 0.2);
  }
  
  .light-mode .message-avatar::before {
    background: linear-gradient(140deg, rgba(70, 100, 255, 0.3), rgba(70, 100, 255, 0.01) 70%);
  }

  .message:hover .message-avatar {
    transform: translateY(-2px) scale(1.05);
    box-shadow: 
      0 6px 16px rgba(0, 0, 0, 0.2),
      inset 0 0 0 1px rgba(255, 255, 255, 0.15);
  }
  
  .light-mode .message:hover .message-avatar {
    box-shadow: 
      0 6px 16px rgba(0, 30, 100, 0.15),
      inset 0 0 0 1px rgba(70, 100, 255, 0.3);
  }

  .user-avatar, .ai-avatar {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
    background: linear-gradient(135deg, #4568ff, #3050e0);
    color: white;
    font-size: 16px;
  }
  
  .light-mode .user-avatar {
    background: linear-gradient(135deg, #4568ff, #3050e0);
  }
  
  .light-mode .ai-avatar {
    background: linear-gradient(135deg, #3060ff, #2040dd);
  }
  
  .ai-avatar {
    background: linear-gradient(135deg, #3060ff, #2040dd);
  }
  
  .suggestion-avatar {
    background: linear-gradient(135deg, #5f8aff, #496cff);
  }
  
  .error-avatar {
    background: linear-gradient(135deg, #ff3a50, #e62040);
  }

  .message-content {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
    contain: layout; /* Improve performance by containing layout changes */
    position: relative; /* For proper containment */
    isolation: isolate; /* Create stacking context to prevent z-index issues */
  }

  .message-text {
    font-size: 14px;
    line-height: 1.6;
    word-wrap: break-word;
    position: relative;
    transform: translateZ(0); /* Force GPU acceleration */
    will-change: contents; /* Hint for browser optimization */
    overflow: hidden; /* Prevent layout shifts */
    min-height: 1.6em; /* Maintain minimum height to reduce jumping */
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
  
  /* New message indicator */
  .new-badge {
    display: inline-block;
    font-size: 10px;
    background: linear-gradient(135deg, #ff3a7c, #ff1f5a);
    color: white;
    padding: 2px 6px;
    border-radius: 10px;
    margin-left: 8px;
    vertical-align: middle;
    font-weight: bold;
    box-shadow: 0 2px 6px rgba(255, 60, 100, 0.4);
    animation: fadeInOut 2s infinite;
  }
  
  .pulse-indicator {
    position: absolute;
    top: -4px;
    right: -4px;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #5a7eff;
    box-shadow: 0 0 0 rgba(90, 126, 255, 0.6);
    animation: pulse-ring 2s cubic-bezier(0.455, 0.03, 0.515, 0.955) infinite;
  }
  
  @keyframes pulse-ring {
    0% {
      transform: scale(0.8);
      box-shadow: 0 0 0 0 rgba(90, 126, 255, 0.6);
    }
    70% {
      transform: scale(1);
      box-shadow: 0 0 0 10px rgba(90, 126, 255, 0);
    }
    100% {
      transform: scale(0.8);
      box-shadow: 0 0 0 0 rgba(90, 126, 255, 0);
    }
  }
  
  .new-message .message {
    transform: translateZ(0);
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
    padding: 18px;
    background: rgba(20, 22, 32, 0.95);
    border-top: none;
    position: relative;
    backdrop-filter: blur(20px);
    box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
    z-index: 2;
  }
  
  .input-area::before {
    content: "";
    position: absolute;
    top: 0;
    left: 15%;
    right: 15%;
    height: 1px;
    background: linear-gradient(90deg, 
      rgba(70, 100, 255, 0), 
      rgba(70, 100, 255, 0.2), 
      rgba(70, 100, 255, 0));
  }
  
  .light-mode .input-area {
    background: rgba(240, 245, 255, 0.95);
    box-shadow: 0 -2px 10px rgba(70, 100, 255, 0.05);
  }
  
  .light-mode .input-area::before {
    background: linear-gradient(90deg, 
      rgba(70, 100, 255, 0), 
      rgba(70, 100, 255, 0.15), 
      rgba(70, 100, 255, 0));
  }

  .input-wrapper {
    display: flex;
    gap: 12px;
    background: rgba(28, 32, 44, 0.9);
    border: none;
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: 
      0 4px 12px rgba(0, 0, 0, 0.2),
      inset 0 0 0 1px rgba(70, 100, 255, 0.2);
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
    overflow: hidden;
  }
  
  .input-wrapper::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 13px;
    padding: 1px;
    background: linear-gradient(140deg, rgba(80, 120, 255, 0.4), rgba(70, 100, 220, 0.01) 70%);
    -webkit-mask: linear-gradient(#000 0 0) content-box, 
                  linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
  }
  
  .light-mode .input-wrapper {
    background: rgba(250, 252, 255, 0.9);
    box-shadow: 
      0 4px 12px rgba(70, 100, 255, 0.08),
      inset 0 0 0 1px rgba(70, 100, 255, 0.15);
  }
  
  .light-mode .input-wrapper::before {
    background: linear-gradient(140deg, rgba(80, 120, 255, 0.3), rgba(70, 100, 220, 0.01) 70%);
  }

  .input-wrapper:focus-within {
    box-shadow: 
      0 6px 16px rgba(70, 100, 255, 0.2),
      inset 0 0 0 1px rgba(70, 100, 255, 0.4);
    transform: translateY(-2px);
  }
  
  .emoji-button {
    background: transparent;
    border: none;
    font-size: 18px;
    cursor: pointer;
    color: #aab;
    width: 38px;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    transition: all 0.2s;
    margin-left: 4px;
  }
  
  .emoji-button:hover {
    background: rgba(80, 120, 255, 0.15);
    color: #fff;
    transform: translateY(-1px) scale(1.05);
  }
  
  .light-mode .emoji-button:hover {
    background: rgba(80, 120, 255, 0.1);
    color: rgb(80, 120, 255);
  }

  .message-input {
    flex: 1;
    border: none;
    padding: 10px;
    font-size: 15px;
    line-height: 1.5;
    resize: none;
    background: transparent;
    outline: none;
    max-height: 120px;
    min-height: 24px;
    color: rgba(255, 255, 255, 0.9);
    width: 100%;
    font-family: inherit;
    letter-spacing: 0.3px;
    backdrop-filter: blur(12px);
    caret-color: rgb(80, 120, 255); /* Blue cursor */
    transition: all 0.2s ease;
  }
  
  .light-mode .message-input {
    color: rgba(30, 40, 60, 0.9);
    caret-color: rgb(70, 100, 250);
  }

  .message-input::placeholder {
    color: rgba(180, 190, 255, 0.5);
    font-style: italic;
  }
  
  .light-mode .message-input::placeholder {
    color: rgba(100, 130, 200, 0.4);
  }

  .send-button {
    width: 42px;
    height: 42px;
    border: none;
    border-radius: 12px;
    background: linear-gradient(145deg, #4568ff, #3050e0);
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    box-shadow: 
      0 4px 12px rgba(70, 100, 255, 0.3),
      inset 0 1px 2px rgba(255, 255, 255, 0.2);
    position: relative;
    overflow: hidden;
  }
  
  .send-button::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 11px;
    padding: 1px;
    background: linear-gradient(140deg, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.01) 70%);
    -webkit-mask: linear-gradient(#000 0 0) content-box, 
                  linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
  }

  .send-button:hover:not(:disabled) {
    background: linear-gradient(145deg, #5a7eff, #4060f0);
    transform: translateY(-2px);
    box-shadow: 
      0 6px 16px rgba(70, 100, 255, 0.4),
      inset 0 1px 2px rgba(255, 255, 255, 0.3);
  }
  
  .send-button:active:not(:disabled) {
    transform: translateY(1px);
    box-shadow: 
      0 2px 8px rgba(70, 100, 255, 0.3),
      inset 0 1px 1px rgba(255, 255, 255, 0.2);
    transition: all 0.1s ease;
  }

  .send-button:disabled {
    background: linear-gradient(135deg, #3a4a68, #2a3a58);
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
    opacity: 0.6;
  }
  
  .light-mode .send-button:disabled {
    background: linear-gradient(135deg, #c0c8e0, #b0b8d0);
    box-shadow: none;
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
    background: rgba(28, 32, 44, 0.95);
    backdrop-filter: blur(25px);
    border-radius: 14px;
    box-shadow: 
      0 10px 30px rgba(0, 0, 0, 0.4),
      inset 0 0 0 1px rgba(70, 100, 255, 0.25);
    padding: 16px;
    z-index: 1000;
    border: none;
    overflow: hidden;
    position: relative;
  }
  
  .emoji-picker::before {
    content: "";
    position: absolute;
    inset: 0;
    border-radius: 13px;
    padding: 1px;
    background: linear-gradient(140deg, rgba(80, 120, 255, 0.4), rgba(70, 100, 220, 0.01) 70%);
    -webkit-mask: linear-gradient(#000 0 0) content-box, 
                  linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
    z-index: -1;
  }
  
  .light-mode .emoji-picker {
    background: rgba(250, 252, 255, 0.95);
    box-shadow: 
      0 10px 30px rgba(0, 30, 100, 0.15),
      inset 0 0 0 1px rgba(70, 100, 255, 0.18);
    border: none;
  }
  
  .light-mode .emoji-picker::before {
    background: linear-gradient(140deg, rgba(80, 120, 255, 0.3), rgba(70, 100, 220, 0.01) 70%);
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
    gap: 8px;
    padding: 12px 16px;
    align-items: center;
    position: relative;
    height: 40px; /* Fix height to prevent container resizing */
    min-width: 150px; /* Set minimum width */
    transform: translateZ(0); /* Force GPU acceleration */
    background: rgba(40, 60, 120, 0.15);
    border-radius: 20px;
    box-shadow: inset 0 0 0 1px rgba(70, 100, 255, 0.2);
    backdrop-filter: blur(8px);
    margin: 0 auto;
  }

  .typing-indicator::after {
    content: "Thinking...";
    font-size: 13px;
    color: rgba(120, 160, 255, 0.9);
    opacity: 0.9;
    animation: fadeInOut 1.5s infinite;
    margin-left: 4px;
    font-weight: 500;
    letter-spacing: 0.3px;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  }
  
  .light-mode .typing-indicator {
    background: rgba(70, 100, 255, 0.08);
    box-shadow: inset 0 0 0 1px rgba(70, 100, 255, 0.15);
  }
  
  .light-mode .typing-indicator::after {
    color: rgba(60, 90, 180, 0.9);
    text-shadow: none;
  }

  .typing-indicator span {
    width: 8px;
    height: 8px;
    background: linear-gradient(135deg, rgb(100, 160, 255), rgb(70, 110, 255));
    border-radius: 50%;
    animation: typing 1.4s infinite cubic-bezier(0.34, 1.56, 0.64, 1);
    box-shadow: 
      0 0 10px rgba(100, 140, 255, 0.7),
      0 0 4px rgba(80, 120, 255, 0.4);
    position: relative;
    filter: blur(0.3px);
    will-change: transform, opacity;
    opacity: 0.9;
  }
  
  .typing-indicator span::before {
    content: '';
    position: absolute;
    top: 1px;
    left: 2px;
    width: 3px;
    height: 3px;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 50%;
    filter: blur(0.3px);
  }

  .typing-indicator span:nth-child(1) { 
    animation-delay: 0s;
    transform-origin: center bottom;
  }
  
  .typing-indicator span:nth-child(2) { 
    animation-delay: 0.3s;
    transform-origin: center;
  }

  .typing-indicator span:nth-child(3) { 
    animation-delay: 0.6s;
    transform-origin: center top;
  }
  
  .light-mode .typing-indicator span {
    background: linear-gradient(135deg, rgb(70, 120, 255), rgb(50, 90, 240));
    box-shadow: 
      0 0 10px rgba(70, 100, 255, 0.5),
      0 0 4px rgba(70, 100, 255, 0.3);
  }

  @keyframes typing {
    0% { transform: scale(0.8) translateY(0); opacity: 0.7; }
    40% { transform: scale(1.2) translateY(-3px); opacity: 1; }
    70% { transform: scale(1.1) translateY(-2px); opacity: 0.9; }
    100% { transform: scale(0.8) translateY(0); opacity: 0.7; }
  }
  
  @keyframes fadeInOut {
    0% { opacity: 0.7; }
    50% { opacity: 1; }
    100% { opacity: 0.7; }
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