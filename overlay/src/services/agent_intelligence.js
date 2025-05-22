// Agent Intelligence Service
// Integrates screen analysis, LLAVA vision, memory context, and proactive suggestions

class AgentIntelligenceService {
    constructor(bridgeService) {
        this.bridge = bridgeService;
        this.isAnalyzing = false;
        this.analysisInterval = null;
        this.lastScreenshot = null;
        this.lastAnalysis = null;
        this.analysisHistory = [];
        this.maxHistorySize = 10;
        
        // Configuration
        this.config = {
            analysisIntervalMs: 5000, // Analyze every 5 seconds
            confidenceThreshold: 0.7, // Only suggest actions above 70% confidence
            enableProactiveMode: true,
            enableScreenCapture: true,
            llavaEndpoint: 'http://localhost:11434/api/generate', // Ollama LLAVA endpoint
        };
        
        this.setupEventListeners();
        console.log('🤖 Agent Intelligence Service initialized');
    }
    
    setupEventListeners() {
        // Listen for bridge messages
        this.bridge.on('message', this.handleBridgeMessage.bind(this));
        
        // Listen for user activity (mouse, keyboard)
        document.addEventListener('click', this.onUserActivity.bind(this));
        document.addEventListener('keydown', this.onUserActivity.bind(this));
        
        // Start proactive analysis if enabled
        if (this.config.enableProactiveMode) {
            this.startProactiveAnalysis();
        }
    }
    
    handleBridgeMessage(message) {
        const { type, payload } = message;
        
        switch (type) {
            case 'query_response':
                // User got a response, analyze what they might want to do next
                this.analyzeContextAfterResponse(payload);
                break;
                
            case 'context_update':
                // Screen context changed, trigger analysis
                this.triggerAnalysis();
                break;
                
            case 'agent_enable_proactive':
                this.startProactiveAnalysis();
                break;
                
            case 'agent_disable_proactive':
                this.stopProactiveAnalysis();
                break;
        }
    }
    
    onUserActivity(event) {
        // Debounced analysis trigger on user activity
        clearTimeout(this.activityTimeout);
        this.activityTimeout = setTimeout(() => {
            this.triggerAnalysis();
        }, 2000); // Wait 2 seconds after user stops activity
    }
    
    startProactiveAnalysis() {
        if (this.analysisInterval) return;
        
        console.log('🎯 Starting proactive agent analysis');
        this.analysisInterval = setInterval(() => {
            this.performIntelligentAnalysis();
        }, this.config.analysisIntervalMs);
        
        // Do initial analysis
        this.performIntelligentAnalysis();
    }
    
    stopProactiveAnalysis() {
        if (this.analysisInterval) {
            clearInterval(this.analysisInterval);
            this.analysisInterval = null;
            console.log('⏸️ Stopped proactive agent analysis');
        }
    }
    
    triggerAnalysis() {
        if (!this.isAnalyzing) {
            this.performIntelligentAnalysis();
        }
    }
    
    async performIntelligentAnalysis() {
        if (this.isAnalyzing) return;
        
        this.isAnalyzing = true;
        
        try {
            console.log('🔍 Performing intelligent screen analysis...');
            
            // Step 1: Capture current screen
            const screenshot = await this.captureScreen();
            if (!screenshot) {
                console.warn('Failed to capture screen');
                return;
            }
            
            // Step 2: Get current context from memory
            const context = await this.getCurrentContext();
            
            // Step 3: Get recent conversation history
            const conversationHistory = await this.getConversationHistory();
            
            // Step 4: Analyze screen with LLAVA
            const screenAnalysis = await this.analyzeScreenWithLLAVA(screenshot, context, conversationHistory);
            
            // Step 5: Generate proactive suggestions
            const suggestions = await this.generateProactiveSuggestions(screenAnalysis, context);
            
            // Step 6: Send suggestions to chat if confidence is high enough
            if (suggestions.length > 0) {
                this.sendProactiveSuggestions(suggestions, screenAnalysis);
            }
            
            // Store analysis for future reference
            this.storeAnalysis(screenAnalysis, suggestions);
            
        } catch (error) {
            console.error('Error in intelligent analysis:', error);
        } finally {
            this.isAnalyzing = false;
        }
    }
    
    async captureScreen() {
        try {
            // Use Tauri API to capture screen
            const { invoke } = window.__TAURI__;
            const screenshot = await invoke('capture_screen');
            
            this.lastScreenshot = {
                data: screenshot,
                timestamp: Date.now(),
                width: screen.width,
                height: screen.height
            };
            
            return screenshot;
        } catch (error) {
            console.error('Failed to capture screen:', error);
            return null;
        }
    }
    
    async getCurrentContext() {
        try {
            // Get context from bridge
            const response = await this.bridge.sendMessage({
                type: 'get_full_context',
                payload: {
                    include_memory: true,
                    include_sensors: true,
                    include_process_info: true
                }
            });
            
            return response.payload || {};
        } catch (error) {
            console.error('Failed to get context:', error);
            return {};
        }
    }
    
