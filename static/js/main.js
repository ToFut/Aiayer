// Constants
const UPDATE_INTERVAL = 5000; // 5 seconds
const PREDICTION_INTERVAL = 60000; // 1 minute
const MAX_EVENTS = 10;
const RECONNECT_DELAY = 3000; // 3 seconds
const HEALTH_STATES = {
    GOOD: { class: 'bg-green-500', text: 'System Healthy' },
    WARNING: { class: 'bg-yellow-500', text: 'System Warning' },
    ERROR: { class: 'bg-red-500', text: 'System Error' },
    UNKNOWN: { class: 'bg-gray-300', text: 'Status Unknown' }
};

// Cache for storing previous values
let previousValues = {
    cpu: 0,
    memory: 0,
    disk: 0,
    events: 0,
    predictions: 0,
    insights: 0
};

// WebSocket connection
let ws = null;
let reconnectTimeout = null;
let isConnected = false;

// Connection status element
const connectionStatus = document.createElement('div');
connectionStatus.id = 'connection-status';
connectionStatus.className = 'fixed top-4 right-4 px-4 py-2 rounded-lg text-white';
document.body.appendChild(connectionStatus);

// Initialize WebSocket connection
function initWebSocket() {
    if (ws) {
        ws.close();
    }

    ws = new WebSocket(`ws://${window.location.host}/ws`);

    ws.onopen = () => {
        console.log('WebSocket connected');
        isConnected = true;
        updateConnectionStatus('connected');
        clearTimeout(reconnectTimeout);
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected');
        isConnected = false;
        updateConnectionStatus('disconnected');
        reconnectTimeout = setTimeout(initWebSocket, RECONNECT_DELAY);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus('error');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
}

// Update connection status UI
function updateConnectionStatus(status) {
    const statusMap = {
        connected: { class: 'bg-green-500', text: 'Connected' },
        disconnected: { class: 'bg-yellow-500', text: 'Disconnected - Reconnecting...' },
        error: { class: 'bg-red-500', text: 'Connection Error' }
    };

    const statusInfo = statusMap[status] || statusMap.disconnected;
    connectionStatus.className = `fixed top-4 right-4 px-4 py-2 rounded-lg text-white ${statusInfo.class}`;
    connectionStatus.textContent = statusInfo.text;
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'system_health':
            updateSystemHealthUI(data.data);
            break;
        case 'ai_sensor_stats':
            updateAISensorStatsUI(data.data);
            break;
        case 'recent_events':
            updateRecentEventsUI(data.data);
            break;
        case 'resource_predictions':
            updateResourcePredictionsUI(data.data);
            break;
        case 'system_insights':
            updateSystemInsightsUI(data.data);
            break;
        case 'chat_message':
            addMessage(data.message, false);
            break;
    }
}

// Update system health
async function updateSystemHealth() {
    try {
        const response = await fetch('/api/system-health');
        const data = await response.json();
        
        // Update metrics with smooth transitions
        animateValue('cpu-usage', previousValues.cpu, data.cpu, '%');
        animateValue('memory-usage', previousValues.memory, data.memory, 'MB');
        animateValue('disk-usage', previousValues.disk, data.disk, '%');
        
        // Update previous values
        previousValues.cpu = data.cpu;
        previousValues.memory = data.memory;
        previousValues.disk = data.disk;
        
        // Update health indicator
        updateHealthIndicator(data.health);
    } catch (error) {
        console.error('Error updating system health:', error);
        updateHealthIndicator('ERROR');
    }
}

// Update AI sensor stats
async function updateAISensorStats() {
    try {
        const response = await fetch('/api/ai-sensor/stats');
        const data = await response.json();
        
        // Update stats with smooth transitions
        animateValue('events-processed', previousValues.events, data.events, '');
        animateValue('active-predictions', previousValues.predictions, data.predictions, '');
        animateValue('insights-generated', previousValues.insights, data.insights, '');
        
        // Update previous values
        previousValues.events = data.events;
        previousValues.predictions = data.predictions;
        previousValues.insights = data.insights;
    } catch (error) {
        console.error('Error updating AI sensor stats:', error);
    }
}

// Update recent events
async function updateRecentEvents() {
    try {
        const response = await fetch('/api/recent-events');
        const data = await response.json();
        
        const eventsContainer = document.getElementById('recent-events');
        eventsContainer.innerHTML = '';
        
        if (data.events && data.events.length > 0) {
            data.events.slice(0, MAX_EVENTS).forEach(event => {
                const eventElement = document.createElement('div');
                eventElement.className = 'p-2 border-b border-gray-200 last:border-0';
                eventElement.innerHTML = `
                    <div class="flex justify-between items-center">
                        <span class="text-sm font-medium">${event.type}</span>
                        <span class="text-xs text-gray-500">${formatTime(event.timestamp)}</span>
                    </div>
                    <p class="text-sm text-gray-600">${event.description}</p>
                `;
                eventsContainer.appendChild(eventElement);
            });
        } else {
            eventsContainer.innerHTML = '<p class="text-gray-500 italic">No recent events</p>';
        }
    } catch (error) {
        console.error('Error updating recent events:', error);
    }
}

