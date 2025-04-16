document.addEventListener('DOMContentLoaded', function() {
    // Initialize chat elements
    const chatMessages = document.getElementById('chat-messages');
    const queryInput = document.getElementById('query-input');
    const sendBtn = document.getElementById('send-btn');
    const commandBtns = document.querySelectorAll('.command-btn');

    // Check if required elements exist
    if (!chatMessages || !queryInput || !sendBtn) {
        console.error('Required chat elements not found in the DOM');
        return;
    }

    // Scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Initialize
    scrollToBottom();

    // Format context analysis sections
    function formatContextSections(content) {
        // Split content into sections
        const sections = content.split('\n\n');
        let formattedContent = '';
        
        sections.forEach(section => {
            if (section.startsWith('[Context Analysis]')) {
                formattedContent += '<div class="context-section">';
                formattedContent += '<h3>Context Analysis</h3>';
                formattedContent += '<div class="context-content">';
                formattedContent += section.replace('[Context Analysis]', '');
                formattedContent += '</div></div>';
            } else if (section.startsWith('[Response]')) {
                formattedContent += '<div class="response-section">';
                formattedContent += '<h3>Response</h3>';
                formattedContent += '<div class="response-content">';
                formattedContent += section.replace('[Response]', '');
                formattedContent += '</div></div>';
            } else if (section.startsWith('[Semantic Understanding]')) {
                formattedContent += '<div class="semantic-section">';
                formattedContent += '<h3>Semantic Understanding</h3>';
                formattedContent += '<div class="semantic-content">';
                formattedContent += section.replace('[Semantic Understanding]', '');
                formattedContent += '</div></div>';
            } else {
                formattedContent += section;
            }
        });
        
        return formattedContent;
    }

    // Add message to chat
    function addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        // Format content based on sections
        let formattedContent = content;
        if (role === 'assistant') {
            // Split content into sections
            const sections = content.split('\n\n');
            formattedContent = '';
            
            for (const section of sections) {
                if (section.startsWith('Context Analysis:')) {
                    formattedContent += `<div class="context-section">
                        <h3>Context Analysis</h3>
                        <div class="context-content">${section.replace('Context Analysis:', '').trim()}</div>
                    </div>`;
                } else if (section.startsWith('Response:')) {
                    formattedContent += `<div class="response-section">
                        <h3>Response</h3>
                        <div class="response-content">${section.replace('Response:', '').trim()}</div>
                    </div>`;
                } else {
                    formattedContent += `<div class="message-content">${section}</div>`;
                }
            }
        } else {
            formattedContent = `<div class="message-content">${content}</div>`;
        }
        
        messageDiv.innerHTML = formattedContent;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Show loading indicator
    function showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant';
        loadingDiv.innerHTML = '<div class="message-content">Thinking...</div>';
        chatMessages.appendChild(loadingDiv);
        scrollToBottom();
        return loadingDiv;
    }

    // Remove loading indicator
    function removeLoading() {
        const loadingDiv = chatMessages.querySelector('.message:last-child');
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
            // Send request with JSON data
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ query: query.trim() })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            // Parse response
            const data = await response.json();
            
            // Remove loading indicator
            removeLoading();
            
            if (data.error) {
                // Show error
                addMessage('assistant', `Error: ${data.reply}`);
            } else {
                // Add assistant message with formatted context
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