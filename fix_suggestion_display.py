#!/usr/bin/env python3
"""
Simple and targeted fix for suggestion display in NextGenAppleChatWidget.svelte
"""

import re
import os
import sys
import shutil
from datetime import datetime

# Path to the component
COMPONENT_PATH = "/Users/segevbin/Desktop/SensAI/Aiayer/overlay/src/components/NextGenAppleChatWidget.svelte"

def backup_file(file_path):
    """Create a backup of the file"""
    timestamp = int(datetime.now().timestamp())
    backup_path = f"{file_path}.bak.{timestamp}"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup at {backup_path}")
    return backup_path

def fix_suggestion_handler():
    """Fix the suggestion handler in the component"""
    # Backup the file first
    backup_file(COMPONENT_PATH)
    
    # Read the file
    with open(COMPONENT_PATH, 'r') as f:
        content = f.read()
    
    # Find the handleBackendMessage function
    handle_backend_pattern = r'function handleBackendMessage\(data\) \{.*?// Handle suggestion messages.*?if \(data\.type === \'suggestion\'.*?\{.*?return;.*?\}'
    suggestion_handler = re.search(handle_backend_pattern, content, re.DOTALL)
    
    if not suggestion_handler:
        print("Couldn't find the suggestion handler section in the file")
        return False
    
    # Extract the original suggestion handler code
    original_code = suggestion_handler.group(0)
    
    # Create a replacement with enhanced suggestion handling
    replacement_code = """function handleBackendMessage(data) {
    console.log('🎯 Smart Progressive message received:', data);
    
    if (data.type === 'connection_established') {
      console.log('🔗 Smart Progressive connection established:', data.features);
      return;
    }
    
    if (data.type === 'registration_success') {
      console.log('📋 Registration successful');
      return;
    }
    
    // Handle progressive updates with typing indicators
    if (data.type === 'progress_update') {
      console.log('⚡ Progress update:', data.stage);
      
      // Mode-specific typing messages
      const modeTypingMessages = {
        'Ask': [
          'Analyzing your question...',
          'Gathering relevant information...',
          'Processing context and background...',
          'Formulating comprehensive response...'
        ],
        'Agent': [
          'Planning task execution...',
          'Analyzing workflow requirements...',
          'Generating step-by-step guidance...',
          'Optimizing automation strategy...'
        ],
        'Suggest': [
          'Evaluating current situation...',
          'Identifying optimization opportunities...',
          'Generating recommendations...',
          'Considering best practices...'
        ],
        'Creative': [
          'Exploring creative possibilities...',
          'Generating innovative ideas...',
          'Brainstorming unique approaches...',
          'Inspiring creative solutions...'
        ]
      };
      
      // Update typing indicator with mode-specific progress or use data.stage
      if (data.stage) {
        typingMessage = data.stage;
      } else {
        const modeMessages = modeTypingMessages[currentMode] || ['AI is thinking...'];
        typingMessage = modeMessages[Math.floor(Math.random() * modeMessages.length)];
      }
      
      // Keep typing indicator visible
      if (!isTyping) {
        showTypingIndicator();
      }
      
      // Play subtle progress sound
      playSound('progress-update');
      return;
    }
    
    // Handle final response
    if ((data.success !== undefined && data.response) || data.type === 'final_response') {
      hideTypingIndicator();
      playSound('message-received');
      
      // Check if this is an Agent mode response with interactive buttons (NEW FORMAT)
      if (data.interactive && data.buttons && data.buttons.length > 0 && currentMode === 'Agent') {
        console.log('🤖 Agent response with interactive buttons:', data);
        
        // Add message with interactive buttons
        const assistantMessage = {
          id: Date.now(),
          type: 'assistant',
          content: data.response,
          timestamp: new Date(),
          confidence: data.confidence || 1.0,
          mode: data.mode || currentMode,
          interactive: true,
          buttons: data.buttons,
          plan_id: data.plan_id,
          requires_approval: data.requires_approval
        };
        
        messages = [...messages, assistantMessage];
        scrollToBottom();
        return;
      }
      
      // Check if this is an Agent mode response requiring confirmation (OLD FORMAT)
      if (data.requiresConfirmation && data.agentSessionId && currentMode === 'Agent') {
        console.log('🤖 Agent response with confirmation buttons:', data);
        
        pendingConfirmation = {
          sessionId: data.agentSessionId,
          response: data.response,
          confidence: data.confidence || 0.0,
          riskLevel: data.riskLevel || 'medium',
          estimatedDuration: data.estimatedDuration || '30 seconds',
          executionPlan: data.executionPlan || {}
        };
        
        // Add message with confirmation buttons
        const assistantMessage = {
          id: Date.now(),
          type: 'assistant',
          content: data.response,
          timestamp: new Date(),
          confidence: data.confidence || 1.0,
          mode: data.mode || currentMode,
          requiresConfirmation: true,
          agentSessionId: data.agentSessionId,
          riskLevel: data.riskLevel,
          estimatedDuration: data.estimatedDuration,
          executionPlan: data.executionPlan
        };
        
        messages = [...messages, assistantMessage];
        scrollToBottom();
        return;
      }
      
      // Enhanced message processing with mode-specific formatting
      const processedContent = processResponseByMode(data.response || 'No response received', data.mode || currentMode);
      
      const assistantMessage = {
        id: Date.now(),
        type: 'assistant',
        content: processedContent,
        timestamp: new Date(),
        confidence: data.confidence || 1.0,
        mode: data.mode || currentMode,
        processingTime: data.processing_time || 0,
        resources: data.resources || [],
        enterpriseValidated: data.enterprise_validated || false,
        processingWorker: data.processing_worker || 'unknown',
        source: data.source || 'unknown',
        modeSpecific: true  // Flag to indicate enhanced processing
      };
      
      messages = [...messages, assistantMessage];
      
      // Mode-specific post-processing actions
      performModeSpecificActions(assistantMessage);
      
      scrollToBottom();
      
    } else if (data.type === 'error' || data.type === 'error_response') {
      hideTypingIndicator();
      showError(data.error || data.message || 'An error occurred');
      playSound('error');
    }
    
    // Handle Agent mode execution progress
    if (data.type === 'execution_progress' && progressVisible) {
      console.log('🚀 Execution progress update:', data);
      currentProgress = {
        progress: data.progress || 0,
        currentStep: data.currentStep || '',
        stepNumber: data.stepNumber || 0,
        totalSteps: data.totalSteps || 0
      };
      playSound('progress-update');
    }
    
    // Handle Agent mode execution completion
    if (data.type === 'execution_complete') {
      console.log('✅ Execution completed:', data);
      progressVisible = false;
      pendingConfirmation = null;
      
      // Add completion message
      const completionMessage = {
        id: Date.now(),
        type: 'assistant',
        content: `✅ **Task Completed Successfully**\n\n${data.result || 'The automation task has been executed.'}`,
        timestamp: new Date(),
        confidence: 1.0,
        mode: 'Agent',
        isCompletion: true
      };
      
      messages = [...messages, completionMessage];
      scrollToBottom();
      playSound('task-complete');
    }
    
    // Handle suggestion messages - NEW ENHANCED HANDLER
    if (data.type === 'suggestion' || (data.mode === 'SUGGEST' && data.notification) || data.notification) {
      console.log('💡 Received suggestion:', data);
      
      // Play notification sound if enabled
      if ((data.play_sound || data.playSound) && soundEnabled) {
        playSound('notification');
      }
      
      // Extract the response and buttons from the data
      const responseText = data.response || data.message || data.content || '';
      const buttons = data.buttons || [];
      const importance = data.importance || 'high';
      
      // Add the suggestion to messages with a unique ID
      const suggestionMessage = {
        id: Date.now(),
        type: 'suggestion',
        content: responseText,
        buttons: buttons,
        timestamp: new Date(),
        importance: importance,
        plan_id: data.plan_id || `suggestion_${Date.now()}`
      };
      
      console.log('💡 Adding suggestion message:', suggestionMessage);
      messages = [...messages, suggestionMessage];
      
      // Scroll to bottom to show the new message
      setTimeout(() => {
        if (chatContainer) {
          chatContainer.scrollTop = chatContainer.scrollHeight;
        }
      }, 100);
      
      return;
    }
  }"""
    
    # Replace the original code with the fixed version
    fixed_content = content.replace(original_code, replacement_code)
    
    # Check if the content has been updated
    if fixed_content == content:
        print("No changes were made to the file")
        return False
    
    # Write the updated content back to the file
    with open(COMPONENT_PATH, 'w') as f:
        f.write(fixed_content)
    
    print("Successfully updated the suggestion handler!")
    return True

if __name__ == "__main__":
    print("\n=== OVERLAY SUGGESTION DISPLAY FIX ===\n")
    
    if not os.path.exists(COMPONENT_PATH):
        print(f"Error: Component file not found at {COMPONENT_PATH}")
        sys.exit(1)
    
    success = fix_suggestion_handler()
    
    if success:
        print("\nFix applied successfully!")
        print("Next steps:")
        print("1. Run 'cd /Users/segevbin/Desktop/SensAI/Aiayer/overlay && npm run build'")
        print("2. Restart the overlay application")
        print("3. Test with 'python3 fixed_nextgen_suggestion_handler.py'")
    else:
        print("\nFailed to apply the fix")
        print("Please check the component file manually")
    
    print("\n===================================\n")