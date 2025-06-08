<script>
  import { onMount, tick, onDestroy } from 'svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import { cubicOut, quintOut } from 'svelte/easing';
  import { CONFIG } from '../config.js';
  
  // Lazy-loaded components to improve initial loading time
  import { lazyLoad } from '../utils/lazyLoad.js';
  const ScreenViewer = lazyLoad(() => import('./ScreenViewer.svelte'));
  const EpiphanyMode = lazyLoad(() => import('./EpiphanyMode.svelte'));
  const VoiceRecorder = lazyLoad(() => import('./VoiceRecorder.svelte'));
  const VoiceCaller = lazyLoad(() => import('./VoiceCaller.svelte'));
  
  // Props
  export let show = false;
  export let initialPosition = { x: 20, y: 90 };
  export let wsEndpoint = CONFIG.websockets.llm.url || 'ws://localhost:8767';
  
  // State
  let messages = [];
  let input = '';
  let ws = null;
  let isTyping = false;
  let typingMessage = 'AI is thinking...';
  let connectionStatus = 'disconnected';
  let currentMode = 'Ask';
  let userId = 'overlay_user_' + Date.now();
  let sessionId = 'overlay_session_' + Date.now();
  
  // UI state
  let chatContainer;
  let isDragging = false;
  let showMinimized = false;
  let position = { ...initialPosition };
  let startX, startY, initialX, initialY;
  let size = { width: 420, height: 680 };
  let inputFocused = false;
  let modeDropdownOpen = false;
  let showScreenViewer = false;
  let showVoiceRecorder = false;
  let showVoiceCaller = false;
  let soundEnabled = true;
  let isGesturing = false;
  
  // Advanced UI state
  let showModeSelector = true;
  let quickActionExpanded = false;
  let pendingConfirmation = null;
  let currentProgress = { progress: 0, currentStep: '', stepNumber: 0, totalSteps: 0 };
  let progressVisible = false;
  
  // Audio elements cache - Improves performance by reusing Audio objects
  const audioCache = new Map();
  
  // WebSocket connection state
  let wsConnectionAttempts = 0;
  let wsReconnectDelay = 1000;
  let wsReconnectTimer = null;
  
  // Event handlers for voice features
  let voiceRecordingCallback = null;
  let voiceCallStatus = "inactive";
  
  // Chat mode configurations
  const modes = {
    'Ask': {
      emoji: '💭',
      name: 'Ask',
      description: 'Deep analysis and comprehensive explanations',
      color: '#007AFF',
      secondaryColor: '#5AC8FA',
      gradient: 'linear-gradient(135deg, #007AFF 0%, #5AC8FA 100%)',
      examples: [
        'Explain how machine learning algorithms work',
        'What are the key differences between React and Vue?',
        'Analyze the pros and cons of remote work'
      ],
    },
    'Agent': {
      emoji: '🤖', 
      name: 'Agent',
      description: 'Task automation and step-by-step execution',
      color: '#FF3B30',
      secondaryColor: '#FF9500',
      gradient: 'linear-gradient(135deg, #FF3B30 0%, #FF9500 100%)',
      examples: [
        'Create a daily productivity workflow for me',
        'Help me set up a project management system',
        'Automate my email organization process'
      ],
    },
    'Suggest': {
      emoji: '✨',
      name: 'Suggest', 
      description: 'Optimization recommendations and improvements',
      color: '#30D158',
      secondaryColor: '#32D74B',
      gradient: 'linear-gradient(135deg, #30D158 0%, #32D74B 100%)',
      examples: [
        'Suggest ways to improve my coding practices',
        'What tools could enhance my workflow?',
        'Recommend strategies for better time management'
      ],
    },
    'Creative': {
      emoji: '🎨',
      name: 'Creative',
      description: 'Innovative ideation and creative collaboration', 
      color: '#AF52DE',
      secondaryColor: '#BF5AF2',
      gradient: 'linear-gradient(135deg, #AF52DE 0%, #BF5AF2 100%)',
      examples: [
        'Brainstorm unique app ideas for sustainability',
        'Help me design an engaging user experience',
        'Create innovative solutions for team collaboration'
      ],
    },
    'Epiphany': {
      emoji: '⚡',
      name: 'Epiphany',
      description: 'Autonomous awareness and proactive suggestions',
      color: '#5B47FB',
      secondaryColor: '#B147FB',
      gradient: 'linear-gradient(135deg, #5B47FB 0%, #B147FB 100%)',
      examples: [
        'Stay active and monitor my workflow',
        'Suggest automation opportunities',
        'Detect repetitive tasks automatically'
      ],
      special: true
    }
  };

  // WebSocket management with improved error handling and reconnection
  function setupWebSocket() {
    if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
      return;
    }
    
    connectionStatus = 'connecting';
    wsConnectionAttempts++;
    
    try {
      ws = new WebSocket(wsEndpoint);
      
      ws.onopen = () => {
        console.log('Connected to NextGen AI backend');
        connectionStatus = 'connected';
        wsConnectionAttempts = 0;
        wsReconnectDelay = 1000; // Reset backoff on successful connection
        isTyping = false;
        
        // Add welcome message if no messages exist
        if (messages.length === 0) {
          addWelcomeMessage();
        }
        
        // Register with server
        const registerMessage = {
          type: 'register',
          client_id: userId,
          session_id: sessionId,
          client_type: 'nextgen_overlay',
          capabilities: ['text', 'json', 'suggestions', 'voice'] // Add voice capability
        };
        
        ws.send(JSON.stringify(registerMessage));
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
        ws = null;
        
        // Only attempt reconnect if chat is visible
        if (show) {
          const delay = Math.min(wsReconnectDelay * Math.pow(1.5, Math.min(wsConnectionAttempts - 1, 5)), 30000);
          console.log(`Reconnecting in ${delay}ms (attempt ${wsConnectionAttempts})`);
          
          clearTimeout(wsReconnectTimer);
          wsReconnectTimer = setTimeout(() => {
            setupWebSocket();
          }, delay);
          
          wsReconnectDelay = delay;
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        connectionStatus = 'error';
      };

    } catch (error) {
      console.error('Connection error:', error);
      connectionStatus = 'error';
      
      // Schedule reconnect attempt
      clearTimeout(wsReconnectTimer);
      wsReconnectTimer = setTimeout(() => {
        setupWebSocket();
      }, wsReconnectDelay);
    }
  }

  // Initialize WebSocket connection when component mounts and is visible
  onMount(() => {
    if (show) {
      setupWebSocket();
      setupGestureListeners();
      setupKeyboardShortcuts();
    }
    
    return () => {
      cleanupResources();
    };
  });

  // Connect to backend when visibility changes
  $: if (show && !ws) {
    setTimeout(() => {
      setupWebSocket();
    }, 50);
  }

  // Clean up resources when component is unmounted
  function cleanupResources() {
    if (ws) {
      try {
        ws.close();
      } catch (e) {
        console.error('Error closing WebSocket:', e);
      }
      ws = null;
    }
    
    cleanupGestureListeners();
    cleanupKeyboardShortcuts();
    clearTimeout(wsReconnectTimer);
    
    // Clean up audio cache
    audioCache.forEach(audio => {
      try {
        audio.pause();
        audio.src = '';
      } catch (e) {
        // Ignore audio cleanup errors
      }
    });
    audioCache.clear();
  }

  onDestroy(cleanupResources);

  // Optimized sound playback with caching
  function playSound(type) {
    if (!soundEnabled) return;
    
    try {
      // Check if we have a cached audio object
      let audio = audioCache.get(type);
      
      if (!audio) {
        // Create and cache a new audio object
        audio = new Audio(`/sounds/${type}.mp3`);
        audio.volume = 0.02; // Ultra-soft volume
        audioCache.set(type, audio);
      }
      
      // Reset and play
      audio.currentTime = 0;
      audio.play().catch(error => {
        console.log(`Sound playback error: ${error.message}`);
      });
    } catch (error) {
      console.log('Sound playback not supported');
    }
  }

  // Add welcome message with optimized animation
  function addWelcomeMessage() {
    const welcomeMessage = {
      id: Date.now(),
      type: 'assistant',
      content: `✨ **Welcome to your NextGen AI companion!** ✨

I'm not just an assistant - I'm your creative partner, problem solver, and productivity amplifier.

What would you like to explore today?
• Discover insights and explanations
• Automate tasks with intelligent execution
• Generate personalized recommendations
• Collaborate on creative projects
• Unlock new possibilities

Let's create something amazing together!`,
      timestamp: new Date(),
      mode: 'System'
    };
    
    messages = [welcomeMessage];
    scrollToBottom();
    
    // Start welcome animation sequence
    setTimeout(() => {
      playSound('startup');
    }, 300);
  }

  // Optimized message handler with improved parsing
  function handleBackendMessage(data) {
    // Handle typing indicators
    if (data.type === 'typing_start') {
      isTyping = true;
      typingMessage = data.message || 'AI is thinking...';
      return;
    }
    
    if (data.type === 'typing_end') {
      isTyping = false;
      return;
    }
    
    // Handle voice-related responses
    if (data.type === 'voice_transcription') {
      // Handle voice transcription result
      const transcribedText = data.text || '';
      input = transcribedText;
      
      // Auto-send if confident
      if (data.confidence && data.confidence > 0.8 && transcribedText.length > 3) {
        sendMessage();
      }
      
      return;
    }
    
    if (data.type === 'voice_call_status') {
      // Update voice call status
      voiceCallStatus = data.status;
      return;
    }
    
    // Handle all response types with unified processing
    if (data.type === 'response' || 
        data.type === 'chat_response' || 
        data.type === 'query_response' || 
        data.type === 'llm_response' ||
        data.type === 'final_response' ||
        data.type === 'llm_request_response') {
      
      // Hide typing indicator
      isTyping = false;
      
      // Extract response content efficiently
      let responseContent = '';
      let responseMode = currentMode;
      
      // Extract content using optimized path-based approach
      if (data.response) {
        responseContent = data.response;
        responseMode = data.mode || currentMode;
      } else if (data.message) {
        responseContent = data.message;
        responseMode = data.mode || currentMode;
      } else if (data.payload?.response) {
        responseContent = data.payload.response;
        responseMode = data.payload.mode || currentMode;
      } else if (data.result) {
        responseContent = data.result;
        responseMode = data.mode || currentMode;
      } else if (data.content) {
        responseContent = data.content;
        responseMode = data.mode || currentMode;
      } else if (typeof data === 'string') {
        // For string responses - try to parse but don't throw
        try {
          const parsed = JSON.parse(data);
          responseContent = parsed.response || parsed.message || parsed.content || data;
          responseMode = parsed.mode || currentMode;
        } catch (e) {
          responseContent = data;
        }
      } else {
        // Last resort - stringify object but limit size
        const stringified = JSON.stringify(data);
        responseContent = stringified.length > 1000 
          ? 'Received data: ' + stringified.substring(0, 1000) + '...' 
          : 'Received data: ' + stringified;
      }
      
      // Add message to chat
      const assistantMessage = {
        id: Date.now(),
        type: 'assistant',
        content: responseContent || 'No response received',
        timestamp: new Date(),
        mode: responseMode
      };
      
      messages = [...messages, assistantMessage];
      scrollToBottom();
      playSound('message-received');
      return;
    }
    
    // Handle confirmation request for agent mode
    if (data.type === 'confirmation_request') {
      pendingConfirmation = {
        id: data.request_id,
        plan: data.plan,
        task: data.task
      };
      
      // Show confirmation UI
      const confirmationMessage = {
        id: Date.now(),
        type: 'confirmation',
        content: `I'll execute the following plan for you:\n\n${data.plan.join('\n')}`,
        timestamp: new Date(),
        mode: 'Agent',
        requestId: data.request_id
      };
      
      messages = [...messages, confirmationMessage];
      scrollToBottom();
      playSound('confirmation-needed');
      return;
    }
    
    // Handle progress updates
    if (data.type === 'progress_update') {
      currentProgress = {
        progress: data.progress || 0,
        currentStep: data.current_step || '',
        stepNumber: data.step_number || 0,
        totalSteps: data.total_steps || 0
      };
      
      progressVisible = true;
      return;
    }
    
    // Handle execution completion
    if (data.type === 'execution_complete') {
      progressVisible = false;
      
      // Add completion message
      const completionMessage = {
        id: Date.now(),
        type: 'assistant',
        content: data.summary || 'Task completed successfully.',
        timestamp: new Date(),
        mode: 'Agent'
      };
      
      messages = [...messages, completionMessage];
      scrollToBottom();
      playSound('execution-complete');
      return;
    }
    
    // Handle errors
    if (data.type === 'error') {
      isTyping = false;
      
      // Add error message
      const errorMessage = {
        id: Date.now(),
        type: 'error',
        content: data.message || 'An error occurred',
        timestamp: new Date()
      };
      
      messages = [...messages, errorMessage];
      scrollToBottom();
      playSound('error');
      return;
    }
  }

  // Send message with optimized payload formatting
  function sendMessage() {
    if (!input.trim() || connectionStatus !== 'connected') return;

    // Create user message
    const userMessage = {
      id: Date.now(),
      type: 'user', 
      content: input.trim(),
      timestamp: new Date(),
      mode: currentMode
    };

    // Add to messages
    messages = [...messages, userMessage];
    
    // Clear input
    const messageToSend = input.trim();
    input = '';
    
    // Show typing indicator
    isTyping = true;
    
    // Scroll to bottom
    scrollToBottom();
    
    // Play sound
    playSound('message-sent');
    
    // Send to backend
    if (ws && ws.readyState === WebSocket.OPEN) {
      // Format message for brain router consumption
      const payload = {
        type: 'chat_request',
        message: messageToSend,
        mode: currentMode,
        session_id: sessionId,
        client_id: userId,
        timestamp: new Date().toISOString()
      };
      
      ws.send(JSON.stringify(payload));
    }
  }

  // Handle voice recording completion
  function handleVoiceRecording(recording) {
    if (!recording || !recording.blob) return;
    
    if (ws && ws.readyState === WebSocket.OPEN) {
      // Show typing indicator while processing voice
      isTyping = true;
      typingMessage = "Transcribing your voice message...";
      
      // Create and send form data with audio blob
      const formData = new FormData();
      formData.append('audio', recording.blob, 'recording.webm');
      formData.append('session_id', sessionId);
      formData.append('client_id', userId);
      
      // Send to transcription endpoint
      fetch('/api/transcribe', {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        if (data.text) {
          // Add transcribed text to input
          input = data.text;
          
          // Auto-send if confident
          if (data.confidence > 0.8) {
            sendMessage();
          }
        } else {
          throw new Error('Transcription failed');
        }
      })
      .catch(error => {
        console.error('Voice transcription error:', error);
        isTyping = false;
        
        // Add error message
        const errorMessage = {
          id: Date.now(),
          type: 'error',
          content: 'Sorry, I had trouble understanding your voice message. Please try again or type your message.',
          timestamp: new Date()
        };
        
        messages = [...messages, errorMessage];
      });
    }
  }

  // Start voice call
  function startVoiceCall() {
    showVoiceCaller = true;
    playSound('call-start');
  }

  // End voice call
  function endVoiceCall() {
    showVoiceCaller = false;
    playSound('call-end');
    
    // Send call end event to server
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'voice_call_end',
        session_id: sessionId,
        client_id: userId
      }));
    }
  }

  // Message input event handlers
  function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }

  // Efficient scroll to bottom implementation using requestAnimationFrame
  function scrollToBottom() {
    if (!chatContainer) return;
    
    // Use requestAnimationFrame for smoother scrolling
    requestAnimationFrame(() => {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    });
  }

  function selectMode(mode) {
    if (currentMode === mode) return;
    
    currentMode = mode;
    playSound('mode-switch');
    modeDropdownOpen = false;
  }

  // Handle confirmation response
  function handleConfirmation(requestId, action) {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    
    const response = {
      type: 'confirmation_response',
      request_id: requestId,
      action: action // 'confirm', 'cancel', or 'modify'
    };
    
    ws.send(JSON.stringify(response));
    
    // Clear pending confirmation
    pendingConfirmation = null;
    
    // Show appropriate feedback
    if (action === 'confirm') {
      progressVisible = true;
      currentProgress = { progress: 0, currentStep: 'Starting execution...', stepNumber: 0, totalSteps: 1 };
    }
  }

  // Optimized drag functionality with smooth transitions
  function startDrag(event) {
    if (event.target.closest('.confirmation-action, .mode-selector, button')) return;
    
    isDragging = true;
    startX = event.clientX;
    startY = event.clientY;
    initialX = position.x;
    initialY = position.y;
    
    document.addEventListener('mousemove', onDrag, { passive: true });
    document.addEventListener('mouseup', stopDrag);
    
    // Add dragging class for visual feedback
    event.currentTarget.classList.add('dragging');
  }

  function onDrag(event) {
    if (!isDragging) return;
    
    // Use requestAnimationFrame for smoother dragging
    requestAnimationFrame(() => {
      const deltaX = event.clientX - startX;
      const deltaY = event.clientY - startY;
      
      position.x = Math.max(0, Math.min(initialX + deltaX, window.innerWidth - size.width));
      position.y = Math.max(0, Math.min(initialY + deltaY, window.innerHeight - size.height));
    });
  }

  function stopDrag(event) {
    if (!isDragging) return;
    
    isDragging = false;
    document.removeEventListener('mousemove', onDrag);
    document.removeEventListener('mouseup', stopDrag);
    
    // Remove dragging class
    document.querySelector('.cloud-chat')?.classList.remove('dragging');
    
    // Notify parent of position change
    dispatchEvent('positionchange', { x: position.x, y: position.y });
  }

  // Gesture support with improved touch handling
  function setupGestureListeners() {
    document.addEventListener('touchstart', handleTouchStart, { passive: true });
    document.addEventListener('touchmove', handleTouchMove, { passive: true });
    document.addEventListener('touchend', handleTouchEnd, { passive: true });
  }
  
  function cleanupGestureListeners() {
    document.removeEventListener('touchstart', handleTouchStart);
    document.removeEventListener('touchmove', handleTouchMove);
    document.removeEventListener('touchend', handleTouchEnd);
  }

  let gestureStartY = 0;
  let gestureCurrentY = 0;

  function handleTouchStart(event) {
    if (!show) return;
    
    // Only handle touches on the chat header
    if (!event.target.closest('.cloud-header')) return;
    
    gestureStartY = event.touches[0].clientY;
    isGesturing = true;
  }

  function handleTouchMove(event) {
    if (!isGesturing || !show) return;
    
    gestureCurrentY = event.touches[0].clientY;
    const deltaY = gestureCurrentY - gestureStartY;
    
    // Pull down to minimize
    if (deltaY > 70 && !showMinimized) {
      toggleMinimize();
      isGesturing = false;
    }
    
    // Pull up to expand
    if (deltaY < -70 && showMinimized) {
      toggleMinimize();
      isGesturing = false;
    }
  }

  function handleTouchEnd() {
    isGesturing = false;
  }

  // Keyboard shortcuts
  function setupKeyboardShortcuts() {
    document.addEventListener('keydown', handleGlobalKeydown);
  }
  
  function cleanupKeyboardShortcuts() {
    document.removeEventListener('keydown', handleGlobalKeydown);
  }

  function handleGlobalKeydown(event) {
    if (!show) return;
    
    // Escape to minimize
    if (event.key === 'Escape') {
      event.preventDefault();
      toggleMinimize();
    }
    
    // Alt+M to toggle mode selector
    if (event.altKey && event.key === 'm') {
      event.preventDefault();
      showModeSelector = !showModeSelector;
    }
    
    // Alt+V to toggle voice recording
    if (event.altKey && event.key === 'v') {
      event.preventDefault();
      toggleVoiceRecorder();
    }
    
    // Alt+1-5 for mode switching
    if (event.altKey && ['1', '2', '3', '4', '5'].includes(event.key)) {
      event.preventDefault();
      const modeKeys = Object.keys(modes);
      const modeIndex = parseInt(event.key) - 1;
      if (modeKeys[modeIndex]) {
        selectMode(modeKeys[modeIndex]);
      }
    }
  }

  // UI control functions
  function toggleMinimize() {
    showMinimized = !showMinimized;
    playSound(showMinimized ? 'minimize' : 'maximize');
  }

  function closeChat() {
    // Dispatch close event to parent
    dispatchEvent('close');
  }

  function toggleModeDropdown() {
    modeDropdownOpen = !modeDropdownOpen;
    playSound('click');
  }

  function toggleScreenViewer() {
    showScreenViewer = !showScreenViewer;
    playSound('click');
  }
  
  function toggleVoiceRecorder() {
    showVoiceRecorder = !showVoiceRecorder;
    
    if (showVoiceRecorder) {
      playSound('voice-start');
    } else {
      playSound('voice-end');
    }
  }

  // Use example convenience function
  function useExample(example) {
    input = example;
    sendMessage();
  }

  // Custom event dispatcher
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();
  
  function dispatchEvent(name, detail) {
    dispatch(name, detail);
  }