// Update resource predictions
async function updateResourcePredictions() {
    try {
        const response = await fetch('/api/resource-predictions');
        const data = await response.json();
        
        document.getElementById('predicted-cpu').textContent = `${data.cpu}%`;
        document.getElementById('predicted-memory').textContent = `${data.memory}MB`;
    } catch (error) {
        console.error('Error updating resource predictions:', error);
    }
}

// Update system insights
async function updateSystemInsights() {
    try {
        const response = await fetch('/api/system-insights');
        const data = await response.json();
        
        const insightsContainer = document.getElementById('system-insights');
        insightsContainer.innerHTML = '';
        
        if (data.insights && data.insights.length > 0) {
            data.insights.forEach(insight => {
                const insightElement = document.createElement('div');
                insightElement.className = 'p-2 border-l-4 border-blue-500 bg-blue-50 mb-2';
                insightElement.innerHTML = `
                    <p class="text-sm text-gray-800">${insight.message}</p>
                    <span class="text-xs text-gray-500">${formatTime(insight.timestamp)}</span>
                `;
                insightsContainer.appendChild(insightElement);
            });
        } else {
            insightsContainer.innerHTML = '<p class="text-gray-500 italic">No insights available</p>';
        }
    } catch (error) {
        console.error('Error updating system insights:', error);
    }
}

// Helper function to animate value changes
function animateValue(elementId, start, end, suffix) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const duration = 500;
    const steps = 20;
    const step = (end - start) / steps;
    let current = start;
    
    const animation = setInterval(() => {
        current += step;
        if ((step > 0 && current >= end) || (step < 0 && current <= end)) {
            clearInterval(animation);
            current = end;
        }
        element.textContent = `${Math.round(current)}${suffix}`;
    }, duration / steps);
}

// Helper function to update health indicator
function updateHealthIndicator(health) {
    const indicator = document.getElementById('health-indicator');
    const text = document.getElementById('health-text');
    const details = document.getElementById('health-details');
    
    if (!indicator || !text || !details) return;
    
    const state = HEALTH_STATES[health] || HEALTH_STATES.UNKNOWN;
    
    // Remove all possible background classes and add the new one
    indicator.className = `w-4 h-4 rounded-full ${state.class}`;
    text.textContent = state.text;
    
    // Update details based on health state
    if (health === 'GOOD') {
        details.textContent = 'All systems operating normally';
        details.className = 'text-sm text-green-600';
    } else if (health === 'WARNING') {
        details.textContent = 'Some systems require attention';
        details.className = 'text-sm text-yellow-600';
    } else if (health === 'ERROR') {
        details.textContent = 'Critical system issues detected';
        details.className = 'text-sm text-red-600';
    } else {
        details.textContent = 'System status information unavailable';
        details.className = 'text-sm text-gray-600';
    }
}

// Helper function to format timestamps
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
}

// Initialize all updates
function initializeUpdates() {
    console.log('Initializing updates...');
    
    // Initialize WebSocket
    initWebSocket();
    
    // Initial updates (fallback if WebSocket fails)
    updateSystemHealth();
    updateAISensorStats();
    updateRecentEvents();
    updateResourcePredictions();
    updateSystemInsights();
    
    // Set update intervals (fallback if WebSocket fails)
    setInterval(() => {
        if (!isConnected) {
            updateSystemHealth();
            updateAISensorStats();
            updateRecentEvents();
            updateSystemInsights();
        }
    }, UPDATE_INTERVAL);
    
    setInterval(() => {
        if (!isConnected) {
            updateResourcePredictions();
        }
    }, PREDICTION_INTERVAL);
}

// Chat functionality
function initializeChat() {
    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-message');
    const chatMessages = document.getElementById('chat-messages');

    function addMessage(message, isUser = false) {
        const messageElement = document.createElement('div');
        messageElement.className = `p-3 rounded-lg ${isUser ? 'bg-blue-100 ml-8' : 'bg-gray-100 mr-8'}`;
        messageElement.innerHTML = `
            <div class="flex items-center space-x-2">
                <span class="font-medium">${isUser ? 'You' : 'AI Assistant'}</span>
                <span class="text-xs text-gray-500">${new Date().toLocaleTimeString()}</span>
            </div>
            <p class="text-gray-700 mt-1">${message}</p>
        `;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function sendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        // Clear input
        chatInput.value = '';

        // Add user message to chat
        addMessage(message, true);

        try {
            if (isConnected && ws) {
                // Send via WebSocket if available
                ws.send(JSON.stringify({ type: 'chat_message', message }));
            } else {
                // Fallback to HTTP
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message })
                });

                const data = await response.json();
                addMessage(data.response);
            }
        } catch (error) {
            console.error('Error sending message:', error);
            addMessage('Sorry, there was an error processing your message. Please try again.', false);
        }
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

// Export functions for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        updateSystemHealth,
        updateAISensorStats,
        updateRecentEvents,
        updateResourcePredictions,
        updateSystemInsights,
        animateValue,
        updateHealthIndicator,
        formatTime,
        initializeUpdates,
        initializeChat
    };
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initializeUpdates();
    initializeChat();
}); 