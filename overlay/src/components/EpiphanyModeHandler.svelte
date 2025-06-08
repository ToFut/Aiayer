<script>
  import { onMount, onDestroy } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { elasticOut } from 'svelte/easing';

  // Props
  export let wsEndpoint = 'ws://localhost:8765';  // WebSocket endpoint
  export let enabled = true;                      // Enable epiphany mode
  export let soundEnabled = true;                 // Enable notification sounds
  export let position = { x: 20, y: 20 };         // Initial position
  
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
  let pulseAnimation = false;
  let executing = false;
  let executionProgress = 0;
  let executionTimer;
  let epiphanyActive = false;
  let hasReceivedSuggestion = false;
  let lastSuggestionId = null;
  
  // Connect to WebSocket server
  function connect() {
    if (ws) {
      ws.close();
    }
    
    try {
      ws = new WebSocket(wsEndpoint);
      
      ws.onopen = () => {
        console.log('🔌 Epiphany mode system connected');
        connected = true;
        reconnectAttempts = 0;
        reconnectDelay = 2000;
        
        // Register as an epiphany mode client
        ws.send(JSON.stringify({
          type: "register",
          client_type: "epiphany_mode_handler",
          client_id: `epiphany_${Date.now()}`
        }));
      };
      
      ws.onclose = (event) => {
        console.log('🔌 Epiphany mode system disconnected', event.code, event.reason);
        connected = false;
        attemptReconnect();
      };
      
      ws.onerror = (error) => {
        console.error('🔌 Epiphany mode system error', error);
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
    // Only process if enabled
    if (!enabled) return;
    
    // Check if this is a duplicate suggestion
    if (lastSuggestionId === data.suggestion_id) {
      console.log('Duplicate suggestion received, ignoring', data.suggestion_id);
      return;
    }
    
    lastSuggestionId = data.suggestion_id;
    hasReceivedSuggestion = true;
    
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
    if (!currentSuggestion) {
      showNextSuggestion();
    }
    
    // Activate epiphany mode visual indicator
    if (!epiphanyActive) {
      epiphanyActive = true;
    }
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
  }
  
  // Show the next suggestion in the queue
  function showNextSuggestion() {
    if (suggestions.length === 0 || currentSuggestion) {
      return;
    }
    
    // Get the next suggestion
    currentSuggestion = suggestions[0];
    showSuggestion = true;
    
    // Play notification sound
    playNotificationSound();
    
    // Start pulse animation
    pulseAnimation = true;
    
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
  }
  
  // Hide the current suggestion
  function hideSuggestion() {
    showSuggestion = false;
    executing = false;
    
    // Wait for transition to complete
    setTimeout(() => {
      currentSuggestion = null;
      executionProgress = 0;
      clearTimeout(executionTimer);
      
      // Show next suggestion if available
      if (suggestions.length > 0) {
        showNextSuggestion();
      } else if (hasReceivedSuggestion) {
        // Keep epiphany indicator active if we've received suggestions before
        epiphanyActive = true;
      }
    }, 300);
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
  
  // Toggle epiphany mode
  function toggleEpiphanyMode() {
    epiphanyActive = !epiphanyActive;
  }
  
  // Lifecycle hooks
  onMount(() => {
    if (enabled) {
      connect();
    }
    
    // Auto-activate epiphany mode after a short delay
    setTimeout(() => {
      epiphanyActive = true;
    }, 3000);
  });
  
  onDestroy(() => {
    if (ws) {
      ws.close();
    }
    
    clearTimeout(executionTimer);
  });
</script>

<!-- Epiphany Mode UI -->
<div class="epiphany-container" style="top: {position.y}px; left: {position.x}px;">
  {#if epiphanyActive}
    <!-- Epiphany Mode Active Indicator -->
    <div class="epiphany-indicator {pulseAnimation ? 'pulse' : ''}" 
         on:click={toggleEpiphanyMode}
         in:fade={{ duration: 300 }}>
      <div class="epiphany-icon">✨</div>
      {#if suggestions.length > 0}
        <div class="suggestion-count">{suggestions.length}</div>
      {/if}
    </div>
  {/if}
  
  <!-- Suggestion Card -->
  {#if showSuggestion && currentSuggestion}
    <div class="suggestion-card {currentSuggestion.confidenceClass}"
         in:fly={{ y: 30, duration: 500, easing: elasticOut }} 
         out:fade={{ duration: 200 }}>
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
  {/if}
</div>

<style>
  .epiphany-container {
    position: fixed;
    z-index: 10000;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    pointer-events: none;
  }
  
  .epiphany-indicator {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #5B47FB, #B147FB);
    box-shadow: 0 2px 20px rgba(91, 71, 251, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 24px;
    cursor: pointer;
    pointer-events: auto;
    position: relative;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  .epiphany-indicator:hover {
    transform: scale(1.1);
  }
  
  .epiphany-indicator.pulse {
    animation: epiphany-pulse 2s infinite;
  }
  
  .epiphany-icon {
    animation: epiphany-rotate 8s linear infinite;
  }
  
  .suggestion-count {
    position: absolute;
    top: -5px;
    right: -5px;
    background-color: #FF3D00;
    color: white;
    font-size: 14px;
    font-weight: bold;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
  }
  
  .suggestion-card {
    width: 350px;
    background: rgba(20, 22, 36, 0.95);
    backdrop-filter: blur(15px);
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 16px;
    pointer-events: auto;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  }
  
  .suggestion-header {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
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
    font-size: 15px;
    line-height: 1.5;
    margin-bottom: 16px;
  }
  
  .suggestion-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
  }
  
  .action-button {
    padding: 8px 16px;
    border-radius: 8px;
    border: none;
    font-size: 14px;
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
    margin-top: 12px;
  }
  
  .execution-status {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
    margin-bottom: 8px;
    font-weight: 500;
  }
  
  .execution-progress-bar {
    height: 8px;
    background-color: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
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
  
  /* Animations */
  @keyframes epiphany-pulse {
    0% {
      box-shadow: 0 0 0 0 rgba(91, 71, 251, 0.7);
    }
    70% {
      box-shadow: 0 0 0 15px rgba(91, 71, 251, 0);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(91, 71, 251, 0);
    }
  }
  
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
</style>