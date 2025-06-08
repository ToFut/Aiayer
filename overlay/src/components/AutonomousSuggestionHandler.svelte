<script>
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import { fade, fly } from 'svelte/transition';
  import { backOut } from 'svelte/easing';

  // Props
  export let wsEndpoint = 'ws://localhost:8765';  // WebSocket endpoint
  export let autoConnect = true;                  // Auto connect on mount
  export let soundEnabled = true;                 // Enable notification sounds
  
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
  let lastSuggestionId = null;
  
  const dispatch = createEventDispatcher();
  
  // Connect to WebSocket server
  function connect() {
    if (ws) {
      ws.close();
    }
    
    try {
      ws = new WebSocket(wsEndpoint);
      
      ws.onopen = () => {
        console.log('🔌 Autonomous suggestion system connected');
        connected = true;
        reconnectAttempts = 0;
        reconnectDelay = 2000;
        
        // Register as an autonomous suggestion client
        ws.send(JSON.stringify({
          type: "register",
          client_type: "autonomous_suggestion_handler",
          client_id: `suggestion_handler_${Date.now()}`
        }));
      };
      
      ws.onclose = (event) => {
        console.log('🔌 Autonomous suggestion system disconnected', event.code, event.reason);
        connected = false;
        attemptReconnect();
      };
      
      ws.onerror = (error) => {
        console.error('🔌 Autonomous suggestion system error', error);
        connected = false;
      };
      
      ws.onmessage = handleMessage;
    } catch (error) {
      console.error('Failed to connect to suggestion WebSocket:', error);
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
    if (!currentSuggestion) {
      showNextSuggestion();
    }
    
    // Dispatch event for parent components
    dispatch('suggestionReceived', suggestion);
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
    
    // Dispatch event for parent components
    dispatch('suggestionApproved', currentSuggestion);
    
    // Mark as approved and hide
    currentSuggestion.approved = true;
    setTimeout(() => {
      hideSuggestion();
    }, 500);
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
    
    // Dispatch event for parent components
    dispatch('suggestionRejected', currentSuggestion);
    
    // Mark as rejected and hide
    currentSuggestion.rejected = true;
    hideSuggestion();
  }
  
  // Hide the current suggestion
  function hideSuggestion() {
    showSuggestion = false;
    
    // Wait for transition to complete
    setTimeout(() => {
      currentSuggestion = null;
      
      // Show next suggestion if available
      if (suggestions.length > 0) {
        showNextSuggestion();
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
        notificationSound = new Audio('/sounds/suggestion-notification.wav');
      }
      
      notificationSound.currentTime = 0;
      notificationSound.play().catch(error => {
        console.error('Error playing notification sound:', error);
      });
    } catch (error) {
      console.error('Error with notification sound:', error);
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
  
  // Lifecycle hooks
  onMount(() => {
    if (autoConnect) {
      connect();
    }
  });
  
  onDestroy(() => {
    if (ws) {
      ws.close();
    }
  });
</script>

<!-- Suggestion UI -->
{#if showSuggestion && currentSuggestion}
  <div class="suggestion-container" 
       in:fly={{ y: 50, duration: 400, easing: backOut }} 
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
      
      <div class="suggestion-actions">
        <button class="action-button reject" on:click={rejectSuggestion}>
          No Thanks
        </button>
        <button class="action-button approve" on:click={approveSuggestion}>
          {currentSuggestion.actions?.[0]?.action_text || 'Apply Suggestion'}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .suggestion-container {
    position: absolute;
    top: 20px;
    right: 20px;
    width: 380px;
    z-index: 10000;
    filter: drop-shadow(0 4px 20px rgba(0, 0, 0, 0.3));
  }
  
  .suggestion-card {
    background: rgba(20, 22, 36, 0.95);
    backdrop-filter: blur(15px);
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 16px;
    animation: pulse 2s infinite;
  }
  
  .suggestion-header {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
  }
  
  .suggestion-icon {
    font-size: 24px;
    margin-right: 12px;
    animation: shine 2s infinite;
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
    background-color: #2979FF;
    color: white;
  }
  
  .action-button.approve:hover {
    background-color: #2962FF;
    box-shadow: 0 4px 8px rgba(41, 98, 255, 0.3);
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
  @keyframes pulse {
    0% {
      box-shadow: 0 0 0 0 rgba(41, 121, 255, 0.4);
    }
    70% {
      box-shadow: 0 0 0 8px rgba(41, 121, 255, 0);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(41, 121, 255, 0);
    }
  }
  
  @keyframes shine {
    0% {
      opacity: 0.8;
      transform: scale(1);
    }
    50% {
      opacity: 1;
      transform: scale(1.1);
    }
    100% {
      opacity: 0.8;
      transform: scale(1);
    }
  }
</style>