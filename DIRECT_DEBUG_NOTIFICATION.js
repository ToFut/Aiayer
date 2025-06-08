// This is a JavaScript file to be pasted into the browser console
// when the overlay is open to directly add a notification

function addDirectNotification(message) {
    // This function directly manipulates the Svelte component state
    // to add a notification to the message list
    try {
        // Find Svelte component instances
        const componentInstances = Array.from(document.querySelectorAll('*')).filter(el => 
            el.__svelte && el.__svelte.component && el.__svelte.component.$$
        ).map(el => el.__svelte.component.$$);
        
        // Find component with messages property
        let chatComponent = null;
        for (const instance of componentInstances) {
            if (instance.ctx && Array.isArray(instance.ctx.messages)) {
                chatComponent = instance;
                break;
            }
        }
        
        if (!chatComponent) {
            console.error("Could not find chat component with messages array");
            return false;
        }
        
        // Create a new notification
        const newMessage = {
            id: Date.now(),
            type: 'assistant',
            content: message,
            timestamp: new Date(),
            confidence: 1.0,
            mode: 'Suggest'
        };
        
        // Add to messages array
        chatComponent.ctx.messages = [...chatComponent.ctx.messages, newMessage];
        
        // Notify Svelte of the change
        if (typeof chatComponent.update === 'function') {
            chatComponent.update();
        }
        
        console.log("✅ Direct notification added:", newMessage);
        return true;
    } catch (error) {
        console.error("Error adding direct notification:", error);
        return false;
    }
}

// Add a test notification
addDirectNotification("This is a direct notification added through the browser console. If you see this, the overlay is working correctly, but WebSocket notifications aren't reaching it.");

// Instructions to run this manually:
// 1. Open the overlay app
// 2. Open browser developer tools (right-click > Inspect Element)
// 3. Go to Console tab
// 4. Copy and paste this entire file content
// 5. Press Enter to execute