<script>
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { elasticOut, backOut } from 'svelte/easing';

  // Props
  export let active = false;          // Is this mode currently active
  export let wsEndpoint = 'ws://localhost:8765';  // WebSocket endpoint
  export let soundEnabled = true;     // Enable notification sounds
  
  // State
  let ws;
  let connected = false;
  let suggestions = [];
  let currentSuggestion = null;
  let showSuggestion = false;
  let reconnectAttempts = 0;
  let maxReconnectAttempts = 10;
  let reconnectDelay = 2000; // Start with 2 seconds
  let notificationSound;
  let suggestionSound;
  let executionSound;
  let executing = false;
  let executionProgress = 0;
  let executionTimer;
  let lastSuggestionId = null;
  let awakeMoment = false;
  
  const dispatch = createEventDispatcher();
  
  // Connect to WebSocket server
  function connect() {
    if (ws) {
      ws.close();
    }
    
    try {
      ws = new WebSocket(wsEndpoint);
      
      ws.onopen = () => {
        console.log('🔌 Epiphany mode connected');
        connected = true;
        reconnectAttempts = 0;
        reconnectDelay = 2000;
        
        // Register as an epiphany mode client
        ws.send(JSON.stringify({
          type: "register",
          client_type: "epiphany_mode",
          mode: "epiphany",
          client_id: `epiphany_${Date.now()}`
        }));
      };
      
      ws.onclose = (event) => {
        console.log('🔌 Epiphany mode disconnected', event.code, event.reason);
        connected = false;
        attemptReconnect();
      };
      
      ws.onerror = (error) => {
        console.error('🔌 Epiphany mode error', error);
        connected = false;
      };
      
      ws.onmessage = handleMessage;
    } catch (error) {
      console.error('Failed to connect to epiphany WebSocket:', error);
      attemptReconnect();
    }
  }
  
  // Handle incoming WebSocket messages
  function handleMessage(event) {
    try {
      const data = JSON.parse(event.data);
      
      // Handle different message types
      switch (data.type) {
        case 'suggestion':
          handleSuggestion(data);
          break;
          
        case 'execution_update':
          handleExecutionUpdate(data);
          break;
          
        case 'execution_complete':
          handleExecutionComplete(data);
          break;
          
        case 'ping':
          // Respond to keep connection alive
          ws.send(JSON.stringify({ type: 'pong' }));
          break;
          
        default:
          // Ignore other message types
          break;
      }
    } catch (error) {
      console.error('Error processing message:', error, event.data);
    }
  }
  
  // Handle suggestion messages
  function handleSuggestion(data) {
    // Only process if active
    if (!active) return;
    
    // Check if this is a duplicate suggestion
    if (lastSuggestionId === data.suggestion_id) {
      console.log('Duplicate suggestion received, ignoring', data.suggestion_id);
      return;
    }
    
    lastSuggestionId = data.suggestion_id;
    
    // Add confidence score styling
    const suggestion = {
      ...data,
      confidenceClass: getConfidenceClass(data.confidence),
      confidenceColor: getConfidenceColor(data.confidence),
      timestamp: new Date(),
      approved: false,
      rejected: false
    };
    
    // Add to suggestions queue
    suggestions = [...suggestions, suggestion];
    
    // If no current suggestion is displayed, show this one
    if (!currentSuggestion && active) {
      showNextSuggestion();
    }
    
    // Create an "epiphany moment" UI effect
    triggerEpiphanyMoment();
    
    // Dispatch event for parent components
    dispatch('suggestionReceived', suggestion);
  }
  
  // Handle execution updates
  function handleExecutionUpdate(data) {
    if (!currentSuggestion || currentSuggestion.suggestion_id !== data.suggestion_id) {
      return;
    }
    
    executing = true;
    executionProgress = data.progress || 0;
    
    // Update execution timer
    clearTimeout(executionTimer);
    executionTimer = setTimeout(() => {
      executing = false;
      executionProgress = 0;
    }, 10000); // Safety timeout
  }
  
  // Handle execution completion
  function handleExecutionComplete(data) {
    if (!currentSuggestion || currentSuggestion.suggestion_id !== data.suggestion_id) {
      return;
    }
    
    executing = false;
    executionProgress = 100;
    
    // Play execution complete sound
    playExecutionSound();
    
    // Clear current suggestion after a delay
    setTimeout(() => {
      hideSuggestion();
    }, 2000);
    
    // Dispatch event for parent components
    dispatch('executionComplete', {
      suggestion: currentSuggestion,
      result: data.result
    });
  }
  
  // Show the next suggestion in the queue
  function showNextSuggestion() {
    if (suggestions.length === 0 || currentSuggestion || !active) {
      return;
    }
    
    // Get the next suggestion
    currentSuggestion = suggestions[0];
    showSuggestion = true;
    
    // Play notification sound
    playNotificationSound();
    
    // Update suggestions queue
    suggestions = suggestions.slice(1);
  }
  
  // Handle user approval of suggestion
  function approveSuggestion() {
    if (!currentSuggestion) return;
    
    // Send approval message to server
    ws.send(JSON.stringify({
      type: 'suggestion_response',
      suggestion_id: currentSuggestion.suggestion_id,
      approved: true
    }));
    
    // Mark as approved
    currentSuggestion.approved = true;
    
    // Play suggestion sound
    playSuggestionSound();
    
    // Show execution in progress
    executing = true;
    executionProgress = 0;
    
    // Safety timeout for execution
    executionTimer = setTimeout(() => {
      executing = false;
      hideSuggestion();
    }, 30000); // 30 second safety timeout
    
    // Dispatch event for parent components
    dispatch('suggestionApproved', currentSuggestion);
  }
  
  // Handle user rejection of suggestion
  function rejectSuggestion() {
    if (!currentSuggestion) return;
    
    // Send rejection message to server
    ws.send(JSON.stringify({
      type: 'suggestion_response',
      suggestion_id: currentSuggestion.suggestion_id,
      approved: false
    }));
    
    // Mark as rejected and hide
    currentSuggestion.rejected = true;
    hideSuggestion();
    
    // Dispatch event for parent components
    dispatch('suggestionRejected', currentSuggestion);
  }
  
  // Hide the current suggestion
  function hideSuggestion() {
    showSuggestion = false;
    
    // Wait for transition to complete
    setTimeout(() => {
      currentSuggestion = null;
      executing = false;
      executionProgress = 0;
      clearTimeout(executionTimer);
      
      // Show next suggestion if available
      if (suggestions.length > 0 && active) {
        showNextSuggestion();
      }
    }, 300);
  }
  
  // Trigger an "epiphany moment" visual effect
  function triggerEpiphanyMoment() {
    awakeMoment = true;
    
    // Reset after animation completes
    setTimeout(() => {
      awakeMoment = false;
    }, 3000);
  }
  
  // Attempt to reconnect with exponential backoff
  function attemptReconnect() {
    if (reconnectAttempts >= maxReconnectAttempts) {
      console.log('Max reconnection attempts reached');
      return;
    }
    
    reconnectAttempts++;
    
    // Calculate delay with exponential backoff (capped at 30 seconds)
    const delay = Math.min(reconnectDelay * Math.pow(1.5, reconnectAttempts - 1), 30000);
    
    console.log(`Attempting to reconnect in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);
    
    setTimeout(() => {
      if (!connected) {
        connect();
      }
    }, delay);
  }
  
  // Play notification sound
  function playNotificationSound() {
    if (!soundEnabled) return;
    
    try {
      if (!notificationSound) {
        notificationSound = new Audio('/sounds/epiphany-notification.wav');
      }
      
      notificationSound.currentTime = 0;
      notificationSound.play().catch(error => {
        console.error('Error playing notification sound:', error);
      });
    } catch (error) {
      console.error('Error with notification sound:', error);
    }
  }
  
  // Play suggestion accepted sound
  function playSuggestionSound() {
    if (!soundEnabled) return;
    
    try {
      if (!suggestionSound) {
        suggestionSound = new Audio('/sounds/epiphany-accept.wav');
      }
      
      suggestionSound.currentTime = 0;
      suggestionSound.play().catch(error => {
        console.error('Error playing suggestion sound:', error);
      });
    } catch (error) {
      console.error('Error with suggestion sound:', error);
    }
  }
  
  // Play execution complete sound
  function playExecutionSound() {
    if (!soundEnabled) return;
    
    try {
      if (!executionSound) {
        executionSound = new Audio('/sounds/epiphany-complete.wav');
      }
      
      executionSound.currentTime = 0;
      executionSound.play().catch(error => {
        console.error('Error playing execution sound:', error);
      });
    } catch (error) {
      console.error('Error with execution sound:', error);
    }
  }
  
  // Get CSS class for confidence level
  function getConfidenceClass(confidence) {
    if (confidence >= 0.9) return 'confidence-high';
    if (confidence >= 0.7) return 'confidence-medium';
    if (confidence >= 0.5) return 'confidence-low';
    return 'confidence-very-low';
  }
  
  // Get color for confidence level
  function getConfidenceColor(confidence) {
    if (confidence >= 0.9) return '#00C853';
    if (confidence >= 0.7) return '#FFD600'; 
    if (confidence >= 0.5) return '#FF6D00';
    return '#9E9E9E';
  }
  
  // Watch for changes in active state
  $: if (active) {
    if (!connected) {
      connect();
    }
    
    // If there are pending suggestions and no current suggestion, show one
    if (suggestions.length > 0 && !currentSuggestion) {
      showNextSuggestion();
    }
  }
  
  // Lifecycle hooks
  onMount(() => {
    if (active) {
      connect();
    }
  });
  
  onDestroy(() => {
    if (ws) {
      ws.close();
    }
    
    clearTimeout(executionTimer);
  });
</script>

<div class="epiphany-mode-container" class:active>
  {#if active}
    <div class="epiphany-status-indicator" class:connected class:awakeMoment>
      <div class="epiphany-icon">✨</div>
      <div class="epiphany-status-text">
        {connected ? 'Epiphany Mode Active' : 'Connecting...'}
      </div>
    </div>
    
    <!-- Suggestion UI -->
    {#if showSuggestion && currentSuggestion}
      <div class="suggestion-container" 
           in:fly={{ y: 30, duration: 500, easing: elasticOut }} 
           out:fade={{ duration: 200 }}>
        <div class="suggestion-card {currentSuggestion.confidenceClass}">
          <div class="suggestion-header">
            <div class="suggestion-icon">💡</div>
            <div class="suggestion-title">{currentSuggestion.title}</div>
            <div class="suggestion-confidence" 
                 style="background-color: {currentSuggestion.confidenceColor}">
              {Math.round(currentSuggestion.confidence * 100)}%
            </div>
          </div>
          
          <div class="suggestion-body">
            <p>{currentSuggestion.message}</p>
          </div>
          
          {#if executing}
            <!-- Execution Progress -->
            <div class="execution-container">
              <div class="execution-status">
                {executionProgress < 100 ? 'Executing...' : 'Completed!'}
              </div>
              <div class="execution-progress-bar">
                <div class="execution-progress" style="width: {executionProgress}%"></div>
              </div>
            </div>
          {:else}
            <!-- Action Buttons -->
            <div class="suggestion-actions">
              <button class="action-button reject" on:click={rejectSuggestion}>
                Dismiss
              </button>
              <button class="action-button approve" on:click={approveSuggestion}>
                {currentSuggestion.actions?.[0]?.action_text || 'Do It'}
              </button>
            </div>
          {/if}
        </div>
      </div>
    {/if}
    
    <!-- Epiphany Moment Effect (shown when a new suggestion arrives) -->
    {#if awakeMoment}
      <div class="epiphany-moment" 
           in:fade={{ duration: 400 }} 
           out:fade={{ duration: 1000 }}>
        <div class="epiphany-rays"></div>
        <div class="epiphany-core"></div>
      </div>
    {/if}
  {/if}
</div>

<style>
  .epiphany-mode-container {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    position: relative;
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.3s ease, visibility 0.3s ease;
  }
  
  .epiphany-mode-container.active {
    opacity: 1;
    visibility: visible;
  }
  
  .epiphany-status-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: linear-gradient(135deg, rgba(91, 71, 251, 0.2), rgba(177, 71, 251, 0.2));
    border-radius: 20px;
    margin-bottom: 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
  }
  
  .epiphany-status-indicator.connected {
    background: linear-gradient(135deg, rgba(91, 71, 251, 0.4), rgba(177, 71, 251, 0.4));
    box-shadow: 0 0 20px rgba(91, 71, 251, 0.3);
  }
  
  .epiphany-status-indicator.awakeMoment {
    transform: scale(1.1);
    background: linear-gradient(135deg, rgba(91, 71, 251, 0.7), rgba(177, 71, 251, 0.7));
    box-shadow: 0 0 30px rgba(91, 71, 251, 0.5);
  }
  
  .epiphany-icon {
    font-size: 20px;
    animation: epiphany-rotate 8s linear infinite;
  }
  
  .epiphany-status-text {
    font-size: 14px;
    font-weight: 500;
    color: white;
  }
  
  .suggestion-container {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 400px;
    max-width: 90%;
    z-index: 10;
  }
  
  .suggestion-card {
    background: rgba(20, 22, 36, 0.95);
    backdrop-filter: blur(15px);
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  }
  
  .suggestion-header {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
  }
  
  .suggestion-icon {
    font-size: 24px;
    margin-right: 12px;
    animation: suggestion-pulse 2s infinite;
  }
  
  .suggestion-title {
    flex-grow: 1;
    font-weight: 600;
    font-size: 18px;
    color: white;
  }
  
  .suggestion-confidence {
    font-size: 14px;
    font-weight: 500;
    padding: 4px 8px;
    border-radius: 12px;
    color: rgba(0, 0, 0, 0.8);
  }
  
  .suggestion-body {
    color: rgba(255, 255, 255, 0.9);
    font-size: 16px;
    line-height: 1.5;
    margin-bottom: 20px;
  }
  
  .suggestion-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
  
  .action-button {
    padding: 10px 20px;
    border-radius: 8px;
    border: none;
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }
  
  .action-button:hover {
    transform: translateY(-2px);
  }
  
  .action-button.reject {
    background-color: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.8);
  }
  
  .action-button.reject:hover {
    background-color: rgba(255, 255, 255, 0.15);
  }
  
  .action-button.approve {
    background: linear-gradient(135deg, #5B47FB, #B147FB);
    color: white;
  }
  
  .action-button.approve:hover {
    box-shadow: 0 4px 12px rgba(91, 71, 251, 0.4);
  }
  
  /* Execution styles */
  .execution-container {
    margin-top: 16px;
  }
  
  .execution-status {
    font-size: 15px;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 8px;
    font-weight: 500;
    text-align: center;
  }
  
  .execution-progress-bar {
    height: 8px;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
    margin: 0 20px;
  }
  
  .execution-progress {
    height: 100%;
    background: linear-gradient(90deg, #5B47FB, #B147FB);
    border-radius: 4px;
    transition: width 0.3s ease-out;
  }
  
  /* Confidence classes */
  .confidence-high {
    border-left: 4px solid #00C853;
  }
  
  .confidence-medium {
    border-left: 4px solid #FFD600;
  }
  
  .confidence-low {
    border-left: 4px solid #FF6D00;
  }
  
  .confidence-very-low {
    border-left: 4px solid #9E9E9E;
  }
  
  /* Epiphany Moment Effect */
  .epiphany-moment {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    pointer-events: none;
    z-index: 5;
  }
  
  .epiphany-rays {
    position: absolute;
    width: 300px;
    height: 300px;
    background: radial-gradient(circle, rgba(91, 71, 251, 0) 0%, rgba(91, 71, 251, 0.1) 50%, rgba(91, 71, 251, 0) 100%);
    border-radius: 50%;
    animation: epiphany-rays 3s ease-out;
  }
  
  .epiphany-core {
    position: absolute;
    width: 100px;
    height: 100px;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.8) 0%, rgba(177, 71, 251, 0.5) 50%, rgba(91, 71, 251, 0) 100%);
    border-radius: 50%;
    animation: epiphany-core 3s ease-out;
  }
  
  /* Animations */
  @keyframes epiphany-rotate {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
  
  @keyframes suggestion-pulse {
    0% {
      opacity: 0.7;
      transform: scale(1);
    }
    50% {
      opacity: 1;
      transform: scale(1.1);
    }
    100% {
      opacity: 0.7;
      transform: scale(1);
    }
  }
  
  @keyframes epiphany-rays {
    0% {
      transform: scale(0.2);
      opacity: 0;
    }
    20% {
      opacity: 1;
    }
    100% {
      transform: scale(4);
      opacity: 0;
    }
  }
  
  @keyframes epiphany-core {
    0% {
      transform: scale(0.2);
      opacity: 0;
    }
    20% {
      opacity: 1;
    }
    100% {
      transform: scale(2);
      opacity: 0;
    }
  }
</style>