</script>

{#if show}
<div 
  class="cloud-chat" 
  class:minimized={showMinimized}
  class:dragging={isDragging}
  style="left: {position.x}px; top: {position.y}px; width: {size.width}px; height: {showMinimized ? 70 : size.height}px;"
  transition:scale={{ duration: 400, easing: quintOut, delay: 50 }}
>
  <!-- Header with drag handle -->
  <div class="cloud-header" on:mousedown={startDrag}>
    <div class="header-left">
      <div class="status-indicator" class:online={connectionStatus === 'connected'} class:connecting={connectionStatus === 'connecting'} class:offline={connectionStatus === 'disconnected' || connectionStatus === 'error'}></div>
      <span class="title">NextGen<span class="title-highlight">AI</span></span>
    </div>
    
    <div class="header-controls">
      <button class="control-btn" class:active={showVoiceRecorder} on:click={toggleVoiceRecorder} aria-label="Voice message">
        {showVoiceRecorder ? '🎙️' : '🎤'}
      </button>
      <button class="control-btn" class:active={showVoiceCaller} on:click={startVoiceCall} aria-label="Voice call">
        📞
      </button>
      <button class="control-btn" class:active={showScreenViewer} on:click={toggleScreenViewer} aria-label="Screen sharing">
        {showScreenViewer ? '🖥️' : '👁️'}
      </button>
      <button class="control-btn" class:active={soundEnabled} on:click={() => soundEnabled = !soundEnabled} aria-label="Toggle sound">
        {soundEnabled ? '🔊' : '🔇'}
      </button>
      <button class="control-btn" on:click={toggleMinimize} aria-label="Minimize">
        {showMinimized ? '↗️' : '↘️'}
      </button>
      <button class="control-btn close-btn" on:click={closeChat} aria-label="Close">×</button>
    </div>
  </div>

  {#if !showMinimized}
    <!-- Mode selector -->
    {#if showModeSelector}
      <div class="mode-selector" transition:fade={{ duration: 150 }}>
        {#each Object.entries(modes) as [modeName, modeData], i}
          <button 
            class="mode-pill" 
            class:active={currentMode === modeName}
            on:click={() => selectMode(modeName)}
            style="--mode-color: {modeData.color}; --mode-gradient: {modeData.gradient};"
            aria-pressed={currentMode === modeName}
          >
            <span class="mode-emoji">{modeData.emoji}</span>
            <span class="mode-name">{modeName}</span>
          </button>
        {/each}
      </div>
    {/if}

    <!-- Messages container with efficient rendering -->
    <div class="messages-container" bind:this={chatContainer}>
      {#each messages as message (message.id)}
        <div 
          class="message {message.type}" 
          in:fly|local={{ y: 15, duration: 200 }}
        >
          <div class="message-content">
            {@html message.content.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}
            
            {#if message.type === 'confirmation'}
              <div class="confirmation-actions">
                <button class="confirmation-action confirm" on:click={() => handleConfirmation(message.requestId, 'confirm')}>
                  <span class="action-icon">✓</span>
                  <span class="action-text">Execute</span>
                </button>
                
                <button class="confirmation-action cancel" on:click={() => handleConfirmation(message.requestId, 'cancel')}>
                  <span class="action-icon">✗</span>
                  <span class="action-text">Cancel</span>
                </button>
                
                <button class="confirmation-action modify" on:click={() => handleConfirmation(message.requestId, 'modify')}>
                  <span class="action-icon">✎</span>
                  <span class="action-text">Modify</span>
                </button>
              </div>
            {/if}
          </div>
          
          <div class="message-meta">
            <span class="message-time">{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            {#if message.mode}
              <span class="message-mode" style="color: {modes[message.mode]?.color || 'var(--text-muted)'};">{message.mode}</span>
            {/if}
          </div>
        </div>
      {/each}
      
      {#if isTyping}
        <div class="typing-indicator" in:fade={{ duration: 150 }}>
          <div class="typing-dots">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
          </div>
          <span class="typing-text">{typingMessage}</span>
        </div>
      {/if}
      
      {#if progressVisible}
        <div class="progress-container" in:fade={{ duration: 200 }}>
          <div class="progress-header">
            <span class="progress-title">Executing plan</span>
            <span class="progress-percent">{currentProgress.progress}%</span>
          </div>
          
          <div class="progress-bar">
            <div 
              class="progress-fill"
              style="width: {currentProgress.progress}%"
            ></div>
          </div>
          
          <div class="progress-step">
            {#if currentProgress.stepNumber > 0}
              Step {currentProgress.stepNumber}/{currentProgress.totalSteps}:
            {/if}
            {currentProgress.currentStep}
          </div>
        </div>
      {/if}
    </div>

    <!-- Voice recorder component -->
    {#if showVoiceRecorder}
      <div class="voice-recorder-container" in:fade={{ duration: 200 }}>
        <svelte:component this={VoiceRecorder} on:recording={e => handleVoiceRecording(e.detail)} on:close={() => showVoiceRecorder = false} />
      </div>
    {/if}

    <!-- Input area with voice features -->
    <div class="input-area" class:focused={inputFocused}>
      <div class="input-container">
        <button 
          class="mode-toggle"
          on:click={toggleModeDropdown}
          class:active={modeDropdownOpen}
          style="--mode-color: {modes[currentMode]?.color}; --mode-gradient: {modes[currentMode]?.gradient};"
        >
          <span class="mode-emoji">{modes[currentMode]?.emoji}</span>
          <span class="mode-name">{currentMode}</span>
        </button>
        
        <textarea 
          class="message-input"
          bind:value={input}
          on:keydown={handleKeydown}
          on:focus={() => inputFocused = true}
          on:blur={() => inputFocused = false}
          placeholder="Message..."
          rows="1"
          disabled={connectionStatus !== 'connected'}
        ></textarea>
        
        <button 
          class="voice-button"
          on:click={toggleVoiceRecorder}
          disabled={connectionStatus !== 'connected'}
          aria-label="Voice message"
        >
          🎤
        </button>
        
        <button 
          class="send-button"
          class:active={input.trim().length > 0}
          on:click={sendMessage}
          disabled={!input.trim() || connectionStatus !== 'connected'}
          style="--mode-color: {modes[currentMode]?.color}; --mode-gradient: {modes[currentMode]?.gradient};"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M22 2L11 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      
      {#if modeDropdownOpen}
        <div class="mode-dropdown" in:fly={{ y: 5, duration: 150 }}>
          {#each Object.entries(modes) as [modeName, modeData], i}
            <button 
              class="mode-option"
              class:active={currentMode === modeName}
              on:click={() => {
                selectMode(modeName);
                toggleModeDropdown();
              }}
            >
              <span class="option-emoji">{modeData.emoji}</span>
              <div class="option-info">
                <span class="option-name">{modeName}</span>
                <span class="option-description">{modeData.description}</span>
              </div>
            </button>
          {/each}
        </div>
      {/if}
    </div>
    
    <!-- Quick example suggestions (when no messages yet) -->
    {#if messages.length === 1 && messages[0].type === 'assistant'}
      <div class="examples-container">
        <div class="examples-title">Try asking about:</div>
        <div class="examples-grid">
          {#each modes[currentMode].examples.slice(0, 3) as example, i}
            <button 
              class="example-button"
              on:click={() => useExample(example)}
              style="--mode-color: {modes[currentMode]?.color}; --mode-gradient: {modes[currentMode]?.gradient};"
            >
              {example}
            </button>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
</div>

<!-- Screen viewer overlay (lazy-loaded) -->
{#if showScreenViewer}
  <div class="screen-viewer-overlay" transition:fade={{ duration: 200 }}>
    <svelte:component this={ScreenViewer} on:close={() => showScreenViewer = false} />
  </div>
{/if}

<!-- Voice call component (lazy-loaded) -->
{#if showVoiceCaller}
  <div class="voice-call-overlay" transition:fade={{ duration: 200 }}>
    <svelte:component this={VoiceCaller} 
      sessionId={sessionId} 
      userId={userId} 
      wsEndpoint={wsEndpoint}
      on:callEnd={endVoiceCall} 
    />
  </div>
{/if}
{/if}

<style>
  /* Modern design system with optimized rendering */
  :root {
    /* Main colors */
    --bg-primary: #161B30;
    --bg-secondary: #1F2542;
    --bg-tertiary: #2A3052;
    --bg-accent: rgba(94, 231, 223, 0.15);
    
    /* Text colors */
    --text-primary: rgba(255, 255, 255, 0.95);
    --text-secondary: rgba(255, 255, 255, 0.75);
    --text-tertiary: rgba(255, 255, 255, 0.55);
    
    /* Accents */
    --accent-blue: #0A84FF;
    --accent-purple: #BF5AF2;
    --accent-teal: #5EE7DF;
    --accent-green: #30D158;
    --accent-red: #FF453A;
    --accent-orange: #FF9F0A;
    
    /* Effects */
    --glass-border: rgba(255, 255, 255, 0.08);
    --glass-highlight: rgba(255, 255, 255, 0.15);
    --glass-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    --blur-effect: 15px;
    
    /* Animation timing */
    --transition-fast: 150ms cubic-bezier(0.4, 0.0, 0.2, 1);
    --transition-normal: 250ms cubic-bezier(0.4, 0.0, 0.2, 1);
    --transition-bouncy: 400ms cubic-bezier(0.34, 1.56, 0.64, 1);
    
    /* Spacing */
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 16px;
    --space-lg: 24px;
    --space-xl: 32px;
    
    /* Misc */
    --radius-sm: 12px;
    --radius-md: 18px;
    --radius-lg: 24px;
    --radius-xl: 32px;
    --font-system: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', system-ui, sans-serif;
  }
  
  /* Optimized chat container with will-change for better performance */
  .cloud-chat {
    position: fixed;
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
    border-radius: var(--radius-xl);
    box-shadow: var(--glass-shadow);
    display: flex;
    flex-direction: column;
    z-index: 10000;
    pointer-events: auto;
    transition: var(--transition-bouncy);
    overflow: hidden;
    font-family: var(--font-system);
    letter-spacing: -0.011em;
    transform-origin: center center;
    border: 1px solid var(--glass-border);
    will-change: transform, opacity;
    
    /* Glass effect */
    backdrop-filter: blur(var(--blur-effect));
    -webkit-backdrop-filter: blur(var(--blur-effect));
  }
  
  /* Dragging state with cursor feedback */
  .cloud-chat.dragging {
    cursor: grabbing;
    transition: none;
    opacity: 0.9;
    box-shadow: 
      0 15px 35px rgba(0, 0, 0, 0.3),
      0 5px 15px rgba(0, 0, 0, 0.2);
  }
  
  /* Minimized state with smooth transition */
  .cloud-chat.minimized {
    height: 70px !important;
    transform: scale(0.98);
    opacity: 0.95;
    box-shadow: 
      0 8px 16px rgba(0, 0, 0, 0.15),
      0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  /* Header with improved grab handle feedback */
  .cloud-header {
    padding: var(--space-md);
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--glass-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: grab;
    user-select: none;
    transition: var(--transition-normal);
  }
  
  /* Header hover effect */
  .cloud-header:hover {
    background: rgba(43, 49, 78, 0.7);
  }
  
  .cloud-header:active {
    cursor: grabbing;
    background: rgba(48, 55, 85, 0.8);
  }
  
  .header-left {
    display: flex;
    align-items: center;
    gap: var(--space-sm);
  }
  
  /* Status indicator with optimized animation */
  .status-indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    position: relative;
    background-color: var(--accent-red);
  }
  
  .status-indicator.online {
    background-color: var(--accent-green);
    box-shadow: 0 0 8px var(--accent-green);
  }
  
  .status-indicator.connecting {
    background-color: var(--accent-orange);
    animation: pulse 1.5s infinite;
  }
  
  .status-indicator.offline {
    background-color: var(--accent-red);
  }
  
  @keyframes pulse {
    0% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(1.2); }
    100% { opacity: 1; transform: scale(1); }
  }
  
  .title {
    color: var(--text-primary);
    font-size: 15px;
    font-weight: 600;
    letter-spacing: -0.01em;
  }
  
  .title-highlight {
    background: linear-gradient(90deg, var(--accent-teal), var(--accent-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-fill-color: transparent;
    font-weight: 700;
  }
  
  .header-controls {
    display: flex;
    gap: 10px;
  }
  
  /* Control buttons with optimized hover states */
  .control-btn {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
    width: 30px;
    height: 30px;
    padding: 0;
    border-radius: 15px;
    cursor: pointer;
    transition: var(--transition-fast);
    font-size: 13px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .control-btn:hover {
    background: rgba(255, 255, 255, 0.12);
    transform: translateY(-2px);
  }
  
  .control-btn:active {
    transform: translateY(0) scale(0.95);
  }
  
  .control-btn.active {
    background: rgba(10, 132, 255, 0.2);
    border-color: rgba(10, 132, 255, 0.4);
    color: var(--accent-blue);
    box-shadow: 0 0 8px rgba(10, 132, 255, 0.3);
  }
  
  .control-btn.close-btn {
    font-size: 18px;
    line-height: 1;
  }
  
  .control-btn.close-btn:hover {
    background: rgba(255, 69, 58, 0.2);
    border-color: rgba(255, 69, 58, 0.4);
    color: var(--accent-red);
  }
  
  /* Mode selector with cleaner layout */
  .mode-selector {
    display: flex;
    gap: 8px;
    padding: var(--space-md) var(--space-md) var(--space-sm);
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    mask-image: linear-gradient(to right, transparent, black 10px, black 90%, transparent);
    -webkit-mask-image: linear-gradient(to right, transparent, black 10px, black 90%, transparent);
  }
  
  .mode-selector::-webkit-scrollbar {
    display: none;
  }
  
  /* Mode pill with optimized transitions */
  .mode-pill {
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: var(--radius-md);
    padding: 8px 14px;
    font-size: 13px;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    transition: var(--transition-fast);
    white-space: nowrap;
  }
  
  .mode-pill:hover {
    background: rgba(255, 255, 255, 0.12);
    transform: translateY(-2px);
  }
  
  .mode-pill.active {
    background: rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.2);
    color: var(--text-primary);
    position: relative;
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
  
  .mode-pill.active::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 20%;
    right: 20%;
    height: 2px;
    background: var(--mode-gradient);
    border-radius: 1px;
    opacity: 0.7;
  }
  
  .mode-emoji {
    font-size: 16px;
    transition: transform 0.2s ease;
  }
  
  .mode-pill:hover .mode-emoji {
    transform: scale(1.2);
  }
  
  /* Messages container with optimized scrolling */
  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: var(--space-md);
    display: flex;
    flex-direction: column;
    gap: 16px;
    scroll-behavior: smooth;
    overscroll-behavior: contain;
    position: relative;
    scrollbar-width: thin;
    scrollbar-color: rgba(255, 255, 255, 0.3) transparent;
    will-change: scroll-position;
  }
  
  .messages-container::-webkit-scrollbar {
    width: 4px;
  }
  
  .messages-container::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 2px;
  }
  
  .messages-container::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.25);
    border-radius: 2px;
  }
  
  /* Message bubbles with optimized rendering */
  .message {
    display: flex;
    flex-direction: column;
    max-width: 85%;
    will-change: transform, opacity;
  }
  
  .message.user {
    align-self: flex-end;
  }
  
  .message.assistant, .message.error, .message.confirmation {
    align-self: flex-start;
  }
  
  .message-content {
    padding: 14px 18px;
    border-radius: var(--radius-md);
    line-height: 1.5;
    font-size: 15px;
    letter-spacing: -0.01em;
    position: relative;
    transition: var(--transition-normal);
  }
  
  /* User message */
  .message.user .message-content {
    background: linear-gradient(135deg, var(--accent-blue) 0%, #5E5EE7 100%);
    color: white;
    border-radius: var(--radius-md) var(--radius-md) 4px var(--radius-md);
    box-shadow: 0 2px 8px rgba(10, 132, 255, 0.2);
  }
  
  /* Assistant message */
  .message.assistant .message-content {
    background: rgba(255, 255, 255, 0.08);
    color: var(--text-primary);
    border-radius: var(--radius-md) var(--radius-md) var(--radius-md) 4px;
    border: 1px solid rgba(255, 255, 255, 0.05);
  }
  
  /* Error message */
  .message.error .message-content {
    background: rgba(255, 69, 58, 0.15);
    color: rgba(255, 160, 160, 1);
    border: 1px solid rgba(255, 69, 58, 0.2);
    border-radius: var(--radius-md);
  }
  
  /* Confirmation message */
  .message.confirmation .message-content {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    border-radius: var(--radius-md);
    border: 1px solid rgba(255, 255, 255, 0.15);
  }
  
  .message-meta {
    font-size: 10px;
    color: var(--text-tertiary);
    margin-top: 6px;
    padding: 0 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    opacity: 0.8;
    transition: opacity 0.3s ease;
  }
  
  .message:hover .message-meta {
    opacity: 1;
  }
  
  /* Confirmation actions */
  .confirmation-actions {
    display: flex;
    gap: 8px;
    margin-top: 16px;
  }
  
  .confirmation-action {
    flex: 1;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-sm);
    padding: 8px 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    cursor: pointer;
    transition: var(--transition-fast);
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
  }
  
  .confirmation-action:hover {
    transform: translateY(-1px);
  }
  
  .confirmation-action.confirm {
    color: var(--accent-green);
  }
  
  .confirmation-action.confirm:hover {
    background: rgba(48, 209, 88, 0.1);
  }
  
  .confirmation-action.cancel {
    color: var(--accent-red);
  }
  
  .confirmation-action.cancel:hover {
    background: rgba(255, 69, 58, 0.1);
  }
  
  .confirmation-action.modify {
    color: var(--accent-orange);
  }
  
  .confirmation-action.modify:hover {
    background: rgba(255, 159, 10, 0.1);
  }
  
  /* Typing indicator */
  .typing-indicator {
    align-self: flex-start;
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: var(--radius-sm);
    padding: 10px 16px;
    max-width: 70%;
  }
  
  .typing-dots {
    display: flex;
    gap: 4px;
  }
  
  .dot {
    width: 6px;
    height: 6px;
    border-radius: 3px;
    background: rgba(255, 255, 255, 0.5);
    animation: dot-pulse 1.5s infinite ease-in-out;
  }
  
  .dot:nth-child(2) {
    animation-delay: 0.2s;
  }
  
  .dot:nth-child(3) {
    animation-delay: 0.4s;
  }
  
  @keyframes dot-pulse {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
    30% { transform: translateY(-4px); opacity: 1; }
  }
  
  .typing-text {
    font-size: 12px;
    color: var(--text-secondary);
  }
  
  /* Progress bar */
  .progress-container {
    background: rgba(40, 45, 70, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: var(--radius-sm);
    padding: 12px 16px;
    margin: 8px 0;
    align-self: stretch;
  }
  
  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }
  
  .progress-title {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
  }
  
  .progress-percent {
    font-size: 13px;
    font-weight: 600;
    color: var(--accent-blue);
  }
  
  .progress-bar {
    height: 4px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
    margin-bottom: 8px;
  }
  
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
    border-radius: 2px;
    transition: width 0.3s ease-out;
    position: relative;
    overflow: hidden;
  }
  
  .progress-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, 
      transparent 0%, 
      rgba(255, 255, 255, 0.3) 50%, 
      transparent 100%);
    animation: progress-shimmer 1.5s infinite;
  }
  
  @keyframes progress-shimmer {
    0% { transform: translateX(0); }
    100% { transform: translateX(200%); }
  }
  
  .progress-step {
    font-size: 12px;
    color: var(--text-secondary);
  }
  
  /* Voice recorder */
  .voice-recorder-container {
    margin: 0 var(--space-md) var(--space-md);
    border-radius: var(--radius-md);
    overflow: hidden;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  /* Input area */
  .input-area {
    padding: var(--space-md);
    background: var(--bg-secondary);
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    transition: var(--transition-normal);
    position: relative;
    z-index: 2;
  }
  
  .input-area.focused {
    background: rgba(35, 42, 70, 0.5);
    box-shadow: 0 -5px 15px rgba(0, 0, 0, 0.05);
  }
  
  .input-container {
    display: flex;
    gap: 10px;
    align-items: center;
  }
  
  /* Mode toggle */
  .mode-toggle {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-sm);
    padding: 6px 12px;
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    transition: var(--transition-fast);
    font-size: 12px;
    color: var(--text-secondary);
    flex-shrink: 0;
  }
  
  .mode-toggle:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .mode-toggle.active {
    background: rgba(255, 255, 255, 0.12);
    color: var(--text-primary);
  }
  
  /* Message input */
  .message-input {
    flex: 1;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius-md);
    padding: 12px 16px;
    color: var(--text-primary);
    font-size: 15px;
    font-family: var(--font-system);
    resize: none;
    height: 44px;
    max-height: 120px;
    line-height: 1.4;
    outline: none;
    transition: var(--transition-fast);
  }
  
  .message-input:focus {
    border-color: rgba(94, 231, 223, 0.2);
    background: rgba(255, 255, 255, 0.07);
    box-shadow: 0 0 0 1px rgba(94, 231, 223, 0.05);
  }
  
  .message-input::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }
  
  .message-input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  /* Voice button */
  .voice-button {
    width: 40px;
    height: 40px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.08);
    color: var(--text-primary);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: var(--transition-fast);
    flex-shrink: 0;
  }
  
  .voice-button:hover {
    background: rgba(255, 255, 255, 0.12);
    transform: translateY(-2px);
  }
  
  .voice-button:active {
    transform: translateY(0) scale(0.95);
  }
  
  .voice-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
  
  /* Send button */
  .send-button {
    width: 40px;
    height: 40px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(94, 231, 223, 0.15);
    color: rgba(255, 255, 255, 0.85);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: var(--transition-fast);
    flex-shrink: 0;
  }
  
  .send-button:hover {
    background: rgba(94, 231, 223, 0.25);
    transform: translateY(-2px);
  }
  
  .send-button.active {
    background: linear-gradient(135deg, rgba(94, 231, 223, 0.5) 0%, rgba(180, 144, 202, 0.5) 100%);
    color: white;
    box-shadow: 0 2px 8px rgba(94, 231, 223, 0.3);
  }
  
  .send-button:active {
    transform: translateY(0) scale(0.95);
  }
  
  .send-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
  
  /* Mode dropdown */
  .mode-dropdown {
    position: absolute;
    top: -220px;
    left: var(--space-md);
    background: rgba(35, 40, 65, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius-md);
    width: 280px;
    padding: 8px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(var(--blur-effect));
    z-index: 100;
  }
  
  .mode-option {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    background: transparent;
    border: none;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: var(--transition-fast);
    width: 100%;
    text-align: left;
  }
  
  .mode-option:hover {
    background: rgba(255, 255, 255, 0.08);
  }
  
  .mode-option.active {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .option-emoji {
    font-size: 16px;
    background: rgba(255, 255, 255, 0.1);
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 15px;
  }
  
  .option-info {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .option-name {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
  }
  
  .option-description {
    font-size: 11px;
    color: var(--text-secondary);
  }
  
  /* Example suggestions */
  .examples-container {
    padding: 0 var(--space-md) var(--space-md);
  }
  
  .examples-title {
    font-size: 13px;
    color: var(--text-secondary);
    margin-bottom: var(--space-sm);
  }
  
  .examples-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .example-button {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: var(--radius-sm);
    padding: 10px 16px;
    font-size: 13px;
    color: var(--text-secondary);
    cursor: pointer;
    transition: var(--transition-fast);
    text-align: left;
  }
  
  .example-button:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    transform: translateY(-1px);
  }
  
  /* Screen viewer overlay */
  .screen-viewer-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.85);
    backdrop-filter: blur(5px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10001;
  }
  
  /* Voice call overlay */
  .voice-call-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10002;
  }
  
  /* Responsive layouts */
  @media (max-width: 480px) {
    .cloud-chat {
      width: 90vw !important;
      height: 70vh !important;
      left: 5vw !important;
      top: 15vh !important;
    }
    
    .message-input {
      font-size: 14px;
    }
    
    .mode-name {
      display: none;
    }
    
    .mode-toggle {
      padding: 6px;
      width: 30px;
      justify-content: center;
    }
    
    .header-controls {
      gap: 6px;
    }
    
    .control-btn {
      width: 28px;
      height: 28px;
      font-size: 12px;
    }
  }
  
  /* Reduced motion preferences */
  @media (prefers-reduced-motion: reduce) {
    .cloud-chat, .mode-pill, .control-btn, .message-input, .send-button, 
    .mode-toggle, .confirmation-action, .example-button {
      transition: opacity 0.1s ease;
    }
    
    .dot {
      animation: none;
    }
    
    .progress-fill::after {
      animation: none;
    }
    
    .status-indicator.connecting {
      animation: none;
    }
  }
</style>