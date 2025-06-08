/**
 * NextGenAppleChatWidget Suggestion Notification Patch
 * 
 * This file contains the patch code to fix the issue with suggestions not appearing
 * with sound notifications in the NextGen overlay. To apply this patch:
 * 
 * 1. Open /Users/segevbin/Desktop/SensAI/Aiayer/overlay/src/components/NextGenAppleChatWidget.svelte
 * 2. Find the handleBackendMessage function
 * 3. Add the new suggestion notification handling code in the appropriate location
 */

// --------------------------------
// Add this function after playModeSound
// --------------------------------

/**
 * Specialized function for playing suggestion notifications with proper volume
 */
const playSuggestionNotification = () => {
  if (!soundEnabled) return;
  try {
    // First try to use the notification sound
    const audio = new Audio(`/sounds/notification.mp3`);
    audio.volume = 0.1; // Louder than regular sounds but not too loud
    audio.currentTime = 0;
    
    audio.play().catch(() => {
      // Fallback to .wav format if .mp3 fails
      try {
        const fallbackAudio = new Audio(`/sounds/notification.wav`);
        fallbackAudio.volume = 0.1;
        fallbackAudio.play().catch(() => {
          // If notification sound fails, try message-received sound
          try {
            const secondFallback = new Audio(`/sounds/message-received.mp3`);
            secondFallback.volume = 0.1;
            secondFallback.play().catch(() => {});
          } catch (error) {
            console.log('All notification sounds failed');
          }
        });
      } catch (fallbackError) {
        console.log(`Notification sound file not found`);
      }
    });
  } catch (e) {
    console.log(`Error playing notification sound`);
  }
};

// --------------------------------
// Add this code in the handleBackendMessage function
// Right after the if statement checking for Agent mode response (around line 378)
// and before the "Enhanced message processing" section
// --------------------------------

// Special handling for Suggestion mode messages with notification
if (data.mode === 'SUGGEST' || (currentMode === 'Suggest' && !data.mode)) {
  console.log('✨ Suggestion notification received:', data);
  hideTypingIndicator();
  
  // Play the notification sound (louder than regular messages)
  if (data.play_sound !== false) {
    playSuggestionNotification();
  } else {
    playSound('message-received');
  }
  
  // Process the suggestion message content
  const processedContent = processResponseByMode(data.response || 'No suggestion received', 'Suggest');
  
  // Create the suggestion message with notification flag
  const suggestionMessage = {
    id: Date.now(),
    type: 'assistant',
    content: processedContent,
    timestamp: new Date(),
    confidence: data.confidence || 1.0,
    mode: 'Suggest',
    processingTime: data.processing_time || 0,
    resources: data.resources || [],
    enterpriseValidated: data.enterprise_validated || false,
    isNotification: true, // Mark this as a notification
    interactive: data.interactive || false,
    buttons: data.buttons || [],
    importance: data.importance || 'normal'
  };
  
  // Add the message to the list
  messages = [...messages, suggestionMessage];
  
  // Ensure the UI shows the notification prominently
  setTimeout(() => {
    // Flash the message briefly for attention
    const messageElement = document.querySelector(`.message[data-id="${suggestionMessage.id}"]`);
    if (messageElement) {
      messageElement.classList.add('flash-notification');
      setTimeout(() => messageElement.classList.remove('flash-notification'), 1000);
    }
    scrollToBottom();
  }, 100);
  
  return;
}

// --------------------------------
// Add this CSS to the <style> section at the end of the file
// --------------------------------

/* Suggestion Notification Styling */
.message.notification-flash {
  animation: notification-pulse 1.5s 1;
}

@keyframes notification-pulse {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 rgba(48, 209, 88, 0); }
  50% { transform: scale(1.03); box-shadow: 0 0 15px rgba(48, 209, 88, 0.5); }
}

/* Add this to the message.assistant class */
.message.assistant.is-notification .message-content {
  background: linear-gradient(135deg, rgba(48, 209, 88, 0.1), rgba(50, 215, 75, 0.2));
  border: 1px solid rgba(48, 209, 88, 0.3);
  box-shadow: 0 0 8px rgba(48, 209, 88, 0.2);
}

/* Add this for high importance notifications */
.message.assistant.is-notification.high-importance .message-content {
  background: linear-gradient(135deg, rgba(48, 209, 88, 0.2), rgba(50, 215, 75, 0.3));
  border: 1px solid rgba(48, 209, 88, 0.5);
  box-shadow: 0 0 12px rgba(48, 209, 88, 0.3);
}

// --------------------------------
// Modify the template to support notification styling
// Find the div with class="message {message.type}" (around line 1210)
// and update it with these additional classes:
// --------------------------------

<div 
  class="message {message.type}" 
  class:welcome={message.isWelcome}
  class:is-notification={message.isNotification}
  class:high-importance={message.importance === 'high'}
  data-id={message.id}
  transition:fly={{ y: 20, duration: 300, easing: cubicOut }}
>