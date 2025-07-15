# 🎉 How to Get the SensAI Overlay Working

## Quick Start Options

You have **3 ways** to get the overlay working with your unified backend:

### Option 1: Simple HTML Overlay (Easiest)
```bash
# 1. Make sure unified backend is running
cd /Users/segevbin/Desktop/SensAI/Aiayer/sensai_ui2html
python start_unified_system.py &

# 2. Open the simple HTML overlay in your browser
open overlay/simple_overlay.html
```

### Option 2: Svelte Development Server
```bash
# 1. Make sure unified backend is running
cd /Users/segevbin/Desktop/SensAI/Aiayer/sensai_ui2html
python start_unified_system.py &

# 2. Start the Svelte overlay
cd overlay
./start_overlay_with_unified_backend.sh
```

### Option 3: Tauri Desktop App
```bash
# 1. Make sure unified backend is running
cd /Users/segevbin/Desktop/SensAI/Aiayer/sensai_ui2html
python start_unified_system.py &

# 2. Start Tauri app
cd overlay
npm run tauri dev
```

## What You'll See

Once connected, you'll have:

✅ **Real-time UI Context** - Shows current app and UI elements  
✅ **Chat Interface** - Ask questions about your screen  
✅ **UI Memory Search** - Search through stored UI snapshots  
✅ **Agent Execution** - Execute UI actions from chat  

## Connection Status

- 🟢 **Connected** - Overlay is talking to unified backend
- 🟡 **Connecting** - Attempting to connect
- 🔴 **Disconnected** - No connection to backend

## Troubleshooting

### Backend Not Running
```bash
# Check if backend is running
lsof -i :8767

# Start backend if not running
cd /Users/segevbin/Desktop/SensAI/Aiayer/sensai_ui2html
python start_unified_system.py &
```

### Port Already in Use
```bash
# Kill existing process on port 8767
lsof -ti:8767 | xargs kill -9

# Restart backend
cd /Users/segevbin/Desktop/SensAI/Aiayer/sensai_ui2html
python start_unified_system.py &
```

### Overlay Won't Connect
1. Check browser console for WebSocket errors
2. Verify backend is running: `curl http://localhost:8767`
3. Try refreshing the page
4. Check firewall settings

## Features Available

### Chat Commands
- "What's on my screen?"
- "Show me the current UI"
- "What can I do here?"
- "Click the first button"
- "Search for Finder windows"

### Quick Actions
- 👁️ What's on my screen?
- 📋 Show current UI
- ❓ What can I do here?
- 🔍 Search UI memory

### UI Context Display
- Current application name
- Number of UI elements
- Memory search results
- Real-time updates

## System Architecture

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│   HTML/Svelte   │ ←────────────→ │   Unified       │
│   Overlay       │    Port 8767   │   Backend       │
└─────────────────┘                └─────────────────┘
                                           │
                                           ▼
                                    ┌─────────────────┐
                                    │   UI2HTML       │
                                    │   Memory        │
                                    │   System        │
                                    └─────────────────┘
```

## Next Steps

1. **Try the simple HTML overlay first** - It's the easiest to test
2. **Explore the Svelte version** - More features and better UI
3. **Build the Tauri app** - Desktop application with native features
4. **Customize the interface** - Modify the overlay to your needs

## Support

If you encounter issues:
1. Check the browser console for errors
2. Verify the unified backend is running and responding
3. Test with the simple HTML overlay first
4. Check the logs in `sensai_ui2html/unified_system.log` 