    async getConversationHistory() {
        try {
            // Get recent conversation from bridge
            const response = await this.bridge.sendMessage({
                type: 'get_conversation_history',
                payload: {
                    limit: 5 // Last 5 messages
                }
            });
            
            return response.payload?.messages || [];
        } catch (error) {
            console.error('Failed to get conversation history:', error);
            return [];
        }
    }
    
    async analyzeScreenWithLLAVA(screenshot, context, conversationHistory) {
        try {
            const prompt = this.buildLLAVAPrompt(context, conversationHistory);
            
            const response = await fetch(this.config.llavaEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: 'llava',
                    prompt: prompt,
                    images: [screenshot],
                    stream: false,
                    options: {
                        temperature: 0.3,
                        top_p: 0.9
                    }
                })
            });
            
            const result = await response.json();
            
            const analysis = {
                timestamp: Date.now(),
                visual_elements: this.extractVisualElements(result.response),
                ui_state: this.extractUIState(result.response),
                possible_actions: this.extractPossibleActions(result.response),
                user_intent_prediction: this.extractUserIntent(result.response),
                confidence_score: this.calculateConfidence(result.response),
                raw_response: result.response
            };
            
            console.log('🎯 LLAVA Analysis:', analysis);
            return analysis;
            
        } catch (error) {
            console.error('Failed to analyze screen with LLAVA:', error);
            return {
                timestamp: Date.now(),
                error: error.message,
                confidence_score: 0
            };
        }
    }
    
    buildLLAVAPrompt(context, conversationHistory) {
        const conversationContext = conversationHistory.length > 0 
            ? `Recent conversation:\n${conversationHistory.map(msg => `${msg.role}: ${msg.content}`).join('\n')}\n\n`
            : '';
            
        const memoryContext = context.memory_summary 
            ? `User's context: ${context.memory_summary}\n\n`
            : '';
            
        const activeApp = context.active_app 
            ? `Currently active application: ${context.active_app}\n\n`
            : '';
        
        return `You are an AI assistant analyzing a user's screen to provide intelligent automation suggestions.

${memoryContext}${activeApp}${conversationContext}

Please analyze this screenshot and provide:

1. **Visual Elements**: List all UI elements you can see (buttons, forms, text fields, menus, etc.) with their approximate positions
2. **Current UI State**: Describe what the user is currently doing or looking at
3. **Possible Actions**: What actions could the user take next (click buttons, fill forms, navigate, etc.)
4. **User Intent Prediction**: Based on the context and conversation, what do you think the user wants to accomplish?
5. **Automation Opportunities**: Specific tasks that could be automated (with confidence level 0-100%)
6. **Actionable Details**: For each suggested action, provide exact details like:
   - Button text to click
   - Form fields to fill and with what information
   - Navigation steps
   - Text to type

Be specific and actionable. Focus on what the user can do right now on this screen.

Format your response as structured analysis that can be parsed for automation suggestions.`;
    }
    
    extractVisualElements(response) {
        // Parse LLAVA response to extract UI elements
        const elements = [];
        const elementRegex = /(?:button|link|field|input|menu|icon)[^.]*?["']([^"']+)["']|(?:button|link|field|input|menu|icon)\s*:\s*([^.\n]+)/gi;
        
        let match;
        while ((match = elementRegex.exec(response)) !== null) {
            elements.push({
                type: match[0].split(/\s|:/)[0].toLowerCase(),
                text: match[1] || match[2],
                position: 'detected' // Would need more sophisticated parsing
            });
        }
        
        return elements;
    }
    
    extractUIState(response) {
        // Extract current UI state description
        const stateMatch = response.match(/(?:current|currently|user is)[^.]*?(?:doing|looking at|viewing)[^.]*?\./i);
        return stateMatch ? stateMatch[0] : 'UI state unclear';
    }
    
    extractPossibleActions(response) {
        // Extract possible actions
        const actions = [];
        const actionRegex = /(?:could|can|might|should)\s+(?:click|fill|navigate|type|select)[^.]*?\./gi;
        
        let match;
        while ((match = actionRegex.exec(response)) !== null) {
            actions.push(match[0]);
        }
        
        return actions;
    }
    
    extractUserIntent(response) {
        // Extract predicted user intent
        const intentMatch = response.match(/(?:user wants|intends to|trying to|goal is)[^.]*?\./i);
        return intentMatch ? intentMatch[0] : 'Intent unclear';
    }
    
    calculateConfidence(response) {
        // Calculate confidence based on response clarity and specificity
        let confidence = 0.5; // Base confidence
        
        // Check for specific UI elements
        if (response.includes('button') || response.includes('field') || response.includes('form')) {
            confidence += 0.2;
        }
        
        // Check for specific actions
        if (response.includes('click') || response.includes('fill') || response.includes('type')) {
            confidence += 0.2;
        }
        
        // Check for confidence indicators in response
        const confidenceMatch = response.match(/confidence[^0-9]*(\d+)/i);
        if (confidenceMatch) {
            confidence = Math.max(confidence, parseInt(confidenceMatch[1]) / 100);
        }
        
        return Math.min(confidence, 1.0);
    }
    
    async generateProactiveSuggestions(screenAnalysis, context) {
        const suggestions = [];
        
        if (screenAnalysis.confidence_score < this.config.confidenceThreshold) {
            return suggestions; // Don't suggest if confidence is too low
        }
        
        // Generate suggestions based on detected elements and user intent
        for (const element of screenAnalysis.visual_elements || []) {
            if (element.type === 'button' && screenAnalysis.confidence_score > 0.8) {
                suggestions.push({
                    id: `click_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                    type: 'click',
                    title: `Click "${element.text}"`,
                    description: `I can click the "${element.text}" button for you`,
                    confidence: screenAnalysis.confidence_score,
                    action_details: {
                        element_text: element.text,
                        element_type: element.type,
                        position: element.position
                    },
                    requires_confirmation: true
                });
            }
            
            if (element.type === 'field' || element.type === 'input') {
                suggestions.push({
                    id: `fill_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                    type: 'fill_field',
                    title: `Fill "${element.text}" field`,
                    description: `I can help fill out the "${element.text}" field based on your profile`,
                    confidence: Math.max(screenAnalysis.confidence_score - 0.1, 0.6),
                    action_details: {
                        field_name: element.text,
                        suggested_value: this.getSuggestedFieldValue(element.text, context)
                    },
                    requires_confirmation: true
                });
            }
        }
        
        return suggestions;
    }
    
    getSuggestedFieldValue(fieldName, context) {
        // Suggest values based on field name and user context
        const fieldLower = fieldName.toLowerCase();
        
        if (fieldLower.includes('name')) {
            return context.user_profile?.name || '[Your name]';
        }
        if (fieldLower.includes('email')) {
            return context.user_profile?.email || '[Your email]';
        }
        if (fieldLower.includes('phone')) {
            return context.user_profile?.phone || '[Your phone]';
        }
        
        return '[Smart suggestion]';
    }
    
    sendProactiveSuggestions(suggestions, screenAnalysis) {
        const proactiveMessage = {
            type: 'agent_proactive_suggestion',
            payload: {
                message: this.formatProactiveMessage(suggestions, screenAnalysis),
                suggestions: suggestions,
                screen_analysis: {
                    ui_state: screenAnalysis.ui_state,
                    confidence: screenAnalysis.confidence_score,
                    timestamp: screenAnalysis.timestamp
                },
                display_type: 'proactive_notification'
            }
        };
        
        // Send to chat overlay as backend push
        this.bridge.sendMessage(proactiveMessage);
        
        console.log('🔮 Sent proactive suggestions:', suggestions.length);
    }
    
    formatProactiveMessage(suggestions, screenAnalysis) {
        const confidencePercent = Math.round(screenAnalysis.confidence_score * 100);
        const summary = screenAnalysis.ui_state || 'Analyzing current screen';
        
        let message = `🤖 **Agent Insight** (${confidencePercent}% confidence)\n\n`;
        message += `📊 **What I see**: ${summary}\n\n`;
        
        if (suggestions.length > 0) {
            message += `💡 **I can help with**:\n`;
            suggestions.forEach((suggestion, index) => {
                const confPercent = Math.round(suggestion.confidence * 100);
                message += `${index + 1}. ${suggestion.title} (${confPercent}% confidence)\n`;
            });
            message += `\nWould you like me to perform any of these actions?`;
        } else {
            message += `🔍 Monitoring for automation opportunities...`;
        }
        
        return message;
    }
    
    storeAnalysis(screenAnalysis, suggestions) {
        this.lastAnalysis = {
            analysis: screenAnalysis,
            suggestions: suggestions,
            timestamp: Date.now()
        };
        
        // Add to history
        this.analysisHistory.push(this.lastAnalysis);
        
        // Trim history
        if (this.analysisHistory.length > this.maxHistorySize) {
            this.analysisHistory = this.analysisHistory.slice(-this.maxHistorySize);
        }
    }
    
    analyzeContextAfterResponse(responsePayload) {
        // User just got a response, analyze what they might want to do next
        setTimeout(() => {
            this.triggerAnalysis();
        }, 1000); // Wait 1 second for UI to update
    }
    
    // Public API methods
    enableProactiveMode() {
        this.config.enableProactiveMode = true;
        this.startProactiveAnalysis();
    }
    
    disableProactiveMode() {
        this.config.enableProactiveMode = false;
        this.stopProactiveAnalysis();
    }
    
    setConfidenceThreshold(threshold) {
        this.config.confidenceThreshold = Math.max(0, Math.min(1, threshold));
    }
    
    getLastAnalysis() {
        return this.lastAnalysis;
    }
    
    getAnalysisHistory() {
        return this.analysisHistory;
    }
}

export default AgentIntelligenceService;