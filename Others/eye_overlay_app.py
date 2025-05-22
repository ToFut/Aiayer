#!/usr/bin/env python3
"""
Eye Widget Overlay - Desktop Application
Creates a floating eye widget that follows the cursor and provides AI assistant functionality
"""
import tkinter as tk
import json
import asyncio
import threading
import websockets
import logging
import os
import time
from PIL import Image, ImageTk
from io import BytesIO
import base64
from typing import Optional, Dict, Any, List
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/eye_overlay.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("eye_overlay")

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

class EyeOverlayApp:
    """Floating eye widget overlay application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Eye Overlay")
        self.root.attributes('-alpha', 0.9)  # Semi-transparent
        self.root.attributes('-topmost', True)  # Always on top
        self.root.overrideredirect(True)  # No window borders
        
        # Connection and state
        self.ws = None
        self.ws_thread = None
        self.is_connected = False
        self.is_connecting = False
        self.is_chat_open = False
        self.is_following_cursor = True
        self.messages = []
        self.event_loop = None
        self.ws_port = 8765  # Default WebSocket port
        
        # Create the eye widget frame
        self.eye_frame = tk.Frame(
            self.root,
            width=50,
            height=50,
            bg='black',
            highlightthickness=0
        )
        self.eye_frame.pack(fill=tk.BOTH, expand=True)
        self.eye_frame.pack_propagate(False)  # Maintain size
        
        # Eye widget with click handler
        self.eye_label = tk.Label(
            self.eye_frame,
            text="👁️",
            font=("Arial", 24),
            fg="white",
            bg="black",
            cursor="hand2"  # Hand cursor on hover
        )
        self.eye_label.pack(fill=tk.BOTH, expand=True)
        self.eye_label.bind("<Button-1>", self.toggle_chat)
        
        # Connection status indicator
        self.status_indicator = tk.Canvas(
            self.eye_frame,
            width=10,
            height=10,
            bg="black",
            highlightthickness=0
        )
        self.status_indicator.place(x=35, y=35)
        self.status_circle = self.status_indicator.create_oval(0, 0, 10, 10, fill="#cccccc")
        
        # Make the frame round (on supported platforms)
        self.make_frame_round()
        
        # Chat panel (hidden initially)
        self.create_chat_panel()
        
        # Start the WebSocket connection
        self.connect_websocket()
        
        # Set up cursor following
        self.follow_cursor()
        
        # Position the eye initially in the top-right corner
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"+{screen_width-70}+20")
        
        # Bind closing events
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def make_frame_round(self):
        """Make the eye frame round (if platform supports it)"""
        try:
            # For Windows
            if sys.platform.startswith('win'):
                self.root.attributes('-transparentcolor', 'black')
            # For Linux
            elif sys.platform.startswith('linux'):
                self.root.wm_attributes('-type', 'splash')
                self.eye_frame.configure(borderwidth=0)
            # For macOS
            elif sys.platform == 'darwin':
                # macOS has limited support for custom window shapes
                pass
        except Exception as e:
            logger.warning(f"Could not make frame round: {e}")
    
    def create_chat_panel(self):
        """Create the chat panel window"""
        # Create a separate top-level window for the chat
        self.chat_window = tk.Toplevel(self.root)
        self.chat_window.title("AI Assistant")
        self.chat_window.geometry("350x500")
        self.chat_window.attributes('-topmost', True)
        self.chat_window.protocol("WM_DELETE_WINDOW", self.hide_chat)
        
        # Make chat window initially hidden
        self.chat_window.withdraw()
        
        # Chat header
        self.header_frame = tk.Frame(self.chat_window, bg="#f8f9fa", height=40)
        self.header_frame.pack(fill=tk.X)
        
        self.title_label = tk.Label(
            self.header_frame,
            text="AI Assistant",
            font=("Arial", 12, "bold"),
            bg="#f8f9fa",
            fg="#333333"
        )
        self.title_label.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.close_button = tk.Button(
            self.header_frame,
            text="×",
            font=("Arial", 16),
            bg="#f8f9fa",
            fg="#666666",
            relief=tk.FLAT,
            command=self.hide_chat
        )
        self.close_button.pack(side=tk.RIGHT, padx=10)
        
        # Messages area
        self.messages_frame = tk.Frame(self.chat_window, bg="white")
        self.messages_frame.pack(fill=tk.BOTH, expand=True)
        
        self.messages_canvas = tk.Canvas(self.messages_frame, bg="white")
        self.messages_scrollbar = tk.Scrollbar(
            self.messages_frame,
            orient="vertical",
            command=self.messages_canvas.yview
        )
        self.messages_scrollable_frame = tk.Frame(self.messages_canvas, bg="white")
        
        self.messages_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.messages_canvas.configure(
                scrollregion=self.messages_canvas.bbox("all")
            )
        )
        
        self.messages_canvas.create_window(
            (0, 0),
            window=self.messages_scrollable_frame,
            anchor="nw"
        )
        self.messages_canvas.configure(yscrollcommand=self.messages_scrollbar.set)
        
        self.messages_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.messages_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add initial greeting message
        self.add_message("assistant", "Hi there! I'm your AI assistant. How can I help you today?")
        
        # Input area
        self.input_frame = tk.Frame(self.chat_window, bg="#f5f5f5", height=60)
        self.input_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.message_entry = tk.Entry(
            self.input_frame,
            font=("Arial", 11),
            bd=1,
            relief=tk.SOLID
        )
        self.message_entry.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=(10, 5),
            pady=10
        )
        self.message_entry.bind("<Return>", self.send_message)
        
        self.send_button = tk.Button(
            self.input_frame,
            text="Send",
            font=("Arial", 10),
            bg="#4CAF50",
            fg="white",
            relief=tk.FLAT,
            command=self.send_message
        )
        self.send_button.pack(side=tk.RIGHT, padx=(5, 10), pady=10)
    
    def add_message(self, msg_type, content):
        """Add a message to the chat panel"""
        # Create a message frame
        msg_frame = tk.Frame(
            self.messages_scrollable_frame,
            bg="white"
        )
        msg_frame.pack(
            fill=tk.X,
            padx=10,
            pady=5,
            anchor="w" if msg_type == "assistant" else "e"
        )
        
        # Message bubble
        bubble_bg = "#F5F5F5" if msg_type == "assistant" else "#E3F2FD"
        bubble_fg = "#333333" if msg_type == "assistant" else "#0D47A1"
        
        msg_bubble = tk.Label(
            msg_frame,
            text=content,
            font=("Arial", 10),
            bg=bubble_bg,
            fg=bubble_fg,
            wraplength=250,
            justify=tk.LEFT,
            padx=10,
            pady=10,
            relief=tk.SOLID,
            bd=0
        )
        msg_bubble.pack(
            side="left" if msg_type == "assistant" else "right",
            anchor="w" if msg_type == "assistant" else "e"
        )
        
        # Store the message
        self.messages.append({
            "type": msg_type,
            "content": content
        })
        
        # Scroll to the bottom
        self.messages_canvas.update_idletasks()
        self.messages_canvas.yview_moveto(1.0)
    
    def send_message(self, event=None):
        """Send a message to the server"""
        # Get message content
        content = self.message_entry.get().strip()
        if not content or not self.is_connected:
            return
        
        # Add to UI
        self.add_message("user", content)
        
        # Clear input
        self.message_entry.delete(0, tk.END)
        
        # Send to server
        self.send_to_ws("user_interaction", {
            "type": "query",
            "query": content
        })
    
    def toggle_chat(self, event=None):
        """Toggle the chat panel visibility"""
        if self.is_chat_open:
            self.hide_chat()
        else:
            self.show_chat()
    
    def show_chat(self):
        """Show the chat panel"""
        self.is_chat_open = True
        self.is_following_cursor = False
        
        # Position chat window near the eye
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        
        # Position the chat either to the left or right of the eye
        screen_width = self.root.winfo_screenwidth()
        if x > screen_width / 2:
            # Eye is on the right side, show chat to the left
            self.chat_window.geometry(f"+{x - 360}+{y}")
        else:
            # Eye is on the left side, show chat to the right
            self.chat_window.geometry(f"+{x + 60}+{y}")
        
        self.chat_window.deiconify()
        self.chat_window.lift()
        self.message_entry.focus_set()
    
    def hide_chat(self):
        """Hide the chat panel"""
        self.is_chat_open = False
        self.is_following_cursor = True
        self.chat_window.withdraw()
    
    def follow_cursor(self):
        """Make the eye widget follow the cursor"""
        if self.is_following_cursor:
            x = self.root.winfo_pointerx() - 25  # Center eye on cursor
            y = self.root.winfo_pointery() - 25
            
            # Keep within screen boundaries
            screen_width = self.root.winfo_screenwidth() 
            screen_height = self.root.winfo_screenheight()
            
            x = max(0, min(x, screen_width - 50))
            y = max(0, min(y, screen_height - 50))
            
            self.root.geometry(f"+{x}+{y}")
        
        # Schedule the next update
        self.root.after(50, self.follow_cursor)
    
    def update_connection_status(self, status):
        """Update the connection status indicator"""
        if status == "connected":
            self.status_indicator.itemconfig(self.status_circle, fill="#4CAF50")
            self.is_connected = True
        elif status == "connecting":
            self.status_indicator.itemconfig(self.status_circle, fill="#FFC107")
            self.is_connected = False
        elif status == "error":
            self.status_indicator.itemconfig(self.status_circle, fill="#F44336")
            self.is_connected = False
        else:
            self.status_indicator.itemconfig(self.status_circle, fill="#cccccc")
            self.is_connected = False
    
    def connect_websocket(self):
        """Create and start a WebSocket client thread"""
        self.is_connecting = True
        self.update_connection_status("connecting")
        
        def run_ws_client():
            # Create an event loop in the new thread
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)
            
            try:
                self.event_loop.run_until_complete(self.ws_client_loop())
            except Exception as e:
                logger.error(f"WebSocket client loop error: {e}")
            finally:
                self.event_loop.close()
        
        # Create and start the thread
        self.ws_thread = threading.Thread(target=run_ws_client)
        self.ws_thread.daemon = True
        self.ws_thread.start()
    
    async def ws_client_loop(self):
        """WebSocket client loop"""
        while True:
            try:
                logger.info(f"Connecting to WebSocket server at ws://localhost:{self.ws_port}")
                async with websockets.connect(f"ws://localhost:{self.ws_port}") as ws:
                    self.ws = ws
                    
                    # Update status in the main thread
                    self.root.after(0, lambda: self.update_connection_status("connected"))
                    logger.info("Connected to WebSocket server")
                    
                    # Send initial connection message
                    await ws.send(json.dumps({
                        "type": "connection_established",
                        "payload": {
                            "client": "eye_overlay_app",
                            "version": "1.0.0",
                            "timestamp": int(time.time())
                        }
                    }))
                    
                    # Message handling loop
                    async for message in ws:
                        try:
                            data = json.loads(message)
                            logger.debug(f"Received message: {data}")
                            
                            # Handle different message types
                            msg_type = data.get('type')
                            
                            if msg_type == 'query_response' and 'response' in data:
                                # Handle AI response
                                response = data.get('response')
                                self.root.after(0, lambda text=response: self.add_message("assistant", text))
                            
                            elif msg_type == 'sensor_data':
                                # Process sensor data (if needed)
                                pass
                            
                        except json.JSONDecodeError:
                            logger.warning(f"Invalid JSON received: {message[:100]}...")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                    
            except (websockets.exceptions.ConnectionClosed, ConnectionRefusedError) as e:
                self.ws = None
                logger.warning(f"WebSocket connection error: {e}")
                self.root.after(0, lambda: self.update_connection_status("error"))
                
                # Wait before reconnecting
                await asyncio.sleep(3)
                
            except Exception as e:
                self.ws = None
                logger.error(f"Unexpected WebSocket error: {e}")
                self.root.after(0, lambda: self.update_connection_status("error"))
                
                # Wait before reconnecting
                await asyncio.sleep(3)
    
    def send_to_ws(self, msg_type, payload):
        """Send a message to the WebSocket server (thread-safe)"""
        if not self.ws or not self.is_connected:
            logger.warning("Cannot send message: WebSocket not connected")
            return
        
        message = {
            "type": msg_type,
            "payload": payload,
            "timestamp": int(time.time())
        }
        
        # Send in the WebSocket thread
        if self.event_loop:
            asyncio.run_coroutine_threadsafe(
                self.ws.send(json.dumps(message)),
                self.event_loop
            )
    
    def on_close(self):
        """Handle window close event"""
        logger.info("Closing application")
        self.root.destroy()
        sys.exit(0)

    def start(self):
        """Start the application main loop"""
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = EyeOverlayApp()
        app.start()
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)