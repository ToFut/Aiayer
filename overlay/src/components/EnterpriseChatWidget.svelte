<script>
  import { onMount, tick } from 'svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import { elasticOut, cubicOut } from 'svelte/easing';
  
  export let show = false;
  export let initialPosition = { x: 20, y: 90 };
  export let wsEndpoint = 'ws://localhost:8765';  // Enhanced enterprise backend port
  
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
  
  // Advanced UI state
  let isCompactMode = false;
  let showModeSelector = true;
  let inputFocused = false;
  let lastUserInteraction = Date.now();
  let adaptiveLayout = 'normal'; // normal, compact, minimal
  let currentTheme = 'system'; // system, light, dark
  let gestureStartY = 0;
  let gestureCurrentY = 0;
  let isGesturing = false;
  let quickActionExpanded = false;
  let soundEnabled = true;
  let dropdownOpen = false;
  let dropdownFocused = false;
  
  // Apple-inspired mode configurations with enhanced metadata
  const modes = {
    'Ask': {
      emoji: '💭',
      name: 'Ask',
      description: 'Ask questions with contextual intelligence',
      color: '#007AFF',
      secondaryColor: '#5AC8FA',
      gradient: 'linear-gradient(135deg, #007AFF 0%, #5AC8FA 100%)',
      examples: [
        'What patterns do you see in my workflow?',
        'How can I optimize this process?',
        'Explain this concept to me'
      ],
      animationDelay: 0
    },
    'Agent': {
      emoji: '🤖', 
      name: 'Agent',
      description: 'Intelligent task planning and execution',
      color: '#FF3B30',
      secondaryColor: '#FF9500',
      gradient: 'linear-gradient(135deg, #FF3B30 0%, #FF9500 100%)',
      examples: [
        'Help me organize my workspace',
        'Create a productivity workflow',
        'Automate this routine task'
      ],
      animationDelay: 100
    },
    'Suggest': {
      emoji: '✨',
      name: 'Suggest', 
      description: 'Proactive insights and recommendations',
      color: '#30D158',
      secondaryColor: '#32D74B',
      gradient: 'linear-gradient(135deg, #30D158 0%, #32D74B 100%)',
      examples: [
        'Suggest improvements for my setup',
        'What should I focus on next?',
        'Recommend best practices'
      ],
      animationDelay: 200
    },
    'Creative': {
      emoji: '🎨',
      name: 'Creative',
      description: 'Brainstorm and ideate together', 
      color: '#AF52DE',
      secondaryColor: '#BF5AF2',
      gradient: 'linear-gradient(135deg, #AF52DE 0%, #BF5AF2 100%)',
      examples: [
        'Help me brainstorm ideas',
        'Create something unique',
        'Think outside the box with me'
      ],
      animationDelay: 300
    }
  };

  // Connection management
  let reconnectAttempts = 0;
  let maxReconnectAttempts = 5;
  let reconnectDelay = 1000;

  onMount(() => {
    connectToBackend();
    setupGestureListeners();
    setupKeyboardShortcuts();
    setupAdaptiveLayout();
    
    // Add click outside listener for dropdown
    document.addEventListener('click', handleClickOutside);
    
    return () => {
      if (ws) ws.close();
      cleanupEventListeners();
      document.removeEventListener('click', handleClickOutside);
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
    console.log('🎯 Enterprise message received:', data);
    
    if (data.type === 'connection_established') {
      console.log('🔗 Enterprise connection with capabilities:', data.capabilities);
      console.log('🚀 Server version:', data.server_version);
      return;
    }
    
    if (data.type === 'registration_success') {
      console.log('📋 Enterprise registration successful');
      return;
    }
    
    // Handle brain router response format: {success: true, response: "...", mode: "Ask", ...}
    if (data.success !== undefined && data.response) {
      hideTypingIndicator();
      
      const assistantMessage = {
        id: Date.now(),
        type: 'assistant',
        content: data.response || 'No response received',
        timestamp: new Date(),
        confidence: 1.0,
        mode: data.mode || currentMode,
        processingTime: data.processing_time || 0,
        resources: [],
        enterpriseValidated: data.enterprise_validated || false,
        processingWorker: data.processing_worker || 'unknown',
        
        // PROFESSIONAL AGENT DATA
        agentSessionId: data.agentSessionId,
        requiresConfirmation: data.requiresConfirmation || false,
        confirmationActions: data.confirmationActions || [],
        executionPlan: data.executionPlan,
        screenAnalysis: data.screen_analysis,
        estimatedDuration: data.estimatedDuration,
        confidence: data.confidence,
        riskLevel: data.riskLevel
      };
      
      messages = [...messages, assistantMessage];
      scrollToBottom();
      
      console.log('✅ Enterprise response processed:', {
        type: data.type,
        mode: data.mode,
        success: data.success,
        enterprise: data.enterprise_validated
      });
      
    } else if (data.type === 'error') {
      hideTypingIndicator();
      showError(data.error || data.message || 'An error occurred');
      console.error('❌ Enterprise error:', data);
    } else {
      console.log('⚠️ Unhandled enterprise message type:', data.type);
    }
  }

  function selectMode(mode) {
    if (currentMode === mode) return;
    
    currentMode = mode;
    playSound('mode-switch');
    
    // Haptic feedback simulation
    if (navigator.vibrate) {
      navigator.vibrate(10);
    }
    
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
    playSound('message-sent');
    
    const messageToSend = input.trim();
    input = '';
    
    showTypingIndicator();
    
    // Use correct brain router message format
    const payload = {
      type: "chat_request",
      mode: currentMode,
      message: messageToSend,
      session_id: sessionId,
      timestamp: new Date().toISOString()
    };

    console.log('🚀 Sending enterprise message:', payload);
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

  // PROFESSIONAL AGENT CONFIRMATION HANDLERS
  function handleAgentConfirmation(sessionId, action, modifications = {}) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected for agent confirmation');
      return;
    }

    const confirmationMessage = {
      type: 'agent_confirmation',
      session_id: sessionId,
      action: action, // DO, DISMISS, ADJUST
      modifications: modifications,
      timestamp: new Date().toISOString()
    };

    console.log('🎯 Sending agent confirmation:', confirmationMessage);
    ws.send(JSON.stringify(confirmationMessage));

    // Show feedback
    if (action === 'DO') {
      showTypingIndicator('🚀 Executing plan...');
    } else if (action === 'DISMISS') {
      showTypingIndicator('❌ Cancelling...');
    } else if (action === 'ADJUST') {
      showTypingIndicator('🔧 Adjusting plan...');
    }
  }

  function showTypingIndicator(customMessage = null) {
    isTyping = true;
    if (customMessage) {
      // Could add custom typing message here
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

  // Apple-inspired sound effects (if enabled)
  const playSound = (type) => {
    if (!soundEnabled) return;
    try {
      const audioContext = getAudioContext();
      synthesizeSound(audioContext, type);
    } catch (error) {
      console.warn('Could not play sound:', error);
    }
  };

  function getAudioContext() {
    if (!window.audioContext) {
      window.audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    return window.audioContext;
  }

  function synthesizeSound(audioContext, type) {
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    const soundConfig = {
      'mode-switch': { frequency: 800, duration: 0.1, volume: 0.1 },
      'message-sent': { frequency: 1000, duration: 0.08, volume: 0.08 },
      'message-received': { frequency: 700, duration: 0.12, volume: 0.1 },
      'interface-click': { frequency: 600, duration: 0.05, volume: 0.05 }
    };
    
    const config = soundConfig[type] || soundConfig['interface-click'];
    
    oscillator.frequency.setValueAtTime(config.frequency, audioContext.currentTime);
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0, audioContext.currentTime);
    gainNode.gain.linearRampToValueAtTime(config.volume, audioContext.currentTime + 0.01);
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + config.duration);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + config.duration);
  }

  // Gesture support
  function setupGestureListeners() {
    // Touch gestures for mobile-like interactions
    document.addEventListener('touchstart', handleTouchStart, { passive: false });
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleTouchEnd, { passive: false });
  }

  function handleTouchStart(event) {
    if (!show) return;
    gestureStartY = event.touches[0].clientY;
    isGesturing = true;
  }

  function handleTouchMove(event) {
    if (!isGesturing || !show) return;
    gestureCurrentY = event.touches[0].clientY;
    
    const deltaY = gestureCurrentY - gestureStartY;
    
    // Pull down to minimize
    if (deltaY > 50 && !showMinimized) {
      toggleMinimize();
      isGesturing = false;
    }
    
    // Pull up to expand
    if (deltaY < -50 && showMinimized) {
      toggleMinimize();
      isGesturing = false;
    }
  }

  function handleTouchEnd() {
    isGesturing = false;
  }

  // Keyboard shortcuts
  function setupKeyboardShortcuts() {
    document.addEventListener('keydown', handleGlobalKeyDown);
  }

  function handleGlobalKeyDown(event) {
    if (!show) return;
    
    // Cmd/Ctrl + 1-4 for mode switching
    if ((event.metaKey || event.ctrlKey) && ['1', '2', '3', '4'].includes(event.key)) {
      event.preventDefault();
      const modeKeys = Object.keys(modes);
      const modeIndex = parseInt(event.key) - 1;
      if (modeKeys[modeIndex]) {
        selectMode(modeKeys[modeIndex]);
      }
    }
    
    // Escape to minimize
    if (event.key === 'Escape') {
      if (!showMinimized) {
        toggleMinimize();
      }
    }
    
    // Cmd/Ctrl + K to focus input
    if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
      event.preventDefault();
      const inputElement = document.querySelector('.message-input');
      if (inputElement) {
        inputElement.focus();
      }
    }
  }

  // Adaptive layout based on usage patterns
  function setupAdaptiveLayout() {
    setInterval(() => {
      const timeSinceInteraction = Date.now() - lastUserInteraction;
      
      if (timeSinceInteraction > 300000) { // 5 minutes
        adaptiveLayout = 'minimal';
      } else if (timeSinceInteraction > 60000) { // 1 minute
        adaptiveLayout = 'compact';
      } else {
        adaptiveLayout = 'normal';
      }
    }, 10000);
  }

  function cleanupEventListeners() {
    document.removeEventListener('touchstart', handleTouchStart);
    document.removeEventListener('touchmove', handleTouchMove);
    document.removeEventListener('touchend', handleTouchEnd);
    document.removeEventListener('keydown', handleGlobalKeyDown);
  }

  // Quick actions
  function toggleQuickActions() {
    quickActionExpanded = !quickActionExpanded;
    playSound('interface-click');
  }

  function clearConversation() {
    messages = [];
    playSound('interface-click');
  }

  function toggleSound() {
    soundEnabled = !soundEnabled;
    if (soundEnabled) {
      playSound('interface-click');
    }
  }

  function handleInputFocus() {
    inputFocused = true;
    lastUserInteraction = Date.now();
  }

  function handleInputBlur() {
    inputFocused = false;
  }

  // Dropdown functions
  function toggleDropdown() {
    dropdownOpen = !dropdownOpen;
    playSound('interface-click');
  }

  function closeDropdown() {
    dropdownOpen = false;
  }

  function selectModeFromDropdown(mode) {
    selectMode(mode);
    closeDropdown();
  }

  function handleDropdownKeydown(event) {
    if (event.key === 'Escape') {
      closeDropdown();
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      toggleDropdown();
    } else {
      handleDropdownNavigation(event);
    }
  }

  // Close dropdown when clicking outside
  function handleClickOutside(event) {
    if (dropdownOpen && !event.target.closest('.mode-dropdown-wrapper')) {
      closeDropdown();
    }
  }

  // Enhanced keyboard navigation for dropdown
  function handleDropdownNavigation(event) {
    if (!dropdownOpen) return;
    
    const modeKeys = Object.keys(modes);
    const currentIndex = modeKeys.indexOf(currentMode);
    
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        const nextIndex = (currentIndex + 1) % modeKeys.length;
        selectMode(modeKeys[nextIndex]);
        break;
      case 'ArrowUp':
        event.preventDefault();
        const prevIndex = (currentIndex - 1 + modeKeys.length) % modeKeys.length;
        selectMode(modeKeys[prevIndex]);
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        closeDropdown();
        break;
      case 'Escape':
        event.preventDefault();
        closeDropdown();
        break;
    }
  }
