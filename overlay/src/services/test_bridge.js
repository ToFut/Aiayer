/**
 * Simple test script to check WebSocket connectivity
 * This file is meant to be run inside the Tauri app to test bridge connectivity
 */

// Function to test connection to a WebSocket server
async function testConnection(url) {
  console.log(`Trying to connect to ${url}...`);
  
  return new Promise((resolve) => {
    try {
      const socket = new WebSocket(url);
      
      socket.onopen = () => {
        console.log(`Connected to ${url} successfully!`);
        
        // Send a test message
        const testMessage = {
          type: "test",
          payload: {
            message: "Hello from Tauri client",
            timestamp: Date.now()
          }
        };
        
        socket.send(JSON.stringify(testMessage));
        console.log(`Sent test message to ${url}`);
      };
      
      socket.onmessage = (event) => {
        console.log(`Received response from ${url}: ${event.data}`);
        resolve(true);
        setTimeout(() => socket.close(), 500);
      };
      
      socket.onerror = (error) => {
        console.error(`Error connecting to ${url}: ${error}`);
        resolve(false);
      };
      
      socket.onclose = () => {
        console.log(`Connection to ${url} closed`);
      };
      
      // Set a timeout in case we never get a response
      setTimeout(() => {
        if (socket.readyState !== WebSocket.CLOSED) {
          console.warn(`No response received from ${url} within timeout`);
          socket.close();
          resolve(false);
        }
      }, 5000);
      
    } catch (error) {
      console.error(`Failed to connect to ${url}: ${error}`);
      resolve(false);
    }
  });
}

// Test both connections when this module is loaded
async function runTests() {
  console.log("Testing WebSocket connections...");
  
  const urls = [
    "ws://localhost:8765",
    "ws://localhost:8770"
  ];
  
  const results = [];
  
  for (const url of urls) {
    const result = await testConnection(url);
    results.push({ url, result });
    console.log("-".repeat(50));
  }
  
  // Print summary
  console.log("\nSummary:");
  for (const { url, result } of results) {
    const status = result ? "✅ WORKING" : "❌ NOT WORKING";
    console.log(`${url}: ${status}`);
  }
  
  // Return overall result
  return results.some(({ result }) => result);
}

// Export the test function
export { runTests };

// Run tests automatically if this is loaded directly
if (typeof window !== 'undefined' && window.document) {
  console.log("Test bridge script loaded");
  window.testBridgeConnections = runTests;
  
  // Create a UI element to display results
  const createTestUI = () => {
    const div = document.createElement('div');
    div.style.position = 'fixed';
    div.style.top = '10px';
    div.style.right = '10px';
    div.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    div.style.color = 'white';
    div.style.padding = '10px';
    div.style.borderRadius = '5px';
    div.style.zIndex = '9999';
    div.style.fontFamily = 'monospace';
    div.style.fontSize = '12px';
    div.style.maxWidth = '400px';
    div.style.maxHeight = '200px';
    div.style.overflow = 'auto';
    div.id = 'ws-test-results';
    div.innerHTML = '<h3>WebSocket Connection Tests</h3><button id="run-tests">Run Tests</button><div id="test-output"></div>';
    document.body.appendChild(div);
    
    document.getElementById('run-tests').addEventListener('click', async () => {
      const output = document.getElementById('test-output');
      output.innerHTML = '<p>Running tests...</p>';
      
      try {
        await runTests();
        
        // Results will already be in the console from the runTests function
        output.innerHTML += '<p>Tests completed! Check console for details.</p>';
      } catch (e) {
        output.innerHTML += `<p>Error running tests: ${e.message}</p>`;
      }
    });
  };
  
  // Add the UI when the DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', createTestUI);
  } else {
    createTestUI();
  }
}