document.addEventListener('DOMContentLoaded', function() {
    const widget = document.querySelector('.assistant-widget');
    const header = document.querySelector('.widget-header');
    const minimizeBtn = document.getElementById('minimize-btn');
    const closeBtn = document.getElementById('close-btn');
    const chatMessages = document.getElementById('chat-messages');
    const queryInput = document.getElementById('query-input');
    const sendBtn = document.getElementById('send-btn');
    const quickQuestionBtns = document.querySelectorAll('.quick-question-btn');

    // For message grouping
    let lastMessageTime = null;
    let lastMessageDate = null;
    let lastMessageRole = null;

    // Drag functionality
    let isDragging = false;
    let currentX;
    let currentY;
    let initialX;
    let initialY;
    let xOffset = 0;
    let yOffset = 0;

    header.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', dragEnd);

    function dragStart(e) {
        if (e.target.closest('.control-btn')) return;
        
        initialX = e.clientX - xOffset;
        initialY = e.clientY - yOffset;

        if (e.target.closest('.widget-header')) {
            isDragging = true;
        }
    }

    function drag(e) {
        if (isDragging) {
            e.preventDefault();
            currentX = e.clientX - initialX;
            currentY = e.clientY - initialY;

            xOffset = currentX;
            yOffset = currentY;

            setTranslate(currentX, currentY, widget);
        }
    }

    function dragEnd() {
        initialX = currentX;
        initialY = currentY;
        isDragging = false;
    }

    function setTranslate(xPos, yPos, el) {
        el.style.transform = `translate3d(${xPos}px, ${yPos}px, 0)`;
    }

    // Auto-resize textarea
    function autoResizeTextarea() {
        queryInput.style.height = 'auto';
        const newHeight = Math.min(Math.max(queryInput.scrollHeight, 38), 120);
        queryInput.style.height = newHeight + 'px';
    }

    queryInput.addEventListener('input', autoResizeTextarea);
    
    // Initial sizing
    setTimeout(autoResizeTextarea, 10);

    // Minimize functionality
    minimizeBtn.addEventListener('click', () => {
        widget.classList.toggle('minimized');
        if (widget.classList.contains('minimized')) {
            widget.style.height = '60px';
            chatMessages.style.display = 'none';
            document.querySelector('.input-area').style.display = 'none';
        } else {
            widget.style.height = '600px';
            chatMessages.style.display = 'flex';
            document.querySelector('.input-area').style.display = 'block';
            scrollToBottom();
            queryInput.focus();
        }
    });

    // Close functionality
    closeBtn.addEventListener('click', () => {
        widget.style.display = 'none';
    });

    // Scroll to bottom of chat
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Initialize
    scrollToBottom();
    
    // Format message content for different sections
    function formatMessageContent(content) {
        // Check if content contains markdown code blocks
        if (content.includes('```')) {
            content = formatCodeBlocks(content);
        }
        
        // Split content into sections
        const sections = content.split('\n\n');
        let formattedContent = '';
        
        let isInSection = false;
        
        for (const section of sections) {
            if (section.startsWith('Context Analysis:') || section.startsWith('[Context Analysis]')) {
                isInSection = true;
                formattedContent += `<div class="context-section">
                    <h4>Context Analysis</h4>
                    <div class="context-content">${section.replace(/(Context Analysis:|^\[Context Analysis\])/g, '').trim()}</div>
                </div>`;
            } else if (section.startsWith('Response:') || section.startsWith('[Response]')) {
                isInSection = true;
                formattedContent += `<div class="response-section">
                    <h4>Response</h4>
                    <div class="response-content">${section.replace(/(Response:|^\[Response\])/g, '').trim()}</div>
                </div>`;
            } else if (section.startsWith('Semantic Understanding:') || section.startsWith('[Semantic Understanding]')) {
                isInSection = true;
                formattedContent += `<div class="semantic-section">
                    <h4>Semantic Understanding</h4>
                    <div class="semantic-content">${section.replace(/(Semantic Understanding:|^\[Semantic Understanding\])/g, '').trim()}</div>
                </div>`;
            } else if (section.toLowerCase().includes('error:')) {
                isInSection = true;
                formattedContent += `<div class="error-message">${section}</div>`;
            } else {
                formattedContent += `<p>${section}</p>`;
            }
        }
        
        return isInSection ? formattedContent : content;
    }
    
    // Format code blocks with syntax highlighting
    function formatCodeBlocks(content) {
        // Simple code block formatting
        return content.replace(/```(\w*)([\s\S]*?)```/g, function(match, language, code) {
            return `<pre><code class="language-${language}">${code.trim()}</code></pre>`;
        });
    }

    // Add timestamp separator if needed
    function addTimestampIfNeeded() {
        const now = new Date();
        const nowDate = now.toLocaleDateString();
        const isNewDay = lastMessageDate !== nowDate;
        
        // Check if we need to add a new day separator
        if (lastMessageDate && isNewDay) {
            const dateSeparator = document.createElement('div');
            dateSeparator.className = 'date-separator';
            dateSeparator.innerHTML = `<div class="separator-line"></div>
                                      <div class="separator-text">${formatDateForDisplay(now)}</div>
                                      <div class="separator-line"></div>`;
            chatMessages.appendChild(dateSeparator);
        }
        
        // Check if we need to add a time separator (if more than 5 minutes have passed)
        const nowTime = now.getTime();
        if (lastMessageTime && (nowTime - lastMessageTime > 5 * 60 * 1000)) {
            const timeSeparator = document.createElement('div');
            timeSeparator.className = 'time-separator';
            timeSeparator.textContent = formatTimeForDisplay(now);
            chatMessages.appendChild(timeSeparator);
        }
        
        // Update the last message time and date
        lastMessageTime = nowTime;
        lastMessageDate = nowDate;
    }
    
    // Format date for display
    function formatDateForDisplay(date) {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        
        if (date.toDateString() === today.toDateString()) {
            return 'Today';
        } else if (date.toDateString() === yesterday.toDateString()) {
            return 'Yesterday';
        } else {
            return date.toLocaleDateString(undefined, { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
        }
    }
    
    // Format time for display
    function formatTimeForDisplay(date) {
        return date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit'
        });
    }

    // Get current timestamp in HH:MM format
    function getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    // Check if message should be grouped
    function shouldGroupMessage(role) {
        // Group messages from the same sender if they're close in time
        return lastMessageRole === role && (Date.now() - lastMessageTime < 60000); // 1 minute
    }

    // Add message to chat
    function addMessage(role, content, isError = false) {
        // Add timestamp separator if needed
        addTimestampIfNeeded();
        
        // Create message wrapper
        const messageWrapper = document.createElement('div');
        messageWrapper.className = `message-wrapper ${role}`;
        
        if (shouldGroupMessage(role)) {
            messageWrapper.classList.add('grouped');
        } else {
            lastMessageRole = role;
        }
        
        const formattedContent = formatMessageContent(content);
        const timestamp = getCurrentTime();
        
        const avatarIcon = role === 'user' ? '👤' : '👁️';
        const avatarClass = role === 'user' ? 'user-avatar' : 'ai-avatar';
        
        // Create avatar or add placeholder for grouped messages
        const avatarHtml = shouldGroupMessage(role) 
            ? '<div class="message-avatar-placeholder"></div>' 
            : `<div class="message-avatar">
                 <div class="${avatarClass}">${avatarIcon}</div>
               </div>`;
        
        messageWrapper.innerHTML = `
            <div class="message ${isError ? 'error' : ''}">
                ${avatarHtml}
                <div class="message-content">
                    <div class="message-text">${formattedContent}</div>
                    <div class="message-time">${timestamp}</div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(messageWrapper);
        scrollToBottom();
    }

    // Show typing indicator
    function showTypingIndicator() {
        // Add timestamp separator if needed
        addTimestampIfNeeded();
        
        const messageWrapper = document.createElement('div');
        messageWrapper.className = 'message-wrapper assistant typing';
        
        if (shouldGroupMessage('assistant')) {
            messageWrapper.classList.add('grouped');
        }
        
        const avatarHtml = shouldGroupMessage('assistant') 
            ? '<div class="message-avatar-placeholder"></div>' 
            : `<div class="message-avatar">
                 <div class="ai-avatar">👁️</div>
               </div>`;
        
        messageWrapper.innerHTML = `
            <div class="message">
                ${avatarHtml}
                <div class="message-content">
                    <div class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(messageWrapper);
        scrollToBottom();
        return messageWrapper;
    }

    // Remove typing indicator
    function removeTypingIndicator() {
        const typingIndicator = chatMessages.querySelector('.message-wrapper.typing');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    // Send query to server
    async function sendQuery(query) {
        if (!query.trim()) return;
        
        // Add user message to chat
        addMessage('user', query);
        
        // Clear input and reset height
        queryInput.value = '';
        queryInput.style.height = 'auto';
        
        // Show typing indicator
        const typingIndicator = showTypingIndicator();
        
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
            
            // Remove typing indicator
            removeTypingIndicator();
            
            if (data.error) {
                // Show error
                addMessage('assistant', `Error: ${data.reply}`, true);
            } else {
                // Add assistant message with formatted content
                addMessage('assistant', data.reply);
            }
            
        } catch (error) {
            console.error('Error sending query:', error);
            removeTypingIndicator();
            addMessage('assistant', 'Failed to communicate with the server. Please try again.', true);
        }
    }

    // Handle quick question buttons
    quickQuestionBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const question = btn.getAttribute('data-question') || btn.textContent;
            sendQuery(question);
        });
    });

    // Handle send button click
    sendBtn.addEventListener('click', () => {
        sendQuery(queryInput.value);
    });

    // Handle Enter key in input (but allow Shift+Enter for new line)
    queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendQuery(queryInput.value);
        }
    });

    // Focus input on page load
    queryInput.focus();

    // Make chat messages container interactive
    chatMessages.addEventListener('click', (e) => {
        // Handle clickable elements within messages if needed
        const codeBlock = e.target.closest('pre');
        if (codeBlock) {
            // Add code copy functionality if desired
            console.log('Code block clicked');
        }
    });

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