document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chat-container');
    const queryInput = document.getElementById('query-input');
    const sendBtn = document.getElementById('send-btn');
    const commandBtns = document.querySelectorAll('.command-btn');

    // Scroll to bottom of chat
    function scrollToBottom() {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // Initialize
    scrollToBottom();

    // Add a message to the chat
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.innerHTML = content;
        
        messageDiv.appendChild(contentDiv);
        chatContainer.appendChild(messageDiv);
        
        scrollToBottom();
        return messageDiv;
    }

    // Show loading indicator
    function showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant';
        loadingDiv.innerHTML = '<div class="message-content">Thinking...</div>';
        chatContainer.appendChild(loadingDiv);
        scrollToBottom();
        return loadingDiv;
    }

    // Remove loading indicator
    function removeLoading() {
        const loadingDiv = chatContainer.querySelector('.message:last-child');
        if (loadingDiv && loadingDiv.querySelector('.message-content').textContent === 'Thinking...') {
            loadingDiv.remove();
        }
    }

    // Send query to server
    async function sendQuery(query) {
        if (!query.trim()) return;
        
        // Add user message to chat
        addMessage('user', query);
        
        // Clear input
        queryInput.value = '';
        
        // Show loading indicator
        const loadingDiv = showLoading();
        
        try {
            // Prepare form data
            const formData = new FormData();
            formData.append('query', query);
            
            // Send request
            const response = await fetch('/ask', {
                method: 'POST',
                body: formData
            });
            
            // Parse response
            const data = await response.json();
            
            // Remove loading indicator
            removeLoading();
            
            if (data.error) {
                // Show error
                addMessage('assistant', `Error: ${data.error}`);
            } else if (data.command === 'clear') {
                // Clear chat
                chatContainer.innerHTML = '';
                addMessage('assistant', data.reply);
            } else {
                // Add assistant message
                addMessage('assistant', data.reply);
            }
            
        } catch (error) {
            console.error('Error sending query:', error);
            removeLoading();
            addMessage('assistant', 'Failed to communicate with the server. Please try again.');
        }
    }

    // Handle command buttons
    commandBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const command = btn.getAttribute('data-command');
            sendQuery(command);
        });
    });

    // Handle send button click
    sendBtn.addEventListener('click', () => {
        sendQuery(queryInput.value);
    });

    // Handle Enter key in input
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            sendQuery(queryInput.value);
        }
    });

    // Focus input on page load
    queryInput.focus();

    // Setup Server-Sent Events for real-time updates
    if (!!window.EventSource) {
        const eventSource = new EventSource('/events');
        
        eventSource.addEventListener('message', function(e) {
            const data = JSON.parse(e.data);
            if (data.event === 'new_message') {
                // Refresh or fetch new messages
                console.log('New message available');
            } else if (data.event === 'context_update') {
                // Context was updated (e.g. screen content changed)
                console.log('Context updated:', data.source);
            }
        });
        
        eventSource.addEventListener('error', function() {
            console.log('SSE connection error, reconnecting...');
        });
    }
}); 