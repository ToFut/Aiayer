// Debug WebSocket connection
function debugWebSocket(url) {
    console.log("Attempting to connect to WebSocket server at:", url);
    
    const ws = new WebSocket(url);
    
    ws.onopen = function() {
        console.log("WebSocket connection established\!");
        document.getElementById('wsDebugStatus').innerHTML = 
            '✅ WebSocket connected successfully to ' + url;
    };
    
    ws.onclose = function(event) {
        console.log("WebSocket connection closed:", event.code, event.reason);
        document.getElementById('wsDebugStatus').innerHTML = 
            '❌ WebSocket closed. Code: ' + event.code + ' Reason: ' + event.reason;
    };
    
    ws.onerror = function(error) {
        console.error("WebSocket error:", error);
        document.getElementById('wsDebugStatus').innerHTML = 
            '❌ WebSocket error - see console for details';
    };
    
    ws.onmessage = function(event) {
        console.log("WebSocket message received:", event.data);
        try {
            const data = JSON.parse(event.data);
            document.getElementById('wsDebugLastMessage').textContent = JSON.stringify(data, null, 2);
        } catch (e) {
            document.getElementById('wsDebugLastMessage').textContent = "Error parsing message: " + e.message;
        }
    };
    
    return ws;
}

// Send a test message
function sendTestMessage(ws) {
    if (\!ws || ws.readyState \!== WebSocket.OPEN) {
        alert("WebSocket is not connected\!");
        return;
    }
    
    const testMessage = {
        type: "test_message",
        message: "Hello from WebSocket Debug Tool",
        timestamp: new Date().toISOString()
    };
    
    ws.send(JSON.stringify(testMessage));
    console.log("Test message sent:", testMessage);
}