</script>

{#if show}
<div 
  class="chat-overlay" 
  class:minimized={showMinimized}
  class:compact={adaptiveLayout === 'compact'}
  class:minimal={adaptiveLayout === 'minimal'}
  style="left: {position.x}px; top: {position.y}px; width: {size.width}px; height: {showMinimized ? 80 : size.height}px;"
  transition:scale={{ duration: 400, easing: elasticOut }}
>
  <!-- Header -->
  <div class="chat-header" on:mousedown={startDrag}>
    <div class="header-left">
      <div class="status-indicator" style="background-color: {getStatusColor()};"></div>
      <span class="title">Enterprise SensAI</span>
    </div>
    <div class="header-controls">
      <button class="control-btn sound-btn" class:active={soundEnabled} on:click={toggleSound} title="Toggle Sound">
        {soundEnabled ? '🔊' : '🔇'}
      </button>
      <button class="control-btn minimize-btn" on:click={toggleMinimize} title={showMinimized ? 'Expand' : 'Minimize'}>
        {showMinimized ? '◯' : '−'}
      </button>
      <button class="control-btn close-btn" on:click={closeChat} title="Close">×</button>
    </div>
  </div>

  {#if !showMinimized}

    <!-- Messages -->
    <div class="chat-messages" bind:this={chatContainer}>
      {#each messages as message (message.id)}
        <div class="message {message.type}" transition:fly={{ y: 20, duration: 300 }}>
          <div class="message-content">
            {@html message.content.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}
          </div>
          
          <!-- PROFESSIONAL AGENT CONFIRMATION INTERFACE -->
          {#if message.requiresConfirmation && message.agentSessionId}
            <div class="agent-confirmation-panel">
              <div class="confirmation-header">
                <span class="confirmation-title">🤖 Professional Agent Ready</span>
                <div class="plan-metrics">
                  <span class="metric">⏱️ {message.estimatedDuration || 0}s</span>
                  <span class="metric">🎯 {Math.round((message.confidence || 0) * 100)}%</span>
                  <span class="metric risk-{message.riskLevel || 'medium'}">⚠️ {(message.riskLevel || 'medium').toUpperCase()}</span>
                </div>
              </div>
              
              <div class="confirmation-actions">
                <button 
                  class="confirmation-btn do-btn"
                  on:click={() => handleAgentConfirmation(message.agentSessionId, 'DO')}
                >
                  🟢 DO
                  <span class="btn-subtitle">Execute Plan</span>
                </button>
                
                <button 
                  class="confirmation-btn dismiss-btn"
                  on:click={() => handleAgentConfirmation(message.agentSessionId, 'DISMISS')}
                >
                  🔴 DISMISS
                  <span class="btn-subtitle">Cancel</span>
                </button>
                
                <button 
                  class="confirmation-btn adjust-btn"
                  on:click={() => handleAgentConfirmation(message.agentSessionId, 'ADJUST')}
                >
                  🔧 ADJUST
                  <span class="btn-subtitle">Modify Plan</span>
                </button>
              </div>
              
              {#if message.executionPlan && message.executionPlan.total_steps}
                <div class="plan-preview">
                  <div class="plan-summary">
                    📋 {message.executionPlan.total_steps} steps planned
                    {#if message.executionPlan.warnings && message.executionPlan.warnings.length > 0}
                      <span class="warning-indicator">⚠️ {message.executionPlan.warnings.length} warnings</span>
                    {/if}
                  </div>
                </div>
              {/if}
            </div>
          {/if}
          
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

    <!-- Enhanced Input Area -->
    <div class="input-area" class:focused={inputFocused}>
      <div class="input-container">
        <div class="input-wrapper">
          <!-- Compact Mode Trigger Button -->
          <button 
            class="cursor-mode-trigger"
            class:open={dropdownOpen}
            class:focused={dropdownFocused}
            class:hidden={adaptiveLayout === 'minimal'}
            on:click={toggleDropdown}
            on:keydown={handleDropdownKeydown}
            on:focus={() => dropdownFocused = true}
            on:blur={() => dropdownFocused = false}
            style="--current-mode-color: {modes[currentMode]?.color}; --current-mode-gradient: {modes[currentMode]?.gradient};"
            title="Switch mode - {modes[currentMode]?.description}"
            aria-label="Mode selector: {modes[currentMode]?.name}"
            aria-expanded={dropdownOpen}
            aria-haspopup="listbox"
          >
            <div class="mode-trigger-content">
              <span class="mode-icon">{modes[currentMode]?.emoji}</span>
              <span class="mode-name">{modes[currentMode]?.name}</span>
              <div class="mode-chevron" class:rotated={dropdownOpen}>
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>
            </div>
            <div class="mode-trigger-bg"></div>
          </button>

          <textarea
            bind:value={input}
            placeholder="Message {modes[currentMode]?.name || 'AI'}..."
            class="message-input"
            on:keydown={handleKeyDown}
            on:focus={handleInputFocus}
            on:blur={handleInputBlur}
            disabled={connectionStatus !== 'connected'}
            rows="1"
          ></textarea>
        </div>
        
        <button 
          class="send-btn" 
          class:active={input.trim().length > 0}
          on:click={sendMessage}
          disabled={!input.trim() || connectionStatus !== 'connected'}
          style="background: {modes[currentMode]?.gradient};"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22 2L11 13" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Floating Mode Dropdown (positioned outside input area) -->
    {#if dropdownOpen && adaptiveLayout !== 'minimal'}
      <div 
        class="cursor-mode-dropdown-floating"
        role="listbox"
        aria-label="Available modes"
        in:fly={{ y: 8, duration: 200, easing: cubicOut }}
        out:fly={{ y: 4, duration: 150, easing: cubicOut }}
      >
        <div class="dropdown-options">
          {#each Object.entries(modes) as [modeKey, modeData], index}
            <button 
              class="cursor-mode-option"
              class:selected={currentMode === modeKey}
              style="--mode-color: {modeData.color}; --mode-gradient: {modeData.gradient};"
              on:click={() => selectModeFromDropdown(modeKey)}
              role="option"
              aria-selected={currentMode === modeKey}
              in:fly={{ y: 6, duration: 160, delay: index * 30, easing: cubicOut }}
            >
              <div class="option-leading">
                <div class="option-icon-wrapper">
                  <span class="option-icon">{modeData.emoji}</span>
                </div>
              </div>
              
              <div class="option-content">
                <div class="option-title">{modeData.name}</div>
                <div class="option-description">{modeData.description}</div>
              </div>
              
              <div class="option-trailing">
                {#if currentMode === modeKey}
                  <div class="option-checkmark">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M13.5 4.5L6 12L2.5 8.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                {/if}
                <div class="option-shortcut">⌘{index + 1}</div>
              </div>
              
              <div class="option-hover-bg"></div>
            </button>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
</div>
{/if}

<style>
  /* CSS Custom Properties for Apple-inspired theming */
  .chat-overlay {
    --primary-blur: saturate(180%) blur(20px);
    --secondary-blur: blur(10px);
    --border-radius-large: 20px;
    --border-radius-medium: 12px;
    --shadow-large: 0 20px 40px rgba(0, 0, 0, 0.2);
    --transition-normal: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    --font-system: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, system-ui, sans-serif;
    
    position: fixed;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: var(--border-radius-large);
    backdrop-filter: var(--primary-blur);
    -webkit-backdrop-filter: var(--primary-blur);
    box-shadow: var(--shadow-large);
    display: flex;
    flex-direction: column;
    z-index: 10000;
    pointer-events: auto;
    transition: all var(--transition-normal);
    overflow: hidden;
    font-family: var(--font-system);
  }

  .chat-overlay.minimized {
    height: 80px !important;
  }

  .chat-header {
    padding: 16px 20px;
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: var(--secondary-blur);
    border-bottom: 1px solid rgba(255, 255, 255, 0.3);
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: grab;
    user-select: none;
    transition: all var(--transition-normal);
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

  /* Compact Cursor-Style Trigger Button in Input */
  .cursor-mode-trigger {
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 14px;
    padding: 0;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex;
    align-items: center;
    font-family: var(--font-system);
    backdrop-filter: blur(12px);
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 10;
    overflow: hidden;
    min-width: 85px;
    height: 32px;
  }

  .cursor-mode-trigger.hidden {
    opacity: 0;
    pointer-events: none;
    transform: translateY(-50%) scale(0.95);
  }

  .mode-trigger-content {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 0 10px;
    position: relative;
    z-index: 2;
  }

  .mode-trigger-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--current-mode-gradient);
    opacity: 0;
    transition: opacity var(--transition-normal);
    z-index: 1;
  }

  .cursor-mode-trigger:hover {
    background: rgba(255, 255, 255, 0.18);
    border-color: rgba(255, 255, 255, 0.24);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .cursor-mode-trigger:hover .mode-trigger-bg {
    opacity: 0.12;
  }

  .cursor-mode-trigger.open {
    background: rgba(255, 255, 255, 0.2);
    border-color: var(--current-mode-color);
    box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.15), 0 6px 20px rgba(0, 0, 0, 0.2);
  }

  .cursor-mode-trigger.open .mode-trigger-bg {
    opacity: 0.2;
  }

  .cursor-mode-trigger.focused {
    outline: none;
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.25);
  }

  .mode-icon {
    font-size: 14px;
    line-height: 1;
    position: relative;
    z-index: 2;
  }

  .mode-name {
    font-weight: 500;
    font-size: 13px;
    color: rgba(255, 255, 255, 0.92);
    white-space: nowrap;
    position: relative;
    z-index: 2;
  }

  .mode-chevron {
    color: rgba(255, 255, 255, 0.7);
    transition: all var(--transition-normal);
    position: relative;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .mode-chevron.rotated {
    transform: rotate(180deg);
    color: var(--current-mode-color);
  }

  /* Floating Cursor-Style Dropdown */
  .cursor-mode-dropdown-floating {
    position: absolute;
    bottom: 70px;
    left: 16px;
    min-width: 260px;
    max-width: 320px;
    background: rgba(255, 255, 255, 0.98);
    border: 1px solid rgba(255, 255, 255, 0.24);
    border-radius: 16px;
    backdrop-filter: blur(40px);
    box-shadow: 
      0 16px 32px rgba(0, 0, 0, 0.12),
      0 4px 16px rgba(0, 0, 0, 0.06),
      inset 0 1px 0 rgba(255, 255, 255, 0.5);
    overflow: hidden;
    z-index: 1002;
    padding: 8px;
  }

  /* Removed dropdown header for cleaner Cursor-like design */

  .dropdown-options {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  /* Cursor-Style Option Buttons */
  .cursor-mode-option {
    width: 100%;
    background: transparent;
    border: none;
    border-radius: 12px;
    padding: 8px 10px;
    cursor: pointer;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex;
    align-items: center;
    font-family: var(--font-system);
    position: relative;
    overflow: hidden;
    gap: 10px;
  }

  .cursor-mode-option:hover {
    background: rgba(0, 0, 0, 0.05);
    transform: translateY(-1px);
  }

  .cursor-mode-option.selected {
    background: rgba(0, 122, 255, 0.1);
    border: 1px solid rgba(0, 122, 255, 0.2);
  }

  .cursor-mode-option.selected:hover {
    background: rgba(0, 122, 255, 0.15);
  }

  .option-hover-bg {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--mode-gradient);
    opacity: 0;
    transition: opacity var(--transition-normal);
    pointer-events: none;
  }

  .cursor-mode-option:hover .option-hover-bg {
    opacity: 0.08;
  }

  .option-leading {
    flex-shrink: 0;
  }

  .option-icon-wrapper {
    width: 28px;
    height: 28px;
    background: rgba(0, 0, 0, 0.05);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
  }

  .option-icon-wrapper::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--mode-gradient);
    opacity: 0.15;
  }

  .option-icon {
    font-size: 16px;
    position: relative;
    z-index: 1;
  }

  .option-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    text-align: left;
    gap: 2px;
  }

  .option-title {
    font-size: 13px;
    font-weight: 600;
    color: rgba(0, 0, 0, 0.9);
    line-height: 1.2;
  }

  .option-description {
    font-size: 11px;
    color: rgba(0, 0, 0, 0.6);
    line-height: 1.3;
  }

  .option-trailing {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 4px;
    flex-shrink: 0;
  }

  .option-checkmark {
    color: var(--mode-color);
    opacity: 0.9;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .option-shortcut {
    font-size: 11px;
    color: rgba(0, 0, 0, 0.4);
    font-weight: 500;
    padding: 2px 6px;
    background: rgba(0, 0, 0, 0.06);
    border-radius: 6px;
    min-width: 24px;
    text-align: center;
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
    padding: 16px 20px 20px;
    background: rgba(255, 255, 255, 0.8);
    border-top: 1px solid rgba(255, 255, 255, 0.3);
    backdrop-filter: var(--secondary-blur);
    transition: all var(--transition-normal);
  }
  
  .input-area.focused {
    background: rgba(255, 255, 255, 0.95);
  }

  .input-container {
    display: flex;
    gap: 10px;
    align-items: flex-end;
  }

  .message-input {
    flex: 1;
    background: transparent;
    border: none;
    border-radius: 20px;
    padding: 12px 16px 12px 110px;
    color: rgba(0, 0, 0, 0.9);
    font-size: 16px;
    font-family: var(--font-system);
    resize: none;
    max-height: 120px;
    min-height: 24px;
    line-height: 1.4;
    outline: none;
    transition: all var(--transition-normal);
    width: 100%;
  }

  .message-input:focus {
    border-color: rgba(0, 122, 255, 0.5);
    box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.1);
  }

  .message-input::placeholder {
    color: rgba(0, 0, 0, 0.4);
  }

  .message-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .send-btn {
    width: 44px;
    height: 44px;
    border-radius: 22px;
    border: none;
    background: #8E8E93;
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all var(--transition-normal);
    backdrop-filter: blur(5px);
    font-size: 18px;
  }
  
  .send-btn.active {
    background: var(--mode-color);
    transform: scale(1.05);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }

  .send-btn:hover:not(:disabled) {
    transform: scale(1.1);
  }
  
  .send-btn:active {
    transform: scale(0.95);
  }

  .send-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }


  /* Input wrapper styling */
  .input-wrapper {
    flex: 1;
    position: relative;
    background: rgba(255, 255, 255, 0.9);
    border: 2px solid rgba(255, 255, 255, 0.5);
    border-radius: 20px;
    transition: all var(--transition-normal);
    backdrop-filter: blur(10px);
  }

  .input-area.focused .input-wrapper {
    border-color: rgba(0, 122, 255, 0.5);
    box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.1);
  }

  .input-accessories {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .mode-indicator-mini {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    color: white;
    background: var(--mode-gradient);
  }

  /* Control button enhancements */
  .control-btn.sound-btn.active {
    background: rgba(0, 122, 255, 0.15);
    color: #007AFF;
  }

  /* Responsive design for compact mode */
  .chat-overlay.compact .cursor-mode-selector {
    left: 10px;
  }

  .chat-overlay.compact .cursor-mode-trigger {
    min-width: 45px;
    height: 28px;
  }

  .chat-overlay.compact .mode-name {
    display: none;
  }

  .chat-overlay.compact .message-input {
    padding-left: 70px;
  }

  /* Minimal mode hides mode selector */
  .chat-overlay.minimal .cursor-mode-selector {
    display: none;
  }

  .chat-overlay.minimal .message-input {
    padding-left: 16px;
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

  /* PROFESSIONAL AGENT CONFIRMATION INTERFACE */
  .agent-confirmation-panel {
    margin: 12px 0;
    padding: 16px;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(255, 77, 77, 0.1) 100%);
    border: 1px solid rgba(102, 126, 234, 0.3);
    border-radius: 12px;
    backdrop-filter: blur(10px);
  }

  .confirmation-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .confirmation-title {
    font-weight: 600;
    color: #fff;
    font-size: 14px;
  }

  .plan-metrics {
    display: flex;
    gap: 8px;
  }

  .metric {
    background: rgba(255, 255, 255, 0.1);
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 11px;
    color: rgba(255, 255, 255, 0.8);
  }

  .metric.risk-low {
    background: rgba(76, 175, 80, 0.2);
    color: #4CAF50;
  }

  .metric.risk-medium {
    background: rgba(255, 152, 0, 0.2);
    color: #FF9800;
  }

  .metric.risk-high {
    background: rgba(244, 67, 54, 0.2);
    color: #F44336;
  }

  .confirmation-actions {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 8px;
    margin-bottom: 12px;
  }

  .confirmation-btn {
    padding: 12px 8px;
    border: none;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    color: #fff;
  }

  .btn-subtitle {
    font-size: 10px;
    font-weight: 400;
    opacity: 0.8;
  }

  .do-btn {
    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);
  }

  .do-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
  }

  .dismiss-btn {
    background: linear-gradient(135deg, #f44336 0%, #d32f2f 100%);
    box-shadow: 0 2px 8px rgba(244, 67, 54, 0.3);
  }

  .dismiss-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(244, 67, 54, 0.4);
  }

  .adjust-btn {
    background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
    box-shadow: 0 2px 8px rgba(255, 152, 0, 0.3);
  }

  .adjust-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(255, 152, 0, 0.4);
  }

  .plan-preview {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 12px;
  }

  .plan-summary {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    color: rgba(255, 255, 255, 0.8);
  }

  .warning-indicator {
    background: rgba(255, 152, 0, 0.2);
    color: #FF9800;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 11px;
  }

  /* Dark mode support */
  @media (prefers-color-scheme: dark) {
    .chat-overlay {
      background: rgba(28, 28, 30, 0.95);
      border-color: rgba(255, 255, 255, 0.1);
    }

    .chat-header {
      background: rgba(44, 44, 46, 0.9);
      border-color: rgba(255, 255, 255, 0.05);
    }

    .title {
      color: rgba(255, 255, 255, 0.9);
    }

    .mode-card {
      background: rgba(44, 44, 46, 0.8);
      border-color: rgba(255, 255, 255, 0.08);
    }

    .mode-card:hover {
      background: rgba(58, 58, 60, 0.9);
      border-color: rgba(255, 255, 255, 0.15);
    }

    .mode-card.active {
      background: rgba(44, 44, 46, 0.95);
      border-color: var(--mode-color);
    }

    /* Cursor-inspired mode selector dark mode */
    .cursor-mode-trigger {
      background: rgba(44, 44, 46, 0.8);
      border-color: rgba(255, 255, 255, 0.12);
    }

    .cursor-mode-trigger:hover {
      background: rgba(58, 58, 60, 0.9);
      border-color: rgba(255, 255, 255, 0.2);
    }

    .cursor-mode-dropdown {
      background: rgba(28, 28, 30, 0.98);
      border-color: rgba(255, 255, 255, 0.12);
      box-shadow: 
        0 20px 40px rgba(0, 0, 0, 0.4),
        0 4px 8px rgba(0, 0, 0, 0.2),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
    }

    /* Removed dropdown header dark mode styles - no longer needed */

    .option-title {
      color: rgba(255, 255, 255, 0.9);
    }

    .option-description {
      color: rgba(255, 255, 255, 0.6);
    }

    .option-icon-wrapper {
      background: rgba(255, 255, 255, 0.08);
    }

    .option-shortcut {
      background: rgba(255, 255, 255, 0.08);
      color: rgba(255, 255, 255, 0.5);
    }

    .cursor-mode-option:hover {
      background: rgba(255, 255, 255, 0.08);
    }

    .cursor-mode-option.selected {
      background: rgba(0, 122, 255, 0.2);
      border-color: rgba(0, 122, 255, 0.4);
    }

    .cursor-mode-option.selected:hover {
      background: rgba(0, 122, 255, 0.25);
    }

    .message.assistant .message-content {
      background: rgba(44, 44, 46, 0.8);
      border-color: rgba(255, 255, 255, 0.1);
      color: rgba(255, 255, 255, 0.9);
    }

    .input-area {
      background: rgba(44, 44, 46, 0.9);
      border-color: rgba(255, 255, 255, 0.05);
    }

    .input-wrapper,
    .message-input {
      background: rgba(58, 58, 60, 0.9);
      border-color: rgba(255, 255, 255, 0.1);
      color: rgba(255, 255, 255, 0.9);
    }

    .message-input::placeholder {
      color: rgba(255, 255, 255, 0.4);
    }

    .input-area.focused .input-wrapper {
      border-color: rgba(0, 122, 255, 0.6);
      box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.15);
    }

    .example-btn {
      background: rgba(58, 58, 60, 0.6);
      border-color: rgba(255, 255, 255, 0.08);
      color: rgba(255, 255, 255, 0.7);
    }

    .example-btn:hover {
      background: rgba(72, 72, 74, 0.8);
      color: rgba(255, 255, 255, 0.9);
    }

    .typing-indicator {
      background: rgba(58, 58, 60, 0.8);
      color: rgba(255, 255, 255, 0.7);
    }

    .control-btn {
      background: rgba(58, 58, 60, 0.8);
      color: rgba(255, 255, 255, 0.8);
    }

    .control-btn:hover {
      background: rgba(72, 72, 74, 0.9);
    }
  }

  /* High contrast mode support */
  @media (prefers-contrast: high) {
    .chat-overlay {
      border-width: 3px;
      border-color: #000;
      backdrop-filter: none;
      background: rgba(255, 255, 255, 0.98);
    }

    .mode-card {
      border-width: 2px;
      border-color: #000;
      background: rgba(255, 255, 255, 0.95);
    }

    .mode-card.active {
      background: var(--mode-color);
      color: white;
    }

    .mode-name,
    .mode-desc {
      color: #000;
    }

    .mode-card.active .mode-name,
    .mode-card.active .mode-desc {
      color: white;
    }

    .message-input {
      border-width: 2px;
      border-color: #000;
      background: white;
      color: #000;
    }

    .control-btn {
      border: 2px solid #000;
      background: white;
      color: #000;
    }

    .send-btn {
      border: 2px solid #000;
    }
  }

  /* Reduced motion support */
  @media (prefers-reduced-motion: reduce) {
    * {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
    }

    .mode-card {
      transform: none !important;
    }

    .chat-overlay {
      animation: none !important;
    }

    .send-btn:hover {
      transform: none !important;
    }

    .example-btn:hover {
      transform: none !important;
    }

    .confirmation-btn:hover {
      transform: none !important;
    }
  }

  /* Enhanced focus states for accessibility */
  .cursor-mode-trigger:focus,
  .cursor-mode-option:focus,
  .message-input:focus,
  .send-btn:focus,
  .control-btn:focus,
  .example-btn:focus,
  .confirmation-btn:focus {
    outline: 3px solid var(--accent-color, #007AFF);
    outline-offset: 2px;
  }

  .cursor-mode-trigger:focus {
    border-color: var(--accent-color, #007AFF);
    box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.25);
  }

  .cursor-mode-option:focus {
    background: rgba(0, 122, 255, 0.12);
    outline-offset: -2px;
  }

  /* Screen reader only content */
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  /* Loading states */
  .loading-indicator {
    display: inline-block;
    width: 20px;
    height: 20px;
    border: 2px solid rgba(0, 122, 255, 0.3);
    border-radius: 50%;
    border-top-color: #007AFF;
    animation: spin 1s ease-in-out infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* Error and success states */
  .error-message {
    color: #FF3B30;
    background: rgba(255, 59, 48, 0.1);
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 14px;
    margin: 8px 0;
    border: 1px solid rgba(255, 59, 48, 0.2);
    backdrop-filter: blur(10px);
  }

  .success-message {
    color: #30D158;
    background: rgba(48, 209, 88, 0.1);
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 14px;
    margin: 8px 0;
    border: 1px solid rgba(48, 209, 88, 0.2);
    backdrop-filter: blur(10px);
  }

  /* Enhanced message animations */
  .message {
    opacity: 0;
    animation: messageSlideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  }

  @keyframes messageSlideIn {
    from {
      opacity: 0;
      transform: translateY(20px) scale(0.95);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  /* Performance optimizations */
  .chat-overlay {
    contain: layout style paint;
    will-change: transform;
  }

  .mode-card {
    contain: layout style;
  }

  .message {
    contain: layout style;
  }

  /* Enhanced gradients and glassmorphism */
  .chat-overlay::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, 
      rgba(255, 255, 255, 0.1) 0%,
      rgba(255, 255, 255, 0.05) 50%,
      rgba(255, 255, 255, 0.1) 100%);
    pointer-events: none;
    z-index: -1;
  }

  /* Status indicator enhancements */
  .status-indicator {
    box-shadow: 0 0 6px currentColor;
    animation: statusPulse 2s ease-in-out infinite;
  }

  @keyframes statusPulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  /* Input enhancements */
  .message-input {
    font-variant-numeric: proportional-nums;
    font-feature-settings: "kern" 1, "liga" 1;
  }

  /* Advanced hover effects */
  .mode-card::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at var(--mouse-x, 50%) var(--mouse-y, 50%), 
      rgba(255, 255, 255, 0.1) 0%, 
      transparent 50%);
    opacity: 0;
    transition: opacity 0.3s ease;
    pointer-events: none;
  }

  .mode-card:hover::after {
    opacity: 1;
  }

  /* Enhanced scrolling */
  .chat-messages {
    scroll-behavior: smooth;
    scrollbar-width: thin;
    scrollbar-color: rgba(255, 255, 255, 0.3) transparent;
  }

  /* Touch device optimizations */
  @media (hover: none) and (pointer: coarse) {
    .mode-card {
      min-height: 48px;
    }

    .control-btn {
      min-width: 44px;
      min-height: 44px;
    }

    .send-btn {
      min-width: 48px;
      min-height: 48px;
    }
  }

  /* Print styles */
  @media print {
    .chat-overlay {
      position: static;
      box-shadow: none;
      border: 1px solid #000;
      background: white;
    }

    .chat-header,
    .mode-selector,
    .input-area {
      display: none;
    }

    .message {
      break-inside: avoid;
    }
  }
</style>