<script>
  import { onMount, tick } from 'svelte';
  import { fade, fly, scale, blur, slide } from 'svelte/transition';
  import { cubicOut, elasticOut, expoOut } from 'svelte/easing';
  import ScreenViewer from './ScreenViewer.svelte';
  import EpiphanyMode from './EpiphanyMode.svelte';
  import EnhancedSpeechControls from './EnhancedSpeechControls.svelte';
  import NextGenPlanCard from './NextGenPlanCard.svelte';
  
  export let show = false;
  export let initialPosition = { x: 20, y: 90 };
  export let wsEndpoint = 'ws://localhost:8767'; // Direct connection to enhanced enterprise backend on port 8767
  
  let messages = [];
  let input = '';
  let ws = null;
  let loading = false;
  let chatContainer;
  let isTyping = false;
  let typingMessage = 'AI is thinking...';
  let isDragging = false;
  let showMinimized = false;
  let position = { ...initialPosition };
  let startX, startY, initialX, initialY;
  let size = { width: 420, height: 680 };
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
  let modeDropdownOpen = false;
  let showScreenViewer = false;
  
  // Voice recording and call state
  let isRecording = false;
  let recorder = null;
  let audioChunks = [];
  let isCallActive = false;
  let callTimer = null;
  let callDuration = 0;
  
  // Track message elements for speech integration
  let messageElements = [];
  
  // Agent mode confirmation state
  let pendingConfirmation = null;
  let currentProgress = { progress: 0, currentStep: '', stepNumber: 0, totalSteps: 0 };
  let progressVisible = false;
  
  // Apple-inspired mode configurations with enhanced metadata
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
        'Analyze the pros and cons of remote work',
        'How do neural networks process information?',
        'What factors influence market volatility?'
      ],
      animationDelay: 0
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
        'Automate my email organization process',
        'Design a morning routine for better focus',
        'Build a habit tracking system'
      ],
      animationDelay: 100
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
        'Recommend strategies for better time management',
        'How can I optimize my workspace for productivity?',
        'What skills should I develop next?'
      ],
      animationDelay: 200
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
        'Create innovative solutions for team collaboration',
        'Generate creative content ideas for my blog',
        'Think of original ways to solve this problem'
      ],
      animationDelay: 300
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
        'Detect repetitive tasks automatically',
        'Proactively identify optimization chances',
        'Provide timely contextual assistance'
      ],
      animationDelay: 400,
      special: true // Special mode with different behavior
    }
  };

  // Apple-inspired sound effects (if enabled) - Ultra-gentle volumes
  const playSound = (type) => {
    if (!soundEnabled) return;
    try {
      const audio = new Audio(`/sounds/${type}.mp3`);
      audio.volume = 0.02; // Ultra-soft volume for all sounds
      audio.currentTime = 0; // Reset to beginning for rapid clicks
      audio.play().catch(() => {
        // Fallback: try .wav format if .mp3 fails
        try {
          const fallbackAudio = new Audio(`/sounds/${type}.wav`);
          fallbackAudio.volume = 0.02; // Ultra-soft volume for fallback too
          fallbackAudio.play().catch(() => {});
        } catch (fallbackError) {
          console.log(`Sound file not found: ${type}`);
        }
      });
    } catch (error) {
      console.log('Sound playback not supported');
    }
  };

  // Real backend connection management
  onMount(() => {
    if (show) {
      connectToBackend();
      setupGestureListeners();
      setupKeyboardShortcuts();
      
      // Add welcome message if no messages exist
      if (messages.length === 0) {
        addWelcomeMessage();
      }
    }
    
    return () => {
      if (ws) ws.close();
      cleanupGestureListeners();
      cleanupKeyboardShortcuts();
    };
  });

  // Connect to backend when visible
  $: if (show && !ws) {
    setTimeout(() => {
      connectToBackend();
    }, 100);
  }

  // Connection management
  function connectToBackend() {
    if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
      return;
    }

    connectionStatus = 'connecting';
    
    try {
      ws = new WebSocket(wsEndpoint);
      
      ws.onopen = () => {
        console.log('Connected to NextGen SensAI backend');
        connectionStatus = 'connected';
        
        // Clear typing message if present
        isTyping = false;
        
        // Add welcome message if no messages exist
        if (messages.length === 0) {
          addWelcomeMessage();
        }
        
        // Register with server silently
        const registerMessage = {
          type: 'register',
          client_id: userId,
          session_id: sessionId,
          client_type: 'nextgen_overlay',
          capabilities: ['text', 'json', 'suggestions']
        };
        
        ws.send(JSON.stringify(registerMessage));
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Generate a unique fingerprint for this message to detect duplicates
          const messageFingerprint = generateMessageFingerprint(data);
          
          // Skip processing if we've already seen this exact message
          if (receivedMessageIds.has(messageFingerprint)) {
            console.log('Skipping duplicate message:', messageFingerprint);
            return;
          }
          
          // Remember we've seen this message
          receivedMessageIds.add(messageFingerprint);
          
          // Process the message
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
          setTimeout(() => {
            connectToBackend();
          }, 2000);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        connectionStatus = 'error';
      };

    } catch (error) {
      console.error('Connection error:', error);
      connectionStatus = 'error';
    }
  }

  function addWelcomeMessage() {
    const welcomeMessage = {
      id: Date.now(),
      type: 'assistant',
      content: `🌟 Welcome to Enterprise SensAI!

Choose your mode:

🔍 Ask - Precise answers with context
🤖 Agent - Task automation & execution
✨ Suggest - Smart recommendations
🎨 Creative - Innovative solutions

Tap a mode to begin!`,
      timestamp: new Date(),
      confidence: 1.0,
      mode: 'System',
      isWelcome: true
    };
    
    messages = [welcomeMessage];
  }

  function setMode(mode) {
    currentMode = mode;
    if (soundEnabled) {
      playSound('click');
    }
    // Add a system message to confirm mode change
    messages = [...messages, {
      id: Date.now(),
      type: 'system',
      content: `Switched to ${mode} mode`,
      timestamp: new Date(),
      confidence: 1.0,
      mode: 'System'
    }];
  }

  function handleBackendMessage(data) {
    // Handle different message types
    console.log('Processing message:', data);
    
    // Handle processing started
    if (data.type === 'processing_started') {
      console.log('🚀 Processing started:', data);
      
      // Show thinking indicator
      isTyping = true;
      typingMessage = '🤖 Processing your request...';
      return;
    }
    
    if (data.type === 'typing_start') {
      isTyping = true;
      typingMessage = data.message || 'AI is thinking...';
      return;
    }
    
    if (data.type === 'typing_end') {
      isTyping = false;
      return;
    }

    // Handle plan generation progress
    if (data.type === 'plan_generation_progress') {
      console.log('🔄 Plan generation progress:', data);
      
      // Show thinking indicator with progress
      isTyping = true;
      typingMessage = data.payload?.progress || '🤖 Generating automation plan...';
      return;
    }

    // Handle plan generation start
    if (data.type === 'plan_generation_started') {
      console.log('🚀 Plan generation started:', data);
      
      // Show thinking indicator
      isTyping = true;
      typingMessage = '🤖 Starting plan generation...';
      return;
    }

    // Handle plan generation completion
    if (data.type === 'plan_generation_completed') {
      console.log('✅ Plan generation completed:', data);
      
      // Hide typing indicator
      isTyping = false;
      return;
    }

    // Handle response generation start
    if (data.type === 'response_generation_started') {
      console.log('🚀 Response generation started:', data);
      
      // Show thinking indicator
      isTyping = true;
      typingMessage = '🤖 Generating response...';
      return;
    }

    // Handle response generation completion
    if (data.type === 'response_generated') {
      console.log('✅ Response generated:', data);
      
      // Hide typing indicator
      isTyping = false;
      
      // Extract response content
      let responseContent = '';
      if (data.payload && typeof data.payload === 'object') {
        if (data.payload.response) {
          responseContent = data.payload.response;
        } else if (data.payload.message) {
          responseContent = data.payload.message;
        } else {
          responseContent = JSON.stringify(data.payload);
        }
      } else if (data.payload) {
        responseContent = data.payload;
      }
      
      // Add response message
      const responseMessage = {
        id: Date.now(),
        type: 'assistant',
        content: responseContent || 'No response received',
        timestamp: new Date(),
        mode: currentMode,
        streaming: false
      };
      
      messages = [...messages, responseMessage];
      scrollToBottom();
      playSound('message-received');
      return;
    }

    // Handle suggestion generation start
    if (data.type === 'suggestion_generation_started') {
      console.log('🚀 Suggestion generation started:', data);
      
      // Show thinking indicator
      isTyping = true;
      typingMessage = '🤖 Generating suggestions...';
      return;
    }

    // Handle suggestion generation completion
    if (data.type === 'suggestion_generated') {
      console.log('✅ Suggestion generated:', data);
      
      // Hide typing indicator
      isTyping = false;
      
      // Extract suggestion content
      let suggestionContent = '';
      if (data.payload && typeof data.payload === 'object') {
        if (data.payload.response) {
          suggestionContent = data.payload.response;
        } else if (data.payload.message) {
          suggestionContent = data.payload.message;
        } else {
          suggestionContent = JSON.stringify(data.payload);
        }
      } else if (data.payload) {
        suggestionContent = data.payload;
      }
      
      // Add suggestion message
      const suggestionMessage = {
        id: Date.now(),
        type: 'assistant',
        content: suggestionContent || 'No suggestions received',
        timestamp: new Date(),
        mode: 'Suggest',
        streaming: false
      };
      
      messages = [...messages, suggestionMessage];
      scrollToBottom();
      playSound('message-received');
      return;
    }

    // Handle plan generation response
    if (data.type === 'plan_generated') {
      console.log('📋 Plan generated received:', data);
      
      // Hide typing indicator
      isTyping = false;
      
      // Extract plan information
      const planId = data.payload?.plan?.plan_id || 'unknown';
      const plan = data.payload?.plan || {};
      const steps = plan.steps || [];
      
      // Create a special plan message with enhanced visualization
      const planMessage = {
        id: Date.now(),
        type: 'assistant',
        content: '🤖 **Automation Plan Generated**\n\nReady to execute your automation plan with detailed step-by-step visualization.',
        timestamp: new Date(),
        mode: 'Agent',
        planId: planId,
        plan: plan,
        requiresConfirmation: true,
        interactive: true,
        isPlanCard: true // Special flag for enhanced plan display
      };
      
      messages = [...messages, planMessage];
      scrollToBottom();
      playSound('message-received');
      return;
    }

    // --- STREAMING RESPONSE HANDLING ---
    if (data.type === 'partial_response') {
      // Extract response content from possible BrainResponse
      let streamContent = '';
      
      // Handle BrainResponse object
      if (data.response && typeof data.response === 'object' && data.response.response !== undefined) {
        streamContent = data.response.response;
      }
      // Handle BrainResponse as string
      else if (data.response && typeof data.response === 'string' && data.response.includes('BrainResponse(')) {
        const responseMatch = data.response.match(/response='([^']*)'/);
        if (responseMatch) {
          streamContent = responseMatch[1];
        } else {
          const doubleQuoteMatch = data.response.match(/response="([^"]*)"/);
          if (doubleQuoteMatch) {
            streamContent = doubleQuoteMatch[1];
          } else {
            streamContent = data.response;
          }
        }
      }
      // Direct response
      else {
        streamContent = data.response || '';
      }
      
      // Check for potential duplicate with existing messages first
      if (messages.length > 0) {
        for (let i = messages.length - 1; i >= Math.max(0, messages.length - 3); i--) {
          if (messages[i].type === 'assistant' && 
              !messages[i].streaming && // Don't compare with other streaming messages
              similarityScore(messages[i].content, streamContent) > 0.85) {
            console.log('Skipping duplicate streaming message');
            return;
          }
        }
      }
      
      // If last message is assistant and streaming, update it
      if (messages.length > 0 && messages[messages.length - 1].type === 'assistant' && messages[messages.length - 1].streaming) {
        messages[messages.length - 1].content = streamContent;
        messages = [...messages]; // Trigger reactivity
      } else {
        // Otherwise, add a new assistant message in streaming mode
        messages = [...messages, {
          id: Date.now(),
          type: 'assistant',
          content: streamContent,
          timestamp: new Date(),
          mode: data.mode || currentMode,
          streaming: true
        }];
      }
      scrollToBottom();
      return;
    }
    if (data.type === 'final_response') {
      const responseContent = data.response || '';
      
      // If last message is assistant and streaming, finalize it
      if (messages.length > 0 && messages[messages.length - 1].type === 'assistant' && messages[messages.length - 1].streaming) {
        messages[messages.length - 1].content = responseContent;
        messages[messages.length - 1].streaming = false;
        messages = [...messages]; // Trigger reactivity
      } else {
        // Check for potential duplicate with existing messages first
        let isDuplicate = false;
        for (let i = messages.length - 1; i >= Math.max(0, messages.length - 3); i--) {
          if (messages[i].type === 'assistant' && 
              similarityScore(messages[i].content, responseContent) > 0.85) {
            console.log('Skipping duplicate final response');
            isDuplicate = true;
            break;
          }
        }
        
        if (!isDuplicate) {
          // Add as a new assistant message
          messages = [...messages, {
            id: Date.now(),
            type: 'assistant',
            content: responseContent || 'No response received',
            timestamp: new Date(),
            mode: data.mode || currentMode,
            streaming: false
          }];
        }
      }
      scrollToBottom();
      playSound('message-received');
      return;
    }
    // --- END STREAMING RESPONSE HANDLING ---
    
    // COMPREHENSIVE RESPONSE HANDLING - Handle all possible backend response formats
    if (data.type === 'response' || 
        data.type === 'chat_response' || 
        data.type === 'query_response' || 
        data.type === 'llm_response' ||
        data.type === 'final_response' ||
        data.type === 'llm_request_response') {
      
      // Hide typing indicator
      isTyping = false;
      
      // Extract response content from multiple possible formats
      let responseContent = '';
      let responseMode = currentMode;
      
      // Handle BrainResponse object
      if (data.response && typeof data.response === 'object') {
        // If it's a BrainResponse object, extract the actual response content
        if (data.response.response !== undefined) {
          // Extract the actual response from the BrainResponse object
          responseContent = data.response.response;
        } else {
          // Fallback to JSON stringifying if no direct response field
          responseContent = JSON.stringify(data.response);
        }
        // Get the mode that was used
        responseMode = data.response.mode_used || currentMode;
      }
      // Handle BrainResponse as string representation
      else if (data.response && typeof data.response === 'string' && data.response.includes('BrainResponse(')) {
        // Extract the response field from the BrainResponse string
        const responseMatch = data.response.match(/response='([^']*)'/);
        if (responseMatch) {
          responseContent = responseMatch[1];
        } else {
          // Try another regex pattern for double-quoted strings
          const doubleQuoteMatch = data.response.match(/response="([^"]*)"/);
          if (doubleQuoteMatch) {
            responseContent = doubleQuoteMatch[1];
          } else {
            responseContent = data.response;
          }
        }
        
        // Try to extract mode_used from string if available
        const modeMatch = data.response.match(/mode_used='([^']*)'/);
        if (modeMatch) {
          responseMode = modeMatch[1];
        }
      }
      // Handle direct object response
      else if (data.success !== undefined && data.response !== undefined) {
        responseContent = data.response;
        responseMode = data.mode_used || data.mode || currentMode;
      }
      // If not a BrainResponse or parsing failed, try other formats
      else if (data.response) {
        // Check if response might be a string representation of an object
        if (typeof data.response === 'string' && (data.response.startsWith('{') || data.response.startsWith('['))) {
          try {
            // Try to parse it as JSON
            const parsedResponse = JSON.parse(data.response);
            // If successful and contains a response field, use that
            if (parsedResponse.response) {
              responseContent = parsedResponse.response;
              responseMode = parsedResponse.mode_used || parsedResponse.mode || currentMode;
            } else {
              // Otherwise use the original string
              responseContent = data.response;
            }
          } catch (e) {
            // If parsing fails, use the original string
            responseContent = data.response;
          }
        } else {
          // Use the response directly
          responseContent = data.response;
        }
        responseMode = data.mode || currentMode;
      } else if (data.message) {
        responseContent = data.message;
        responseMode = data.mode || currentMode;
      } else if (data.payload?.response) {
        // Check if payload.response might be a BrainResponse
        if (typeof data.payload.response === 'object' && data.payload.response.response) {
          responseContent = data.payload.response.response;
          responseMode = data.payload.response.mode_used || data.payload.mode || currentMode;
        } else {
          responseContent = data.payload.response;
          responseMode = data.payload.mode || currentMode;
        }
      } else if (data.result) {
        responseContent = data.result;
        responseMode = data.mode || currentMode;
      } else if (data.content) {
        responseContent = data.content;
        responseMode = data.mode || currentMode;
      } else if (typeof data === 'string') {
        // For string responses
        try {
          const parsed = JSON.parse(data);
          responseContent = parsed.response || parsed.message || parsed.content || data;
          responseMode = parsed.mode || currentMode;
        } catch (e) {
          responseContent = data;
        }
      } else {
        // Last resort - stringify the entire object
        responseContent = 'Received data: ' + JSON.stringify(data);
      }
      
      // Add message to chat
      // Check for potential duplicate with last message
      const isDuplicate = messages.length > 0 && 
                          messages[messages.length - 1].type === 'assistant' &&
                          similarityScore(
                            messages[messages.length - 1].content || '',
                            responseContent || ''
                          ) > 0.85; // High threshold for exact duplicates
      
      if (isDuplicate) {
        console.log('Skipping duplicate assistant message');
        return;
      }
      
      // Check for any similar automation plan in last 5 messages
      if (contentContainsAutomationPlan(responseContent)) {
        const recentMessages = messages.slice(-5);
        for (const msg of recentMessages) {
          if (msg.type === 'assistant' && contentContainsAutomationPlan(msg.content)) {
            const similarity = similarityScore(msg.content, responseContent);
            if (similarity > 0.7) { // Similar enough to be the same plan
              console.log('Skipping similar automation plan message:', similarity);
              return;
            }
          }
        }
      }
      
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
    
    if (data.type === 'confirmation_request') {
      // Handle confirmation request for agent mode
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
    
    if (data.type === 'progress_update') {
      // Update progress UI
      currentProgress = {
        progress: data.progress || 0,
        currentStep: data.current_step || '',
        stepNumber: data.step_number || 0,
        totalSteps: data.total_steps || 0
      };
      
      progressVisible = true;
      return;
    }
    
    if (data.type === 'execution_complete') {
      // Hide progress UI
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
    
    if (data.type === 'error') {
      // Hide typing indicator
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
      // BRAIN ROUTER COMPATIBLE FORMAT
      // Format message for direct brain router consumption
      const payload = {
        type: 'chat_request',
        message: messageToSend,
        mode: currentMode.toLowerCase(),
        session_id: sessionId,
        client_id: userId,
        timestamp: new Date().toISOString()
      };
      
      console.log('Sending to brain router:', payload);
      ws.send(JSON.stringify(payload));
    }
  }

  function handleKeydown(event) {
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

  function selectMode(mode) {
    if (currentMode === mode) return;
    
    currentMode = mode;
    playSound('mode-switch');
    console.log(`Switched to ${mode} mode`);
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

  // Plan execution functions
  function executePlan(planId) {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected for plan execution');
      return;
    }

    console.log('🚀 Executing plan:', planId);
    
    const executeMessage = {
      type: 'execute_plan',
      plan_id: planId,
      client_id: userId,
      timestamp: new Date().toISOString()
    };

    ws.send(JSON.stringify(executeMessage));
    showTypingIndicator('🚀 Executing automation plan...');
  }

  function cancelPlan(planId) {
    console.log('❌ Cancelling plan:', planId);
    // Remove the plan message from chat
    messages = messages.filter(msg => msg.planId !== planId);
  }

  function modifyPlan(planId) {
    console.log('✎ Modifying plan:', planId);
    // For now, just show a message that modification is not implemented
    messages = [...messages, {
      id: Date.now(),
      type: 'assistant',
      content: 'Plan modification is not yet implemented. Please try again with a different prompt.',
      timestamp: new Date(),
      mode: 'Agent'
    }];
    scrollToBottom();
  }

  // Dragging functionality
  function startDrag(event) {
    if (event.target.closest('.confirmation-action, .mode-selector, button')) return;
    
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
    if (!isDragging) return;
    
    isDragging = false;
    document.removeEventListener('mousemove', onDrag);
    document.removeEventListener('mouseup', stopDrag);
    
    // Notify parent of position change
    dispatch('positionchange', { x: position.x, y: position.y });
  }

  // Gesture support
  function setupGestureListeners() {
    document.addEventListener('touchstart', handleTouchStart, { passive: false });
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleTouchEnd, { passive: false });
  }
  
  function cleanupGestureListeners() {
    document.removeEventListener('touchstart', handleTouchStart);
    document.removeEventListener('touchmove', handleTouchMove);
    document.removeEventListener('touchend', handleTouchEnd);
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

  // Example convenience function
  function useExample(example) {
    input = example;
    sendMessage();
  }

  function toggleMinimize() {
    showMinimized = !showMinimized;
    playSound(showMinimized ? 'minimize' : 'maximize');
  }

  function closeChat() {
    // Dispatch close event to parent
    dispatch('close');
  }

  function toggleModeDropdown() {
    modeDropdownOpen = !modeDropdownOpen;
    playSound('click');
  }

  function toggleScreenViewer() {
    showScreenViewer = !showScreenViewer;
    playSound('click');
  }
  
  // Voice recording functionality
  async function toggleVoiceRecording() {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }
  
  async function startRecording() {
    try {
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Create media recorder
      recorder = new MediaRecorder(stream);
      audioChunks = [];
      
      // Set up event listeners
      recorder.ondataavailable = (e) => {
        audioChunks.push(e.data);
      };
      
      recorder.onstop = async () => {
        // Create audio blob
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        
        // Create a temporary URL for the audio
        const audioUrl = URL.createObjectURL(audioBlob);
        
        // Play sound effect
        playSound('message-sent');
        
        // Create a message for the recording
        const recordingMessage = {
          id: Date.now(),
          type: 'user',
          content: `🎤 Voice message sent`,
          timestamp: new Date(),
          mode: currentMode,
          audioUrl: audioUrl
        };
        
        // Add to messages
        messages = [...messages, recordingMessage];
        
        // Scroll to bottom
        scrollToBottom();
        
        // Here you would normally send the audio data to the server
        // For demonstration purposes, we'll add a response after a short delay
        isTyping = true;
        
        setTimeout(() => {
          const assistantMessage = {
            id: Date.now(),
            type: 'assistant',
            content: `I've received your voice message. Let me transcribe and respond to it.`,
            timestamp: new Date(),
            mode: currentMode
          };
          
          messages = [...messages, assistantMessage];
          isTyping = false;
          scrollToBottom();
          playSound('message-received');
        }, 2000);
        
        // Stop the tracks to release the microphone
        stream.getTracks().forEach(track => track.stop());
      };
      
      // Start recording
      recorder.start();
      isRecording = true;
      
      // Play sound effect
      playSound('click');
      
      // Add a subtle visual indication
      const recordingIndicator = {
        id: Date.now(),
        type: 'system',
        content: `🎤 Recording voice message... (tap microphone icon again to stop)`,
        timestamp: new Date()
      };
      
      messages = [...messages, recordingIndicator];
      scrollToBottom();
      
    } catch (error) {
      console.error('Error starting recording:', error);
      
      // Show error message
      const errorMessage = {
        id: Date.now(),
        type: 'error',
        content: `Microphone access was denied or an error occurred. Please check your permissions.`,
        timestamp: new Date()
      };
      
      messages = [...messages, errorMessage];
      scrollToBottom();
      playSound('error');
    }
  }
  
  function stopRecording() {
    if (recorder && isRecording) {
      recorder.stop();
      isRecording = false;
      
      // Remove the recording indicator message
      messages = messages.filter(msg => msg.type !== 'system' || !msg.content.includes('Recording voice message'));
    }
  }
  
  // Phone call functionality
  function initiateCall() {
    if (isCallActive) {
      endCall();
    } else {
      startCall();
    }
  }
  
  function startCall() {
    // Play sound effect
    playSound('click');
    
    // Show call initiating message
    const callMessage = {
      id: Date.now(),
      type: 'system',
      content: `📞 Initiating call with AI assistant...`,
      timestamp: new Date()
    };
    
    messages = [...messages, callMessage];
    scrollToBottom();
    
    // Simulate call connection
    setTimeout(() => {
      isCallActive = true;
      callDuration = 0;
      
      // Start call timer
      callTimer = setInterval(() => {
        callDuration += 1;
        
        // Update last message with duration
        const lastMessageIndex = messages.length - 1;
        if (messages[lastMessageIndex].type === 'system' && messages[lastMessageIndex].content.includes('call')) {
          const minutes = Math.floor(callDuration / 60);
          const seconds = callDuration % 60;
          
          messages[lastMessageIndex] = {
            ...messages[lastMessageIndex],
            content: `📞 Call in progress: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
          };
          
          messages = [...messages]; // Trigger reactivity
        }
      }, 1000);
      
      // After a short delay, show AI response
      setTimeout(() => {
        const assistantMessage = {
          id: Date.now(),
          type: 'assistant',
          content: `Hello! I'm your AI assistant. How can I help you on this call?`,
          timestamp: new Date(),
          mode: currentMode,
          isCallMessage: true
        };
        
        messages = [...messages, assistantMessage];
        scrollToBottom();
        playSound('message-received');
      }, 1500);
    }, 2000);
  }
  
  function endCall() {
    if (callTimer) {
      clearInterval(callTimer);
      callTimer = null;
    }
    
    isCallActive = false;
    
    // Show call ended message
    const minutes = Math.floor(callDuration / 60);
    const seconds = callDuration % 60;
    
    const callEndedMessage = {
      id: Date.now(),
      type: 'system',
      content: `📞 Call ended. Duration: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`,
      timestamp: new Date()
    };
    
    // Find and replace the current call message
    const updatedMessages = messages.filter(msg => !(msg.type === 'system' && msg.content.includes('Call in progress')));
    messages = [...updatedMessages, callEndedMessage];
    
    scrollToBottom();
    playSound('click');
  }
  
  // Clean up on component unmount
  onMount(() => {
    // ... existing code ...
    
    return () => {
      // ... existing code ...
      
      // Clean up call timer
      if (callTimer) {
        clearInterval(callTimer);
      }
      
      // Stop recording if active
      if (isRecording && recorder) {
        recorder.stop();
      }
    };
  });

  // Create event dispatcher
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();
  
  // Enhanced message formatting function
  // Track processed messages to avoid duplicates
  const processedMessages = new Set();
  const formattedHtmlCache = new Map();
  const receivedMessageIds = new Set(); // For tracking duplicate incoming messages
  let lastAutomationPlan = null;
  
  function formatMessageContent(content) {
    if (!content) return '';
    
    // If we've already formatted this exact content, return the cached formatted HTML
    if (formattedHtmlCache.has(content)) {
      return formattedHtmlCache.get(content);
    }
    
    // Create a unique hash for the content for deduplication
    // Strip out timestamps, IDs, and other variable elements
    const normalizedContent = content
      .replace(/plan_\d+/g, 'plan_ID')
      .replace(/\d{10,}/g, 'TIMESTAMP')
      .replace(/\n+/g, '\n')
      .trim();
    
    const contentFingerprint = normalizedContent.substring(0, 100);
    
    // If the message contains elements of an automation plan, do special deduplication
    if (contentContainsAutomationPlan(content)) {
      // If we already have a similar automation plan processed recently
      if (lastAutomationPlan && similarityScore(lastAutomationPlan, normalizedContent) > 0.7) {
        console.log('Skipping duplicate automation plan');
        return content; // Just return unformatted to avoid duplicates
      }
      
      // Remember this automation plan for future deduplication
      lastAutomationPlan = normalizedContent;
    }
    
    // If we've already processed a very similar message, return it without formatting
    if (processedMessages.has(contentFingerprint)) {
      return content;
    }
    
    // Add this message to our processed set for deduplication
    processedMessages.add(contentFingerprint);
    
    let formattedHtml = content;
    
    // Check if this is a well-formatted automation plan with the specific format we expect
    if (content.includes('**AUTOMATION EXECUTION PLAN**') || 
        content.includes('🎯 **AUTOMATION EXECUTION PLAN**')) {
      formattedHtml = formatAutomationPlan(content);
    }
    // Check if this is an agent mode response that needs formatting
    // With tighter conditions to avoid false positives
    else if ((content.includes('🎯 AUTOMATION EXECUTION PLAN') ||
         content.includes('Automation Plan for') ||
         content.includes('Automation Steps:')) ||
        (content.match(/I['']ll|I will|Here['']s what|Here['']s the plan/) && 
         content.match(/\d+\.\s+/) && 
         content.split('\n').filter(line => /^\d+\./.test(line.trim())).length >= 2)) {
      // If this contains markers of a less-structured plan, send it through the enhanced formatter
      formattedHtml = formatAgentModeResponse(content);
    }
    // Process regular text content
    else {
      formattedHtml = processRegularContentFormatting(content);
    }
    
    // Cache the formatted HTML for future use
    formattedHtmlCache.set(content, formattedHtml);
    
    return formattedHtml;
  }
  
  // Helper function to check if content contains automation plan elements
  function contentContainsAutomationPlan(content) {
    return content.includes('AUTOMATION EXECUTION PLAN') ||
           content.includes('Automation Plan') ||
           content.includes('Automation Steps:') ||
           (content.match(/I['']ll|I will|Here['']s what|Here['']s the plan/) && 
            content.match(/\d+\.\s+/) && 
            content.split('\n').filter(line => /^\d+\./.test(line.trim())).length >= 2);
  }
  
  // Calculates similarity between two strings (0-1)
  function similarityScore(str1, str2) {
    // Simple word overlap similarity calculation
    const words1 = new Set(str1.split(/\s+/).filter(w => w.length > 3));
    const words2 = new Set(str2.split(/\s+/).filter(w => w.length > 3));
    
    if (words1.size === 0 || words2.size === 0) return 0;
    
    let intersection = 0;
    for (const word of words1) {
      if (words2.has(word)) intersection++;
    }
    
    return intersection / Math.max(words1.size, words2.size);
  }
  
  // Generate a unique fingerprint for a message to detect duplicates
  function generateMessageFingerprint(data) {
    try {
      // Extract relevant fields based on message type
      let fingerprintData = {};
      
      // Extract type
      fingerprintData.type = data.type;
      
      // Extract content based on message type
      if (data.type === 'response' || data.type === 'chat_response' || 
          data.type === 'query_response' || data.type === 'llm_response' ||
          data.type === 'final_response' || data.type === 'llm_request_response') {
        
        // Extract content from various response formats
        if (data.response) {
          if (typeof data.response === 'object' && data.response.response) {
            // It's a BrainResponse object
            fingerprintData.content = data.response.response;
          } else if (typeof data.response === 'string') {
            if (data.response.includes('BrainResponse(')) {
              // It's a string representation of BrainResponse
              const match = data.response.match(/response=['"]([^'"]*)['"]/);
              fingerprintData.content = match ? match[1] : data.response;
            } else {
              // It's a direct string
              fingerprintData.content = data.response;
            }
          } else {
            // Something else
            fingerprintData.content = JSON.stringify(data.response);
          }
        } else if (data.message) {
          fingerprintData.content = data.message;
        } else if (data.payload?.response) {
          fingerprintData.content = typeof data.payload.response === 'object' ? 
            JSON.stringify(data.payload.response) : data.payload.response;
        }
      } else if (data.type === 'confirmation_request') {
        fingerprintData.request_id = data.request_id;
        fingerprintData.plan = JSON.stringify(data.plan);
      } else if (data.type === 'progress_update') {
        fingerprintData.progress = data.progress;
        fingerprintData.step = data.current_step;
      } else if (data.type === 'execution_complete') {
        fingerprintData.summary = data.summary;
      } else {
        // For other message types, use the whole data
        fingerprintData = { ...data };
      }
      
      // Clean up the content for fingerprinting
      if (fingerprintData.content) {
        fingerprintData.content = fingerprintData.content
          .replace(/plan_\d+/g, 'plan_ID')
          .replace(/\d{10,}/g, 'TIMESTAMP')
          .substring(0, 200); // Limit length for fingerprint
      }
      
      // Convert to a string for storage in the Set
      return JSON.stringify(fingerprintData);
    } catch (e) {
      // If anything goes wrong, fall back to a simple timestamp-based approach
      console.error('Error generating message fingerprint:', e);
      return Date.now().toString();
    }
  }
  
  // Process and format regular text content (non-automation plans)
  function processRegularContentFormatting(content) {
    // Protect code blocks first - we'll handle them differently
    const codeBlocks = [];
    let processedContent = content.replace(/```([\s\S]*?)```/g, (match, code) => {
      const id = `CODE_BLOCK_${codeBlocks.length}`;
      codeBlocks.push(code);
      return id;
    });
    
    // Handle regular newlines
    let formatted = processedContent;
    
    // Handle paragraphs (double newlines) with more spacing
    formatted = formatted.replace(/\n\n/g, '</p><p>');
    
    // Handle single newlines
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Wrap in paragraphs if not already done
    if (!formatted.startsWith('<p>')) {
      formatted = '<p>' + formatted + '</p>';
    }
    
    // Handle markdown-style formatting
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); // Bold
    formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>'); // Italic
    formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>'); // Inline code
    
    // Handle links [text](url)
    formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // Handle bullet points for better readability - process each paragraph
    formatted = formatted.replace(/<p>- (.*?)<\/p>/g, '<p class="bullet-point">• $1</p>');
    formatted = formatted.replace(/<p>• (.*?)<\/p>/g, '<p class="bullet-point">• $1</p>');
    
    // Handle numbered lists for better readability - process each paragraph
    formatted = formatted.replace(/<p>(\d+)\. (.*?)<\/p>/g, '<p class="numbered-item"><span class="number">$1.</span> $2</p>');
    
    // Restore code blocks with proper formatting
    codeBlocks.forEach((code, index) => {
      const id = `CODE_BLOCK_${index}`;
      formatted = formatted.replace(id, `<pre><code>${code.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</code></pre>`);
    });
    
    return formatted;
  }
  
  // Function to clean up and format agent mode responses
  function formatAgentModeResponse(content) {
    try {
      // Check if we can extract a clear plan structure
      let taskType = 'User Request';
      let taskTitle = 'Execute Automation';
      let steps = [];
      let planId = `plan_${Date.now()}`;
      
      // Try to extract task title from various formats
      const titleMatches = [
        content.match(/Automation Plan for: ([^\n]+)/),
        content.match(/I'll (help you |)([^\.]+)/),
        content.match(/Task: ([^\n]+)/)
      ];
      
      for (const match of titleMatches) {
        if (match && match[1]) {
          taskTitle = match[1].trim();
          break;
        } else if (match && match[2]) {
          taskTitle = match[2].trim();
          break;
        }
      }
      
      // Try to identify task type from content
      const contentLower = content.toLowerCase();
      
      // Check for common task types with priority ordering (more specific first)
      if (contentLower.includes('google') && (contentLower.includes('search') || contentLower.includes('find'))) {
        taskType = 'Google Search';
      } else if (contentLower.includes('youtube') && contentLower.includes('search')) {
        taskType = 'YouTube Search';
      } else if (contentLower.includes('search') || contentLower.includes('find information')) {
        taskType = 'Web Search';
      } else if (contentLower.match(/open|launch|start/) && contentLower.match(/app|application|program/)) {
        taskType = 'App Launch';
      } else if (contentLower.match(/open|launch|navigate/) && contentLower.match(/website|site|url|web|http/)) {
        taskType = 'Website Navigation';
      } else if (contentLower.match(/click|press|select|choose/) && contentLower.match(/button|link|element|option/)) {
        taskType = 'UI Interaction';
      } else if (contentLower.match(/type|enter|input|fill/)) {
        taskType = 'Data Entry';
      } else if (contentLower.match(/scroll|move/)) {
        taskType = 'Page Navigation';
      } else if (contentLower.match(/download|save|export/)) {
        taskType = 'File Operation';
      } else if (contentLower.match(/read|extract|get/)) {
        taskType = 'Data Extraction';
      } else {
        // Default to a generic task type if no specific pattern matches
        taskType = 'Automated Task';
      }
      
      // Extract steps from different formats
      const stepsRegexes = [
        /(?:Steps|Automation Steps|Here's what I'll do):([\s\S]*?)(?=\n\n|$)/i,
        /(?:I'll|Here's the plan|I will|First):([\s\S]*?)(?=\n\n|$)/i,
        /(?:\d+\.\s+[^\n]+\n)+/g
      ];
      
      for (const regex of stepsRegexes) {
        const stepsMatch = content.match(regex);
        if (stepsMatch) {
          if (typeof stepsMatch === 'string') {
            // It's a single string match
            steps = stepsMatch
              .split('\n')
              .filter(line => /^\d+\./.test(line.trim()))
              .map(line => line.replace(/^\d+\.\s*/, '').trim());
          } else if (stepsMatch[1]) {
            // It's a capturing group match
            steps = stepsMatch[1]
              .split('\n')
              .filter(line => line.trim())
              .map(line => line.replace(/^\d+\.\s*/, '').replace(/^-\s*/, '').trim());
          } else if (Array.isArray(stepsMatch)) {
            // It's a global regex match
            steps = stepsMatch
              .join('\n')
              .split('\n')
              .filter(line => /^\d+\./.test(line.trim()))
              .map(line => line.replace(/^\d+\.\s*/, '').trim());
          }
          
          if (steps.length > 0) break;
        }
      }
      
      // If no steps found, try to extract bullet points or anything that looks like steps
      if (steps.length === 0) {
        steps = content
          .split('\n')
          .filter(line => line.trim().startsWith('-') || line.trim().startsWith('•') || /^\d+\./.test(line.trim()))
          .map(line => line.replace(/^-\s*/, '').replace(/^•\s*/, '').replace(/^\d+\.\s*/, '').trim());
      }
      
      // If still no steps, create some based on the content
      if (steps.length === 0) {
        const sentences = content
          .replace(/\n/g, ' ')
          .split(/\.\s+/)
          .filter(s => s.length > 10 && !s.includes('AUTOMATION EXECUTION PLAN'));
        
        steps = sentences.slice(0, Math.min(3, sentences.length));
      }
      
      // Ensure we have at least 1 step
      if (steps.length === 0) {
        steps = ['Execute the requested automation'];
      }
      
      // Clean up steps - remove similar or duplicate steps
      steps = deduplicateSteps(steps);
      
      // Limit to 5 steps maximum to avoid clutter
      steps = steps.slice(0, 5);
      
      // Make sure steps are properly formatted and clean
      steps = steps.map(step => {
        // Remove any leading numbers or bullets that might have been missed
        step = step.replace(/^(\d+[\.\):]|\*|\-|\•)\s+/g, '');
        // Capitalize first letter
        return step.charAt(0).toUpperCase() + step.slice(1);
      });
      
      // Try to extract plan ID if it exists
      const planIdMatch = content.match(/plan[_-]id[:\s]+([a-z0-9_-]+)/i) || 
                         content.match(/Plan ID:[ \t]*`?([a-z0-9_-]+)`?/i);
      if (planIdMatch && planIdMatch[1]) {
        planId = planIdMatch[1];
      }
      
      // Create beautiful HTML for the automation plan with improved next-gen design
      const html = `
        <div class="automation-plan-card">
          <div class="plan-header">
            <div class="plan-icon">🎯</div>
            <div class="plan-title">
              <h3>AUTOMATION EXECUTION PLAN</h3>
              <div class="plan-id">ID: ${planId}</div>
            </div>
          </div>
          
          <div class="plan-content">
            <div class="plan-details">
              <div class="detail-grid">
                <div class="detail-item">
                  <div class="detail-icon">🔍</div>
                  <div class="detail-content">
                    <div class="detail-label">Task Type</div>
                    <div class="detail-value" title="${taskType}">${taskType}</div>
                  </div>
                </div>
                <div class="detail-item">
                  <div class="detail-icon">📋</div>
                  <div class="detail-content">
                    <div class="detail-label">Task</div>
                    <div class="detail-value" title="${taskTitle}">${taskTitle}</div>
                  </div>
                </div>
                <div class="detail-item">
                  <div class="detail-icon">⏱️</div>
                  <div class="detail-content">
                    <div class="detail-label">Duration</div>
                    <div class="detail-value">10.0 seconds</div>
                  </div>
                </div>
                <div class="detail-item">
                  <div class="detail-icon">🎯</div>
                  <div class="detail-content">
                    <div class="detail-label">Success Rate</div>
                    <div class="detail-value">85%</div>
                  </div>
                </div>
                <div class="detail-item">
                  <div class="detail-icon">🔧</div>
                  <div class="detail-content">
                    <div class="detail-label">Complexity</div>
                    <div class="detail-value">Medium</div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="divider"></div>
            
            <div class="plan-steps">
              <div class="steps-header">
                <div class="steps-icon">🚀</div>
                <div class="steps-title">Automation Steps</div>
              </div>
              <div class="steps-list">
                ${steps.map((step, i) => `
                  <div class="step-item">
                    <div class="step-number">${i + 1}</div>
                    <div class="step-content">
                      <div class="step-indicator">🟢</div>
                      <div class="step-text">${step}</div>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
            
            <div class="divider"></div>
            
            <div class="plan-system">
              <div class="system-icon">🧠</div>
              <div class="system-text">Agent Mode Intelligence</div>
            </div>
          </div>
          
          <div class="plan-footer">
            <div class="action-buttons">
              <button class="action-button execute" onclick="sendPlanAction('${planId}', 'execute')">
                <div class="button-icon">▶️</div>
                <div class="button-text">EXECUTE</div>
              </button>
              <button class="action-button simulate" onclick="sendPlanAction('${planId}', 'simulate')">
                <div class="button-icon">🔍</div>
                <div class="button-text">SIMULATE</div>
              </button>
              <button class="action-button modify" onclick="sendPlanAction('${planId}', 'modify')">
                <div class="button-icon">✏️</div>
                <div class="button-text">MODIFY</div>
              </button>
              <button class="action-button cancel" onclick="sendPlanAction('${planId}', 'cancel')">
                <div class="button-icon">❌</div>
                <div class="button-text">CANCEL</div>
              </button>
            </div>
          </div>
        </div>
      `;
      
      return html;
    } catch (error) {
      console.error('Error formatting agent mode response:', error);
      return content; // Return original content if parsing fails
    }
  }
  
  // Function to format automation plans with an elegant card layout
  // Handle plan action commands (execute, cancel, modify, simulate)
  function sendPlanAction(planId, action) {
    console.log(`Plan action: ${action} for plan ${planId}`);
    const actionMessage = `/do_${action} ${planId}`;
    // Use the sendMessage function to send the command
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: 'query',
        payload: {
          message: actionMessage,
          timestamp: Date.now()
        }
      }));
      
      // Add a message indicating the action was taken
      const actionText = {
        'execute': 'Executing',
        'simulate': 'Simulating',
        'modify': 'Modifying',
        'cancel': 'Cancelling'
      }[action];
      
      messages = [...messages, {
        id: Date.now(),
        type: 'system',
        content: `${actionText} plan ${planId}...`,
        timestamp: new Date().toISOString()
      }];
    }
  }
  
  // Make the function available to the window so it can be called from inline event handlers
  if (typeof window !== 'undefined') {
    window.sendPlanAction = sendPlanAction;
  }
  
  function formatAutomationPlan(content) {
    try {
      // Extract key elements from the automation plan
      const taskTypeMatch = content.match(/\*\*🔍 Task Type:\*\* ([^\n]+)/);
      const taskTitleMatch = content.match(/\*\*📋 Task:\*\* ([^\n]+)/);
      const durationMatch = content.match(/\*\*⏱️ Estimated Duration:\*\* ([^\n]+)/);
      const probabilityMatch = content.match(/\*\*🎯 Success Probability:\*\* ([^\n]+)/);
      const complexityMatch = content.match(/\*\*🔧 Complexity:\*\* ([^\n]+)/);
      const stepsCountMatch = content.match(/\*\*📝 Steps:\*\* ([^\n]+)/);
      const planIdMatch = content.match(/\*\*🆔 Plan ID:\*\* `([^`]+)`/);
      const planningMatch = content.match(/\*\*🧠 Planning:\*\* ([^\n]+)/);
      
      // Extract steps
      let steps = [];
      const stepsSection = content.match(/\*\*🚀 Automation Steps:\*\*\n([\s\S]*?)(?=\n\n\*\*🆔|$)/);
      if (stepsSection) {
        const stepsText = stepsSection[1];
        steps = stepsText.split('\n')
          .filter(step => step.trim())
          .map(step => {
            const stepMatch = step.match(/\d+\.\s+🟢\s+(.*)/);
            return stepMatch ? stepMatch[1] : step.trim();
          });
      }
      
      // Get values or defaults
      const taskType = taskTypeMatch ? taskTypeMatch[1] : 'Automated Action';
      const taskTitle = taskTitleMatch ? taskTitleMatch[1] : 'Execute Task';
      const duration = durationMatch ? durationMatch[1] : '10.0 seconds';
      const probability = probabilityMatch ? probabilityMatch[1] : '85%';
      const complexity = complexityMatch ? complexityMatch[1] : 'Medium';
      const stepsCount = stepsCountMatch ? stepsCountMatch[1] : `${steps.length} actions`;
      const planId = planIdMatch ? planIdMatch[1] : `plan_${Date.now()}`;
      const planning = planningMatch ? planningMatch[1] : 'Universal Intelligence System';
      
      // Create beautiful HTML for the automation plan with improved next-gen design
      const html = `
        <div class="automation-plan-card">
          <div class="plan-header">
            <div class="plan-icon">🎯</div>
            <div class="plan-title">
              <h3>AUTOMATION EXECUTION PLAN</h3>
              <div class="plan-id">ID: ${planId}</div>
            </div>
          </div>
          
          <div class="plan-content">
            <div class="plan-details">
              <div class="detail-grid">
                <div class="detail-item">
                  <div class="detail-icon">🔍</div>
                  <div class="detail-content">
                    <div class="detail-label">Task Type</div>
                    <div class="detail-value" title="${taskType}">${taskType}</div>
                  </div>
                </div>
                <div class="detail-item">
                  <div class="detail-icon">📋</div>
                  <div class="detail-content">
                    <div class="detail-label">Task</div>
                    <div class="detail-value" title="${taskTitle}">${taskTitle}</div>
                  </div>
                </div>
                <div class="detail-item">
                  <div class="detail-icon">⏱️</div>
                  <div class="detail-content">
                    <div class="detail-label">Duration</div>
                    <div class="detail-value">${duration}</div>
                  </div>
                </div>
                <div class="detail-item">
                  <div class="detail-icon">🎯</div>
                  <div class="detail-content">
                    <div class="detail-label">Success Rate</div>
                    <div class="detail-value">${probability}</div>
                  </div>
                </div>
                <div class="detail-item">
                  <div class="detail-icon">🔧</div>
                  <div class="detail-content">
                    <div class="detail-label">Complexity</div>
                    <div class="detail-value">${complexity}</div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="divider"></div>
            
            <div class="plan-steps">
              <div class="steps-header">
                <div class="steps-icon">🚀</div>
                <div class="steps-title">Automation Steps</div>
              </div>
              <div class="steps-list">
                ${steps.map((step, i) => `
                  <div class="step-item">
                    <div class="step-number">${i + 1}</div>
                    <div class="step-content">
                      <div class="step-indicator">🟢</div>
                      <div class="step-text">${step}</div>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
            
            <div class="divider"></div>
            
            <div class="plan-system">
              <div class="system-icon">🧠</div>
              <div class="system-text">${planning}</div>
            </div>
          </div>
          
          <div class="plan-footer">
            <div class="action-buttons">
              <button class="action-button execute" onclick="sendPlanAction('${planId}', 'execute')">
                <div class="button-icon">▶️</div>
                <div class="button-text">EXECUTE</div>
              </button>
              <button class="action-button simulate" onclick="sendPlanAction('${planId}', 'simulate')">
                <div class="button-icon">🔍</div>
                <div class="button-text">SIMULATE</div>
              </button>
              <button class="action-button modify" onclick="sendPlanAction('${planId}', 'modify')">
                <div class="button-icon">✏️</div>
                <div class="button-text">MODIFY</div>
              </button>
              <button class="action-button cancel" onclick="sendPlanAction('${planId}', 'cancel')">
                <div class="button-icon">❌</div>
                <div class="button-text">CANCEL</div>
              </button>
            </div>
          </div>
        </div>
      `;
      
      return html;
    } catch (error) {
      console.error('Error formatting automation plan:', error);
      return content; // Return original content if parsing fails
    }
  }

  let micPermission = null; // null = not asked, true = granted, false = denied

  // Helper function to remove similar or duplicate steps
  function deduplicateSteps(steps) {
    if (!steps || steps.length <= 1) return steps;
    
    const result = [];
    const similarityThreshold = 0.6; // Higher = more strict deduplication
    
    // Clean steps for comparison
    const cleanedSteps = steps.map(step => 
      step.toLowerCase()
         .replace(/^\d+\.\s*/, '')
         .replace(/^[•\-]\s*/, '')
         .trim()
    );
    
    // Calculate similarity between two strings (0-1)
    function calculateSimilarity(str1, str2) {
      // Simple word overlap similarity calculation
      const words1 = new Set(str1.split(/\s+/).filter(w => w.length > 3));
      const words2 = new Set(str2.split(/\s+/).filter(w => w.length > 3));
      
      if (words1.size === 0 || words2.size === 0) return 0;
      
      let intersection = 0;
      for (const word of words1) {
        if (words2.has(word)) intersection++;
      }
      
      return intersection / Math.max(words1.size, words2.size);
    }
    
    // Add first step
    result.push(steps[0]);
    
    // Check each subsequent step for similarity with already added steps
    for (let i = 1; i < steps.length; i++) {
      let isDuplicate = false;
      
      for (let j = 0; j < result.length; j++) {
        const similarity = calculateSimilarity(cleanedSteps[i], cleanedSteps[result.indexOf(result[j])]);
        
        if (similarity > similarityThreshold) {
          isDuplicate = true;
          break;
        }
      }
      
      if (!isDuplicate) {
        result.push(steps[i]);
      }
    }
    
    return result;
  }
  
  async function requestMicrophonePermission() {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      micPermission = true;
      messages = [...messages, {
        id: Date.now(),
        type: 'system',
        content: `✅ Microphone access granted! You can now record voice messages.`,
        timestamp: new Date()
      }];
    } catch (err) {
      micPermission = false;
      messages = [...messages, {
        id: Date.now(),
        type: 'error',
        content: `❌ Microphone access denied. Please check your browser permissions and try again.`,
        timestamp: new Date()
      }];
    }
  }
</script>

{#if show}
<div 
  class="cloud-chat" 
  class:minimized={showMinimized}
  style="left: {position.x}px; top: {position.y}px; width: {size.width}px; height: {showMinimized ? 80 : size.height}px;"
  transition:scale={{ duration: 800, easing: elasticOut, delay: 100 }}
  on:outrostart={() => playSound('minimize')}
  on:introstart={() => playSound('maximize')}
>
  <!-- Header -->
  <div class="cloud-header" on:mousedown={startDrag}>
    <div class="header-left">
      <div class="status-indicator" style="background-color: {connectionStatus === 'connected' ? '#30D158' : connectionStatus === 'connecting' ? '#FF9F0A' : '#FF453A'};"></div>
      <span class="title">NextGen<span class="title-highlight">AI</span></span>
    </div>
    
    <div class="header-controls">
      <button class="control-btn" class:active={showScreenViewer} on:click={toggleScreenViewer} aria-label="Toggle screen sharing">
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
    <!-- Cloud background pattern -->
    <div class="cloud-bg-pattern"></div>
    
    <!-- Mode selector -->
    {#if showModeSelector}
      <div class="mode-selector" transition:fade={{ duration: 300 }}>
        {#each Object.entries(modes) as [modeName, modeData], i}
          <button 
            class="mode-pill" 
            class:active={currentMode === modeName}
            on:click={() => selectMode(modeName)}
            style="--mode-color: {modeData.color}; --mode-gradient: {modeData.gradient}; animation-delay: {i * 100}ms;"
            aria-pressed={currentMode === modeName}
          >
            <span class="mode-emoji">{modeData.emoji}</span>
            <span class="mode-name">{modeName}</span>
          </button>
        {/each}
      </div>
    {/if}

    <!-- Messages -->
    <div class="messages-container" bind:this={chatContainer}>
      <!-- Add Enhanced Speech Controls -->
      <EnhancedSpeechControls 
        messages={messages} 
        currentMode={currentMode} 
        modeColors={modes} 
      />
      
      {#each messages as message, i (message.id)}
        <!-- Bind to messageElements array for speech position tracking -->
        <div 
          class="message {message.type}"
          bind:this={messageElements[i]}
          on:DOMNodeInserted={() => {
            if (messageElements[i]) {
              message.offsetTop = messageElements[i].offsetTop;
            }
          }}
          in:fly|local={{ y: 20, duration: 300, delay: 50 }}
        >
          <div class="message-content">
            {@html formatMessageContent(message.content)}
            
            {#if message.isPlanCard && message.plan}
              <NextGenPlanCard 
                plan={message.plan}
                planId={message.planId}
                mode={message.mode || 'Agent'}
                onExecute={() => executePlan(message.planId)}
                onModify={() => modifyPlan(message.planId)}
                onCancel={() => cancelPlan(message.planId)}
              />
            {:else if message.planId && message.requiresConfirmation}
              <div class="plan-actions">
                <button class="plan-action execute" on:click={() => executePlan(message.planId)}>
                  <span class="action-icon">🚀</span>
                  <span class="action-text">DO</span>
                </button>
                
                <button class="plan-action cancel" on:click={() => cancelPlan(message.planId)}>
                  <span class="action-icon">✗</span>
                  <span class="action-text">Cancel</span>
                </button>
                
                <button class="plan-action modify" on:click={() => modifyPlan(message.planId)}>
                  <span class="action-icon">✎</span>
                  <span class="action-text">Modify</span>
                </button>
              </div>
            {/if}
            
            {#if message.audioUrl}
              <div class="audio-player">
                <audio controls src={message.audioUrl}></audio>
              </div>
            {/if}
            
            {#if message.type === 'system' && (message.content.includes('Recording voice message') || message.content.includes('Call in progress'))}
              <div class="active-indicator">
                <div class="pulse-dot"></div>
                {#if message.content.includes('Recording')}
                  <span class="indicator-text recording">Recording...</span>
                {:else if message.content.includes('Call in progress')}
                  <span class="indicator-text call">On call</span>
                {/if}
              </div>
            {/if}
            
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
        <div class="typing-indicator" in:fade={{ duration: 200 }}>
          <div class="typing-dots">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
          </div>
          <span class="typing-text">{typingMessage}</span>
        </div>
      {/if}
      
      {#if progressVisible}
        <div class="progress-container" in:fade={{ duration: 300 }}>
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

    <!-- Input area -->
    <div class="input-area" class:focused={inputFocused}>
      <div class="input-container">
        <!-- Mode toggle button (minimized) -->
        <button 
          class="icon-button mode-button"
          on:click={toggleModeDropdown}
          class:active={modeDropdownOpen}
          style="--button-color: {modes[currentMode]?.color};"
          title="{currentMode} mode - Click to change"
        >
          <span class="mode-emoji">{modes[currentMode]?.emoji}</span>
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
        
        <!-- Action button group -->
        <div class="action-group">
          <!-- Voice recording button -->
          <button 
            class="icon-button voice-button" 
            aria-label="Voice recording"
            on:click={toggleVoiceRecording}
            class:active={isRecording}
            style="--button-color: #FF453A;"
            title="Record voice message"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2C10.3431 2 9 3.34315 9 5V12C9 13.6569 10.3431 15 12 15C13.6569 15 15 13.6569 15 12V5C15 3.34315 13.6569 2 12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M7 12C7 15.866 9.79086 19 13.5 19C17.2091 19 20 15.866 20 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          
          <!-- Call button -->
          <button 
            class="icon-button call-button" 
            class:active={isCallActive}
            aria-label="Phone call"
            on:click={initiateCall}
            style="--button-color: #30D158;"
            title="Start voice call"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 16.92V19.92C22 20.4704 21.7893 20.9983 21.4142 21.3871C21.0391 21.7659 20.5304 21.98 20 22C16.83 21.8379 13.7662 20.7659 11 19C8.55758 17.435 6.52484 15.4204 5 13C3.2 10.1667 2.12 7.08333 2 4C1.98758 3.46537 2.20108 2.95082 2.58077 2.57436C2.96046 2.19789 3.48475 1.98458 4.03 2H7.03C7.99292 1.9833 8.8226 2.70519 9 3.66C9.0875 4.68875 9.31 5.69667 9.66 6.66C9.88275 7.3194 9.793 8.0564 9.4 8.64L8.21 9.83C9.40064 12.383 11.5304 14.4989 14.1 15.69L15.29 14.5C15.8773 14.107 16.6143 14.0173 17.2737 14.24C18.243 14.59 19.2509 14.8125 20.28 14.9C21.2522 15.0783 21.9845 15.9514 22 16.92Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          
          <!-- Text-to-speech button -->
          <div class="icon-button speech-button">
            <EnhancedSpeechControls 
              messages={messages} 
              currentMode={currentMode} 
              modeColors={modes} 
            />
          </div>
          
          <!-- Send button -->
          <button 
            class="icon-button send-button"
            class:active={input.trim().length > 0}
            on:click={sendMessage}
            disabled={!input.trim() || connectionStatus !== 'connected'}
            style="--button-color: {modes[currentMode]?.color};"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M5 12H19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M12 5L19 12L12 19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
      
      {#if modeDropdownOpen}
        <div class="mode-dropdown" in:fly={{ y: 10, duration: 200 }}>
          {#each Object.entries(modes) as [modeName, modeData], i}
            <button 
              class="mode-option"
              class:active={currentMode === modeName}
              on:click={() => {
                selectMode(modeName);
                toggleModeDropdown();
              }}
              in:fly={{ y: 5, duration: 200, delay: i * 50 }}
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
              in:fly={{ y: 10, duration: 300, delay: i * 100 }}
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

<!-- Screen viewer overlay -->
{#if showScreenViewer}
  <div class="screen-viewer-overlay" transition:fade={{ duration: 300 }}>
    <ScreenViewer on:close={() => showScreenViewer = false} />
  </div>
{/if}
{/if}

<style>
  /* NextGen AI variables - ultra modern design system */
  :root {
    /* Futuristic gradient backgrounds with increased depth */
    --nextgen-bg-dark: linear-gradient(140deg, rgba(32, 38, 60, 0.85) 0%, rgba(28, 32, 55, 0.8) 50%, rgba(25, 28, 48, 0.85) 100%);
    --nextgen-bg-light: linear-gradient(140deg, rgba(245, 247, 255, 0.7) 0%, rgba(235, 240, 255, 0.65) 50%, rgba(225, 232, 248, 0.7) 100%);
    
    /* Glass morphism border effects */
    --nextgen-border: linear-gradient(to bottom, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.05));
    --nextgen-border-glow: linear-gradient(90deg, 
      rgba(125, 145, 255, 0.5) 0%, 
      rgba(160, 115, 255, 0.5) 50%,
      rgba(125, 145, 255, 0.5) 100%);
      
    /* Enhanced dimensions */
    --nextgen-radius: 32px;
    --nextgen-shadow: 
      0 20px 80px rgba(0, 0, 0, 0.15),
      0 8px 30px rgba(0, 0, 0, 0.12), 
      0 1px 0 rgba(255, 255, 255, 0.08);
    --nextgen-glow: 
      0 0 80px rgba(120, 170, 255, 0.2),
      0 0 30px rgba(140, 100, 255, 0.15);
    
    /* Enhanced blur effects */
    --blur-heavy: saturate(150%) blur(40px);
    --blur-medium: saturate(130%) blur(25px);
    --blur-light: saturate(120%) blur(15px);
    
    /* Modern color system */
    --text-primary: rgba(255, 255, 255, 0.98);
    --text-secondary: rgba(255, 255, 255, 0.78);
    --text-muted: rgba(255, 255, 255, 0.55);
    --text-highlight: linear-gradient(90deg, #5ee7df 0%, #b490ca 100%);
    
    /* Vibrant accents */
    --accent-blue: rgb(10, 132, 255);
    --accent-purple: rgb(191, 90, 242);
    --accent-teal: rgb(94, 231, 223);
    --accent-green: rgb(48, 209, 88);
    --accent-red: rgb(255, 69, 58);
    --accent-orange: rgb(255, 159, 10);
    --accent-pink: rgb(255, 55, 95);
    
    /* Animation timing */
    --font-system: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', system-ui, sans-serif;
    --spring-transition: 0.85s cubic-bezier(0.2, 0.8, 0.2, 1);
    --smooth-transition: 0.45s cubic-bezier(0.32, 0.08, 0.24, 1);
    --quick-transition: 0.25s cubic-bezier(0.32, 0.08, 0.24, 1);
    
    /* Rename for compatibility but update values */
    --cloud-bg-dark: var(--nextgen-bg-dark);
    --cloud-bg-light: var(--nextgen-bg-light);
    --cloud-border: var(--nextgen-border);
    --cloud-radius: var(--nextgen-radius);
    --cloud-shadow: var(--nextgen-shadow);
    --cloud-glow: var(--nextgen-glow);
  }
  
  /* NextGen AI container with enhanced depth and materials */
  .cloud-chat {
    position: fixed;
    background: var(--cloud-bg-dark);
    border-radius: var(--cloud-radius);
    backdrop-filter: var(--blur-heavy);
    -webkit-backdrop-filter: var(--blur-heavy);
    box-shadow: var(--cloud-shadow), var(--cloud-glow);
    display: flex;
    flex-direction: column;
    z-index: 10000;
    pointer-events: auto;
    transition: all var(--spring-transition);
    overflow: hidden;
    font-family: var(--font-system);
    letter-spacing: -0.011em;
    transform-origin: center center;
    animation: cloud-appear 1.5s cubic-bezier(0.22, 1, 0.36, 1);
    
    /* Enhanced border effect with depth */
    position: relative;
    padding: 2px;
  }
  
  /* Enhanced layered border effects */
  .cloud-chat::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: var(--cloud-radius);
    padding: 1px;
    background: var(--nextgen-border);
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
    opacity: 0.9;
    z-index: 1;
    
    /* Shimmer animation */
    animation: border-shimmer 8s infinite linear;
  }
  
  /* Enhanced inner glow with depth perception */
  .cloud-chat::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: var(--cloud-radius);
    background: 
      radial-gradient(circle at 25% 25%, rgba(120, 170, 255, 0.15), transparent 50%),
      radial-gradient(circle at 75% 75%, rgba(190, 140, 255, 0.12), transparent 50%),
      linear-gradient(120deg, rgba(94, 231, 223, 0.08) 0%, rgba(180, 144, 202, 0.08) 100%);
    opacity: 0.75;
    pointer-events: none;
    z-index: -1;
    filter: blur(5px);
    transform: translateZ(0);
    
    /* Subtle glow pulsing */
    animation: glow-pulse 6s infinite alternate ease-in-out;
  }
  
  /* Shimmer animation for borders */
  @keyframes border-shimmer {
    0% { 
      background-position: -300px 0;
      background: linear-gradient(90deg, 
        rgba(125, 145, 255, 0.2) 0%, 
        rgba(160, 115, 255, 0.3) 30%,
        rgba(94, 231, 223, 0.2) 70%,
        rgba(125, 145, 255, 0.2) 100%
      );
    }
    100% { 
      background-position: 300px 0;
      background: linear-gradient(90deg, 
        rgba(125, 145, 255, 0.2) 0%, 
        rgba(94, 231, 223, 0.2) 30%,
        rgba(160, 115, 255, 0.3) 70%,
        rgba(125, 145, 255, 0.2) 100%
      );
    }
  }
  
  /* Subtle glow pulsing */
  @keyframes glow-pulse {
    0% { opacity: 0.65; filter: blur(5px); }
    50% { opacity: 0.75; filter: blur(7px); }
    100% { opacity: 0.8; filter: blur(5px); }
  }
  
  /* Enhanced nextgen entrance animation */
  @keyframes cloud-appear {
    0% { 
      opacity: 0;
      transform: translateY(40px) scale(0.85);
      filter: brightness(0.6) blur(5px);
      box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    }
    25% {
      opacity: 0.5;
      transform: translateY(20px) scale(0.92);
      filter: brightness(0.8) blur(2px);
    }
    60% {
      opacity: 0.85;
      transform: translateY(5px) scale(0.98);
      filter: brightness(0.95) blur(0);
    }
    85% {
      transform: translateY(-2px) scale(1.01);
    }
    100% { 
      opacity: 1;
      transform: translateY(0) scale(1);
      filter: brightness(1) blur(0);
      box-shadow: var(--cloud-shadow), var(--cloud-glow);
    }
  }
  
  /* Advanced dynamic floating animation */
  @media (prefers-reduced-motion: no-preference) {
    .cloud-chat {
      animation: 
        cloud-appear 1.5s cubic-bezier(0.22, 1, 0.36, 1), 
        float 10s ease-in-out infinite;
    }
    
    @keyframes float {
      0% { 
        transform: translateY(0px) translateX(0px) rotate(0deg); 
        box-shadow: var(--cloud-shadow), 0 0 60px rgba(120, 170, 255, 0.15);
      }
      25% {
        transform: translateY(-5px) translateX(2px) rotate(0.1deg);
      }
      50% { 
        transform: translateY(-10px) translateX(0px) rotate(-0.1deg); 
        box-shadow: var(--cloud-shadow), 0 0 80px rgba(120, 170, 255, 0.2);
      }
      75% {
        transform: translateY(-5px) translateX(-2px) rotate(0deg);
      }
      100% { 
        transform: translateY(0px) translateX(0px) rotate(0deg); 
        box-shadow: var(--cloud-shadow), 0 0 60px rgba(120, 170, 255, 0.15);
      }
    }
  }
  
  /* NextGen background pattern with particle effect */
  .cloud-bg-pattern {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    opacity: 0.08;
    background-image: 
      url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='400' height='400' viewBox='0 0 800 800'%3E%3Cg fill='none' stroke='%23FFFFFF' stroke-width='1'%3E%3Cpath d='M769 229L1037 260.9M927 880L731 737 520 660 309 538 40 599 295 764 126.5 879.5 40 599-197 493 102 382-31 229 126.5 79.5-69-63'/%3E%3Cpath d='M-31 229L237 261 390 382 603 493 308.5 537.5 101.5 381.5M370 905L295 764'/%3E%3Cpath d='M520 660L578 842 731 737 840 599 603 493 520 660 295 764 309 538 390 382 539 269 769 229 577.5 41.5 370 105 295 -36 126.5 79.5 237 261 102 382 40 599 -69 737 127 880'/%3E%3Cpath d='M520-140L578.5 42.5 731-63M603 493L539 269 237 261 370 105M902 382L539 269M390 382L102 382'/%3E%3Cpath d='M-222 42L126.5 79.5 370 105 539 269 577.5 41.5 927 80 769 229 902 382 603 493 731 737M295-36L577.5 41.5M578 842L295 764M40-201L127 80M102 382L-261 269'/%3E%3C/g%3E%3Cg fill='%23FFFFFF'%3E%3Ccircle cx='769' cy='229' r='1'/%3E%3Ccircle cx='539' cy='269' r='1'/%3E%3Ccircle cx='603' cy='493' r='3'/%3E%3Ccircle cx='731' cy='737' r='1'/%3E%3Ccircle cx='520' cy='660' r='1'/%3E%3Ccircle cx='309' cy='538' r='1'/%3E%3Ccircle cx='295' cy='764' r='1'/%3E%3Ccircle cx='40' cy='599' r='1'/%3E%3Ccircle cx='102' cy='382' r='1'/%3E%3Ccircle cx='127' cy='80' r='2'/%3E%3Ccircle cx='370' cy='105' r='1'/%3E%3Ccircle cx='578' cy='42' r='1'/%3E%3Ccircle cx='237' cy='261' r='1'/%3E%3Ccircle cx='390' cy='382' r='1'/%3E%3C/g%3E%3C/svg%3E"),
      radial-gradient(circle at 15% 25%, rgba(150, 200, 255, 0.1) 0%, transparent 45%),
      radial-gradient(circle at 85% 85%, rgba(190, 140, 255, 0.08) 0%, transparent 45%);
    background-position: center;
    background-size: 180%;
    pointer-events: none;
    z-index: -1;
    animation: bg-float 120s infinite linear;
    opacity: 0;
    transform: translateZ(0);
    animation: bg-fade-in 2s 0.5s forwards ease-out, bg-float 120s infinite linear;
  }
  
  @keyframes bg-fade-in {
    0% { opacity: 0; }
    100% { opacity: 0.08; }
  }
  
  @keyframes bg-float {
    0% { background-position: 0% 0%; }
    100% { background-position: 200% 200%; }
  }
  
  /* Particle background - advanced effect */
  .cloud-chat::before, .cloud-chat::after {
    content: '';
    pointer-events: none;
  }
  
  /* Dynamic minimized state with enhanced animation */
  .cloud-chat.minimized {
    height: 70px !important;
    transform: scale(0.97) translateY(5px);
    opacity: 0.95;
    transition: 
      height 0.6s cubic-bezier(0.34, 1.56, 0.64, 1), 
      transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1), 
      opacity 0.6s ease-in-out,
      box-shadow 0.6s ease-in-out;
    box-shadow: 
      0 10px 30px rgba(0, 0, 0, 0.08), 
      0 5px 15px rgba(0, 0, 0, 0.06),
      0 0 0 1px rgba(255, 255, 255, 0.05),
      0 0 40px rgba(130, 170, 255, 0.1);
  }
  
  .cloud-chat.minimized .cloud-header {
    backdrop-filter: var(--blur-medium);
    border-bottom: none;
  }
  
  /* Add slight bounce when expanding */
  .cloud-chat:not(.minimized) {
    transition: 
      height 0.7s cubic-bezier(0.34, 1.56, 0.64, 1), 
      transform 0.7s cubic-bezier(0.34, 1.56, 0.64, 1),
      opacity 0.6s ease-in-out,
      box-shadow 0.6s ease-in-out;
  }
  
  /* NextGen header with premium materials */
  .cloud-header {
    padding: 16px 22px;
    background: rgba(35, 40, 60, 0.25);
    backdrop-filter: var(--blur-medium);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: grab;
    user-select: none;
    transition: all var(--smooth-transition);
    margin: 1px;
    border-top-left-radius: calc(var(--cloud-radius) - 2px);
    border-top-right-radius: calc(var(--cloud-radius) - 2px);
    position: relative;
    overflow: hidden;
    box-shadow: 0 1px 0 rgba(255, 255, 255, 0.03);
    z-index: 5;
  }
  
  .cloud-header::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 60px;
    background: linear-gradient(to bottom, 
      rgba(120, 170, 255, 0.07) 0%, 
      rgba(160, 120, 255, 0.04) 50%,
      rgba(130, 170, 255, 0) 100%);
    pointer-events: none;
    opacity: 0;
    animation: header-glow-in 1.5s 0.6s forwards ease-out;
  }
  
  @keyframes header-glow-in {
    0% { opacity: 0; }
    100% { opacity: 1; }
  }
  
  .cloud-header:active {
    cursor: grabbing;
    background: rgba(40, 45, 70, 0.3);
  }
  
  .header-left {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  
  .status-indicator {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    transition: background-color 0.5s ease;
    box-shadow: 0 0 8px currentColor, 0 0 12px currentColor;
    position: relative;
    z-index: 1;
  }
  
  .status-indicator::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: currentColor;
    opacity: 0.15;
    transform: translate(-50%, -50%);
    animation: pulse 2s infinite ease-in-out;
  }
  
  @keyframes pulse {
    0% { transform: translate(-50%, -50%) scale(1); opacity: 0.15; }
    50% { transform: translate(-50%, -50%) scale(2.5); opacity: 0; }
    100% { transform: translate(-50%, -50%) scale(1); opacity: 0.15; }
  }
  
  .title {
    color: var(--text-primary);
    font-size: 15px;
    font-weight: 600;
    letter-spacing: -0.01em;
    background: linear-gradient(90deg, 
      rgba(255, 255, 255, 0.98),
      rgba(255, 255, 255, 0.85) 70%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-fill-color: transparent;
    position: relative;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  }
  
  .title-highlight {
    background: var(--text-highlight);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-fill-color: transparent;
    font-weight: 700;
  }
  
  .header-controls {
    display: flex;
    gap: 12px;
  }
  
  .control-btn {
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
    width: 30px;
    height: 30px;
    padding: 0;
    border-radius: 15px;
    cursor: pointer;
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
    font-size: 13px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .control-btn::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, 
      rgba(255, 255, 255, 0.15) 0%, 
      rgba(255, 255, 255, 0) 100%);
    opacity: 0;
    transition: opacity 0.25s ease;
  }
  
  .control-btn::after {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    right: -50%;
    bottom: -50%;
    background: radial-gradient(circle, 
      rgba(255, 255, 255, 0.2) 0%, 
      transparent 70%);
    opacity: 0;
    transform: scale(0.5);
    transition: transform 0.5s ease-out, opacity 0.5s ease-out;
  }
  
  .control-btn:hover {
    background: rgba(255, 255, 255, 0.12);
    transform: translateY(-2px) scale(1.05);
    box-shadow: 
      0 5px 15px rgba(0, 0, 0, 0.1),
      0 0 5px rgba(255, 255, 255, 0.1);
  }
  
  .control-btn:hover::before {
    opacity: 1;
  }
  
  .control-btn:hover::after {
    opacity: 0.5;
    transform: scale(1);
  }
  
  .control-btn:active {
    transform: translateY(0) scale(0.95);
    transition: all 0.1s ease-out;
  }
  
  .control-btn.active {
    background: rgba(10, 132, 255, 0.2);
    border-color: rgba(10, 132, 255, 0.4);
    color: rgb(10, 132, 255);
    box-shadow: 
      0 0 0 1px rgba(10, 132, 255, 0.2),
      0 0 8px rgba(10, 132, 255, 0.3);
  }
  
  .control-btn.close-btn {
    font-size: 18px;
    line-height: 1;
    font-weight: 300;
  }
  
  .control-btn.close-btn:hover {
    background: rgba(255, 69, 58, 0.2);
    border-color: rgba(255, 69, 58, 0.4);
    color: rgb(255, 69, 58);
    box-shadow: 
      0 0 0 1px rgba(255, 69, 58, 0.2),
      0 0 8px rgba(255, 69, 58, 0.3);
  }
  
  /* Advanced interactive mode selector */
  .mode-selector {
    display: flex;
    gap: 10px;
    padding: 16px 22px 6px;
    overflow-x: auto;
    scrollbar-width: none;
    -ms-overflow-style: none;
    position: relative;
    z-index: 2;
  }
  
  .mode-selector::-webkit-scrollbar {
    display: none;
  }
  
  .mode-pill {
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 18px;
    padding: 8px 14px;
    font-size: 13px;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    white-space: nowrap;
    animation: pill-appear 0.8s cubic-bezier(0.22, 1, 0.36, 1) backwards;
    position: relative;
    box-shadow: 
      0 2px 6px rgba(0, 0, 0, 0.07),
      0 1px 2px rgba(0, 0, 0, 0.1);
    overflow: visible;
    z-index: 3;
  }
  
  /* Fancy staggered entrance animation */
  @keyframes pill-appear {
    0% { 
      opacity: 0; 
      transform: translateY(15px) scale(0.85);
      filter: blur(2px);
    }
    70% {
      transform: translateY(-2px) scale(1.02);
      filter: blur(0);
    }
    100% { 
      opacity: 1; 
      transform: translateY(0) scale(1);
      filter: blur(0);
    }
  }
  
  /* Subtle shine effect */
  .mode-pill::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(
      120deg,
      transparent,
      rgba(255, 255, 255, 0.2),
      transparent
    );
    transition: left 0.7s ease;
  }
  
  .mode-pill:hover {
    background: rgba(255, 255, 255, 0.12);
    transform: translateY(-3px) scale(1.05);
    box-shadow: 
      0 8px 20px rgba(0, 0, 0, 0.1),
      0 3px 8px rgba(0, 0, 0, 0.1);
    color: var(--text-primary);
  }
  
  .mode-pill:hover::before {
    left: 100%;
  }
  
  .mode-pill:active {
    transform: translateY(0) scale(0.98);
    transition: all 0.1s ease-out;
  }
  
  .mode-pill.active {
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: var(--text-primary);
    position: relative;
    overflow: hidden;
    transform: translateY(-1px);
    box-shadow: 
      0 6px 15px rgba(0, 0, 0, 0.08),
      0 2px 5px rgba(0, 0, 0, 0.08),
      0 0 0 1px rgba(255, 255, 255, 0.1);
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
    box-shadow: 0 0 8px currentColor;
    z-index: 3;
  }
  
  .mode-pill.active::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--mode-gradient);
    opacity: 0.15;
    z-index: 1;
  }
  
  .mode-emoji {
    font-size: 16px;
    line-height: 1;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
    z-index: 4;
  }
  
  .mode-name {
    position: relative;
    z-index: 4;
    font-weight: 500;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  }
  
  .mode-pill:hover .mode-emoji {
    transform: scale(1.2) rotate(5deg);
  }
  
  .mode-pill.active .mode-emoji {
    transform: scale(1.15);
  }
  
  /* Enhanced messages container with depth effects */
  .messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 20px 22px;
    display: flex;
    flex-direction: column;
    gap: 18px;
    scroll-behavior: smooth;
    position: relative;
    scrollbar-width: thin;
    scrollbar-color: rgba(255, 255, 255, 0.3) transparent;
    background-image: 
      radial-gradient(
        circle at 50% 0%, 
        rgba(120, 170, 255, 0.03) 0%, 
        transparent 70%
      ),
      radial-gradient(
        circle at 80% 80%, 
        rgba(180, 140, 240, 0.03) 0%, 
        transparent 70%
      );
    z-index: 1;
  }
  
  .messages-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 50px;
    background: linear-gradient(
      to bottom, 
      rgba(35, 40, 60, 0.2) 0%, 
      rgba(35, 40, 60, 0) 100%
    );
    pointer-events: none;
    z-index: 5;
    opacity: 0.7;
  }
  
  .messages-container::after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 50px;
    background: linear-gradient(
      to top, 
      rgba(35, 40, 60, 0.2) 0%, 
      rgba(35, 40, 60, 0) 100%
    );
    pointer-events: none;
    z-index: 5;
    opacity: 0.7;
  }
  
  .messages-container::-webkit-scrollbar {
    width: 5px;
  }
  
  .messages-container::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.02);
    border-radius: 3px;
    margin: 10px 0;
  }
  
  .messages-container::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.25);
    border-radius: 3px;
    transition: background 0.3s ease;
  }
  
  .messages-container::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.4);
  }
  
  /* Enhanced message bubbles with depth and materials */
  .message {
    display: flex;
    flex-direction: column;
    max-width: 85%;
    animation: message-appear 0.6s cubic-bezier(0.22, 1, 0.36, 1);
    transform-origin: center bottom;
    position: relative;
    margin-bottom: 16px;
  }
  
  @keyframes message-appear {
    0% {
      opacity: 0;
      transform: translateY(20px) scale(0.95);
      filter: blur(2px);
    }
    60% {
      opacity: 0.9;
      filter: blur(0);
    }
    85% {
      transform: translateY(-2px) scale(1.01);
    }
    100% {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }
  
  .message.user {
    align-self: flex-end;
    animation-delay: 0.1s;
  }
  
  .message.assistant, .message.error, .message.confirmation {
    align-self: flex-start;
  }
  
  .message-content {
    padding: 14px 18px;
    border-radius: 22px;
    line-height: 1.5;
    font-size: 15px;
    letter-spacing: -0.01em;
    position: relative;
    transition: all 0.3s ease;
    box-shadow: 
      0 3px 10px rgba(0, 0, 0, 0.07),
      0 1px 4px rgba(0, 0, 0, 0.05),
      0 0 0 1px rgba(255, 255, 255, 0.02);
  }
  
  /* Enhanced message formatting styles */
  .message-content p {
    margin: 0 0 10px 0;
  }
  
  .message-content p:last-child {
    margin-bottom: 0;
  }
  
  .message-content a {
    color: #0A84FF;
    text-decoration: none;
    border-bottom: 1px dotted rgba(10, 132, 255, 0.5);
    transition: all 0.2s ease;
  }
  
  .message-content a:hover {
    border-bottom: 1px solid rgba(10, 132, 255, 0.8);
    text-shadow: 0 0 3px rgba(10, 132, 255, 0.3);
  }
  
  .message-content code {
    background: rgba(0, 0, 0, 0.2);
    padding: 2px 5px;
    border-radius: 4px;
    font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
    font-size: 0.9em;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }
  
  .message-content pre {
    background: rgba(0, 0, 0, 0.2);
    border-radius: 8px;
    padding: 12px;
    margin: 10px 0;
    overflow-x: auto;
    border: 1px solid rgba(255, 255, 255, 0.1);
    max-width: 100%;
  }
  
  .message-content pre code {
    background: transparent;
    padding: 0;
    border: none;
    display: block;
    line-height: 1.4;
    color: #E0E0E0;
  }
  
  .message-content p.bullet-point {
    position: relative;
    padding-left: 5px;
    margin-bottom: 5px;
  }
  
  .message-content p.numbered-item {
    position: relative;
    padding-left: 5px;
    margin-bottom: 5px;
  }
  
  .message-content p.numbered-item .number {
    display: inline-block;
    min-width: 20px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.9);
  }
  
  .message.user .message-content a {
    color: white;
    border-bottom: 1px dotted rgba(255, 255, 255, 0.5);
  }
  
  .message.user .message-content a:hover {
    border-bottom: 1px solid rgba(255, 255, 255, 0.8);
    text-shadow: 0 0 3px rgba(255, 255, 255, 0.3);
  }
  
  .message.user .message-content code {
    background: rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.15);
  }
  
  /* Enhanced user message with glass morphism and glow */
  .message.user .message-content {
    background: linear-gradient(135deg, 
      rgba(10, 132, 255, 0.85) 0%, 
      rgba(94, 92, 230, 0.85) 50%,
      rgba(120, 170, 255, 0.85) 100%);
    color: white;
    border-radius: 24px 24px 6px 24px;
    box-shadow: 
      0 8px 25px rgba(10, 132, 255, 0.25),
      0 4px 10px rgba(10, 132, 255, 0.15),
      0 0 0 1px rgba(255, 255, 255, 0.15),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }
  
  /* Add light reflection to user messages */
  .message.user .message-content::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 50%;
    background: linear-gradient(
      to bottom,
      rgba(255, 255, 255, 0.15),
      rgba(255, 255, 255, 0)
    );
    border-radius: 22px 22px 0 0;
    pointer-events: none;
  }
  
  /* Enhanced assistant message with improved depth */
  .message.assistant .message-content {
    background: rgba(255, 255, 255, 0.12);
    color: var(--text-primary);
    border-radius: 24px 24px 24px 6px;
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    position: relative;
    overflow: hidden;
    box-shadow: 
      0 4px 15px rgba(0, 0, 0, 0.1),
      0 2px 8px rgba(0, 0, 0, 0.05),
      inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }
  
  /* Add subtle pattern to assistant messages */
  .message.assistant .message-content::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-image: 
      radial-gradient(
        circle at 85% 15%, 
        rgba(255, 255, 255, 0.1) 0%, 
        transparent 50%
      );
    opacity: 0.5;
    pointer-events: none;
  }
  
  /* Enhanced error message */
  .message.error .message-content {
    background: rgba(255, 69, 58, 0.15);
    color: rgba(255, 160, 160, 1);
    border: 1px solid rgba(255, 69, 58, 0.2);
    border-radius: 18px;
    box-shadow: 
      0 5px 15px rgba(255, 69, 58, 0.1),
      0 2px 5px rgba(255, 69, 58, 0.05);
  }
  
  /* Enhanced confirmation message with glass effect */
  .message.confirmation .message-content {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    border-radius: 22px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    backdrop-filter: var(--blur-light);
    box-shadow: 
      0 8px 20px rgba(0, 0, 0, 0.1),
      0 3px 6px rgba(0, 0, 0, 0.05),
      0 0 0 1px rgba(255, 255, 255, 0.05);
  }
  
  .message-meta {
    font-size: 10px;
    color: var(--text-muted);
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
    gap: 10px;
    margin-top: 16px;
  }
  
  .confirmation-action {
    flex: 1;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 8px 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    cursor: pointer;
    transition: all var(--smooth-transition);
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
    position: relative;
    overflow: hidden;
  }
  
  .confirmation-action::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    opacity: 0;
    transition: opacity 0.25s ease;
  }
  
  .confirmation-action:hover {
    transform: translateY(-1px);
  }
  
  .confirmation-action:hover::before {
    opacity: 1;
  }
  
  .confirmation-action.confirm {
    color: var(--accent-green);
  }
  
  .confirmation-action.confirm::before {
    background: linear-gradient(135deg, 
      rgba(48, 209, 88, 0.1) 0%, 
      rgba(48, 209, 88, 0.2) 100%);
  }
  
  .confirmation-action.cancel {
    color: var(--accent-red);
  }
  
  .confirmation-action.cancel::before {
    background: linear-gradient(135deg, 
      rgba(255, 69, 58, 0.1) 0%, 
      rgba(255, 69, 58, 0.2) 100%);
  }
  
  .confirmation-action.modify {
    color: var(--accent-orange);
  }
  
  .confirmation-action.modify::before {
    background: linear-gradient(135deg, 
      rgba(255, 159, 10, 0.1) 0%, 
      rgba(255, 159, 10, 0.2) 100%);
  }
  
  .action-icon {
    font-size: 14px;
  }

  /* Plan action styles */
  .plan-actions {
    display: flex;
    gap: 8px;
    margin-top: 12px;
    flex-wrap: wrap;
  }

  .plan-action {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    border: none;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
    background: var(--nextgen-bg-light);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .plan-action.execute {
    background: linear-gradient(135deg, #30D158 0%, #28A745 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(48, 209, 88, 0.3);
  }

  .plan-action.execute:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(48, 209, 88, 0.4);
  }

  .plan-action.cancel {
    background: linear-gradient(135deg, #FF453A 0%, #DC3545 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(255, 69, 58, 0.3);
  }

  .plan-action.cancel:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(255, 69, 58, 0.4);
  }

  .plan-action.modify {
    background: linear-gradient(135deg, #007AFF 0%, #0056CC 100%);
    color: white;
    box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
  }

  .plan-action.modify:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 122, 255, 0.4);
  }
  
  /* Typing indicator */
  .typing-indicator {
    align-self: flex-start;
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    padding: 10px 16px;
    max-width: 70%;
    animation: message-appear 0.4s cubic-bezier(0.16, 1, 0.3, 1);
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
    0%, 60%, 100% { transform: translateY(0) scale(1); opacity: 0.5; }
    30% { transform: translateY(-4px) scale(1.2); opacity: 1; }
  }
  
  .typing-text {
    font-size: 12px;
    color: var(--text-secondary);
  }
  
  /* Progress bar */
  .progress-container {
    background: rgba(40, 45, 70, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 16px;
    padding: 12px 16px;
    margin: 8px 0;
    align-self: stretch;
    animation: message-appear 0.4s cubic-bezier(0.16, 1, 0.3, 1);
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
    transition: width 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
  }
  
  .progress-fill::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(90deg, 
      transparent 0%, 
      rgba(255, 255, 255, 0.3) 50%, 
      transparent 100%);
    animation: progress-shimmer 2s infinite;
  }
  
  @keyframes progress-shimmer {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
  
  .progress-step {
    font-size: 12px;
    color: var(--text-secondary);
  }
  
  /* NextGen input area with enhanced interactive elements */
  .input-area {
    padding: 16px 20px;
    background: rgba(32, 38, 60, 0.4);
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(20px);
    transition: all var(--smooth-transition);
    position: relative;
    margin: 0 1px 1px 1px;
    border-bottom-left-radius: calc(var(--cloud-radius) - 2px);
    border-bottom-right-radius: calc(var(--cloud-radius) - 2px);
    z-index: 5;
    box-shadow: 
      0 -1px 0 rgba(255, 255, 255, 0.05),
      0 -4px 20px rgba(0, 0, 0, 0.1);
  }
  
  .input-area::before {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 100px;
    background: linear-gradient(to top, 
      rgba(94, 231, 223, 0.03) 0%, 
      rgba(180, 144, 202, 0.02) 50%,
      rgba(120, 170, 255, 0) 100%);
    pointer-events: none;
    z-index: -1;
    opacity: 0;
    transition: opacity 0.5s ease;
  }
  
  .input-area.focused {
    background: rgba(35, 42, 70, 0.5);
    box-shadow: 
      0 -1px 0 rgba(255, 255, 255, 0.05),
      0 -5px 15px rgba(0, 0, 0, 0.05);
  }
  
  .input-area.focused::before {
    opacity: 1;
  }
  
  .input-container {
    display: flex;
    gap: 6px;
    align-items: center;
    position: relative;
  }
  
  .mode-toggle {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 6px 12px;
    display: flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    transition: all var(--smooth-transition);
    font-size: 12px;
    color: var(--text-secondary);
    position: relative;
    overflow: hidden;
    flex-shrink: 0;
  }
  
  .mode-toggle::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--mode-gradient);
    opacity: 0;
    transition: opacity 0.25s ease;
  }
  
  .mode-toggle:hover {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .mode-toggle:hover::before {
    opacity: 0.1;
  }
  
  .mode-toggle.active {
    background: rgba(255, 255, 255, 0.12);
    color: var(--text-primary);
  }
  
  .mode-toggle.active::before {
    opacity: 0.15;
  }
  
  .message-input {
    flex: 1;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 10px 12px;
    color: var(--text-primary);
    font-size: 15px;
    font-family: var(--font-system);
    resize: none;
    height: 40px;
    max-height: 120px;
    line-height: 1.4;
    outline: none;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    backdrop-filter: var(--blur-light);
    letter-spacing: -0.01em;
    box-shadow: 
      0 2px 8px rgba(0, 0, 0, 0.05),
      0 1px 2px rgba(0, 0, 0, 0.05),
      0 0 0 1px rgba(255, 255, 255, 0.01);
    position: relative;
    overflow: hidden;
    margin: 0;
  }
  
  /* Subtle shimmer effect on input */
  .message-input::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      120deg,
      transparent,
      rgba(255, 255, 255, 0.05),
      transparent
    );
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
  }
  
  .message-input:focus {
    border-color: rgba(94, 231, 223, 0.2);
    border-right-color: rgba(180, 144, 202, 0.2);
    border-bottom-color: rgba(180, 144, 202, 0.2);
    box-shadow: 
      0 0 0 4px rgba(94, 231, 223, 0.05),
      0 0 20px rgba(94, 231, 223, 0.05),
      0 0 0 1px rgba(255, 255, 255, 0.02);
    background: rgba(255, 255, 255, 0.07);
    transform: translateY(-1px);
  }
  
  .message-input:focus::before {
    opacity: 1;
  }
  
  .message-input::placeholder {
    color: rgba(255, 255, 255, 0.4);
    font-weight: 400;
  }
  
  .message-input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    filter: saturate(70%);
  }
  
  /* NextGen futuristic send button */
  .send-button {
    width: 48px;
    height: 48px;
    border-radius: 24px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: linear-gradient(135deg, 
      rgba(94, 231, 223, 0.15) 0%,
      rgba(180, 144, 202, 0.15) 100%);
    color: rgba(255, 255, 255, 0.85);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    backdrop-filter: var(--blur-light);
    position: relative;
    overflow: hidden;
    flex-shrink: 0;
    box-shadow: 
      0 2px 10px rgba(0, 0, 0, 0.1),
      0 0 0 1px rgba(255, 255, 255, 0.03);
  }
  
  /* Glowing effect */
  .send-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--mode-gradient);
    opacity: 0;
    transition: opacity 0.3s ease, transform 0.3s ease;
    z-index: 0;
    border-radius: 24px;
  }
  
  /* Ripple effect */
  .send-button::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 100px;
    height: 100px;
    background: radial-gradient(circle, 
      rgba(255, 255, 255, 0.3) 0%, 
      transparent 70%);
    border-radius: 50%;
    transform: translate(-50%, -50%) scale(0);
    opacity: 0;
    transition: transform 0.6s ease-out, opacity 0.6s ease-out;
    z-index: 0;
  }
  
  .send-button svg {
    position: relative;
    z-index: 1;
    width: 18px;
    height: 18px;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  
  .send-button.active {
    border-color: rgba(94, 231, 223, 0.2);
    color: rgba(255, 255, 255, 1);
    transform: translateY(-3px) scale(1.05);
    box-shadow: 
      0 10px 25px rgba(0, 0, 0, 0.1), 
      0 5px 10px rgba(94, 231, 223, 0.1),
      0 0 0 1px rgba(255, 255, 255, 0.05);
  }
  
  .send-button.active::before {
    opacity: 0.8;
  }
  
  .send-button.active svg {
    transform: scale(1.1) rotate(-10deg);
  }
  
  .send-button:hover:not(:disabled) {
    transform: translateY(-3px) scale(1.05);
    color: var(--text-primary);
    box-shadow: 
      0 15px 30px rgba(0, 0, 0, 0.1), 
      0 8px 15px rgba(94, 231, 223, 0.05),
      0 0 0 1px rgba(255, 255, 255, 0.05);
  }
  
  .send-button:hover:not(:disabled)::before {
    opacity: 0.5;
  }
  
  .send-button:hover:not(:disabled) svg {
    transform: scale(1.1);
  }
  
  .send-button:active {
    transform: translateY(0) scale(0.95);
    transition: all 0.1s ease-out;
  }
  
  .send-button:active::after {
    transform: translate(-50%, -50%) scale(1);
    opacity: 0.3;
  }
  
  .send-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
    filter: saturate(70%);
  }
  
  /* Mode dropdown */
  .mode-dropdown {
    position: absolute;
    top: -240px;
    left: 20px;
    background: rgba(35, 40, 65, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    width: 280px;
    padding: 8px;
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.2), 0 5px 15px rgba(0, 0, 0, 0.1);
    backdrop-filter: var(--blur-heavy);
    z-index: 100;
  }
  
  .mode-option {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    background: transparent;
    border: none;
    border-radius: 12px;
    cursor: pointer;
    transition: all var(--smooth-transition);
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
    padding: 0 20px 16px;
    animation: fade-in 0.5s ease;
  }
  
  @keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
  }
  
  .examples-title {
    font-size: 13px;
    color: var(--text-secondary);
    margin-bottom: 8px;
  }
  
  .examples-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .example-button {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 10px 16px;
    font-size: 13px;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all var(--smooth-transition);
    text-align: left;
    position: relative;
    overflow: hidden;
  }
  
  .example-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--mode-gradient);
    opacity: 0;
    transition: opacity 0.25s ease;
  }
  
  .example-button:hover {
    background: rgba(255, 255, 255, 0.1);
    color: var(--text-primary);
    transform: translateY(-1px);
  }
  
  .example-button:hover::before {
    opacity: 0.08;
  }
  
  /* Screen viewer overlay */
  .screen-viewer-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background: rgba(0, 0, 0, 0.8);
    backdrop-filter: blur(10px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10001;
  }
  
  /* Action buttons container */
  /* Icon button - shared styles for all compact buttons */
  .icon-button {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border-radius: 50%;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.15s ease;
    position: relative;
    padding: 0;
    opacity: 0.75;
    flex-shrink: 0;
    fill: none;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
  }
  
  /* Button interactions */
  .icon-button:hover {
    color: var(--text-primary);
    opacity: 1;
    transform: scale(1.05);
    background-color: rgba(255, 255, 255, 0.05);
  }
  
  .icon-button:active {
    transform: scale(0.95);
    background-color: rgba(255, 255, 255, 0.1);
  }
  
  .icon-button.active {
    color: var(--button-color, var(--accent-blue));
    opacity: 1;
  }
  
  /* Mode button specific */
  .icon-button.mode-button {
    font-size: 18px;
    margin-right: 2px;
  }
  
  .mode-emoji {
    line-height: 1;
  }
  
  /* Action group for buttons on the right */
  .action-group {
    display: flex;
    align-items: center;
    gap: 2px;
    margin-left: 2px;
  }
  
  /* Send button specific */
  .icon-button.send-button {
    color: var(--button-color, var(--accent-blue));
    opacity: 0.6;
  }
  
  .icon-button.send-button.active {
    opacity: 1;
  }
  
  .icon-button.send-button:hover {
    opacity: 1;
    transform: scale(1.05);
    background-color: rgba(var(--button-color-rgb, var(--accent-blue-rgb)), 0.1);
  }
  
  /* Speech button styling */
  .icon-button.speech-button {
    background: transparent;
    border: none;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  /* Legacy action buttons (now hidden) */
  .action-buttons {
    display: none; /* Hide the old action buttons */
  }
  
  /* Voice and call buttons (legacy) */
  .action-button {
    width: 36px;
    height: 36px;
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-secondary);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    position: relative;
    overflow: hidden;
  }
  
  .action-button::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    opacity: 0;
    transition: opacity 0.25s ease;
    z-index: 0;
  }
  
  .action-button svg {
    position: relative;
    z-index: 1;
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  
  .action-button:hover {
    transform: translateY(-2px);
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.1);
  }
  
  .action-button:hover svg {
    transform: scale(1.1);
  }
  
  .action-button:active {
    transform: translateY(0) scale(0.95);
    transition: all 0.1s ease-out;
  }
  
  /* Voice button specific styles */
  .voice-button::before {
    background: linear-gradient(135deg, 
      rgba(255, 69, 58, 0.15) 0%, 
      rgba(255, 159, 10, 0.15) 100%);
  }
  
  .voice-button:hover {
    border-color: rgba(255, 69, 58, 0.2);
  }
  
  .voice-button.active {
    background: rgba(255, 69, 58, 0.15);
    border-color: rgba(255, 69, 58, 0.3);
    color: rgb(255, 69, 58);
    animation: pulse-recording 1.5s infinite;
  }
  
  @keyframes pulse-recording {
    0% { box-shadow: 0 0 0 0 rgba(255, 69, 58, 0.4); }
    70% { box-shadow: 0 0 0 6px rgba(255, 69, 58, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 69, 58, 0); }
  }
  
  /* Call button specific styles */
  .call-button::before {
    background: linear-gradient(135deg, 
      rgba(48, 209, 88, 0.15) 0%, 
      rgba(94, 231, 223, 0.15) 100%);
  }
  
  .call-button:hover {
    border-color: rgba(48, 209, 88, 0.2);
  }
  
  .call-button.active {
    background: rgba(48, 209, 88, 0.15);
    border-color: rgba(48, 209, 88, 0.3);
    color: rgb(48, 209, 88);
    animation: pulse-call 1.5s infinite;
  }
  
  @keyframes pulse-call {
    0% { box-shadow: 0 0 0 0 rgba(48, 209, 88, 0.4); }
    70% { box-shadow: 0 0 0 6px rgba(48, 209, 88, 0); }
    100% { box-shadow: 0 0 0 0 rgba(48, 209, 88, 0); }
  }
  
  /* Audio player styling */
  .audio-player {
    margin-top: 10px;
    border-radius: 12px;
    overflow: hidden;
    background: rgba(0, 0, 0, 0.2);
    padding: 2px;
  }
  
  .audio-player audio {
    width: 100%;
    height: 36px;
    border-radius: 12px;
  }
  
  /* Active indicator for recording and calls */
  .active-indicator {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    padding: 6px 10px;
    background: rgba(0, 0, 0, 0.15);
    border-radius: 12px;
    font-size: 12px;
  }
  
  .pulse-dot {
    width: 8px;
    height: 8px;
    border-radius: 4px;
    animation: pulse-indicator 1.5s infinite;
  }
  
  .indicator-text.recording ~ .pulse-dot {
    background: rgb(255, 69, 58);
    box-shadow: 0 0 8px rgba(255, 69, 58, 0.6);
  }
  
  .indicator-text.call ~ .pulse-dot {
    background: rgb(48, 209, 88);
    box-shadow: 0 0 8px rgba(48, 209, 88, 0.6);
  }
  
  .indicator-text.recording {
    color: rgb(255, 159, 10);
  }
  
  .indicator-text.call {
    color: rgb(48, 209, 88);
  }
  
  @keyframes pulse-indicator {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.3); opacity: 0.7; }
    100% { transform: scale(1); opacity: 1; }
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
      font-size: 13px;
    }
    
    .mode-name {
      display: none;
    }
    
    .mode-toggle {
      padding: 6px;
      width: 30px;
      justify-content: center;
    }
    
    .action-buttons {
      position: absolute;
      bottom: -45px;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(35, 40, 65, 0.8);
      border-radius: 20px;
      padding: 4px 10px;
      backdrop-filter: var(--blur-medium);
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }
  }
  
  /* Welcome message styling */
  .welcome-message {
    padding: 16px;
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
    border-radius: 12px;
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    animation: welcomeFade 0.5s ease-out;
    margin-bottom: 16px;
  }
  
  .welcome-header {
    text-align: left;
    margin-bottom: 16px;
  }
  
  .welcome-icon {
    font-size: 32px;
    margin-bottom: 8px;
    animation: float 3s infinite ease-in-out;
  }
  
  .welcome-subtitle {
    color: var(--text-secondary);
    font-size: 14px;
    margin-top: 4px;
  }
  
  .features-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    margin-bottom: 32px;
  }
  
  .feature-item {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 16px;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }
  
  .feature-item:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  .feature-icon {
    font-size: 24px;
    background: rgba(255, 255, 255, 0.1);
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 10px;
  }
  
  .feature-content h3 {
    margin: 0 0 4px 0;
    font-size: 16px;
    color: var(--text-primary);
  }
  
  .feature-content p {
    margin: 0;
    font-size: 14px;
    color: var(--text-secondary);
    line-height: 1.4;
  }
  
  .quick-start {
    text-align: center;
    margin-top: 24px;
  }
  
  .quick-start h3 {
    margin: 0 0 16px 0;
    font-size: 18px;
    color: var(--text-primary);
  }
  
  .quick-start-buttons {
    display: flex;
    gap: 12px;
    justify-content: center;
  }
  
  .quick-start-btn {
    background: var(--primary-color);
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    cursor: pointer;
    transition: transform 0.2s ease, background 0.2s ease;
  }
  
  .quick-start-btn:hover {
    transform: translateY(-1px);
    background: var(--primary-dark);
  }
  
  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
  }
  
  @keyframes welcomeFade {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
  
  @media (max-width: 480px) {
    .features-grid {
      grid-template-columns: 1fr;
    }
  
    .quick-start-buttons {
      flex-direction: column;
    }
  
    .quick-start-btn {
      width: 100%;
    }
  }

  .welcome-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
    padding: 16px;
  }

  .welcome-icon-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 16px;
    cursor: pointer;
    transition: all 0.3s ease;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .welcome-icon-item:hover {
    transform: translateY(-2px);
    background: rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.2);
  }

  .welcome-icon-item .icon {
    font-size: 32px;
    margin-bottom: 8px;
  }

  .welcome-icon-item .label {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
    font-weight: 500;
  }

  .mic-permission-btn {
    margin-bottom: 10px;
    background: #f1f1f1;
    color: #333;
    border: 1px solid #ccc;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 14px;
    cursor: pointer;
    transition: background 0.2s;
  }
  .mic-permission-btn:hover {
    background: #e0e0e0;
  }

  /* Next-Gen Automation Plan Card Styles */
  .automation-plan-card {
    background: linear-gradient(145deg, rgba(25, 25, 35, 0.95) 0%, rgba(18, 18, 28, 0.98) 100%);
    border-radius: 18px;
    box-shadow: 
      0 10px 30px rgba(0, 0, 0, 0.35), 
      0 4px 10px rgba(0, 0, 0, 0.25),
      0 0 0 1px rgba(255, 255, 255, 0.08);
    margin: 18px 0;
    overflow: hidden;
    backdrop-filter: blur(12px);
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    max-width: 100%;
    position: relative;
    width: 100%;
    isolation: isolate;
  }

  .automation-plan-card:hover {
    transform: translateY(-3px) scale(1.01);
    box-shadow: 
      0 15px 40px rgba(0, 0, 0, 0.45), 
      0 5px 15px rgba(0, 0, 0, 0.3),
      0 0 0 1px rgba(255, 255, 255, 0.12);
  }

  .automation-plan-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 200px;
    background: linear-gradient(180deg, 
      rgba(120, 170, 255, 0.05) 0%, 
      rgba(90, 140, 255, 0.02) 50%,
      transparent 100%);
    pointer-events: none;
    opacity: 0.7;
  }

  .plan-header {
    display: flex;
    align-items: center;
    padding: 16px 20px;
    background: rgba(30, 30, 50, 0.65);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    position: relative;
    z-index: 1;
  }

  .plan-icon {
    font-size: 28px;
    margin-right: 14px;
    text-shadow: 0 2px 8px rgba(255, 255, 255, 0.15);
  }

  .plan-title {
    flex: 1;
  }

  .plan-title h3 {
    margin: 0;
    font-size: 18px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.98);
    letter-spacing: 0.5px;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }

  .plan-id {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
    margin-top: 4px;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
    opacity: 0.8;
  }

  .plan-content {
    padding: 0;
    background: rgba(25, 25, 35, 0.5);
    position: relative;
  }

  .divider {
    height: 1px;
    background: linear-gradient(
      90deg, 
      rgba(255, 255, 255, 0.01) 0%, 
      rgba(255, 255, 255, 0.07) 50%,
      rgba(255, 255, 255, 0.01) 100%
    );
    margin: 0;
  }

  .plan-details {
    padding: 16px 20px;
  }

  .detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 14px;
    width: 100%;
  }

  .detail-item {
    display: flex;
    background: rgba(255, 255, 255, 0.04);
    border-radius: 12px;
    padding: 12px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.3s ease;
  }

  .detail-item:hover {
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255, 255, 255, 0.08);
    transform: translateY(-1px);
  }

  .detail-icon {
    font-size: 18px;
    margin-right: 12px;
    opacity: 0.95;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  }

  .detail-content {
    flex: 1;
    overflow: hidden;
  }

  .detail-label {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: 5px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .detail-value {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.95);
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    line-height: 1.3;
    max-width: 100%;
  }

  .plan-steps {
    padding: 16px 20px;
  }

  .steps-header {
    display: flex;
    align-items: center;
    margin-bottom: 14px;
  }

  .steps-icon {
    font-size: 18px;
    margin-right: 10px;
    text-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  }

  .steps-title {
    font-size: 15px;
    font-weight: 700;
    color: rgba(255, 255, 255, 0.9);
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }

  .steps-list {
    margin-left: 8px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    width: 100%;
    overflow: hidden;
  }

  .step-item {
    display: flex;
    align-items: flex-start;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 10px;
    padding: 10px 12px;
    border: 1px solid rgba(255, 255, 255, 0.04);
    transition: all 0.3s ease;
  }

  .step-item:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.08);
    transform: translateX(2px);
  }

  .step-number {
    background: rgba(120, 160, 255, 0.2);
    color: rgba(255, 255, 255, 0.9);
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    margin-right: 10px;
    flex-shrink: 0;
    font-weight: 700;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
  }

  .step-content {
    display: flex;
    align-items: flex-start;
    flex: 1;
    width: calc(100% - 40px);
    overflow: hidden;
  }

  .step-indicator {
    margin-right: 8px;
    font-size: 16px;
    padding-top: 1px;
  }

  .step-text {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.9);
    line-height: 1.5;
    flex: 1;
    font-weight: 500;
    overflow-wrap: break-word;
    word-wrap: break-word;
    word-break: break-word;
    hyphens: auto;
    max-width: 100%;
  }

  .plan-system {
    display: flex;
    align-items: center;
    padding: 14px 20px;
  }

  .system-icon {
    font-size: 16px;
    margin-right: 10px;
    opacity: 0.85;
    color: rgba(180, 140, 255, 0.9);
  }

  .system-text {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.75);
    font-style: italic;
    font-weight: 500;
  }

  .plan-footer {
    padding: 16px 20px;
    background: rgba(20, 20, 35, 0.6);
    border-top: 1px solid rgba(255, 255, 255, 0.06);
  }

  .action-buttons {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .action-button {
    padding: 10px;
    border-radius: 12px;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    position: relative;
    overflow: hidden;
  }

  .action-button::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(to bottom, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0) 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
  }

  .action-button:hover {
    transform: translateY(-2px);
  }

  .action-button:hover::after {
    opacity: 1;
  }

  .action-button:active {
    transform: translateY(1px);
  }

  .action-button .button-icon {
    margin-right: 8px;
    font-size: 16px;
  }

  .action-button.execute {
    background: linear-gradient(145deg, #34c759 0%, #28a745 100%);
    color: #ffffff;
    box-shadow: 0 4px 12px rgba(52, 199, 89, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .action-button.execute:hover {
    box-shadow: 0 6px 16px rgba(52, 199, 89, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }

  .action-button.simulate {
    background: linear-gradient(145deg, #5ac8fa 0%, #0a84ff 100%);
    color: #ffffff;
    box-shadow: 0 4px 12px rgba(10, 132, 255, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .action-button.simulate:hover {
    box-shadow: 0 6px 16px rgba(10, 132, 255, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }

  .action-button.modify {
    background: linear-gradient(145deg, #ff9f0a 0%, #fd7e14 100%);
    color: #ffffff;
    box-shadow: 0 4px 12px rgba(255, 149, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .action-button.modify:hover {
    box-shadow: 0 6px 16px rgba(255, 149, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }

  .action-button.cancel {
    background: linear-gradient(145deg, #ff453a 0%, #dc3545 100%);
    color: #ffffff;
    box-shadow: 0 4px 12px rgba(255, 59, 48, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .action-button.cancel:hover {
    box-shadow: 0 6px 16px rgba(255, 59, 48, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
</style>